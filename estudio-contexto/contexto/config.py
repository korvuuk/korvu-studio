"""Configuração do módulo: raiz do estúdio, banco e modelo.

Nada aqui é segredo. O banco é o Postgres LOCAL do painel (127.0.0.1:55322, usuário padrão do Supabase local, o
mesmo que `painel/sync/sincronizar.py` usa). Para apontar para outro banco, defina `CONTEXTO_DB_URL` no ambiente.
O `.env` do estúdio nunca é lido por este módulo.
"""
from __future__ import annotations

import os
from pathlib import Path

MODULO = Path(__file__).resolve().parents[1]                     # .../Korvu Studio/estudio-contexto
RAIZ = Path(os.environ.get("CONTEXTO_RAIZ") or MODULO.parent).resolve()  # .../Korvu Studio

DB_URL = os.environ.get("CONTEXTO_DB_URL") or "postgresql://postgres:postgres@127.0.0.1:55322/postgres"
# De onde o grafo lê as tabelas do painel (só leitura). Padrão: o mesmo banco.
PAINEL_DB_URL = os.environ.get("CONTEXTO_PAINEL_DB_URL") or DB_URL

MIGRACOES = MODULO / "migrations"
PROJETOS_YAML = Path(os.environ.get("CONTEXTO_PROJETOS") or MODULO / "projetos.yaml")
CORPUS_YAML = Path(os.environ.get("CONTEXTO_CORPUS") or MODULO / "corpus.yaml")

MODELO = os.environ.get("CONTEXTO_MODELO") or "intfloat/multilingual-e5-small"
DIMENSOES = 384
PREFIXO_TRECHO = "passage: "
PREFIXO_CONSULTA = "query: "

# Portas proibidas (outro projeto local). O módulo recusa conectar nelas.
PORTAS_PROIBIDAS = range(54300, 54400)
