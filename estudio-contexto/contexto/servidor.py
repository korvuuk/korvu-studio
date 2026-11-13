"""Servidor MCP do contexto do estúdio — SOMENTE LEITURA (ESPECIFICACAO.md §8).

Nenhuma ferramenta escreve nada nem chama API externa. A conexão com o banco abre em transação só-leitura e baixa
para o papel `contexto_leitor` (só SELECT no schema `contexto`; o `public` do painel fica de fora).

Rodar (stdio, como o Claude Code usa):  uv --directory estudio-contexto run python -m contexto.servidor
"""
from __future__ import annotations

import json
import os
import sys
import threading

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_OFFLINE", "1")  # o servidor nunca vai à rede: o modelo já está no cache

import psycopg
from mcp.server.fastmcp import FastMCP

from . import consultas
from .consultas import _limpar
from .db import conectar
from .embeddings import embedder

mcp = FastMCP(
    "estudio-contexto",
    instructions=(
        "Contexto do estúdio Korvu Studio (Korvu): grafo de projetos, agentes, vídeos, portões, veredictos e decisões, "
        "e busca semântica nos documentos do projeto (CLAUDE.md, decisoes.md, HANDOFF.md, roteiros, relatórios dos "
        "portões). Somente leitura. Cada resposta traz 'fonte': cite o caminho ao usar a informação. Os arquivos "
        "continuam sendo a fonte da verdade; o índice é derivado e pode estar algumas horas atrasado."),
)

_trava = threading.Lock()
_con: psycopg.Connection | None = None


def _conexao() -> psycopg.Connection:
    global _con
    if _con is None or _con.closed or _con.broken:
        _con = conectar(leitura=True)
    return _con


def _rodar(fn, *args, **kw) -> str:
    with _trava:
        try:
            r = fn(_conexao(), *args, **kw)
        except psycopg.OperationalError as e:
            global _con
            _con = None
            r = {"erro": f"banco do contexto indisponível ({type(e).__name__}). O Postgres do painel "
                         f"(127.0.0.1:55322) está ligado? bash painel/iniciar.sh"}
        except psycopg.Error as e:
            try:
                _conexao().rollback()
            except psycopg.Error:
                pass
            r = {"erro": f"{type(e).__name__}: {str(e).splitlines()[0]}"}
    return json.dumps(_limpar(r), ensure_ascii=False, indent=1, default=str)


@mcp.tool()
def contexto_do_projeto(projeto: str) -> str:
    """Contexto de um projeto/área do estúdio (estudio, painel, automacao-meta, ai-engineer, remotion,
    carrosseis, estudio-contexto): descrição, pastas, dependências, agentes, documentos principais e decisões."""
    return _rodar(consultas.contexto_do_projeto, projeto)


@mcp.tool()
def contexto_do_video(slug: str) -> str:
    """Tudo sobre um vídeo pelo slug (ou o fim do slug, ex.: 'exemplo'): estado, portões e veredictos, decisões,
    publicação e métricas (se houver) e os documentos da pasta."""
    return _rodar(consultas.contexto_do_video, slug)


@mcp.tool()
def buscar(consulta: str, projeto: str | None = None, tipo: str | None = None, limite: int = 8,
           agente: str | None = None, desde: str | None = None, ate: str | None = None) -> str:
    """Busca híbrida (semântica + texto + grafo) nos documentos do estúdio. Devolve trechos com caminho, seção,
    data, um recorte do texto e os nós ligados.

    Filtros opcionais: projeto (id do projeto; inclui sub-áreas), tipo (tipo de documento: decisoes, handoff,
    roteiro, revisao_roteiro, dossie, relatorio_portao, backlog, instrucoes, readme, status_video — ou tipo de nó
    citado: video, agente, decisao), agente (id do agente citado), desde/ate (AAAA-MM-DD)."""
    return _rodar(consultas.busca, consulta, projeto, tipo, limite, agente, desde, ate)


@mcp.tool()
def vizinhos(no: str, profundidade: int = 1) -> str:
    """Nós e arestas ao redor de um nó do grafo (id como 'video:2026-01-15-exemplo', 'agente:roteirista',
    'decisao:PD9', ou só o nome). Profundidade 1 a 3."""
    return _rodar(consultas.vizinhanca, no, profundidade)


@mcp.tool()
def decisoes_sobre(tema: str) -> str:
    """Decisões do autor (docs/decisoes.md) e códigos PD (backlog dos portões) sobre um tema, com data, motivo e
    onde estão aplicadas, mais os trechos de outros documentos que as citam."""
    return _rodar(consultas.decisoes_sobre, tema)


@mcp.tool()
def quem_fiscaliza(agente: str) -> str:
    """Portão (GAUNTLET) que fiscaliza um agente e os veredictos recentes desse portão. Se o agente for ele mesmo um
    portão, diz também quem ele fiscaliza."""
    return _rodar(consultas.quem_fiscaliza, agente)


def main() -> None:
    # carrega o modelo antes da primeira pergunta (o MCP usa stdout; log só no stderr)
    threading.Thread(target=embedder, daemon=True).start()
    print("estudio-contexto: servidor MCP (somente leitura) no ar", file=sys.stderr)
    mcp.run()


if __name__ == "__main__":
    main()
