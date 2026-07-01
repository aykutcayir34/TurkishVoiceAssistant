"""Konuşma turu durum makinesi.

Saf ve senkron; hiçbir I/O yapmaz. Barge-in davranışının temelidir ve
kolayca unit test edilebilir (bkz. tests/unit/test_state_machine.py).

Geçiş diyagramı (PRD §7.2):

    IDLE ──► LISTENING ──► THINKING ──► SPEAKING ──► IDLE
              ▲                             │
              └──────── INTERRUPTED ◄───────┘  (barge-in)
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum


class TurnState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"


# İzin verilen geçişler. Her anahtar, o durumdan gidilebilecek durumları listeler.
_ALLOWED: dict[TurnState, frozenset[TurnState]] = {
    TurnState.IDLE: frozenset({TurnState.LISTENING}),
    TurnState.LISTENING: frozenset({TurnState.THINKING, TurnState.IDLE}),
    TurnState.THINKING: frozenset(
        {TurnState.SPEAKING, TurnState.INTERRUPTED, TurnState.IDLE}
    ),
    TurnState.SPEAKING: frozenset(
        {TurnState.IDLE, TurnState.INTERRUPTED, TurnState.LISTENING}
    ),
    # Barge-in sonrası: kesilen tur işlenip yeni girdi dinlenmeye başlanır.
    TurnState.INTERRUPTED: frozenset({TurnState.LISTENING, TurnState.IDLE}),
}


class InvalidTransition(RuntimeError):
    """Geçiş tablosunda tanımlı olmayan bir durum değişikliği denendi."""


TransitionCallback = Callable[[TurnState, TurnState], None]


class TurnStateMachine:
    """Tek bir oturumun konuşma turu durumunu yönetir."""

    def __init__(self, on_transition: TransitionCallback | None = None) -> None:
        self._state = TurnState.IDLE
        self._on_transition = on_transition

    @property
    def state(self) -> TurnState:
        return self._state

    def can(self, target: TurnState) -> bool:
        return target in _ALLOWED[self._state]

    def to(self, target: TurnState) -> TurnState:
        """Hedef duruma geç. Geçiş yasadışıysa :class:`InvalidTransition` fırlatır."""
        if target == self._state:
            return self._state
        if not self.can(target):
            raise InvalidTransition(f"{self._state.value} -> {target.value} geçersiz")
        previous, self._state = self._state, target
        if self._on_transition is not None:
            self._on_transition(previous, target)
        return self._state

    @property
    def is_speaking(self) -> bool:
        return self._state is TurnState.SPEAKING

    @property
    def is_busy(self) -> bool:
        """Asistan aktif olarak düşünüyor veya konuşuyor mu?"""
        return self._state in (TurnState.THINKING, TurnState.SPEAKING)

    def reset(self) -> None:
        self._state = TurnState.IDLE
