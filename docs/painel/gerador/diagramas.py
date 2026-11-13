"""Diagramas da documentação do korvu. painel — mesma marcação para o SVG inline (classes estilizadas pelo CSS da
página, com os tokens nos dois temas) e para o SVG solto (mesmas classes + <style> com os valores do tema Marfim)."""
import html, json, sys

AVISOS = []

def esc(s):
    return html.escape(s, quote=True)

def largura(txt, tam, mono=False):
    return len(txt) * tam * (0.6 if mono else 0.56)

class D:
    def __init__(s, nome, w, h, rotulo):
        s.nome, s.w, s.h, s.rotulo = nome, w, h, rotulo
        s.el = []
    def add(s, x):
        s.el.append(x)
    def box(s, x, y, w, h, cls="dg-box", rx=10):
        s.add(f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"/>')
    def t(s, x, y, txt, cls="dg-t", anchor=None, limite=None, tam=13, mono=False):
        a = f' text-anchor="{anchor}"' if anchor else ""
        if limite is not None and largura(txt, tam, mono) > limite:
            AVISOS.append(f"{s.nome}: '{txt}' ~{largura(txt, tam, mono):.0f}px > {limite}")
        s.add(f'<text class="{cls}" x="{x}" y="{y}"{a}>{esc(txt)}</text>')
    def linha(s, d, cls="dg-acc", seta=True):
        m = f' marker-end="url(#{s.nome}-{"a" if "acc" in cls else ("e" if "err" in cls else "n")})"' if seta else ""
        s.add(f'<path class="{cls}" d="{d}"{m}/>')
    def num(s, x, y, n):
        s.add(f'<circle class="dg-num" cx="{x}" cy="{y}" r="11"/>'
              f'<text class="dg-numt" x="{x}" y="{y + 4}" text-anchor="middle">{n}</text>')
    def svg(s, solto=False):
        defs = (f'<defs>'
                f'<marker id="{s.nome}-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="dg-aha" d="M0 0L10 5L0 10z"/></marker>'
                f'<marker id="{s.nome}-n" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="dg-ahn" d="M0 0L10 5L0 10z"/></marker>'
                f'<marker id="{s.nome}-e" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="dg-ahe" d="M0 0L10 5L0 10z"/></marker>'
                f'</defs>')
        corpo = "\n".join(s.el)
        if solto:
            return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s.w} {s.h}" width="{s.w}" height="{s.h}" '
                    f'role="img" aria-label="{esc(s.rotulo)}">\n<style>{CSS_SOLTO}</style>\n{defs}\n'
                    f'<rect class="dg-bg" x="0" y="0" width="{s.w}" height="{s.h}"/>\n{corpo}\n</svg>\n')
        return (f'<svg class="dg" viewBox="0 0 {s.w} {s.h}" role="img" aria-label="{esc(s.rotulo)}" '
                f'style="--dg-w:{s.w}px">{defs}\n{corpo}\n</svg>')

