"""Busca híbrida (vetorial + textual + entidades do grafo) com RRF e expansão pelo grafo (ESPECIFICACAO.md §6).

Três listas ordenadas entram na fusão RRF (score = Σ 1 / (60 + posição)):
  1. vetorial: distância de cosseno no índice HNSW (`query: ` + pergunta);
  2. textual:  tsvector `contexto.pt` (português sem acento), termos em OU, ts_rank_cd;
  3. entidades: trechos que citam as entidades nomeadas na pergunta (slug de vídeo, agente, PD…) — o grafo
     entra aqui e na expansão.
Depois, cada trecho recebe os nós ligados: as entidades que ele cita e os vizinhos do documento (profundidade 1).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import psycopg

from .embeddings import embedder
from .seguranca import excluido, mascarar, tokens_no_texto

RRF_K = 60
GARANTIR_TOPO = 1  # quantos primeiros de cada lista (vetorial, textual) entram sempre no resultado
TIPOS_DE_NO = {"projeto", "agente", "departamento", "video", "publicacao", "portao", "veredicto", "decisao",
               "documento", "trecho"}


@dataclass
class Filtros:
    projeto: str | None = None
    tipo: str | None = None
    agente: str | None = None
    desde: str | None = None   # AAAA-MM-DD
    ate: str | None = None

    def sql(self, con: psycopg.Connection) -> tuple[str, list]:
        w, p = [], []
        if self.projeto:
            projs = [r[0] for r in con.execute(
                "select split_part(id, ':', 2) from contexto.nos where tipo = 'projeto' and (id = %s or id in ("
                "select origem from contexto.arestas where destino = %s and tipo = 'pertence_a' "
                "and origem like 'projeto:%%'))", (f"projeto:{self.projeto}", f"projeto:{self.projeto}"))]
            w.append("d.projeto = any(%s)")
            p.append(projs or [self.projeto])
        if self.tipo:
            if self.tipo in TIPOS_DE_NO:
                w.append("exists (select 1 from unnest(t.entidades) e where e like %s)")
                p.append(f"{self.tipo}:%")
            else:
                w.append("t.tipo = %s")
                p.append(self.tipo)
        if self.agente:
            w.append("(%s = any(t.entidades) or t.caminho = %s)")
            p += [f"agente:{self.agente}", f".claude/agents/{self.agente}.md"]
        if self.desde:
            w.append("t.data >= %s::date")
            p.append(self.desde)
        if self.ate:
            w.append("t.data <= %s::date")
            p.append(self.ate)
        return (" and ".join(w) or "true"), p


def entidades_da_consulta(con: psycopg.Connection, consulta: str) -> list[str]:
    """Ids de nós nomeados na pergunta: PD12, slug ou parte do slug de vídeo, nome de agente."""
    ids = {f"decisao:{c.upper()}" for c in re.findall(r"\b[Pp][Dd]\d{1,3}\b", consulta)}
    termos = [t for t in re.findall(r"[a-z0-9][a-z0-9-]{3,}", consulta.lower()) if "-" in t]
    for t in termos:
        for (i,) in con.execute("select id from contexto.nos where tipo in ('video', 'agente') and "
                                "(nome = %s or nome like %s)", (t, f"%-{t}")).fetchall():
            ids.add(i)
    for (i,) in con.execute("select id from contexto.nos where tipo = 'agente' and %s ~* ('(^|[^a-z-])' || "
                            "replace(nome, '-', '\\-') || '($|[^a-z-])')", (consulta,)).fetchall():
        ids.add(i)
    existentes = {r[0] for r in con.execute("select id from contexto.nos where id = any(%s)", (list(ids),))}
    return sorted(existentes)


# palavras de pergunta que o stemmer português não descarta e que, numa busca em OU, só trazem ruído
PALAVRAS_DE_PERGUNTA = {"quant", "qual", "quai", "pod", "ter", "ser", "faz", "fez", "sobr", "usar", "usad", "dev",
                        "pra", "par", "est", "tem", "tinh", "foi", "sao", "algum", "onde", "quand", "com", "porqu",
                        "hoj", "ainda", "aind", "agor", "nao", "sim", "fic", "dess", "dest", "ness", "nest"}


def consulta_textual(con: psycopg.Connection, consulta: str) -> str:
    """tsquery em OU com os lexemas da pergunta, sem as palavras de pergunta."""
    lexemas = con.execute("select array(select unnest(tsvector_to_array(to_tsvector('contexto.pt', %s))))",
                          (consulta,)).fetchone()[0] or []
    uteis = [x for x in lexemas if x not in PALAVRAS_DE_PERGUNTA and len(x) > 1]
    return " | ".join("'" + x.replace("'", "''") + "'" for x in (uteis or lexemas))


def datas_da_consulta(consulta: str) -> list:
    from .chunking import RX_DATA_BR, RX_DATA_ISO, ANO_PADRAO
    import datetime as dt
    saida = []
    for m in RX_DATA_ISO.finditer(consulta):
        try:
            saida.append(dt.date(int(m[1]), int(m[2]), int(m[3])))
        except ValueError:
            pass
    for m in RX_DATA_BR.finditer(consulta):
        try:
            saida.append(dt.date(int(m[3] or ANO_PADRAO), int(m[2]), int(m[1])))
        except ValueError:
            pass
    return saida


def _rrf(listas: list[list[str]], pesos: list[float]) -> dict[str, float]:
    score: dict[str, float] = {}
    for lista, peso in zip(listas, pesos):
        for pos, tid in enumerate(lista):
            score[tid] = score.get(tid, 0.0) + peso / (RRF_K + pos + 1)
    return score


def _recorte(texto: str, consulta: str, n: int = 420) -> str:
    texto = re.sub(r"\s+", " ", texto).strip()
    if len(texto) <= n:
        return texto
    palavras = [w for w in re.findall(r"\w{4,}", consulta.lower())]
    baixo = texto.lower()
    pos = min((baixo.find(w) for w in palavras if baixo.find(w) >= 0), default=0)
    ini = max(0, pos - n // 4)
    return ("…" if ini else "") + texto[ini:ini + n].strip() + "…"


def buscar(con: psycopg.Connection, consulta: str, filtros: Filtros | None = None, limite: int = 8,
           k: int = 40, expandir: bool = True) -> list[dict]:
    filtros = filtros or Filtros()
    where, params = filtros.sql(con)
    q = embedder().consulta(consulta)
    con.execute("set hnsw.ef_search = 200")
    try:
        con.execute("set hnsw.iterative_scan = relaxed_order")
    except psycopg.Error:
        pass

    vetorial = [r[0] for r in con.execute(
        f"select t.id from contexto.trechos t join contexto.documentos d using (caminho) where {where} "
        f"order by t.embedding <=> %s limit %s", [*params, q, k]).fetchall()]

    tsq = consulta_textual(con, consulta)
    textual = []
    if tsq:
        textual = [r[0] for r in con.execute(
            f"select t.id from contexto.trechos t join contexto.documentos d using (caminho), "
            f"to_tsquery('contexto.pt', %s) q where t.tsv @@ q and {where} "
            f"order by ts_rank_cd(t.tsv, q, 32) desc limit %s", [tsq, *params, k]).fetchall()]

    ents = entidades_da_consulta(con, consulta)
    por_entidade = []
    if ents:
        por_entidade = [r[0] for r in con.execute(
            f"select t.id from contexto.trechos t join contexto.documentos d using (caminho) "
            f"where t.entidades && %s and {where} order by t.embedding <=> %s limit %s",
            [ents, *params, q, k]).fetchall()]

    # datas citadas na pergunta ("em 22/10", "2026-11-10"): trechos datados de até 1 dia antes/depois
    datas = datas_da_consulta(consulta)
    por_data = []
    if datas:
        por_data = [r[0] for r in con.execute(
            f"select t.id from contexto.trechos t join contexto.documentos d using (caminho) "
            f"where exists (select 1 from unnest(%s::date[]) x where t.data between x - 1 and x + 1) and {where} "
            f"order by t.embedding <=> %s limit %s", [datas, *params, q, k]).fetchall()]

    score = _rrf([vetorial, textual, por_entidade, por_data], [1.0, 1.0, 0.8, 0.8])
    ordem = sorted(score, key=lambda i: -score[i])
    # A RRF premia quem aparece nas duas listas; o 1.º lugar isolado de uma lista (ex.: o vetor acha a regra exata,
    # mas as palavras não batem) cairia para fora do topo. Garante o topo de cada lista entre os resultados.
    garantidos = [t for lista in (vetorial, textual) for t in lista[:GARANTIR_TOPO]]
    topo = ordem[:limite]
    for tid in dict.fromkeys(garantidos):
        if tid in topo:
            continue
        # sai o último do topo que não é garantido
        sai = next((t for t in reversed(topo) if t not in garantidos), None)
        if sai is None:
            break
        topo[topo.index(sai)] = tid
    ordem = topo + [t for t in ordem if t not in topo]
    if not ordem:
        return []
    linhas = {r[0]: r for r in con.execute(
        "select t.id, t.caminho, t.secao, t.texto, t.tipo, t.data, t.entidades, d.projeto "
        "from contexto.trechos t join contexto.documentos d using (caminho) where t.id = any(%s)",
        (ordem[: limite * 3],)).fetchall()}

    saida = []
    for tid in ordem:
        if tid not in linhas:
            continue
        _, caminho, secao, texto, tipo, data, entidades, projeto = linhas[tid]
        # defesa em profundidade (§7): nada de arquivo excluído nem trecho com token sai daqui
        if excluido(caminho) or tokens_no_texto(texto):
            continue
        saida.append({"id": tid, "fonte": caminho, "secao": secao, "tipo": tipo, "projeto": projeto,
                      "data": data.isoformat() if data else None, "score": round(score[tid], 5),
                      "trecho": mascarar(_recorte(texto, consulta)), "entidades": list(entidades)})
        if len(saida) >= limite:
            break
    if expandir:
        for r in saida:
            r["nos_ligados"] = nos_ligados(con, r["fonte"], r.pop("entidades"))
    return saida


def nos_ligados(con: psycopg.Connection, caminho: str, entidades: list[str], limite: int = 10) -> list[dict]:
    """Entidades citadas no trecho + vizinhos do documento (profundidade 1), sem documentos/trechos."""
    linhas = con.execute(
        "with viz as ("
        "  select destino as id, 0 as pri from contexto.arestas where origem = %(doc)s and tipo <> 'contem' "
        "  union select origem, 1 from contexto.arestas where destino = %(doc)s and tipo <> 'contem' "
        "  union select unnest(%(ents)s::text[]), -1) "
        "select n.id, n.tipo, n.nome, min(v.pri) p from viz v join contexto.nos n on n.id = v.id "
        "where n.tipo not in ('trecho', 'documento') group by 1, 2, 3 order by p, n.tipo, n.id limit %(lim)s",
        {"doc": f"documento:{caminho}", "ents": entidades, "lim": limite}).fetchall()
    return [{"id": i, "tipo": t, "nome": n} for i, t, n, _ in linhas]


# ───────────────────────────── grafo ─────────────────────────────

PRIORIDADE_TIPO = ["projeto", "agente", "portao", "video", "decisao", "departamento", "publicacao", "veredicto",
                   "documento", "trecho"]


def resolver_no(con: psycopg.Connection, termo: str, tipos: list[str] | None = None) -> str | None:
    termo = termo.strip()
    filtro = "and tipo = any(%(tipos)s)" if tipos else ""
    args = {"t": termo, "tl": termo.lower(), "tipos": tipos, "pri": PRIORIDADE_TIPO}
    for sql in (
        f"select id from contexto.nos where id = %(t)s {filtro}",
        f"select id from contexto.nos where (lower(nome) = %(tl)s or id = 'decisao:' || upper(%(t)s)) {filtro} "
        f"order by array_position(%(pri)s, tipo)",
        f"select id from contexto.nos where tipo = 'video' and nome like '%%-' || %(tl)s {filtro}",
        f"select id from contexto.nos where tipo not in ('trecho') and lower(nome) like '%%' || %(tl)s || '%%' "
        f"{filtro} order by array_position(%(pri)s, tipo), length(nome)",
    ):
        r = con.execute(sql + " limit 1", args).fetchone()
        if r:
            return r[0]
    return None


def vizinhos(con: psycopg.Connection, no_id: str, profundidade: int = 1, incluir_trechos: bool = False,
             limite: int = 80) -> dict:
    profundidade = max(1, min(int(profundidade), 3))
    excluir = [] if incluir_trechos else ["trecho"]
    nos = con.execute(
        "with recursive viz(id, nivel) as ("
        "  select %(id)s::text, 0 "
        "  union "
        "  select case when a.origem = v.id then a.destino else a.origem end, v.nivel + 1 "
        "  from viz v join contexto.arestas a on (a.origem = v.id or a.destino = v.id) "
        "  where v.nivel < %(prof)s and (%(trechos)s or a.tipo <> 'contem')) "
        "select n.id, n.tipo, n.nome, min(v.nivel) nivel, n.fonte, n.data from viz v join contexto.nos n using (id) "
        "where n.tipo <> all(%(excl)s) or n.id = %(id)s "
        "group by n.id, n.tipo, n.nome, n.fonte, n.data order by nivel, n.tipo, n.id limit %(lim)s",
        {"id": no_id, "prof": profundidade, "trechos": incluir_trechos, "excl": excluir, "lim": limite}).fetchall()
    ids = [r[0] for r in nos]
    arestas = con.execute(
        "select origem, tipo, destino, fonte from contexto.arestas where origem = any(%s) and destino = any(%s) "
        "order by tipo, origem, destino", (ids, ids)).fetchall()
    return {"centro": no_id,
            "nos": [{"id": i, "tipo": t, "nome": n, "distancia": d, "fonte": f, "data": dt.isoformat() if dt else None}
                    for i, t, n, d, f, dt in nos],
            "arestas": [{"de": o, "tipo": t, "para": d, "fonte": f} for o, t, d, f in arestas]}
