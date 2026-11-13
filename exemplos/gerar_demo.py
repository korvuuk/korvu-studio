#!/usr/bin/env python3
"""Recria exemplos/estudio-demo/ e exemplos/registros-demo/ do zero — dados FICTÍCIOS para o painel.

Tudo é inventado: quatro vídeos de IA para iniciantes em fases diferentes do pipeline, os portões do GAUNTLET de cada
um (registrados pelo próprio scripts/portoes.py, para as impressões baterem), uma publicação com métricas, leituras do
perfil e registros sintéticos do Claude Code (tela de tokens). Nenhuma pessoa real, nenhum dado de conta real, nenhuma
mídia pesada (capas são PNG lisos gerados aqui; as gravações entram pelo manifesto ARQUIVADO.json).

Determinístico: a mesma data-base gera os mesmos arquivos, com as mesmas datas de modificação. As telas do painel
contam "últimos 30 dias" a partir de hoje — para a demo parecer recente, gere de novo com --hoje <data de hoje>.

Uso (da raiz do repositório):
  uv run python exemplos/gerar_demo.py                 # data-base padrão (2026-11-12)
  uv run python exemplos/gerar_demo.py --hoje 2027-03-01
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import struct
import sys
import zlib
from pathlib import Path

import yaml

EXEMPLOS = Path(__file__).resolve().parent
CODIGO = EXEMPLOS.parent
DEMO = EXEMPLOS / "estudio-demo"
REG = EXEMPLOS / "registros-demo"
HOJE_PADRAO = "2026-11-12"
FUSO = dt.timezone(dt.timedelta(hours=-3))  # America/Sao_Paulo (sem horário de verão)
FUSO_NOME = "America/Sao_Paulo"

# A raiz demo empresta do repositório só o que o sincronizador lê e não é dado: a equipe, a marca, o código.
LINKS_RAIZ = {".claude": "../../.claude", "00-marca": "../../00-marca", "remotion": "../../remotion",
              "scripts": "../../scripts", ".python-version": "../../.python-version"}
# painel/ é uma pasta própria: o biblioteca.yaml do repositório cita capas de pacotes reais, então a demo tem o seu.
LINKS_PAINEL = {"equipe.yaml": "../../../painel/equipe.yaml", "cambio.yaml": "../../../painel/cambio.yaml",
                "web": "../../../painel/web", "supabase": "../../../painel/supabase"}


# ───────────────────────── utilidades ─────────────────────────

class Raiz:
    def __init__(self, base: Path, mtime: float):
        self.base, self.mtime, self.escritos = base, mtime, []

    def escrever(self, rel: str, conteudo, mtime: float | None = None) -> Path:
        p = self.base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(conteudo, (dict, list)):
            p.write_text(json.dumps(conteudo, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        elif isinstance(conteudo, bytes):
            p.write_bytes(conteudo)
        else:
            p.write_text(conteudo, encoding="utf-8")
        t = self.mtime if mtime is None else mtime
        os.utime(p, (t, t))
        return p


def png(largura: int, altura: int, fundo: tuple, faixa: tuple, faixa_y: tuple[float, float]) -> bytes:
    """PNG RGB liso com uma faixa horizontal: a "capa" da demo (alguns KB, gerada aqui)."""
    y0, y1 = int(altura * faixa_y[0]), int(altura * faixa_y[1])
    linha_fundo = b"\x00" + bytes(fundo) * largura
    linha_faixa = b"\x00" + bytes(fundo) * (largura // 12) + bytes(faixa) * (largura - 2 * (largura // 12)) \
        + bytes(fundo) * (largura // 12)
    bruto = b"".join(linha_faixa if y0 <= y < y1 else linha_fundo for y in range(altura))

    def bloco(tipo: bytes, dados: bytes) -> bytes:
        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", zlib.crc32(tipo + dados) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + bloco(b"IHDR", struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0))
            + bloco(b"IDAT", zlib.compress(bruto, 9)) + bloco(b"IEND", b""))


def pdf(titulo: str, linhas: list[str]) -> bytes:
    """PDF de uma página, só texto (Helvetica), escrito à mão: o "material da palavra-chave" da demo."""
    def esc(t: str) -> str:
        return t.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    texto = "BT /F1 22 Tf 60 780 Td (" + esc(titulo) + ") Tj /F1 12 Tf"
    for ln in linhas:
        texto += " 0 -24 Td (" + esc(ln) + ") Tj"
    texto += " ET"
    stream = texto.encode("latin-1", "replace")
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
            b"/Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"]
    out, pos = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        pos.append(len(out))
        out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{p:010d} 00000 n \n".encode() for p in pos)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


def roteiro_md(slug: str, titulo: str, palavra: str, linhas: list[tuple[str, str, str]]) -> str:
    corpo = "\n".join(f"| {i} | {s} | {f} |" for i, s, f in linhas)
    return f"""---
