"""
Stopping policy — first-class decision about whether to continue, stop, abstain,
or return partial results.

Uses: remaining ignorance, expected value of additional cognition,
confidence calibration, budget, hypothesis entropy, marginal cost.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from schemas.ree.epistemic_state import EpistemicState


class StoppingDecision(str, Enum):
    CONTINUE = "continue"
    STOP = "stop"
    ABSTAIN = "abstain"
    RETURN_PARTIAL = "return_partial"


@dataclass(frozen=True)
class StoppingSignals:
    """Aggregated signals for the stopping decision."""

    budget_fraction_remaining: float
    hypothesis_count: int
    claim_count: int
    evidence_count: int
    ignorance_count: int
    contradiction_count: int
    has_synthesized: bool
    step_count: int
    unresolved_impact: float


@dataclass(frozen=True)
class StoppingReason:
    """Typed reason for a stopping decision."""

    decision: StoppingDecision
    reason: str
    confidence: float


class StoppingPolicy:
    """Decides whether the research episode should continue or terminate."""

    def __init__(
        self,
        *,
        min_evidence: int = 1,
        min_steps_before_stop: int = 2,
        budget_exhaustion_threshold: float = 0.05,
        ignorance_impact_threshold: float = 0.3,
    ) -> None:
        self._min_evidence = min_evidence
        self._min_steps = min_steps_before_stop
        self._budget_threshold = budget_exhaustion_threshold
        self._ignorance_threshold = ignorance_impact_threshold

    def extract_signals(self, state: EpistemicState) -> StoppingSignals:
        """Extract stopping-relevant signals from the current state."""
        ignorance_impact = 0.0
        for iid in state.ignorance_ids:
            artifact = state.artifacts.get(iid, {})
            if isinstance(artifact, dict):
                ignorance_impact += artifact.get("impact_if_resolved", 0.0)

        return StoppingSignals(
            budget_fraction_remaining=state.budget.budget_fraction_remaining,
            hypothesis_count=len(state.hypothesis_ids),
            claim_count=len(state.claim_ids),
            evidence_count=len(state.evidence_ids),
            ignorance_count=len(state.ignorance_ids),
            contradiction_count=len(state.contradiction_ids),
            has_synthesized="synthesize" in state.operator_history,
            step_count=state.process.step_count,
            unresolved_impact=ignorance_impact,
        )

    def evaluate(self, state: EpistemicState) -> StoppingReason:
        """Evaluate whether to stop, continue, abstain, or return partial."""
        signals = self.extract_signals(state)

        if state.budget.is_exhausted:
            if signals.claim_count > 0:
                return StoppingReason(StoppingDecision.STOP, "budget exhausted with claims available", 0.9)
            return StoppingReason(StoppingDecision.RETURN_PARTIAL, "budget exhausted, insufficient claims", 0.8)

        if signals.budget_fraction_remaining < self._budget_threshold:
            return StoppingReason(StoppingDecision.STOP, "budget nearly exhausted", 0.8)

        if signals.step_count < self._min_steps:
            return StoppingReason(StoppingDecision.CONTINUE, "below minimum steps", 0.9)

        if signals.evidence_count < self._min_evidence:
            if signals.step_count > 5:
                return StoppingReason(StoppingDecision.ABSTAIN, "no evidence after multiple attempts", 0.7)
            return StoppingReason(StoppingDecision.CONTINUE, "need more evidence", 0.8)

        if signals.has_synthesized and signals.claim_count > 0:
            if signals.unresolved_impact < self._ignorance_threshold:
                return StoppingReason(StoppingDecision.STOP, "sufficient work, low remaining ignorance impact", 0.7)
            if signals.contradiction_count == 0:
                return StoppingReason(StoppingDecision.STOP, "claims produced, no contradictions", 0.6)

        return StoppingReason(StoppingDecision.CONTINUE, "more work potentially valuable", 0.5)
