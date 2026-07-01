"""Konuşma hafızası (kısa süreli bağlam).

Barge-in senaryosunda kesilen asistan cevabının **yalnızca sesli söylenmiş kısmı**
``[kesildi]`` önekiyle kaydedilir (PRD §10, FR-10). Böylece model bir sonraki turda
neyin yarım kaldığını bilir ve yeni bağlamla tutarlı cevap üretir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Role = Literal["system", "user", "assistant"]

INTERRUPTED_PREFIX = "[kesildi] "


@dataclass(slots=True)
class Message:
    role: Role
    content: str
    interrupted: bool = False

    def to_dict(self) -> dict[str, str]:
        """LLM sohbet formatına (OpenAI-uyumlu) dönüştür."""
        return {"role": self.role, "content": self.content}


class ConversationMemory:
    """Bir oturumun mesaj geçmişini tutar.

    Token bütçesi aşılırsa en eski mesajlar (system hariç) düşürülür; gerçek
    özetleme Faz 3'te ``summarize_hook`` üzerinden takılabilir.
    """

    def __init__(self, system_prompt: str | None = None) -> None:
        self._messages: list[Message] = []
        if system_prompt:
            self._messages.append(Message(role="system", content=system_prompt))

    def add_user(self, text: str) -> None:
        self._messages.append(Message(role="user", content=text))

    def add_assistant(self, text: str, interrupted: bool = False) -> None:
        """Asistan cevabını ekle.

        ``interrupted=True`` ise (barge-in) metin ``[kesildi]`` önekiyle yazılır;
        boş metin (hiç ses söylenmeden kesildi) hiç eklenmez.
        """
        text = text.strip()
        if interrupted:
            if not text:
                return
            text = INTERRUPTED_PREFIX + text
        self._messages.append(Message(role="assistant", content=text, interrupted=interrupted))

    @property
    def messages(self) -> list[Message]:
        return list(self._messages)

    def render_history(self, max_messages: int | None = None) -> list[dict[str, str]]:
        """LLM'e verilecek sohbet geçmişini üret.

        ``max_messages`` verilirse system mesajı korunarak son N mesaj döndürülür.
        """
        msgs = self._messages
        if max_messages is not None and len(msgs) > max_messages:
            system = [m for m in msgs if m.role == "system"]
            rest = [m for m in msgs if m.role != "system"][-max_messages:]
            msgs = system + rest
        return [m.to_dict() for m in msgs]

    def last_user_text(self) -> str | None:
        for m in reversed(self._messages):
            if m.role == "user":
                return m.content
        return None

    def clear(self) -> None:
        system = [m for m in self._messages if m.role == "system"]
        self._messages = system
