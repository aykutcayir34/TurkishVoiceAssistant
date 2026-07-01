"""WebSocket uçtan uca akış testi (tüm mock backend'lerle)."""

from __future__ import annotations

import base64

import pytest
from fastapi.testclient import TestClient

from sohbet.app import create_app


def _collect_until(ws, stop_type: str, limit: int = 200) -> list[dict]:
    events = []
    for _ in range(limit):
        msg = ws.receive_json()
        events.append(msg)
        if msg["type"] == stop_type:
            break
    return events


@pytest.mark.asyncio
async def test_ws_text_turn():
    app = create_app()
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "text", "text": "iade politikası nedir"})
            events = _collect_until(ws, "turn_end")
            types = {e["type"] for e in events}
            assert "final_transcript" in types
            assert "assistant_token" in types
            assert "tts_audio" in types
            assert "turn_end" in types


@pytest.mark.asyncio
async def test_ws_audio_turn():
    app = create_app()
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            loud = base64.b64encode(b"\x00\x40" * 800).decode()
            ws.send_json({"type": "audio_chunk", "data": loud, "sample_rate": 16000})
            ws.send_json({"type": "audio_end"})
            events = _collect_until(ws, "turn_end")
            assert any(e["type"] == "final_transcript" for e in events)
            assert any(e["type"] == "turn_end" for e in events)
