"""faster-whisper gerçek STT backend.

Basitlik için akıştaki tüm sesi biriktirip nihai transkripsiyon üretir; ara
sonuçlar VAD ile bölünmüş segmentlerden gelir. Ağır kütüphane lazy yüklenir.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import numpy as np

from sohbet.domain.types import AudioChunk, Transcript
from sohbet.interfaces.stt import STTBackend


class FasterWhisperSTT(STTBackend):
    def __init__(
        self,
        model: str = "large-v3",
        device: str = "cuda",
        compute_type: str = "float16",
        language: str = "tr",
    ) -> None:
        from faster_whisper import WhisperModel  # lazy

        self._model = WhisperModel(model, device=device, compute_type=compute_type)
        self._language = language

    async def stream(self, audio: AsyncIterator[AudioChunk]) -> AsyncIterator[Transcript]:
        buf = bytearray()
        sr = 16000
        async for chunk in audio:
            buf.extend(chunk.data)
            sr = chunk.sample_rate
        samples = np.frombuffer(bytes(buf), dtype=np.int16).astype(np.float32) / 32768.0

        def _run() -> str:
            segments, _ = self._model.transcribe(
                samples, language=self._language, vad_filter=True
            )
            return " ".join(seg.text.strip() for seg in segments).strip()

        text = await asyncio.to_thread(_run)
        yield Transcript(text=text, is_final=True, confidence=1.0)
