"""Backend registry: config'e göre backend'leri kurar.

Gerçek backend'ler yalnızca seçildiklerinde import edilir; böylece ağır/GPU
bağımlılıkları kurulu olmasa da mock backend'lerle sistem çalışır.
"""

from __future__ import annotations

from dataclasses import dataclass

from sohbet.config import Settings
from sohbet.interfaces import (
    EmbeddingBackend,
    LLMBackend,
    STTBackend,
    TTSBackend,
    VADBackend,
    VectorDBBackend,
)
from sohbet.logging import get_logger

logger = get_logger("sohbet.registry")


@dataclass
class Backends:
    """Bir oturumun ihtiyaç duyduğu tüm backend'lerin paketi."""

    vad: VADBackend
    stt: STTBackend
    llm: LLMBackend
    embedding: EmbeddingBackend
    vectordb: VectorDBBackend
    tts: TTSBackend


def _build_vad(s: Settings) -> VADBackend:
    if s.vad_backend == "silero":
        from sohbet.backends.vad.silero import SileroVAD

        return SileroVAD(threshold=s.vad_speech_threshold, sample_rate=s.sample_rate)
    from sohbet.backends.vad.energy_mock import EnergyVAD

    return EnergyVAD(threshold=s.vad_speech_threshold)


def _build_stt(s: Settings) -> STTBackend:
    if s.stt_backend == "faster_whisper":
        from sohbet.backends.stt.faster_whisper import FasterWhisperSTT

        return FasterWhisperSTT(
            model=s.whisper_model,
            device=s.whisper_device,
            compute_type=s.whisper_compute_type,
            language=s.stt_language,
        )
    from sohbet.backends.stt.mock import MockSTT

    return MockSTT()


def _build_llm(s: Settings) -> LLMBackend:
    if s.llm_backend == "vllm":
        from sohbet.backends.llm.vllm_openai import VLLMBackend

        return VLLMBackend(
            base_url=s.llm_base_url, api_key=s.llm_api_key, model=s.llm_model
        )
    from sohbet.backends.llm.mock import MockLLM

    return MockLLM()


def _build_embedding(s: Settings) -> EmbeddingBackend:
    if s.embedding_backend == "bge_m3":
        from sohbet.backends.embedding.bge_m3 import BGEEmbedding

        return BGEEmbedding(
            model=s.embedding_model, device=s.embedding_device, dim=s.embedding_dim
        )
    from sohbet.backends.embedding.hash_mock import HashEmbedding

    return HashEmbedding(dim=256)


def _build_vectordb(s: Settings) -> VectorDBBackend:
    if s.vectordb_backend == "qdrant":
        from sohbet.backends.vectordb.qdrant import QdrantVectorDB

        return QdrantVectorDB(url=s.qdrant_url, collection=s.qdrant_collection)
    from sohbet.backends.vectordb.memory import InMemoryVectorDB

    return InMemoryVectorDB()


def _build_tts(s: Settings) -> TTSBackend:
    if s.tts_backend == "xtts":
        from sohbet.backends.tts.xtts import XTTSBackend

        return XTTSBackend(
            model=s.xtts_model, speaker_wav=s.tts_speaker_wav, language=s.tts_language
        )
    if s.tts_backend == "piper":
        from sohbet.backends.tts.piper import PiperBackend

        return PiperBackend(model=s.piper_model)
    from sohbet.backends.tts.mock import MockTTS

    return MockTTS()


def build_backends(settings: Settings) -> Backends:
    logger.info(
        "Backend'ler kuruluyor: vad=%s stt=%s llm=%s emb=%s vdb=%s tts=%s",
        settings.vad_backend,
        settings.stt_backend,
        settings.llm_backend,
        settings.embedding_backend,
        settings.vectordb_backend,
        settings.tts_backend,
    )
    return Backends(
        vad=_build_vad(settings),
        stt=_build_stt(settings),
        llm=_build_llm(settings),
        embedding=_build_embedding(settings),
        vectordb=_build_vectordb(settings),
        tts=_build_tts(settings),
    )