# Regras das classes. {v} = var(--x) na página; hex no arquivo solto (tema Marfim de tokens.css).
REGRAS = """
.dg-bg{fill:%(bg)s}
.dg text{font-family:Geist,Inter,system-ui,sans-serif;font-variant-numeric:tabular-nums}
.dg-box{fill:%(surface)s;stroke:%(line_strong)s;stroke-width:1}
.dg-soft{fill:%(sunken)s;stroke:%(line)s;stroke-width:1}
.dg-dec{fill:%(bg)s;stroke:%(ink)s;stroke-width:1.5}
.dg-ink{fill:%(ink)s;stroke:%(ink)s;stroke-width:1}
.dg-hl{fill:%(accent_soft)s;stroke:none}
.dg-zone{fill:none;stroke:%(line_strong)s;stroke-width:1;stroke-dasharray:5 5}
.dg-errb{fill:%(danger_soft)s;stroke:%(danger)s;stroke-width:1}
.dg-okb{fill:%(positive_soft)s;stroke:%(positive)s;stroke-width:1}
.dg-t{fill:%(ink)s;font-size:13px;font-weight:600}
.dg-s{fill:%(ink_2)s;font-size:11px;font-weight:500}
.dg-m{fill:%(ink_2)s;font-size:10.5px;font-weight:500;font-family:"Geist Mono",ui-monospace,monospace !important}
.dg-mi{fill:%(ink)s;font-size:12px;font-weight:600;font-family:"Geist Mono",ui-monospace,monospace !important}
.dg-fk{fill:%(accent_text)s;font-size:10.5px;font-weight:500;font-family:"Geist Mono",ui-monospace,monospace !important}
.dg-hlt{fill:%(accent_ink)s;font-size:10.5px;font-weight:600;font-family:"Geist Mono",ui-monospace,monospace !important}
.dg-cap{fill:%(ink_2)s;font-size:10.5px;font-weight:600;letter-spacing:.08em}
.dg-lbl{fill:%(ink_2)s;font-size:10.5px;font-weight:600}
.dg-inkt{fill:%(bg)s;font-size:13px;font-weight:600}
.dg-inks{fill:%(bg)s;font-size:10.5px;font-weight:500;font-family:"Geist Mono",ui-monospace,monospace !important}
.dg-errt{fill:%(danger)s;font-size:12px;font-weight:600}
.dg-errs{fill:%(danger)s;font-size:10.5px;font-weight:500}
.dg-okt{fill:%(positive)s;font-size:13px;font-weight:600}
.dg-oks{fill:%(positive)s;font-size:10.5px;font-weight:500}
.dg-acc{fill:none;stroke:%(accent)s;stroke-width:2;stroke-linejoin:round}
.dg-ln{fill:none;stroke:%(ink_2)s;stroke-width:1.25;stroke-linejoin:round}
.dg-dash{fill:none;stroke:%(ink_2)s;stroke-width:1.25;stroke-dasharray:5 4;stroke-linejoin:round}
.dg-err{fill:none;stroke:%(danger)s;stroke-width:1.25;stroke-dasharray:5 4}
.dg-aha{fill:%(accent)s}
.dg-ahn{fill:%(ink_2)s}
.dg-ahe{fill:%(danger)s}
.dg-num{fill:%(accent)s;stroke:%(surface)s;stroke-width:2}
.dg-numt{fill:%(on_accent)s;font-size:11px;font-weight:700}
"""
PAGINA = dict(bg="var(--bg)", surface="var(--surface)", sunken="var(--surface-sunken)", line="var(--line)",
              line_strong="var(--line-strong)", ink="var(--ink)", ink_2="var(--ink-2)", accent="var(--accent)",
              accent_soft="var(--accent-soft)", accent_ink="var(--accent-ink)", accent_text="var(--accent-text)",
              danger="var(--danger)", danger_soft="var(--danger-soft)", positive="var(--positive)",
              positive_soft="var(--positive-soft)", on_accent="var(--on-accent)")
MARFIM = dict(bg="#f5f2e8", surface="#fbf9f4", sunken="#efebe0", line="#e4dfd2", line_strong="#928874", ink="#111111",
              ink_2="#6b6458", accent="#ff4d00", accent_soft="#ffe8dc", accent_ink="#b33600", accent_text="#b33600",
              danger="#c2271b", danger_soft="#fbe3df", positive="#1e7a45", positive_soft="#e3f0e4", on_accent="#111111")
CSS_PAGINA = REGRAS % PAGINA
CSS_SOLTO = None  # preenchido pelo build (com a fonte embutida)

