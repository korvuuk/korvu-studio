"""Gera o Volume 1 · Estúdio da documentação: docs/estudio/site/index.html, site/diagramas/*.svg, site/fontes/ e
docs/estudio/README.md. Entrada: docs/estudio/dossie/dados.json (+ o texto do dossie.md, transcrito no template).
Visual: CSS-base copiado do gerador do painel (_base.css) e tokens de painel/design/.

    python3 docs/estudio/gerador/build.py

Só usa a biblioteca padrão. Caminhos relativos a este arquivo (nada absoluto)."""
import html, json, os, re, shutil, sys, urllib.parse

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import diagramas as DG

RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
DOC = os.path.join(RAIZ, "docs", "estudio")
SITE = os.path.join(DOC, "site")
FONTES_DS = os.path.join(RAIZ, "painel", "design", "fontes")
# Link do Volume 2: relativo no repositório. Para a cópia publicada fora (Artifact), quem publica passa
# VOLUME2_URL + SAIDA (pasta): o index.html vai para SAIDA com essa URL; o repositório não guarda URL nenhuma.
URL_PAINEL = "../../painel/site/index.html"
SAIDA_EXTRA = None
if os.environ.get("VOLUME2_URL") or os.environ.get("SAIDA"):
    assert os.environ.get("VOLUME2_URL") and os.environ.get("SAIDA"), "use VOLUME2_URL e SAIDA juntas"
    URL_PAINEL = os.environ["VOLUME2_URL"]
    SAIDA_EXTRA = os.path.abspath(os.environ["SAIDA"])
    assert not SAIDA_EXTRA.startswith(DOC + os.sep), "SAIDA fica fora de docs/estudio/ (a URL não entra no repositório)"
dados = json.load(open(os.path.join(DOC, "dossie", "dados.json"), encoding="utf-8"))
e = html.escape


