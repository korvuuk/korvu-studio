"""Fixtures dos testes (ESPECIFICACAO.md §11), no padrão de painel/tests/test_sincronizar.py:

- RAIZ TEMPORÁRIA com um estúdio de exemplo (nenhum arquivo real é lido como dado);
- BANCO DESCARTÁVEL `contexto_teste_<pid>` criado e apagado no mesmo Postgres do painel (127.0.0.1:55322), com as
  tabelas `public` do painel reduzidas às colunas que o grafo lê. O banco do autor (`postgres`) nunca é escrito;
- embedder FALSO (determinístico) — a qualidade da busca é medida em avaliacao/, não aqui.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

MODULO = Path(__file__).resolve().parents[1]
RAIZ = Path(tempfile.mkdtemp(prefix="korvu-contexto-")).resolve()
SERVIDOR = "postgresql://postgres:postgres@127.0.0.1:55322"
NOME_BANCO = f"contexto_teste_{os.getpid()}"
BANCO = f"{SERVIDOR}/{NOME_BANCO}"

os.environ["CONTEXTO_RAIZ"] = str(RAIZ)
os.environ["CONTEXTO_DB_URL"] = BANCO
os.environ["CONTEXTO_EMBEDDER"] = "falso"
os.environ.pop("CONTEXTO_PAINEL_DB_URL", None)
sys.path.insert(0, str(MODULO))
sys.dont_write_bytecode = True

import psycopg  # noqa: E402

FALSO_SEGREDO = "valor-falso-de-teste-0123456789abcdef"   # fictício, só existe neste teste
FALSO_TOKEN = "sk-" + "T" * 20 + "0123456789abcdefXYZ"      # fictício, formato de chave

DECISOES = """# Decisões do autor — o que fazer e o que não fazer

## 1. Roteiro

| Decisão | Data | Por quê | Onde está |
|---|---|---|---|
| **Duração livre do roteiro** — a duração é a que a história pedir; o roteirista não conta palavras e o FB recebe vídeo da Página acima de 90 s. Vale para o 2026-11-01-teste-um e todos os seguintes, sem exceção, e o portao-pauta confere a história antes do roteiro ir para o revisor; o autor pediu que nada seja cortado só para caber num tempo fixo | 02/11 | "Sem teto" | roteirista, `painel/README.md` |
| **Música só da ElevenLabs** — nada de biblioteca de terceiros, nem trilha baixada da internet, nem música de banco gratuito; o produtor-musical gera duas opções e o autor escolhe ouvindo, sempre mixada abaixo da voz, com o ducking automático e o volume final em −14 LUFS no master do vídeo inteiro | 14/10 | licença | produtor-musical |

## 6. O que NÃO fazer

