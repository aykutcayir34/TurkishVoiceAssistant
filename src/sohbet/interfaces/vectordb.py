"""Vektör veritabanı sözleşmesi."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(slots=True)
class VectorPoint:
    """Vektör DB'ye yazılacak bir kayıt."""

    id: str
    vector: list[float]
    text: str
    source: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass(slots=True)
class Hit:
    """Aramadan dönen bir sonuç."""

    text: str
    source: str
    score: float
    metadata: dict = field(default_factory=dict)


class VectorDBBackend(ABC):
    @abstractmethod
    async def ensure_collection(self, dim: int) -> None:
        """Koleksiyonu (yoksa) verilen boyutla oluştur."""

    @abstractmethod
    async def upsert(self, points: list[VectorPoint]) -> None:
        """Kayıtları ekle/güncelle."""

    @abstractmethod
    async def search(
        self, vector: list[float], k: int = 5, filter: dict | None = None
    ) -> list[Hit]:
        """En yakın k kaydı döndür."""

    async def count(self) -> int:
        return 0
