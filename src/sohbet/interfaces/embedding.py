"""Gömme (embedding) sözleşmesi."""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingBackend(ABC):
    @property
    @abstractmethod
    def dim(self) -> int:
        """Üretilen vektörlerin boyutu."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Metin listesini vektör listesine gömer."""

    async def embed_one(self, text: str) -> list[float]:
        return (await self.embed([text]))[0]
