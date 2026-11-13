"""Diagramas do Volume 1 · Estúdio. Mesma base visual do gerador do painel (docs/painel/gerador/diagramas.py,
que não é alterado): as classes dg-* ficam estilizadas pelo CSS da página (tokens nos dois temas) e, no SVG solto,
por um <style> com os valores do tema Marfim + as fontes Geist embutidas.

Todos os textos saem do dossiê (docs/estudio/dossie/dossie.md) ou do dados.json."""
import html

AVISOS = []


def esc(s):
    return html.escape(s, quote=True)


def largura(txt, tam, mono=False):
    return len(txt) * tam * (0.6 if mono else 0.56)


def quebrar(txt, n):
    """Quebra por palavras em linhas de até n caracteres."""
    out, atual = [], ""
    for p in txt.split():
        cand = (atual + " " + p).strip()
        if len(cand) > n and atual:
            out.append(atual)
            atual = p
        else:
            atual = cand
    if atual:
        out.append(atual)
    return out


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
        m = ""
        if seta:
            k = "a" if "acc" in cls else ("e" if "err" in cls else "n")
            m = f' marker-end="url(#{s.nome}-{k})"'
        s.add(f'<path class="{cls}" d="{d}"{m}/>')

    def num(s, x, y, n, r=11):
        s.add(f'<circle class="dg-num" cx="{x}" cy="{y}" r="{r}"/>'
              f'<text class="dg-numt" x="{x}" y="{y + 4}" text-anchor="middle">{n}</text>')

    def pilula(s, x, y, txt, cls="hl", tam=10.5):
        w = largura(txt, tam, True) + 16
        s.add(f'<rect class="dg-{cls}" x="{x}" y="{y}" width="{w:.0f}" height="20" rx="10"/>')
        s.t(x + 8, y + 14, txt, "dg-hlt" if cls == "hl" else ("dg-inks" if cls == "ink" else "dg-m"))
        return w

    def svg(s, solto=False):
        defs = "".join(
            f'<marker id="{s.nome}-{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path class="dg-ah{c}" d="M0 0L10 5L0 10z"/></marker>'
            for k, c in (("a", "a"), ("n", "n"), ("e", "e")))
        defs = f"<defs>{defs}</defs>"
        corpo = "\n".join(s.el)
        if solto:
            return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s.w} {s.h}" width="{s.w}" height="{s.h}" '
                    f'role="img" aria-label="{esc(s.rotulo)}">\n<style>{CSS_SOLTO}</style>\n{defs}\n'
                    f'<rect class="dg-bg" x="0" y="0" width="{s.w}" height="{s.h}"/>\n{corpo}\n</svg>\n')
        return (f'<svg class="dg" viewBox="0 0 {s.w} {s.h}" role="img" aria-label="{esc(s.rotulo)}" '
                f'style="--dg-w:{s.w}px">{defs}\n{corpo}\n</svg>')


REGRAS = """
.dg-bg{fill:%(bg)s}
.dg text{font-family:Geist,Inter,system-ui,sans-serif;font-variant-numeric:tabular-nums}
.dg-box{fill:%(surface)s;stroke:%(line_strong)s;stroke-width:1}
.dg-soft{fill:%(sunken)s;stroke:%(line)s;stroke-width:1}
.dg-dec{fill:%(bg)s;stroke:%(ink)s;stroke-width:1.5}
.dg-ink{fill:%(ink)s;stroke:%(ink)s;stroke-width:1}
.dg-hl{fill:%(accent_soft)s;stroke:none}
.dg-acb{fill:%(surface)s;stroke:%(accent)s;stroke-width:2}
.dg-zone{fill:none;stroke:%(line_strong)s;stroke-width:1;stroke-dasharray:5 5}
.dg-frame{fill:none;stroke:%(ink_2)s;stroke-width:1;stroke-dasharray:3 3}
.dg-errb{fill:%(danger_soft)s;stroke:%(danger)s;stroke-width:1}
.dg-okb{fill:%(positive_soft)s;stroke:%(positive)s;stroke-width:1}
.dg-t{fill:%(ink)s;font-size:13px;font-weight:600}
.dg-s{fill:%(ink_2)s;font-size:11px;font-weight:500}
.dg-m{fill:%(ink_2)s;font-size:10.5px;font-weight:500;font-family:"Geist Mono",ui-monospace,monospace !important}
.dg-mi{fill:%(ink)s;font-size:12px;font-weight:600;font-family:"Geist Mono",ui-monospace,monospace !important}
.dg-ep{fill:%(ink)s;font-size:11.5px;font-weight:600;font-family:"Geist Mono",ui-monospace,monospace !important}
.dg-hlt{fill:%(accent_ink)s;font-size:10.5px;font-weight:600;font-family:"Geist Mono",ui-monospace,monospace !important}
.dg-cap{fill:%(ink_2)s;font-size:10.5px;font-weight:600;letter-spacing:.08em}
.dg-lbl{fill:%(ink_2)s;font-size:10.5px;font-weight:600}
.dg-inkt{fill:%(bg)s;font-size:13px;font-weight:600}
.dg-inks{fill:%(bg)s;font-size:10.5px;font-weight:500;font-family:"Geist Mono",ui-monospace,monospace !important}
.dg-inkl{fill:%(bg)s;font-size:11px;font-weight:500}
.dg-errt{fill:%(danger)s;font-size:12px;font-weight:600}
.dg-errs{fill:%(danger)s;font-size:10.5px;font-weight:500}
.dg-okt{fill:%(positive)s;font-size:13px;font-weight:600}
.dg-oks{fill:%(positive)s;font-size:10.5px;font-weight:500}
.dg-acc{fill:none;stroke:%(accent)s;stroke-width:2;stroke-linejoin:round}
.dg-ln{fill:none;stroke:%(ink_2)s;stroke-width:1.25;stroke-linejoin:round}
.dg-dash{fill:none;stroke:%(ink_2)s;stroke-width:1.25;stroke-dasharray:5 4;stroke-linejoin:round}
.dg-life{fill:none;stroke:%(line_strong)s;stroke-width:1;stroke-dasharray:2 4}
.dg-err{fill:none;stroke:%(danger)s;stroke-width:1.25;stroke-dasharray:5 4}
.dg-tick{fill:none;stroke:%(accent)s;stroke-width:1}
.dg-tickn{fill:none;stroke:%(ink_2)s;stroke-width:1}
.dg-grid{fill:none;stroke:%(line)s;stroke-width:1}
.dg-aha{fill:%(accent)s}
.dg-ahn{fill:%(ink_2)s}
.dg-ahe{fill:%(danger)s}
.dg-num{fill:%(accent)s;stroke:%(surface)s;stroke-width:2}
.dg-numt{fill:%(on_accent)s;font-size:11px;font-weight:700}
"""
PAGINA = dict(bg="var(--bg)", surface="var(--surface)", sunken="var(--surface-sunken)", line="var(--line)",
              line_strong="var(--line-strong)", ink="var(--ink)", ink_2="var(--ink-2)", accent="var(--accent)",
              accent_soft="var(--accent-soft)", accent_ink="var(--accent-ink)",
              danger="var(--danger)", danger_soft="var(--danger-soft)", positive="var(--positive)",
              positive_soft="var(--positive-soft)", on_accent="var(--on-accent)")
