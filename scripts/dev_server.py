#!/usr/bin/env python
"""Tüm mock backend'lerle CPU üzerinde geliştirme sunucusu başlatır.

Ortam değişkenlerini mock'a zorlar ve uvicorn'u çalıştırır.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

os.environ.setdefault("SOHBET_VAD_BACKEND", "energy")
os.environ.setdefault("SOHBET_STT_BACKEND", "mock")
os.environ.setdefault("SOHBET_LLM_BACKEND", "mock")
os.environ.setdefault("SOHBET_EMBEDDING_BACKEND", "hash")
os.environ.setdefault("SOHBET_VECTORDB_BACKEND", "memory")
os.environ.setdefault("SOHBET_TTS_BACKEND", "mock")

import uvicorn  # noqa: E402

from sohbet.config import get_settings  # noqa: E402

if __name__ == "__main__":
    s = get_settings()
    uvicorn.run("sohbet.app:app", host=s.host, port=s.port, reload=False)
