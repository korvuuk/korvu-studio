"""Embeddings locais (multilingual-e5-small no MPS do M1). Nenhuma API externa.

Prefixos exigidos pelo e5: `passage: ` ao indexar, `query: ` ao buscar (§4).
`CONTEXTO_EMBEDDER=falso` troca o modelo por um embedder determinístico (hash de palavras) — só para testes que
não precisam medir qualidade.
"""
from __future__ import annotations

import hashlib
import os
import re
import threading
import unicodedata

import numpy as np

from . import config


class EmbedderFalso:
    nome = "falso"

    def _vetor(self, texto: str) -> np.ndarray:
        v = np.zeros(config.DIMENSOES, dtype=np.float32)
        t = unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()
        for palavra in re.findall(r"[a-z0-9]{3,}", t):
            h = int.from_bytes(hashlib.md5(palavra.encode()).digest()[:4], "little")
            v[h % config.DIMENSOES] += 1.0
        n = np.linalg.norm(v)
        return v / n if n else v + (1.0 / np.sqrt(config.DIMENSOES))

    def trechos(self, textos: list[str]) -> np.ndarray:
        return np.stack([self._vetor(t) for t in textos]) if textos else np.zeros((0, config.DIMENSOES))

    def consulta(self, texto: str) -> np.ndarray:
        return self._vetor(texto)


class EmbedderE5:
    def __init__(self, modelo: str = config.MODELO):
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
        import torch
        from sentence_transformers import SentenceTransformer

        dispositivo = "mps" if torch.backends.mps.is_available() else "cpu"
        self.nome = modelo
        self.modelo = SentenceTransformer(modelo, device=dispositivo)
        self.modelo.max_seq_length = 512

    def trechos(self, textos: list[str]) -> np.ndarray:
        if not textos:
            return np.zeros((0, config.DIMENSOES))
        return self.modelo.encode([config.PREFIXO_TRECHO + t for t in textos], batch_size=32,
                                  normalize_embeddings=True, show_progress_bar=False)

    def consulta(self, texto: str) -> np.ndarray:
        return self.modelo.encode([config.PREFIXO_CONSULTA + texto], normalize_embeddings=True,
                                  show_progress_bar=False)[0]


_trava = threading.Lock()
_embedder = None


def embedder():
    """Um embedder por processo (o servidor pré-carrega numa thread; a trava evita carregar o modelo duas vezes)."""
    global _embedder
    with _trava:
        if _embedder is None:
            _embedder = EmbedderFalso() if os.environ.get("CONTEXTO_EMBEDDER") == "falso" else EmbedderE5()
        return _embedder
