"""Deterministik hash tabanlı gömme (mock).

Model gerektirmez; her metni sabit boyutlu, normalize edilmiş bir vektöre
eşler. Aynı girdi her zaman aynı çıktıyı verir (testler için ideal) ve benzer
kelimeleri paylaşan metinler bir miktar benzerlik gösterir (bag-of-hashed-tokens).
"""

from __future__ import annotations

import hashlib

import numpy as np

from sohbet.interfaces.embedding import EmbeddingBackend


class HashEmbedding(EmbeddingBackend):
    def __init__(self, dim: int = 256) -> None:
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    def _embed_one(self, text: str) -> list[float]:
        vec = np.zeros(self._dim, dtype=np.float32)
        for token in text.lower().split():
            h = hashlib.sha1(token.encode("utf-8")).digest()
            idx = int.from_bytes(h[:4], "little") % self._dim
            sign = 1.0 if h[4] % 2 == 0 else -1.0
            vec[idx] += sign
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec /= norm
        return vec.tolist()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]
