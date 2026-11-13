"""Resolve o corpus (corpus.yaml) e o mapa de projetos (projetos.yaml)."""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import config
from .seguranca import motivo_exclusao


@dataclass
class Projeto:
    id: str
    nome: str
    descricao: str = ""
    pai: str | None = None
    pastas: list[str] = field(default_factory=list)
    departamentos: list[str] = field(default_factory=list)
    depende_de: list[str] = field(default_factory=list)
    instrucoes: str | None = None


def carregar_projetos(caminho: Path | None = None) -> list[Projeto]:
    dados = yaml.safe_load((caminho or config.PROJETOS_YAML).read_text(encoding="utf-8"))
    projetos = [Projeto(**p) for p in dados["projetos"]]
    ids = {p.id for p in projetos}
    for p in projetos:
        for ref in [p.pai, *p.depende_de]:
            if ref and ref not in ids:
                raise ValueError(f"projetos.yaml: {p.id} cita projeto inexistente {ref!r}")
    return projetos


def projeto_do_caminho(caminho: str, projetos: list[Projeto]) -> str:
    """Projeto cuja pasta é o prefixo MAIS LONGO do caminho ('' = raiz → estúdio)."""
    melhor, tam = projetos[0].id, -1
    for p in projetos:
        for pasta in p.pastas:
            if pasta == "":
                casa = True                          # raiz: vale para tudo, com o menor peso
            elif pasta.endswith("/"):
                casa = caminho.startswith(pasta)     # pasta
            else:
                casa = caminho == pasta              # arquivo avulso (ex.: scripts/publicar.py)
            if casa and len(pasta) > tam:
                melhor, tam = p.id, len(pasta)
    return melhor


def tipo_do_documento(caminho: str) -> str:
    nome = Path(caminho).name
    if nome == "CLAUDE.md":
        return "instrucoes"
    if caminho == "docs/decisoes.md":
        return "decisoes"
    if caminho == "HANDOFF.md":
        return "handoff"
    if caminho == "_controle/backlog-portoes.md":
        return "backlog"
    if caminho == "_controle/CONTINUAR.md":
        return "estado"
    if caminho.startswith("painel/portoes/") or "/qa/portoes/" in caminho:
        return "relatorio_portao"
    if nome == "roteiro.md":
        return "roteiro"
    if nome == "roteiro-revisao.md":
        return "revisao_roteiro"
    if nome == "dossie.md":
        return "dossie"
    if nome == "status.json":
        return "status_video"
    if nome == "README.md":
        return "readme"
    if caminho.startswith("docs/"):
        return "documentacao"
    if nome.endswith((".yaml", ".yml")):
        return "mapa"
    return "documento"


def video_do_caminho(caminho: str) -> str | None:
    partes = caminho.split("/")
    if len(partes) >= 3 and partes[0] == "videos" and not partes[1].startswith("_"):
        return partes[1]
    return None


@dataclass
class Corpus:
    arquivos: list[str]
    excluidos: list[tuple[str, str]]   # (caminho, motivo) — nunca conteúdo
    maximo: int = 1800
    minimo: int = 120


def resolver_corpus(raiz: Path | None = None, caminho_yaml: Path | None = None) -> Corpus:
    raiz = raiz or config.RAIZ
    dados = yaml.safe_load((caminho_yaml or config.CORPUS_YAML).read_text(encoding="utf-8"))
    excluir = dados.get("excluir", [])
    ck = dados.get("chunking", {})
    vistos: dict[str, None] = {}
    excluidos: list[tuple[str, str]] = []
    for padrao in dados["incluir"]:
        for p in sorted(raiz.glob(padrao)):
            if not p.is_file() or p.is_symlink():
                continue
            rel = p.relative_to(raiz).as_posix()
            if rel in vistos:
                continue
            if any(fnmatch.fnmatch(rel, e) for e in excluir):
                continue
            motivo = motivo_exclusao(rel)
            if motivo:
                excluidos.append((rel, motivo))
                continue
            vistos[rel] = None
    return Corpus(list(vistos), excluidos, ck.get("max_caracteres", 1800), ck.get("min_caracteres", 120))
