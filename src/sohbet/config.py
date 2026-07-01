"""Uygulama yapılandırması (pydantic-settings).

Backend seçimleri tamamen ortam değişkenleriyle yapılır; örn.
``SOHBET_LLM_BACKEND=vllm`` veya ``SOHBET_LLM_BACKEND=mock``. Varsayılan tüm
backend'ler ``mock``'tur → sıfır ML bağımlılığıyla CPU'da çalışır.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SOHBET_", env_file=".env", extra="ignore"
    )

    # --- Backend seçimi (mock | gerçek) --- #
    vad_backend: str = "energy"          # energy | silero
    stt_backend: str = "mock"            # mock | faster_whisper
    llm_backend: str = "mock"            # mock | vllm
    embedding_backend: str = "hash"      # hash | bge_m3
    vectordb_backend: str = "memory"     # memory | qdrant
    tts_backend: str = "mock"            # mock | xtts | piper

    # --- STT --- #
    whisper_model: str = "large-v3"
    whisper_device: str = "cuda"
    whisper_compute_type: str = "float16"
    stt_language: str = "tr"

    # --- LLM (vLLM OpenAI-uyumlu endpoint) --- #
    llm_base_url: str = "http://vllm:8000/v1"
    llm_api_key: str = "EMPTY"
    llm_model: str = "Qwen/Qwen2.5-7B-Instruct"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 512

    # --- Embedding --- #
    embedding_model: str = "BAAI/bge-m3"
    embedding_dim: int = 1024
    embedding_device: str = "cuda"

    # --- Vektör DB --- #
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "sohbet_kb"

    # --- TTS --- #
    xtts_model: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    tts_speaker_wav: str = "data/voices/tr_reference.wav"
    tts_language: str = "tr"
    piper_model: str = "tr_TR-dfki-medium"

    # --- RAG --- #
    chunk_size: int = 700
    chunk_overlap: int = 100
    retrieval_top_k: int = 5
    use_reranker: bool = False

    # --- Ses / VAD --- #
    sample_rate: int = 16000
    vad_frame_ms: int = 30
    vad_speech_threshold: float = 0.5
    # Barge-in için: SPEAKING sırasında kaç ardışık konuşma çerçevesi kesme sayılır.
    barge_in_frames: int = 3

    # --- Diyalog --- #
    system_prompt: str = (
        "Sen yardımcı bir Türkçe sesli asistansın. Kısa, akıcı ve doğal konuş. "
        "Sana verilen bağlamı kullanarak soruyu yanıtla. Bağlamda cevap yoksa "
        "bilmediğini dürüstçe söyle."
    )
    max_history_messages: int = 12

    # --- Sunucu --- #
    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "INFO"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