def code(s):
    """`x` → <code>x</code> (texto escapado)."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", e(s, quote=False))


# ── contagens que a página afirma ──
TOT = dados["totais"]
assert len(dados["integracoes"]) == TOT["integracoes"] == 14
assert len(dados["jobs_locais"]) == TOT["jobs_locais"] == 5
assert dados["em_producao"]["jobs_carregados"] == TOT["jobs_locais"], "jobs_carregados ≠ jobs_locais"
assert len(dados["pipeline"]) == TOT["etapas_pipeline"] == 20
assert len(dados["edicao"]) == TOT["passos_edicao"] == 14
assert len(dados["agentes"]) == TOT["agentes_estudio"] == 22
assert len(dados["portoes"]) == 5
assert len(dados["testes"]) == 4

for p in ("diagramas", "fontes"):
    os.makedirs(os.path.join(SITE, p), exist_ok=True)
for f in ("Geist-Variable.woff2", "GeistMono-Variable.woff2", "OFL.txt"):
    shutil.copy2(os.path.join(FONTES_DS, f), os.path.join(SITE, "fontes", f))
def fonte_dados(nome):
    # Percent-encoding (não base64): o texto embutido não cria falsos positivos no grep de segredos.
    return urllib.parse.quote_from_bytes(open(os.path.join(FONTES_DS, nome), "rb").read(), safe="")


g_url, m_url = fonte_dados("Geist-Variable.woff2"), fonte_dados("GeistMono-Variable.woff2")
# Embutidas: a página abre sozinha (Artifact, GitHub Pages ou arquivo local) sem depender da pasta fontes/.
FONTES = (f'@font-face{{font-family:"Geist";src:url("data:font/woff2,{g_url}") format("woff2");font-weight:100 900;font-style:normal;font-display:swap}}\n'
          f'@font-face{{font-family:"Geist Mono";src:url("data:font/woff2,{m_url}") format("woff2");font-weight:100 900;font-style:normal;font-display:swap}}')
# Padrões proibidos montados por partes, para o próprio gerador não aparecer no grep de segredos.
PROIBIDOS = [r"/Us" + "ers/", "@gm" + "ail", r"\bs" + "k-", r"\bey" + "J", r"r2\.d" + "ev", "pass" + "word"]


# ── índice ──
SECOES = [("capa", "Início"), ("meta", "API da Meta", "6"), ("automacao", "Automação local", "6"),
          ("edicao", "Metodologia de edição", str(TOT["passos_edicao"])),
          ("integracoes", "Integrações", str(TOT["integracoes"])),
          ("pipeline", "Pipeline e portões", str(TOT["etapas_pipeline"])), ("tecnologia", "Tecnologia"), ("qualidade", "Qualidade"),
          ("instalar", "Instalar e reusar")]


def nav():
    out = ['<ul class="nav">']
    for s in SECOES:
        cont = f'<span class="cont">{s[2]}</span>' if len(s) > 2 else ""
        out.append(f'<li><a href="#{s[0]}">{e(s[1])}{cont}</a></li>')
    return "".join(out) + "</ul>"


# ── pilha ──
ST = {s["tecnologia"]: s["versao"] for s in dados["stack"]}
SELOS = [("Python", ST["Python"]), ("uv", ST["uv"]), ("requests", ST["requests"]), ("boto3", ST["boto3"]),
         ("ElevenLabs SDK", ST["elevenlabs SDK (Scribe v2)"]), ("mlx-whisper", ST["mlx-whisper (whisper-large-v3-turbo)"]),
         ("OpenCV", ST["Pillow / OpenCV headless"].split(" / ")[1]), ("rapidfuzz", ST["rapidfuzz"]),
         ("Remotion", ST["Remotion / React / TypeScript"].split(" / ")[0]), ("yt-dlp", ST["yt-dlp"]),
         ("ffmpeg", None), ("launchd", None), ("Graph API", "v23.0"), ("Claude Code", None)]


def selos():
    return "".join(f'<li class="selo">{e(n)}{f" <b>{e(v)}</b>" if v else ""}</li>' for n, v in SELOS)


def numeros():
    p = dados["em_producao"]
    itens = [(p["publicacoes"], "publicações"), (len(dados["agentes"]), "agentes"), (len(dados["portoes"]), "portões"),
             (p["jobs_carregados"], "jobs launchd"), (TOT["integracoes"], "integrações"),
             (len(dados["pipeline"]), "etapas")]
    return "".join(f"<div><b>{n}</b><span>{t}</span></div>" for n, t in itens)


# “Por quê” e camada legível: dossiê §3 (só o que está escrito).
POR_QUE = {
    "uv": "“rodar sempre com `uv run`”",
    "elevenlabs SDK (Scribe v2)": "Scribe é “mais literal” que o Whisper",
    "mlx-whisper (whisper-large-v3-turbo)": "sem API, Apple Silicon",
    "ffmpeg estático + ffprobe": "ffmpeg “com libass/zimg”",
    "Chrome headless": "“não há reportlab/weasyprint no projeto, e o Chrome já está na máquina”",
    "launchd (macOS)": "sem servidor: o script pergunta em vez de receber webhook",
    "DaVinci Resolve (FCPXML + MCP)": "reserva para ajuste fino à mão",
}
CAMADA = {"scripts": "Linguagem dos scripts", "executor": "Gerenciador / executor", "HTTP Meta": "HTTP para a Meta",
          "upload R2 (S3)": "Upload para o R2 (API S3)", "transcrição API": "Transcrição (API)",
          "transcrição local": "Transcrição (local, alternativa)", "imagem/rosto": "Imagem / rosto para o zoom",
          "sinais": "Áudio / sinais", "alinhamento": "Alinhamento de texto", "vídeo/áudio": "Vídeo e áudio",
          "gráficos": "Gráficos, legendas, animações", "download YouTube": "Download do YouTube",
          "PDF": "PDF do material", "agendamento": "Agendamento", "agentes": "Agentes",
          "ajuste fino": "Ajuste fino manual"}


def tec():
    out = []
    for s in dados["stack"]:
        v = s["versao"] or ("não fixada" if s["tecnologia"].startswith("ffmpeg") else "—")
        out.append(f'<tr><td class="cam">{e(CAMADA[s["camada"]])}</td><td>{code(s["tecnologia"])}</td>'
                   f'<td class="v">{e(v)}</td><td>{code(POR_QUE.get(s["tecnologia"], "—"))}</td></tr>')
    out.append('<tr><td class="cam">Config</td><td>PyYAML · python-dotenv</td><td class="v">ver <code>uv.lock</code></td><td>—</td></tr>')
    out.append('<tr><td class="cam">Banco do painel e do índice</td><td>Postgres local (Supabase)</td><td class="v">ver Volume 2</td><td>—</td></tr>')
    return "".join(out)


CONFERIDA = {
    "instagram_basic": "`publicar.py`, `responder_comentarios.py`, `metricas.py`",
    "instagram_content_publish": "`publicar.py`",
    "instagram_manage_comments": "`responder_comentarios.py`",
    "instagram_manage_messages": "`responder_comentarios.py`",
    "instagram_manage_insights": "`metricas.py`, `perfil.py`",
    "pages_show_list": "`publicar.py`",
    "pages_read_engagement": "`publicar.py`, `responder_comentarios.py`, `metricas.py`",
    "pages_manage_posts": "`publicar.py`",
    "read_insights": "`metricas.py`, `perfil.py`",
    "pages_manage_engagement": "só um aviso no log de `publicar.py` (`comentar_primeiro`)",
}


def permissoes():
    ps = dados["meta"]["permissoes"]
    assert len(ps) == 10 and set(CONFERIDA) == {p["nome"] for p in ps}
    out = [f'<tr><td><code>{e(p["nome"])}</code></td><td>{code(p["uso"])}</td><td>{code(CONFERIDA[p["nome"]])}</td></tr>' for p in ps]
    out.append('<tr><td><code>pages_manage_metadata</code>, <code>business_management</code></td><td>“se a tela pedir”</td>'
               '<td><code>CONFIGURAR-APP-META.md</code> §3</td></tr>')
    return "".join(out)


ERROS = [
    ("`/comments` deixou de devolver comentários novos de quem não tem papel no app (~03/11)", "lê também `/ordered_comments`"),
    ("Robô do Facebook leva 403 da Cloudflare no R2", "o Facebook sobe do disco (rupload, graph-video, photos)"),
    ("Upload de 171 MB num pedido só → 413", "upload retomável em pedaços"),
    ("`/{ig-user-id}/messages` → “(#3) Application does not have the capability”", "o direct sai por `/{page-id}/messages`"),
    ("`media_publish` e `/feed` não são idempotentes", "confere o estado antes de repetir; uma tentativa só no `/feed`"),
    ("Códigos transitórios `1, 2, 4, 17, 32, 341, 613, 80001, 80002`, HTTP 5xx/429", "até 5 tentativas, espera exponencial (máx. 60 s)"),
    ("9004", "“a Meta não conseguiu baixar a mídia do URL (o R2 está público?)”"),
    ("2207026", "formato de vídeo não suportado (H.264/AAC, 9:16, 3 s–15 min)"),
    ("36003 / 2207009", "proporção fora de 4:5 a 1,91:1: “o 3:4 do modelo pode não passar”"),
    ("190", "“token inválido ou expirado: gere um novo e rode `verificar-tokens`”"),
    ("Legenda > 2.200 caracteres ou > 5 hashtags", "pacote inválido"),
    ("Vídeo fora de 3–900 s", "pacote inválido; > 300 MB só aviso"),
    ("1 direct por comentário, até 7 dias; quem não segue recebe em “Solicitações”", "o material vai como link já na 1.ª mensagem"),
    ("App em “Acesso Padrão” pode só falar com quem tem papel no app", "se falhar, pedir App Review de `instagram_manage_messages` / `instagram_manage_comments`"),
]


def erros():
    return "".join(f"<tr><td>{code(a)}</td><td>{code(b)}</td></tr>" for a, b in ERROS)


def quebra_barra(x):
    return e(x).replace("/", "/<wbr>")


def lista(xs):
    return "<br>".join(f"<code>{quebra_barra(x)}</code>" if ("/" in x or "." in x) else e(x) for x in xs)


def jobs():
    return "".join(
        f'<tr><td><code class="lab">{e(j["nome"])}</code><small><code>{quebra_barra(j["script"])}</code></small></td>'
        f'<td>{e(j["intervalo"])}</td>'
        f'<td>{lista(j["le"])}</td><td>{lista(j["escreve"])}</td><td><code>{quebra_barra(j["log"])}</code></td></tr>'
        for j in dados["jobs_locais"])


def integracoes():
    out = []
    for it in dados["integracoes"]:
        el = it["nome"].startswith("ElevenLabs")
        chips = []
        if el:
            chips.append('<span class="tabchip el">ElevenLabs · ELEVENLABS_API_KEY</span>')
        cred = [c for c in it["credencial"] if c != "não confirmado"]
        cred_html = ('<div class="chips">' + "".join(f'<span class="tabchip">{e(c)}</span>' for c in cred) + "</div>") if cred else \
            ("não confirmado" if it["credencial"] else "nenhuma")
        if it.get("verificado") is False:
            chips.append('<span class="chip vencido">não verificada com chamada real</span>')
        scripts = "<br>".join(f"<code>{e(s)}</code>" for s in it["script"])
        if it.get("quem_chama"):
            scripts += "<br>chamada por " + ", ".join(f"<code>{e(q)}</code>" for q in it["quem_chama"])
        custo = it["custo_limite"] or "—"
        extra = ""
        if it.get("motores"):
            mot = "".join(f'<li><code>{e(m["motor"])}</code>{" (padrão)" if m.get("padrao") else ""}: {code(m["modelo"])} · '
                          f'<code>{e(m["chave"])}</code> · {e(m["papel"])}</li>' for m in it["motores"])
            extra += f'<div><dt>Motores (<code>--motor</code>)</dt><dd><ul class="motores">{mot}</ul></dd></div>'
        if it.get("guarda_em"):
            extra += '<div><dt>Onde guarda</dt><dd>' + "<br>".join(code(g) for g in it["guarda_em"]) + "</dd></div>"
        if it.get("status"):
            extra += f'<div><dt>Estado</dt><dd>{code(it["status"])}</dd></div>'
        cls = " api-larga" if it.get("motores") else ""
        out.append(f'<article class="card api{cls}"><h3>{e(it["nome"])}</h3>{"<div class=tipo>" + "".join(chips) + "</div>" if chips else ""}<dl>'
                   f'<div><dt>Para quê</dt><dd>{code(it["para_que"])}</dd></div>'
                   f'{extra}'
                   f'<div><dt>Como</dt><dd>{code(it["como"])}</dd></div>'
                   f'<div><dt>Credencial</dt><dd>{cred_html}</dd></div>'
                   f'<div><dt>Script / quem</dt><dd>{scripts}</dd></div>'
                   f'<div><dt>Quando roda</dt><dd>{code(it["quando_roda"])}</dd></div>'
                   f'<div><dt>Custo / limite</dt><dd class="ink2">{code(custo)}</dd></div></dl></article>')
    return "".join(out)


def nao_integrado():
    return "".join(f'<li>{e(re.sub(r" *\(.*\)$", "", n))}: ainda não integrada</li>' for n in dados["nao_integrado"])


def portoes():
    return "".join(
        f'<article class="card area"><div class="topo"><h4>PORTÃO-{e(p["nome"])}</h4><span class="chip vencido">{e(p["agente"])}</span></div>'
        f'<p><b style="color:var(--ink)">Fiscaliza:</b> {e(", ".join(p["fiscaliza"]))}</p>'
        f'<p><b style="color:var(--ink)">Cobre:</b> {", ".join(f"<code>{e(c)}</code>" for c in p["cobre"])}</p></article>'
        for p in dados["portoes"])


def agentes():
    return "".join(f'<li class="{"portao" if "PORTÃO" in a["faz"] else ""}"><b>{e(a["nome"])}</b><span>{e(a["faz"])}</span></li>'
                   for a in dados["agentes"])


def testes():
    out = []
    for t in dados["testes"]:
        a, b = t["resultado"].split("/")
        ok = a == b
        out.append(f'<tr><td>{e(t["nome"])}</td><td><code>{e(t["comando"])}</code></td>'
                   f'<td class="res {"ok" if ok else "mal"}">{e(t["resultado"])}</td><td>{e(t.get("nota", "—"))}</td></tr>')
    return "".join(out)


def producao():
    p = dados["em_producao"]
    itens = [(p["publicacoes"], "publicações"), (p["reels"], "Reels"), (p["carrosseis"], "carrossel"),
             (p["com_trial"], "com Trial no IG"), (p["fb_reel"], "Reel no FB"), (p["fb_video_pagina"], "vídeo da Página"),
             (p["fb_fotos"], "post de fotos no FB")]
    return "".join(f"<div><b>{n}</b><span>{t}</span></div>" for n, t in itens)


REUSO = [
    ("Pastas `06-publicar/`, `07-publicados/`, `_controle/` e o contrato do `post.json` / `pacote.json`", "`docs/contratos.md` §9–10; constantes no topo de `publicar.py`"),
    ("Selo GAUNTLET obrigatório para publicar", "`portoes.conferir_pacote` em `validar_pacote` (ou a lista `_controle/gauntlet-legado.json`)"),
    ("Vagas, fuso e Trial", "bloco YAML de `_controle/calendario.md`"),
    ("Textos do direct e da resposta pública, nome da conta", "`automacao-meta/respostas.yaml`"),
    ("Labels `uk.korvu.*` e caminhos dos logs", "`scripts/launchd/*.plist`, `instalar.sh`"),
    ("Câmera V-Log, 25 fps, LUT da marca", "`FPS_PROJETO`, `CAMERA_PERFIL`, `00-marca/cor/luts/`"),
    ("Método de 2 vozes (ChatGPT monitor)", "funciona com 1 voz sem mudança"),
    ("Transcrição em português", "`language_code=\"por\"` em `transcribe.py`"),
]


def regras_corte():
    p = next(x for x in dados["edicao"] if x["passo"] == 5)["parametros"]
    a = next(x for x in dados["edicao"] if x["passo"] == 4)["parametros"]
    n = lambda v: f"{v:.2f}".replace(".", ",")
    pa = p["PAUSA_ALVO_s"]
    linhas = [
        ("PRE", f"{n(p['PRE_s'])} s", "`in` = 1.ª palavra − PRE"),
        ("POS", f"{n(p['POS_s'])} s", "sobra mínima depois da última palavra"),
        ("PAUSA_ALVO", f"{n(pa['normal'])} / {n(pa['pausa'])} / {n(pa['pausa_longa'])} s",
         "`out` = última palavra + max(POS, pausa da linha): normal / pausa / pausa longa"),
        ("SNAP", f"±{n(p['SNAP_s'])} s", "a borda procura o ponto mais silencioso nessa janela"),
        ("GUARDA_ENERGIA", f"{n(p['GUARDA_ENERGIA_s'])} s", "o corte fica fora do ataque e da cauda: nunca entra na energia de uma palavra"),
        ("PAUSA_INTERNA → PAUSA_RESTA", f"> {n(p['PAUSA_INTERNA_s'])} s fica {n(p['PAUSA_RESTA_s'])} s", "pausa dentro da linha é encurtada"),
        ("GAP_MULETA", f"{n(p['GAP_MULETA_s'])} s", "silêncio que sobra no lugar de uma muleta cortada (“é”, “hum”, “tipo”, “né”…)"),
        ("MARGEM_IA", f"{n(p['MARGEM_IA_s'])} s", "distância mínima entre o corte e a voz da IA (zona proibida)"),
        ("MIN_PECA", f"{n(p['MIN_PECA_s'])} s", "peça menor que isso é fundida"),
        ("ZOOM_ESCALA / ZOOM_MAX", f"{p['ZOOM_ESCALA']:.2f} / {p['ZOOM_MAX']:.2f}".replace(".", ","), "enquadramento fechado / máximo sem ampliar o 1440"),
        ("ZOOM_SEGURA_MIN", f"{n(p['ZOOM_SEGURA_MIN_s'])} s", "um enquadramento segura pelo menos isso antes de trocar"),
        ("SIM_OK · SIM_PARAFRASE", f"{n(a['SIM_OK'])} · {n(a['SIM_PARAFRASE'])}", "take [OK] a partir de 0,80; [PARAFRASE] a partir de 0,45; abaixo, [FALTANDO]"),
    ]
    return "".join(f'<tr><td><code>{e(k)}</code></td><td class="v">{e(v)}</td><td>{code(d)}</td></tr>' for k, v, d in linhas)


def reuso():
    return "".join(f"<tr><td>{code(a)}</td><td>{code(b)}</td></tr>" for a, b in REUSO)


# ── diagramas ──
ds = DG.todos(dados)
if DG.AVISOS:
    print("AVISOS de largura:")
    for a in DG.AVISOS:
        print("  ", a)
DG.CSS_SOLTO = FONTES + DG.REGRAS.replace(".dg text", "text") % DG.MARFIM
for n, d in ds.items():
    open(os.path.join(SITE, "diagramas", f"{n}.svg"), "w", encoding="utf-8").write(d.svg(solto=True))

t = open(os.path.join(AQUI, "template.html"), encoding="utf-8").read()
rep = {"FONTES": FONTES, "CSS_BASE": open(os.path.join(AQUI, "_base.css"), encoding="utf-8").read(),
       "CSS_DG": DG.CSS_PAGINA, "NAV": nav(), "SELOS": selos(), "NUMEROS": numeros(), "TEC": tec(),
       "PERMISSOES": permissoes(), "ERROS": erros(), "JOBS": jobs(), "INTEGRACOES": integracoes(), "NAO_INTEGRADO": nao_integrado(),
       "PORTOES": portoes(), "AGENTES": agentes(), "TESTES": testes(), "PRODUCAO": producao(),
       "PERIODO": e(dados["em_producao"]["periodo"]), "REUSO": reuso(), "REGRAS_CORTE": regras_corte(), "URL_PAINEL": URL_PAINEL}
for n, d in ds.items():
    rep[f"SVG_{n}"] = d.svg()
for k, v in rep.items():
    t = t.replace("{{" + k + "}}", v)
falta = re.findall(r"\{\{[A-Za-z_-]+\}\}", t)
assert not falta, falta

# Conferências: versões da página saem do dados.json; nada de caminho do Mac, e-mail ou chave.
for proibido in PROIBIDOS:
    assert not re.search(proibido, t, re.I), proibido
    for n, d in ds.items():
        assert not re.search(proibido, d.svg(solto=True), re.I), (n, proibido)
if SAIDA_EXTRA:
    os.makedirs(SAIDA_EXTRA, exist_ok=True)
    open(os.path.join(SAIDA_EXTRA, "index.html"), "w", encoding="utf-8").write(t)
    print("cópia para publicar:", os.path.join(SAIDA_EXTRA, "index.html"), "(o site/ do repositório não muda)")
    sys.exit(0)
open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(t)
print("index.html ok,", len(t) // 1024, "KB;", len(ds), "diagramas")

readme = open(os.path.join(AQUI, "README.md.modelo"), encoding="utf-8").read()
for proibido in PROIBIDOS:
    assert not re.search(proibido, readme, re.I), proibido
open(os.path.join(DOC, "README.md"), "w", encoding="utf-8").write(readme)
print("README ok")
