"""As consultas por trás das ferramentas do MCP (ESPECIFICACAO.md §8). Todas só leem `contexto.*`.

Cada resposta traz a fonte (caminho do arquivo ou tabela do painel) — o agente deve citá-la.
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

import psycopg
from psycopg.rows import dict_row

from .busca import Filtros, buscar, resolver_no, vizinhos
from .seguranca import excluido


def _limpar(v):
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, dict):
        return {k: _limpar(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_limpar(x) for x in v]
    return v


def _no(con, id_: str) -> dict | None:
    with con.cursor(row_factory=dict_row) as cur:
        r = cur.execute("select id, tipo, nome, projeto, data, fonte, dados from contexto.nos where id = %s",
                        (id_,)).fetchone()
    return _limpar(r) if r else None


def _ligados(con, id_: str, tipo_aresta: str, sentido: str = "saida", tipo_no: str | None = None,
             ordem: str = "n.nome", limite: int = 200) -> list[dict]:
    lado, outro = ("origem", "destino") if sentido == "saida" else ("destino", "origem")
    filtro = "and n.tipo = %s" if tipo_no else ""
    params = [id_, tipo_aresta] + ([tipo_no] if tipo_no else []) + [limite]
    with con.cursor(row_factory=dict_row) as cur:
        linhas = cur.execute(
            f"select n.id, n.tipo, n.nome, n.projeto, n.data, n.fonte, n.dados, a.dados as aresta "
            f"from contexto.arestas a join contexto.nos n on n.id = a.{outro} "
            f"where a.{lado} = %s and a.tipo = %s {filtro} order by {ordem} limit %s", params).fetchall()
    return [_limpar(x) for x in linhas]


def _nao_achado(termo: str, tipo: str) -> dict:
    return {"erro": f"{tipo} não encontrado: {termo!r}",
            "dica": "use buscar(consulta) ou vizinhos(no) para achar o nome certo"}


def contexto_do_projeto(con: psycopg.Connection, projeto: str) -> dict:
    pid = resolver_no(con, projeto, ["projeto"])
    if not pid:
        return _nao_achado(projeto, "projeto")
    no = _no(con, pid)
    agentes = _ligados(con, pid, "pertence_a", "entrada", "agente")
    docs = _ligados(con, pid, "pertence_a", "entrada", "documento")
    principais_tipos = {"instrucoes": 0, "readme": 1, "decisoes": 2, "estado": 3, "handoff": 4, "documentacao": 5,
                        "backlog": 6, "mapa": 7}
    principais = sorted([d for d in docs if d["dados"].get("tipo_doc") in principais_tipos],
                        key=lambda d: (principais_tipos[d["dados"]["tipo_doc"]], d["nome"]))
    decisoes = _ligados(con, pid, "decide_sobre", "entrada", "decisao", "n.data desc nulls last, n.id", 40)
    with con.cursor(row_factory=dict_row) as cur:
        contagem = cur.execute(
            "select d.tipo, count(*) n from contexto.documentos d where d.projeto = %s group by 1 order by 2 desc",
            (pid.split(":", 1)[1],)).fetchall()
    return {
        "projeto": {"id": pid, "nome": no["nome"], "descricao": no["dados"].get("descricao"),
                    "pastas": no["dados"].get("pastas"), "instrucoes": no["dados"].get("instrucoes"),
                    "fonte": no["fonte"]},
        "area_pai": [p["id"] for p in _ligados(con, pid, "pertence_a", "saida", "projeto")],
        "sub_areas": [p["id"] for p in _ligados(con, pid, "pertence_a", "entrada", "projeto")],
        "depende_de": [p["id"] for p in _ligados(con, pid, "depende_de", "saida")],
        "dependem_dele": [p["id"] for p in _ligados(con, pid, "depende_de", "entrada")],
        "agentes": [{"id": a["id"], "cargo": a["dados"].get("cargo"), "departamento": a["dados"].get("departamento"),
                     "fonte": a["fonte"]} for a in agentes],
        "documentos_principais": [{"caminho": d["nome"], "tipo": d["dados"].get("tipo_doc")} for d in principais][:15],
        "documentos_por_tipo": {c["tipo"]: c["n"] for c in contagem},
        "decisoes": [{"id": d["id"], "nome": d["nome"], "data": d["data"], "fonte": d["fonte"]} for d in decisoes],
        "fonte": "estudio-contexto/projetos.yaml + painel.agentes + contexto.documentos",
    }


def contexto_do_video(con: psycopg.Connection, slug: str) -> dict:
    vid = resolver_no(con, slug, ["video"])
    if not vid:
        return _nao_achado(slug, "vídeo")
    no = _no(con, vid)
    portoes = _ligados(con, vid, "avalia", "entrada", "portao", "n.id")
    veredictos = _ligados(con, vid, "aprovou", "entrada", "veredicto", "n.data desc", 50) + \
        _ligados(con, vid, "bloqueou", "entrada", "veredicto", "n.data desc", 50)
    veredictos.sort(key=lambda v: v["dados"].get("em") or "", reverse=True)
    decisoes = _ligados(con, vid, "decide_sobre", "entrada", "decisao", "n.data desc nulls last")
    publicacoes = _ligados(con, vid, "publicado_como", "saida", "publicacao", "n.data")
    docs = _ligados(con, vid, "pertence_a", "entrada", "documento")
    mencoes = _ligados(con, vid, "menciona", "entrada", "documento", "n.nome", 30)
    return {
        "video": {"slug": no["nome"], **{k: no["dados"].get(k) for k in (
            "tema", "pilar", "estado", "estrutura", "cta_palavra", "roteiro_versao", "atualizado",
            "gravacao_prevista")}, "pasta": no["dados"].get("pasta"), "fonte": no["fonte"]},
        "portoes": [{"portao": p["aresta"].get("portao"), "agente": p["nome"], "status": p["aresta"].get("status"),
                     "volta": p["aresta"].get("volta"), "motivos": p["aresta"].get("motivos"),
                     "fonte": "painel.portoes_estado"} for p in portoes],
        "veredictos": [{"resultado": v["dados"].get("resultado"), "portao": v["dados"].get("portao"),
                        "agente": v["dados"].get("agente"), "volta": v["dados"].get("volta"),
                        "em": v["dados"].get("em"), "s0": v["dados"].get("s0"), "s1": v["dados"].get("s1"),
                        "nota": v["dados"].get("nota"), "decisao_autor": v["dados"].get("decisao_autor"),
                        "fonte": v["dados"].get("relatorio") or "painel.veredictos"} for v in veredictos],
        "decisoes": [{"id": d["id"], "nome": d["nome"], "data": d["data"], "fonte": d["fonte"]} for d in decisoes],
        "publicacoes": [{"slug": p["nome"], "publicado_em": p["dados"].get("publicado_em"),
                         "plataformas": p["dados"].get("plataformas"), "trial": p["dados"].get("trial"),
                         "palavra": p["dados"].get("palavra"), "metricas": p["dados"].get("metricas"),
                         "permalink_instagram": p["dados"].get("permalink_instagram"),
                         "fonte": f"painel.publicacoes + painel.metricas ({p['dados'].get('pasta')})"}
                        for p in publicacoes],
        "documentos": [d["nome"] for d in docs if not excluido(d["nome"])],
        "citado_em": [d["nome"] for d in mencoes if not excluido(d["nome"]) and d["nome"] not in {x["nome"] for x in docs}],
    }


def busca(con: psycopg.Connection, consulta: str, projeto: str | None = None, tipo: str | None = None,
          limite: int = 8, agente: str | None = None, desde: str | None = None, ate: str | None = None) -> dict:
    limite = max(1, min(int(limite or 8), 25))
    res = buscar(con, consulta, Filtros(projeto=projeto, tipo=tipo, agente=agente, desde=desde, ate=ate), limite)
    ultima = con.execute("select max(fim) from contexto.sincronizacoes where ok").fetchone()[0]
    return {"consulta": consulta, "resultados": res, "indice_atualizado_em": ultima,
            "aviso": "cite o campo 'fonte' (caminho do arquivo) ao usar cada trecho; o arquivo vence o índice"}


def vizinhanca(con: psycopg.Connection, no: str, profundidade: int = 1) -> dict:
    nid = resolver_no(con, no)
    if not nid:
        return _nao_achado(no, "nó")
    r = vizinhos(con, nid, profundidade)
    r["nos"] = [n for n in r["nos"] if not (n["tipo"] == "documento" and excluido(n["nome"]))]
    return r


def decisoes_sobre(con: psycopg.Connection, tema: str, limite: int = 8) -> dict:
    # 1) trechos das fontes de decisão (docs/decisoes.md e backlog dos portões)
    fontes = buscar(con, tema, Filtros(tipo="decisoes"), limite=limite, expandir=False) + \
        buscar(con, tema, Filtros(tipo="backlog"), limite=max(3, limite // 2), expandir=False)
    fontes.sort(key=lambda r: -r["score"])
    ids: list[str] = []
    for r in fontes:
        for e in r["entidades"]:
            if e.startswith("decisao:") and e not in ids:
                ids.append(e)
    # 2) decisões nomeadas no próprio tema (PD9…)
    for e in buscar(con, tema, limite=limite, expandir=False):
        for x in e["entidades"]:
            if x.startswith("decisao:") and x.split(":", 1)[1].lower() in tema.lower() and x not in ids:
                ids.insert(0, x)
    decisoes = []
    for i in ids[: limite * 2]:
        n = _no(con, i)
        if not n:
            continue
        d = n["dados"]
        decisoes.append({"id": i, "nome": n["nome"], "data": n["data"], "secao": d.get("secao"),
                         "decisao": d.get("decisao") or (d.get("entradas") or [{}])[0].get("achado"),
                         "por_que": d.get("por_que"), "onde": d.get("onde"), "fonte": n["fonte"]})
    # 3) outros documentos que citam essas decisões (HANDOFF, relatórios, README…)
    citam = []
    if ids:
        citam = buscar(con, tema, Filtros(tipo="decisao"), limite=limite, expandir=False)
        citam = [{"fonte": c["fonte"], "secao": c["secao"], "data": c["data"], "trecho": c["trecho"],
                  "decisoes": [e for e in c["entidades"] if e in ids]} for c in citam
                 if c["fonte"] not in ("docs/decisoes.md",)]
    return {"tema": tema, "decisoes": decisoes[:limite],
            "trechos_das_fontes": [{"fonte": r["fonte"], "secao": r["secao"], "data": r["data"],
                                    "trecho": r["trecho"]} for r in fontes[:limite]],
            "citadas_em": citam}


def quem_fiscaliza(con: psycopg.Connection, agente: str, recentes: int = 8) -> dict:
    aid = resolver_no(con, agente, ["agente"])
    if not aid:
        return _nao_achado(agente, "agente")
    nome = aid.split(":", 1)[1]
    portoes = _ligados(con, aid, "fiscaliza", "entrada", "portao")
    no = _no(con, aid)

    def veredictos_do(portao_id: str) -> list[dict]:
        vs = _ligados(con, portao_id, "emitiu", "saida", "veredicto", "n.data desc, n.id desc", recentes)
        return [{"resultado": v["dados"].get("resultado"), "alvo": v["dados"].get("alvo"),
                 "portao": v["dados"].get("portao"), "volta": v["dados"].get("volta"), "em": v["dados"].get("em"),
                 "s0": v["dados"].get("s0"), "s1": v["dados"].get("s1"),
                 "fonte": v["dados"].get("relatorio") or "painel.veredictos"} for v in vs]

    saida = {"agente": nome, "cargo": no["dados"].get("cargo"), "departamento": no["dados"].get("departamento"),
             "fonte": no["fonte"],
             "fiscalizado_por": [{"portao": p["nome"], "areas": p["dados"].get("areas"),
                                  "veredictos_recentes": veredictos_do(p["id"]), "fonte": "painel.agentes"}
                                 for p in portoes]}
    if not portoes:
        saida["observacao"] = "nenhum portão fiscaliza este agente (painel.agentes.fiscalizado_por vazio)"
    proprio = _no(con, f"portao:{nome}")
    if proprio:
        saida["e_portao_de"] = [a["id"] for a in _ligados(con, f"portao:{nome}", "fiscaliza", "saida", "agente")]
        saida["veredictos_que_emitiu"] = veredictos_do(f"portao:{nome}")
    return saida
