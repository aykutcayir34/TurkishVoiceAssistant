from __future__ import annotations

from sohbet.domain.memory import INTERRUPTED_PREFIX, ConversationMemory


def test_basic_history():
    m = ConversationMemory(system_prompt="sistem")
    m.add_user("selam")
    m.add_assistant("merhaba")
    rendered = m.render_history()
    assert rendered[0] == {"role": "system", "content": "sistem"}
    assert rendered[1] == {"role": "user", "content": "selam"}
    assert rendered[2] == {"role": "assistant", "content": "merhaba"}


def test_interrupted_prefix():
    m = ConversationMemory()
    m.add_assistant("Ankara için yarın parçalı bulutlu", interrupted=True)
    assert m.messages[-1].content.startswith(INTERRUPTED_PREFIX)
    assert m.messages[-1].interrupted is True


def test_empty_interrupted_not_recorded():
    m = ConversationMemory()
    m.add_assistant("", interrupted=True)
    assert len(m.messages) == 0


def test_history_truncation_keeps_system():
    m = ConversationMemory(system_prompt="sistem")
    for i in range(20):
        m.add_user(f"soru {i}")
        m.add_assistant(f"cevap {i}")
    rendered = m.render_history(max_messages=4)
    assert rendered[0]["role"] == "system"
    assert len(rendered) == 5  # system + son 4
    assert rendered[-1]["content"] == "cevap 19"


def test_last_user_text():
    m = ConversationMemory()
    m.add_user("ilk")
    m.add_assistant("yanıt")
    m.add_user("son")
    assert m.last_user_text() == "son"
