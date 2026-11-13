"""Divisão dos documentos em trechos (ESPECIFICACAO.md §6).

- Markdown: por seção `##` (o título de nível 1 e o `###` entram no caminho da seção). Seção maior que o limite é
  partida por bloco (parágrafo, linha de tabela, item de lista), sem cortar no meio de um bloco quando dá.
- YAML e JSON: o arquivo inteiro se couber; senão um trecho por item de primeiro nível.
- Cada trecho guarda: seção, data (se houver), códigos PD (se houver) e o hash do texto.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from dataclasses import dataclass, field

import yaml

RX_PD = re.compile(r"\bPD\d{1,3}\b")
RX_DATA_ISO = re.compile(r"\b(20\d\d)-(\d\d)-(\d\d)\b")
RX_DATA_BR = re.compile(r"(?<![\d/])(\d{1,2})/(\d{1,2})(?:/(20\d\d))?(?![\d/])")
RX_TITULO = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
ANO_PADRAO = 2026
# Mudou a regra de divisão? Suba a versão: os arquivos são redivididos (só os trechos novos são reembedados).
VERSAO = "6"
# linha de tabela ou item de lista com 400+ caracteres = um trecho próprio (uma decisão = um trecho). Medido em
# 12/11 (avaliacao/): 200 fragmenta o backlog e o HANDOFF e piora a busca; 400 deu o melhor resultado.
LINHA_SOZINHA = 400
ITEM_SOZINHO = 400


@dataclass
class Trecho:
    ordem: int
    secao: str
    texto: str
    data: dt.date | None = None
    pds: list[str] = field(default_factory=list)

    @property
    def hash(self) -> str:
        return hashlib.sha256(f"{self.secao}\n{self.texto}".encode()).hexdigest()


def achar_data(texto: str) -> dt.date | None:
    m = RX_DATA_ISO.search(texto)
    if m:
        try:
            return dt.date(int(m[1]), int(m[2]), int(m[3]))
        except ValueError:
            pass
    m = RX_DATA_BR.search(texto)
    if m:
        try:
            return dt.date(int(m[3] or ANO_PADRAO), int(m[2]), int(m[1]))
        except ValueError:
            pass
    return None


def pds(texto: str) -> list[str]:
    return sorted(set(RX_PD.findall(texto)), key=lambda s: int(s[2:]))


def _partir_bloco(bloco: str, maximo: int) -> list[str]:
    """Bloco maior que o limite: por linha; linha maior que o limite: por frase; e por fim corte seco."""
    if len(bloco) <= maximo:
        return [bloco]
    pedacos: list[str] = []
    linhas = bloco.split("\n")
    if len(linhas) > 1:
        for ln in linhas:
            pedacos.extend(_partir_bloco(ln, maximo))
        return pedacos
    frases = re.split(r"(?<=[.;!?])\s+", bloco)
    if len(frases) > 1:
        for f in frases:
            pedacos.extend(_partir_bloco(f, maximo))
        return pedacos
    return [bloco[i:i + maximo] for i in range(0, len(bloco), maximo)]


def _blocos(corpo: str) -> list[str]:
    """Parágrafos, mas cada linha de tabela e cada item de lista de 1.º nível é um bloco próprio."""
    blocos: list[str] = []
    atual: list[str] = []

    def fechar():
        if atual and "".join(atual).strip():
            blocos.append("\n".join(atual).strip("\n"))
        atual.clear()

    for ln in corpo.split("\n"):
        if re.match(r"^\|[\s:|-]+\|\s*$", ln):
            continue  # separador de tabela (|---|---|) não carrega informação
        if not ln.strip():
            fechar()
        elif ln.startswith("|") or re.match(r"^(?:[-*]|\d+\.)\s", ln):
            fechar()
            atual.append(ln)
        elif atual and (atual[0].startswith("|") or re.match(r"^(?:[-*]|\d+\.)\s", atual[0])) \
                and not ln.startswith((" ", "\t")):
            fechar()
            atual.append(ln)
        else:
            atual.append(ln)
    fechar()
    return blocos


def _empacotar(blocos: list[str], maximo: int, cabecalho_tabela: str = "") -> list[str]:
    saida: list[str] = []
    atual = ""
    for b in blocos:
        for parte in _partir_bloco(b, maximo):
            if atual and len(atual) + 2 + len(parte) > maximo:
                saida.append(atual)
                atual = ""
            atual = f"{atual}\n\n{parte}" if atual else parte
    if atual:
        saida.append(atual)
    return saida


def _empacotar_rotulado(unidades: list[tuple[str, str]], maximo: int) -> list[tuple[str, str]]:
    """Como _empacotar, mas cada pedaço leva o rótulo (sub-seção/chave) do seu primeiro bloco."""
    saida: list[tuple[str, str]] = []
    rotulo, atual = "", ""
    for rot, b in unidades:
        # linha de tabela longa (ex.: uma decisão em docs/decisoes.md) vira um trecho só dela: a busca acha a
        # decisão inteira em vez de um pacote de três decisões vizinhas
        sozinha = (b.startswith("|") and len(b) >= LINHA_SOZINHA) or \
            (re.match(r"^(?:[-*]|\d+\.)\s", b) is not None and len(b) >= ITEM_SOZINHO)
        if sozinha and atual:
            saida.append((rotulo, atual))
            atual = ""
        for parte in _partir_bloco(b, maximo):
            if atual and len(atual) + 2 + len(parte) > maximo:
                saida.append((rotulo, atual))
                atual = ""
            if not atual:
                rotulo = rot
            atual = f"{atual}\n\n{parte}" if atual else parte
        if sozinha:
            saida.append((rotulo, atual))
            atual = ""
    if atual:
        saida.append((rotulo, atual))
    return saida


def _secoes_markdown(texto: str) -> list[tuple[str, str]]:
    """[(caminho da seção, corpo)] cortando em `#` e `##`; `###` fica dentro, mas entra no caminho do trecho."""
    h1 = ""
    secao = ""
    corpo: list[str] = []
    saida: list[tuple[str, str]] = []
    em_codigo = False
    for ln in texto.split("\n"):
        if ln.lstrip().startswith("```"):
            em_codigo = not em_codigo
        m = None if em_codigo else RX_TITULO.match(ln)
        if m and len(m[1]) <= 2:
            if corpo and "\n".join(corpo).strip():
                saida.append((" › ".join(x for x in (h1, secao) if x), "\n".join(corpo).strip("\n")))
            corpo = []
            if len(m[1]) == 1:
                h1, secao = m[2], ""
            else:
                secao = m[2]
        else:
            corpo.append(ln)
    if corpo and "\n".join(corpo).strip():
        saida.append((" › ".join(x for x in (h1, secao) if x), "\n".join(corpo).strip("\n")))
    return saida


def _sub_secoes(corpo: str) -> list[tuple[str, str]]:
    """Corta o corpo de uma seção `##` nos `###` (o título do ### vai para o caminho)."""
    partes: list[tuple[str, str]] = []
    titulo = ""
    atual: list[str] = []
    for ln in corpo.split("\n"):
        m = RX_TITULO.match(ln)
        if m and len(m[1]) >= 3:
            if "\n".join(atual).strip():
                partes.append((titulo, "\n".join(atual).strip("\n")))
            titulo, atual = m[2], []
        else:
            atual.append(ln)
    if "\n".join(atual).strip():
        partes.append((titulo, "\n".join(atual).strip("\n")))
    return partes


def chunk_markdown(texto: str, maximo: int = 1800, minimo: int = 120) -> list[Trecho]:
    trechos: list[Trecho] = []
    pendente: tuple[str, str] | None = None  # seção curta demais esperando a próxima
    for secao, corpo in _secoes_markdown(texto):
        if pendente is not None:
            ps, pc = pendente
            # a seção curta entra no começo da próxima, com o título dela para não perder o contexto
            corpo = (f"{ps}\n{pc}" if ps and ps != secao else pc) + f"\n\n{corpo}"
            pendente = None
        if len(corpo.strip()) < minimo:
            pendente = (secao, corpo)
            continue
        data_secao = achar_data(secao)
        # os ### não cortam sozinhos: os blocos de várias sub-seções curtas dividem o mesmo trecho; o caminho do
        # trecho leva o ### do primeiro bloco dele
        unidades: list[tuple[str, str]] = []
        for sub, sub_corpo in _sub_secoes(corpo):
            if sub:
                unidades.append((sub, f"### {sub}"))
            unidades.extend((sub, b) for b in _blocos(sub_corpo))
        for sub, pedaco in _empacotar_rotulado(unidades, maximo):
            caminho = f"{secao} › {sub}" if sub else secao
            trechos.append(Trecho(len(trechos), caminho, pedaco,
                                  data_secao or achar_data(sub) or achar_data(pedaco[:300]),
                                  pds(f"{caminho}\n{pedaco}")))
    if pendente is not None:
        ps, pc = pendente
        if trechos and len(trechos[-1].texto) + len(pc) < maximo:
            t = trechos[-1]
            t.texto = f"{t.texto}\n\n{pc}"
            t.pds = pds(f"{t.secao}\n{t.texto}")
        elif pc.strip():
            trechos.append(Trecho(len(trechos), ps, pc.strip(), achar_data(ps) or achar_data(pc), pds(pc)))
    return trechos


def _dump(v) -> str:
    if isinstance(v, (dict, list)):
        return yaml.safe_dump(v, allow_unicode=True, sort_keys=False, width=120).strip()
    return str(v)


def chunk_estruturado(texto: str, formato: str, maximo: int = 1800) -> list[Trecho]:
    """YAML/JSON: arquivo inteiro se couber; senão um trecho por item de 1.º nível (partido se ainda for grande)."""
    try:
        dados = json.loads(texto) if formato == "json" else yaml.safe_load(texto)
    except (json.JSONDecodeError, yaml.YAMLError):
        return chunk_markdown(texto, maximo)
    inteiro = _dump(dados)
    if len(inteiro) <= maximo:
        return [Trecho(0, "", inteiro, achar_data(inteiro[:400]), pds(inteiro))]
    itens = list(dados.items()) if isinstance(dados, dict) else list(enumerate(dados)) if isinstance(dados, list) \
        else [("", dados)]
    unidades: list[tuple[str, str]] = []
    for chave, valor in itens:
        corpo = _dump(valor)
        if isinstance(valor, list) and len(corpo) > maximo:
            # lista grande dentro do item (ex.: historico do status.json): um bloco por elemento
            unidades.extend((str(chave), f"{chave}[{i}]: {_dump(x)}") for i, x in enumerate(valor))
        else:
            unidades.append((str(chave), f"{chave}: {corpo}"))
    return [Trecho(i, secao, pedaco, achar_data(pedaco[:400]), pds(pedaco))
            for i, (secao, pedaco) in enumerate(_empacotar_rotulado(unidades, maximo))]


def chunk(caminho: str, texto: str, maximo: int = 1800, minimo: int = 120) -> list[Trecho]:
    if caminho.endswith(".json"):
        return chunk_estruturado(texto, "json", maximo)
    if caminho.endswith((".yaml", ".yml")):
        return chunk_estruturado(texto, "yaml", maximo)
    return chunk_markdown(texto, maximo, minimo)
