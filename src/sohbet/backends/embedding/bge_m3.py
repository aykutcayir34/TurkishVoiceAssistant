"""BAAI/bge-m3 gerçek gömme backend (çok dilli, güçlü Türkçe)."""

from __future__ import annotations

import asyncio

from sohbet.interfaces.embedding import EmbeddingBackend


class BGEEmbedding(EmbeddingBackend):
    def __init__(
        self, model: str = "BAAI/bge-m3", device: str = "cuda", dim: int = 1024
    ) -> None:
        from sentence_transformers import SentenceTransformer  # lazy

        self._model = SentenceTransformer(model, device=device)
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        def _run() -> list[list[float]]:
            emb = self._model.encode(texts, normalize_embeddings=True)
            return [v.tolist() for v in emb]

        return await asyncio.to_thread(_run)
