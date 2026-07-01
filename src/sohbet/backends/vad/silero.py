"""Silero VAD gerçek backend.

Torch bağımlılığı modül gövdesinde değil, örnek oluşturulurken lazy yüklenir.
"""

from __future__ import annotations

import numpy as np

from sohbet.domain.types import AudioChunk
from sohbet.interfaces.vad import VADBackend


class SileroVAD(VADBackend):
    def __init__(self, threshold: float = 0.5, sample_rate: int = 16000) -> None:
        import torch  # lazy
        from silero_vad import load_silero_vad

        self._torch = torch
        self._model = load_silero_vad()
        self._threshold = threshold
        self._sample_rate = sample_rate

    def is_speech(self, chunk: AudioChunk) -> bool:
        if not chunk.data:
            return False
        samples = np.frombuffer(chunk.data, dtype=np.int16).astype(np.float32) / 32768.0
        tensor = self._torch.from_numpy(samples)
        # Silero 16kHz'de 512 örneklik pencere bekler; kısa parçalarda sıfır dolgu.
        if tensor.shape[0] < 512:
            pad = self._torch.zeros(512 - tensor.shape[0])
            tensor = self._torch.cat([tensor, pad])
        with self._torch.no_grad():
            prob = float(self._model(tensor[:512], self._sample_rate).item())
        return prob >= self._threshold

    def reset(self) -> None:
        if hasattr(self._model, "reset_states"):
            self._model.reset_states()
