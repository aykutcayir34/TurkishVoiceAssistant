from __future__ import annotations

import asyncio

import pytest

from sohbet.domain.events import (
    AssistantToken,
    FinalTranscript,
    TTSAudio,
    TurnEnd,
)
from sohbet.domain.state import TurnState
from sohbet.orchestration.session import ConversationSession
from tests.conftest import make_backends


class Collector:
    def __init__(self) -> None:
        self.events = []

    async def __call__(self, msg) -> None:
        self.events.append(msg)

    def of(self, cls) -> list:
        return [e for e in self.events if isinstance(e, cls)]


@pytest.mark.asyncio
async def test_full_turn_via_text(settings):
    backends = make_backends(llm_delay=0.0, tts_chunk_ms=5)
    col = Collector()
    session = ConversationSession(backends, settings, col)

    await session.on_text("iade politikası nedir")
    assert session.current_task is not None
    await session.current_task

    # Beklenen olay dizisi: final transcript -> token'lar -> tts sesleri -> turn_end
    assert col.of(FinalTranscript)
    assert col.of(AssistantToken)
    assert col.of(TTSAudio)
    assert col.of(TurnEnd)

    # Doğal tamamlanma: state IDLE'a döner ve asistan cevabı hafızaya yazılır.
    assert session.state.state is TurnState.IDLE
    assert any(m.role == "assistant" for m in session.memory.messages)
    assert not any(m.interrupted for m in session.memory.messages)


@pytest.mark.asyncio
async def test_full_turn_via_audio(settings):
    backends = make_backends(llm_delay=0.0, tts_chunk_ms=5, stt_script="kargo ne zaman gelir")
    col = Collector()
    session = ConversationSession(backends, settings, col)

    from sohbet.domain.types import AudioChunk

    # Yüksek genlikli PCM -> mock STT scripted metni üretir.
    loud = b"\x00\x40" * 800  # ~0.5 genlik
    await session.on_audio_chunk(AudioChunk(data=loud, sample_rate=16000))
    await session.on_audio_end()
    assert session.current_task is not None
    await session.current_task

    finals = col.of(FinalTranscript)
    assert finals and finals[-1].text == "kargo ne zaman gelir"
    assert col.of(TurnEnd)
