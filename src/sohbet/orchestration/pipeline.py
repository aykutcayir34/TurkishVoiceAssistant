"""Bir konuşma turunun cancellable akışı: RAG → LLM → cümle böl → TTS.

``run_turn`` tek bir ``asyncio.Task`` içinde çalışır; barge-in bu task'ı iptal
eder. İptal edildiğinde LLM/TTS generator'ları ``async for`` üzerinden düzgünce
kapatılır (abort). "Gerçekten söylenen" metin (``spoken_so_far``) yalnızca
istemciye gönderilmiş TTS parçalarından toplanır (FR-10).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sohbet.domain.events import AssistantToken, TTSAudio, TurnEnd
from sohbet.domain.state import TurnState
from sohbet.logging import get_logger
from sohbet.rag.prompt import assemble_messages

if TYPE_CHECKING:
    from sohbet.orchestration.session import ConversationSession

logger = get_logger("sohbet.pipeline")

# Cümle sınırı: . ! ? … veya satır sonu.
_SENTENCE_RE = re.compile(r"[^.!?…\n]*[.!?…\n]")


def split_sentences(buffer: str) -> tuple[list[str], str]:
    """Tamamlanmış cümleleri ve kalan (yarım) metni döndürür."""
    sentences = []
    last_end = 0
    for m in _SENTENCE_RE.finditer(buffer):
        s = m.group().strip()
        if s:
            sentences.append(s)
        last_end = m.end()
    return sentences, buffer[last_end:]


async def _speak_sentence(session: ConversationSession, sentence: str) -> None:
    """Tek bir cümleyi sentezleyip istemciye gönderir; spoken_so_far'ı günceller.

    Asistan bir cümleyi seslendirmeye başladığı anda o cümle "söylenmekte olan"
    kabul edilir ve ``spoken_so_far``a eklenir; barge-in tam bu cümlenin
    ortasında gelse bile kullanıcı onu duymaya başlamıştır (PRD §4.2). Henüz
    seslendirilmeye başlanmamış (kuyruktaki) cümleler sayılmaz (FR-10).
    """
    if session.state.state is not TurnState.SPEAKING:
        session.state.to(TurnState.SPEAKING)
        session.metrics.mark("speak_start")
    session.spoken_so_far = (
        (session.spoken_so_far + " " + sentence).strip()
        if session.spoken_so_far
        else sentence
    )
    async for chunk in session.backends.tts.synthesize(sentence):
        await session.send(TTSAudio.from_pcm(chunk.data, chunk.sample_rate))
        if session.metrics.first_audio is None:
            session.metrics.mark("first_audio")


async def run_turn(session: ConversationSession) -> None:
    """Kullanıcının son mesajına RAG + LLM + TTS ile cevap üretir (cancellable)."""
    sm = session.state
    sm.to(TurnState.THINKING)
    session.spoken_so_far = ""

    query = session.memory.last_user_text() or ""
    chunks = await session.retriever.retrieve(query)
    logger.info("Retrieval: '%s' için %d parça", query[:40], len(chunks))

    history = session.memory.render_history(session.settings.max_history_messages)
    messages = assemble_messages(history, chunks)

    full_tokens: list[str] = []
    sentence_buf = ""
    # Generator'ı açıkça yönetiyoruz ki iptalde deterministik biçimde kapatıp
    # alttaki üretimi (vLLM abort) durdurabilelim.
    gen = session.backends.llm.generate(
        messages,
        temperature=session.settings.llm_temperature,
        max_tokens=session.settings.llm_max_tokens,
    )
    try:
        async for token in gen:
            if session.metrics.first_token is None:
                session.metrics.mark("first_token")
            full_tokens.append(token)
            await session.send(AssistantToken(text=token))
            sentence_buf += token
            sentences, sentence_buf = split_sentences(sentence_buf)
            for s in sentences:
                await _speak_sentence(session, s)

        if sentence_buf.strip():
            await _speak_sentence(session, sentence_buf.strip())
    finally:
        # İptal (barge-in) veya doğal bitişte generator'ı kapat → abort tetiklenir.
        await gen.aclose()

    # Doğal tamamlanma: tüm cevabı hafızaya yaz (kesilmedi).
    session.memory.add_assistant("".join(full_tokens))
    await session.send(TurnEnd(citations=[c.source for c in chunks]))
    session.metrics.log_summary()

    sm.to(TurnState.IDLE)
    session.current_task = None
