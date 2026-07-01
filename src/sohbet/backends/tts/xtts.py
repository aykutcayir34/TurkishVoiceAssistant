"""Coqui XTTS-v2 gerçek TTS backend (çok dilli, ses klonlama).

Tek cümleyi sentezler ve int16 PCM olarak tek parça halinde yield eder. Ağır
kütüphane lazy yüklenir.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import numpy as np

from sohbet.domain.types import TTSChunk
from sohbet.interfaces.tts import TTSBackend


class XTTSBackend(TTSBackend):
    def __init__(
        self,
        model: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        speaker_wav: str = "data/voices/tr_reference.wav",
        language: str = "tr",
    ) -> None:
        from TTS.api import TTS  # lazy

        self._tts = TTS(model)
        self._speaker_wav = speaker_wav
        self._language = language
        self._sample_rate = 24000

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    async def synthesize(self, text: str) -> AsyncIterator[TTSChunk]:
        def _run() -> bytes:
            wav = self._tts.tts(
                text=text, speaker_wav=self._speaker_wav, language=self._language
            )
            arr = np.array(wav, dtype=np.float32)
            pcm = (np.clip(arr, -1.0, 1.0) * 32767).astype(np.int16)
            return pcm.tobytes()

        pcm = await asyncio.to_thread(_run)
        yield TTSChunk(
            data=pcm, text=text, sample_rate=self._sample_rate, is_last=True
        )
