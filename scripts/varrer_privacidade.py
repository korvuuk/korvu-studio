#!/usr/bin/env python3
"""Varredura de privacidade e segredos do repositório (roda no CI e antes de todo pull request).

Procura, em todo arquivo de texto versionável: chaves e tokens com cara de reais, caminhos absolutos com nome de
usuário, e-mails fora dos domínios de exemplo, IDs numéricos longos (contas, páginas, mídias da Meta), URLs de
webhook e domínios públicos de bucket. Só biblioteca padrão.

Uso (da raiz):
  python3 -I scripts/varrer_privacidade.py                 # varre o repositório; exit 1 se achar algo
  python3 -I scripts/varrer_privacidade.py --nomes lista.txt   # também procura cada linha de um arquivo PRIVADO
                                                                # (nomes reais, @ de contas) — nunca versione a lista

Falso positivo? Prefira trocar o dado por um fictício. Se for mesmo legítimo, acrescente-o a PERMITIDOS abaixo
com o motivo, no mesmo pull request.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

PULAR_PASTAS = {".git", "node_modules", ".venv", ".next", "__pycache__", "out", "_saida"}
PULAR_ARQUIVOS = {"uv.lock", "package-lock.json", "varrer_privacidade.py"}
MAX_BYTES = 5_000_000

PADROES: list[tuple[str, re.Pattern[str]]] = [
    ("caminho absoluto com usuário", re.compile(r"(?<![\w.])/(?:Users|home)/[A-Za-z0-9._-]+/|[A-Z]:\\\\?Users\\\\?[A-Za-z]|-Users-(?!voce-)[A-Za-z0-9._]+-")),
    ("chave OpenAI/Anthropic", re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}")),
    ("token da Meta", re.compile(r"\bEAA[A-Za-z0-9]{30,}")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("chave AWS", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("token do GitHub", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}")),
    ("token do Slack", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("chave Google", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}")),
    ("chave ElevenLabs", re.compile(r"\bsk_[a-f0-9]{40,}")),
    ("URN do LinkedIn", re.compile(r"urn:li:(?:person|member):[A-Za-z0-9_-]+")),
    ("webhook", re.compile(r"[a-z0-9-]+\.n8n\.cloud|hooks\.slack\.com/services|discord(?:app)?\.com/api/webhooks|hooks\.zapier\.com")),
    ("domínio público de bucket R2", re.compile(r"\bpub-[a-f0-9]{16,}\.r2\.dev")),
    ("e-mail", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")),
    ("ID numérico longo", re.compile(r"(?<![\w.,\-/#])\d{15,}(?![\w.])")),
]

# Valores fictícios ou públicos que os testes, a documentação e o Supabase local usam de propósito.
PERMITIDOS = re.compile(
    r"@(?:example\.(?:com|org|invalid)|exemplo\.\w+|[a-z.]*\.test|[a-z.]*\.invalid|email\.com|users\.noreply\.github\.com)"
    r"|noreply@anthropic\.com"
    r"|^EAAG(?:teste|pagina)"                      # tokens falsos dos testes (tests/publicar, metricas, comentarios)
    r"|\.eyJpc3MiOiJzdXBhYmFzZS1kZW1v"             # chave de demonstração pública do Supabase local ("supabase-demo")
    r"|^(?:17841400000000000|100000000000001|0{12,}\d{0,4})$"
)


def arquivos() -> list[Path]:
    out = []
    for p in RAIZ.rglob("*"):
        if not p.is_file() or p.name in PULAR_ARQUIVOS or any(x in PULAR_PASTAS for x in p.relative_to(RAIZ).parts):
            continue
        if p.stat().st_size > MAX_BYTES:
            continue
        out.append(p)
    return out


def ler(p: Path) -> str | None:
    try:
        b = p.read_bytes()
    except OSError:
        return None
    if b"\0" in b[:4096]:
        return None  # binário (imagem, fonte)
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nomes", type=Path, help="arquivo privado: um termo por linha (nomes reais, @ de contas)")
    args = ap.parse_args()
    extras = []
    if args.nomes:
        termos = [t.strip() for t in args.nomes.read_text(encoding="utf-8").splitlines() if t.strip() and not t.startswith("#")]
        extras = [("termo da lista privada", re.compile(re.escape(t), re.I)) for t in termos]
    achados = 0
    for p in sorted(arquivos()):
        txt = ler(p)
        if txt is None:
            continue
        for n, linha in enumerate(txt.splitlines(), 1):
            for nome, rx in PADROES + extras:
                for m in rx.finditer(linha):
                    if nome != "termo da lista privada" and PERMITIDOS.search(m.group(0)):
                        continue
                    achados += 1
                    trecho = m.group(0) if nome == "termo da lista privada" else m.group(0)[:12] + "…"
                    print(f"✗ {p.relative_to(RAIZ)}:{n}: {nome}: {trecho}")
    if achados:
        print(f"\n{achados} achado(s). Troque por dado fictício ou, se for legítimo, explique em PERMITIDOS.")
        return 1
    print("✓ nenhum segredo, caminho pessoal, e-mail ou ID real encontrado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
