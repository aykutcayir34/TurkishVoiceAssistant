"""Soyut backend sözleşmeleri (plug noktaları).

Bu modül hiçbir ağır kütüphane import etmez. Gerçek backend'ler kendi
ağır bağımlılıklarını modül gövdesinde değil, örnek oluşturulurken
(lazy-import) yükler; böylece GPU/ML paketleri kurulu olmasa bile mock
backend'lerle sistem çalışır.
"""

from sohbet.interfaces.embedding import EmbeddingBackend
from sohbet.interfaces.llm import LLMBackend
from sohbet.interfaces.stt import STTBackend
from sohbet.interfaces.tts import TTSBackend
from sohbet.interfaces.vad import VADBackend
from sohbet.interfaces.vectordb import Hit, VectorDBBackend, VectorPoint

__all__ = [
    "EmbeddingBackend",
    "LLMBackend",
    "STTBackend",
    "TTSBackend",
    "VADBackend",
    "VectorDBBackend",
    "VectorPoint",
    "Hit",
]