# ───────────────────────── 1. Arquitetura ─────────────────────────
def arquitetura():
    d = D("arq", 1200, 490, "Arquitetura do korvu. painel: os arquivos do projeto são lidos pelo sincronizar.py, que "
          "grava numa transação no Postgres 17 local; o Next.js lê pela API do Supabase com a chave service_role e "
          "entrega HTML ao navegador, tudo em 127.0.0.1. Os números 1 a 7 seguem o veredicto de um portão até a tela.")
    d.add('<rect class="dg-zone" x="8" y="76" width="1184" height="404" rx="14"/>')
    d.t(24, 98, "SÓ NO MAC · TUDO EM 127.0.0.1", "dg-cap")
    # Meta (fora do Mac)
    d.box(24, 10, 220, 44, "dg-soft")
    d.t(40, 29, "Meta Graph API", limite=190)
    d.t(40, 46, "internet · v23.0 (padrão)", "dg-s", limite=190, tam=11)
    d.t(258, 29, "scripts/metricas.py · perfil.py · publicar.py (área Automação Meta)", "dg-s")
    d.t(258, 46, "gravam .json em 07-publicados/ e _controle/perfil/ — o painel só lê", "dg-s")
    d.linha("M224 54 V106", "dg-dash")
    # A — arquivos
    d.box(24, 110, 220, 232)
    d.t(40, 134, "arquivos do projeto", limite=188)
    linhas = [".claude/agents/*.md", "videos/<slug>/portoes.json", "videos/<slug>/status.json", "05-render-pronto/",
              "06-publicar/ · 07-publicados/", "_controle/ · painel/*.yaml", "00-marca/cor/"]
    for i, l in enumerate(linhas):
        y = 162 + i * 24
        if i == 1:
            d.add(f'<rect class="dg-hl" x="32" y="{y - 14}" width="204" height="20" rx="4"/>')
            d.t(40, y, l, "dg-hlt", limite=188, tam=10.5, mono=True)
        else:
            d.t(40, y, l, "dg-m", limite=188, tam=10.5, mono=True)
    d.num(244, 158, 1)
    d.box(24, 382, 220, 64)
    d.t(40, 406, "registros do Claude Code", limite=188)
    d.t(40, 426, "~/.claude/projects/…/*.jsonl", "dg-m", limite=188, tam=10.5, mono=True)
    # B — launchd + sync + prévias
    d.box(320, 110, 180, 50)
    d.t(336, 131, "launchd", limite=150)
    d.t(336, 149, "uk.korvu.painel · 900 s", "dg-m", limite=150, tam=10.5, mono=True)
    d.num(500, 110, 2)
    d.linha("M410 160 V196")
    d.t(418, 183, "roda", "dg-lbl")
    d.box(320, 200, 180, 112)
    d.t(336, 224, "sincronizar.py", limite=150)
    d.t(336, 243, "Python 3.12 · psycopg", "dg-s", limite=150, tam=11)
    d.t(336, 266, "import portoes", "dg-m", limite=150, tam=10.5, mono=True)
    d.t(336, 284, "SO_LEITURA = True", "dg-m", limite=150, tam=10.5, mono=True)
    d.num(500, 200, 3)
    d.linha("M244 256 H316")
    d.t(280, 248, "lê", "dg-lbl", "middle")
    d.linha("M244 414 H282 V292 H316", "dg-dash")
    d.t(24, 464, "só números, ids, modelo, horário", "dg-lbl")
    d.box(320, 382, 180, 64, "dg-soft")
    d.t(336, 406, "previas_looks.py", limite=150)
    d.t(336, 426, "ffmpeg + LUTs → .jpg", "dg-s", limite=150, tam=11)
    d.t(320, 464, "o único passo que grava arquivo", "dg-lbl")
    d.linha("M500 414 H925 V344", "dg-dash")
    d.t(712, 406, "GET /look/[id]", "dg-lbl", "middle")
    # C — Postgres
    d.box(580, 180, 170, 160)
    d.t(596, 204, "Postgres 17", limite=140)
    d.t(596, 223, "127.0.0.1:55322", "dg-m", limite=140, tam=10.5, mono=True)
    d.t(596, 250, "32 tabelas · 10 views", "dg-s", limite=140, tam=11)
    d.t(596, 269, "RLS ligado em todas", "dg-s", limite=140, tam=11)
    d.t(596, 288, "0 políticas", "dg-s", limite=140, tam=11)
    d.t(596, 316, "portoes_estado", "dg-m", limite=140, tam=10.5, mono=True)
    d.t(596, 331, "veredictos", "dg-m", limite=140, tam=10.5, mono=True)
    d.num(750, 180, 4)
    d.linha("M500 262 H576")
    d.t(540, 254, "1 transação", "dg-lbl", "middle")
    # D — Next.js
    d.box(840, 180, 170, 160)
    d.t(856, 204, "Next.js 15", limite=140)
    d.t(856, 223, "Server Components", "dg-s", limite=140, tam=11)
    d.t(856, 242, "127.0.0.1:3456", "dg-m", limite=140, tam=10.5, mono=True)
    d.t(856, 268, "db.portoesEstado()", "dg-m", limite=140, tam=10.5, mono=True)
    d.t(856, 285, "db.veredictos()", "dg-m", limite=140, tam=10.5, mono=True)
    d.t(856, 310, "páginas de 1.000", "dg-s", limite=140, tam=11)
    d.t(856, 327, "contagem exata", "dg-s", limite=140, tam=11)
    d.num(1010, 180, 5)
    d.linha("M750 262 H836")
    d.t(795, 254, "PostgREST", "dg-lbl", "middle")
    d.t(795, 280, "só SELECT", "dg-lbl", "middle")
    # E — navegador
    d.box(1080, 190, 104, 144)
    d.t(1090, 214, "navegador", limite=92)
    d.t(1090, 240, "Produção", "dg-s", limite=92, tam=10.5)
    d.t(1090, 258, "ficha do agente", "dg-s", limite=92, tam=10.5)
    d.t(1090, 276, "sino de avisos", "dg-s", limite=92, tam=10.5)
    d.t(1090, 304, "rodapé: hora", "dg-s", limite=92, tam=10.5)
    d.t(1090, 320, "da passagem", "dg-s", limite=92, tam=10.5)
    d.num(1184, 190, 6)
    d.num(1184, 310, 7)
    d.linha("M1010 262 H1076")
    d.t(1043, 254, "HTML", "dg-lbl", "middle")
    return d