slug: {slug}
titulo: {titulo}
cta_tipo: palavra-material
cta_palavra: {palavra}
---

# {titulo}

> Roteiro FICTÍCIO da demonstração do Korvu Studio.

> Antes da L01: 3 s parado olhando para a câmera, em silêncio (pausa da capa).

| ID | Seção | FALA |
|---|---|---|
{corpo}
"""


def roteiro_json(slug: str, versao: int, palavra: str, linhas, extras: list[str]) -> dict:
    return {"slug": slug, "versao": versao, "cta_tipo": "palavra-material", "cta_palavra": palavra,
            "extras": [{"id": e} for e in extras],
            "linhas": [{"id": i, "secao": s, "fala": f} for i, s, f in linhas]}


def srt(linhas) -> str:
    out = []
    for n, (_, _, fala) in enumerate(linhas, 1):
        ini, fim = (n - 1) * 4, n * 4 - 0.4
        def tc(s):
            return f"00:00:{int(s):02d},{int(round((s % 1) * 1000)):03d}"
        out.append(f"{n}\n{tc(ini)} --> {tc(fim)}\n{fala.replace(' / ', ' ')}\n")
    return "\n".join(out)


# ───────────────────────── conteúdo inventado ─────────────────────────

ROTEIROS = {
    "resumir-reunioes": ("Resumir reuniões com IA", "ATA", [
        ("L01", "gancho", "Você sai de uma reunião de uma hora / e não lembra o que ficou decidido?"),
        ("L02", "contexto", "Dá pra pedir pra IA transformar a transcrição / numa ata de cinco linhas."),
        ("L03", "virada", "O segredo é dizer o formato: / decisões, responsáveis e prazos."),
        ("L04", "climax", "Em dois minutos / você tem o resumo que ninguém tinha paciência de escrever."),
        ("L05", "cta", "Salva esse vídeo / e comenta ATA que eu te mando o modelo de pedido."),
    ]),
    "planilha-com-ia": ("Planilha com IA, sem fórmula", "TABELA", [
        ("L01", "gancho", "Você trava toda vez que precisa de uma fórmula na planilha?"),
        ("L02", "contexto", "Conta pra IA o que você quer calcular / em português normal."),
        ("L03", "virada", "Ela te devolve a fórmula / e explica cada pedaço."),
        ("L04", "climax", "Você cola, confere com dois números / e pronto."),
        ("L05", "cta", "Comenta TABELA / que eu te mando os dez pedidos que mais uso."),
    ]),
    "prompt-claro": ("O prompt claro em três partes", "PROMPT", [
        ("L01", "gancho", "A resposta da IA veio genérica? / O problema quase sempre é o pedido."),
        ("L02", "contexto", "Um pedido claro tem três partes: / quem você é, o que precisa e como quer receber."),
        ("L03", "virada", "Olha a diferença / com o mesmo assunto."),
        ("L04", "climax", "Mesma IA, / resposta muito melhor."),
        ("L05", "cta", "Comenta PROMPT / que eu te mando o roteiro das três partes."),
    ]),
    "ia-no-atendimento": ("IA no atendimento do pequeno negócio", "RESPOSTA", [
        ("L01", "gancho", "Responder a mesma pergunta vinte vezes por dia / cansa qualquer um."),
        ("L02", "contexto", "Uma loja pequena pode usar IA / pra rascunhar as respostas mais comuns."),
        ("L03", "virada", "Você revisa, ajusta o tom / e só depois envia."),
        ("L04", "climax", "A IA ajuda, / mas quem atende continua sendo você."),
        ("L05", "cta", "Comenta RESPOSTA / que eu te mando os modelos de mensagem."),
    ]),
}
PILARES = {"resumir-reunioes": "produtividade", "planilha-com-ia": "tutoriais-rapidos",
           "prompt-claro": "tutoriais-rapidos", "ia-no-atendimento": "pequenos-negocios"}
PDFS = {"resumir-reunioes": "modelo-de-ata.pdf", "planilha-com-ia": "dez-pedidos-de-planilha.pdf",
        "prompt-claro": "prompt-em-tres-partes.pdf", "ia-no-atendimento": "modelos-de-resposta.pdf"}


# ───────────────────────── geração ─────────────────────────

def gerar(hoje: dt.date) -> None:
    def dia(n: int) -> dt.date:
        return hoje + dt.timedelta(days=n)

    def em(n: int, h: int = 10, m: int = 0) -> dt.datetime:
        return dt.datetime.combine(dia(n), dt.time(h, m), FUSO)

    def iso(n: int, h: int = 10, m: int = 0) -> str:
        return em(n, h, m).isoformat()

    def ts(n: int, h: int = 10, m: int = 0) -> float:
        return em(n, h, m).timestamp()

    slug = {"resumir-reunioes": f"{dia(-16)}-resumir-reunioes", "planilha-com-ia": f"{dia(-6)}-planilha-com-ia",
            "prompt-claro": f"{dia(-2)}-prompt-claro", "ia-no-atendimento": f"{dia(7)}-ia-no-atendimento"}
    PUB, AG, ED, RT = (slug[k] for k in ("resumir-reunioes", "planilha-com-ia", "prompt-claro", "ia-no-atendimento"))

    # do zero
    for pasta in (DEMO, REG):
        if pasta.exists() or pasta.is_symlink():
            shutil.rmtree(pasta)
    r = Raiz(DEMO, ts(-30))
    DEMO.mkdir(parents=True)
    for nome, alvo in LINKS_RAIZ.items():
        (DEMO / nome).symlink_to(alvo)
    (DEMO / "painel").mkdir()
    for nome, alvo in LINKS_PAINEL.items():
        (DEMO / "painel" / nome).symlink_to(alvo)
    for p in ("videos", "05-render-pronto", "06-publicar", "07-publicados", "_controle"):
        (DEMO / p).mkdir()

    # o portoes.py lê a raiz no import: só depois de a raiz existir
    os.environ["CONTENT_AI_ROOT"] = str(DEMO)
    sys.path.insert(0, str(CODIGO / "scripts"))
    sys.dont_write_bytecode = True
    import portoes  # noqa: E402

    def registrar(alvo_rel: str, portao: str, resultado: str, quando: str, s0=0, s1=0, s2=0, nota=""):
        alvo = DEMO / alvo_rel
        rel = f"{alvo_rel}/qa/portoes/{portao}-v{len(portoes.veredictos(alvo, portao)) + 1}.md" \
            if portao != "publicacao" else f"{alvo_rel}/qa/portao-publicacao-v1.md"
        r.escrever(rel, f"# PORTÃO-{portao.upper()} — {resultado}\n\nRelatório fictício da demonstração.\n"
                        f"S0 {s0} · S1 {s1} · S2 {s2}\n" + (f"\n{nota}\n" if nota else ""))
        imp = portoes.impressao(portoes.arquivos_da_area(alvo, portao))
        portoes.registrar(alvo, portao, resultado, imp, rel, s0, s1, s2, nota=nota)
        # o `em` real é o relógio de quem roda; na demo, uma data fixa (a impressão não depende dele)
        livro = json.loads((alvo / "portoes.json").read_text(encoding="utf-8"))
        livro["veredictos"][-1]["em"] = quando
        (alvo / "portoes.json").write_text(json.dumps(livro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.utime(alvo / "portoes.json", (r.mtime, r.mtime))

    def video_base(chave: str, versao: int, estado: str, historico: list[tuple[str, str, str]], extras=()):
        s = slug[chave]
        titulo, palavra, linhas = ROTEIROS[chave]
        v = f"videos/{s}"
        r.escrever(f"{v}/roteiro.md", roteiro_md(s, titulo, palavra, linhas))
        r.escrever(f"{v}/roteiro.json", roteiro_json(s, versao, palavra, linhas, list(extras)))
        r.escrever(f"{v}/material/{PDFS[chave]}", pdf(titulo, [
            "Material fictício da demonstração do Korvu Studio.",
            f"Palavra-chave: {palavra}", "1. Escreva o que você precisa em uma frase.",
            "2. Diga o formato da resposta.", "3. Confira o resultado antes de usar."]))
        r.escrever(f"{v}/material/dossie.md", f"# Dossiê — {titulo}\n\nPesquisa fictícia da demonstração. "
                                               "Sem fatos de notícia: o vídeo é um tutorial.\n")
        r.escrever(f"{v}/material/fontes.json", {"fontes": [], "nota": "tutorial sem afirmação de notícia (demo)"})
        r.escrever(f"{v}/status.json", {"slug": s, "estado": estado, "atualizado": historico[-1][1],
                                        "historico": [{"estado": e, "em": q, "nota": n} for e, q, n in historico]})
        return v, linhas

    def gravado(v: str, n_dia: int, tamanhos: tuple[int, ...]) -> None:
        """A gravação entra pelo manifesto de originais arquivados (docs/contratos.md §0): o painel a conta como
        gravada sem nenhum .MOV no repositório."""
        r.escrever(f"{v}/brutos/principal/ARQUIVADO.json", {
            "nota": "Demonstração: as gravações não vêm no repositório; o manifesto as conta como arquivadas.",
            "arquivos": [{"nome": f"camera-0{i}.MOV", "bytes": b,
                          "sha256": hashlib.sha256(f"{v}-{i}".encode()).hexdigest(),
                          "mtime": iso(n_dia, 15, 10 + 20 * i), "ctime": iso(n_dia, 18, i)}
                         for i, b in enumerate(tamanhos, 1)]})

    # 1) publicado há duas semanas, com métricas
    v, linhas = video_base("resumir-reunioes", 2, "publicado", [
        ("roteiro", iso(-24), "roteiro v1"), ("gravacao", iso(-17), "gravado"), ("edicao", iso(-16), "EDL v1"),
        ("pronto", iso(-15, 18), "pacote QA PASS"), ("agendado", iso(-15, 19), "fila"),
        ("publicado", iso(-14, 19, 2), "IG + FB")])
    gravado(v, -17, (3_920_000_000,))
    r.escrever(f"{v}/capa/capa.png", png(270, 480, (17, 17, 17), (255, 77, 0), (0.62, 0.70)))
    r.escrever(f"{v}/edicao/legendas.srt", srt(linhas))
    for portao, quando in (("pauta", iso(-25)), ("roteiro", iso(-24, 15)), ("imagem", iso(-16, 11)),
                           ("corte", iso(-16, 17))):
        registrar(v, portao, "APROVADO", quando, s2=1 if portao == "corte" else 0,
                  nota="S2: legenda da L03 pode quebrar em duas linhas (backlog)" if portao == "corte" else "")
    # 2) agendado na fila
    v2, linhas2 = video_base("planilha-com-ia", 1, "agendado", [
        ("roteiro", iso(-12), "roteiro v1"), ("gravacao", iso(-6), "gravado"), ("edicao", iso(-5), "EDL v1"),
        ("pronto", iso(-3, 18), "pacote QA PASS"), ("agendado", iso(-2, 9), "fila")], extras=("E01",))
    gravado(v2, -6, (2_740_000_000, 1_310_000_000))
    r.escrever(f"{v2}/capa/capa.png", png(270, 480, (245, 241, 232), (255, 77, 0), (0.30, 0.36)))
    r.escrever(f"{v2}/edicao/legendas.srt", srt(linhas2))
    registrar(v2, "pauta", "APROVADO", iso(-13))
    registrar(v2, "roteiro", "BLOQUEADO", iso(-12, 14), s1=1, nota="S1: o CTA prometia um material que não existia")
    registrar(v2, "roteiro", "APROVADO", iso(-12, 17))
    registrar(v2, "imagem", "APROVADO", iso(-4, 11))
    registrar(v2, "corte", "APROVADO", iso(-4, 16))
    # 3) gravado, em edição; capa reprovada pelo portão da imagem
    v3, _ = video_base("prompt-claro", 3, "edicao", [
        ("roteiro", iso(-9), "roteiro v1"), ("roteiro", iso(-7), "roteiro v3 (dramaturgo)"),
        ("gravacao", iso(-2, 16), "gravado em 2 partes"), ("edicao", iso(-1, 11), "EDL v1 aguardando aprovação")],
        extras=("E01", "E02"))
    r.escrever(f"{v3}/capa/capa.png", png(270, 480, (30, 30, 34), (240, 240, 240), (0.10, 0.16)))
    r.escrever(f"{v3}/brutos/extras/E02.png", png(160, 90, (245, 241, 232), (17, 17, 17), (0.4, 0.6)))
    r.escrever(f"{v3}/animacoes/E01/brief.md", f"""# E01 — "Pedido vago × pedido claro" (L03 + L04)