MARFIM = dict(bg="#f5f2e8", surface="#fbf9f4", sunken="#efebe0", line="#e4dfd2", line_strong="#928874", ink="#111111",
              ink_2="#6b6458", accent="#ff4d00", accent_soft="#ffe8dc", accent_ink="#b33600",
              danger="#c2271b", danger_soft="#fbe3df", positive="#1e7a45", positive_soft="#e3f0e4", on_accent="#111111")
CSS_PAGINA = REGRAS % PAGINA
CSS_SOLTO = None  # preenchido pelo build (com as fontes embutidas)


# ───────────────────────── diagrama de sequência genérico ─────────────────────────
def sequencia(nome, rotulo, parts, passos, W=1160):
    """parts: [(titulo, sub)]; passos: tuplas
       ("m", a, b, rotulo, sub, estilo)  seta de a para b (estilo acc | ret | ln)
       ("self", a, rotulo, sub)          ação interna
       ("quadro", rotulo, a, b) … ("fim",)   moldura (repetição/condição) sobre as colunas a..b
       ("faixa", texto)                  faixa de seção na largura toda
       ("nota", a, b, [linhas], estilo)  caixa de nota (soft | err | ok)"""
    n = len(parts)
    M = 16
    cw = (W - 2 * M) / n
    X = [M + cw * (i + 0.5) for i in range(n)]
    d = D(nome, W, 100, rotulo)
    topo = 12
    for i, (tit, sub) in enumerate(parts):
        bw = cw - 20
        d.box(X[i] - bw / 2, topo, bw, 52, "dg-ink")
        d.t(X[i], topo + 22, tit, "dg-inkt", "middle", limite=bw - 12)
        d.t(X[i], topo + 40, sub, "dg-inks", "middle", limite=bw - 12, tam=10.5, mono=True)
    y = topo + 52 + 30
    pilha, k = [], 0
    for p in passos:
        tipo = p[0]
        if tipo == "m":
            _, a, b, rot, sub, est = p
            k += 1
            xa, xb = X[a], X[b]
            esq = min(xa, xb)
            tx = esq + 22 if xa < xb else esq + 12
            lim = max(abs(xb - xa) - 30, min(460, W - tx - 20))
            d.t(tx, y, rot, "dg-ep", limite=W - tx - 16, tam=11.5, mono=True)
            ya = y + 10
            if sub:
                subs = [q for l in (sub if isinstance(sub, list) else [sub]) for q in quebrar(l, int(lim / 6.2))]
                for j, l in enumerate(subs):
                    d.t(tx, y + 15 + 14 * j, l, "dg-s", limite=lim, tam=11)
                ya = y + 15 + 14 * len(subs) + 2
            cls = {"acc": "dg-acc", "ret": "dg-dash", "ln": "dg-ln"}[est]
            x1 = xa + (12 if xb > xa else -12)
            x2 = xb - 3 if xb > xa else xb + 3
            d.linha(f"M{x1:.1f} {ya} H{x2:.1f}", cls)
            d.num(xa, ya, k)
            y = ya + 30
        elif tipo == "self":
            _, a, rot, sub = p
            k += 1
            xa = X[a]
            lim = min(460, W - xa - 60)
            d.num(xa, y + 2, k)
            d.linha(f"M{xa + 12:.1f} {y + 2} H{xa + 34:.1f} V{y + 22} H{xa + 5:.1f}", "dg-ln")
            d.t(xa + 44, y + 6, rot, "dg-ep", limite=lim, tam=11.5, mono=True)
            subs = [q for l in (sub if isinstance(sub, list) else ([sub] if sub else [])) for q in quebrar(l, int(lim / 6.2))]
            for j, l in enumerate(subs):
                d.t(xa + 44, y + 21 + 14 * j, l, "dg-s", limite=lim, tam=11)
            y += 44 + 14 * max(0, len(subs) - 1) + 6
        elif tipo == "quadro":
            _, rot, a, b = p
            x0, x1 = X[a] - cw / 2 + 8, X[b] + cw / 2 - 8
            pilha.append((x0, x1, y - 8, rot))
            y += 26
        elif tipo == "fim":
            x0, x1, y0, rot = pilha.pop()
            d.add(f'<rect class="dg-frame" x="{x0:.1f}" y="{y0}" width="{x1 - x0:.1f}" height="{y - y0 - 12}" rx="6"/>')
            w = largura(rot, 10.5, True) + 16
            d.add(f'<rect class="dg-hl" x="{x0:.1f}" y="{y0}" width="{w:.0f}" height="20" rx="6"/>')
            d.t(x0 + 8, y0 + 14, rot, "dg-hlt")
            y += 16
        elif tipo == "faixa":
            d.add(f'<rect class="dg-soft" x="{M}" y="{y - 6}" width="{W - 2 * M}" height="26" rx="6"/>')
            d.t(W / 2, y + 11, p[1], "dg-cap", "middle")
            y += 40
        elif tipo == "nota":
            _, a, b, linhas, est = p
            x0, x1 = X[a] - cw / 2 + 8, X[b] + cw / 2 - 8
            linhas = [q for l in linhas for q in quebrar(l, int((x1 - x0 - 24) / 6.1))]
            h = 16 + 16 * len(linhas)
            cls, tc = {"soft": ("dg-soft", "dg-s"), "err": ("dg-errb", "dg-errs"), "ok": ("dg-okb", "dg-oks")}[est]
            d.box(x0, y - 4, x1 - x0, h, cls, rx=8)
            for j, l in enumerate(linhas):
                d.t(x0 + 12, y + 14 + 16 * j, l, tc, limite=x1 - x0 - 20, tam=11)
            y += h + 18
    H = y + 6
    vidas = [f'<path class="dg-life" d="M{X[i]:.1f} {topo + 52} V{H - 8}"/>' for i in range(n)]
    d.el = vidas + d.el
    d.h = H
    return d


