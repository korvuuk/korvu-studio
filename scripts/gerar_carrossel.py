#!/usr/bin/env python3
"""Gera os slides de um CARROSSEL da Korvu (PNG 1080×1440, 3:4) no modelo aprovado pelo autor em 09/11.

Modelo e regras de conteúdo: `00-marca/modelo-carrossel.md`. Estrutura copiada da referência @pedro___neres
(`01-ideias/pesquisas/referencias-carrossel/2026-11-09-plataformas-gratuitas/`), visual nosso:
foto do autor em P&B (frame da PAUSA DA CAPA) + LOGOS OFICIAIS na capa, cabeçalho limpo (sem korvu./@),
Inter Tight 900 em caixa alta, um acento laranja, miolo escuro com luz laranja. Motor: Chrome headless.

ENTRADA — `carrosseis/<slug>/carrossel.md`: frontmatter YAML + um bloco por slide, aberto por `=== <tipo>`.
Dentro do bloco, linhas `chave: valor` no começo; o resto é o corpo (o texto do item).

    ---
    palavra: ESTUDO                 # a palavra do CTA (sem acento, ≤ ~6 letras)
    ---
    === capa
    foto: fotos/capa.png            # frame da pausa da capa (sai em P&B)
    foto_posicao: center 12%        # opcional (CSS background-position)
    foto_brilho: 1.4                # opcional; gravação escura fica preta em P&B (padrão 1.12)
    numero: 6                       # sai no laranja, antes do título
    titulo: cursos | grátis de IA   # " | " quebra a linha
    titulo_tamanho: 104             # opcional; padrão 124 px — diminuir quando a linha não cabe
    sub: das maiores instituições do mundo, do zero ao avançado
    logos: harvard, google, microsoft, helsinki, anthropic, huggingface-simbolo   # até 6, em volta da cabeça
    === item
    logo: google                    # nome em 00-marca/assets/logos-terceiros/ (sem .png) ou caminho relativo ao .md
    nome: Google Skills
    link: skills.google
    print: prints/google.png        # a página oficial (sai na tela do notebook)
    tags: grátis*, 45 min, selo digital, inglês   # "*" = etiqueta em destaque (laranja)
    resumo: Introduction to Generative AI · 45 min   # a linha deste item no slide de resumo
    Aula do Google de 45 minutos que explica IA generativa… (≤ 30 palavras)
    === resumo
    titulo: salva essa lista
    sub: na ordem em que eu faria
    === cta
    foto: fotos/cta.png
    texto: que eu te mando o PDF com os 6 links

Tipos: capa · item · resumo · cta. O 1.º slide tem de ser `capa` e o último `cta`. O `resumo` lista sozinho
todos os `item` (logo + nome + linha `resumo:`), numerados.

SAÍDA (na pasta do .md): `slides/01.png`… + `slides/grade.jpg` (3 por linha, para conferir olhando).
Confere: 3–10 slides (teto da API de carrossel do Instagram), capa primeiro, CTA no fim, palavra válida,
foto/logo/print existem, até 6 logos na capa, corpo ≤ 45 palavras por slide (aviso).

Uso:
  uv run python scripts/gerar_carrossel.py carrosseis/<slug>/carrossel.md [--html] [--so 3]
"""
from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
LOGOS = RAIZ / "00-marca" / "assets" / "logos-terceiros"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
LARGURA, ALTURA = 1080, 1440
MAX_SLIDES = 10
ACENTO = "#E85002"

FONTES_GOOGLE = ('<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;800;900'
                 '&display=swap" rel="stylesheet">')

# Lugares dos logos na capa: em volta da cabeça, nunca sobre o rosto (rosto ≈ x 365–787, y 270–790 com a
# foto da pausa da capa em `foto_posicao: center 12%`). A ordem de `logos:` preenche estes lugares.
LUGARES = [
    "left:50px; top:120px; width:230px; height:200px",
    "left:400px; top:70px; width:280px; height:130px",
    "right:50px; top:110px; width:270px; height:120px",
    "left:40px; top:370px; width:220px; height:200px",
    "right:40px; top:290px; width:250px; height:100px",
    "right:70px; top:430px; width:170px; height:160px",
]

