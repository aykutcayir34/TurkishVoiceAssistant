"""In-memory kosinüs benzerliği vektör deposu (mock).

Docker/Qdrant gerektirmez; unit ve integration testleri için idealdir.
"""

from __future__ import annotations

import numpy as np

from sohbet.interfaces.vectordb import Hit, VectorDBBackend, VectorPoint


class InMemoryVectorDB(VectorDBBackend):
    def __init__(self) -> None:
        self._points: list[VectorPoint] = []
        self._matrix: np.ndarray | None = None

    async def ensure_collection(self, dim: int) -> None:
        # Bellek deposunda şema yok; boyut ilk upsert'te örtük belirlenir.
        pass

    async def upsert(self, points: list[VectorPoint]) -> None:
        self._points.extend(points)
        self._matrix = None  # yeniden hesaplanacak

    def _ensure_matrix(self) -> None:
        if self._matrix is None and self._points:
            mat = np.array([p.vector for p in self._points], dtype=np.float32)
            norms = np.linalg.norm(mat, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self._matrix = mat / norms

    async def search(
        self, vector: list[float], k: int = 5, filter: dict | None = None
    ) -> list[Hit]:
        self._ensure_matrix()
        if self._matrix is None:
            return []
        q = np.array(vector, dtype=np.float32)
        qn = np.linalg.norm(q)
        if qn > 0:
            q = q / qn
        scores = self._matrix @ q
        top = np.argsort(-scores)[:k]
        return [
            Hit(
                text=self._points[i].text,
                source=self._points[i].source,
                score=float(scores[i]),
                metadata=self._points[i].metadata,
            )
            for i in top
        ]

    async def count(self) -> int:
        return len(self._points)