# ───────────────────────── capa: o sistema inteiro ─────────────────────────
def sistema():
    d = D("sistema", 1200, 690,
          "O sistema inteiro: a produção com agentes do Claude Code e portões GAUNTLET gera o pacote; o apresentador "
          "move para a fila; o launchd publica no Instagram e no Facebook pela Graph API (arquivos no R2); comentários "
          "viram direct com o PDF; as métricas aos 5 dias voltam ao roteirista; o painel lê tudo a cada 15 minutos.")
    d.add('<rect class="dg-zone" x="8" y="30" width="904" height="650" rx="14"/>')
    d.t(24, 52, "NO MAC · ARQUIVOS + LAUNCHD", "dg-cap")
    d.add('<rect class="dg-zone" x="928" y="30" width="264" height="650" rx="14"/>')
    d.t(944, 52, "INTERNET", "dg-cap")
    d.t(24, 20, "Os dois pontos de parada humanos estão em preto: a aprovação da EDL e a ida para a fila.", "dg-s")
    # produção
    d.box(24, 70, 250, 300)
    d.t(40, 94, "produção")
    d.t(40, 112, "agentes do Claude Code + scripts uv", "dg-s", limite=220, tam=11)
    etapas = ["pauta → roteiro → PDF", "material (yt-dlp) · extras", "gravação (apresentador)",
              "edição: Scribe → EDL", None, "corte → cor → Remotion", "música + áudio −14 LUFS", "capa → QA final"]
    yy = 140
    for e_ in etapas:
        if e_ is None:
            d.box(36, yy - 15, 226, 24, "dg-ink", rx=6)
            d.t(48, yy + 1, "PARA · aprovação da EDL", "dg-inks")
        else:
            d.t(48, yy, e_, "dg-m", limite=210, tam=10.5, mono=True)
        yy += 26
    d.box(36, 342, 226, 22, "dg-hl", rx=6)
    d.t(48, 357, "portões GAUNTLET em cada etapa", "dg-hlt", limite=210, tam=10.5, mono=True)
    d.num(274, 70, 1)
    # pacote
    d.box(330, 70, 170, 84)
    d.t(346, 94, "pacote selado")
    d.t(346, 114, "05-render-pronto/", "dg-m")
    d.t(346, 130, "<slug>/ + selo", "dg-m")
    d.linha("M274 112 H326")
    d.num(500, 70, 2)
    # fila
    d.box(330, 200, 170, 96, "dg-ink")
    d.t(346, 224, "fila = autorização", "dg-inkt")
    d.t(346, 244, "06-publicar/<slug>/", "dg-inks")
    d.t(346, 262, "post.json", "dg-inks")
    d.t(346, 280, "publicar_em (ISO)", "dg-inks")
    d.linha("M415 154 V196")
    d.t(423, 182, "/publicar (move)", "dg-lbl")
    d.num(500, 200, 3)
    # publicar.py
    d.box(560, 200, 200, 96)
    d.t(576, 224, "publicar.py --due")
    d.t(576, 244, "launchd · a cada 900 s", "dg-m")
    d.t(576, 262, "confere selo + portão", "dg-s", limite=170, tam=11)
    d.t(576, 280, "trava .publicar.lock", "dg-s", limite=170, tam=11)
    d.linha("M500 248 H556")
    d.t(528, 240, "lê", "dg-lbl", "middle")
    d.num(760, 200, 4)
    # internet
    d.box(944, 70, 232, 70, "dg-soft")
    d.t(960, 94, "Cloudflare R2")
    d.t(960, 114, "vídeo, capa, slides, PDF", "dg-s", limite=200, tam=11)
    d.t(960, 130, "link público (API S3)", "dg-s", limite=200, tam=11)
    d.box(944, 170, 232, 66, "dg-acb")
    d.t(960, 194, "Instagram")
    d.t(960, 214, "Graph API v23.0", "dg-m")
    d.t(960, 229, "/media → /media_publish", "dg-m")
    d.box(944, 256, 232, 66, "dg-acb")
    d.t(960, 280, "Página do Facebook")
    d.t(960, 300, "rupload · graph-video", "dg-m")
    d.t(960, 315, "photos + feed", "dg-m")
    d.linha("M760 216 H830 V105 H940")
    d.t(838, 98, "sobe o arquivo", "dg-lbl")
    d.linha("M760 236 H940")
    d.t(850, 228, "URL do R2", "dg-lbl", "middle")
    d.linha("M760 280 H940")
    d.t(850, 272, "bytes do disco", "dg-lbl", "middle")
    d.linha("M1060 166 V144", "dg-dash")
    d.t(1068, 160, "baixa", "dg-lbl")
    # publicados
    d.box(560, 340, 200, 80)
    d.t(576, 364, "07-publicados/<slug>/")
    d.t(576, 384, "post.json + permalinks", "dg-s", limite=170, tam=11)
    d.t(576, 402, "dm-material.json", "dg-m")
    d.linha("M660 296 V336", "dg-ln")
    d.t(668, 322, "move", "dg-lbl")
    d.num(760, 340, 5)
    # comentarios
    d.box(560, 450, 200, 56)
    d.t(576, 472, "responder_comentarios")
    d.t(576, 491, "launchd · a cada 120 s", "dg-m")
    d.linha("M760 470 H900 V300 H940")
    d.t(772, 496, "comentário → direct", "dg-lbl")
    d.linha("M660 420 V446", "dg-ln")
    d.num(760, 450, 6)
    # metricas
    d.box(560, 522, 200, 56)
    d.t(576, 544, "metricas.py")
    d.t(576, 563, "09:30 · posts ≥ 5 dias", "dg-m")
    d.linha("M1060 322 V558 H764", "dg-dash")
    d.t(1068, 540, "/insights", "dg-lbl")
    d.num(760, 522, 7)
    # aprendizados → produção
    d.box(330, 522, 190, 56, "dg-soft")
    d.t(346, 544, "aprendizados.md")
    d.t(346, 563, "analista-de-metricas", "dg-m")
    d.linha("M560 550 H524")
    d.linha("M330 550 H150 V374")
    d.t(158, 400, "volta ao roteirista", "dg-lbl")
    # painel: faixa no fim (lê todas as pastas acima)
    d.box(24, 604, 872, 60, "dg-soft")
    d.t(40, 628, "painel web · Volume 2")
    d.t(40, 648, "painel/sync/sincronizar.py a cada 15 min lê todas as pastas acima (só leitura) → Postgres local → Next.js", "dg-s", limite=840, tam=11)
    return d


