"""Bağlantı başına konuşma oturumu.

Durum makinesini, hafızayı, backend'leri, aktif tur task'ını ve giden-mesaj
kanalını sahiplenir. Barge-in bu sınıfta tetiklenir. Transport katmanı yalnızca
``on_audio_chunk`` / ``on_audio_end`` / ``on_text`` çağırır ve ``send`` sağlar.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from sohbet.backends.registry import Backends
from sohbet.config import Settings
from sohbet.domain.events import FinalTranscript, PartialTranscript, ServerMessage
from sohbet.domain.memory import ConversationMemory
from sohbet.domain.state import TurnState, TurnStateMachine
from sohbet.domain.types import AudioChunk
from sohbet.logging import get_logger
from sohbet.metrics import TurnMetrics
from sohbet.orchestration import barge_in as barge_in_mod
from sohbet.orchestration.audio_router import AudioRouter
from sohbet.orchestration.pipeline import run_turn
from sohbet.rag.retriever import Retriever

logger = get_logger("sohbet.session")

SendFn = Callable[[ServerMessage], Awaitable[None]]


class ConversationSession:
    def __init__(
        self,
        backends: Backends,
        settings: Settings,
        send: SendFn,
    ) -> None:
        self.backends = backends
        self.settings = settings
        self.send = send

        self.state = TurnStateMachine(on_transition=self._on_transition)
        self.memory = ConversationMemory(system_prompt=settings.system_prompt)
        self.retriever = Retriever(
            backends.embedding, backends.vectordb, top_k=settings.retrieval_top_k
        )
        self.router = AudioRouter(backends.vad, barge_in_frames=settings.barge_in_frames)
        self.metrics = TurnMetrics()

        self.current_task: asyncio.Task | None = None
        self.spoken_so_far: str = ""
        self._lock = asyncio.Lock()

    def _on_transition(self, prev: TurnState, nxt: TurnState) -> None:
        logger.debug("Durum: %s -> %s", prev.value, nxt.value)

    # ------------------------------------------------------------------ #
    # Transport tarafından çağrılan giriş noktaları
    # ------------------------------------------------------------------ #
    async def on_audio_chunk(self, chunk: AudioChunk) -> None:
        # Asistan meşgulse: barge-in tespiti.
        if self.state.is_busy:
            if self.router.detect_barge_in(chunk):
                await barge_in_mod.interrupt(self)
                # Kesmeyi tetikleyen konuşmayı yeni söylentinin başı yap.
                self.router.start_utterance(chunk)
            return

        # Dinleme: sesi biriktir.
        if self.state.state is TurnState.IDLE:
            self.state.to(TurnState.LISTENING)
        self.router.append(chunk)

    async def on_audio_end(self) -> None:
        """Kullanıcı konuşmayı bitirdi: STT çalıştır ve turu başlat."""
        if not self.router.has_utterance:
            return
        async with self._lock:
            utterance = self.router.take_utterance()
            self.metrics = TurnMetrics()
            self.metrics.mark("listen_end")
            text = await self._run_stt(utterance)
            if not text.strip():
                self.state.to(TurnState.IDLE)
                return
            self._start_turn(text)

    async def on_text(self, text: str) -> None:
        """Geliştirme/test kısayolu: sesi atlayıp doğrudan metinle tur başlat."""
        if self.state.is_busy:
            await barge_in_mod.interrupt(self)
        if self.state.state is TurnState.IDLE:
            self.state.to(TurnState.LISTENING)
        self.metrics = TurnMetrics()
        self.metrics.mark("listen_end")
        await self.send(FinalTranscript(text=text))
        self._start_turn(text)

    # ------------------------------------------------------------------ #
    # Yardımcılar
    # ------------------------------------------------------------------ #
    async def _run_stt(self, utterance: AudioChunk) -> str:
        """Söylentiyi STT'den geçirir; ara ve nihai transkriptleri iletir."""

        async def _one():
            yield utterance

        final = ""
        async for t in self.backends.stt.stream(_one()):
            if t.is_final:
                final = t.text
                await self.send(FinalTranscript(text=t.text))
            else:
                await self.send(PartialTranscript(text=t.text))
        return final

    def _start_turn(self, user_text: str) -> None:
        self.memory.add_user(user_text)
        self.current_task = asyncio.create_task(self._guarded_turn())

    async def _guarded_turn(self) -> None:
        try:
            await run_turn(self)
        except asyncio.CancelledError:
            # Barge-in tarafından iptal edildi; hafıza kaydı orada yapılır.
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Tur sırasında hata: %s", exc)
            from sohbet.domain.events import ErrorEvent

            await self.send(ErrorEvent(message="İç hata oluştu."))
            if self.state.state is not TurnState.IDLE:
                try:
                    self.state.to(TurnState.IDLE)
                except Exception:  # noqa: BLE001
                    self.state.reset()

    async def aclose(self) -> None:
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
            try:
                await self.current_task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass
