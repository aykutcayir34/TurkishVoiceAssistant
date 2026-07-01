"""Mock TTS.

Metin uzunluğuyla orantılı bir sinüs dalgası (duyulabilir "bip") üretir; gerçek
sese ihtiyaç duymadan ses akışı davranışını ve barge-in flush'ını test etmeye
yarar. Uzun metinleri parçalara bölerek streaming'i taklit eder.
"""

from __future__ import annotations

import asyncio
import math
import struct
from collections.abc import AsyncIterator

from sohbet.domain.types import TTSChunk
from sohbet.interfaces.tts import TTSBackend


class MockTTS(TTSBackend):
    def __init__(self, sample_rate: int = 24000, chunk_ms: int = 100) -> None:
        self._sample_rate = sample_rate
        self._chunk_ms = chunk_ms

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def _tone(self, num_samples: int, freq: float = 220.0) -> bytes:
        out = bytearray()
        for n in range(num_samples):
            val = int(0.2 * 32767 * math.sin(2 * math.pi * freq * n / self._sample_rate))
            out += struct.pack("<h", val)
        return bytes(out)

    async def synthesize(self, text: str) -> AsyncIterator[TTSChunk]:
        # Metin uzunluğuna göre yaklaşık süre: ~60ms/karakter, min 200ms.
        total_ms = max(200, len(text) * 60)
        samples_per_chunk = int(self._sample_rate * self._chunk_ms / 1000)
        remaining_ms = total_ms
        while remaining_ms > 0:
            await asyncio.sleep(self._chunk_ms / 1000)  # gerçek zamanı taklit
            n = samples_per_chunk if remaining_ms > self._chunk_ms else int(
                self._sample_rate * remaining_ms / 1000
            )
            remaining_ms -= self._chunk_ms
            yield TTSChunk(
                data=self._tone(n),
                text=text if remaining_ms <= 0 else "",
                sample_rate=self._sample_rate,
                is_last=remaining_ms <= 0,
            )
