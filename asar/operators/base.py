"""
Base protocol for cognitive operators in the REE architecture.

Operators propose actions and execute them, returning typed results.
They never mutate EpistemicState directly.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from schemas.ree.epistemic_event import EpistemicAction, EpistemicActionBid, OperatorResult
from schemas.ree.epistemic_state import EpistemicState


@runtime_checkable
class CognitiveOperator(Protocol):
    """
    Protocol for all cognitive operators in the REE architecture.

    Operators propose candidate actions (bids) and execute selected actions.
    They return typed OperatorResult — they never mutate state directly.
    """

    @property
    def name(self) -> str:
        """Unique name identifying this operator."""
        ...

    async def propose(
        self,
        state: EpistemicState,
    ) -> list[EpistemicActionBid]:
        """
        Given the current epistemic state, propose candidate actions.

        Returns a list of bids — the metacognitive controller will select among them.
        May return an empty list if this operator has nothing useful to propose.
        """
        ...

    async def execute(
        self,
        state: EpistemicState,
        action: EpistemicAction,
    ) -> OperatorResult:
        """
        Execute a selected action and return a typed result.

        The operator MUST NOT mutate state. It returns an OperatorResult
        containing any new/modified artifacts and workspace changes.
        The reducer applies these to produce the next state.
        """
        ...
