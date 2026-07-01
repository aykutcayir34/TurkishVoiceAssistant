"""Konuşma tanıma (STT) sözleşmesi."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from sohbet.domain.types import AudioChunk, Transcript


class STTBackend(ABC):
    """Ses akışını metne çevirir; ara (partial) ve nihai (final) sonuç üretir."""

    @abstractmethod
    def stream(self, audio: AsyncIterator[AudioChunk]) -> AsyncIterator[Transcript]:
        """Bir ses akışını tüketip transkriptler üreten async generator döndür.

        Son üretilen transkriptin ``is_final=True`` olması beklenir.
        """
        raise NotImplementedError

    async def transcribe(self, audio: bytes, sample_rate: int = 16000) -> str:
        """Tek seferlik (non-streaming) kolaylık yardımcısı."""

        async def _one() -> AsyncIterator[AudioChunk]:
            yield AudioChunk(data=audio, sample_rate=sample_rate)

        text = ""
        async for t in self.stream(_one()):
            if t.is_final:
                text = t.text
        return text
