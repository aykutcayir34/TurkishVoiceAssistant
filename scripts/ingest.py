#!/usr/bin/env python
"""Bilgi tabanı ingest CLI'ı.

Kullanım:
    python scripts/ingest.py data/docs

Backend seçimleri ortam değişkenleriyle yapılır (bkz. .env.example). Varsayılan
mock backend'ler CPU'da çalışır; gerçek Qdrant + bge-m3 için:
    SOHBET_EMBEDDING_BACKEND=bge_m3 SOHBET_VECTORDB_BACKEND=qdrant \
        python scripts/ingest.py data/docs
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# src/ layout'u doğrudan çalıştırma için ekle.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sohbet.backends.registry import build_backends  # noqa: E402
from sohbet.config import get_settings  # noqa: E402
from sohbet.logging import setup_logging  # noqa: E402
from sohbet.rag.ingest import ingest_directory  # noqa: E402


async def _main(directory: str) -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    backends = build_backends(settings)
    count = await ingest_directory(
        directory,
        backends.embedding,
        backends.vectordb,
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap,
    )
    print(f"Toplam {count} parça yazıldı.")


if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else "data/docs"
    asyncio.run(_main(directory))
