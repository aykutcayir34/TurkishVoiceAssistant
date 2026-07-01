"""/ws WebSocket endpoint.

Her bağlantı için bir :class:`ConversationSession` oluşturur. Gelen mesajları
çözüp oturuma yönlendirir; oturumun ürettiği sunucu olaylarını JSON olarak
istemciye gönderir.
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from sohbet.backends.registry import Backends
from sohbet.config import Settings
from sohbet.domain.events import (
    ClientAudioChunk,
    ClientAudioEnd,
    ClientText,
    ServerMessage,
    parse_client_message,
)
from sohbet.domain.types import AudioChunk
from sohbet.logging import get_logger
from sohbet.orchestration.session import ConversationSession

logger = get_logger("sohbet.ws")

router = APIRouter()


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    backends: Backends = websocket.app.state.backends
    settings: Settings = websocket.app.state.settings

    async def send(msg: ServerMessage) -> None:
        await websocket.send_json(msg.model_dump())

    session = ConversationSession(backends=backends, settings=settings, send=send)
    logger.info("Yeni WS oturumu")

    try:
        while True:
            raw = await websocket.receive_json()
            try:
                msg = parse_client_message(raw)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Geçersiz istemci mesajı: %s", exc)
                continue

            if isinstance(msg, ClientAudioChunk):
                await session.on_audio_chunk(
                    AudioChunk(data=msg.pcm(), sample_rate=msg.sample_rate)
                )
            elif isinstance(msg, ClientAudioEnd):
                await session.on_audio_end()
            elif isinstance(msg, ClientText):
                await session.on_text(msg.text)
    except WebSocketDisconnect:
        logger.info("WS oturumu kapandı")
    finally:
        await session.aclose()
