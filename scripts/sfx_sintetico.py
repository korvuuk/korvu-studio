"""Efeitos sonoros SINTETIZADOS (sem API) — reserva da biblioteca de `00-marca/som/sfx.json`.

Gera os mesmos nomes que o `gerar_sfx.py` (ElevenLabs), em WAV, só para os que ainda não existem. Serve quando a
API está fora (ex.: chave inválida em 05/11) e para modelos/testes. A versão da ElevenLabs, quando gerada, tem
prioridade: o Remotion procura `<nome>.mp3` e cai para `<nome>.wav`.

    uv run python scripts/sfx_sintetico.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "remotion/public/_marca/sfx"
SR = 48000
rng = np.random.default_rng(7)


def t(d: float) -> np.ndarray:
    return np.arange(int(SR * d)) / SR


def env_ad(n: int, ataque: float, curva: float = 3.0) -> np.ndarray:
    a = max(1, int(n * ataque))
    return np.concatenate([np.linspace(0, 1, a) ** 2, np.linspace(1, 0, n - a) ** curva])


def banda_varrida(ruido: np.ndarray, f0: float, f1: float, q: float = 0.6, passos: int = 60) -> np.ndarray:
    """Ruído passando por um passa-banda que desliza de f0 a f1 (o 'ar' do whoosh)."""
    out = np.zeros_like(ruido)
    bloco = len(ruido) // passos + 1
    for i in range(passos):
        fc = f0 * (f1 / f0) ** (i / (passos - 1))
        lo, hi = fc * (1 - q / 2), min(fc * (1 + q / 2), SR / 2 - 100)
        sos = butter(2, [lo, hi], btype="band", fs=SR, output="sos")
        seg = slice(max(0, i * bloco - 2000), min(len(ruido), (i + 1) * bloco))
        filt = sosfilt(sos, ruido[seg])
        janela = slice(i * bloco, min(len(ruido), (i + 1) * bloco))
        out[janela] = filt[-(janela.stop - janela.start):] if janela.stop > janela.start else out[janela]
    return out


def estereo(x: np.ndarray, pan_de: float = 0.0, pan_ate: float = 0.0) -> np.ndarray:
    p = np.linspace(pan_de, pan_ate, len(x))
    return np.stack([x * np.sqrt((1 - p) / 2), x * np.sqrt((1 + p) / 2)], axis=1)


def norm(x: np.ndarray, pico_db: float = -3.0) -> np.ndarray:
    return x / (np.max(np.abs(x)) + 1e-9) * 10 ** (pico_db / 20)


def whoosh(d: float, sobe: bool) -> np.ndarray:
    n = int(SR * d)
    r = rng.standard_normal(n)
    f0, f1 = (300, 5000) if sobe else (5000, 250)
    x = banda_varrida(r, f0, f1) * env_ad(n, 0.55 if sobe else 0.15, 2.2)
    if not sobe:                                         # termina num baque suave
        tt = t(d)
        baque = np.sin(2 * np.pi * 70 * tt) * np.exp(-np.maximum(0, tt - d * 0.7) * 18) * (tt > d * 0.7)
        x = x + baque * 0.6
    return estereo(norm(x, -4), -0.6 if sobe else 0.6, 0.6 if sobe else -0.4)


def pop(d: float = 0.18) -> np.ndarray:
    tt = t(d)
    f = 900 * np.exp(-tt * 28) + 380
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 30)
    return estereo(norm(x, -5))


def clique(d: float = 0.06) -> np.ndarray:
    tt = t(d)
    x = (np.sin(2 * np.pi * 2400 * tt) * 0.6 + rng.standard_normal(len(tt)) * 0.4) * np.exp(-tt * 140)
    return estereo(norm(x, -6))


def tick(d: float = 0.05) -> np.ndarray:
    tt = t(d)
    return estereo(norm(np.sin(2 * np.pi * 3600 * tt) * np.exp(-tt * 160), -9))


def digitar(d: float = 2.0) -> np.ndarray:
    n = int(SR * d)
    x = np.zeros(n)
    pos = 0.02
    while pos < d - 0.08:
        k = clique(0.035)[:, 0] * rng.uniform(0.4, 1.0)
        i = int(pos * SR)
        x[i:i + len(k)] += k[: n - i]
        pos += rng.uniform(0.055, 0.14)
    sos = butter(2, [800, 7000], btype="band", fs=SR, output="sos")
    return estereo(norm(sosfilt(sos, x), -9))


def swipe(d: float = 0.35) -> np.ndarray:
    n = int(SR * d)
    return estereo(norm(banda_varrida(rng.standard_normal(n), 1500, 6000, 0.8, 30) * env_ad(n, 0.3, 2), -8), -0.5, 0.5)


def corte_papel(d: float = 0.3) -> np.ndarray:
    n = int(SR * d)
    sos = butter(2, 3000, btype="high", fs=SR, output="sos")
    x = sosfilt(sos, rng.standard_normal(n)) * env_ad(n, 0.05, 4)
    return estereo(norm(x, -9))


def brilho(d: float = 1.4) -> np.ndarray:
    tt = t(d)
    x = np.zeros_like(tt)
    for i, f in enumerate([1318.5, 1760, 2217.5, 2637]):        # E6 A6 C#7 E7, arpejo rápido
        ini = i * 0.06
        m = tt >= ini
        x[m] += np.sin(2 * np.pi * f * (tt[m] - ini)) * np.exp(-(tt[m] - ini) * 3.2) * 0.5
    return estereo(norm(x, -10), -0.3, 0.3)


def riser(d: float = 2.0) -> np.ndarray:
    tt = t(d)
    n = len(tt)
    ar = banda_varrida(rng.standard_normal(n), 400, 7000, 0.5, 50)
    f = 110 * (4 ** (tt / d))
    tom = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    x = (ar + tom) * (tt / d) ** 2.2
    x[-int(SR * 0.02):] *= np.linspace(1, 0, int(SR * 0.02))
    return estereo(norm(x, -6))


def impacto(d: float = 1.2) -> np.ndarray:
    tt = t(d)
    f = 55 + 60 * np.exp(-tt * 20)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3.5)
    sos = butter(2, 2500, btype="low", fs=SR, output="sos")
    ar = sosfilt(sos, rng.standard_normal(len(tt))) * np.exp(-tt * 9) * 0.35
    return estereo(norm(sub + ar, -3))


def erro(d: float = 0.45) -> np.ndarray:
    tt = t(d)
    x = np.where(tt < d / 2, np.sin(2 * np.pi * 330 * tt), np.sin(2 * np.pi * 247 * tt))
    x = x * np.exp(-((tt % (d / 2)) * 9)) * 0.8
    return estereo(norm(x, -10))


def conectar(d: float = 0.35) -> np.ndarray:
    tt = t(d)
    f = 600 + 1400 * (tt / d)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 10) + clique(d)[:, 0] * 0.6
    return estereo(norm(x, -8))


GERADORES = {
    "whoosh-entra": lambda: whoosh(1.1, True), "whoosh-sai": lambda: whoosh(1.1, False),
    "swipe": swipe, "pop": pop, "clique": clique, "digitar": digitar, "tick": tick,
    "corte-papel": corte_papel, "brilho": brilho, "riser": riser, "impacto": impacto,
    "erro": erro, "conectar": conectar,
}


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    nomes = [e["nome"] for e in json.loads((RAIZ / "00-marca/som/sfx.json").read_text())["efeitos"]]
    for nome in nomes:
        destino = SAIDA / f"{nome}.wav"
        if (SAIDA / f"{nome}.mp3").exists() or destino.exists():
            continue
        sf.write(destino, GERADORES[nome]().astype(np.float32), SR, subtype="PCM_24")
        print("sintetizado", destino.relative_to(RAIZ))


if __name__ == "__main__":
    main()
