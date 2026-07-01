"""RMS enerji tabanlı basit VAD (mock).

ML gerektirmez; 16-bit PCM'in RMS enerjisi bir eşiğin üzerindeyse konuşma
sayar. Testler ve CPU geliştirme için yeterlidir.
"""

from __future__ import annotations

import numpy as np

from sohbet.domain.types import AudioChunk
from sohbet.interfaces.vad import VADBackend


class EnergyVAD(VADBackend):
    def __init__(self, threshold: float = 0.02) -> None:
        # threshold: normalize edilmiş [0,1] RMS eşiği.
        self._threshold = threshold

    def is_speech(self, chunk: AudioChunk) -> bool:
        if not chunk.data:
            return False
        samples = np.frombuffer(chunk.data, dtype=np.int16).astype(np.float32) / 32768.0
        if samples.size == 0:
            return False
        rms = float(np.sqrt(np.mean(samples**2)))
        return rms >= self._threshold

    def reset(self) -> None:
        pass
