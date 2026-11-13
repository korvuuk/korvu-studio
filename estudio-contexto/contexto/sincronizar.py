"""Sincronizador do contexto: migra, indexa (incremental) e recalcula o grafo inteiro.

Uso (de estudio-contexto/):
    uv run python -m contexto.sincronizar            # tudo
    uv run python -m contexto.sincronizar --migrar   # só as migrações
    uv run python -m contexto.sincronizar --grafo    # só o grafo (não reembeda nada)

Só LÊ o estúdio e as tabelas `public` do painel; só ESCREVE no schema `contexto`.
"""
from __future__ import annotations

import argparse
import sys
import time

import psycopg
from psycopg.rows import dict_row

from . import config
from .corpus import carregar_projetos, resolver_corpus
from .db import conectar, migrar
from .grafo import construir, gravar, ler_painel, montar_catalogo
from .indexar import indexar


def sincronizar(so_migrar: bool = False, so_grafo: bool = False, log=print) -> dict:
    raiz = config.RAIZ
    con = conectar()
    try:
        aplicadas = migrar(con)
        if aplicadas:
            log(f"migrações aplicadas: {', '.join(aplicadas)}")
        if so_migrar:
            return {"migracoes": aplicadas}
        sid = con.execute("insert into contexto.sincronizacoes default values returning id").fetchone()[0]
        con.commit()
        t0 = time.time()
        try:
            projetos = carregar_projetos()
            painel = ler_painel(config.PAINEL_DB_URL)
            cat = montar_catalogo(raiz, projetos, painel)
            res = None
            if not so_grafo:
                corpus = resolver_corpus(raiz)
                log(f"corpus: {len(corpus.arquivos)} arquivos ({len(corpus.excluidos)} recusados pela segurança)")
                res = indexar(con, raiz, corpus, projetos, cat, log=log)
            with con.cursor(row_factory=dict_row) as cur:
                docs = cur.execute("select caminho, projeto, tipo, modificado from contexto.documentos").fetchall()
                trechos = cur.execute("select id, caminho, secao, texto, ordem, data, entidades "
                                      "from contexto.trechos").fetchall()
            g = construir(raiz, projetos, painel, cat, docs, trechos)
            n_nos, n_arestas = gravar(con, g)
            resumo = {"nos": n_nos, "arestas": n_arestas, "documentos": len(docs), "trechos": len(trechos),
                      "embedados": res.embedados if res else 0, "removidos": res.removidos if res else 0,
                      "excluidos": res.excluidos if res else [], "segundos": round(time.time() - t0, 1)}
            con.execute("update contexto.sincronizacoes set fim = now(), nos = %s, arestas = %s, documentos = %s, "
                        "trechos = %s, embedados = %s, removidos = %s, excluidos = %s, ok = true where id = %s",
                        (n_nos, n_arestas, len(docs), len(trechos), resumo["embedados"], resumo["removidos"],
                         resumo["excluidos"], sid))
            con.commit()
            return resumo
        except Exception as e:  # registra a falha e repassa
            con.rollback()
            con.execute("update contexto.sincronizacoes set fim = now(), ok = false, erro = %s where id = %s",
                        (f"{type(e).__name__}: {e}"[:500], sid))
            con.commit()
            raise
    finally:
        con.close()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--migrar", action="store_true", help="só aplica as migrações")
    ap.add_argument("--grafo", action="store_true", help="só recalcula o grafo (sem reindexar)")
    a = ap.parse_args(argv)
    print(f"— {time.strftime('%Y-%m-%d %H:%M:%S')} sincronização")
    try:
        r = sincronizar(so_migrar=a.migrar, so_grafo=a.grafo)
    except psycopg.OperationalError as e:
        print(f"✗ banco do contexto indisponível ({str(e).splitlines()[0]}). Ligue o painel: bash painel/iniciar.sh",
              file=sys.stderr)
        return 1
    for k, v in r.items():
        if k == "excluidos":
            print(f"excluidos: {len(v)}")
            for x in v:
                print(f"  - {x}")
        else:
            print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
