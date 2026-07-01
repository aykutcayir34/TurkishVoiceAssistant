"""Tur ve barge-in gecikme metrikleri (NFR-5).

Zaman kaynağı dışarıdan enjekte edilebilir (test edilebilirlik için).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from collections.abc import Callable

from sohbet.logging import get_logger

logger = get_logger("sohbet.metrics")


@dataclass
class TurnMetrics:
    """Tek bir konuşma turunun zaman damgaları (saniye cinsinden monotonik)."""

    now: Callable[[], float] = time.monotonic
    listen_end: float | None = None       # kullanıcı konuşması bitti
    first_token: float | None = None      # LLM ilk token
    first_audio: float | None = None      # istemciye ilk TTS
    speak_start: float | None = None
    interrupt_signal: float | None = None  # VAD kesme algıladı
    interrupt_done: float | None = None    # ses susturuldu
    extra: dict = field(default_factory=dict)

    def mark(self, name: str) -> None:
        setattr(self, name, self.now())

    @property
    def turn_latency(self) -> float | None:
        """Konuşma bitişinden ilk sese kadar (PRD hedefi P50 < 1.2s)."""
        if self.listen_end is None or self.first_audio is None:
            return None
        return self.first_audio - self.listen_end

    @property
    def barge_in_latency(self) -> float | None:
        """Kesme sinyalinden ses susmasına kadar (PRD hedefi < 300ms)."""
        if self.interrupt_signal is None or self.interrupt_done is None:
            return None
        return self.interrupt_done - self.interrupt_signal

    def log_summary(self) -> None:
        tl = self.turn_latency
        bl = self.barge_in_latency
        parts = []
        if tl is not None:
            parts.append(f"tur_gecikmesi={tl * 1000:.0f}ms")
        if bl is not None:
            parts.append(f"barge_in={bl * 1000:.0f}ms")
        if parts:
            logger.info("Tur metrikleri: %s", " ".join(parts))
