"""Mock LLM.

Token'ları bir zamanlayıcıyla (yavaşça) üretir; bu sayede barge-in testleri
üretim ortasında kesme yapabilir. İptal edildiğinde ``finally`` bloğu çalışır
ve "abort" davranışını simüle eder.

Basit bir sahte cevap kuralı: getirilen bağlamı (varsa) yansıtır, yoksa genel
bir cevap üretir. Bu, mimariyi test etmek için yeterlidir.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from sohbet.interfaces.llm import LLMBackend
from sohbet.logging import get_logger

logger = get_logger("sohbet.llm.mock")


class MockLLM(LLMBackend):
    def __init__(self, token_delay: float = 0.05, reply: str | None = None) -> None:
        self._token_delay = token_delay
        self._reply = reply
        self.aborted = False  # test gözlemi için

    def _compose_reply(self, messages: list[dict[str, str]]) -> str:
        if self._reply is not None:
            return self._reply
        user = ""
        context = ""
        for m in messages:
            if m["role"] == "user":
                user = m["content"]
            if m["role"] == "system" and "[BAĞLAM]" in m["content"]:
                context = m["content"]
        if context.strip():
            return "Bağlama göre kısaca cevaplıyorum: bu konuda elimdeki bilgi bu şekilde."
        return f"Anladım, '{user[:40]}' hakkında yardımcı olayım. İşte kısa cevabım."

    async def generate(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> AsyncIterator[str]:
        reply = self._compose_reply(messages)
        tokens = reply.split(" ")
        try:
            for i, tok in enumerate(tokens):
                await asyncio.sleep(self._token_delay)  # iptal edilebilir nokta
                yield (tok if i == 0 else " " + tok)
        finally:
            # Gerçek backend'de burada vLLM'e abort gönderilirdi.
            self.aborted = True
            logger.debug("MockLLM üretimi sonlandı/iptal edildi (abort simülasyonu)")
