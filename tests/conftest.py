"""Ortak test fixture'ları: mock backend'ler ve yardımcı bir oturum kurucusu."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# src/ layout'u test yolu için ekle.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sohbet.backends.registry import Backends  # noqa: E402
from sohbet.backends.embedding.hash_mock import HashEmbedding  # noqa: E402
from sohbet.backends.llm.mock import MockLLM  # noqa: E402
from sohbet.backends.stt.mock import MockSTT  # noqa: E402
from sohbet.backends.tts.mock import MockTTS  # noqa: E402
from sohbet.backends.vad.energy_mock import EnergyVAD  # noqa: E402
from sohbet.backends.vectordb.memory import InMemoryVectorDB  # noqa: E402
from sohbet.config import Settings  # noqa: E402


@pytest.fixture
def settings() -> Settings:
    return Settings(
        vad_backend="energy",
        stt_backend="mock",
        llm_backend="mock",
        embedding_backend="hash",
        vectordb_backend="memory",
        tts_backend="mock",
    )


def make_backends(
    llm_delay: float = 0.02, tts_chunk_ms: int = 20, stt_script: str = "merhaba"
) -> Backends:
    return Backends(
        vad=EnergyVAD(threshold=0.02),
        stt=MockSTT(script=stt_script),
        llm=MockLLM(token_delay=llm_delay),
        embedding=HashEmbedding(dim=64),
        vectordb=InMemoryVectorDB(),
        tts=MockTTS(sample_rate=24000, chunk_ms=tts_chunk_ms),
    )


@pytest.fixture
def backends() -> Backends:
    return make_backends()
