"""Doküman ingest: yükle → parçala → göm → vektör DB'ye yaz (PRD §9.1)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from sohbet.interfaces import EmbeddingBackend, VectorDBBackend
from sohbet.interfaces.vectordb import VectorPoint
from sohbet.logging import get_logger
from sohbet.rag.chunking import chunk_text
from sohbet.rag.loaders import iter_documents, load_document

logger = get_logger("sohbet.ingest")


def _point_id(source: str, index: int) -> str:
    h = hashlib.sha1(f"{source}:{index}".encode()).hexdigest()
    # Qdrant UUID veya unsigned int ister; hex'in ilk 32'sinden UUID biçimi üret.
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


async def ingest_documents(
    paths: list[Path],
    embedding: EmbeddingBackend,
    vectordb: VectorDBBackend,
    chunk_size: int = 700,
    overlap: int = 100,
) -> int:
    """Verilen dosyaları parçalayıp gömerek vektör DB'ye yazar. Yazılan parça sayısını döndürür."""
    await vectordb.ensure_collection(embedding.dim)

    total = 0
    for path in paths:
        text = load_document(path)
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        if not chunks:
            logger.warning("Boş doküman atlandı: %s", path)
            continue
        vectors = await embedding.embed([c.text for c in chunks])
        points = [
            VectorPoint(
                id=_point_id(str(path), c.index),
                vector=vec,
                text=c.text,
                source=path.name,
                metadata={"chunk_index": c.index},
            )
            for c, vec in zip(chunks, vectors)
        ]
        await vectordb.upsert(points)
        total += len(points)
        logger.info("Yüklendi: %s (%d parça)", path.name, len(points))
    return total


async def ingest_directory(
    directory: str | Path,
    embedding: EmbeddingBackend,
    vectordb: VectorDBBackend,
    chunk_size: int = 700,
    overlap: int = 100,
) -> int:
    paths = iter_documents(directory)
    logger.info("%d doküman bulundu: %s", len(paths), directory)
    return await ingest_documents(paths, embedding, vectordb, chunk_size, overlap)