- **Vídeo:** {ED}
- **Modo:** `split`
- **Linhas:** L03 + L04 · **duração 7,2 s**

---

Animação fictícia da demonstração: dois balões de conversa lado a lado, o vago e o claro.
""")
    gravado(v3, -2, (4_812_000_000, 2_154_000_000))
    registrar(v3, "pauta", "APROVADO", iso(-10))
    registrar(v3, "roteiro", "APROVADO", iso(-7, 15))
    registrar(v3, "imagem", "BLOQUEADO", iso(-1, 15), s1=1, nota="S1: título da capa em cima do rosto")
    # 4) roteiro aprovado, gravação na semana que vem
    v4, _ = video_base("ia-no-atendimento", 1, "roteiro", [("roteiro", iso(-1, 10), "roteiro v1")])
    registrar(v4, "pauta", "APROVADO", iso(-1, 9))
    registrar(v4, "roteiro", "APROVADO", iso(-1, 14))

    # pacotes prontos (05-render-pronto), com o selo do GAUNTLET tirado dos portões aprovados
    def pacote(chave: str, pasta: str, criado: str, duracao: float) -> dict:
        s = slug[chave]
        base = f"{pasta}/{s}"
        r.escrever(f"{base}/capa/capa.png", (DEMO / f"videos/{s}/capa/capa.png").read_bytes())
        r.escrever(f"{base}/legendas/legendas.srt", (DEMO / f"videos/{s}/edicao/legendas.srt").read_text())
        r.escrever(f"{base}/material/{PDFS[chave]}", (DEMO / f"videos/{s}/material/{PDFS[chave]}").read_bytes())
        arquivos = {"capa": "capa/capa.png", "legendas": "legendas/legendas.srt", "material": f"material/{PDFS[chave]}"}
        selo = portoes.selar(DEMO / "videos" / s, DEMO / base, arquivos)
        selo["selado_em"] = criado  # os `em` dos veredictos já são as datas fixas reescritas no registrar()
        pac = {"slug": s, "qa": "PASS", "duracao": duracao, "criado_em": criado, "cta_palavra": ROTEIROS[chave][1],
               "tema": ROTEIROS[chave][0], "pilar": PILARES[chave], "arquivos": arquivos, "gauntlet": selo}
        r.escrever(f"{base}/pacote.json", pac)
        return pac

    pac_pub = pacote("resumir-reunioes", "05-render-pronto", iso(-15, 18), 41.6)
    pac_ag = pacote("planilha-com-ia", "05-render-pronto", iso(-3, 18), 37.2)

    # fila: o agendado em 06-publicar/
    q = f"06-publicar/{AG}"
    for rel in ("capa/capa.png", "legendas/legendas.srt", f"material/{PDFS['planilha-com-ia']}", "pacote.json"):
        r.escrever(f"{q}/{rel}", (DEMO / f"05-render-pronto/{AG}/{rel}").read_bytes())
    r.escrever(f"{q}/legenda-instagram.txt", "TABELA: planilha com IA, sem decorar fórmula.\n\n"
                                            "Comenta TABELA que eu te mando os dez pedidos.\n\n#ia #planilha #produtividade\n")
    r.escrever(f"{q}/legenda-facebook.txt", "Planilha com IA, sem decorar fórmula. Comenta TABELA e eu te mando os "
                                           "dez pedidos que mais uso.\n")
    r.escrever(f"{q}/post.json", {
        "slug": AG, "publicar_em": iso(3, 19), "plataformas": ["instagram", "facebook"], "estado": "agendado",
        "confirmar": False,
        "instagram": {"legenda_arquivo": "legenda-instagram.txt", "capa": "capa/capa.png", "share_to_feed": True,
                      "trial": {"graduation_strategy": "SS_PERFORMANCE"}},
        "facebook": {"legenda_arquivo": "legenda-facebook.txt"},
        "material": {"palavra": "TABELA", "arquivo": f"material/{PDFS['planilha-com-ia']}",
                     "titulo": "dez pedidos de planilha"}})
    registrar(q, "publicacao", "APROVADO", iso(-2, 10))

    # publicado: 07-publicados/ com post.json, pacote.json, capa e as leituras de métricas
    p = f"07-publicados/{PUB}"
    r.escrever(f"{p}/pacote.json", pac_pub)
    r.escrever(f"{p}/capa/capa.png", (DEMO / f"videos/{PUB}/capa/capa.png").read_bytes())
    r.escrever(f"{p}/post.json", {
        "slug": PUB, "publicar_em": iso(-14, 19), "publicado_em": iso(-14, 19, 2),
        "plataformas": ["instagram", "facebook"], "estado": "publicado",
        "instagram": {"permalink": "https://www.instagram.com/reel/DEMO0001/", "capa": "capa/capa.png",
                      "trial": {"graduation_strategy": "SS_PERFORMANCE"}},
        "facebook": {"permalink": "https://www.facebook.com/reel/1000000001/", "tipo": "reel"},
        "material": {"palavra": "ATA"}})

    def leitura(n_dia: int, dias: float, views, alcance, curt, com, salv, comp, tm, pct, plays, tmfb, pal, dms):
        return {"lido_em": iso(n_dia, 9, 30), "dias_desde_publicacao": dias,
                "resumo": {"instagram": {"views": views, "alcance": alcance, "curtidas": curt, "comentarios": com,
                                         "salvamentos": salv, "compartilhamentos": comp, "tempo_medio_s": tm,
                                         "pct_medio_assistido": pct},
                           "facebook": {"plays": plays, "tempo_medio_s": tmfb},
                           "palavra": {"comentarios": pal, "directs": dms}}}
    r.escrever(f"{p}/metricas.json", {
        "slug": PUB, "publicado_em": iso(-14, 19, 2), "duracao_s": 41.6, "palavra": "ATA",
        "trial": {"graduation_strategy": "SS_PERFORMANCE"}, "tema": "Resumir reuniões com IA", "pilar": "produtividade",
        "permalink_instagram": "https://www.instagram.com/reel/DEMO0001/",
        "permalink_facebook": "https://www.facebook.com/reel/1000000001/",
        "leituras": [leitura(-13, 0.6, 1840, 1612, 96, 41, 133, 22, 14.8, 35.6, 420, 9.1, 33, 31),
                     leitura(-9, 4.6, 6210, 5380, 288, 117, 512, 74, 16.2, 38.9, 1310, 9.8, 98, 95)]})

    # tracker, calendário, perfil
    r.escrever("_controle/tracker.md", "# Tracker de vídeos (demonstração)\n\n"
               "| Slug | Tema | Pilar | Estrutura | Hook | CTA | Estado | Atualizado |\n"
               "|---|---|---|---|---|---|---|---|\n" + "".join(
                   f"| {slug[k]} | {ROTEIROS[k][0]} | {PILARES[k]} | narrativo | A | {ROTEIROS[k][1]} | {e} | {d} |\n"
                   for k, e, d in (("resumir-reunioes", "publicado", f"{dia(-14)} 19:02"),
                                   ("planilha-com-ia", "agendado", f"{dia(-2)} 09:00"),
                                   ("prompt-claro", "edicao", f"{dia(-1)} 11:00"),
                                   ("ia-no-atendimento", "roteiro", f"{dia(-1)} 10:00"))))
    r.escrever("_controle/calendario.md", f"""# Calendário (demonstração)