CSS = """
* { margin: 0; box-sizing: border-box; }
html, body { width: 1080px; height: 1440px; overflow: hidden; background: #000; }
body { font-family: "Inter Tight", sans-serif; color: #fff; position: relative; -webkit-font-smoothing: antialiased; }

.foto { position: absolute; inset: 0; background-size: cover; background-repeat: no-repeat;
        filter: grayscale(1) brightness(1.12) contrast(1.08); }
.sombra { position: absolute; inset: 0;
          background: linear-gradient(180deg, rgba(0,0,0,.25) 0%, rgba(0,0,0,0) 18%, rgba(0,0,0,0) 52%, rgba(0,0,0,.85) 80%, #000 100%); }

.logo { position: absolute; background: #fff; display: flex; align-items: center; justify-content: center;
        box-shadow: 0 12px 34px rgba(0,0,0,.4); }
.logo img { max-width: 82%; max-height: 74%; object-fit: contain; }

.titulo { font-weight: 900; text-transform: uppercase; letter-spacing: -.028em; word-spacing: .06em; line-height: .98; }
.titulo .n { color: __ACENTO__; }

.bloco { position: absolute; left: 60px; right: 60px; bottom: 96px; }
.bloco .titulo { font-size: 124px; }
.bloco .sub { margin-top: 26px; font-weight: 500; font-size: 38px; line-height: 1.22; letter-spacing: -.01em; opacity: .92; }

.item { position: absolute; inset: 0;
        background: radial-gradient(ellipse 90% 55% at 50% 40%, rgba(232,80,2,.22), rgba(0,0,0,0) 70%), #0b0a09; }
.cab { position: absolute; top: 96px; left: 70px; right: 70px; display: flex; gap: 34px; align-items: center; }
.cab .logo { position: static; width: 168px; height: 168px; flex: none; }
.cab .nome { font-size: 66px; }
.cab .link { margin-top: 12px; font-weight: 500; font-size: 28px; opacity: .6; letter-spacing: -.005em; }
/* texto e etiquetas descem juntos: frase de 4 linhas empurra as etiquetas em vez de passar por cima */
.meio { position: absolute; top: 340px; left: 70px; right: 70px; display: flex; flex-direction: column; gap: 40px; }
.texto { font-weight: 500; font-size: 40px; line-height: 1.32; letter-spacing: -.012em; text-align: center; text-wrap: pretty; }
.texto b { font-weight: 800; }
.tags { display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }
.tag { border: 1.5px solid rgba(255,255,255,.35); border-radius: 999px; padding: 10px 22px; font-weight: 600; font-size: 26px; }
.tag.forte { background: __ACENTO__; border-color: __ACENTO__; }
.note { position: absolute; left: 70px; right: 70px; top: 720px; bottom: -40px; background: #1b1b1d; border-radius: 26px 26px 0 0;
        padding: 22px 22px 0; box-shadow: 0 -20px 80px rgba(232,80,2,.18), 0 30px 60px rgba(0,0,0,.6); }
.note .tela { width: 100%; height: 100%; border-radius: 10px 10px 0 0; background-color: #fff;
              background-size: 100% auto; background-repeat: no-repeat; background-position: top center; }

.resumo { position: absolute; inset: 0; background: #0b0a09; padding: 110px 70px 0; }
.resumo .titulo { font-size: 92px; }
.resumo .sub { margin-top: 18px; font-weight: 500; font-size: 32px; opacity: .65; }
.linhas { margin-top: 56px; }
.linha { display: flex; align-items: center; gap: 28px; padding: 26px 0; border-top: 1px solid rgba(255,255,255,.14); }
.linha:last-child { border-bottom: 1px solid rgba(255,255,255,.14); }
.linha .logo { position: static; width: 104px; height: 104px; flex: none; box-shadow: none; }
.linha .q { font-weight: 800; font-size: 36px; letter-spacing: -.02em; }
.linha .d { margin-top: 6px; font-weight: 500; font-size: 26px; opacity: .65; }
.linha .nr { margin-left: auto; font-weight: 900; font-size: 44px; color: __ACENTO__; }
""".replace("__ACENTO__", ACENTO)

TIPOS = {"capa", "item", "resumo", "cta"}


def inline(t: str) -> str:
    t = html.escape(t)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)


def titulo(t: str) -> str:
    return "<br>".join(inline(p.strip()) for p in t.split("|"))


def ler(src: Path) -> tuple[dict, list[dict]]:
    txt = src.read_text(encoding="utf-8")
    fm: dict = {}
    if txt.startswith("---"):
        _, bruto, txt = txt.split("---", 2)
        fm = yaml.safe_load(bruto) or {}
    slides = []
    for bloco in re.split(r"^===\s*", txt, flags=re.M)[1:]:
        linhas = bloco.splitlines()
        s = {"tipo": linhas[0].strip().lower(), "corpo": []}
        campos = True
        for ln in linhas[1:]:
            m = re.match(r"^([a-z_]+):\s*(.*)$", ln)
            if campos and m:
                s[m.group(1)] = m.group(2).strip()
            else:
                if ln.strip():
                    campos = False
                s["corpo"].append(ln)
        slides.append(s)
    return fm, slides


