"""Conexões e migrações do schema `contexto`."""
from __future__ import annotations

from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector
from psycopg.conninfo import conninfo_to_dict

from . import config


def _conferir_porta(url: str) -> None:
    porta = int(conninfo_to_dict(url).get("port") or 5432)
    if porta in config.PORTAS_PROIBIDAS:
        raise RuntimeError(f"porta {porta} é do outro projeto local (543xx): o contexto só usa o banco do painel (553xx)")


def conectar(url: str | None = None, *, leitura: bool = False) -> psycopg.Connection:
    """Conexão de escrita (sincronizador) ou de leitura (MCP: transação só-leitura + papel contexto_leitor)."""
    url = url or config.DB_URL
    _conferir_porta(url)
    opcoes = "-c default_transaction_read_only=on" if leitura else None
    con = psycopg.connect(url, connect_timeout=5, options=opcoes, autocommit=leitura)
    if leitura:
        try:
            con.execute("set role contexto_leitor")
        except psycopg.Error:
            con.close()
            raise
    con.execute("set search_path = contexto, extensions, public")
    _registrar_vector(con)
    return con


def _registrar_vector(con: psycopg.Connection) -> None:
    """Ensina o psycopg o tipo vector (se a extensão ainda não existe, a migração 001 cria e chama de novo)."""
    try:
        register_vector(con)
    except psycopg.ProgrammingError:
        if not con.autocommit:
            con.rollback()


def migrar(con: psycopg.Connection, pasta: Path = config.MIGRACOES) -> list[str]:
    """Aplica as migrações que faltam, em ordem, cada uma na sua transação. Devolve as aplicadas agora."""
    tem = con.execute("select to_regclass('contexto.migracoes') is not null").fetchone()[0]
    feitas = {r[0] for r in con.execute("select versao from contexto.migracoes")} if tem else set()
    con.commit()
    aplicadas = []
    for arq in sorted(pasta.glob("*.sql")):
        versao = arq.stem
        if versao in feitas:
            continue
        with con.transaction():
            con.execute(arq.read_text(encoding="utf-8"))
            con.execute("insert into contexto.migracoes (versao) values (%s)", (versao,))
        aplicadas.append(versao)
    # o papel de leitura enxerga também as tabelas criadas por migrações futuras
    with con.transaction():
        con.execute("grant select on all tables in schema contexto to contexto_leitor")
    _registrar_vector(con)
    return aplicadas
