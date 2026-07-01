"""Barge-in (kullanıcının modeli konuşarak kesmesi) mantığı.

Kritik yol ve sıralaması (PRD §7.2, <300ms bütçe):

1. İstemciye ``interrupted`` gönder → istemci playback buffer'ını DERHAL boşaltır
   (sessizliğe en hızlı yol; ilk adım budur).
2. Turu taşıyan ``asyncio.Task``'ı iptal et → LLM ve TTS generator'ları kapanır
   (vLLM abort).
3. O ana kadar **gerçekten söylenmiş** metni (``spoken_so_far``) hafızaya
   ``[kesildi]`` işaretiyle yaz.
4. Duruma LISTENING'e geç → sürekli ses döngüsü yeni turu STT'ye besler.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from sohbet.domain.events import Interrupted
from sohbet.domain.state import TurnState
from sohbet.logging import get_logger

if TYPE_CHECKING:
    from sohbet.orchestration.session import ConversationSession

logger = get_logger("sohbet.barge_in")


async def interrupt(session: ConversationSession) -> None:
    """Aktif asistan turunu keser ve yeni girdi için dinlemeye geçer."""
    if not session.state.is_busy:
        return

    session.metrics.mark("interrupt_signal")

    # 1. Önce istemciye sustur sinyali (en hızlı sessizlik yolu).
    await session.send(Interrupted())
    session.state.to(TurnState.INTERRUPTED)

    # 2. Turu iptal et ve bitmesini bekle (temizlik/abort tamamlansın).
    task = session.current_task
    if task is not None and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception as exc:  # noqa: BLE001
            logger.warning("Tur iptalinde beklenmeyen hata: %s", exc)
    session.current_task = None

    # 3. Gerçekten söylenmiş kısmı kesildi olarak hafızaya yaz (FR-10).
    session.memory.add_assistant(session.spoken_so_far, interrupted=True)
    logger.info("Barge-in: söylenen='%s'", session.spoken_so_far[:60])
    session.spoken_so_far = ""

    session.metrics.mark("interrupt_done")
    session.metrics.log_summary()

    # 4. Yeni girdiyi dinlemeye geç.
    session.state.to(TurnState.LISTENING)
