import base64, json, os, re, shutil, sys, html
sys.path.insert(0, os.path.dirname(__file__))
import diagramas as DG

import os
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "painel"))
DOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE = f"{DOC}/site"
AQUI = os.path.dirname(__file__)
dados = json.load(open(f"{DOC}/dossie/dados.json"))
e = html.escape

os.makedirs(f"{SITE}/capturas", exist_ok=True)
os.makedirs(f"{SITE}/fontes", exist_ok=True)
os.makedirs(f"{SITE}/diagramas", exist_ok=True)
for f in os.listdir(f"{DOC}/dossie/capturas"):
    if f.endswith(".png"):
        shutil.copy2(f"{DOC}/dossie/capturas/{f}", f"{SITE}/capturas/{f}")
for f in ["Geist-Variable.woff2", "GeistMono-Variable.woff2", "OFL.txt"]:
    shutil.copy2(f"{RAIZ}/design/fontes/{f}", f"{SITE}/fontes/{f}")
g64 = base64.b64encode(open(f"{RAIZ}/design/fontes/Geist-Variable.woff2", "rb").read()).decode()
m64 = base64.b64encode(open(f"{RAIZ}/design/fontes/GeistMono-Variable.woff2", "rb").read()).decode()

def code(s):
    """`x` → <code>x</code> (texto já escapado)."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", e(s, quote=False))

# ── logo ──
logo = open(f"{RAIZ}/design/marca/korvu-painel-ink.svg").read()
logo = logo.replace('fill="#111111"', 'class="la"').replace('fill="#6b6458"', 'class="lb"')
logo = logo.replace('<svg ', '<svg class="logo" ', 1).replace('role="img" aria-label="korvu. painel"', 'aria-hidden="true"')
logo = re.sub(r"<\?xml[^>]*>", "", logo).strip()

# ── nav ──
secoes = [("capa", "Início"), ("arquitetura", "Arquitetura"), ("tecnologia", "Tecnologia"), ("banco", "Banco de dados"),
          ("backend", "Back-end e sincronização"), ("apis", "APIs", "7"), ("telas", "Tela por tela", "9"),
          ("design", "Design system"), ("qualidade", "Qualidade"), ("instalar", "Instalar e reusar")]
def nav():
    out = ['<ul class="nav">']
    for s in secoes:
        cont = f'<span class="cont">{s[2]}</span>' if len(s) > 2 else ""
        out.append(f'<li><a href="#{s[0]}">{e(s[1])}{cont}</a></li>')
    out.append("</ul>")
    return "".join(out)

# ── selos da pilha (dados.json → stack) ──
def selos():
    st = {s["tecnologia"]: s["versao"] for s in dados["stack"]}
    escolha = [("Next.js", st["Next.js (App Router)"]), ("React", st["React / React DOM"]),
               ("TypeScript", st["TypeScript"]), ("Tailwind CSS", st["Tailwind CSS"]),
               ("supabase-js", st["@supabase/supabase-js"]), ("Supabase local", st["Supabase local / Postgres"]),
               ("Python", st["Python"]), ("psycopg", st["psycopg[binary]"]), ("PyYAML", st["PyYAML"]),
               ("uv", None), ("launchd", None), ("Geist", None)]
    return "".join(f'<li class="selo">{e(n)}{f" <b>{e(v)}</b>" if v else ""}</li>' for n, v in escolha)

TEC = [
    ("Framework web", "Next.js (App Router)", "15.5.28", "—"),
    ("UI", "React / React DOM", "19.1.10", "—"),
    ("Linguagem (web)", "TypeScript (`strict`)", "5.9.3", "—"),
    ("Estilo", "Tailwind CSS (+ `@tailwindcss/postcss`)", "4.3.3", "—"),
    ("CSS do design system", "CSS próprio “korvu. painel” (tokens, componentes, acréscimos, movimento)", "—",
     "cópia sem mudar de `painel/design/`"),
    ("Cliente do banco", "`@supabase/supabase-js`", "2.58.0", "lê do lado do servidor com a chave de serviço"),
    ("Trava de servidor", "`server-only`", "0.0.1", "impede importar o acesso ao banco em componente de cliente"),
    ("Lint", "ESLint + `eslint-config-next`", "9.39.5 / 15.5.28", "—"),
    ("Banco", "Supabase local (CLI), Postgres", "Postgres 17",
     "banco próprio, isolado do outro projeto do Mac (portas 553xx)"),
    ("Sincronizador", "Python", "≥ 3.12", "—"),
    ("Driver Postgres", "psycopg (binary)", "≥ 3.2", "—"),
    ("YAML", "PyYAML", "≥ 6.0.3", "ler `equipe.yaml`, `cambio.yaml`, `biblioteca.yaml`"),
    ("Gerenciador Python", "uv", "—", "“rodar sempre com `uv run`”"),
    ("Agendador", "launchd (macOS)", "—", "sincronização a cada 15 min"),
    ("Docker", "Colima", "—", "o encaminhador dele define o endereço publicado; daí a rede só-no-Mac"),
    ("Prévias dos looks", "ffmpeg", "—", "aplica as LUTs num quadro de amostra"),
    ("Capturas de tela", "Chrome sem janela via CDP + Node", "Node ≥ 22", "olhar a tela de verdade a 1440 e 375 px"),
    ("Fontes", "Geist e Geist Mono (variáveis, OFL 1.1)", "—", "locais, nada do Google"),
]
# confere versões contra dados.json
vers = {s["versao"] for s in dados["stack"] if s["versao"]}
for _, _, v, _ in TEC:
    for p in v.split(" / "):
        p2 = p.replace("≥ ", "≥")
        if p not in ("—",) and p2 not in vers and p not in vers and p != "15.5.28":
            print("VERSÃO fora do dados.json:", p)
def tec():
    return "".join(f'<tr><td class="cam">{e(c)}</td><td>{code(t)}</td><td class="v">{e(v)}</td><td>{code(p)}</td></tr>'
                   for c, t, v, p in TEC)

def portas():
    p = dados["portas"]
    itens = [("app Next.js", p["app"]), ("API Supabase (PostgREST/Kong)", p["api_supabase"]), ("Postgres", p["postgres"]),
             ("shadow", str(p["shadow"])), ("Studio, desligado", p["studio_desligado"])]
    return "".join(f'<li class="selo">{e(n)} <b>{e(v)}</b></li>' for n, v in itens)

def migracoes():
    dias = {}
    for m in dados["migracoes"]:
        dias.setdefault(m["data"], []).append(m)
    assert sum(len(v) for v in dias.values()) == 18
    out = []
    for d, ms in dias.items():
        _, mes, dia = d.split("-")
        lis = []
        for m in ms:
            n = m["arquivo"]
            hh = n[8:10] + ":" + n[10:12]
            lis.append(f'<li><span class="res"><span class="hora">{hh}</span>{e(m["resumo"][0].upper() + m["resumo"][1:])}</span>'
                       f'<span class="arq">{e(n)}</span></li>')
        out.append(f'<li class="dia"><div class="dia-rot"><b>{dia}/{mes}</b><span>{len(ms)} migraç{"ão" if len(ms) == 1 else "ões"}</span></div>'
                   f'<ol class="migs">{"".join(lis)}</ol></li>')
    return "".join(out)

ORIGENS = [
    ("`.claude/agents/*.md` (frontmatter) + `painel/equipe.yaml`", "`departamentos`, `agentes` (skills e comandos achados no texto)"),
    ("`videos/*/portoes.json` e demais alvos, via `scripts/portoes.py` (só leitura)", "`portoes_estado`, `veredictos`"),
    ("`_controle/tracker.md`, `videos/<slug>/status.json`, `roteiro.json`, `brutos/principal/` (só listagem e `stat()`), `ARQUIVADO.json`", "`videos`"),
    ("`05-render-pronto/<slug>/pacote.json`", "`prontos`, `videos.pronto`"),
    ("`06-publicar/<slug>/` (pacote + post) + `portoes.conferir_pacote(...)`", "`fila`"),
    ("`07-publicados/<slug>/post.json` e `metricas.json`", "`publicacoes`, `metricas`"),
    ("`_controle/perfil/*.json` e `_controle/perfil/diario/*.json` (proposta)", "`perfil_snapshots`, `perfil_demografia`, `perfil_diario`"),
    ("`_controle/calendario.md` (1.º bloco yaml)", "`calendario_vagas`"),
    ("`_controle/nao-publicar.json` (proposta)", "`nao_publicar`"),
    ("`videos/*/material/**`, `videos/*/brutos/extras/**`, `00-marca/referencias`, `painel/referencias`", "`biblioteca_*`"),
    ("`00-marca/cor/luts/*`, `00-marca/cor/cor.md`, `painel/biblioteca.yaml`, `remotion/src/brand.ts`",
     "`looks`, `capa_estilos(+_exemplos)`, `legenda_estilos`, `fontes`, `sistema_ferramentas`, `modelos_descricao`"),
    ("`videos/*/animacoes/Exx/brief.md`", "`animacoes`"),
    ("`.claude/agents`, `.claude/skills`, `.claude/commands`", "`sistema_contagens`"),
    ("`painel/cambio.yaml`", "`cambio`"),
    ("`PRECOS` no próprio código", "`precos_modelo`"),
    ("registros do Claude Code `~/.claude/projects/<projeto>/**/*.jsonl` + `agent-<id>.meta.json`", "`execucoes`, `uso_execucao`"),
]
def origens():
    return "".join(f"<tr><td>{code(a)}</td><td>{code(b)}</td></tr>" for a, b in ORIGENS)

APIS = [
    ("Supabase / PostgREST", ["rede local", "HTTP"], "o app Next.js, só no servidor, com `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`",
     "as 32 tabelas e 10 views, só SELECT (127.0.0.1:55321)", "— (lê o banco)", "`web/src/lib/db.ts`"),
    ("Postgres direto (psycopg)", ["rede local"], "o sincronizador (`PAINEL_DB_URL`, padrão o banco local)",
     "— (escreve)", "banco do painel, 127.0.0.1:55322", "`sync/sincronizar.py`"),
    ("Meta Graph API v23.0", ["indireta", "internet"],
     "`scripts/metricas.py` (métricas de cada Reel aos 5 dias), `scripts/perfil.py` (insights da conta, quebras por país/cidade/idade), `scripts/publicar.py` (publica) — área Automação Meta, não o painel",
     "métricas de Reels, perfil e demografia, permalinks; versão por `META_GRAPH_VERSION` (padrão `v23.0`)",
     "`07-publicados/<slug>/metricas.json` e `post.json`, `_controle/perfil/*.json` → o painel lê e grava em `metricas`, `publicacoes`, `perfil_*`",
     "`scripts/publicar.py`, `scripts/perfil.py`, `scripts/metricas.py`"),
    ("Registros do Claude Code", ["arquivos locais"], "o sincronizador",
     "`message.usage`, `message.model`, `message.id`, `timestamp`; tipo do subagente no `.meta.json`",
     "`execucoes`, `uso_execucao`; o custo sai das views", "`sync/sincronizar.py`"),
    ("Preço de tabela da API da Anthropic", ["copiado no código"], "— (não é chamada)",
     "US$ por milhão de tokens: Opus 5.5 4/20, Sonnet 5.5 2/10, Fable 5.1 10/50, Opus 5 5/25; cache 5 min 1,25×, 1 h 2×",
     "`PRECOS` → `precos_modelo`", "`sync/sincronizar.py`"),
    ("`scripts/portoes.py`", ["Python interno"], "o sincronizador, importado em modo só leitura",
     "estado dos portões, veredictos, `conferir_pacote` da fila", "`portoes_estado`, `veredictos`, `fila.erros_gauntlet`",
     "`sync/sincronizar.py`"),
    ("Rotas do próprio app", ["HTTP", "só leitura"], "o navegador",
     "`GET /capa/[pasta]/[slug]` (PNG), `GET /look/[id]` (JPEG)", "—",
     "`app/capa/…/route.ts`, `app/look/[id]/route.ts`"),
]
assert len(APIS) == len(dados["apis"]) == 7
def apis():
    out = []
    for nome, tipos, quem, traz, guarda, fonte in APIS:
        chips = "".join(f'<span class="tabchip">{e(t)}</span>' for t in tipos)
        out.append(f'<article class="card api"><h3>{code(nome)}</h3><div class="tipo">{chips}</div><dl>'
                   f'<div><dt>Quem chama</dt><dd>{code(quem)}</dd></div>'
                   f'<div><dt>O que traz</dt><dd>{code(traz)}</dd></div>'
                   f'<div><dt>Onde guarda</dt><dd>{code(guarda)}</dd></div>'
                   f'<div><dt>Fonte</dt><dd class="ink2">{code(fonte)}</dd></div></dl></article>')
    return "".join(out)

# ── telas: blocos (dossiê §7) + posição dos marcadores sobre a foto de 1440 (x %, y %) ──
TELAS = {
 "inicio": dict(blocos=["4 números do perfil: seguidores, alcance 28 dias, alcance fora da bolha, melhor vídeo",
    "Próximas publicações", "Desempenho · 28 dias", "Público · top 10 países (quem segue × quem os vídeos alcançam)",
    "Tokens e custos · 30 dias (rosca por modelo + custo estimado)", "Equipe (filtro por departamento, 5 cartões com foto)"],
    pos=[(15.1, 8.4), (49.5, 20.9), (15.1, 39.6), (15.1, 51.6), (57.6, 51.6), (43.0, 71.9)],
    vazio="Vazio: “Nada agendado” na fila (aparece na foto)."),
 "equipe": dict(blocos=["Busca de agente", "Filtros: Todos · Portões · Opus 5.5 · Sonnet 5.5 · Ainda não rodou",
    "4 números: agentes, departamentos, portões, tokens 30 dias", "Direção (o Atlas)",
    "Um cartão por departamento, gerente primeiro: modelo que rodou, consumo, tarefas"],
    pos=[(38.5, 5.8), (54.5, 8.1), (15.1, 11.6), (15.1, 21.4), (15.1, 32.2)],
    vazio="Vazio: “Equipe ainda não sincronizada”; sem consumo, o número mostra “—”. Sem foto, o cartão mostra as iniciais."),
 "equipe-portao-imagem": dict(blocos=["Cabeçalho com foto, departamento e cargo",
    "A função: papel, o que faz, modelo, skills, comandos, ferramentas, quem fiscaliza, arquivo",
    "O que passa por aqui: o estado do portão em cada alvo", "Veredictos recentes (os 12 mais novos)"],
    pos=[(15.1, 4.0), (15.1, 9.0), (15.1, 26.3), (15.1, 74.1)],
    vazio="Vazio: “Nenhum alvo com este portão ainda”, “Nenhum veredicto ainda”; id inexistente = 404; erro de banco nunca vira 404."),
 "equipe-contratar": dict(blocos=["Formulário: nome, cargo, departamento, o que faz, o que entrega, quando é chamado, modelo",
    "Pedido de contratação, montado ao vivo", "Botão “Copiar pedido”: o pedido é colado numa conversa com o Claude Code; o painel não cria arquivo"],
    pos=[(15.1, 27.7), (57.6, 27.7), (57.6, 62.8)], vazio=""),
 "producao": dict(blocos=["Busca", "Filtro de formato (Todos · Reels · Stories · Carrossel) e a fonte lida",
    "5 fases com os elos: você grava, pós e QA, você agenda, publica no horário", "Tabela da fase escolhida",
    "Precisam de atenção", "Portões (resumo por área)"],
    pos=[(38.5, 4.25), (43.0, 5.95), (15.1, 7.6), (15.1, 16.4), (15.1, 79.0), (56.6, 79.0)],
    vazio="Fase: Roteiros = sem gravação; Gravados = gravado sem pronto; Prontos = QA PASS; Agendados = fila; Publicados = publicações. Vazio: “Nada em produção”, “Nada pede atenção agora”, “Nenhum portão no banco”."),
 "calendario": dict(blocos=["Navegação: Hoje, ‹ ›, Mês | Semana", "Legenda dos canais e estados",
    "Eventos publicados e agendados com capa e canais, e as vagas livres", "Fila (com a linha “Portões:”)",
    "Melhores horários"],
    pos=[(15.1, 6.75), (51.5, 6.75), (15.1, 14.0), (15.1, 68.5), (56.8, 68.5)],
    vazio="Hora do fuso de publicação. Vazio: “Nada programado neste mês”, “Fila vazia”, “Sem print de horários”. Sem vagas, o calendário continua."),
 "desempenho": dict(blocos=["Período", "4 números com delta: seguidores, visualizações, contas alcançadas, visitas ao perfil",
    "Crescimento: curva por dia (hoje vazia: a Meta só manda o total de 28 dias)",
    "Fora da bolha: rosca não seguidores × seguidores", "De onde vem o público: quem segue × quem os vídeos alcançam",
    "Conteúdo que funciona: ranking dos Reels (views, alcance, % assistido, engajamento)"],
    pos=[(71.4, 4.9), (15.1, 6.6), (15.1, 13.7), (70.6, 13.7), (15.1, 32.8), (15.1, 51.0)],
    vazio="Leitura marcada como suspeita nunca entra em gráfico, ranking nem conta. Vazio: “Ainda não há dia a dia”."),
 "biblioteca": dict(blocos=["Abas: Tudo · Looks de cor · Capas · Legendas · Fontes · Animações · Sistema",
    "Looks de cor (5 cartões com a prévia)", "Capas", "Legendas", "Fontes", "Animações (roteirizada × renderizada)",
    "Armazenamento (GB no Mac)", "Sistema: modelos de IA dos 30 dias, ferramentas, contagem de agentes, habilidades e comandos"],
    pos=[(63.0, 5.1), (15.1, 7.45), (15.1, 29.7), (61.6, 29.7), (15.1, 44.2), (61.6, 44.2), (15.1, 65.2), (57.2, 65.2)],
    vazio=""),
 "tokens": dict(blocos=["Período", "4 números: tokens, custo estimado, agentes, custo médio por agente",
    "Consumo por dia (Tokens | Custo)", "Por modelo", "Por departamento", "Custo por vídeo",
    "Projeção mensal (média dos 30 dias × 30)", "Quem mais consome (Gerentes | Ranking geral)"],
    pos=[(45.6, 4.95), (15.1, 6.65), (15.1, 14.05), (70.8, 14.05), (15.1, 36.1), (57.0, 36.1), (57.0, 57.8), (15.1, 66.85)],
    vazio="Custo = equivalente na API pelo preço de tabela, não a fatura da assinatura."),
}
TELA_TELAS = {"/": "inicio", "/equipe": "equipe", "/equipe/[id]": "equipe-portao-imagem", "/equipe/contratar": "equipe-contratar",
              "/producao": "producao", "/calendario": "calendario", "/desempenho": "desempenho", "/biblioteca": "biblioteca",
              "/tokens": "tokens"}
from struct import unpack
def dims(p):
    with open(p, "rb") as f:
        f.read(16); w, h = unpack(">II", f.read(8))
    return w, h

def telas():
    idx, out = [], []
    assert len(dados["telas"]) == 9
    for t in dados["telas"]:
        chave = TELA_TELAS[t["rota"]]
        info = TELAS[chave]
        assert len(info["blocos"]) == len(t["blocos"]) == len(info["pos"]), (chave, len(info["blocos"]), len(t["blocos"]))
        pc, cel = t["captura_desktop"], t["captura_celular"]
        wp, hp = dims(f"{SITE}/{pc}"); wc, hc = dims(f"{SITE}/{cel}")
        aid = f"tela-{chave}"
        idx.append(f'<li><a href="#{aid}">{e(t["nome"])}</a></li>')
        marcas = "".join(f'<span class="marca" style="left:{x}%;top:{y}%" aria-hidden="true">{i + 1}</span>'
                         for i, (x, y) in enumerate(info["pos"]))
        blocos = "".join(f"<li>{e(b)}</li>" for b in info["blocos"])
        chips = "".join(f'<span class="tabchip">{e(d)}</span>' for d in t["dados"])
        rota_ex = " · foto: /equipe/portao-imagem" if t["rota"] == "/equipe/[id]" else ""
        out.append(f'''<article class="tela" id="{aid}">
  <div class="tela-cab"><div class="t"><h3>{e(t["nome"])}</h3><span class="rota">{e(t["rota"])}</span></div>
  <p class="pergunta">{e(t["pergunta"])}</p></div>
  <div class="fotos marfim-fotos">
    <figure class="foto-pc"><div class="sobre"><img src="{pc}" width="{wp}" height="{hp}" alt="Tela {e(t["nome"])} no computador, a 1440 px, com os blocos numerados de 1 a {len(info["blocos"])}.">{marcas}</div>
      <figcaption class="foto-rot">Computador · 1440 px{rota_ex}</figcaption></figure>
    <figure class="foto-cel"><div class="celular" id="cel-{chave}"><div class="tela-cel"><img src="{cel}" width="{wc}" height="{hc}" alt="Tela {e(t["nome"])} no celular, a 375 px, página inteira."></div></div>
      <figcaption class="foto-rot">Celular · 375 px</figcaption>
      <button class="ver-cel" type="button" aria-expanded="false" aria-controls="cel-{chave}">Ver a página inteira</button></figure>
  </div>
  <div class="blocos-dados">
    <div><p class="k-cap">Os blocos, na ordem dos números</p><ol class="blocos">{blocos}</ol></div>
    <div><p class="k-cap">De onde vem cada dado</p><div class="dados-tela">{chips}</div>
      {f'<p class="vazio-tela">{e(info["vazio"])}</p>' if info["vazio"] else ""}</div>
  </div>
</article>''')
    return "".join(idx), "\n".join(out)

CORES = [("bg", "#f5f2e8", "fundo marfim"), ("surface", "#fbf9f4", "cartões"), ("surface-sunken", "#efebe0", "trilhos, iniciais"),
         ("line", "#e4dfd2", "divisórias"), ("line-strong", "#928874", "bordas de controle"), ("ink", "#111111", "texto"),
         ("ink-2", "#6b6458", "texto auxiliar"), ("sidebar", "#111111", "barra lateral"), ("sidebar-raised", "#1d1c1a", "item ativo"),
         ("accent", "#ff4d00", "a cor da marca"), ("accent-hover", "#e64500", "hover do primário"), ("accent-soft", "#ffe8dc", "fundo de portão"),
         ("accent-ink", "#b33600", "laranja sobre claro, foco"), ("positive", "#1e7a45", "aprovado, alta"), ("danger", "#c2271b", "bloqueado, queda"),
         ("chart-3", "#a39b8b", "gráfico 3"), ("chart-4", "#d6ccb5", "gráfico 4"), ("chart-5", "#4f6475", "gráfico 5, Facebook")]
tok = open(f"{RAIZ}/design/tokens.css").read()
for n, h, _ in CORES:
    assert re.search(rf"--{n}:\s*{h};", tok), n
def cores():
    return "".join(f'<div class="cor"><i style="background:{h}"></i><div><b>--{n}</b><span>{h.upper()}</span><span>{e(u)}</span></div></div>'
                   for n, h, u in CORES)

COMPS = ("Acervo, Alternador, Anel, Avatar, Avisos, BarraApp, Botao, Busca, Calendario, Campo, Canais, Capa, Card, "
         "CardPessoa, CartaoAgente, CartaoPublicacao, Casca, Chip, Contador, Destaque, Dica, Dicas, Equipe, ErroBloco, "
         "Escolha, Esqueleto, EstadoPagina, Evento, FiltroLista, GraficoLinha, Graficos, Icone, Kpi, LinhaPortoes, ListaKv, "
         "Logo, NavCalendario, Nota, Numeros, Pagina, Pedido, Portao, Progresso, Revelar, Selecao, Tabela, Texto, Vazio").split(", ")
def componentes():
    return "".join(f'<span class="tabchip">{c}</span>' for c in COMPS)

GAU = [("design", "portao-interface", "designer-de-produto", "fidelidade ao design aprovado, telas olhadas a 1440 e 375 px",
        "ok", "aprovado", "em 04/11"),
       ("interface", "portao-interface", "engenheiro-frontend",
        "código × design, dados honestos, gráficos, acessibilidade, chave nenhuma no navegador, tipos/lint/build", "ok", "aprovado", "em 04/11"),
       ("dados", "portao-dados", "engenheiro-backend",
        "migrações versionadas, RLS e permissões, sincronizador que só lê, contagens, segredos, isolamento, testes",
        "vencido", "vencido", "último APROVADO em 25/10; depois mudou o painel/equipe.yaml (o docs/gauntlet.md diz que esse arquivo fica fora das áreas)")]
assert dados["gauntlet_painel_12_11"]["design"] == "aprovado" and dados["gauntlet_painel_12_11"]["dados"].startswith("vencido")
def gauntlet():
    return "".join(f'<article class="card area"><div class="topo"><h4>Área {a}</h4><span class="chip {c}">{s}</span></div>'
                   f'<p class="quem">{p} fiscaliza {f}</p><p>Confere: {e(cf)}.</p><p>{code(q)}</p></article>'
                   for a, p, f, cf, c, s, q in GAU)

# ── diagramas ──
ds = DG.todos(dados)
if DG.AVISOS:
    print("AVISOS de largura:"); [print("  ", a) for a in DG.AVISOS]
fonte_svg = (f'@font-face{{font-family:"Geist";src:url(data:font/woff2;base64,{g64}) format("woff2");font-weight:100 900}}'
             f'@font-face{{font-family:"Geist Mono";src:url(data:font/woff2;base64,{m64}) format("woff2");font-weight:100 900}}')
DG.CSS_SOLTO = DG.REGRAS.replace(".dg text", "text") % DG.MARFIM
for n, d in ds.items():
    open(f"{SITE}/diagramas/{n}.svg", "w").write(d.svg(solto=True))

idx_telas, html_telas = telas()
t = open(f"{AQUI}/template.html").read()
rep = {"FONT_GEIST": g64, "FONT_MONO": m64, "LOGO": logo, "NAV": nav(), "SELOS": selos(), "TEC": tec(),
       "PORTAS": portas(), "MIGRACOES": migracoes(), "ORIGENS": origens(), "APIS": apis(), "INDICE_TELAS": idx_telas,
       "TELAS": html_telas, "CORES": cores(), "COMPONENTES": componentes(), "GAUNTLET": gauntlet(),
       "CSS_DG": DG.CSS_PAGINA}
for n, d in ds.items():
    rep[f"SVG_{n}"] = d.svg()
for k, v in rep.items():
    t = t.replace("{{" + k + "}}", v)
falta = re.findall(r"\{\{[A-Za-z_]+\}\}", t)
assert not falta, falta
open(f"{SITE}/index.html", "w").write(t)
print("ok", len(t) // 1024, "KB;", len(COMPS), "componentes")

# README do GitHub: sai do modelo (aviso "revisar antes de publicar" retirado em 12/11: Autor liberou as capturas como estão)
readme = open(f"{AQUI}/README.md.modelo").read()
assert "REVISAR ANTES DE PUBLICAR" not in readme
open(f"{DOC}/README.md", "w").write(readme)
print("README ok")
