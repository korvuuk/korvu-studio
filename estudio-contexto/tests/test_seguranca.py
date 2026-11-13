"""Teste obrigatório de vazamento (§7, §9) contra o ÍNDICE REAL, numa conexão só-leitura.

Lê as chaves do `.env` do estúdio SÓ para comparar: os valores nunca são impressos (nem em falha — a mensagem só
conta quantos e diz o NOME da variável). Valores curtos (< 12 caracteres: portas, true/false, caminhos curtos)
ficam de fora para não acusar falso positivo.
Pula se o índice real ainda não existe ou se o `.env` não está lá.
"""
from __future__ import annotations

from pathlib import Path

import psycopg
import pytest

from contexto.seguranca import motivo_exclusao

ESTUDIO = Path(__file__).resolve().parents[2]
REAL = "postgresql://postgres:postgres@127.0.0.1:55322/postgres"


def _valores_do_env() -> dict[str, str]:
    saida = {}
    for arq in (ESTUDIO / ".env", ESTUDIO / "painel" / "web" / ".env.local"):
        if not arq.exists():
            continue
        for ln in arq.read_text(encoding="utf-8", errors="replace").splitlines():
            ln = ln.strip()
            if not ln or ln.startswith("#") or "=" not in ln:
                continue
            k, v = ln.split("=", 1)
            v = v.strip().strip('"').strip("'")
            if len(v) >= 12:
                saida[k.strip().removeprefix("export ").strip()] = v
    return saida


@pytest.fixture(scope="module")
def real():
    try:
        c = psycopg.connect(REAL, connect_timeout=3, options="-c default_transaction_read_only=on")
    except psycopg.OperationalError:
        pytest.skip("Postgres do painel desligado")
    if not c.execute("select to_regclass('contexto.trechos') is not null").fetchone()[0]:
        pytest.skip("índice real ainda não criado")
    c.execute("set role contexto_leitor")
    yield c
    c.close()


def test_nenhum_valor_do_env_no_indice(real):
    valores = _valores_do_env()
    if not valores:
        pytest.skip(".env sem valores longos")
    vazaram = [k for k, v in valores.items()
               if real.execute("select exists (select 1 from contexto.trechos where strpos(texto, %s) > 0 "
                               "or strpos(secao, %s) > 0)", (v, v)).fetchone()[0]]
    assert not vazaram, f"{len(vazaram)} valor(es) do .env no índice — variáveis: {', '.join(vazaram)}"


def test_nenhum_arquivo_excluido_ou_midia_no_indice(real):
    caminhos = [r[0] for r in real.execute("select caminho from contexto.documentos")]
    assert caminhos, "índice vazio"
    ruins = [c for c in caminhos if motivo_exclusao(c)]
    assert not ruins, ruins


def test_nenhum_padrao_de_token_no_indice(real):
    from contexto.seguranca import tokens_no_texto
    com_token = [i for i, t in real.execute("select id, texto from contexto.trechos") if tokens_no_texto(t)]
    assert not com_token, com_token
