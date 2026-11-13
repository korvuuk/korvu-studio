"""Indexação incremental do corpus (ESPECIFICACAO.md §6).

- Hash de cada arquivo: arquivo igual → nada a fazer (só as entidades são reconferidas, sem reembedar).
- Hash de cada trecho: só os trechos novos ou alterados são embedados; os que sumiram são apagados.
- Arquivo que saiu do corpus (apagado, excluído ou com token) → documento e trechos apagados.
- Nunca apaga a tabela inteira.
"""
from __future__ import annotations

import datetime as dt
import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import psycopg

from . import config
from .chunking import VERSAO as VERSAO_CHUNKING, chunk
from .corpus import Corpus, Projeto, projeto_do_caminho, tipo_do_documento, video_do_caminho
from .embeddings import embedder
from .grafo import Catalogo
from .seguranca import VERSAO_MASCARA, excluido, mascarar, tokens_no_texto


@dataclass
class Resultado:
    documentos: int = 0
    trechos: int = 0
    embedados: int = 0
    removidos: int = 0
    inalterados: int = 0
    excluidos: list[str] = field(default_factory=list)   # "caminho (motivo)" — nunca conteúdo


def _entidades(cat: Catalogo, caminho: str, secao: str, texto: str) -> list[str]:
    ids = set(cat.entidades(f"{secao}\n{texto}"))
    slug = video_do_caminho(caminho)
    if slug and slug in cat.videos:
        ids.add(f"video:{slug}")
    ids.update(cat.decisoes_no_trecho(caminho, texto))
    return sorted(ids)


def indexar(con: psycopg.Connection, raiz: Path, corpus: Corpus, projetos: list[Projeto], cat: Catalogo,
            log=print) -> Resultado:
    r = Resultado(excluidos=[f"{c} ({m})" for c, m in corpus.excluidos])
    emb = embedder()
    no_corpus: set[str] = set()

    for rel in corpus.arquivos:
        arq = raiz / rel
        bruto = arq.read_bytes()
        texto = mascarar(bruto.decode("utf-8", errors="replace"))
        achados = tokens_no_texto(texto)
        if achados:
            r.excluidos.append(f"{rel} (token: {', '.join(achados)})")
            continue
        no_corpus.add(rel)
        # o hash do documento inclui a versão e os limites do chunking: mudou a regra → o arquivo é redividido
        h_arq = hashlib.sha256(bruto + f"|chunking {VERSAO_CHUNKING} {corpus.maximo} {corpus.minimo} mascara {VERSAO_MASCARA}".encode()).hexdigest()
        projeto = projeto_do_caminho(rel, projetos)
        tipo = tipo_do_documento(rel)
        antigo = con.execute("select hash from contexto.documentos where caminho = %s", (rel,)).fetchone()

        if antigo and antigo[0] == h_arq:
            r.inalterados += 1
            # o arquivo não mudou, mas o catálogo pode ter mudado (vídeo novo, agente novo): só as entidades
            with con.transaction():
                for tid, secao, txt, ents in con.execute(
                        "select id, secao, texto, entidades from contexto.trechos where caminho = %s", (rel,)).fetchall():
                    novas = _entidades(cat, rel, secao, txt)
                    if novas != list(ents):
                        con.execute("update contexto.trechos set entidades = %s where id = %s", (novas, tid))
                con.execute("update contexto.documentos set projeto = %s, tipo = %s where caminho = %s",
                            (projeto, tipo, rel))
            continue

        trechos = chunk(rel, texto, corpus.maximo, corpus.minimo)
        # ids estáveis: caminho#hash curto (+ sufixo se o mesmo texto aparece 2x no arquivo)
        ids, contagem = [], {}
        for t in trechos:
            base = f"{rel}#{t.hash[:12]}"
            contagem[base] = contagem.get(base, 0) + 1
            ids.append(base if contagem[base] == 1 else f"{base}-{contagem[base]}")
        existentes = {row[0]: row[1] for row in con.execute(
            "select id, ordem from contexto.trechos where caminho = %s", (rel,)).fetchall()}
        novos = [(i, t) for i, t in zip(ids, trechos) if i not in existentes]
        vetores = emb.trechos([f"{t.secao}\n{t.texto}" if t.secao else t.texto for _, t in novos])
        modificado = dt.datetime.fromtimestamp(arq.stat().st_mtime, dt.timezone.utc)

        with con.transaction():
            con.execute(
                "insert into contexto.documentos (caminho, projeto, tipo, hash, bytes, modificado) "
                "values (%s, %s, %s, %s, %s, %s) on conflict (caminho) do update set projeto = excluded.projeto, "
                "tipo = excluded.tipo, hash = excluded.hash, bytes = excluded.bytes, modificado = excluded.modificado, "
                "indexado_em = now()", (rel, projeto, tipo, h_arq, len(bruto), modificado))
            sumiram = [i for i in existentes if i not in set(ids)]
            if sumiram:
                con.execute("delete from contexto.trechos where id = any(%s)", (sumiram,))
                r.removidos += len(sumiram)
            for i, t in zip(ids, trechos):
                if i in existentes:
                    novas = _entidades(cat, rel, t.secao, t.texto)
                    con.execute("update contexto.trechos set ordem = %s, entidades = %s "
                                "where id = %s and (ordem <> %s or entidades <> %s)", (t.ordem, novas, i, t.ordem, novas))
            for (i, t), v in zip(novos, vetores):
                con.execute(
                    "insert into contexto.trechos (id, caminho, ordem, secao, tipo, data, pds, entidades, hash, texto, "
                    "embedding) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (i, rel, t.ordem, t.secao, tipo, t.data, t.pds, _entidades(cat, rel, t.secao, t.texto), t.hash,
                     t.texto, v))
        r.embedados += len(novos)
        if novos or (antigo is None):
            log(f"  {rel}: {len(trechos)} trechos, {len(novos)} embedados")

    # documentos que saíram do corpus (apagados, excluídos ou com token)
    with con.transaction():
        for (caminho,) in con.execute("select caminho from contexto.documentos").fetchall():
            if caminho not in no_corpus or excluido(caminho):
                n = con.execute("delete from contexto.trechos where caminho = %s", (caminho,)).rowcount
                con.execute("delete from contexto.documentos where caminho = %s", (caminho,))
                r.removidos += n
                log(f"  removido do índice: {caminho} ({n} trechos)")

    r.documentos, r.trechos = con.execute(
        "select (select count(*) from contexto.documentos), (select count(*) from contexto.trechos)").fetchone()
    return r