# ───────────────────────── automação: 24 horas ─────────────────────────
def jobs24(jobs):
    X0, X1 = 300, 1180
    ph = (X1 - X0) / 24
    linhas = [
        ("uk.korvu.publicar", "publicar.py --due", 900, True, "a cada 15 min"),
        ("uk.korvu.comentarios", "responder_comentarios.py", 120, True, "a cada 2 min"),
        ("uk.korvu.metricas", "metricas.py", None, True, "todo dia às 09:30"),
        ("uk.korvu.painel", "painel/sync/sincronizar.py", 900, False, "a cada 15 min + ao entrar"),
        ("uk.korvu.contexto", "contexto.sincronizar", 1800, False, "a cada 30 min + ao entrar"),
    ]
    assert [l[0] for l in linhas] == [j["nome"] for j in jobs]
    RH, Y0 = 64, 64
    H = Y0 + RH * len(linhas) + 70
    d = D("jobs-24h", 1200, H,
          "Linha do tempo de 24 horas com os 5 jobs do launchd: publicar e painel a cada 15 minutos, "
          "comentários a cada 2 minutos, contexto a cada 30 minutos e métricas uma vez por dia às 09:30.")
    for h in range(0, 25, 3):
        x = X0 + h * ph
        d.add(f'<path class="dg-grid" d="M{x:.1f} {Y0 - 10} V{Y0 + RH * len(linhas)}"/>')
        d.t(x, Y0 - 18, f"{h:02d}h", "dg-m", "middle")
    d.t(20, Y0 - 18, "JOB (LABEL) · SCRIPT", "dg-cap")
    for i, (lab, scr, seg, net, txt) in enumerate(linhas):
        y = Y0 + i * RH
        d.add(f'<path class="dg-grid" d="M20 {y + RH} H{X1}"/>')
        d.t(20, y + 24, lab, "dg-mi", limite=270, tam=12, mono=True)
        d.t(20, y + 42, scr, "dg-m", limite=270, tam=10.5, mono=True)
        cls = "dg-tick" if net else "dg-tickn"
        if seg:
            passo = seg / 3600 * ph
            nn = int(24 * 3600 / seg)
            segs = " ".join(f"M{X0 + j * passo:.2f} {y + 16}V{y + 40}" for j in range(nn))
            d.add(f'<path class="{cls}" d="{segs}"/>')
            d.add(f'<rect class="dg-bg" x="{X0 + 4}" y="{y + 44}" width="{largura(txt, 11) + 90:.0f}" height="16"/>')
            d.t(X0 + 6, y + 56, f"{txt} · até {nn}× por dia", "dg-s")
        else:
            x = X0 + 9.5 * ph
            d.add(f'<path class="dg-acc" d="M{x:.1f} {y + 10}V{y + 44}" style="stroke-width:3"/>')
            d.add(f'<circle class="dg-num" cx="{x:.1f}" cy="{y + 27}" r="6"/>')
            d.t(x + 12, y + 31, "09:30 · lê os posts com ≥ 5 dias", "dg-ep")
            d.t(X0 + 6, y + 56, f"{txt} · 1× por dia", "dg-s")
    ly = Y0 + RH * len(linhas) + 30
    d.add(f'<path class="dg-tick" d="M20 {ly - 8}V{ly + 8} M24 {ly - 8}V{ly + 8} M28 {ly - 8}V{ly + 8}"/>')
    d.t(38, ly + 4, "fala com a internet (Meta, R2)", "dg-lbl")
    d.add(f'<path class="dg-tickn" d="M330 {ly - 8}V{ly + 8} M334 {ly - 8}V{ly + 8} M338 {ly - 8}V{ly + 8}"/>')
    d.t(348, ly + 4, "fica no Mac (Postgres local)", "dg-lbl")
    d.t(560, ly + 4, "Cada risco é uma execução. Com o Mac dormindo, nada roda; o publicar.py tem a regra das 6 h.", "dg-lbl")
    return d


# ───────────────────────── automação: sem servidor ─────────────────────────
def sem_servidor():
    d = D("sem-servidor", 1100, 300,
          "Comparação: com webhook a Meta precisa de um endereço na internet ligado 24 horas; no estúdio o launchd "
          "roda um script que pergunta à Meta a cada 2 minutos, e com o Mac desligado nada se perde porque a Meta "
          "deixa responder até 7 dias depois do comentário.")
    # esquerda
    d.t(24, 26, "COM WEBHOOK (o que o estúdio não usa)", "dg-cap")
    d.box(24, 50, 190, 64, "dg-acb")
    d.t(40, 76, "Meta")
    d.t(40, 96, "avisa quando há comentário", "dg-s", limite=166, tam=11)
    d.box(300, 50, 220, 64, "dg-errb")
    d.t(316, 76, "endereço na internet", "dg-errt")
    d.t(316, 96, "ligado 24 h", "dg-errs")
    d.linha("M214 82 H296", "dg-err")
    d.t(255, 74, "webhook", "dg-lbl", "middle")
    d.box(300, 140, 220, 84, "dg-soft")
    d.t(316, 164, "ferramentas descartadas")
    d.t(316, 184, "n8n · Zapier · Make: não usados", "dg-s", limite=196, tam=11)
    d.t(316, 202, "ManyChat: “pago por contato”", "dg-s", limite=196, tam=11)
    d.t(316, 218, "(descartado em 15/09)", "dg-s", limite=196, tam=11)
    d.add('<path class="dg-grid" d="M550 20 V280"/>')
    # direita
    d.t(580, 26, "NO ESTÚDIO (sem servidor)", "dg-cap")
    d.box(580, 50, 150, 64, "dg-ink")
    d.t(596, 76, "launchd", "dg-inkt")
    d.t(596, 96, "o macOS agenda", "dg-inkl")
    d.box(770, 50, 150, 64)
    d.t(786, 76, "script Python")
    d.t(786, 96, "uv run · local", "dg-s")
    d.box(960, 50, 120, 64, "dg-acb")
    d.t(976, 76, "Meta")
    d.t(976, 96, "Graph API", "dg-s")
    d.linha("M730 82 H766", "dg-ln")
    d.t(748, 132, "roda", "dg-lbl", "middle")
    d.linha("M920 74 H956")
    d.t(938, 44, "pergunta", "dg-lbl", "middle")
    d.linha("M956 96 H924", "dg-dash")
    d.box(580, 150, 500, 110, "dg-okb")
    d.t(596, 174, "o que substitui o servidor", "dg-okt")
    d.t(596, 196, "fila = uma pasta (06-publicar/) · estado = JSON no disco", "dg-oks", limite=470, tam=10.5)
    d.t(596, 214, "agenda = launchd · comentários lidos a cada 2 min", "dg-oks", limite=470, tam=10.5)
    d.t(596, 232, "Mac desligado: nada se perde, a Meta deixa responder até 7 dias", "dg-oks", limite=470, tam=10.5)
    d.t(596, 250, "“o mesmo script pode ir para um servidor sem mudar nada”", "dg-oks", limite=470, tam=10.5)
    return d


