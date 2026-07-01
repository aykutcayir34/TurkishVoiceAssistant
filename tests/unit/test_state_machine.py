from __future__ import annotations

import pytest

from sohbet.domain.state import InvalidTransition, TurnState, TurnStateMachine


def test_happy_path_transitions():
    sm = TurnStateMachine()
    assert sm.state is TurnState.IDLE
    sm.to(TurnState.LISTENING)
    sm.to(TurnState.THINKING)
    sm.to(TurnState.SPEAKING)
    sm.to(TurnState.IDLE)
    assert sm.state is TurnState.IDLE


def test_barge_in_transitions():
    sm = TurnStateMachine()
    sm.to(TurnState.LISTENING)
    sm.to(TurnState.THINKING)
    sm.to(TurnState.SPEAKING)
    # Barge-in: SPEAKING -> INTERRUPTED -> LISTENING
    sm.to(TurnState.INTERRUPTED)
    sm.to(TurnState.LISTENING)
    assert sm.state is TurnState.LISTENING


def test_illegal_transition_raises():
    sm = TurnStateMachine()
    with pytest.raises(InvalidTransition):
        sm.to(TurnState.SPEAKING)  # IDLE -> SPEAKING geçersiz


def test_same_state_noop():
    sm = TurnStateMachine()
    assert sm.to(TurnState.IDLE) is TurnState.IDLE


def test_transition_callback_fires():
    seen = []
    sm = TurnStateMachine(on_transition=lambda p, n: seen.append((p, n)))
    sm.to(TurnState.LISTENING)
    assert seen == [(TurnState.IDLE, TurnState.LISTENING)]


def test_is_busy():
    sm = TurnStateMachine()
    sm.to(TurnState.LISTENING)
    assert not sm.is_busy
    sm.to(TurnState.THINKING)
    assert sm.is_busy
    sm.to(TurnState.SPEAKING)
    assert sm.is_busy and sm.is_speaking
