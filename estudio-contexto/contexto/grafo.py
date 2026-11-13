"""Grafo de entidades do estúdio (ESPECIFICACAO.md §5).

Fontes (todas só LIDAS):
  - projetos.yaml                              → projeto, pertence_a, depende_de
  - painel.departamentos / painel.agentes       → departamento, agente, gerencia, membro_de, pertence_a, fiscaliza
  - .claude/agents/*.md (frontmatter)           → agente (descrição)
  - painel.videos + pastas de videos/           → video
  - painel.portoes_estado                       → portao, avalia
  - painel.veredictos                           → veredicto, emitiu, aprovou/bloqueou
  - painel.publicacoes + painel.metricas        → publicacao, publicado_como (métricas = valor dentro do nó)
  - docs/decisoes.md + _controle/backlog-portoes.md (códigos PD) → decisao, decide_sobre
  - contexto.documentos / contexto.trechos      → documento, trecho, contem, menciona

`contexto.nos` e `contexto.arestas` são apagadas e refeitas por inteiro a cada passagem, numa transação só.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import psycopg
import yaml
from psycopg.rows import dict_row

from . import config
from .chunking import RX_PD, achar_data
from .corpus import Projeto, video_do_caminho

RX_SLUG = re.compile(r"\b(20\d\d-\d\d-\d\d-[a-z0-9][a-z0-9-]*[a-z0-9])\b")


def _limpo(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[*`_]", "", s)).strip()


def _resumo(s: str, n: int = 140) -> str:
    s = _limpo(s)
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


@dataclass
class Decisao:
    id: str
    nome: str
    texto: str
    fonte: str
    secao: str = ""
    data: dt.date | None = None
    codigo: str | None = None
    dados: dict = field(default_factory=dict)

    @property
    def assinatura(self) -> str:
        """Começo do texto, usado para achar o trecho do índice que contém esta decisão."""
        return _limpo(self.texto)[:80]


def ler_decisoes_md(raiz: Path) -> list[Decisao]:
    arq = raiz / "docs" / "decisoes.md"
    if not arq.exists():
        return []
    saida: list[Decisao] = []
    sec_num, sec_nome, n = "0", "", 0
    for ln in arq.read_text(encoding="utf-8").split("\n"):
        m = re.match(r"^##\s+(\d+[a-z]?)\.?\s*(.*)$", ln)
        if m:
            sec_num, sec_nome, n = m[1], m[2].strip(), 0
            continue
        if ln.startswith("| ") and not ln.startswith(("| Decisão", "|---", "| ---")):
            cel = [c.strip() for c in ln.strip().strip("|").split(" | ")]
            if len(cel) < 2 or set(cel[0]) <= {"-", " ", ":"}:
                continue
            n += 1
            titulo = re.search(r"\*\*(.+?)\*\*", cel[0])
            data = achar_data(cel[1]) if len(cel) > 1 else None
            saida.append(Decisao(
                id=f"decisao:dec-{sec_num}-{n:02d}", nome=_resumo(titulo[1] if titulo else cel[0], 120),
                texto=ln, fonte="docs/decisoes.md", secao=f"{sec_num}. {sec_nome}", data=data,
                dados={"decisao": _resumo(cel[0], 600), "data_texto": cel[1] if len(cel) > 1 else "",
                       "por_que": _resumo(cel[2], 400) if len(cel) > 2 else "",
                       "onde": cel[3] if len(cel) > 3 else ""}))
        elif sec_num == "6" and ln.startswith("- **"):
            n += 1
            titulo = re.search(r"\*\*(.+?)\*\*", ln)
            saida.append(Decisao(id=f"decisao:dec-6-{n:02d}", nome=_resumo(titulo[1] if titulo else ln, 120),
                                 texto=ln, fonte="docs/decisoes.md", secao=f"6. {sec_nome}",
                                 dados={"decisao": _resumo(ln, 600), "categoria": "nao_fazer"}))
    return saida


def ler_pds(raiz: Path) -> dict[str, Decisao]:
    """Códigos PD (achados/decisões do PORTÃO-DADOS) do backlog dos portões, agregando as linhas de cada código."""
    arq = raiz / "_controle" / "backlog-portoes.md"
    saida: dict[str, Decisao] = {}
    if not arq.exists():
        return saida
    for ln in arq.read_text(encoding="utf-8").split("\n"):
        m = re.match(r"^\|\s*(PD\d+)\b([^|]*)\|", ln)
        if not m:
            continue
        cod = m[1]
        cel = [c.strip() for c in ln.strip().strip("|").split(" | ")]
        entrada = {"rotulo": _limpo(cel[0]), "arquivo": cel[1] if len(cel) > 1 else "",
                   "achado": _resumo(cel[2], 600) if len(cel) > 2 else "",
                   "estado": _limpo(cel[-1]) if len(cel) > 6 else ""}
        if cod not in saida:
            saida[cod] = Decisao(id=f"decisao:{cod}", nome=f"{cod} — {_resumo(entrada['achado'], 110)}",
                                 texto=ln, fonte="_controle/backlog-portoes.md", data=achar_data(ln), codigo=cod,
                                 dados={"entradas": []})
        else:
            saida[cod].texto += "\n" + ln
        saida[cod].dados["entradas"].append(entrada)
    return saida


def ler_agentes_arquivos(raiz: Path) -> dict[str, dict]:
    saida = {}
    for arq in sorted((raiz / ".claude" / "agents").glob("*.md")):
        txt = arq.read_text(encoding="utf-8")
        fm = {}
        m = re.match(r"^---\n(.*?)\n---", txt, re.S)
        if m:
            try:
                fm = yaml.safe_load(m[1]) or {}
            except yaml.YAMLError:
                fm = {}
        saida[arq.stem] = {"descricao": _resumo(str(fm.get("description", "")), 600),
                           "modelo": fm.get("model"), "arquivo": arq.relative_to(raiz).as_posix()}
    return saida


def ler_painel(url: str) -> dict[str, list[dict]]:
    """Tabelas do painel numa transação só-leitura. Nada é escrito no painel."""
    tabelas = {
        "departamentos": "select id, nome, descricao, gerente_id from public.departamentos order by ordem, id",
        "agentes": "select id, nome, cargo, departamento_id, papel, resumo, fiscalizado_por, fiscaliza, arquivo, "
                   "modelo from public.agentes order by id",
        "videos": "select slug, tema, pilar, estrutura, cta, estado, atualizado, cta_palavra, gravacao_prevista, "
                  "nome_curto, roteiro_versao from public.videos order by slug",
        "portoes_estado": "select alvo, slug, portao, agente, status, motivos, volta from public.portoes_estado",
        "veredictos": "select alvo, slug, portao, agente, resultado, em, volta, s0, s1, s2, relatorio, nota, "
                      "decisao_autor, ordem from public.veredictos order by em",
        "publicacoes": "select slug, publicado_em, tema, pilar, palavra, duracao_s, trial, permalink_instagram, "
                       "permalink_facebook, video_slug, plataformas, estado from public.publicacoes",
        "metricas": "select distinct on (slug) slug, lido_em, dias, views, alcance, tempo_medio_s, pct_assistido, "
                    "curtidas, comentarios, salvamentos, compartilhamentos, palavra_comentarios, palavra_directs "
                    "from public.metricas order by slug, lido_em desc",
    }
    saida = {}
    with psycopg.connect(url, connect_timeout=5, options="-c default_transaction_read_only=on",
                         row_factory=dict_row) as con:
        for nome, sql in tabelas.items():
            saida[nome] = con.execute(sql).fetchall()
        con.rollback()
    return saida


@dataclass
class Catalogo:
    """Entidades conhecidas, para achar quem cada texto menciona."""
    videos: set[str]
    agentes: set[str]
    projetos: list[Projeto]
    decisoes: list[Decisao]
    pds: dict[str, Decisao]
    _rx_video: re.Pattern | None = None
    _rx_agente: re.Pattern | None = None
    _caudas: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        caudas: dict[str, list[str]] = {}
        for s in self.videos:
            cauda = s[11:]
            if len(cauda) >= 8 and "-" in cauda:
                caudas.setdefault(cauda, []).append(s)
        self._caudas = {c: v[0] for c, v in caudas.items() if len(v) == 1}  # cauda ambígua não conta
        termos = sorted(set(self.videos) | set(self._caudas), key=len, reverse=True)
        self._rx_video = re.compile(r"(?<![\w-])(" + "|".join(map(re.escape, termos)) + r")(?![a-z0-9])") \
            if termos else None
        ag = sorted(self.agentes, key=len, reverse=True)
        self._rx_agente = re.compile(r"(?<![\w-])(" + "|".join(map(re.escape, ag)) + r")(?![\w-])") if ag else None

    def entidades(self, texto: str) -> list[str]:
        ids: set[str] = set()
        if self._rx_video:
            for m in self._rx_video.finditer(texto):
                ids.add("video:" + self._caudas.get(m[1], m[1]))
        if self._rx_agente:
            for m in self._rx_agente.finditer(texto):
                ids.add("agente:" + m[1])
        for cod in RX_PD.findall(texto):
            ids.add("decisao:" + cod)
        for p in self.projetos:
            for pasta in p.pastas:
                if pasta.endswith("/") and len(pasta) > 4 and not pasta.startswith(("videos/", ".claude/", "_controle",
                                                                                   "docs/", "0")):
                    if re.search(r"(?<![\w/-])" + re.escape(pasta), texto):
                        ids.add("projeto:" + p.id)
        return sorted(ids)

    def decisoes_no_trecho(self, caminho: str, texto: str) -> list[str]:
        if caminho != "docs/decisoes.md":
            return []
        limpo = _limpo(texto)
        return [d.id for d in self.decisoes if d.assinatura and d.assinatura in limpo]


def montar_catalogo(raiz: Path, projetos: list[Projeto], painel: dict[str, list[dict]]) -> Catalogo:
    videos = {r["slug"] for r in painel["videos"]}
    pasta = raiz / "videos"
    if pasta.exists():
        videos |= {p.name for p in pasta.iterdir() if p.is_dir() and RX_SLUG.fullmatch(p.name)}
    agentes = {r["id"] for r in painel["agentes"]} | set(ler_agentes_arquivos(raiz))
    return Catalogo(videos, agentes, projetos, ler_decisoes_md(raiz), ler_pds(raiz))


# ───────────────────────────── construção ─────────────────────────────

class Grafo:
    def __init__(self):
        self.nos: dict[str, dict] = {}
        self.arestas: dict[tuple[str, str, str], dict] = {}

    def no(self, id_: str, tipo: str, nome: str, fonte: str, *, projeto=None, data=None, **dados):
        if id_ in self.nos:
            self.nos[id_]["dados"].update({k: v for k, v in dados.items() if v not in (None, "", [], {})})
            return
        self.nos[id_] = {"id": id_, "tipo": tipo, "nome": nome or id_.split(":", 1)[1], "projeto": projeto,
                         "data": data, "fonte": fonte,
                         "dados": {k: v for k, v in dados.items() if v not in (None, "", [], {})}}

    def aresta(self, origem: str, destino: str, tipo: str, fonte: str, **dados):
        if origem == destino:
            return
        self.arestas[(origem, destino, tipo)] = {"fonte": fonte, "dados": dados}


def _json(v):
    if isinstance(v, (dt.datetime, dt.date)):
        return v.isoformat()
    if hasattr(v, "__float__") and not isinstance(v, (int, float, bool)):
        return float(v)
    raise TypeError(type(v))


def construir(raiz: Path, projetos: list[Projeto], painel: dict[str, list[dict]], cat: Catalogo,
              documentos: list[dict], trechos: list[dict]) -> Grafo:
    g = Grafo()
    pid = {p.id for p in projetos}

    # projetos
    for p in projetos:
        g.no(f"projeto:{p.id}", "projeto", p.nome, "estudio-contexto/projetos.yaml", projeto=p.id,
             descricao=p.descricao, pastas=p.pastas, instrucoes=p.instrucoes)
    for p in projetos:
        if p.pai:
            g.aresta(f"projeto:{p.id}", f"projeto:{p.pai}", "pertence_a", "estudio-contexto/projetos.yaml")
        for d in p.depende_de:
            g.aresta(f"projeto:{p.id}", f"projeto:{d}", "depende_de", "estudio-contexto/projetos.yaml")
    proj_do_dep = {d: p.id for p in projetos for d in p.departamentos}

    # departamentos
    for d in painel["departamentos"]:
        g.no(f"departamento:{d['id']}", "departamento", d["nome"], "painel.departamentos",
             projeto=proj_do_dep.get(d["id"]), descricao=d["descricao"], gerente=d["gerente_id"])

    # agentes
    arquivos = ler_agentes_arquivos(raiz)
    painel_ag = {a["id"]: a for a in painel["agentes"]}
    for aid in sorted(set(painel_ag) | set(arquivos)):
        a, f = painel_ag.get(aid, {}), arquivos.get(aid, {})
        projeto = proj_do_dep.get(a.get("departamento_id"))
        g.no(f"agente:{aid}", "agente", aid, f.get("arquivo") or "painel.agentes", projeto=projeto,
             nome_pessoa=a.get("nome"), cargo=a.get("cargo"), departamento=a.get("departamento_id"),
             papel=a.get("papel"), descricao=f.get("descricao") or a.get("resumo"),
             modelo=f.get("modelo") or a.get("modelo"), arquivo=f.get("arquivo"),
             fiscalizado_por=a.get("fiscalizado_por"), sem_arquivo=(not f) or None)
        if a.get("departamento_id"):
            g.aresta(f"agente:{aid}", f"departamento:{a['departamento_id']}", "membro_de", "painel.agentes")
        if projeto:
            g.aresta(f"agente:{aid}", f"projeto:{projeto}", "pertence_a", "painel/equipe.yaml + projetos.yaml")
    for d in painel["departamentos"]:
        if d["gerente_id"] and f"agente:{d['gerente_id']}" in g.nos:
            g.aresta(f"agente:{d['gerente_id']}", f"departamento:{d['id']}", "gerencia", "painel.departamentos")

    # portões (o agente que audita) e quem cada um fiscaliza
    areas: dict[str, set[str]] = {}
    for e in painel["portoes_estado"]:
        areas.setdefault(e["agente"], set()).add(e["portao"])
    for a in painel["agentes"]:
        if a["fiscaliza"]:
            areas.setdefault(a["id"], set())
    for a in painel["agentes"]:
        if a["fiscalizado_por"]:
            areas.setdefault(a["fiscalizado_por"], set())
    for gid, ar in areas.items():
        g.no(f"portao:{gid}", "portao", gid, "painel.portoes_estado", projeto=proj_do_dep.get(
            painel_ag.get(gid, {}).get("departamento_id")), agente=gid, areas=sorted(ar))
    for a in painel["agentes"]:
        for alvo in a["fiscaliza"] or []:
            g.aresta(f"portao:{a['id']}", f"agente:{alvo}", "fiscaliza", "painel.agentes.fiscaliza")
        if a["fiscalizado_por"]:
            g.aresta(f"portao:{a['fiscalizado_por']}", f"agente:{a['id']}", "fiscaliza",
                     "painel.agentes.fiscalizado_por")

    # vídeos
    painel_v = {v["slug"]: v for v in painel["videos"]}
    for slug in sorted(cat.videos):
        v = painel_v.get(slug, {})
        projeto = "ai-engineer" if v.get("pilar") == "ai-engineer" and "ai-engineer" in pid else "estudio"
        g.no(f"video:{slug}", "video", slug, "painel.videos" if v else f"videos/{slug}/", projeto=projeto,
             data=dt.date.fromisoformat(slug[:10]), tema=v.get("tema"), pilar=v.get("pilar"),
             estado=v.get("estado"), estrutura=v.get("estrutura"), cta_palavra=v.get("cta_palavra"),
             nome_curto=v.get("nome_curto"), roteiro_versao=v.get("roteiro_versao"),
             atualizado=v.get("atualizado"), gravacao_prevista=v.get("gravacao_prevista"),
             pasta=f"videos/{slug}/")
        g.aresta(f"video:{slug}", f"projeto:{projeto}", "pertence_a", "painel.videos.pilar")

    def alvo_id(alvo: str, slug: str | None) -> str | None:
        if alvo == "painel":
            return "projeto:painel"
        if slug and f"video:{slug}" in g.nos:
            return f"video:{slug}"
        return None

    for e in painel["portoes_estado"]:
        destino = alvo_id(e["alvo"], e["slug"])
        if destino:
            g.aresta(f"portao:{e['agente']}", destino, "avalia", "painel.portoes_estado", portao=e["portao"],
                     status=e["status"], volta=e["volta"], motivos=e["motivos"])

    # veredictos
    for v in painel["veredictos"]:
        destino = alvo_id(v["alvo"], v["slug"])
        vid = f"veredicto:{v['alvo']}|{v['portao']}|{v['ordem']}"
        quem = v["slug"] or v["alvo"]
        g.no(vid, "veredicto", f"{v['resultado']} · {v['portao']} · volta {v['volta']} · {quem}", "painel.veredictos",
             projeto="painel" if v["alvo"] == "painel" else "estudio", data=v["em"].date() if v["em"] else None,
             resultado=v["resultado"], portao=v["portao"], agente=v["agente"], volta=v["volta"], s0=v["s0"],
             s1=v["s1"], s2=v["s2"], relatorio=v["relatorio"], nota=v["nota"], decisao_autor=v["decisao_autor"],
             em=v["em"], alvo=v["alvo"])
        if f"portao:{v['agente']}" not in g.nos:
            g.no(f"portao:{v['agente']}", "portao", v["agente"], "painel.veredictos", agente=v["agente"],
                 areas=[v["portao"]])
        g.aresta(f"portao:{v['agente']}", vid, "emitiu", "painel.veredictos")
        if destino:
            tipo = "aprovou" if v["resultado"] == "APROVADO" else "bloqueou"
            g.aresta(vid, destino, tipo, "painel.veredictos.resultado", resultado=v["resultado"])

    # publicações + métricas (valor dentro do nó)
    met = {m["slug"]: {k: val for k, val in m.items() if k != "slug" and val is not None} for m in painel["metricas"]}
    for p in painel["publicacoes"]:
        g.no(f"publicacao:{p['slug']}", "publicacao", p["slug"], "painel.publicacoes", projeto="estudio",
             data=p["publicado_em"].date() if p["publicado_em"] else None, publicado_em=p["publicado_em"],
             tema=p["tema"], palavra=p["palavra"], duracao_s=p["duracao_s"], trial=p["trial"],
             plataformas=p["plataformas"], estado=p["estado"], permalink_instagram=p["permalink_instagram"],
             permalink_facebook=p["permalink_facebook"], metricas=met.get(p["slug"]), pasta=f"07-publicados/{p['slug']}/")
        if p["video_slug"] and f"video:{p['video_slug']}" in g.nos:
            g.aresta(f"video:{p['video_slug']}", f"publicacao:{p['slug']}", "publicado_como",
                     "painel.publicacoes.video_slug")

    # decisões
    for d in [*cat.decisoes, *cat.pds.values()]:
        g.no(d.id, "decisao", d.nome, d.fonte, projeto="painel" if d.codigo else None, data=d.data,
             codigo=d.codigo, secao=d.secao, **d.dados)
        for ent in cat.entidades(d.texto):
            if ent in g.nos and not ent.startswith("decisao:"):
                g.aresta(d.id, ent, "decide_sobre", d.fonte)
        if d.codigo:
            g.aresta(d.id, "projeto:painel", "decide_sobre", d.fonte)

    # documentos e trechos
    for doc in documentos:
        did = f"documento:{doc['caminho']}"
        g.no(did, "documento", doc["caminho"], doc["caminho"], projeto=doc["projeto"],
             data=doc["modificado"].date() if doc.get("modificado") else None, tipo_doc=doc["tipo"])
        g.aresta(did, f"projeto:{doc['projeto']}", "pertence_a", "projetos.yaml (pastas)")
        slug = video_do_caminho(doc["caminho"])
        if slug and f"video:{slug}" in g.nos:
            g.aresta(did, f"video:{slug}", "pertence_a", "caminho")
    relatorios = {n["dados"].get("relatorio"): i for i, n in g.nos.items() if n["tipo"] == "veredicto"}
    for caminho, vid in relatorios.items():
        if caminho and f"documento:{caminho}" in g.nos:
            g.aresta(f"documento:{caminho}", vid, "menciona", "painel.veredictos.relatorio")
    for t in trechos:
        tid = f"trecho:{t['id']}"
        did = f"documento:{t['caminho']}"
        g.no(tid, "trecho", t["secao"] or _resumo(t["texto"], 60), t["caminho"], data=t["data"],
             caminho=t["caminho"], secao=t["secao"], ordem=t["ordem"])
        g.aresta(did, tid, "contem", "chunking")
        for ent in t["entidades"]:
            if ent.startswith("decisao:PD") and ent not in g.nos:
                g.no(ent, "decisao", ent.split(":", 1)[1], t["caminho"], projeto="painel", codigo=ent.split(":", 1)[1])
            if ent in g.nos and ent != did:
                g.aresta(did, ent, "menciona", "texto do documento")
    return g


def gravar(con: psycopg.Connection, g: Grafo) -> tuple[int, int]:
    with con.transaction():
        con.execute("delete from contexto.arestas")
        con.execute("delete from contexto.nos")
        with con.cursor().copy("copy contexto.nos (id, tipo, nome, projeto, data, fonte, dados) from stdin") as cp:
            for n in g.nos.values():
                cp.write_row((n["id"], n["tipo"], n["nome"], n["projeto"], n["data"], n["fonte"],
                              json.dumps(n["dados"], ensure_ascii=False, default=_json)))
        with con.cursor().copy("copy contexto.arestas (origem, destino, tipo, fonte, dados) from stdin") as cp:
            for (o, d, t), a in g.arestas.items():
                if o in g.nos and d in g.nos:
                    cp.write_row((o, d, t, a["fonte"], json.dumps(a["dados"], ensure_ascii=False, default=_json)))
    n = con.execute("select (select count(*) from contexto.nos), (select count(*) from contexto.arestas)").fetchone()
    return n[0], n[1]
