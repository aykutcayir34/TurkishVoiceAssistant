"""Sorgu zamanı retrieval: embed → vektör arama → (ops.) rerank."""

from __future__ import annotations

from sohbet.domain.types import RetrievedChunk
from sohbet.interfaces import EmbeddingBackend, VectorDBBackend


class Retriever:
    def __init__(
        self,
        embedding: EmbeddingBackend,
        vectordb: VectorDBBackend,
        top_k: int = 5,
    ) -> None:
        self._embedding = embedding
        self._vectordb = vectordb
        self._top_k = top_k

    async def retrieve(self, query: str, top_k: int | None = None) -> list[RetrievedChunk]:
        k = top_k or self._top_k
        vector = await self._embedding.embed_one(query)
        hits = await self._vectordb.search(vector, k=k)
        return [
            RetrievedChunk(
                text=h.text, source=h.source, score=h.score, metadata=h.metadata
            )
            for h in hits
        ]
