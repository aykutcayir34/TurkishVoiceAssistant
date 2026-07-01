"""vLLM (OpenAI-uyumlu) gerçek LLM backend.

Cancellation sözleşmesi: async stream ``finally`` bloğunda kapatılır; bağlantı
kapandığında vLLM sunucusu üretimi durdurur. Kapatma ``asyncio.shield`` ile
korunur ki iptal sırasında temizlik yarıda kalmasın.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from sohbet.interfaces.llm import LLMBackend
from sohbet.logging import get_logger

logger = get_logger("sohbet.llm.vllm")


class VLLMBackend(LLMBackend):
    def __init__(
        self,
        base_url: str,
        api_key: str = "EMPTY",
        model: str = "Qwen/Qwen2.5-7B-Instruct",
    ) -> None:
        from openai import AsyncOpenAI  # lazy

        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self._model = model

    async def generate(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        try:
            async for event in stream:
                delta = event.choices[0].delta.content
                if delta:
                    yield delta
        finally:
            # İptal edilirse bağlantıyı düzgünce kapat -> vLLM üretimi durdurur.
            await asyncio.shield(_safe_close(stream))


async def _safe_close(stream) -> None:
    try:
        await stream.close()
    except Exception as exc:  # noqa: BLE001
        logger.debug("vLLM stream kapatılırken hata (yok sayıldı): %s", exc)
