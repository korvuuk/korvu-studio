"""Ponte com o DaVinci Resolve (10/11) — a timeline do corte num arquivo FCPXML que o Resolve importa, e a volta.

O agente continua sendo a fonte do corte (edl.json). Este script só TRADUZ:

  exportar  edl.json -> edicao/resolve/<slug>.fcpxml
            V1  = o autor: uma peça por trecho ([in, out] − cortes_internos), apontando para o intermediário
                  edicao/fontes/<fonte>.mp4 (V-Log, 1440x2560) com o zoom de cada peça (escala + posição no rosto)
                  e um marcador por linha do roteiro (L01, L02…) — com alças: dá para esticar cada corte.
            V2  = cenas extras (vídeo/print) no lugar e no layout (split em cima / full / card);
                  animação Remotion sem arquivo vira marcador "E07 animação".
            A   = o som da própria fonte (vem preso ao vídeo, corta junto) + a música escolhida, baixa.
            Legendas, títulos e gráficos do Remotion NÃO vão: são refeitos depois, a partir do corte novo.
  importar  o FCPXML que o autor exportou do Resolve (File > Export > Timeline > FCPXML) -> edl.json
            Lê as peças da V1 (fonte, início e fim na fonte), devolve cada uma ao segmento de onde veio
            (maior sobreposição na mesma fonte), refaz in/out/cortes_internos e o zoom (escala) que ele mexeu;
            peça nova vira segmento "manual" da linha vizinha. Faz cópia (edl.antes-resolve.json) e roda
            `edl.py --recalcular`. Mudança de tempo das cenas extras só é AVISADA (elas seguem as linhas).

Uso:
  uv run python .claude/skills/corte-por-roteiro/scripts/resolve.py exportar videos/<slug>
  uv run python .claude/skills/corte-por-roteiro/scripts/resolve.py importar videos/<slug> [arquivo.fcpxml] [--simular]
  uv run python .claude/skills/corte-por-roteiro/scripts/resolve.py luts      # instala os LUTs no Resolve
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.sax.saxutils import quoteattr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ALTURA, FFMPEG, FPS, LARGURA, ROOT, ZOOM_MAX, duracao, edicao, eh_log,  # noqa: E402
                    escrever_json, ffprobe_json, filtro_lut_camera, janela_zoom, ler_json, perfil_da_fonte,
                    resolver_video_dir, tipo_da_fonte, wav48k_path, zoom_das_pecas)

EXT_IMG = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}
LUT_DIR_RESOLVE = Path("/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/Korvu")
FR = Fraction(1, int(round(FPS))) if float(FPS).is_integer() else Fraction(FPS).limit_denominator(1001) ** -1
# split = extra deitado em cima, caixa 1080x608 em y 0 (00-marca/layouts.md); card = 1000x330 com o pé em y 1250
SPLIT_CAIXA_H, CARD_W, CARD_PE = 608, 1000, 1250


def log(m: str) -> None:
    print(m, flush=True)


# ---------------------------------------------------------------- tempo
def frames(t: float) -> int:
    return int(round(float(t) / float(FR)))


def ft(n: int) -> str:
    """n frames -> tempo racional FCPXML ("123/25s")."""
    v = FR * n
    return f"{v.numerator}/{v.denominator}s" if v.denominator != 1 else f"{v.numerator}s"


def parse_t(s: str | None) -> Fraction:
    if not s:
        return Fraction(0)
    s = s.strip().rstrip("s")
    if "/" in s:
        a, b = s.split("/", 1)
        return Fraction(int(a), int(b))
    return Fraction(s)


# ---------------------------------------------------------------- EDL -> peças
def pecas_do_segmento(s: dict) -> list[tuple[float, float]]:
    a, b = float(s["in"]), float(s["out"])
    out, cur = [], a
    for c0, c1 in sorted((float(x), float(y)) for x, y in (s.get("cortes_internos") or [])):
        if c0 > cur:
            out.append((cur, min(c0, b)))
        cur = max(cur, c1)
    if cur < b:
        out.append((cur, b))
    return [(x, y) for x, y in out if y - x > 1e-6]


def dims(p: Path) -> tuple[int, int]:
    for s in ffprobe_json(p).get("streams", []):
        if s.get("codec_type") == "video":
            w, h = int(s["width"]), int(s["height"])
            rot = 0
            for sd in s.get("side_data_list") or []:
                rot = int(sd.get("rotation") or rot)
            return (h, w) if abs(rot) % 180 == 90 else (w, h)
    return LARGURA, ALTURA


def transform_zoom(sw: int, sh: int, escala: float, origem) -> tuple[float, tuple[float, float]]:
    """Mesmo recorte do render_corte (janela_zoom) em termos de Resolve: escala sobre o quadro já 'fit' e posição
    em % da altura do quadro (unidade do FCPXML; y para cima)."""
    cw, ch, x, y = janela_zoom(sw, sh, escala, origem, LARGURA, ALTURA)
    s = sw / cw                                   # 1440 'fit' em 1080 -> escala relativa ao fit
    cx, cy = (x + cw / 2) / sw, (y + ch / 2) / sh  # centro do recorte, normalizado
    dx = (0.5 - cx) * s * LARGURA
    dy = (cy - 0.5) * s * ALTURA                  # y do FCPXML cresce para cima
    return s, (dx / ALTURA * 100, dy / ALTURA * 100)


# ---------------------------------------------------------------- mídia de edição (Resolve grátis)
def midia_de_edicao(vd: Path, fonte: str, arq: Path, info: dict | None) -> Path:
    """O Resolve GRÁTIS não abre H.264 10-bit 4:2:2 (os intermediários de edicao/fontes/) — diz 'File not found'
    (medido no 21.2, 10/11). Cópia de edição: mesma duração e mesmos quadros, 1080x1920 H.264 8-bit 4:2:0,
    GOP de 1 s (corre bem na timeline), LUT de entrada aplicada SÓ para ver (V-Log fica com cor normal),
    som = o master sem perdas do ingest (wav48k) em AAC. Refeita só quando a fonte é mais nova."""
    destino = vd / "edicao" / "resolve" / "midia" / f"{fonte}.mp4"
    if destino.exists() and destino.stat().st_mtime >= arq.stat().st_mtime:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    vf = []
    if eh_log(perfil_da_fonte(fonte, info)):
        lut = filtro_lut_camera()
        if lut:
            vf.append(lut)
    vf.append(f"scale={LARGURA}:{ALTURA}:flags=lanczos,format=yuv420p")
    wav = wav48k_path(vd, fonte)
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", str(arq)]
    if wav.exists():
        cmd += ["-i", str(wav), "-map", "0:v:0", "-map", "1:a:0"]
    else:
        cmd += ["-map", "0:v:0", "-map", "0:a:0?"]
    cmd += ["-vf", ",".join(vf), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-profile:v", "high",
            "-g", str(int(round(FPS))), "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
            "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest", "-movflags", "+faststart",
            str(destino.with_suffix(".tmp.mp4"))]
    log(f"   mídia de edição {fonte} …")
    subprocess.run(cmd, check=True)
    destino.with_suffix(".tmp.mp4").replace(destino)
    return destino


# ---------------------------------------------------------------- exportar
class Recursos:
    def __init__(self, vd: Path):
        self.vd, self.assets, self.formatos, self._ids = vd, {}, {}, 0

    def _id(self, p: str) -> str:
        self._ids += 1
        return f"{p}{self._ids}"

    def formato(self, w: int, h: int, still: bool = False) -> str:
        k = (w, h, still)
        if k not in self.formatos:
            self.formatos[k] = self._id("rf")
        return self.formatos[k]

    def asset(self, p: Path, *, video: bool = True) -> tuple[str, dict]:
        p = p.resolve()
        if p in self.assets:
            return self.assets[p]["id"], self.assets[p]
        still = p.suffix.lower() in EXT_IMG
        info = {"id": self._id("a"), "src": p.as_uri(), "nome": p.stem, "still": still, "video": video}
        if still:
            info["w"], info["h"], info["dur"], info["audio"] = *dims(p), 0, False
        else:
            pr = ffprobe_json(p)
            tipos = {s.get("codec_type") for s in pr.get("streams", [])}
            info["audio"] = "audio" in tipos
            info["video"] = video and "video" in tipos
            info["w"], info["h"] = dims(p) if info["video"] else (0, 0)
            info["dur"] = frames(duracao(p))
        if info["video"]:
            info["fmt"] = self.formato(info["w"], info["h"], still)
        self.assets[p] = info
        return info["id"], info

    def xml(self, seq_fmt: str) -> str:
        L = [f'    <format id="{seq_fmt}" name="Korvu 1080x1920p{int(FPS)}" frameDuration="{ft(1)}" '
             f'width="{LARGURA}" height="{ALTURA}" colorSpace="1-1-1 (Rec. 709)"/>']
        for (w, h, still), fid in self.formatos.items():
            fd = "" if still else f' frameDuration="{ft(1)}"'
            L.append(f'    <format id="{fid}"{fd} width="{w}" height="{h}"/>')
        for a in self.assets.values():
            attrs = [f'id="{a["id"]}"', f'name={quoteattr(a["nome"])}', 'start="0s"',
                     f'duration="{ft(a["dur"])}"', f'hasVideo="{int(a["video"])}"', f'hasAudio="{int(a["audio"])}"']
            if a["video"]:
                attrs.append(f'format="{a["fmt"]}"')
            if a["audio"]:
                attrs += ['audioSources="1"', 'audioChannels="2"', 'audioRate="48000"']
            L.append(f'    <asset {" ".join(attrs)}>\n'
                     f'      <media-rep kind="original-media" src={quoteattr(a["src"])}/>\n    </asset>')
        return "\n".join(L)


def arquivo_do_extra(vd: Path, ov: dict) -> Path | None:
    if ov.get("arquivo"):
        p = vd / ov["arquivo"]
        if p.exists():
            return p
    ex = ov.get("extra") or ""
    for d in (vd / "edicao" / "extras", vd / "animacoes" / ex, vd / "brutos" / "extras"):
        if d.is_dir():
            for p in sorted(d.iterdir()):
                if p.stem.startswith(ex) and p.suffix.lower() in EXT_IMG | {".mp4", ".mov", ".m4v"}:
                    return p
    return None


def layout_extra(modo: str, w: int, h: int) -> str:
    """adjust-transform do extra no quadro 1080x1920 (o Resolve encaixa 'fit' antes)."""
    if modo == "split" or (modo != "card" and w / max(1, h) >= 1.2 and modo != "full"):
        fit_h = LARGURA * h / w                       # largura cheia
        sc = SPLIT_CAIXA_H / fit_h if fit_h > SPLIT_CAIXA_H else 1.0
        y_centro = SPLIT_CAIXA_H / 2
        return f'<adjust-transform position="0 {(ALTURA / 2 - y_centro) / ALTURA * 100:.4f}" scale="{sc:.4f} {sc:.4f}"/>'
    if modo == "card":
        fit_w = min(LARGURA, ALTURA * w / h)
        sc = CARD_W / fit_w
        y_centro = CARD_PE - (CARD_W * h / w) / 2
        return f'<adjust-transform position="0 {(ALTURA / 2 - y_centro) / ALTURA * 100:.4f}" scale="{sc:.4f} {sc:.4f}"/>'
    # full = cover
    fit_esc = min(LARGURA / w, ALTURA / h)
    sc = max(LARGURA / w, ALTURA / h) / fit_esc
    return f'<adjust-transform scale="{sc:.4f} {sc:.4f}"/>'


def exportar(vd: Path, saida: Path | None = None, midia: bool = True) -> Path:
    ed = edicao(vd)
    edl = ler_json(ed / "edl.json")
    slug = edl.get("slug") or vd.name
    R = Recursos(vd)
    seq_fmt = "r0"

    # V1 — as peças do autor, na ordem da timeline
    pecas, t = [], 0
    for s in edl["segmentos"]:
        fonte = s["fonte"]
        arq = vd / (edl.get("fontes", {}).get(fonte) or f"edicao/fontes/{fonte}.mp4")
        if not arq.exists():
            sys.exit(f"[ERRO] intermediário não encontrado: {arq} (o FCPXML precisa das fontes)")
        if midia:
            arq = midia_de_edicao(vd, fonte, arq, ler_json(vd / "edicao" / "fontes.json", padrao={})
                                  .get("fontes", {}).get(fonte))
        aid, a = R.asset(arq)
        ps = pecas_do_segmento(s)
        zs = zoom_das_pecas(s, len(ps))
        camera = tipo_da_fonte(fonte) != "tela" and s.get("zoom_origem") is not None
        for k, ((p0, p1), z) in enumerate(zip(ps, zs)):
            f0, f1 = frames(p0), frames(p1)
            if f1 <= f0:
                continue
            pecas.append({"seg": s, "k": k, "aid": aid, "a": a, "start": f0, "dur": f1 - f0, "offset": t,
                          "zoom": z if camera else 1.0, "origem": s.get("zoom_origem")})
            t += f1 - f0
    total = t

    # V2 — extras; textos e animações sem arquivo viram marcadores
    conectados, marcadores = [], []
    for ov in edl.get("overlays", []):
        o0, o1 = frames(ov.get("saida_inicio", 0)), frames(ov.get("saida_fim", 0))
        if o1 <= o0:
            continue
        if ov.get("tipo") == "texto":
            marcadores.append((o0, f'TEXTO: {ov.get("texto") or ""}'))
            continue
        arq = arquivo_do_extra(vd, ov)
        if not arq:
            marcadores.append((o0, f'{ov.get("extra")} {ov.get("extra_tipo") or "extra"} (sem arquivo)'))
            continue
        aid, a = R.asset(arq)
        if not a["video"]:
            continue
        ini = 0 if a["still"] else frames(ov.get("in") or 0)
        conectados.append({"aid": aid, "a": a, "offset": o0, "dur": o1 - o0, "start": ini, "lane": 1,
                           "nome": f'{ov.get("extra")} · {ov.get("modo") or "split"} · {"/".join(ov.get("linhas") or [])}',
                           "transform": layout_extra(ov.get("modo") or "split", a["w"], a["h"]),
                           "mudo": not ov.get("som")})

    # música escolhida (fica baixa: −23 dB sugerido, ajustável no Resolve)
    mj = ler_json(vd / "musica" / "musica.json", padrao={})
    esc = next((o for o in mj.get("opcoes", []) if o.get("n") == mj.get("escolhida")), None)
    if esc and (ROOT / esc["arquivo"]).exists():
        aid, a = R.asset(ROOT / esc["arquivo"], video=False)
        conectados.append({"aid": aid, "a": a, "offset": 0, "dur": min(total, a["dur"]), "start": 0, "lane": -1,
                           "nome": f'música opção {esc["n"]}', "volume": mj.get("volume_sugerido_db", -23)})

    # pendura cada conectado na peça da V1 que cobre o seu início (offset do filho = tempo da peça-mãe)
    def mae(off: int) -> dict:
        for p in pecas:
            if p["offset"] <= off < p["offset"] + p["dur"]:
                return p
        return pecas[-1]

    filhos: dict[int, list[str]] = {}
    for c in conectados:
        p = mae(c["offset"])
        off_local = p["start"] + (c["offset"] - p["offset"])
        a = c["a"]
        extra = ""
        if c.get("transform"):
            extra += f'\n          {c["transform"]}'
        if c.get("volume") is not None:
            extra += f'\n          <adjust-volume amount="{c["volume"]}dB"/>'
        src = ' srcEnable="video"' if (c.get("mudo") and a["audio"] and a["video"]) else ""
        start = f' start="{ft(c["start"])}"' if c["start"] else ""
        filhos.setdefault(id(p), []).append(
            f'        <asset-clip ref="{c["aid"]}" lane="{c["lane"]}" offset="{ft(off_local)}" '
            f'name={quoteattr(c["nome"])}{start} duration="{ft(c["dur"])}"{src}'
            + (f' format="{a["fmt"]}"' if a["video"] else "") + f'>{extra}\n        </asset-clip>')

    for m0, txt in marcadores:
        p = mae(m0)
        filhos.setdefault(id(p), []).append(
            f'        <marker start="{ft(p["start"] + m0 - p["offset"])}" duration="{ft(1)}" value={quoteattr(txt)}/>')

    # spine
    corpo, linha_ant = [], None
    for p in pecas:
        s, a = p["seg"], p["a"]
        nome = f'{s["linha"]} · {s.get("take") or ""} · p{p["k"] + 1}'
        dentro = []
        if p["zoom"] and p["zoom"] > 1.0001:
            sc, (px, py) = transform_zoom(a["w"], a["h"], p["zoom"], p["origem"])
            dentro.append(f'        <adjust-transform position="{px:.4f} {py:.4f}" scale="{sc:.4f} {sc:.4f}"/>')
        if s["linha"] != linha_ant and p["k"] == 0:
            leg = (s.get("legenda_texto") or "")[:80]
            dentro.insert(0, f'        <marker start="{ft(p["start"])}" duration="{ft(1)}" '
                             f'value={quoteattr(s["linha"] + (" — " + leg if leg else ""))}/>')
        linha_ant = s["linha"]
        dentro += filhos.get(id(p), [])
        corpo.append(f'      <asset-clip ref="{p["aid"]}" offset="{ft(p["offset"])}" name={quoteattr(nome)} '
                     f'start="{ft(p["start"])}" duration="{ft(p["dur"])}" format="{a["fmt"]}" tcFormat="NDF"'
                     f' audioRole="dialogue">\n' + "\n".join(dentro) + "\n      </asset-clip>")

    nome_proj = f'{slug} · EDL v{edl.get("versao", "?")}'
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<!-- Gerado por corte-por-roteiro/scripts/resolve.py a partir de edicao/edl.json v{edl.get("versao")}.
     Imagem em V-Log: aplique o LUT Korvu/entrada-camera só para VER. Legendas e gráficos não estão aqui. -->
<fcpxml version="1.10">
  <resources>
{R.xml(seq_fmt)}
  </resources>
  <library>
    <event name={quoteattr("Korvu — " + slug)}>
      <project name={quoteattr(nome_proj)}>
        <sequence format="{seq_fmt}" duration="{ft(total)}" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">
          <spine>
{chr(10).join(corpo)}
          </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>
'''
    ET.fromstring(xml.split("\n", 2)[2])           # XML bem formado (falha alto se não)
    saida = saida or ed / "resolve" / f"{slug}.fcpxml"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(xml, encoding="utf-8")
    log(f"[resolve] {len(pecas)} peças na V1 · {len(conectados)} clipes conectados · {len(marcadores)} marcadores "
        f"· {total / float(1 / FR):.2f}s -> {saida.relative_to(vd)}")
    return saida


# ---------------------------------------------------------------- importar
def mesmo(novo: float, antigo) -> float:
    return antigo if abs(float(novo) - float(antigo)) <= float(FR) / 2 + 1e-6 else novo


def ler_fcpxml(p: Path) -> tuple[list[dict], list[dict]]:
    """-> (peças da V1 em ordem de timeline, clipes conectados) com fonte = nome do arquivo sem extensão."""
    root = ET.parse(p).getroot()
    srcs = {}
    for a in root.iter("asset"):
        mr = a.find("media-rep")
        src = mr.get("src") if mr is not None else a.get("src")
        if src:
            srcs[a.get("id")] = Path(unquote(urlparse(src).path))
    seq = next(root.iter("sequence"))
    spine = seq.find("spine")
    v1, outros = [], []

    def clipe(el, off_tl: Fraction, lane: int | None):
        ref = el.get("ref")
        if ref is None:                                # <clip> do Resolve: o vídeo vem num filho <video ref>
            v = el.find("video") or el.find("asset-clip")
            ref = v.get("ref") if v is not None else None
        start, dur = parse_t(el.get("start")), parse_t(el.get("duration"))
        sc = None
        tr = el.find("adjust-transform")
        if tr is not None and tr.get("scale"):
            sc = float(tr.get("scale").split()[0])
        return {"arquivo": srcs.get(ref), "start": start, "dur": dur, "tl": off_tl, "lane": lane,
                "escala": sc, "nome": el.get("name")}

    for el in list(spine):
        off = parse_t(el.get("offset"))
        if el.tag in ("gap", "transition"):
            pass
        else:
            v1.append(clipe(el, off, None))
        base_start = parse_t(el.get("start"))
        for ch in el:
            if ch.get("lane") is not None and ch.tag in ("asset-clip", "clip", "video", "audio"):
                o = clipe(ch, off + parse_t(ch.get("offset")) - base_start, int(ch.get("lane")))
                outros.append(o)
    return [c for c in v1 if c["arquivo"]], outros


def importar(vd: Path, arq: Path | None, simular: bool = False) -> None:
    ed = edicao(vd)
    edl = ler_json(ed / "edl.json")
    if arq is None:
        cands = sorted((ed / "resolve").glob("*.fcpxml"), key=lambda q: q.stat().st_mtime, reverse=True)
        cands = [c for c in cands if c.name != f'{edl.get("slug") or vd.name}.fcpxml']
        if not cands:
            sys.exit("[ERRO] nenhum FCPXML exportado do Resolve em edicao/resolve/ (salve lá com outro nome)")
        arq = cands[0]
    log(f"[resolve] lendo {arq}")
    v1, outros = ler_fcpxml(arq)
    fontes_por_stem = {Path(v).stem: k for k, v in (edl.get("fontes") or {}).items()}
    segs = edl["segmentos"]
    fps = 1 / float(FR)

    pecas = []
    for c in v1:
        fonte = fontes_por_stem.get(c["arquivo"].stem)
        if fonte is None:
            log(f"   [AVISO] V1 com arquivo que não é fonte do corte ({c['arquivo'].name}) — ignorado")
            continue
        a, b = float(c["start"]), float(c["start"] + c["dur"])
        melhor, sobre = None, 0.0
        for i, s in enumerate(segs):
            if s["fonte"] != fonte:
                continue
            ov = min(b, float(s["out"])) - max(a, float(s["in"]))
            if ov > sobre:
                melhor, sobre = i, ov
        pecas.append({"fonte": fonte, "in": round(a, 4), "out": round(b, 4), "seg": melhor, "escala": c["escala"]})

    # agrupa peças seguidas do mesmo segmento (em ordem crescente na fonte) num segmento
    grupos: list[dict] = []
    usados: set[int] = set()
    for p in pecas:
        g = grupos[-1] if grupos else None
        if g and g["seg"] == p["seg"] and p["seg"] is not None and g["fonte"] == p["fonte"] and p["in"] >= g["pecas"][-1]["out"] - 1e-3:
            g["pecas"].append(p)
        else:
            grupos.append({"seg": p["seg"], "fonte": p["fonte"], "pecas": [p]})

    novos, linha_ant = [], segs[0]["linha"] if segs else "L01"
    for g in grupos:
        ps = g["pecas"]
        orig = segs[g["seg"]] if g["seg"] is not None else None
        seg = dict(orig) if orig and g["seg"] not in usados else {
            "linha": (orig or {}).get("linha") or linha_ant, "take": "manual", "fonte": g["fonte"],
            "layout": (orig or {}).get("layout", "full"), "zoom": None,
            "zoom_origem": (orig or {}).get("zoom_origem")}
        seg["_orig"] = orig if (orig and g["seg"] not in usados) else None
        if g["seg"] is not None:
            usados.add(g["seg"])
        seg["fonte"] = g["fonte"]
        seg["in"], seg["out"] = ps[0]["in"], ps[-1]["out"]
        seg["cortes_internos"] = [[x["out"], y["in"]] for x, y in zip(ps, ps[1:]) if y["in"] - x["out"] > 1e-3]
        if seg["_orig"]:                                 # dentro de meio quadro = o mesmo ponto: guarda o valor exato
            o = seg["_orig"]
            seg["in"], seg["out"] = mesmo(seg["in"], o["in"]), mesmo(seg["out"], o["out"])
            oc = o.get("cortes_internos") or []
            if len(oc) == len(seg["cortes_internos"]):
                seg["cortes_internos"] = [[mesmo(a, c), mesmo(b, d)] for (a, b), (c, d) in zip(seg["cortes_internos"], oc)]
        # zoom: a escala que está no Resolve é relativa ao 'fit'; com origem mantida, zoom = escala
        zs = [min(ZOOM_MAX, max(1.0, p["escala"] or 1.0)) for p in ps]
        antigos = zoom_das_pecas(orig, len(pecas_do_segmento(orig))) if orig else None
        if antigos is not None and len(antigos) == len(zs) and all(abs(x - y) < 0.01 for x, y in zip(antigos, zs)):
            pass                                         # nada mudou no enquadramento
        else:
            seg["zoom_pecas"] = [round(z, 3) for z in zs]
        linha_ant = seg["linha"]
        novos.append(seg)

    # relatório
    def resumo(s):
        return f'{s["linha"]:<5} {s["fonte"]} {float(s["in"]):8.2f}–{float(s["out"]):8.2f}  cortes {len(s.get("cortes_internos") or [])}'
    mud = 0
    for i, s in enumerate(segs):
        if i not in usados:
            log(f"   – removido   {resumo(s)}")
            mud += 1
    for s in novos:
        o = s.pop("_orig", None)
        if o is None:
            log(f"   + manual     {resumo(s)}")
            mud += 1
        elif (abs(float(o["in"]) - float(s["in"])) > 1e-3 or abs(float(o["out"]) - float(s["out"])) > 1e-3
              or (o.get("cortes_internos") or []) != s["cortes_internos"]):
            d0, d1 = (float(s["in"]) - float(o["in"])) * fps, (float(s["out"]) - float(o["out"])) * fps
            log(f"   ~ ajustado   {resumo(s)}   (in {d0:+.0f} quadros, out {d1:+.0f} quadros)")
            mud += 1
    # extras: só aviso
    for c in outros:
        if c["lane"] and c["lane"] > 0 and c["arquivo"]:
            ov = next((o for o in edl.get("overlays", []) if o.get("arquivo") and Path(o["arquivo"]).stem == c["arquivo"].stem), None)
            if ov and abs(float(c["tl"]) - float(ov["saida_inicio"])) > 0.08:
                log(f"   [AVISO] {ov.get('extra')} movido no Resolve ({float(ov['saida_inicio']):.2f}s -> {float(c['tl']):.2f}s): "
                    "extras seguem as linhas do roteiro — o tempo dele sai do corte novo, não deste arrasto")

    if simular:
        log(f"[resolve] SIMULAÇÃO: {len(novos)} segmentos, {mud} mudanças — nada gravado")
        return
    escrever_json(ed / "edl.antes-resolve.json", edl)
    edl["segmentos"] = novos
    escrever_json(ed / "edl.json", edl)
    log(f"[resolve] {len(novos)} segmentos ({mud} mudanças) gravados; cópia em edicao/edl.antes-resolve.json")
    r = subprocess.run([sys.executable, str(Path(__file__).with_name("edl.py")), str(vd), "--recalcular",
                        "--sem-preview"])
    if r.returncode != 0:
        sys.exit("[ERRO] edl.py --recalcular falhou — o edl.json anterior está em edicao/edl.antes-resolve.json")
    log("[resolve] pronto. Próximo: render_corte.py (ou /renderizar) — legendas e gráficos saem do corte novo.")


# ---------------------------------------------------------------- LUTs
def instalar_luts() -> None:
    LUT_DIR_RESOLVE.mkdir(parents=True, exist_ok=True)
    luts = ROOT / "00-marca" / "cor" / "luts"
    looks = sorted(luts.glob("korvu-look-v*.cube"), key=lambda p: int(p.stem.rsplit("v", 1)[1]))
    for p in [luts / "entrada-camera.cube"] + looks[-1:]:
        shutil.copy2(p, LUT_DIR_RESOLVE / p.name)
        log(f"[resolve] LUT {p.name} -> {LUT_DIR_RESOLVE}")
    log("[resolve] no Resolve: Project Settings > Color Management > Update Lists (ou reabrir o Resolve).")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("exportar")
    e.add_argument("video_dir")
    e.add_argument("--saida")
    e.add_argument("--sem-midia", action="store_true",
                   help="aponta direto para edicao/fontes (só Resolve Studio abre o H.264 10-bit 4:2:2)")
    i = sub.add_parser("importar")
    i.add_argument("video_dir")
    i.add_argument("fcpxml", nargs="?")
    i.add_argument("--simular", action="store_true", help="só mostra o que mudaria, não grava")
    sub.add_parser("luts")
    a = ap.parse_args()
    if a.cmd == "exportar":
        exportar(resolver_video_dir(a.video_dir), Path(a.saida) if a.saida else None, not a.sem_midia)
    elif a.cmd == "importar":
        importar(resolver_video_dir(a.video_dir), Path(a.fcpxml).resolve() if a.fcpxml else None, a.simular)
    else:
        instalar_luts()


if __name__ == "__main__":
    main()
