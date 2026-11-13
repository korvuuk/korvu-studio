"""Integração (§11): banco temporário, migrações do zero, indexação, idempotência, consultas e o MCP só-leitura."""
from __future__ import annotations

import json

import psycopg
import pytest
from conftest import BANCO, FALSO_SEGREDO, escrever

from contexto import consultas
from contexto.busca import Filtros, buscar
from contexto.db import conectar
from contexto.sincronizar import sincronizar


def _estado(con) -> dict:
    return {r[0]: (r[1], r[2]) for r in con.execute("select id, hash, ordem from contexto.trechos")}


def test_migracoes_do_zero(sincronizado):
    with psycopg.connect(BANCO) as c:
        assert c.execute("select versao from contexto.migracoes").fetchall() == [("001_schema_contexto",)]
        tabelas = {r[0] for r in c.execute("select table_name from information_schema.tables "
                                           "where table_schema = 'contexto'")}
        assert {"nos", "arestas", "documentos", "trechos", "migracoes", "sincronizacoes"} <= tabelas
        idx = {r[0] for r in c.execute("select indexdef from pg_indexes where schemaname = 'contexto'")}
        assert any("hnsw" in i and "vector_cosine_ops" in i for i in idx)
        assert any("gin (tsv)" in i for i in idx)
        # as tabelas do "painel" continuam intactas
        assert c.execute("select count(*) from public.veredictos").fetchone()[0] == 3


def test_indexacao_e_exclusoes(sincronizado):
    assert sincronizado["trechos"] > 5
    assert any("dossie.md (token: openai)" in x for x in sincronizado["excluidos"])
    with psycopg.connect(BANCO) as c:
        caminhos = {r[0] for r in c.execute("select caminho from contexto.documentos")}
        assert "videos/2026-11-01-teste-um/material/dossie.md" not in caminhos
        assert not any(".env" in x or x.endswith(".mp4") or "/brutos/" in x for x in caminhos)
        n = c.execute("select count(*) from contexto.trechos where texto like %s",
                      (f"%{FALSO_SEGREDO}%",)).fetchone()[0]
        assert n == 0
        assert c.execute("select count(*) from contexto.trechos where texto like 'passage:%'").fetchone()[0] == 0


def test_idempotencia_rodar_duas_vezes_nao_muda_nada(sincronizado):
    with psycopg.connect(BANCO) as c:
        antes = _estado(c)
        nos_antes = c.execute("select count(*), md5(string_agg(id || dados::text, ',' order by id)) "
                              "from contexto.nos").fetchone()
    r = sincronizar(log=lambda *_: None)
    assert r["embedados"] == 0 and r["removidos"] == 0
    with psycopg.connect(BANCO) as c:
        assert _estado(c) == antes
        assert c.execute("select count(*), md5(string_agg(id || dados::text, ',' order by id)) "
                         "from contexto.nos").fetchone() == nos_antes


def test_reindexacao_incremental(sincronizado):
    rel = "HANDOFF.md"
    with psycopg.connect(BANCO) as c:
        antes = {r[0] for r in c.execute("select id from contexto.trechos where caminho = %s", (rel,))}
    original = (escrever.__globals__["RAIZ"] / rel).read_text(encoding="utf-8")
    escrever(rel, original.replace("duas páginas", "três páginas"))
    try:
        r = sincronizar(log=lambda *_: None)
        with psycopg.connect(BANCO) as c:
            depois = {r_[0] for r_ in c.execute("select id from contexto.trechos where caminho = %s", (rel,))}
        assert r["embedados"] == 1 and r["removidos"] == 1     # só o trecho que mudou
        assert len(antes & depois) == len(antes) - 1
    finally:
        escrever(rel, original)
        sincronizar(log=lambda *_: None)


def test_arquivo_apagado_sai_do_indice(sincronizado):
    rel = "painel/portoes/dados-2026-11-10-v1.md"
    p = escrever.__globals__["RAIZ"] / rel
    conteudo = p.read_text(encoding="utf-8")
    p.unlink()
    try:
        r = sincronizar(log=lambda *_: None)
        assert r["removidos"] >= 1
        with psycopg.connect(BANCO) as c:
            assert c.execute("select count(*) from contexto.trechos where caminho = %s", (rel,)).fetchone()[0] == 0
            assert c.execute("select count(*) from contexto.nos where id = %s",
                             (f"documento:{rel}",)).fetchone()[0] == 0
    finally:
        escrever(rel, conteudo)
        sincronizar(log=lambda *_: None)


def test_grafo_derivado_do_painel(con_leitura):
    tipos = dict(con_leitura.execute("select tipo, count(*) from contexto.nos group by 1").fetchall())
    assert tipos["video"] == 1 and tipos["veredicto"] == 3 and tipos["publicacao"] == 1 and tipos["projeto"] == 8
    v = consultas.contexto_do_video(con_leitura, "teste-um")
    assert v["video"]["estado"] == "roteiro" and v["video"]["pilar"] == "perfil"
    assert [x["resultado"] for x in v["veredictos"]] == ["APROVADO", "BLOQUEADO"]
    assert v["publicacoes"][0]["metricas"]["views"] == 900          # a leitura mais recente
    assert "videos/2026-11-01-teste-um/roteiro.md" in v["documentos"]
    assert any(d["id"] == "decisao:dec-1-01" for d in v["decisoes"])


def test_vizinhanca_recursiva(con_leitura):
    r = consultas.vizinhanca(con_leitura, "PD9", 1)
    ids = {n["id"] for n in r["nos"]}
    assert r["centro"] == "decisao:PD9" and "projeto:painel" in ids
    assert "documento:painel/README.md" in ids and not any(i.startswith("trecho:") for i in ids)
    r2 = consultas.vizinhanca(con_leitura, "decisao:PD9", 2)
    assert len(r2["nos"]) > len(r["nos"])
    assert all(a["de"] in {n["id"] for n in r2["nos"]} for a in r2["arestas"])


