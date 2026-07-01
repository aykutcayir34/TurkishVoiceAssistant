"""Metin parçalama (chunking).

Kelime tabanlı yaklaşık token sayımı (tiktoken bağımlılığı zorunlu olmasın diye).
Yaklaşık ~700 token, %10-15 örtüşme (PRD §9.1).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Chunk:
    text: str
    index: int


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 100) -> list[Chunk]:
    """Metni yaklaşık ``chunk_size`` kelimelik, ``overlap`` örtüşmeli parçalara böler.

    Kelime sayısı token'a kaba bir yaklaşımdır; Türkçe için yeterlidir.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size pozitif olmalı")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap 0 ile chunk_size arasında olmalı")

    words = text.split()
    if not words:
        return []

    chunks: list[Chunk] = []
    step = chunk_size - overlap
    idx = 0
    for start in range(0, len(words), step):
        window = words[start : start + chunk_size]
        if not window:
            break
        chunks.append(Chunk(text=" ".join(window), index=idx))
        idx += 1
        if start + chunk_size >= len(words):
            break
    return chunks
