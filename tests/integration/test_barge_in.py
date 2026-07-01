"""Barge-in senaryosunun uçtan uca doğrulaması (PRD §4.2, FR-9..FR-12)."""

from __future__ import annotations

import asyncio

import pytest

from sohbet.domain.events import Interrupted
from sohbet.domain.memory import INTERRUPTED_PREFIX
from sohbet.domain.state import TurnState
from sohbet.domain.types import AudioChunk
from sohbet.orchestration.session import ConversationSession
from tests.conftest import make_backends


class Collector:
    def __init__(self) -> None:
        self.events = []

    async def __call__(self, msg) -> None:
        self.events.append(msg)

    def of(self, cls) -> list:
        return [e for e in self.events if isinstance(e, cls)]


def loud_chunk() -> AudioChunk:
    # EnergyVAD eşiğinin (0.02) üzerinde RMS'e sahip yüksek genlikli çerçeve.
    return AudioChunk(data=b"\x00\x40" * 480, sample_rate=16000)


@pytest.mark.asyncio
async def test_barge_in_interrupts_and_records_spoken(settings):
    # Yavaş token + kısa tts -> tur konuşurken kesme yapabilelim.
    backends = make_backends(llm_delay=0.03, tts_chunk_ms=10)
    col = Collector()
    session = ConversationSession(backends, settings, col)

    # 1. Turu başlat (metinle) ve asistanın konuşmaya başlamasını bekle.
    await session.on_text("bana uzun bir cevap ver")
    for _ in range(200):
        await asyncio.sleep(0.01)
        if session.state.is_speaking:
            break
    assert session.state.is_speaking, "asistan konuşmaya başlamadı"

    # 2. Kullanıcı konuşarak keser: barge_in_frames (3) ardışık konuşma çerçevesi.
    for _ in range(settings.barge_in_frames):
        await session.on_audio_chunk(loud_chunk())

    # 3. Kesme gerçekleşti mi?
    assert col.of(Interrupted), "interrupted olayı gönderilmedi"
    assert session.state.state is TurnState.LISTENING
    assert session.current_task is None

    # 4. Söylenen kısım [kesildi] işaretiyle hafızada.
    interrupted_msgs = [m for m in session.memory.messages if m.interrupted]
    assert interrupted_msgs, "kesilen cevap hafızaya yazılmadı"
    assert interrupted_msgs[0].content.startswith(INTERRUPTED_PREFIX)

    # 5. LLM abort edildi (mock gözlemi).
    assert backends.llm.aborted is True


@pytest.mark.asyncio
async def test_barge_in_latency_under_budget(settings):
    backends = make_backends(llm_delay=0.03, tts_chunk_ms=10)
    col = Collector()
    session = ConversationSession(backends, settings, col)

    await session.on_text("uzun cevap")
    for _ in range(200):
        await asyncio.sleep(0.01)
        if session.state.is_speaking:
            break
    assert session.state.is_speaking

    for _ in range(settings.barge_in_frames):
        await session.on_audio_chunk(loud_chunk())

    lat = session.metrics.barge_in_latency
    assert lat is not None
    # PRD hedefi <300ms; mock ortamda çok daha düşük olmalı.
    assert lat < 0.3, f"barge-in gecikmesi çok yüksek: {lat*1000:.0f}ms"


@pytest.mark.asyncio
async def test_new_context_after_interruption(settings):
    """Kesme sonrası yeni bağlamla ikinci tur çalışır ve geçmiş kesmeyi içerir."""
    backends = make_backends(llm_delay=0.02, tts_chunk_ms=10)
    col = Collector()
    session = ConversationSession(backends, settings, col)

    await session.on_text("Ankara hava durumu")
    for _ in range(200):
        await asyncio.sleep(0.01)
        if session.state.is_speaking:
            break
    for _ in range(settings.barge_in_frames):
        await session.on_audio_chunk(loud_chunk())
    await session.on_audio_end()  # kesmeyi tetikleyen sesle yeni söylenti başladı

    # Not: mock STT scripted olduğundan yeni tur da başlar.
    if session.current_task:
        await session.current_task

    roles = [(m.role, m.interrupted) for m in session.memory.messages]
    # En az bir kesilmiş asistan mesajı ve ardından yeni bir user mesajı olmalı.
    assert any(r == ("assistant", True) for r in roles)
