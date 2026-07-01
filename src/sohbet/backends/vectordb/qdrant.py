"""Qdrant gerçek vektör DB backend."""

from __future__ import annotations

from sohbet.interfaces.vectordb import Hit, VectorDBBackend, VectorPoint


class QdrantVectorDB(VectorDBBackend):
    def __init__(self, url: str, collection: str) -> None:
        from qdrant_client import AsyncQdrantClient  # lazy

        self._client = AsyncQdrantClient(url=url)
        self._collection = collection

    async def ensure_collection(self, dim: int) -> None:
        from qdrant_client.models import Distance, VectorParams

        exists = await self._client.collection_exists(self._collection)
        if not exists:
            await self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )

    async def upsert(self, points: list[VectorPoint]) -> None:
        from qdrant_client.models import PointStruct

        qpoints = [
            PointStruct(
                id=p.id,
                vector=p.vector,
                payload={"text": p.text, "source": p.source, **p.metadata},
            )
            for p in points
        ]
        await self._client.upsert(collection_name=self._collection, points=qpoints)

    async def search(
        self, vector: list[float], k: int = 5, filter: dict | None = None
    ) -> list[Hit]:
        res = await self._client.query_points(
            collection_name=self._collection, query=vector, limit=k, with_payload=True
        )
        hits: list[Hit] = []
        for pt in res.points:
            payload = pt.payload or {}
            hits.append(
                Hit(
                    text=payload.get("text", ""),
                    source=payload.get("source", ""),
                    score=float(pt.score),
                    metadata={
                        kk: vv
                        for kk, vv in payload.items()
                        if kk not in ("text", "source")
                    },
                )
            )
        return hits

    async def count(self) -> int:
        res = await self._client.count(collection_name=self._collection)
        return int(res.count)
