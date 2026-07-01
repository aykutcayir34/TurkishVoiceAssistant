"""Üretken dil modeli (LLM) sözleşmesi — sistemin en kritik arayüzü.

İptal (cancellation) sözleşmesi barge-in'in temelidir:

* ``generate`` bir async generator döndürür; token'lar geldikçe yield edilir.
* Tüketici (pipeline) turu iptal ettiğinde generator ``GeneratorExit`` /
  ``asyncio.CancelledError`` alır ve ``finally`` bloğunda alttaki üretimi
  durdurmalıdır (ör. vLLM'e abort isteği göndermek). Bu blok
  ``asyncio.shield`` ile korunmalı ki abort'un kendisi yarıda kesilmesin.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class LLMBackend(ABC):
    @abstractmethod
    def generate(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> AsyncIterator[str]:
        """Sohbet mesajlarından token akışı üret (streaming).

        ``messages`` OpenAI-uyumlu ``{"role", "content"}`` listesidir ve
        getirilen RAG bağlamını içeren system/user mesajlarını barındırır.
        Dönen generator iptal edilebilir olmalıdır.
        """
        raise NotImplementedError
