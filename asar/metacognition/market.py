"""
Epistemic Market — Level 1 heuristic scheduler.

Evaluates competing bids from operators and selects the action
with highest estimated net epistemic utility.

Includes DiversityAwareMarket variant that penalizes repeated selection
of the same operator family (Phase 15 intervention).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from schemas.ree.epistemic_event import EpistemicActionBid, EpistemicDecision
from schemas.ree.epistemic_state import EpistemicState


@dataclass(frozen=True)
class MarketWeights:
    """Configurable weights for the heuristic bid evaluation."""

    information_gain: float = 0.25
    decision_change: float = 0.20
    falsification: float = 0.15
    novelty: float = 0.10
    uncertainty_reduction: float = 0.15
    calibration_gain: float = 0.05
    token_cost_penalty: float = 0.05
    failure_risk_penalty: float = 0.05


class EpistemicMarket:
    """Level 1 heuristic scheduler for cognitive action selection."""

    def __init__(self, weights: MarketWeights | None = None) -> None:
        self._weights = weights or MarketWeights()

    def evaluate_bid(self, bid: EpistemicActionBid, state: EpistemicState) -> float:
        """Score a single bid given the current state."""
        w = self._weights

        value = (
            w.information_gain * bid.expected_information_gain
            + w.decision_change * bid.probability_changes_decision
            + w.falsification * bid.expected_falsification_value
            + w.novelty * bid.novelty_gain
            + w.uncertainty_reduction * bid.expected_uncertainty_reduction
            + w.calibration_gain * bid.expected_calibration_gain
        )

        budget_fraction = state.budget.budget_fraction_remaining
        token_cost_normalized = min(1.0, bid.estimated_token_cost / max(1, state.budget.tokens_remaining))
        cost = (
            w.token_cost_penalty * token_cost_normalized
            + w.failure_risk_penalty * bid.failure_risk
        )

        if budget_fraction < 0.2:
            cost *= 2.0

        return value - cost

    def select(
        self,
        bids: list[EpistemicActionBid],
        state: EpistemicState,
    ) -> EpistemicDecision | None:
        """Select the best action from competing bids."""
        if not bids:
            return None

        scored = [(bid, self.evaluate_bid(bid, state)) for bid in bids]
        scored.sort(key=lambda x: x[1], reverse=True)

        best_bid, best_score = scored[0]
        competing = [bid for bid, _ in scored[1:]]

        return EpistemicDecision(
            selected_bid=best_bid,
            competing_bids=competing,
            selection_score=best_score,
            selection_rationale=f"Highest net epistemic utility: {best_score:.4f}",
        )


class DiversityAwareMarket(EpistemicMarket):
    """Market with diversity penalty for repeated operator selection.

    Penalizes selecting the same operator consecutively. The penalty
    grows with the number of consecutive selections of the same operator.
    """

    def __init__(
        self,
        weights: MarketWeights | None = None,
        *,
        diversity_penalty: float = 0.15,
        consecutive_decay: float = 0.5,
    ) -> None:
        super().__init__(weights)
        self._diversity_penalty = diversity_penalty
        self._consecutive_decay = consecutive_decay

    def select(
        self,
        bids: list[EpistemicActionBid],
        state: EpistemicState,
    ) -> EpistemicDecision | None:
        if not bids:
            return None

        recent_ops = state.operator_history[-5:] if state.operator_history else []
        recent_counts = Counter(recent_ops)

        scored: list[tuple[EpistemicActionBid, float]] = []
        for bid in bids:
            base_score = self.evaluate_bid(bid, state)
            op_name = bid.action.operator_name

            consecutive = 0
            for past_op in reversed(recent_ops):
                if past_op == op_name:
                    consecutive += 1
                else:
                    break

            penalty = self._diversity_penalty * consecutive * self._consecutive_decay
            adjusted_score = base_score - penalty
            scored.append((bid, adjusted_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        best_bid, best_score = scored[0]
        competing = [bid for bid, _ in scored[1:]]

        return EpistemicDecision(
            selected_bid=best_bid,
            competing_bids=competing,
            selection_score=best_score,
            selection_rationale=f"Diversity-aware selection: {best_score:.4f}",
        )


class RoundRobinMarket:
    """Non-market baseline: cycles through operators in fixed order.

    Used as the ablation condition for epistemic_market=False.
    """

    def __init__(self) -> None:
        self._call_count = 0

    def evaluate_bid(self, bid: EpistemicActionBid, state: EpistemicState) -> float:
        return 0.0

    def select(
        self,
        bids: list[EpistemicActionBid],
        state: EpistemicState,
    ) -> EpistemicDecision | None:
        if not bids:
            return None

        idx = self._call_count % len(bids)
        self._call_count += 1

        selected = bids[idx]
        competing = [b for i, b in enumerate(bids) if i != idx]

        return EpistemicDecision(
            selected_bid=selected,
            competing_bids=competing,
            selection_score=0.0,
            selection_rationale="Round-robin selection",
        )