# ───────────────────────── edição: 14 passos ─────────────────────────
def grade(nome, rotulo, itens, por_linha=5, W=1240, BH=118, legenda=None):
    """itens: dicts com n, titulo, mono, linhas(list), estilo (box|ink|acb), tag (texto, estilo) opcional."""
    M, G = 20, 30
    BW = (W - 2 * M - (por_linha - 1) * G) / por_linha
    GV = 46
    linhas_n = (len(itens) + por_linha - 1) // por_linha
    H = 20 + linhas_n * (BH + GV) + (30 if legenda else 0)
    d = D(nome, W, H, rotulo)
    pos = []
    for i, it in enumerate(itens):
        r, c = divmod(i, por_linha)
        x, y = M + c * (BW + G), 20 + r * (BH + GV)
        pos.append((x, y))
        est = it.get("estilo", "box")
        d.box(x, y, BW, BH, {"box": "dg-box", "ink": "dg-ink", "acb": "dg-acb", "soft": "dg-soft"}[est])
        tt, ts, tm = ("dg-inkt", "dg-inkl", "dg-inks") if est == "ink" else ("dg-t", "dg-s", "dg-m")
        d.num(x + 18, y + 20, it["n"])
        d.t(x + 36, y + 25, it["titulo"], tt, limite=BW - 44)
        yy = y + 44
        if it.get("mono"):
            for l in quebrar(it["mono"], int((BW - 24) / 6.3)):
                d.t(x + 12, yy, l, tm, limite=BW - 20, tam=10.5, mono=True)
                yy += 15
            yy += 3
        for l in it.get("linhas", []):
            d.t(x + 12, yy, l, ts, limite=BW - 20, tam=11)
            yy += 15
        if yy > y + BH - (26 if it.get("tag") else 2):
            AVISOS.append(f"{nome}: caixa {it['n']} transborda ({yy - y} > {BH})")
        if it.get("tag"):
            txt, est2 = it["tag"]
            d.pilula(x + 10, y + BH - 28, txt, est2)
    for i in range(len(itens) - 1):
        (x, y), (x2, y2) = pos[i], pos[i + 1]
        if y2 == y:
            d.linha(f"M{x + BW:.1f} {y + BH / 2} H{x2 - 4:.1f}")
        else:
            mid = y + BH + GV / 2
            d.linha(f"M{x + BW / 2:.1f} {y + BH} V{mid} H{x2 + BW / 2:.1f} V{y2 - 4}")
    if legenda:
        d.t(M, H - 14, legenda, "dg-lbl")
    return d


def edicao(passos):
    LIN = {
        1: ["1440×2560, 10-bit 4:2:2, V-Log", "WAV 48 kHz 24-bit, passa-altas", "60 Hz, sem redução de ruído"],
        2: ["Scribe v2: tempo por palavra", "diarização de 2 vozes", "sem chave → mlx-whisper local"],
        3: ["separa o apresentador da voz", "do ChatGPT: diarização +", "graves, nível, pitch + HMM"],
        4: ["último take limpo (sim ≥ 0,80)", "[PARAFRASE] a partir de 0,45", "abaixo → [FALTANDO]"],
        5: ["in = 1.ª palavra − 0,06 s;", "pausa interna > 0,25 s fica", "0,12 s; zoom 1.00 ↔ 1.12"],
        6: ["edl.json.aprovado = true", "regra rígida 1: sem isso", "nada é renderizado"],
        7: ["corte.mp4 10-bit V-Log", "grade de frames; alças 15 ms,", "cruzamento de 30 ms"],
        8: ["5 quadros −0,2…+0,2 s + forma", "de onda de ±0,5 s em cada corte"],
        9: ["WER ≤ 8 %, A/V ≤ 1 frame,", "voz da IA no corte ≤ 0,2 s"],
        10: ["16 bits: V-Log → Rec.709 →", "primária ±0,5 stop → LUT da", "marca → bt709; grão padrão 0"],
        11: ["legendas do texto do roteiro,", "extras split/full/card, cartão", "do CTA; h264 CRF 18"],
        12: ["1,5:1 → −14 LUFS → limitador", "com teto = alvo − 0,3 dB;", "música −22 dB com ducking"],
        13: ["SPEC: 1080×1920, 25 fps, High", "yuv420p, AAC 48 kHz, 3–900 s,", "−14 ±1 LUFS, TP ≤ −1,5"],
        14: ["05-render-pronto/<slug>/", "com o selo GAUNTLET"],
    }
    itens = []
    for p in passos:
        n = p["passo"]
        script = " + ".join(x.rsplit("/", 1)[-1] for x in (p["script"] or "").split(" + ")) if p["script"] else ""
        titulo = {"Alinhamento + escolha do take": "Alinhamento + take"}.get(p["nome"], p["nome"])
        it = dict(n=n, titulo=titulo, mono=script, linhas=LIN[n])
        if n == 6:
            it.update(estilo="ink", titulo="PARA · aprovação humana", mono="")
        if n == 2:
            it["tag"] = ("ElevenLabs Scribe", "hl")
        itens.append(it)
    assert len(itens) == 14
    return grade("edicao", "Os 14 passos da edição, da ingestão ao pacote. O passo 6 é a parada humana: nada é "
                 "renderizado sem a EDL aprovada.", itens, BH=138,
                 legenda="Passos 1–9: skill corte-por-roteiro. Passos 10–14: cor, gráficos, áudio, QA e pacote (/renderizar).")