# ───────────────────────── 2. Banco (ER) ─────────────────────────
def banco(dados):
    tab = {t["nome"]: t for t in dados["tabelas"]}
    W, G, X0 = 210, 30, 20
    cols = [
        [("EQUIPE E GAUNTLET", ["departamentos", "agentes", "portoes_estado", "veredictos"]),
         ("PERFIL IG/FB", ["perfil_snapshots", "perfil_demografia", "perfil_diario"])],
        [("TOKENS E CUSTOS", ["precos_modelo", "execucoes", "uso_execucao", "cambio"]),
         ("OPERAÇÃO", ["sincronizacoes"])],
        [("VÍDEOS, FILA E PUBLICAÇÃO", ["videos", "prontos", "fila", "nao_publicar", "publicacoes", "metricas",
                                        "calendario_vagas"])],
        [("BIBLIOTECA · MATERIAL", ["biblioteca_materiais", "biblioteca_arquivos", "biblioteca_referencias",
                                    "biblioteca_mais_utilizados"])],
        [("BIBLIOTECA · ACERVO DE ESTILOS", ["looks", "capa_estilos", "capa_estilos_exemplos", "legenda_estilos",
                                             "fontes", "sistema_ferramentas", "modelos_descricao", "animacoes",
                                             "sistema_contagens"])],
    ]
    usadas = [n for c in cols for _, g in c for n in g]
    assert sorted(usadas) == sorted(tab), set(tab) ^ set(usadas)
    assert len(usadas) == 32
    MAXC = 31  # caracteres mono 10.5 por linha (≈ 6,3 px)

    def quebra(prefixo, itens):
        out, atual = [], prefixo
        for i, it in enumerate(itens):
            pedaco = it + ("," if i < len(itens) - 1 else "")
            cand = (atual + " " + pedaco) if atual.strip() else pedaco
            if len(cand) > MAXC and atual.strip() and atual != prefixo:
                out.append(atual)
                atual = "   " + pedaco
            else:
                atual = cand
        out.append(atual)
        return out

    caixas, corpo = {}, []
    alt_col = []
    for ci, col in enumerate(cols):
        x = X0 + ci * (W + G)
        y = 22
        for gi, (rot, nomes) in enumerate(col):
            if gi:
                y += 26
            corpo.append(("cap", x, y + 8, f"{rot} · {len(nomes)}"))
            y += 20
            for n in nomes:
                t = tab[n]
                pk = [c["nome"] for c in t["colunas"] if "PK" in c["chave"]]
                fks = [(c["nome"], c["chave"].split("FK ")[1]) for c in t["colunas"] if "FK" in c["chave"]]
                linhas = [("dg-m", l) for l in quebra("PK", pk)]
                for col_, alvo in fks:
                    um = f"FK {col_} → {alvo.split('.')[0]}"
                    if len(um) <= MAXC:
                        linhas.append(("dg-fk", um))
                    else:
                        linhas += [("dg-fk", f"FK {col_}"), ("dg-fk", f"   → {alvo.split('.')[0]}")]
                h = 30 + 15 * len(linhas) + 6
                caixas[n] = (x, y, W, h)
                corpo.append(("tab", x, y, W, h, n, linhas, len(t["colunas"])))
                y += h + 12
        alt_col.append(y)
    # views abaixo da coluna 2
    xv = X0 + 1 * (W + G)
    yv = alt_col[1] + 14
    views = [v["nome"] for v in dados["views"]]
    assert len(views) == 10
    hv = 70 + 16 * len(views)
    H = max(max(alt_col), yv + hv) + 70
    d = D("er", X0 * 2 + 5 * W + 4 * G, H,
          "Diagrama entidade-relação do banco do painel: 32 tabelas em cinco grupos e as 10 views. Linhas laranja são "
          "chaves estrangeiras; tracejadas são relações lógicas sem chave.")
    for item in corpo:
        if item[0] == "cap":
            d.t(item[1], item[2], item[3], "dg-cap")
        else:
            _, x, y, w, h, n, linhas, ncol = item
            d.box(x, y, w, h, rx=8)
            d.t(x + 12, y + 20, n, "dg-mi", limite=w - 20, tam=12, mono=True)
            for i, (cls, l) in enumerate(linhas):
                d.t(x + 12, y + 38 + 15 * i, l, cls, limite=w - 20, tam=10.5, mono=True)
    d.box(xv, yv, W, hv, "dg-soft", rx=8)
    d.t(xv + 12, yv + 20, "10 views", "dg-mi")
    d.t(xv + 12, yv + 36, "security_invoker = true", "dg-m")
    for i, v in enumerate(views):
        d.t(xv + 12, yv + 58 + 16 * i, v, "dg-m", limite=W - 20, tam=10.5, mono=True)

    def bx(n):
        return caixas[n]
    def vert(filho, pai, dx=0, cls="dg-acc"):
        fx, fy, fw, fh = bx(filho); px, py, pw, ph = bx(pai)
        cx = fx + fw / 2 + dx
        d.linha(f"M{cx} {fy} V{py + ph + 2}", cls)
    vert("agentes", "departamentos", -40)
    x, y, w, h = bx("departamentos")
    ax, ay, aw, ah = bx("agentes")
    d.linha(f"M{x + w / 2 + 40} {y + h} V{ay - 2}")  # gerente_id: departamentos → agentes
    d.linha(f"M{ax + aw} {ay + 16} H{ax + aw + 13} V{ay + 34} H{ax + aw + 2}")  # fiscalizado_por (auto)
    vert("metricas", "publicacoes")
    vert("perfil_demografia", "perfil_snapshots")
    vert("uso_execucao", "execucoes")
    vert("biblioteca_arquivos", "biblioteca_materiais")
    vert("capa_estilos_exemplos", "capa_estilos")
    vert("prontos", "videos", 0, "dg-dash")
    vx, vy, vw, vh = bx("videos")
    fx, fy, fw, fh = bx("fila")
    d.linha(f"M{fx} {fy + 18} H{fx - 12} V{vy + vh - 14} H{vx - 2}", "dg-dash")
    # para videos pela direita, pelo corredor entre as colunas 3 e 4
    dir_ = vx + vw
    for (n, gx, chegada) in [("biblioteca_materiais", 731, 16), ("biblioteca_arquivos", 723, 30), ("animacoes", 715, 44)]:
        x, y, w, h = bx(n)
        sy = y + 16
        d.linha(f"M{x} {sy} H{gx} V{vy + chegada} H{dir_ + 2}")
    # legenda
    ly = H - 30
    d.add(f'<path class="dg-acc" d="M20 {ly} H60" marker-end="url(#er-a)"/>')
    d.t(68, ly + 4, "chave estrangeira (FK), da filha para a mãe", "dg-lbl")
    d.add(f'<path class="dg-dash" d="M360 {ly} H400" marker-end="url(#er-n)"/>')
    d.t(408, ly + 4, "relação lógica, sem FK (prontos e fila → videos)", "dg-lbl")
    d.t(760, ly + 4, "RLS ligado nas 32, sem nenhuma política", "dg-lbl")
    return d

