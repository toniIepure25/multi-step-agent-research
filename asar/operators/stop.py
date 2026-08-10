"""
Stop and Abstain operators — terminal cognitive actions for REE.

STOP: research is complete, produce final answer.
ABSTAIN: research cannot produce a reliable answer, decline.
"""

from __future__ import annotations

from asar.common import generate_id
from schemas.ree.epistemic_event import (
    ActionType,
    EpistemicAction,
    EpistemicActionBid,
    OperatorOutcome,
    OperatorResult,
)
from schemas.ree.epistemic_state import EpistemicState, ResourceCost


class StopOperator:
    """Proposes stopping the research episode when sufficient work is done."""

    @property
    def name(self) -> str:
        return "stop"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        if state.process.status != "active":
            return []

        bids: list[EpistemicActionBid] = []

        has_claims = len(state.claim_ids) > 0
        budget_low = state.budget.budget_fraction_remaining < 0.1
        has_synthesized = "synthesize" in state.operator_history

        stop_value = 0.0
        if budget_low:
            stop_value = 0.8
        elif has_claims and has_synthesized:
            stop_value = 0.4
        elif state.process.step_count > 10:
            stop_value = 0.5

        high_ignorance = state.views.highest_ignorance_priority > 0.5
        if high_ignorance and not budget_low:
            stop_value *= 0.5

        if stop_value > 0.1:
            reason = "budget exhausted" if budget_low else "sufficient work completed"
            bids.append(EpistemicActionBid(
                action=EpistemicAction(
                    action_id=generate_id("action"),
                    action_type=ActionType.STOP,
                    operator_name=self.name,
                    parameters={"reason": reason},
                    description=f"Stop research: {reason}",
                ),
                expected_information_gain=stop_value,
                probability_changes_decision=0.0,
                estimated_token_cost=0,
                rationale=f"Stop (value={stop_value:.2f}, high_ignorance={high_ignorance})",
            ))

        return bids

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        return OperatorResult(
            operator_name=self.name,
            action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS,
            resource_cost=ResourceCost(),
            notes=action.parameters.get("reason", "stop requested"),
        )


class AbstainOperator:
    """Proposes abstaining when the research cannot produce a reliable answer."""

    @property
    def name(self) -> str:
        return "abstain"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        if state.process.status != "active":
            return []

        no_evidence = len(state.evidence_ids) == 0 and state.process.step_count > 3
        if not no_evidence:
            return []

        return [EpistemicActionBid(
            action=EpistemicAction(
                action_id=generate_id("action"),
                action_type=ActionType.ABSTAIN,
                operator_name=self.name,
                parameters={"reason": "insufficient evidence after multiple attempts"},
                description="Abstain: cannot produce reliable answer",
            ),
            expected_information_gain=0.0,
            probability_changes_decision=0.0,
            estimated_token_cost=0,
            rationale="No evidence gathered despite multiple attempts — abstaining",
        )]

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        return OperatorResult(
            operator_name=self.name,
            action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS,
            resource_cost=ResourceCost(),
            notes=action.parameters.get("reason", "abstain requested"),
        )
