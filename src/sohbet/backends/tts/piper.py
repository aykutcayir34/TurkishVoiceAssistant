"""Piper gerçek TTS backend (hafif, düşük gecikme).

XTTS'e göre daha hafif bir alternatif; CPU'da bile makul hızlıdır.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from sohbet.domain.types import TTSChunk
from sohbet.interfaces.tts import TTSBackend


class PiperBackend(TTSBackend):
    def __init__(self, model: str = "tr_TR-dfki-medium") -> None:
        from piper import PiperVoice  # lazy

        self._voice = PiperVoice.load(model)
        self._sample_rate = self._voice.config.sample_rate

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    async def synthesize(self, text: str) -> AsyncIterator[TTSChunk]:
        def _run() -> bytes:
            chunks = bytearray()
            for audio_bytes in self._voice.synthesize_stream_raw(text):
                chunks.extend(audio_bytes)
            return bytes(chunks)

        pcm = await asyncio.to_thread(_run)
        yield TTSChunk(
            data=pcm, text=text, sample_rate=self._sample_rate, is_last=True
        )
