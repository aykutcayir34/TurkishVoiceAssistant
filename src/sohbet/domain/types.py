"""Boru hattı boyunca dolaşan temel veri tipleri.

Bu modül hiçbir ağır bağımlılık içermez; sadece stdlib dataclass'ları kullanır,
böylece hem gerçek hem mock backend'ler ve testler bunları serbestçe paylaşabilir.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AudioChunk:
    """Ham PCM ses parçası (16-bit little-endian mono varsayılır)."""

    data: bytes
    sample_rate: int = 16000

    @property
    def num_samples(self) -> int:
        return len(self.data) // 2


@dataclass(slots=True)
class Transcript:
    """STT çıktısı. ``is_final=False`` iken ara (partial) sonuçtur."""

    text: str
    is_final: bool = False
    confidence: float | None = None


@dataclass(slots=True)
class Citation:
    """RAG kaynak referansı."""

    source: str
    score: float
    snippet: str = ""


@dataclass(slots=True)
class RetrievedChunk:
    """Vektör aramasından dönen bir doküman parçası."""

    text: str
    source: str
    score: float
    metadata: dict = field(default_factory=dict)

    def as_citation(self) -> Citation:
        return Citation(source=self.source, score=self.score, snippet=self.text[:160])


@dataclass(slots=True)
class TTSChunk:
    """TTS çıktısı: bir cümleye ait sentezlenmiş ses ve kaynak metni.

    ``text`` alanı barge-in sırasında "gerçekten söylenen" (spoken_so_far)
    muhasebesi için tutulur; sadece istemciye gönderilmiş parçaların metni sayılır.
    """

    data: bytes
    text: str = ""
    sample_rate: int = 24000
    is_last: bool = False
