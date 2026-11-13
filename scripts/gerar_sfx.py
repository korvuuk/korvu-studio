"""Gera a biblioteca de efeitos sonoros (sound design) da Korvu na ElevenLabs Sound Effects.

O catálogo (`00-marca/som/sfx.json`) diz o nome, a descrição em inglês (o modelo entende melhor) e a duração de
cada efeito; este script gera o que ainda não existe em `remotion/public/_marca/sfx/<nome>.mp3`, onde o Remotion
o acha com `staticFile("_marca/sfx/<nome>.mp3")`. Regras do som: `00-marca/som/sound-design.md`.

    uv run python scripts/gerar_sfx.py            # gera os que faltam
    uv run python scripts/gerar_sfx.py --refazer whoosh-entra pop   # gera de novo só estes
    uv run python scripts/gerar_sfx.py --listar
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "00-marca/som/sfx.json"
SAIDA = RAIZ / "remotion/public/_marca/sfx"
API = "https://api.elevenlabs.io/v1/sound-generation"
PICO_DB = -3.0  # todo efeito sai com o mesmo pico; o volume relativo se decide no Remotion


def env() -> None:
    try:
        from dotenv import load_dotenv
        if (RAIZ / ".env").exists():          # nunca imprimir o .env
            load_dotenv(RAIZ / ".env", override=False)
    except ImportError:
        pass


def gerar(chave: str, efeito: dict) -> bytes:
    corpo = json.dumps({
        "text": efeito["descricao"],
        "duration_seconds": efeito["duracao"],
        "prompt_influence": efeito.get("influencia", 0.6),
    }).encode()
    req = urllib.request.Request(f"{API}?output_format=mp3_44100_192", data=corpo, method="POST",
                                 headers={"xi-api-key": chave, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def normalizar(arq: Path) -> None:
    """Leva o pico do efeito a PICO_DB (a ElevenLabs devolve níveis muito diferentes entre efeitos)."""
    ffmpeg = os.environ.get("FFMPEG_BIN") or "ffmpeg"
    med = subprocess.run([ffmpeg, "-hide_banner", "-i", str(arq), "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"max_volume: (-?[0-9.]+) dB", med)
    if not m:
        return
    ganho = PICO_DB - float(m.group(1))
    tmp = arq.with_suffix(".tmp.mp3")
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(arq), "-af", f"volume={ganho:.2f}dB",
                    "-c:a", "libmp3lame", "-b:a", "192k", str(tmp)], check=True)
    tmp.replace(arq)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refazer", nargs="*", default=[], help="nomes a gerar de novo")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--normalizar", action="store_true", help="só iguala o pico dos que já existem")
    a = ap.parse_args()

    efeitos = json.loads(CATALOGO.read_text())["efeitos"]
    if a.listar:
        for e in efeitos:
            ok = "✓" if (SAIDA / f"{e['nome']}.mp3").exists() else "·"
            print(f"{ok} {e['nome']:<18} {e['duracao']:>4}s  {e['uso']}")
        return 0

    env()
    if a.normalizar:
        for e in efeitos:
            if (SAIDA / f"{e['nome']}.mp3").exists():
                normalizar(SAIDA / f"{e['nome']}.mp3")
        return 0
    chave = os.environ.get("ELEVENLABS_API_KEY")
    if not chave:
        print("ELEVENLABS_API_KEY ausente no ambiente", file=sys.stderr)
        return 1
    SAIDA.mkdir(parents=True, exist_ok=True)
    falhas = 0
    for e in efeitos:
        destino = SAIDA / f"{e['nome']}.mp3"
        if destino.exists() and e["nome"] not in a.refazer:
            continue
        try:
            destino.write_bytes(gerar(chave, e))
            normalizar(destino)
            print(f"gerado {destino.relative_to(RAIZ)}")
        except urllib.error.HTTPError as err:
            falhas += 1
            print(f"FALHOU {e['nome']}: HTTP {err.code} {err.read()[:300]!r}", file=sys.stderr)
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
