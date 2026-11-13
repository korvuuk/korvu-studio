#!/usr/bin/env python3
"""Detector de ACERTOS — que Reel foi muito acima da média da conta (pedido do autor, 10/11).

"Toda vez que chega o relatório e um vídeo viraliza, pesquisar conteúdo nesse ângulo e trazer mais conteúdo
parecido para manter a consistência." Este script é a parte que DETECTA (regra fixa, sem opinião); quem pesquisa
e propõe a série é o agente `multiplicador-de-acertos` (comando /multiplicar).

Base de comparação = Reels com leitura de ≥ 5 dias e alcance ≥ 30 (leituras quebradas ficam de fora).
Um Reel (qualquer idade ≥ 1 dia, inclusive leitura precoce) é ACERTO se tem alcance ≥ 100 e pelo menos um sinal:
  alcance          ≥ 2× a mediana do alcance
  salvamentos      ≥ 5 e salv./alcance ≥ max(2× mediana, 1 %)
  compartilhamentos≥ 5 e compart./alcance ≥ max(2× mediana, 0,5 %)
  palavra-chave    ≥ 5 comentários com a palavra
  retenção         % médio assistido ≥ 1,5× a mediana (e ≥ 15 %)
Salvar e comentar a palavra pesam mais que alcance (estratégia de 13/10) — a ordem da lista segue isso.

Uso (da raiz):
  uv run python scripts/acertos.py               # recalcula, grava _controle/acertos.json e lista
  uv run python scripts/acertos.py --pendentes   # só os acertos que ainda não viraram série (sai 10 se houver)
  uv run python scripts/acertos.py --marcar <slug> --serie <arquivo>   # o multiplicador marca como feito
Só lê 07-publicados/*/metricas.json. Nunca chama a Meta.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import statistics
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CONTENT_AI_ROOT") or Path(__file__).resolve().parent.parent)
SAIDA = ROOT / "_controle" / "acertos.json"
PESO = {"salvamentos": 5, "palavra-chave": 4, "compartilhamentos": 3, "retenção": 2, "alcance": 1}


def ler_reels() -> list[dict]:
    reels = []
    for f in sorted((ROOT / "07-publicados").glob("*/metricas.json")):
        try:
            m = json.loads(f.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        u = m.get("ultima") or {}
        ig = (u.get("resumo") or {}).get("instagram") or {}
        if not ig:
            continue
        alc = ig.get("alcance") or 0
        tx = ig.get("taxas_sobre_alcance_pct") or {}
        palavra = ((u.get("resumo") or {}).get("palavra") or {})
        pct = ig.get("pct_medio_assistido")
        reels.append({
            "slug": m.get("slug") or f.parent.name, "tema": m.get("tema"), "pilar": m.get("pilar"),
            "palavra": m.get("palavra"), "trial": m.get("trial"), "dias": u.get("dias_desde_publicacao") or 0,
            "alcance": alc, "views": ig.get("views") or 0, "salvamentos": ig.get("salvamentos") or 0,
            "compartilhamentos": ig.get("compartilhamentos") or 0, "comentarios": ig.get("comentarios") or 0,
            "salv_pct": tx.get("salvamentos") or 0.0, "compart_pct": tx.get("compartilhamentos") or 0.0,
            "palavra_coment": palavra.get("comentarios") or 0, "palavra_directs": palavra.get("directs") or 0,
            # leitura quebrada da API (ex.: 953 %) não entra como retenção
            "pct_assistido": pct if pct is not None and 0 <= pct <= 100 else None,
        })
    return reels


def mediana(vals: list[float]) -> float:
    vals = [v for v in vals if v is not None]
    return statistics.median(vals) if vals else 0.0


def calcular() -> dict:
    reels = ler_reels()
    base = [r for r in reels if r["dias"] >= 5 and r["alcance"] >= 30]
    med = {
        "alcance": mediana([r["alcance"] for r in base]),
        "salv_pct": mediana([r["salv_pct"] for r in base]),
        "compart_pct": mediana([r["compart_pct"] for r in base]),
        "pct_assistido": mediana([r["pct_assistido"] for r in base]),
    }
    acertos = []
    for r in reels:
        if r["dias"] < 1 or r["alcance"] < 100:
            continue
        s = []
        if med["alcance"] and r["alcance"] >= 2 * med["alcance"]:
            s.append(("alcance", r["alcance"], med["alcance"]))
        if r["salvamentos"] >= 5 and r["salv_pct"] >= max(2 * med["salv_pct"], 1.0):
            s.append(("salvamentos", r["salv_pct"], med["salv_pct"]))
        if r["compartilhamentos"] >= 5 and r["compart_pct"] >= max(2 * med["compart_pct"], 0.5):
            s.append(("compartilhamentos", r["compart_pct"], med["compart_pct"]))
        if r["palavra_coment"] >= 5:
            s.append(("palavra-chave", r["palavra_coment"], None))
        if r["pct_assistido"] is not None and med["pct_assistido"] and r["pct_assistido"] >= max(
                1.5 * med["pct_assistido"], 15):
            s.append(("retenção", r["pct_assistido"], med["pct_assistido"]))
        if not s:
            continue
        acertos.append({
            "slug": r["slug"], "tema": r["tema"], "pilar": r["pilar"], "palavra": r["palavra"],
            "trial": r["trial"], "leitura_dias": r["dias"], "precoce": r["dias"] < 5,
            "numeros": {k: r[k] for k in ("alcance", "views", "salvamentos", "compartilhamentos", "comentarios",
                                          "salv_pct", "compart_pct", "pct_assistido", "palavra_coment",
                                          "palavra_directs")},
            "sinais": [{"metrica": m, "valor": v, "mediana": md,
                        "vezes": round(v / md, 1) if md else None} for m, v, md in s],
            "forca": sum(PESO[m] for m, _, _ in s),
        })
    acertos.sort(key=lambda a: (-a["forca"], -a["numeros"]["alcance"]))
    return {"base": {"n": len(base), "slugs": [r["slug"] for r in base], "medianas": med}, "acertos": acertos}


def carregar() -> dict:
    try:
        return json.loads(SAIDA.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def gravar(novo: dict) -> dict:
    antigo = {a["slug"]: a for a in carregar().get("acertos", [])}
    for a in novo["acertos"]:
        velho = antigo.get(a["slug"], {})
        for k in ("multiplicado_em", "serie"):
            if velho.get(k):
                a[k] = velho[k]
        a["primeira_vez"] = velho.get("primeira_vez") or dt.date.today().isoformat()
    novo["gerado_em"] = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    SAIDA.write_text(json.dumps(novo, ensure_ascii=False, indent=2) + "\n")
    return novo


def linha(a: dict) -> str:
    sin = ", ".join(f"{s['metrica']} {s['valor']:g}" + (f" ({s['vezes']}× a mediana)" if s["vezes"] else "")
                    for s in a["sinais"])
    feito = f"série: {a['serie']}" if a.get("serie") else "PENDENTE"
    pre = " · leitura precoce" if a["precoce"] else ""
    return f"  {a['slug']} (força {a['forca']}, {a['leitura_dias']:g} d{pre}) — {sin} — {feito}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Detecta os Reels muito acima da média da conta.")
    ap.add_argument("--pendentes", action="store_true", help="só os que ainda não viraram série (sai 10 se houver)")
    ap.add_argument("--marcar", metavar="SLUG", help="marca o acerto como multiplicado")
    ap.add_argument("--serie", help="arquivo da série (com --marcar)")
    a = ap.parse_args(argv)

    if a.marcar:
        d = carregar()
        for x in d.get("acertos", []):
            if x["slug"] == a.marcar:
                x["multiplicado_em"] = dt.date.today().isoformat()
                x["serie"] = a.serie or x.get("serie")
                SAIDA.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
                print(f"✓ {a.marcar} marcado como multiplicado → {x['serie']}")
                return 0
        print(f"✗ {a.marcar} não está em {SAIDA.relative_to(ROOT)} (rode sem argumentos antes)", file=sys.stderr)
        return 1

    d = gravar(calcular())
    med = d["base"]["medianas"]
    print(f"base: {d['base']['n']} Reels com ≥ 5 dias — medianas: alcance {med['alcance']:g}, "
          f"salv. {med['salv_pct']:g} %, compart. {med['compart_pct']:g} %, assistido {med['pct_assistido']:g} %")
    lista = [x for x in d["acertos"] if not (a.pendentes and x.get("serie"))]
    if not lista:
        print("nenhum acerto" + (" pendente" if a.pendentes else ""))
        return 0
    print(("acertos pendentes:" if a.pendentes else "acertos:"))
    for x in lista:
        print(linha(x))
    return 10 if a.pendentes else 0


if __name__ == "__main__":
    sys.exit(main())
