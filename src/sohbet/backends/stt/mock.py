"""Mock STT.

Ham sesi çözemeyeceği için, önceden ayarlanmış (scripted) bir metni ara ve
nihai transkript olarak üretir. Testler bu metni ``push_script`` ile ayarlar.
Ayrıca ClientText yolu sesi tümüyle atlayabilir; bu backend sadece ses yolu
kullanıldığında devreye girer.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from sohbet.domain.types import AudioChunk, Transcript
from sohbet.interfaces.stt import STTBackend


class MockSTT(STTBackend):
    def __init__(self, script: str = "merhaba dünya") -> None:
        self._script = script

    def set_script(self, text: str) -> None:
        self._script = text

    async def stream(self, audio: AsyncIterator[AudioChunk]) -> AsyncIterator[Transcript]:
        # Sesi tüket (gerçekçi davranış), sonra scripted metni üret.
        async for _ in audio:
            pass
        words = self._script.split()
        acc = ""
        for w in words:
            acc = (acc + " " + w).strip()
            await asyncio.sleep(0)  # iptal edilebilirlik noktası
            yield Transcript(text=acc, is_final=False)
        yield Transcript(text=self._script, is_final=True, confidence=1.0)