def pipeline(etapas):
    TAG = {"PAUTA": "PORTÃO PAUTA", "ROTEIRO": "PORTÃO ROTEIRO", "IMAGEM": "PORTÃO IMAGEM", "CORTE": "PORTÃO CORTE",
           "PUBLICACAO": "PORTÃO PUBLICACAO"}
    itens = []
    for i, p in enumerate(etapas, 1):
        po = p["portao"]
        if po in TAG:
            tag = (TAG[po], "hl")
        elif po == "aprovação humana da EDL":
            tag = ("aprovação humana", "ink")
        elif po and po.startswith("revisão 1"):
            tag = ("revisão 1", "soft")
        elif po and po.startswith("exige"):
            tag = ("exige os portões", "hl")
        elif po and po.startswith("confere"):
            tag = ("confere selo + portão", "hl")
        else:
            tag = None
        linhas = quebrar(p["quem"], 31) + quebrar("→ " + p["sai"], 31)
        assert len(linhas) <= 5, linhas
        it = dict(n=i, titulo=p["etapa"], linhas=linhas, tag=tag)
        if p["etapa"] == "Gravação":
            it["estilo"] = "soft"
        if "launchd" in p["quem"]:
            it["estilo"] = "acb"
        itens.append(it)
    assert len(itens) == 20
    return grade("pipeline", "As 20 etapas do pipeline, do tema às métricas, com o portão GAUNTLET de cada uma. "
                 "Com borda laranja, as etapas que o launchd roda sozinho.", itens,
                 legenda="Borda laranja = roda sozinha pelo launchd. Caixa cinza = o apresentador grava. "
                         "Pílula = quem aprova antes de seguir.", BH=150)


# ───────────────────────── GAUNTLET ─────────────────────────
def gauntlet():
    d = D("gauntlet", 1160, 360,
          "Como um portão GAUNTLET funciona: o construtor entrega, o portão audita; APROVADO fica preso ao sha256 dos "
          "arquivos; BLOQUEADO por S0 ou S1 volta ao construtor, até 3 voltas, e na terceira vira ESCALADO para "
          "decisão humana; S2 vai para o backlog. Arquivo mudado depois do APROVADO vence o veredicto.")
    d.box(20, 120, 180, 70)
    d.t(36, 146, "construtor")
    d.t(36, 166, "ex.: colorista", "dg-s", limite=150, tam=11)
    d.box(270, 110, 200, 90, "dg-ink")
    d.t(286, 138, "portão (gerente)", "dg-inkt")
    d.t(286, 158, "audita, não constrói", "dg-inkl")
    d.t(286, 176, "roda sozinho", "dg-inkl")
    d.linha("M200 155 H266")
    d.t(233, 147, "entrega", "dg-lbl", "middle")
    # aprovado
    d.box(560, 30, 260, 84, "dg-okb")
    d.t(576, 56, "APROVADO", "dg-okt")
    d.t(576, 76, "veredicto preso ao sha256", "dg-oks", limite=230, tam=10.5)
    d.t(576, 92, "dos arquivos (portoes.json)", "dg-oks", limite=230, tam=10.5)
    d.linha("M470 130 H515 V72 H556")
    # bloqueado
    d.box(560, 196, 260, 84, "dg-errb")
    d.t(576, 222, "BLOQUEADO · S0 ou S1", "dg-errt")
    d.t(576, 242, "o construtor corrige e volta", "dg-errs", limite=230, tam=10.5)
    d.t(576, 258, "ao mesmo portão (até 3 voltas)", "dg-errs", limite=230, tam=10.5)
    d.linha("M470 180 H515 V238 H556", "dg-err")
    d.linha("M690 280 V320 H110 V194", "dg-err")
    d.t(400, 314, "corrige", "dg-errs", "middle")
    d.box(870, 214, 270, 50, "dg-ink")
    d.t(886, 236, "3.ª volta → ESCALADO", "dg-inkt")
    d.t(886, 254, "decisão humana", "dg-inkl")
    d.linha("M820 238 H866", "dg-err")
    d.box(560, 128, 260, 52, "dg-soft")
    d.t(576, 150, "S2 → backlog", "dg-t")
    d.t(576, 168, "não bloqueia", "dg-s")
    d.linha("M470 155 H556", "dg-dash")
    # selo
    d.box(870, 30, 270, 150)
    d.t(886, 54, "pacote e publicação")
    d.t(886, 76, "montar_pacote.py recusa sem os", "dg-s", limite=240, tam=11)
    d.t(886, 92, "portões e sela o pacote", "dg-s", limite=240, tam=11)
    d.t(886, 116, "publicar.py recusa: pacote sem", "dg-s", limite=240, tam=11)
    d.t(886, 132, "selo, arquivo diferente do", "dg-s", limite=240, tam=11)
    d.t(886, 148, "aprovado, post sem PUBLICACAO", "dg-s", limite=240, tam=11)
    d.linha("M820 72 H866")
    d.linha("M690 30 V20 H370 V106", "dg-dash")
    d.t(530, 14, "arquivo mudou depois do APROVADO → o portão roda de novo", "dg-lbl", "middle")
    return d