- **Não ler nem imprimir `.env`.**
"""

ARQUIVOS = {
    "CLAUDE.md": "# Korvu Studio\n\n## Captação\nCâmera Panasonic Lumix S5IIX em V-Log, 25 fps. Nunca converter para 30 "
                 "(judder). O roteirista escreve; o revisor-de-roteiro aprova.\n\n## Regras rígidas\n1. Nunca "
                 "renderizar sem `edl.json.aprovado = true`.\n2. Máximo 5 hashtags.\n",
    "docs/decisoes.md": DECISOES,
    "HANDOFF.md": "# HANDOFF\n\n## 2026-11-10 — Painel e PD9\n- **Feito:** a rede só no Mac (PD9) conferida; o vídeo "
                  "2026-11-01-teste-um ganhou roteiro v2. Endpoint `/ordered_comments` para comentários.\n"
                  "- **Verificado:** sincronizador exit 0, 27 agentes e a contagem de veredictos batendo com o banco.\n"
                  "\n## 2026-11-11 — Sessão seguinte\n- **Feito:** teste-um aprovado no PORTÃO-ROTEIRO; o PDF ficou "
                  "com duas páginas e a capa ainda espera a cor.\n- **Pendente:** gravar a fala principal e as cenas "
                  "extras; depois o /editar e a EDL para o autor aprovar.\n",
    "_controle/backlog-portoes.md": "# Backlog\n\n| Nº | Arquivo | Achado | Portão | Dono | Gatilho | Estado |\n"
                                    "|---|---|---|---|---|---|---|\n| PD9 | `painel/supabase/config.toml` | O banco "
                                    "atende na rede local (23/10) | portao-dados | engenheiro-backend | já | aberto |\n",
    "painel/README.md": "# Painel\n\n## Só no Mac (PD9, 23/10)\nO banco responde só em 127.0.0.1:55322.\n",
    "painel/portoes/dados-2026-11-10-v1.md": "PORTÃO-DADOS: APROVADO\n\n# Relatório\nNada a apontar no "
                                             "sincronizador; migrações conferidas uma a uma.\n",
    "videos/2026-11-01-teste-um/roteiro.md": "# Roteiro teste-um\n\n## Fala\nL01 — Você sabia que a IA aprende "
                                             "com dados rotulados por gente de verdade, todo santo dia?\n",
    "videos/2026-11-01-teste-um/status.json": '{"slug": "2026-11-01-teste-um", "estado": "roteiro", "pilar": "perfil"}',
    "videos/2026-11-01-teste-um/qa/portoes/pauta-2026-11-01-v1.md": "PORTÃO-PAUTA: BLOQUEADO\n\n## Achados\n"
                                                                    "S1-1: a foto mostra outra pessoa no lugar do "
                                                                    "fundador; trocar antes do roteiro.\n",
    # o que NUNCA pode entrar
    ".env": f"API_TESTE={FALSO_SEGREDO}\n",
    "painel/web/.env.local": f"OUTRA={FALSO_SEGREDO}\n",
    "videos/2026-11-01-teste-um/brutos/principal/take.mp4": b"\x00\x00\x00\x18ftypmp42",
    "videos/2026-11-01-teste-um/material/dossie.md": f"# Dossiê\n\nChave colada por engano: {FALSO_TOKEN}\n",
    ".claude/agents/roteirista.md": "---\nname: roteirista\ndescription: Escreve roteiros narrativos.\nmodel: opus\n"
                                    "---\nCorpo.\n",
    ".claude/agents/revisor-de-roteiro.md": "---\nname: revisor-de-roteiro\ndescription: Portão do roteiro.\n---\n",
}

PAINEL_SQL = """
create table public.departamentos (id text primary key, nome text, descricao text, gerente_id text, ordem int);
create table public.agentes (id text primary key, nome text, cargo text, departamento_id text, papel text,
  resumo text, fiscalizado_por text, fiscaliza text[], arquivo text, modelo text);
create table public.videos (slug text primary key, tema text, pilar text, estrutura text, cta text, estado text,
  atualizado timestamptz, cta_palavra text, gravacao_prevista date, nome_curto text, roteiro_versao text);
create table public.portoes_estado (alvo text, slug text, portao text, agente text, status text, motivos text,
  volta int);
create table public.veredictos (alvo text, slug text, portao text, agente text, resultado text, em timestamptz,
  volta int, s0 int, s1 int, s2 int, relatorio text, nota text, decisao_autor text, ordem int);
create table public.publicacoes (slug text primary key, publicado_em timestamptz, tema text, pilar text, palavra text,
  duracao_s numeric, trial boolean, permalink_instagram text, permalink_facebook text, video_slug text,
  plataformas text[], estado text);
create table public.metricas (slug text, lido_em timestamptz, dias int, views int, alcance int, tempo_medio_s numeric,
  pct_assistido numeric, curtidas int, comentarios int, salvamentos int, compartilhamentos int,
  palavra_comentarios int, palavra_directs int);
insert into public.departamentos values
  ('roteiro', 'roteiro', 'Escreve o roteiro.', 'revisor-de-roteiro', 1),
  ('tecnologia', 'tecnologia', 'Painel.', 'portao-dados', 2);
