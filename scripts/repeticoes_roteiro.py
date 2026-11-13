"""Detector de FÓRMULA nos roteiros — o que o ouvido do autor pega e a gente não via (07/11).

Ele reclamou: "na minha leitura", "pra isso… são dois", "eu tô estudando pra virar AI Engineer", "hoje custa…",
"salva… comenta a palavra…" saem iguais em todo roteiro; e as frases são todas curtas, ponto a ponto, sem ligação.
Este script mede isso para o diretor-de-naturalidade (e o PORTÃO-ROTEIRO) não depender só de impressão.

Uso:
  uv run python scripts/repeticoes_roteiro.py videos/<slug> [videos/<slug2> ...] [--historico 12] [--saida arq.md]

  --historico N  compara também com os N vídeos mais recentes de videos/ (padrão 12) — a repetição que cansa é entre
                 vídeos que o mesmo seguidor vê em sequência.

O que sai (markdown):
  1. Expressões (3–6 palavras) que aparecem em 2+ roteiros — a fórmula entre vídeos.
  2. Abertura e fecho: a 2.ª linha e as 2 últimas de cada roteiro, lado a lado (o "molde" fica visível).
  3. Por roteiro: começos de frase repetidos, muletas de pivô ("só que", "ou seja", "olha"…), e o ritmo
     (frases curtas seguidas, variação de tamanho) — o "picotado" de que ele reclamou.
Não reescreve nada: só aponta.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Palavras que sozinhas não fazem expressão (um n-grama só delas não conta).
VAZIAS = set("""
a o as os e é de do da dos das em no na nos nas um uma uns umas que pra para por com se mas ou eu você ele ela
isso esse essa este esta aqui lá já não sim tá tô te me meu minha seu sua dele dela mais muito também só ao à
""".split())

# Pivôs e muletas de roteiro de IA: com moderação, viram assinatura de máquina.
PIVOS = {
    "só que": r"\bsó que\b",
    "ou seja": r"\bou seja\b",
    "olha (só/o/que)": r"\bolha\b",
    "na minha leitura": r"\bna minha leitura\b",
    "e aí": r"(^|[.!?]\s*)e aí\b",
    "então,": r"(^|[.!?]\s*)então\b",
    "agora,": r"(^|[.!?]\s*)agora\b",
    "o problema": r"\bo problema\b",
    "hoje (custa/sai)": r"\bhoje\b",
    "de verdade": r"\bde verdade\b",
    "a sacada": r"\bsacada\b",
}


def normalizar(t: str) -> str:
    t = re.sub(r"\*\*|__|`", "", t)
    t = t.replace(" / ", " ").replace("//", " ")
    return re.sub(r"\s+", " ", t).strip()


def palavras(t: str) -> list[str]:
    return re.findall(r"[a-zà-úç0-9%]+", t.lower())


def ler_falas(pasta: Path) -> list[str] | None:
    js = pasta / "roteiro.json"
    if not js.exists():
        return None
    try:
        d = json.loads(js.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    linhas = d.get("linhas") or []
    falas = []
    for l in linhas:
        lid = str(l.get("id", ""))
        if re.fullmatch(r"L\d+[B-Z]", lid):  # hooks alternativos não contam
            continue
        f = normalizar(l.get("fala") or "")
        if f:
            falas.append(f)
    return falas or None


def frases(falas: list[str]) -> list[str]:
    out = []
    for f in falas:
        out += [s.strip() for s in re.split(r"(?<=[.!?])\s+", f) if s.strip()]
    return out


def ngramas(ws: list[str], n: int) -> set[tuple[str, ...]]:
    return {tuple(ws[i:i + n]) for i in range(len(ws) - n + 1)}


def expressoes_compartilhadas(roteiros: dict[str, list[str]], alvo: set[str]) -> list[tuple[str, list[str]]]:
    onde: dict[tuple[str, ...], set[str]] = defaultdict(set)
    for slug, falas in roteiros.items():
        for f in frases(falas):
            ws = palavras(f)
            for n in range(3, 7):
                for g in ngramas(ws, n):
                    if sum(w not in VAZIAS for w in g) >= 1 and not all(w in VAZIAS for w in g[:1] + g[-1:]):
                        onde[g].add(slug)
    achados = {g: s for g, s in onde.items() if len(s) >= 2 and s & alvo}
    # tira n-grama contido num maior com os mesmos roteiros
    finais = []
    for g, s in sorted(achados.items(), key=lambda x: (-len(x[0]), -len(x[1]))):
        txt = " ".join(g)
        if any(txt in f2 and s <= s2 for f2, s2 in finais):
            continue
        finais.append((txt, s))
    finais.sort(key=lambda x: (-len(x[1]), -len(x[0])))
    return [(t, sorted(s)) for t, s in finais]


def ritmo(falas: list[str]) -> dict:
    fr = frases(falas)
    tam = [len(palavras(f)) for f in fr]
    if not tam:
        return {}
    curtas_seguidas = maior = 0
    for t in tam:
        curtas_seguidas = curtas_seguidas + 1 if t <= 9 else 0
        maior = max(maior, curtas_seguidas)
    conectadas = sum(1 for f in fr if re.search(r",|\b(porque|quando|que|e|mas|então|só que)\b", f.lower()))
    return {
        "frases": len(fr),
        "media": round(statistics.mean(tam), 1),
        "desvio": round(statistics.pstdev(tam), 1),
        "curtas_<=9": sum(t <= 9 for t in tam),
        "maior_sequencia_curtas": maior,
        "frases_com_ligacao_%": round(100 * conectadas / len(fr)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pastas", nargs="+", type=Path)
    ap.add_argument("--historico", type=int, default=12)
    ap.add_argument("--saida", type=Path)
    a = ap.parse_args()

    alvo: dict[str, list[str]] = {}
    for p in a.pastas:
        p = p if p.is_absolute() else RAIZ / p
        f = ler_falas(p)
        if f is None:
            print(f"aviso: {p} sem roteiro.json legível", file=sys.stderr)
            continue
        alvo[p.name] = f
    if not alvo:
        print("nenhum roteiro lido", file=sys.stderr)
        return 1

    todos = dict(alvo)
    if a.historico:
        outros = sorted((d for d in (RAIZ / "videos").iterdir() if d.is_dir() and d.name[:2] == "20" and d.name not in alvo),
                        key=lambda d: (d / "roteiro.json").stat().st_mtime if (d / "roteiro.json").exists() else 0,
                        reverse=True)
        for d in outros[: a.historico]:
            f = ler_falas(d)
            if f:
                todos[d.name] = f

    L = [f"# Repetições e ritmo — {len(alvo)} roteiro(s) analisado(s), comparados com {len(todos) - len(alvo)} recentes\n"]

    L.append("## 1. Expressões que se repetem ENTRE roteiros (fórmula)\n")
    comp = expressoes_compartilhadas(todos, set(alvo))
    if comp:
        L.append("| Expressão | Em quantos | Onde |\n|---|---|---|")
        for t, s in comp[:40]:
            L.append(f"| \"{t}\" | {len(s)} | {', '.join(x.replace('2026-', '') for x in s)} |")
    else:
        L.append("Nenhuma expressão de 3+ palavras repetida entre roteiros.")

    L.append("\n## 2. Molde de abertura e fecho (2.ª linha e as 2 últimas)\n")
    L.append("| Roteiro | 2.ª linha | Penúltima | Última |\n|---|---|---|---|")
    for slug, f in todos.items():
        marca = "**" if slug in alvo else ""
        seg = f[1] if len(f) > 1 else ""
        L.append(f"| {marca}{slug.replace('2026-', '')}{marca} | {seg} | {f[-2] if len(f) > 1 else ''} | {f[-1]} |")

    L.append("\n## 3. Por roteiro: pivôs, começos repetidos e ritmo\n")
    for slug, f in alvo.items():
        texto = " ".join(f).lower()
        fr = frases(f)
        piv = {k: len(re.findall(rx, texto)) for k, rx in PIVOS.items()}
        piv = {k: v for k, v in piv.items() if v}
        com = Counter(" ".join(palavras(x)[:2]) for x in fr)
        rep = {k: v for k, v in com.items() if v >= 2}
        r = ritmo(f)
        L.append(f"### {slug}")
        L.append(f"- Pivôs/muletas: {', '.join(f'{k} ×{v}' for k, v in piv.items()) or '—'}")
        L.append(f"- Frases que começam igual: {', '.join(f'\"{k}…\" ×{v}' for k, v in rep.items()) or '—'}")
        L.append(f"- Ritmo: {r['frases']} frases, média {r['media']} palavras (desvio {r['desvio']}); "
                 f"{r['curtas_<=9']} curtas (≤ 9); maior sequência de curtas seguidas: {r['maior_sequencia_curtas']}; "
                 f"frases com ligação (vírgula/conector): {r['frases_com_ligacao_%']} %")
        alerta = []
        if r["maior_sequencia_curtas"] >= 5:
            alerta.append("picotado: 5+ frases curtas seguidas, sem respiro de frase longa")
        if r["desvio"] < 3.5:
            alerta.append("ritmo monótono: as frases têm todas o mesmo tamanho")
        if alerta:
            L.append(f"- ⚠ {'; '.join(alerta)}")
        L.append("")

    out = "\n".join(L) + "\n"
    if a.saida:
        a.saida.write_text(out, encoding="utf-8")
        print(f"→ {a.saida}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
