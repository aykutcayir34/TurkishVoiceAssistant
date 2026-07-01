"""Metin-ses sentezi (TTS) sözleşmesi.

Cümle bazlı streaming: ilk sese kadar gecikmeyi (time-to-first-audio) azaltır.
Kesme (flush) model seviyesinde değil, orkestrasyon katmanında gerçekleşir:
turu taşıyan asyncio.Task iptal edilir ve istemciye ``interrupted`` gönderilerek
playback buffer'ı boşaltılır.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from sohbet.domain.types import TTSChunk


class TTSBackend(ABC):
    @abstractmethod
    def synthesize(self, text: str) -> AsyncIterator[TTSChunk]:
        """Bir metin (genellikle tek cümle) için ses parçaları üret."""
        raise NotImplementedError

    @property
    def sample_rate(self) -> int:
        return 24000