insert into public.agentes values
  ('roteirista', 'Marina', 'roteirista', 'roteiro', 'construtor', '', 'revisor-de-roteiro', '{}',
   '.claude/agents/roteirista.md', 'opus'),
  ('revisor-de-roteiro', 'Otávio', 'gerente', 'roteiro', 'portao', '', null, '{roteirista}',
   '.claude/agents/revisor-de-roteiro.md', 'opus'),
  ('portao-dados', 'Sérgio', 'portão dos dados', 'tecnologia', 'portao', '', null, '{}', null, 'opus');
insert into public.videos values ('2026-11-01-teste-um', 'Quem rotula os dados da IA', 'perfil', 'narrativa', 'x',
  'roteiro', now(), 'DADOS', null, 'teste-um', '2');
insert into public.portoes_estado values
  ('videos/2026-11-01-teste-um', '2026-11-01-teste-um', 'roteiro', 'revisor-de-roteiro', 'aprovado', null, 2),
  ('painel', null, 'dados', 'portao-dados', 'aprovado', null, 1);
insert into public.veredictos values
  ('videos/2026-11-01-teste-um', '2026-11-01-teste-um', 'roteiro', 'revisor-de-roteiro', 'BLOQUEADO',
   '2026-11-01 10:00+00', 1, 0, 1, 0, null, null, null, 0),
  ('videos/2026-11-01-teste-um', '2026-11-01-teste-um', 'roteiro', 'revisor-de-roteiro', 'APROVADO',
   '2026-11-01 11:00+00', 2, 0, 0, 1, null, null, null, 1),
  ('painel', null, 'dados', 'portao-dados', 'APROVADO', '2026-11-10 09:00+00', 1, 0, 0, 0,
   'painel/portoes/dados-2026-11-10-v1.md', null, null, 2);
insert into public.publicacoes values ('2026-11-01-teste-um', '2026-11-05 19:00+00', 'Quem rotula', 'perfil',
  'DADOS', 80, false, 'https://example.invalid/p/1', null, '2026-11-01-teste-um', '{instagram,facebook}', 'publicado');
insert into public.metricas values
  ('2026-11-01-teste-um', '2026-11-06 09:30+00', 1, 100, 90, 10, 40, 5, 1, 2, 0, 1, 1),
  ('2026-11-01-teste-um', '2026-11-10 09:30+00', 5, 900, 800, 12, 45, 30, 4, 9, 3, 2, 2);
"""


def escrever(rel: str, conteudo) -> Path:
    p = RAIZ / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(conteudo, bytes):
        p.write_bytes(conteudo)
    else:
        p.write_text(conteudo, encoding="utf-8")
    return p


def pytest_sessionstart(session):
    for rel, c in ARQUIVOS.items():
        escrever(rel, c)
    with psycopg.connect(f"{SERVIDOR}/postgres", autocommit=True) as c:
        c.execute(f'drop database if exists "{NOME_BANCO}"')
        c.execute(f'create database "{NOME_BANCO}"')
    with psycopg.connect(BANCO, autocommit=True) as c:
        c.execute(PAINEL_SQL)


def pytest_sessionfinish(session, exitstatus):
    if os.environ.get("CONTEXTO_TESTE_MANTER"):
        print(f"\nmantidos: {RAIZ} e o banco {NOME_BANCO}")
        return
    shutil.rmtree(RAIZ, ignore_errors=True)
    with psycopg.connect(f"{SERVIDOR}/postgres", autocommit=True) as c:
        c.execute(f'drop database if exists "{NOME_BANCO}" with (force)')


@pytest.fixture(scope="session")
def sincronizado():
    from contexto.sincronizar import sincronizar
    return sincronizar(log=lambda *_: None)


@pytest.fixture
def con_leitura(sincronizado):
    from contexto.db import conectar
    c = conectar(leitura=True)
    yield c
    c.close()
