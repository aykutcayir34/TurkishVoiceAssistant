"""WebSocket tel protokolü (PRD §11).

İstemci ↔ sunucu arasındaki tüm mesajların tek doğruluk kaynağı. Hem
``transport/ws.py`` hem de testler bu modelleri kullanır. Ses verisi tel
üzerinde base64 kodlu taşınır.
"""

from __future__ import annotations

import base64
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# İstemci -> Sunucu
# --------------------------------------------------------------------------- #


class ClientAudioChunk(BaseModel):
    type: Literal["audio_chunk"] = "audio_chunk"
    data: str  # base64 PCM
    sample_rate: int = 16000

    def pcm(self) -> bytes:
        return base64.b64decode(self.data)


class ClientAudioEnd(BaseModel):
    type: Literal["audio_end"] = "audio_end"


class ClientText(BaseModel):
    """Test/geliştirme kolaylığı için doğrudan metin girişi (sesi atlar)."""

    type: Literal["text"] = "text"
    text: str


ClientMessage = Annotated[
    Union[ClientAudioChunk, ClientAudioEnd, ClientText],
    Field(discriminator="type"),
]


# --------------------------------------------------------------------------- #
# Sunucu -> İstemci
# --------------------------------------------------------------------------- #


class PartialTranscript(BaseModel):
    type: Literal["partial_transcript"] = "partial_transcript"
    text: str


class FinalTranscript(BaseModel):
    type: Literal["final_transcript"] = "final_transcript"
    text: str


class AssistantToken(BaseModel):
    type: Literal["assistant_token"] = "assistant_token"
    text: str


class TTSAudio(BaseModel):
    type: Literal["tts_audio"] = "tts_audio"
    data: str  # base64 PCM
    sample_rate: int = 24000

    @classmethod
    def from_pcm(cls, pcm: bytes, sample_rate: int = 24000) -> TTSAudio:
        return cls(data=base64.b64encode(pcm).decode("ascii"), sample_rate=sample_rate)


class Interrupted(BaseModel):
    """Barge-in tetiklendi: istemci playback buffer'ını DERHAL boşaltmalı."""

    type: Literal["interrupted"] = "interrupted"


class TurnEnd(BaseModel):
    type: Literal["turn_end"] = "turn_end"
    citations: list[str] = Field(default_factory=list)


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str


ServerMessage = Union[
    PartialTranscript,
    FinalTranscript,
    AssistantToken,
    TTSAudio,
    Interrupted,
    TurnEnd,
    ErrorEvent,
]


def parse_client_message(raw: dict) -> ClientMessage:
    """Ham dict'i doğru istemci mesaj modeline çözer."""
    from pydantic import TypeAdapter

    return TypeAdapter(ClientMessage).validate_python(raw)