def todos(dados):
    import sys
    D_ = {}
    D_["sistema"] = sistema()
    D_["meta-reel-instagram"] = sequencia(
        "meta-reel-instagram",
        "Sequência para publicar um Reel no Instagram: o publicar.py sobe vídeo e capa ao R2, confere a URL pública, "
        "cria o contêiner, consulta o status a cada 5 segundos, publica, busca o permalink, grava o dm-material.json "
        "e faz o primeiro comentário.",
        [("pasta do post", "06-publicar/<slug>/"), ("publicar.py", "launchd · --due"), ("Cloudflare R2", "API S3 (boto3)"),
         ("Instagram", "graph.facebook.com/v23.0")],
        [
            ("m", 1, 0, "lê post.json + pacote", "selo GAUNTLET e portão PUBLICACAO conferidos", "ln"),
            ("m", 1, 2, "PUT reels/<slug>/… (vídeo, capa JPEG, PDF)", "CacheControl público; a capa PNG vira JPEG", "acc"),
            ("m", 1, 2, "HEAD na URL pública", "exige HTTP 200 (conferir_publico)", "acc"),
            ("m", 1, 3, "POST /{ig-user-id}/media", "media_type=REELS, video_url, cover_url, caption, share_to_feed, trial_params?", "acc"),
            ("m", 3, 2, "a Meta baixa o vídeo pela URL", None, "ret"),
            ("m", 3, 1, "container_id", "gravado no post.json com a impressão do portão", "ret"),
            ("quadro", "repete a cada 5 s, até 10 min", 1, 3),
            ("m", 1, 3, "GET /{container-id}?fields=status_code,status", "até FINISHED; ERROR ou EXPIRED = falha", "acc"),
            ("fim",),
            ("m", 1, 3, "POST /{ig-user-id}/media_publish", "creation_id · não é idempotente: antes de repetir, confere PUBLISHED e procura pela legenda", "acc"),
            ("m", 3, 1, "media_id", None, "ret"),
            ("m", 1, 3, "GET /{media-id}?fields=permalink", None, "acc"),
            ("m", 1, 0, "grava dm-material.json", "{palavra, media_id_instagram, material_url}", "ln"),
            ("m", 1, 3, "POST /{media-id}/comments", "1.º comentário: a própria conta comenta (primeiro-comentario.txt)", "acc"),
            ("m", 1, 0, "move para 07-publicados/<slug>/", "depois de todas as plataformas: calendário, tracker, status.json, notificação", "ln"),
        ])
    D_["meta-reel-facebook"] = sequencia(
        "meta-reel-facebook",
        "Sequência para publicar no Facebook: o arquivo sobe do disco, nunca por URL. Até 90 segundos vira Reel da "
        "Página (start, rupload, status, finish); acima de 90 segundos vira vídeo da Página com upload retomável em "
        "pedaços.",
        [("arquivo de vídeo", "video/ no disco"), ("publicar.py", "launchd · --due"), ("Página do Facebook", "graph.facebook.com/v23.0"),
         ("upload do Facebook", "rupload · graph-video")],
        [
            ("nota", 0, 3, ["Por que do disco: “o robô do Facebook leva 403 da Cloudflare” no domínio público do R2, embora o do Instagram baixe normalmente (13/10)."], "err"),
            ("faixa", "VÍDEO ATÉ 90 S → REEL DA PÁGINA (A API DE REELS DA PÁGINA SÓ ACEITA 3–90 S)"),
            ("m", 1, 2, "POST /{page-id}/video_reels", "upload_phase=start", "acc"),
            ("m", 2, 1, "video_id, upload_url", None, "ret"),
            ("m", 0, 1, "lê os bytes do arquivo", None, "ln"),
            ("m", 1, 3, "POST rupload.facebook.com/video-upload/{v}/{video-id}", "bytes do arquivo · Authorization: OAuth …, offset, file_size", "acc"),
            ("quadro", "repete até ~5 min", 1, 2),
            ("m", 1, 2, "GET /{video-id}?fields=status", "até uploading_phase = complete", "acc"),
            ("fim",),
            ("m", 1, 2, "POST /{page-id}/video_reels", "upload_phase=finish, video_state=PUBLISHED, description", "acc"),
            ("m", 1, 2, "GET /{video-id}?fields=status,permalink_url", "até pronto", "acc"),
            ("m", 1, 2, "POST /{video-id}/comments", "1.º comentário", "acc"),
            ("faixa", "VÍDEO ACIMA DE 90 S → VÍDEO DA PÁGINA (UPLOAD RETOMÁVEL)"),
            ("m", 1, 3, "POST graph-video…/{page-id}/videos", "upload_phase=start (file_size)", "acc"),
            ("quadro", "um pedido por pedaço", 0, 3),
            ("m", 1, 3, "upload_phase=transfer", "video_file_chunk, start_offset", "acc"),
            ("fim",),
            ("m", 1, 3, "upload_phase=finish", "description, published=true", "acc"),
            ("nota", 1, 3, ["Num pedido só “deu 413 com 171 MB” (15/10): por isso o envio em pedaços."], "soft"),
        ])
    D_["meta-carrossel"] = sequencia(
        "meta-carrossel",
        "Sequência para publicar um carrossel de 3 a 10 slides: no Instagram, um contêiner por slide pela URL do R2 e "
        "depois o contêiner CAROUSEL; no Facebook, cada slide sobe do disco como foto não publicada e um único post "
        "no feed junta todas.",
        [("publicar.py", "launchd · --due"), ("Cloudflare R2", "carrosseis/<slug>/"), ("Instagram", "/{ig-user-id}/media"),
         ("Página do Facebook", "/{page-id}/photos · /feed")],
        [
            ("faixa", "INSTAGRAM · 3 A 10 SLIDES, SÓ JPEG EM IMAGE_URL"),
            ("quadro", "para cada slide", 0, 2),
            ("m", 0, 1, "PUT carrosseis/<slug>/<slide>.jpg", "PNG → JPEG qualidade 95", "acc"),
            ("m", 0, 2, "POST /{ig-user-id}/media", "image_url + is_carousel_item=true · espera cada filho FINISHED", "acc"),
            ("fim",),
            ("m", 0, 2, "POST /{ig-user-id}/media", "media_type=CAROUSEL, children, caption", "acc"),
            ("m", 0, 2, "POST /{ig-user-id}/media_publish", None, "acc"),
            ("faixa", "FACEBOOK · CADA SLIDE SOBE DO DISCO"),
            ("quadro", "para cada slide", 0, 3),
            ("m", 0, 3, "POST /{page-id}/photos", "published=false, multipart source", "acc"),
            ("m", 3, 0, "media_fbid", None, "ret"),
            ("fim",),
            ("m", 0, 3, "POST /{page-id}/feed", "message + attached_media[i]={\"media_fbid\": …} · não idempotente: uma tentativa só", "acc"),
            ("nota", 0, 3, ["Sem Trial e sem capa separada: a capa é o 1.º slide. Proporção fora de 4:5 a 1,91:1 dá 36003 / 2207009 (“o 3:4 do modelo pode não passar”)."], "soft"),
        ])
    D_["meta-agendamento"] = sequencia(
        "meta-agendamento",
        "Sequência do agendamento: a hora mora no post.json, não na Meta. O launchd roda o publicar.py a cada 900 "
        "segundos; com atraso acima de 6 horas o post vai para aguardando_confirmacao e o macOS avisa.",
        [("pasta 06-publicar/", "post.json"), ("publicar.py", "agendar · --due"), ("portao-publicacao", "agente (opus)"),
         ("launchd", "uk.korvu.publicar"), ("Meta", "IG + FB")],
        [
            ("self", 0, "/publicar move a pasta para cá", "mover para 06-publicar/ = autorização para publicar"),
            ("m", 1, 0, "agendar <slug> [--em \"AAAA-MM-DD HH:MM\"]", ["valida o pacote e reserva a próxima vaga livre", "de vagas_semanais → publicar_em (ISO com fuso)"], "ln"),
            ("m", 2, 0, "audita legendas, post.json e arquivos", "sem APROVADO não publica", "ln"),
            ("quadro", "a cada 900 s (StartInterval)", 0, 4),
            ("m", 3, 1, "uv run python scripts/publicar.py --due", "trava _controle/.publicar.lock: nunca duas ao mesmo tempo", "acc"),
            ("m", 1, 0, "estado = agendado e publicar_em ≤ agora?", "precisão: até 15 min depois da hora", "ln"),
            ("quadro", "atraso até 6 h", 1, 4),
            ("m", 1, 4, "publica no Instagram e no Facebook", "e move a pasta para 07-publicados/", "acc"),
            ("fim",),
            ("quadro", "atraso acima de PUBLICAR_ATRASO_MAX_H (6 h): Mac desligado ou dormindo", 0, 4),
            ("m", 1, 0, "estado = aguardando_confirmacao", None, "ln"),
            ("self", 1, "notificação do macOS", "osascript; confirma-se com publicar <slug> --sim"),
            ("fim",),
            ("fim",),
        ], W=1180)
    D_["meta-comentario-direct"] = sequencia(
        "meta-comentario-direct",
        "Sequência do comentário até o direct: a cada 120 segundos o script lê os posts com menos de 7 dias, busca "
        "comentários em ordered_comments e comments, filtra a palavra-chave, manda o direct com o link do PDF pela "
        "Página e, só se o direct saiu, responde em público.",
        [("pasta", "07-publicados/"), ("launchd", "uk.korvu.comentarios"), ("responder_comentarios.py", "respostas.yaml"),
         ("Instagram", "mídia e comentário"), ("Página", "/{page-id}/messages")],
        [
            ("m", 1, 2, "a cada 120 s", None, "acc"),
            ("m", 2, 0, "lê */dm-material.json", "só posts publicados há menos de janela_dias (7)", "ln"),
            ("quadro", "para cada post", 0, 4),
            ("m", 2, 3, "GET /{media-id}/ordered_comments", "e GET /{media-id}/comments · 50 por página, até 40 páginas", "acc"),
            ("m", 3, 2, "id, text, timestamp, username, from, replies", "as duas listas juntadas sem repetir", "ret"),
            ("self", 2, "filtra", ["palavra sem acento, maiúscula e pontuação;", "plural S/ES; ignora a própria conta, quem", "já tem resposta manual e quem já recebeu"]),
            ("m", 2, 4, "POST /{page-id}/messages", "recipient={comment_id} · texto com {usuario}, {material}, {link} · token da Página", "acc"),
            ("quadro", "só se o direct saiu", 2, 4),
            ("m", 2, 3, "POST /{comment-id}/replies", "uma das 5 frases sorteadas", "acc"),
            ("fim",),
            ("m", 2, 0, "_controle/comentarios/estado.json", "quem recebeu, quando, tentativas", "ln"),
            ("fim",),
            ("nota", 0, 4, ["Limites (respostas.yaml): 25 envios por passagem, 150 por hora, 4 s entre envios; ativo: false desliga tudo.",
                            "“Esta pessoa não pode receber” (2018001, 2018108, 2018278, 2534014, 2534022, 1545041, 551): desiste só dela.",
                            "Configuração (3, 10, 102, 190, 200): para a passagem sem descartar ninguém e avisa no máximo 1× por hora."], "soft"),
        ], W=1200)
    D_["meta-metricas"] = sequencia(
        "meta-metricas",
        "Sequência das métricas: todo dia às 09:30 o metricas.py lê os posts com pelo menos 5 dias, pede os dados e "
        "insights do Instagram e os video_insights do Facebook, calcula o percentual médio assistido e grava "
        "metricas.json e _controle/metricas.md; depois o acertos.py avisa quando um vídeo vai muito acima da mediana.",
        [("launchd", "uk.korvu.metricas"), ("metricas.py", "DIAS_PADRAO = 5"), ("Instagram", "/{media}"),
         ("Facebook", "/{video}"), ("disco", "07-publicados/ · _controle/")],
        [
            ("m", 0, 1, "todo dia às 09:30", None, "acc"),
            ("m", 1, 4, "posts com ≥ 5 dias ainda sem leitura completa", None, "ln"),
            ("m", 1, 2, "GET /{media}?fields=like_count,comments_count,…", "permalink, timestamp, media_product_type, is_shared_to_feed; trial_params", "acc"),
            ("m", 1, 2, "GET /{media}/insights", "views, reach, likes, comments, saved, shares, total_interactions, ig_reels_avg_watch_time, follows, profile_visits…", "acc"),
            ("m", 1, 3, "GET /{video}/video_insights", "blue_reels_play_count, fb_reels_total_plays, post_video_avg_time_watched… “pede-se tudo e fica o que responder”", "acc"),
            ("self", 1, "% médio assistido = tempo médio / duração", "taxas sobre o alcance; junta os comentários da palavra"),
            ("m", 1, 4, "<slug>/metricas.json + _controle/metricas.md", "saída 3 = permissão de insights em falta", "ln"),
            ("m", 1, 4, "acertos.py → _controle/acertos.json", "vídeo muito acima da mediana → aviso para /multiplicar", "ln"),
            ("nota", 0, 4, ["A API não dá a curva de retenção segundo a segundo. Carrossel ainda não é lido (“o metricas.py só lê Reel por enquanto”).",
                            "Depois: analista-de-metricas → _controle/aprendizados.md → roteirista."], "soft"),
        ], W=1180)
    D_["jobs-24h"] = jobs24(dados["jobs_locais"])
    D_["sem-servidor"] = sem_servidor()
    D_["edicao"] = edicao(dados["edicao"])
    D_["pipeline"] = pipeline(dados["pipeline"])
    D_["gauntlet"] = gauntlet()
    return D_