```yaml
fuso: {FUSO_NOME}
vagas_semanais:        # dia: hora (24h)
  terça: "19:00"
  quinta: "19:00"
  sábado: "11:00"
plataformas_padrao: [instagram, facebook]
```

## Agenda
| Data/hora | Slug | Plataformas | Estado |
|---|---|---|---|
| {dia(-14)} 19:00 | {PUB} | instagram, facebook | publicado |
| {dia(3)} 19:00 | {AG} | instagram, facebook | agendado |
""")
    seguidores = [1180, 1236, 1302, 1415, 1488]
    for i, n in enumerate((-28, -21, -14, -7, 0)):
        seg = seguidores[i]
        alcance = 900 + 640 * i
        r.escrever(f"_controle/perfil/{dia(n)}.json", {
            "lido_em": iso(n, 9, 30),
            "instagram": {
                "conta": {"followers_count": seg, "follows_count": 210, "media_count": 18 + i},
                "janela": {"dias": 28},
                "metricas_conta": {
                    "reach": {"valor": alcance}, "views": {"valor": alcance * 3}, "accounts_engaged": {"valor": 60 + 25 * i},
                    "total_interactions": {"valor": 140 + 90 * i}, "profile_views": {"valor": 80 + 30 * i},
                    "profile_links_taps": {"valor": 6 + 3 * i},
                    "reach_por_follow_type": {"valor": alcance, "quebras": [{"dimensao": ["follow_type"], "resultados": [
                        {"chave": ["NON_FOLLOWER"], "valor": int(alcance * (0.55 + 0.05 * i))},
                        {"chave": ["FOLLOWER"], "valor": alcance - int(alcance * (0.55 + 0.05 * i))}]}]}},
                "demografia": {
                    "follower_demographics": {
                        "country": [{"chave": ["BR"], "valor": int(seg * 0.62)}, {"chave": ["PT"], "valor": int(seg * 0.14)},
                                    {"chave": ["US"], "valor": int(seg * 0.08)}, {"chave": ["ES"], "valor": int(seg * 0.04)}],
                        "city": [{"chave": ["São Paulo, São Paulo"], "valor": int(seg * 0.18)},
                                 {"chave": ["Rio de Janeiro, Rio de Janeiro"], "valor": int(seg * 0.09)},
                                 {"chave": ["Lisboa, Lisboa"], "valor": int(seg * 0.06)}],
                        "age": [{"chave": ["18-24"], "valor": int(seg * 0.21)}, {"chave": ["25-34"], "valor": int(seg * 0.39)},
                                {"chave": ["35-44"], "valor": int(seg * 0.24)}, {"chave": ["45-54"], "valor": int(seg * 0.10)}],
                        "gender": [{"chave": ["F"], "valor": int(seg * 0.47)}, {"chave": ["M"], "valor": int(seg * 0.51)}]},
                    "reached_audience_demographics": {
                        "country": [{"chave": ["BR"], "valor": int(alcance * 0.58)}, {"chave": ["PT"], "valor": int(alcance * 0.12)},
                                    {"chave": ["US"], "valor": int(alcance * 0.09)}],
                        "gender": [{"chave": ["F"], "valor": int(alcance * 0.49)}, {"chave": ["M"], "valor": int(alcance * 0.50)}]}}},
            "facebook": {"pagina": {"followers_count": 310 + 12 * i}}})
    for n in range(-13, 1):
        k = n + 13
        r.escrever(f"_controle/perfil/diario/{dia(n)}.json", {
            "dia": str(dia(n)), "lido_em": iso(n + 1, 9, 30),
            "metricas": {"reach": 140 + (k * 37) % 220 + (900 if n == -13 else 0), "views": 380 + (k * 91) % 600,
                         "seguidores": 1415 + 5 * k, "profile_views": 12 + (k * 7) % 25}})

    # painel/biblioteca.yaml da demo: o do repositório, com os exemplos de capa trocados pelos pacotes da demo
    cfg = yaml.safe_load((CODIGO / "painel" / "biblioteca.yaml").read_text(encoding="utf-8"))
    exemplos = [[PUB], [AG]]
    for i, c in enumerate(cfg.get("capas") or []):
        c["exemplos"] = exemplos[i % len(exemplos)]
    r.escrever("painel/biblioteca.yaml", "# Biblioteca da DEMONSTRAÇÃO — gerada por exemplos/gerar_demo.py a partir de "
               "painel/biblioteca.yaml\n# (os exemplos de capa apontam para os pacotes fictícios).\n"
               + yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False, width=200))

    # o cache de hashes do portoes.py guarda caminhos absolutos desta máquina: fora da demo
    for lixo in (DEMO / "_controle" / ".cache-portoes.json", DEMO / "_controle" / ".cache-portoes.tmp"):
        lixo.unlink(missing_ok=True)

    gerar_registros(hoje, slug)
    print(f"✓ {DEMO.relative_to(CODIGO)} e {REG.relative_to(CODIGO)} recriados (data-base {hoje})")


# ───────────────────────── registros sintéticos do Claude Code ─────────────────────────

def gerar_registros(hoje: dt.date, slug: dict[str, str]) -> None:
    rr = Raiz(REG, dt.datetime.combine(hoje, dt.time(12), dt.timezone.utc).timestamp())

    def t(n: int, h: int, m: int = 0) -> str:
        return (dt.datetime.combine(hoje + dt.timedelta(days=n), dt.time(h, m), dt.timezone.utc)
                .isoformat().replace("+00:00", ".000Z"))

    def resp(mid: str, quando: str, modelo: str, e: int, c5: int, c1: int, cl: int, s: int) -> dict:
        return {"type": "assistant", "uuid": f"u-{mid}", "timestamp": quando,
                "message": {"id": mid, "model": modelo, "role": "assistant",
                            "content": [{"type": "text", "text": "(resposta fictícia da demonstração)"}],
                            "usage": {"input_tokens": e, "cache_creation_input_tokens": c5 + c1,
                                      "cache_read_input_tokens": cl, "output_tokens": s, "service_tier": "standard",
                                      "cache_creation": {"ephemeral_5m_input_tokens": c5,
                                                         "ephemeral_1h_input_tokens": c1}}}}

    def pedido(texto: str, quando: str) -> dict:
        return {"type": "user", "uuid": "u-pedido", "timestamp": quando,
                "message": {"role": "user", "content": texto}}

    def jsonl(rel: str, linhas: list, meta: dict | None = None) -> None:
        rr.escrever(rel, "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in linhas))
        if meta is not None:
            rr.escrever(rel[: -len(".jsonl")] + ".meta.json", meta)

    opus, sonnet = "claude-opus-5-5", "claude-sonnet-5-5"
    # sessão principal (o diretor): uma resposta por dia útil nas últimas três semanas
    principal = [pedido("Sessão de demonstração.", t(-20, 9))]
    for n in range(-20, 0):
        if (hoje + dt.timedelta(days=n)).weekday() < 5:
            k = n + 21
            principal.append(resp(f"demo-p{k:02d}", t(n, 10 + k % 6), opus, 1800 + 90 * k, 12000 + 400 * k,
                                  3000 * (k % 3), 160000 + 9000 * k, 1400 + 120 * k))
    jsonl("sessao-demo-1.jsonl", principal)
    sub = "sessao-demo-1/subagents"
    jsonl(f"{sub}/agent-demo01.jsonl", [
        pedido(f"Escreva o roteiro de videos/{slug['ia-no-atendimento']}/ (demonstração).", t(-2, 13)),
        resp("demo-r1", t(-2, 13, 5), opus, 4200, 38000, 0, 210000, 6400),
        resp("demo-r2", t(-2, 13, 40), opus, 900, 6000, 0, 240000, 3100)],
        meta={"agentType": "roteirista", "description": "roteiro v1 (demo)", "spawnDepth": 1, "finished": True})
    jsonl(f"{sub}/agent-demo02.jsonl", [
        pedido(f"Gere a EDL de videos/{slug['prompt-claro']}/ (demonstração).", t(-1, 14)),
        resp("demo-e1", t(-1, 14, 10), sonnet, 8800, 52000, 12000, 380000, 9200)],
        meta={"agentType": "editor-de-video", "description": "EDL v1 (demo)", "spawnDepth": 1, "finished": True})
    jsonl("sessao-demo-2.jsonl", [
        pedido(f"Agende 06-publicar/{slug['planilha-com-ia']}/ (demonstração).", t(-3, 15)),
        resp("demo-q1", t(-3, 15, 3), sonnet, 2100, 16000, 0, 90000, 2500),
        resp("demo-q2", t(-3, 15, 20), opus, 1300, 9000, 0, 120000, 1900)])
    jsonl("sessao-demo-2/subagents/agent-demo03.jsonl", [
        pedido(f"Escreva as legendas do post de 06-publicar/{slug['planilha-com-ia']}/ (demonstração).", t(-3, 15, 5)),
        resp("demo-l1", t(-3, 15, 8), sonnet, 3300, 21000, 0, 70000, 2800)],
        meta={"agentType": "publicador", "description": "legendas do post (demo)", "spawnDepth": 1, "finished": True})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hoje", default=HOJE_PADRAO, type=dt.date.fromisoformat, metavar="AAAA-MM-DD",
                    help=f"data-base da demo (padrão {HOJE_PADRAO})")
    gerar(ap.parse_args().hoje)
    return 0


if __name__ == "__main__":
    sys.exit(main())
