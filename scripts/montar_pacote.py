"""Monta o pacote final de um vídeo em 05-render-pronto/<slug>/ (contrato: docs/contratos.md §9).

Uso: uv run python scripts/montar_pacote.py videos/<slug> [--capa capa-A.png] [--material nome.pdf] [--sem-material]
     uv run python scripts/montar_pacote.py carrosseis/<slug> [--material nome.pdf] [--sem-material]

CARROSSEL (09/11, docs/contratos.md §9c): carrosseis/<slug>/ com carrossel.md, slides/01.png… (3–10, 1080×1440,
gerados pelo scripts/gerar_carrossel.py) e material/<arquivo>.pdf quando há `palavra`. Portões: roteiro e imagem
(e pauta, se houver pesquisa) aprovados sobre carrosseis/<slug>. O pacote sai com `formato: "carrossel"`, os slides em
`arquivos.slides` e o selo. O QA do carrossel é o que este script confere (quantidade, formato e tamanho dos slides).

Requisitos:
- videos/<slug>/edicao/final.mp4            (render Remotion + loudnorm)
- videos/<slug>/capa/<capa escolhida>.png   (padrão: capa/capa.png, senão a única capa-*.png)
- videos/<slug>/edicao/legendas.srt
- videos/<slug>/qa/relatorio.md com a linha "RESULTADO: PASS"
- videos/<slug>/material/<arquivo>.pdf se o CTA for de palavra-chave (gerado pelo produtor-de-material)
- GAUNTLET (22/10, docs/gauntlet.md): portões pauta (se houver pesquisa), roteiro, imagem e corte APROVADOS e
  válidos em videos/<slug>/portoes.json. O pacote sai SELADO (`pacote.json.gauntlet`): o publicar.py recusa
  arquivo trocado depois do selo ou que os portões não viram.

MATERIAL: o pacote leva SÓ o PDF (decisão de 13/10: palavra-chave = sempre um PDF). dossie.md, fontes.json,
obra*.json/md, _fonte/ e afins ficam em videos/ — o publicar.py sobe o material para o R2 PÚBLICO, e estudo
ou cópia de obra nunca pode sair de casa (docs/contratos.md §1a).
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import portoes

RAIZ = portoes.ROOT  # = raiz do projeto (CONTENT_AI_ROOT só nos testes)
SLIDES_MIN, SLIDES_MAX = 3, 10  # o Instagram aceita 2–10 no carrossel; o modelo da Korvu tem pelo menos capa + item + CTA
SLIDE_TAMANHO = (1080, 1440)  # 3:4 (decisão de 09/11)


def falhar(msg: str) -> int:
    print(f"ERRO: {msg}")
    return 1


def escolher_material(pasta: Path, args: list[str], com_palavra: bool, palavra) -> tuple[Path | None, str | None]:
    """(pdf, erro). Só PDFs da raiz de material/ contam; o resto da pasta é estudo e não sai de casa."""
    rel = pasta.relative_to(RAIZ).as_posix()
    pdfs = sorted(p for p in (pasta / "material").glob("*.pdf") if p.is_file() and not p.name.startswith("."))
    if "--material" in args:
        material = pasta / "material" / args[args.index("--material") + 1]
        if material.suffix.lower() != ".pdf" or not material.is_file():
            return None, f"--material tem de ser um .pdf existente em {rel}/material/ ({material.name})"
        return material, None
    if com_palavra and "--sem-material" not in args:
        if not pdfs:
            return None, (f"o CTA é de palavra-chave ({palavra}) mas não há PDF em {rel}/material/ — rode o "
                          "produtor-de-material (scripts/gerar_material_pdf.py)")
        if len(pdfs) > 1:
            return None, ("há mais de um PDF em material/: " + ", ".join(p.name for p in pdfs)
                          + " — escolha com --material nome.pdf")
        return pdfs[0], None
    return None, None


def conferir_slides(slides: list[Path]) -> list[str]:
    from PIL import Image

    erros = []
    if not SLIDES_MIN <= len(slides) <= SLIDES_MAX:
        erros.append(f"{len(slides)} slides em slides/ (o carrossel leva de {SLIDES_MIN} a {SLIDES_MAX})")
    for s in slides:
        with Image.open(s) as im:
            if im.format not in ("PNG", "JPEG"):
                erros.append(f"{s.name}: formato {im.format} (só PNG ou JPEG)")
            if im.size != SLIDE_TAMANHO:
                erros.append(f"{s.name}: {im.size[0]}×{im.size[1]} (o modelo é {SLIDE_TAMANHO[0]}×{SLIDE_TAMANHO[1]}, 3:4)")
    return erros


def montar_carrossel(cdir: Path, args: list[str]) -> int:
    import yaml

    slug = cdir.name
    fonte = cdir / "carrossel.md"
    if not fonte.is_file():
        return falhar(f"{fonte.relative_to(RAIZ)} não existe")
    txt = fonte.read_text(encoding="utf-8")
    fm = (yaml.safe_load(txt.split("---", 2)[1]) or {}) if txt.startswith("---") else {}

    problemas = portoes.exigir(cdir)
    if problemas:
        return falhar("portões GAUNTLET sem APROVADO válido — o pacote não sai assim:\n  - " + "\n  - ".join(problemas)
                      + f"\n  (sinais: uv run python scripts/portoes.py estado carrosseis/{slug})")
    slides = sorted(p for p in (cdir / "slides").glob("[0-9]*.png") if p.is_file())
    erros = conferir_slides(slides)
    if erros:
        return falhar("slides fora do modelo:\n  - " + "\n  - ".join(erros))
    palavra = fm.get("palavra")
    material, erro = escolher_material(cdir, args, bool(palavra), palavra)
    if erro:
        return falhar(erro)

    dest = RAIZ / "05-render-pronto" / slug
    for sub in ("slides", "material"):
        (dest / sub).mkdir(parents=True, exist_ok=True)
    for velho in [*(dest / "slides").iterdir(), *(dest / "material").iterdir()]:  # pacote refeito: só o atual
        if velho.is_file():
            velho.unlink()
    for s in slides:
        shutil.copy2(s, dest / "slides" / s.name)
    grade = cdir / "slides" / "grade.jpg"
    if grade.exists():  # prévia para o autor; não vai ao ar
        shutil.copy2(grade, dest / "grade.jpg")
    if material:
        shutil.copy2(material, dest / "material" / material.name)
    shutil.copy2(fonte, dest / "carrossel.md")

    pacote = {
        "slug": slug,
        "formato": "carrossel",
        "criado_em": datetime.now().astimezone().isoformat(timespec="seconds"),
        "qa": "PASS",  # o QA do carrossel = conferir_slides acima + portões imagem/roteiro
        "arquivos": {
            "slides": [f"slides/{s.name}" for s in slides],
            "material": f"material/{material.name}" if material else None,
            "carrossel": "carrossel.md",
        },
        "cta_palavra": palavra,
        "material_titulo": fm.get("material_titulo"),
        "tema": fm.get("tema"),
        "pilar": fm.get("pilar"),
    }
    try:
        pacote["gauntlet"] = portoes.selar(cdir, dest, pacote["arquivos"])
    except portoes.ErroPortao as e:
        return falhar(str(e))
    (dest / "pacote.json").write_text(json.dumps(pacote, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Pacote de carrossel pronto: 05-render-pronto/{slug}/ ({len(slides)} slides)")
    for k, v in pacote["arquivos"].items():
        print(f"  {k:10} {v}")
    return 0


def main() -> int:
    args = [a for a in sys.argv[1:]]
    if not args:
        print(__doc__)
        return 1
    vdir = (RAIZ / args[0]).resolve()  # absoluto: o `/` mantém o caminho; resolve() casa /var com /private/var
    slug = vdir.name
    if portoes.eh_carrossel(vdir):
        return montar_carrossel(vdir, args)
    roteiro = json.loads((vdir / "roteiro.json").read_text(encoding="utf-8"))
    edl = json.loads((vdir / "edicao" / "edl.json").read_text(encoding="utf-8"))

    final = vdir / "edicao" / "final.mp4"
    if not final.exists():
        return falhar(f"{final.relative_to(RAIZ)} não existe — rode /renderizar")

    problemas = portoes.exigir(vdir)
    if problemas:
        return falhar("portões GAUNTLET sem APROVADO válido — o pacote não sai assim:\n  - " + "\n  - ".join(problemas)
                      + f"\n  (sinais: uv run python scripts/portoes.py estado videos/{slug})")

    relatorio = vdir / "qa" / "relatorio.md"
    if not relatorio.exists() or not re.search(r"^RESULTADO:\s*PASS\b", relatorio.read_text(encoding="utf-8"), re.M):
        return falhar("qa/relatorio.md sem 'RESULTADO: PASS' — o revisor-de-video precisa aprovar")

    capas = sorted((vdir / "capa").glob("capa*.png"))
    escolhida = None
    if "--capa" in args:
        escolhida = vdir / "capa" / args[args.index("--capa") + 1]
    elif (vdir / "capa" / "capa.png").exists():
        escolhida = vdir / "capa" / "capa.png"
    elif len([c for c in capas if c.name.startswith("capa-")]) == 1:
        escolhida = [c for c in capas if c.name.startswith("capa-")][0]
    if not escolhida or not escolhida.exists():
        return falhar("capa não definida — passe --capa capa-X.png ou crie capa/capa.png")

    srt = vdir / "edicao" / "legendas.srt"
    if not srt.exists():
        return falhar("edicao/legendas.srt não existe")

    com_palavra = roteiro.get("cta_tipo") == "palavra-material" or bool(roteiro.get("cta_palavra"))
    material, erro = escolher_material(vdir, args, com_palavra, roteiro.get("cta_palavra"))
    if erro:
        return falhar(erro)

    dest = RAIZ / "05-render-pronto" / slug
    for sub in ("video", "capa", "legendas", "material"):
        (dest / sub).mkdir(parents=True, exist_ok=True)

    shutil.copy2(final, dest / "video" / "video-final.mp4")
    variantes = []
    for v in sorted((vdir / "edicao").glob("final-L01*.mp4")):
        nome = v.name.replace("final-", "video-final-")
        shutil.copy2(v, dest / "video" / nome)
        variantes.append(f"video/{nome}")
    shutil.copy2(escolhida, dest / "capa" / "capa.png")
    for extra in capas:
        if extra != escolhida:
            shutil.copy2(extra, dest / "capa" / extra.name)
    grade = vdir / "capa" / "grade-3x4.png"
    if grade.exists():
        shutil.copy2(grade, dest / "capa" / grade.name)
    shutil.copy2(srt, dest / "legendas" / "legendas.srt")
    # SRT de cada variante (CGI-C30, 08/11). Fora do selo: a área do PORTÃO-CORTE é `legendas.srt` e mudá-la
    # venceria o veredicto dos outros vídeos; o publicar.py não sobe SRT.
    legendas_variantes = []
    for s in sorted((vdir / "edicao").glob("legendas-L01*.srt")):
        shutil.copy2(s, dest / "legendas" / s.name)
        legendas_variantes.append(f"legendas/{s.name}")
    for velho in (dest / "material").iterdir():      # pacote refeito: tira material de uma versão anterior
        if velho.is_file() and (material is None or velho.name != material.name):
            velho.unlink()
            print(f"  (removido do pacote: material/{velho.name})")
    if material:
        shutil.copy2(material, dest / "material" / material.name)
    shutil.copy2(vdir / "roteiro.md", dest / "roteiro.md")
    shutil.copy2(relatorio, dest / "qa-relatorio.md")

    pacote = {
        "slug": slug,
        "criado_em": datetime.now().astimezone().isoformat(timespec="seconds"),
        "duracao": edl.get("duracao_saida"),
        "qa": "PASS",
        "arquivos": {
            "video": "video/video-final.mp4",
            "variantes": variantes,
            "capa": "capa/capa.png",
            "legendas": "legendas/legendas.srt",
            "legendas_variantes": legendas_variantes,
            "material": f"material/{material.name}" if material else None,
            "roteiro": "roteiro.md",
            "qa": "qa-relatorio.md",
        },
        "cta_palavra": roteiro.get("cta_palavra"),
        "material_titulo": roteiro.get("material_titulo"),
        "tema": roteiro.get("tema"),
        "pilar": roteiro.get("pilar"),
    }
    try:
        pacote["gauntlet"] = portoes.selar(vdir, dest, pacote["arquivos"])
    except portoes.ErroPortao as e:
        return falhar(str(e))
    (dest / "pacote.json").write_text(json.dumps(pacote, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Pacote pronto: 05-render-pronto/{slug}/")
    for k, v in pacote["arquivos"].items():
        print(f"  {k:10} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
