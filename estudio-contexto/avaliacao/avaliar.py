"""Avaliação do contexto (ESPECIFICACAO.md §9): Recall@5, respostas corretas com a fonte certa e vazamento.

Uso (de estudio-contexto/):  uv run python avaliacao/avaliar.py [--relatorio avaliacao/resultado.md] [-v]
Roda contra o banco real, na conexão SÓ-LEITURA do servidor MCP (as mesmas funções que as ferramentas usam).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contexto import consultas  # noqa: E402
from contexto.busca import buscar  # noqa: E402
from contexto.db import conectar  # noqa: E402
from contexto.seguranca import motivo_exclusao  # noqa: E402

AQUI = Path(__file__).resolve().parent
FERRAMENTAS = {"quem_fiscaliza": consultas.quem_fiscaliza, "contexto_do_video": consultas.contexto_do_video,
               "contexto_do_projeto": consultas.contexto_do_projeto, "decisoes_sobre": consultas.decisoes_sobre,
               "vizinhos": lambda con, no, profundidade=1: consultas.vizinhanca(con, no, profundidade),
               "buscar": consultas.busca}


def fonte_ok(caminho: str, fontes: list[str]) -> bool:
    return any(caminho == f or (f.endswith("/") and caminho.startswith(f)) for f in fontes)


def avaliar(verboso: bool = False) -> dict:
    perguntas = yaml.safe_load((AQUI / "perguntas.yaml").read_text(encoding="utf-8"))
    con = conectar(leitura=True)
    linhas = []
    rec = cor = 0
    for p in perguntas["busca"]:
        res = buscar(con, p["pergunta"], limite=5, expandir=False)
        textos = {r[0]: r[1] for r in con.execute("select id, texto from contexto.trechos where id = any(%s)",
                                                  ([r["id"] for r in res],)).fetchall()}
        pos_fonte = next((i + 1 for i, r in enumerate(res) if fonte_ok(r["fonte"], p["fontes"])), None)
        pos_resp = next((i + 1 for i, r in enumerate(res) if fonte_ok(r["fonte"], p["fontes"]) and any(
            x.lower() in textos.get(r["id"], "").lower() for x in p["resposta"])), None)
        rec += pos_fonte is not None
        cor += pos_resp is not None
        linhas.append({"id": p["id"], "pergunta": p["pergunta"], "recall": pos_fonte, "correta": pos_resp,
                       "top": [f"{r['fonte']} › {r['secao'][:60]}" for r in res]})
        if verboso:
            print(p["id"], pos_fonte, pos_resp, [r["fonte"] for r in res])
    ok_ferr = 0
    for p in perguntas["ferramenta"]:
        saida = json.dumps(consultas._limpar(FERRAMENTAS[p["chamada"]](con, **p["args"])), ensure_ascii=False,
                           default=str)
        faltam = [x for x in p["contem"] if x not in saida]
        ok_ferr += not faltam
        linhas.append({"id": p["id"], "pergunta": p["pergunta"], "ferramenta": p["chamada"], "ok": not faltam,
                       "faltam": faltam})
        if verboso:
            print(p["id"], "ok" if not faltam else f"faltam {faltam}")

    # vazamento: nenhum trecho de arquivo excluído (segredo ou mídia) e nenhum caminho de mídia no índice
    vaz = [c for (c,) in con.execute("select distinct caminho from contexto.trechos").fetchall() if motivo_exclusao(c)]
    midia = con.execute("select count(*) from contexto.trechos where caminho ~* "
                        "'\\.(mp4|mov|wav|mp3|m4a|aac)$' or caminho like '%%/brutos/%%'").fetchone()[0]
    n_b, n_f = len(perguntas["busca"]), len(perguntas["ferramenta"])
    con.close()
    return {"data": dt.datetime.now().isoformat(timespec="minutes"),
            "recall_at_5": round(rec / n_b, 3), "busca_corretas": f"{cor}/{n_b}",
            "ferramentas_corretas": f"{ok_ferr}/{n_f}", "corretas_total": round((cor + ok_ferr) / (n_b + n_f), 3),
            "vazamento_arquivos_excluidos": vaz, "vazamento_midia": midia, "linhas": linhas}


def relatorio_md(r: dict) -> str:
    alvo = lambda v, a: "✅" if v >= a else "❌"  # noqa: E731
    out = [f"# Avaliação do estudio-contexto — {r['data']}", "",
           "| Métrica | Valor | Alvo (§9) |", "|---|---|---|",
           f"| Recall@5 da busca híbrida | {r['recall_at_5']:.2f} | ≥ 0,80 {alvo(r['recall_at_5'], 0.8)} |",
           f"| Respostas corretas com a fonte certa ({n_b + n_f} perguntas) | {r['corretas_total']:.0%} "
           f"(busca {r['busca_corretas']}, ferramentas {r['ferramentas_corretas']}) | ≥ 80% "
           f"{alvo(r['corretas_total'], 0.8)} |",
           f"| Vazamento (.env / arquivos excluídos) | {len(r['vazamento_arquivos_excluidos'])} | 0 "
           f"{'✅' if not r['vazamento_arquivos_excluidos'] else '❌'} |",
           f"| Vazamento (mídia) | {r['vazamento_midia']} | 0 {'✅' if not r['vazamento_midia'] else '❌'} |",
           "", "O teste de valores do `.env` fica em `tests/test_seguranca.py` (lê as chaves sem imprimir).", "",
           "## Por pergunta", "", "| id | pergunta | recall (pos.) | correta (pos.) |", "|---|---|---|---|"]
    for ln in r["linhas"]:
        if "ferramenta" in ln:
            out.append(f"| {ln['id']} | {ln['pergunta']} (`{ln['ferramenta']}`) | — | "
                       f"{'✅' if ln['ok'] else '❌ faltam ' + ', '.join(ln['faltam'])} |")
        else:
            out.append(f"| {ln['id']} | {ln['pergunta']} | {ln['recall'] or '❌'} | {ln['correta'] or '❌'} |")
    falhas = [ln for ln in r["linhas"] if "top" in ln and not ln["correta"]]
    if falhas:
        out += ["", "## Erros da busca (top 5 devolvido)", ""]
        for ln in falhas:
            out.append(f"- **{ln['id']}** {ln['pergunta']}")
            out += [f"  {i + 1}. `{t}`" for i, t in enumerate(ln["top"])]
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--relatorio", type=Path)
    ap.add_argument("-v", "--verboso", action="store_true")
    a = ap.parse_args()
    r = avaliar(a.verboso)
    print(f"Recall@5: {r['recall_at_5']:.3f} · corretas: {r['corretas_total']:.1%} (busca {r['busca_corretas']}, "
          f"ferramentas {r['ferramentas_corretas']}) · vazamento: {len(r['vazamento_arquivos_excluidos'])} / "
          f"mídia {r['vazamento_midia']}")
    if a.relatorio:
        a.relatorio.write_text(relatorio_md(r), encoding="utf-8")
        print(f"relatório: {a.relatorio}")
    return 0 if r["recall_at_5"] >= 0.8 and r["corretas_total"] >= 0.8 and not r["vazamento_arquivos_excluidos"] \
        and not r["vazamento_midia"] else 1


if __name__ == "__main__":
    sys.exit(main())