# ───────────────────────── 3. Papéis e RLS ─────────────────────────
def seguranca():
    d = D("seg", 1000, 300, "Quem acessa o banco: o papel postgres (o sincronizador) escreve; service_role (o app) só "
          "lê; anon e authenticated não têm nenhum privilégio. RLS ligado em todas as tabelas, sem políticas.")
    d.box(390, 80, 220, 140)
    d.t(406, 106, "banco do painel")
    d.t(406, 128, "32 tabelas · 10 views", "dg-s")
    d.t(406, 148, "RLS ligado em todas", "dg-s")
    d.t(406, 168, "0 políticas", "dg-s")
    d.t(406, 196, "127.0.0.1:55322 / :55321", "dg-m")
    d.box(20, 30, 260, 62)
    d.t(36, 55, "postgres", "dg-mi")
    d.t(36, 76, "sincronizador · dono das tabelas", "dg-s", limite=228)
    d.linha("M280 61 H330 V120 H386")
    d.t(305, 52, "escreve", "dg-lbl", "middle")
    d.box(20, 190, 260, 80, "dg-soft")
    d.t(36, 214, "o que for criado depois")
    d.t(36, 236, "default privileges do postgres", "dg-s", limite=228)
    d.t(36, 254, "EXECUTE de PUBLIC revogado", "dg-s", limite=228)
    d.linha("M280 230 H330 V180 H386", "dg-dash")
    d.t(288, 248, "mesma regra", "dg-lbl")
    d.box(720, 30, 260, 62)
    d.t(736, 55, "service_role", "dg-mi")
    d.t(736, 76, "o app Next.js · só no servidor", "dg-s", limite=228)
    d.linha("M610 120 H660 V61 H716")
    d.t(688, 52, "só SELECT", "dg-lbl", "middle")
    d.box(720, 190, 260, 80, "dg-errb")
    d.t(736, 214, "anon · authenticated", "dg-errt")
    d.t(736, 236, "nenhum privilégio", "dg-errs")
    d.t(736, 254, "em tabela, sequência ou função", "dg-errs")
    d.add('<path class="dg-err" d="M610 180 H660 V230 H716"/>')
    d.add('<circle class="dg-errb" cx="660" cy="205" r="10"/>')
    d.add('<path d="M655 200 L665 210 M665 200 L655 210" class="dg-err" style="stroke-dasharray:none;stroke-width:2"/>')
    return d