def logo_path(nome: str, base: Path) -> Path:
    p = base / nome
    return p if p.suffix and p.exists() else LOGOS / f"{nome}.png"


def lista(campo: str) -> list[str]:
    return [x.strip() for x in campo.split(",") if x.strip()]


def validar(fm: dict, slides: list[dict], base: Path) -> tuple[list[str], list[str]]:
    erros, avisos = [], []
    if not 3 <= len(slides) <= MAX_SLIDES:
        erros.append(f"{len(slides)} slides; o carrossel tem de ter 3–{MAX_SLIDES}")
    if slides and slides[0]["tipo"] != "capa":
        erros.append("o 1.º slide tem de ser `capa`")
    if slides and slides[-1]["tipo"] != "cta":
        erros.append("o último slide tem de ser `cta`")
    palavra = str(fm.get("palavra", ""))
    if not re.fullmatch(r"[A-Z]{2,8}", palavra):
        erros.append(f"palavra inválida: {palavra!r} (CAIXA ALTA, sem acento, ≤ ~6 letras)")
    for i, s in enumerate(slides, 1):
        t = s["tipo"]
        if t not in TIPOS:
            erros.append(f"slide {i}: tipo desconhecido {t!r}")
        for chave in ("foto", "print"):
            if s.get(chave) and not (base / s[chave]).exists():
                erros.append(f"slide {i}: {chave} não existe: {s[chave]}")
        if t in ("capa", "cta") and not s.get("foto"):
            erros.append(f"slide {i}: `{t}` precisa de `foto:` (frame da pausa da capa)")
        logos = lista(s.get("logos", "")) + ([s["logo"]] if s.get("logo") else [])
        for lg in logos:
            if not logo_path(lg, base).exists():
                erros.append(f"slide {i}: logo não existe: {lg} (baixe o OFICIAL para {LOGOS.relative_to(RAIZ)}/)")
        if t == "capa" and len(lista(s.get("logos", ""))) > len(LUGARES):
            erros.append(f"slide {i}: no máximo {len(LUGARES)} logos na capa")
        if t == "item":
            for chave in ("logo", "nome", "print"):
                if not s.get(chave):
                    erros.append(f"slide {i}: `item` sem `{chave}:`")
        n = len(re.findall(r"\w+", " ".join(s["corpo"])))
        if n > 45:
            avisos.append(f"slide {i}: {n} palavras no corpo (alvo ≤ 30, teto 45)")
    return erros, avisos


def img_logo(nome: str, base: Path, estilo: str = "") -> str:
    st = f' style="{estilo}"' if estilo else ""
    return f'<div class="logo"{st}><img src="{logo_path(nome, base).resolve().as_uri()}"></div>'


def foto(s: dict, base: Path) -> str:
    url = (base / s["foto"]).resolve().as_uri()
    pos = s.get("foto_posicao", "center 12%")
    # gravação com pouca luz fica escura demais em P&B: `foto_brilho: 1.4` (padrão 1.12)
    brilho = s.get("foto_brilho", "1.12")
    return (f'<div class="foto" style="background-image:url({url}); background-position:{pos}; '
            f'filter:grayscale(1) brightness({brilho}) contrast(1.08)"></div><div class="sombra"></div>')


def tamanho(s: dict) -> str:
    # título longo ("6 CERTIFICADOS") não cabe em 124 px numa linha: `titulo_tamanho: 104`
    return f' style="font-size:{int(s["titulo_tamanho"])}px"' if s.get("titulo_tamanho") else ""


