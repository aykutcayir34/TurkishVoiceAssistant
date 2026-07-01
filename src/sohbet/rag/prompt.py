"""Türkçe RAG prompt kurulumu (PRD §9.3).

Getirilen bağlamı bir system mesajına yerleştirir; konuşma geçmişi ayrı mesajlar
olarak korunur (böylece kesme/hafıza yapısı doğal biçimde LLM'e geçer).
"""

from __future__ import annotations

from sohbet.domain.types import RetrievedChunk

_CONTEXT_TEMPLATE = """[BAĞLAM]
{context}

Yukarıdaki bağlamı kullanarak kullanıcının sorusunu Türkçe, kısa ve akıcı yanıtla.
Bağlamda cevap yoksa bunu dürüstçe belirt."""


def build_context_message(chunks: list[RetrievedChunk]) -> dict[str, str] | None:
    """Getirilen parçalardan bir system bağlam mesajı üretir (yoksa None)."""
    if not chunks:
        return None
    context = "\n\n".join(f"[{i + 1}] ({c.source}) {c.text}" for i, c in enumerate(chunks))
    return {"role": "system", "content": _CONTEXT_TEMPLATE.format(context=context)}


def assemble_messages(
    base_history: list[dict[str, str]], chunks: list[RetrievedChunk]
) -> list[dict[str, str]]:
    """Sohbet geçmişine RAG bağlamını enjekte edilmiş mesaj listesi döndürür.

    Bağlam mesajı, son kullanıcı mesajından hemen önce eklenir ki model bağlamı
    soruyla ilişkilendirebilsin.
    """
    context_msg = build_context_message(chunks)
    if context_msg is None:
        return list(base_history)

    # Son 'user' mesajının indeksini bul.
    last_user = None
    for i in range(len(base_history) - 1, -1, -1):
        if base_history[i]["role"] == "user":
            last_user = i
            break
    if last_user is None:
        return [*base_history, context_msg]
    return [*base_history[:last_user], context_msg, *base_history[last_user:]]