# ───────────────────────── 4. Sincronização ─────────────────────────
def sincronizacao():
    d = D("sync", 1100, 790, "Fluxograma do sincronizar.py: três gatilhos, a leitura só de leitura dos arquivos, a "
          "gravação numa transação, os três erros que param a passagem e o que ele nunca toca.")
    CX, MX, MW = 510, 360, 300
    trig = [(150, 200, "launchd", "a cada 900 s"), (380, 240, "RunAtLoad", "ao entrar na sessão do Mac"),
            (650, 330, "manual", "uv run python painel/sync/sincronizar.py")]
    for x, w, t, s in trig:
        d.box(x, 16, w, 54)
        d.t(x + 16, 38, t)
        d.t(x + 16, 57, s, "dg-m" if t == "manual" else "dg-s", limite=w - 24, tam=10.5, mono=(t == "manual"))
    d.add(f'<path class="dg-acc" d="M250 70 V90 H{CX} M815 70 V90 H{CX}"/>')
    d.linha(f"M{CX} 70 V106")
    d.box(MX, 110, MW, 52)
    d.t(MX + 16, 132, "ler_projeto()")
    d.t(MX + 16, 151, "lê os arquivos do quadro à esquerda", "dg-s", limite=MW - 24, tam=11)
    fontes = [".claude/agents/*.md · painel/equipe.yaml", "videos/*/portoes.json (portoes.py)",
              "_controle/tracker.md · status.json", "roteiro.json · ARQUIVADO.json",
              "brutos/principal/ (só listagem e stat)", "05-render-pronto/*/pacote.json",
              "06-publicar/* · 07-publicados/*", "_controle/perfil/ · calendario.md", "_controle/nao-publicar.json",
              "videos/*/material/** · brutos/extras/**", "00-marca/cor/ · painel/biblioteca.yaml",
              "remotion/src/brand.ts · animacoes/*/brief.md", ".claude/agents · skills · commands",
              "painel/cambio.yaml · PRECOS (no código)", "registros .jsonl + agent-<id>.meta.json"]
    d.box(20, 110, 310, 48 + 19 * len(fontes))
    d.t(36, 134, "o que lê (só leitura)")
    for i, f in enumerate(fontes):
        d.t(36, 158 + 19 * i, f, "dg-m", limite=284, tam=10.5, mono=True)
    d.linha("M330 136 H356", "dg-ln")

    def passo(y, h, titulo, linhas, cls="dg-box", tcls="dg-t", scls="dg-s"):
        d.box(MX, y, MW, h, cls, rx=10 if cls != "dg-dec" else 24)
        d.t(MX + 16 if cls != "dg-dec" else CX, y + 22 if linhas else y + 29, titulo, tcls,
            None if cls != "dg-dec" else "middle")
        for i, l in enumerate(linhas):
            d.t(MX + 16, y + 42 + 18 * i, l, scls, limite=MW - 24, tam=10.5)

    def erro(y, titulo, sub):
        d.box(700, y, 380, 52, "dg-errb")
        d.t(716, y + 22, titulo, "dg-errt", limite=350, tam=12)
        d.t(716, y + 40, sub, "dg-errs", limite=350, tam=10.5)

    passo(200, 48, "todo arquivo legível?", [], "dg-dec")
    d.linha(f"M{CX} 162 V196")
    erro(198, "✗ … nada gravado", "exit 1")
    d.linha("M660 224 H696", "dg-err")
    d.t(678, 216, "não", "dg-lbl", "middle")
    d.linha(f"M{CX} 248 V286")
    d.t(CX + 8, 272, "sim", "dg-lbl")
    passo(290, 52, "gravar()", ["abre o Postgres pelo PAINEL_DB_URL (psycopg)"])
    d.linha(f"M{CX} 342 V376")
    passo(380, 48, "banco no ar?", [], "dg-dec")
    erro(378, "✗ banco do painel fora do ar", "ligar com: bash painel/iniciar.sh · exit 1")
    d.linha("M660 404 H696", "dg-err")
    d.t(678, 396, "não", "dg-lbl", "middle")
    d.linha(f"M{CX} 428 V466")
    d.t(CX + 8, 452, "sim", "dg-lbl")
    passo(470, 104, "uma transação só", ["truncate das 29 tabelas-espelho + insert",
                                         "execucoes e uso_execucao: nunca truncadas",
                                         "regrava o que o .jsonl ainda mostra; o que",
                                         "sumiu fica com registro_presente = false"])
    d.box(700, 482, 380, 52, "dg-soft")
    d.t(716, 504, "⚠ anomalia que não para a passagem", limite=350)
    d.t(716, 522, "vira uma linha ⚠ na saída", "dg-s", limite=350, tam=11)
    d.linha("M660 508 H696", "dg-dash")
    d.linha(f"M{CX} 574 V606")
    passo(610, 48, "o banco aceitou?", [], "dg-dec")
    erro(608, "✗ recusa do banco (FK, chave repetida)", "DETAIL do Postgres · transação desfeita")
    d.linha("M660 634 H696", "dg-err")
    d.t(678, 626, "não", "dg-lbl", "middle")
    d.linha(f"M{CX} 658 V696")
    d.t(CX + 8, 682, "sim", "dg-lbl")
    d.box(MX, 700, MW, 56, "dg-okb")
    d.t(MX + 16, 723, "passagem gravada", "dg-okt")
    d.t(MX + 16, 742, "1 linha em sincronizacoes (guarda 7 dias)", "dg-oks", limite=MW - 24, tam=10.5)
    d.t(700, 690, "Em todo erro, o painel continua mostrando", "dg-lbl")
    d.t(700, 706, "a passagem anterior.", "dg-lbl")
    # nunca toca
    y0 = 110 + 48 + 19 * len(fontes) + 40
    nunca = ["videos/ · 00-marca/", "_controle/ · scripts/", "~/.claude (só lê os registros)",
             "portoes.SO_LEITURA = True", "sys.dont_write_bytecode = True", "vídeos: nenhum é aberto",
             "nenhum texto de conversa no banco"]
    d.box(20, y0, 310, 44 + 19 * len(nunca), "dg-ink")
    d.t(36, y0 + 24, "nunca escreve em / nunca faz", "dg-inkt")
    for i, l in enumerate(nunca):
        d.t(36, y0 + 48 + 19 * i, l, "dg-inks", limite=284, tam=10.5, mono=True)
    return d

def todos(dados):
    return {"arquitetura": arquitetura(), "banco": banco(dados), "seguranca": seguranca(),
            "sincronizacao": sincronizacao()}
