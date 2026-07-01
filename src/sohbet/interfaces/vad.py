"""Ses Etkinliği Tespiti (VAD) sözleşmesi."""

from __future__ import annotations

from abc import ABC, abstractmethod

from sohbet.domain.types import AudioChunk


class VADBackend(ABC):
    """Bir ses çerçevesinde konuşma olup olmadığını belirler.

    SPEAKING durumunda barge-in tespiti için sürekli çağrılır; bu yüzden
    ucuz olmalıdır.
    """

    @abstractmethod
    def is_speech(self, chunk: AudioChunk) -> bool:
        """Verilen parçada konuşma varsa True döndür."""

    def reset(self) -> None:
        """Konuşmalar arası dahili durumu sıfırla (opsiyonel)."""