def slide_html(s: dict, slides: list[dict], fm: dict, base: Path) -> str:
    tipo = s["tipo"]
    if tipo == "capa":
        num = f'<span class="n">{inline(s["numero"])}</span> ' if s.get("numero") else ""
        miolo = (foto(s, base)
                 + "".join(img_logo(lg, base, LUGARES[k]) for k, lg in enumerate(lista(s.get("logos", ""))))
                 + f'<div class="bloco"><div class="titulo"{tamanho(s)}>{num}{titulo(s.get("titulo", ""))}</div>'
                 + (f'<div class="sub">{inline(s["sub"])}</div>' if s.get("sub") else "") + "</div>")
    elif tipo == "item":
        tags = "".join(f'<span class="tag{" forte" if t.endswith("*") else ""}">{inline(t.rstrip("*"))}</span>'
                       for t in lista(s.get("tags", "")))
        tela = (base / s["print"]).resolve().as_uri()
        miolo = (f'<div class="item"></div><div class="cab">{img_logo(s["logo"], base)}'
                 f'<div><div class="titulo nome">{inline(s["nome"])}</div>'
                 f'<div class="link">{inline(s.get("link", ""))}</div></div></div>'
                 f'<div class="meio"><div class="texto">{inline(" ".join(x.strip() for x in s["corpo"] if x.strip()))}</div>'
                 + (f'<div class="tags">{tags}</div>' if tags else "") + "</div>"
                 + f'<div class="note"><div class="tela" style="background-image:url({tela})"></div></div>')
    elif tipo == "resumo":
        itens = [x for x in slides if x["tipo"] == "item"]
        linhas = "".join(f'<div class="linha">{img_logo(it["logo"], base)}<div><div class="q">{inline(it["nome"])}</div>'
                         f'<div class="d">{inline(it.get("resumo", ""))}</div></div><div class="nr">{k}</div></div>'
                         for k, it in enumerate(itens, 1))
        miolo = (f'<div class="resumo"><div class="titulo">{titulo(s.get("titulo", "salva essa lista"))}</div>'
                 + (f'<div class="sub">{inline(s["sub"])}</div>' if s.get("sub") else "")
                 + f'<div class="linhas">{linhas}</div></div>')
    else:  # cta — palavra sem ponto (decisão de 21/10)
        miolo = (foto(s, base)
                 + f'<div class="bloco"><div class="titulo"{tamanho(s)}>comenta<br><span class="n">{html.escape(str(fm["palavra"]))}</span></div>'
                 + f'<div class="sub">{inline(s.get("texto", ""))}</div></div>')
    return (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">{FONTES_GOOGLE}<style>{CSS}</style>'
            f'</head><body>{miolo}</body></html>')


def fotografar(doc: str, dst: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        pagina = Path(tmp) / "slide.html"
        pagina.write_text(doc, encoding="utf-8")
        cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
               f"--window-size={LARGURA},{ALTURA}", "--force-device-scale-factor=1",
               # dá tempo às fontes do Google; sem ele sai com a fonte de sistema.
               "--virtual-time-budget=6000", f"--screenshot={dst}", pagina.as_uri()]
        # O Chrome headless às vezes trava num slide (09/11): limite curto e uma 2.ª tentativa.
        for tentativa in (1, 2):
            dst.unlink(missing_ok=True)
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            except subprocess.TimeoutExpired:
                continue
            if r.returncode == 0 and dst.exists() and dst.stat().st_size > 5000:
                return
        raise RuntimeError(f"Chrome não gerou {dst.name} em 2 tentativas")


def grade(pngs: list[Path], dst: Path) -> None:
    from PIL import Image
    w, h, gap, por_linha = 360, 480, 10, 3
    linhas = (len(pngs) + por_linha - 1) // por_linha
    img = Image.new("RGB", (w * por_linha + gap * (por_linha - 1), h * linhas + gap * (linhas - 1)), "#888888")
    for k, p in enumerate(pngs):
        img.paste(Image.open(p).convert("RGB").resize((w, h)), ((k % por_linha) * (w + gap), (k // por_linha) * (h + gap)))
    img.save(dst, quality=88)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("md", type=Path)
    ap.add_argument("--html", action="store_true", help="grava também o HTML de cada slide (depuração)")
    ap.add_argument("--so", type=int, help="gera só este slide (número) e remonta a grade")
    a = ap.parse_args()
    src = a.md.resolve()
    base = src.parent
    fm, slides = ler(src)
    erros, avisos = validar(fm, slides, base)
    for av in avisos:
        print("AVISO:", av)
    if erros:
        for e in erros:
            print("ERRO:", e)
        return 1
    saida = base / "slides"
    saida.mkdir(exist_ok=True)
    if not a.so:
        for velho in saida.glob("*.png"):
            velho.unlink()
    for i, s in enumerate(slides, 1):
        if a.so and i != a.so:
            continue
        doc = slide_html(s, slides, fm, base)
        if a.html:
            (saida / f"{i:02d}.html").write_text(doc, encoding="utf-8")
        dst = saida / f"{i:02d}.png"
        fotografar(doc, dst)
        print(f"ok  {dst.relative_to(base)}  ({s['tipo']})")
    pngs = [saida / f"{i:02d}.png" for i in range(1, len(slides) + 1)]
    grade([p for p in pngs if p.exists()], saida / "grade.jpg")
    print(f"ok  slides/grade.jpg  — {len(slides)} slides")
    return 0


if __name__ == "__main__":
    sys.exit(main())
