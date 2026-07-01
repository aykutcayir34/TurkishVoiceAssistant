from __future__ import annotations

import pytest

from sohbet.rag.chunking import chunk_text
from sohbet.rag.prompt import assemble_messages
from sohbet.domain.types import RetrievedChunk


def test_chunking_overlap():
    words = " ".join(f"w{i}" for i in range(100))
    chunks = chunk_text(words, chunk_size=30, overlap=10)
    assert len(chunks) >= 3
    # Örtüşme: 1. parçanın sonu ile 2. parçanın başı kesişmeli.
    first_words = chunks[0].text.split()
    second_words = chunks[1].text.split()
    assert first_words[-1] in second_words


def test_chunking_empty():
    assert chunk_text("") == []


def test_chunking_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text("a b c", chunk_size=5, overlap=5)


def test_prompt_injects_context_before_last_user():
    history = [
        {"role": "system", "content": "sistem"},
        {"role": "user", "content": "iade nasıl yapılır"},
    ]
    chunks = [RetrievedChunk(text="14 gün içinde iade", source="kb.md", score=0.9)]
    msgs = assemble_messages(history, chunks)
    # Bağlam mesajı son user'dan önce gelmeli.
    roles = [m["role"] for m in msgs]
    assert roles == ["system", "system", "user"]
    assert "BAĞLAM" in msgs[1]["content"]


def test_prompt_no_context():
    history = [{"role": "user", "content": "selam"}]
    assert assemble_messages(history, []) == history