def test_quem_fiscaliza_e_projeto(con_leitura):
    q = consultas.quem_fiscaliza(con_leitura, "roteirista")
    assert q["fiscalizado_por"][0]["portao"] == "revisor-de-roteiro"
    assert len(q["fiscalizado_por"][0]["veredictos_recentes"]) == 2
    q2 = consultas.quem_fiscaliza(con_leitura, "revisor-de-roteiro")
    assert q2["e_portao_de"] == ["agente:roteirista"]
    p = consultas.contexto_do_projeto(con_leitura, "painel")
    assert "projeto:estudio" in p["depende_de"] and any(a["id"] == "agente:portao-dados" for a in p["agentes"])
    assert consultas.contexto_do_projeto(con_leitura, "não-existe")["erro"]


def test_busca_com_filtros_e_fonte(con_leitura):
    r = buscar(con_leitura, "PD9 rede só no Mac", limite=5)
    assert r and all(x["fonte"] and "trecho" in x and "nos_ligados" in x for x in r)
    assert any(n["id"] == "decisao:PD9" for x in r for n in x["nos_ligados"])
    so_painel = buscar(con_leitura, "banco", Filtros(projeto="painel"), limite=10)
    assert so_painel and all(x["projeto"] == "painel" for x in so_painel)
    datados = buscar(con_leitura, "sessão", Filtros(desde="2026-11-11", ate="2026-11-11"), limite=10)
    assert datados and all(x["data"] == "2026-11-11" for x in datados)
    roteiros = buscar(con_leitura, "IA", Filtros(tipo="video"), limite=10)
    assert roteiros and all(x["fonte"].startswith(("videos/", "HANDOFF", "docs/")) for x in roteiros)


def test_decisoes_sobre(con_leitura):
    d = consultas.decisoes_sobre(con_leitura, "música ElevenLabs")
    assert d["decisoes"][0]["id"] == "decisao:dec-1-02" and d["decisoes"][0]["fonte"] == "docs/decisoes.md"


def test_conexao_do_mcp_e_so_leitura(con_leitura):
    for sql in ("insert into contexto.migracoes values ('x')", "delete from contexto.nos",
                "select count(*) from public.veredictos"):
        with pytest.raises(psycopg.Error):
            con_leitura.execute(sql)
    con_leitura.execute("set default_transaction_read_only = off")   # mesmo tirando a trava da transação…
    with pytest.raises(psycopg.errors.InsufficientPrivilege):         # …o papel não tem INSERT
        con_leitura.execute("insert into contexto.migracoes values ('x')")


def test_mcp_nunca_devolve_arquivo_excluido(sincronizado):
    """Mesmo que um trecho de .env entre no banco por engano, a busca não o devolve (§7)."""
    with psycopg.connect(BANCO) as c:
        c.execute("insert into contexto.documentos (caminho, projeto, tipo, hash, bytes, modificado) "
                  "values ('.env', 'estudio', 'documento', 'x', 1, now())")
        v = c.execute("select embedding from contexto.trechos limit 1").fetchone()[0]
        c.execute("insert into contexto.trechos (id, caminho, ordem, secao, tipo, hash, texto, embedding) "
                  "values ('.env#x', '.env', 0, '', 'documento', 'x', %s, %s)",
                  (f"API_TESTE={FALSO_SEGREDO} segredo segredo", v))
        c.commit()
    try:
        con = conectar(leitura=True)
        r = consultas.busca(con, f"API_TESTE segredo {FALSO_SEGREDO}", limite=25)
        assert FALSO_SEGREDO not in json.dumps(r["resultados"]) and all(x["fonte"] != ".env" for x in r["resultados"])
        con.close()
    finally:
        with psycopg.connect(BANCO) as c:
            c.execute("delete from contexto.documentos where caminho = '.env'")
            c.commit()


def test_servidor_registra_as_seis_ferramentas():
    import asyncio

    from contexto import servidor
    nomes = {t.name for t in asyncio.run(servidor.mcp.list_tools())}
    assert nomes == {"contexto_do_projeto", "contexto_do_video", "buscar", "vizinhos", "decisoes_sobre",
                     "quem_fiscaliza"}


def test_privilegios_do_schema(sincronizado):
    """S1-1 do PORTÃO-DADOS (12/11): a API do Supabase (anon/authenticated/service_role) e o PUBLIC não enxergam o
    schema `contexto`; o papel do MCP só tem SELECT."""
    with psycopg.connect(BANCO) as c:
        papeis = [r[0] for r in c.execute("select rolname from pg_roles where rolname = any(%s)",
                                          (["anon", "authenticated", "service_role"],))]
        for papel in papeis:
            assert not c.execute("select has_schema_privilege(%s, 'contexto', 'USAGE')", (papel,)).fetchone()[0], papel
        assert not c.execute("select has_schema_privilege('public', 'contexto', 'USAGE')").fetchone()[0]
        grants = c.execute("select grantee, privilege_type from information_schema.role_table_grants "
                           "where table_schema = 'contexto' and grantee not in ('postgres', current_user)").fetchall()
        assert {g for g, _ in grants} == {"contexto_leitor"}, grants
        assert {p for _, p in grants} == {"SELECT"}, grants


def test_trava_de_transacao_so_leitura_sozinha(sincronizado):
    """S2-4: a transação só-leitura recusa escrita mesmo sem o papel de leitura (as duas travas valem sozinhas)."""
    con = conectar(leitura=True)
    try:
        con.execute("reset role")
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            con.execute("insert into contexto.migracoes values ('x')")
    finally:
        con.close()
