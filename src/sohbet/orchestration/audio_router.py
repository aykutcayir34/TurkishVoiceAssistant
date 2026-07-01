"""Gelen ses yönlendirme: VAD tabanlı barge-in tespiti + söylenti tamponu.

Bu bileşen, asistan konuşurken de sürekli çalışır. SPEAKING/THINKING sırasında
VAD ile kullanıcının konuşup konuşmadığını izler; ``barge_in_frames`` kadar
ardışık konuşma çerçevesi görülünce barge-in tetiklenmesi gerektiğini bildirir.
LISTENING sırasında ise gelen sesi bir söylenti (utterance) tamponunda biriktirir.
"""

from __future__ import annotations

from sohbet.domain.types import AudioChunk
from sohbet.interfaces.vad import VADBackend


class AudioRouter:
    def __init__(self, vad: VADBackend, barge_in_frames: int = 3) -> None:
        self._vad = vad
        self._barge_in_frames = barge_in_frames
        self._speech_frames = 0
        self._utterance = bytearray()
        self._sample_rate = 16000

    # --- Barge-in tespiti (asistan meşgulken) --- #
    def detect_barge_in(self, chunk: AudioChunk) -> bool:
        """Meşgul durumda çağrılır. Yeterli ardışık konuşma varsa True döner."""
        if self._vad.is_speech(chunk):
            self._speech_frames += 1
        else:
            self._speech_frames = 0
        if self._speech_frames >= self._barge_in_frames:
            self._speech_frames = 0
            return True
        return False

    # --- Söylenti tamponu (dinlerken) --- #
    def append(self, chunk: AudioChunk) -> None:
        self._utterance.extend(chunk.data)
        self._sample_rate = chunk.sample_rate

    def start_utterance(self, chunk: AudioChunk) -> None:
        """Barge-in'i tetikleyen çerçeveyle yeni söylentiyi başlat."""
        self._utterance = bytearray(chunk.data)
        self._sample_rate = chunk.sample_rate

    def take_utterance(self) -> AudioChunk:
        data = bytes(self._utterance)
        self._utterance = bytearray()
        return AudioChunk(data=data, sample_rate=self._sample_rate)

    @property
    def has_utterance(self) -> bool:
        return len(self._utterance) > 0

    def reset(self) -> None:
        self._speech_frames = 0
        self._utterance = bytearray()
        self._vad.reset()
