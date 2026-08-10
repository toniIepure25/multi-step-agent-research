"""
Counterfactual Cognitive Policy Study — Phase 12.

Uses event-sourced state forking to evaluate alternative cognitive actions
from identical epistemic states. Builds a CognitiveActionOutcomeDataset
for studying Q(E_t, a) — the expected epistemic utility of cognitive
action 'a' in epistemic state E_t.

This is the central scientific contribution: learning the value of
different forms of cognition from the epistemic state.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from asar.common import generate_id
from asar.epistemic.reducer import StateReducer
from asar.epistemic.store import AppendOnlyEventStore
from asar.metacognition.controller import EpistemicController
from asar.operators.registry import OperatorRegistry
from asar.operators.stop import StopOperator
from schemas.ree.epistemic_event import (
    ActionType,
    EpistemicAction,
    EpistemicActionBid,
    EpistemicEvent,
    OperatorOutcome,
    OperatorResult,
)
from schemas.ree.epistemic_state import (
    BudgetState,
    EpistemicState,
    ResourceCost,
)
from schemas.ree.experiment import (
    CognitiveActionOutcome,
    CognitiveActionRegret,
    EpistemicStateFeatures,
    RealizedEpistemicGain,
)


# ---------------------------------------------------------------
# State feature extraction
# ---------------------------------------------------------------

def extract_state_features(state: EpistemicState) -> EpistemicStateFeatures:
    """Extract rich state features from an EpistemicState.

    Avoids leaking final outcomes into features.
    """
    recent_ops = state.operator_history[-5:] if state.operator_history else []

    belief_changes = []
    for snap in state.views.belief_trajectory:
        belief_changes.append(abs(snap.posterior - 0.5))
    volatility = (
        sum(belief_changes) / len(belief_changes) if belief_changes else 0.0
    )

    support = 0.0
    for hv in state.views.hypotheses.values():
        support += len(hv.supporting_evidence_ids) * 0.1
    if state.views.hypotheses:
        support /= len(state.views.hypotheses)

    return EpistemicStateFeatures(
        hypothesis_entropy=state.views.hypothesis_entropy,
        top_hypothesis_margin=state.views.top_hypothesis_margin,
        belief_volatility=volatility,
        support_strength=min(1.0, support),
        contradiction_density=state.views.contradiction_density,
        highest_ignorance_priority=state.views.highest_ignorance_priority,
        mean_ignorance_priority=state.views.mean_ignorance_priority,
        workspace_saturation=state.views.workspace_saturation,
        decision_stability=state.views.decision_stability,
        self_model_expected_success=state.views.self_model.overall_success_rate,
        budget_fraction=state.budget.budget_fraction_remaining,
        recent_operator_sequence=recent_ops,
        evidence_count=len(state.evidence_ids),
        hypothesis_count=len(state.views.hypotheses),
        claim_count=len(state.claim_ids),
        ignorance_count=len(state.views.ignorance_items),
        assumption_count=len(state.assumption_ids),
        step_count=state.process.step_count,
        state_version=state.version,
        episode_id=state.process.episode_id,
    )


# ---------------------------------------------------------------
# State forking and continuation
# ---------------------------------------------------------------

async def fork_and_execute(
    state: EpistemicState,
    operator: Any,
    *,
    continuation_budget: BudgetState | None = None,
) -> tuple[EpistemicState, ResourceCost]:
    """Fork from a state, execute a single operator action, return new state."""
    reducer = StateReducer()

    bids = await operator.propose(state)
    if not bids:
        return state, ResourceCost()

    action = bids[0].action
    result = await operator.execute(state, action)

    event = EpistemicEvent(
        event_id=generate_id("event"),
        episode_id=state.process.episode_id,
        version_before=state.version,
        version_after=state.version + 1,
        action=action,
        result=result,
        resource_cost=result.resource_cost,
    )

    new_state = reducer.apply(state, event)
    return new_state, result.resource_cost


def compute_realized_gain(
    state_before: EpistemicState,
    state_after: EpistemicState,
    cost: ResourceCost,
) -> RealizedEpistemicGain:
    """Compute the realized epistemic gain vector between two states."""
    hyp_before = len(state_before.views.hypotheses)
    hyp_after = len(state_after.views.hypotheses)

    entropy_before = state_before.views.hypothesis_entropy
    entropy_after = state_after.views.hypothesis_entropy

    ign_before = len([i for i in state_before.views.ignorance_items.values() if i.status == "open"])
    ign_after = len([i for i in state_after.views.ignorance_items.values() if i.status == "open"])

    evidence_before = len(state_before.evidence_ids)
    evidence_after = len(state_after.evidence_ids)

    claim_before = len(state_before.claim_ids)
    claim_after = len(state_after.claim_ids)

    task_quality = 0.0
    if evidence_after > evidence_before:
        task_quality += 0.2
    if claim_after > claim_before:
        task_quality += 0.3
    if hyp_after > hyp_before:
        task_quality += 0.1

    hypothesis_disc = 0.0
    if entropy_after != entropy_before:
        hypothesis_disc = min(0.5, abs(entropy_after - entropy_before) * 0.5)

    contra_before = len(state_before.contradiction_ids)
    contra_after = len(state_after.contradiction_ids)
    contra_resolution = max(0, contra_before - contra_after) * 0.2

    ign_reduction = max(0, ign_before - ign_after) * 0.15

    return RealizedEpistemicGain(
        task_quality_delta=task_quality,
        calibration_delta=0.0,
        hypothesis_discrimination_delta=hypothesis_disc,
        contradiction_resolution_delta=contra_resolution,
        ignorance_reduction_delta=ign_reduction,
        provenance_quality_delta=0.0,
        robustness_delta=0.0,
        compute_cost=cost.total_tokens / 1000.0,
    )


# ---------------------------------------------------------------
# CognitiveActionOutcomeDataset
# ---------------------------------------------------------------

class CognitiveActionOutcomeDataset:
    """Dataset of (state, action, outcome) records for cognitive policy study.

    Target: hundreds to thousands of observations from controlled scenarios.
    Maintains task-level train/test separation.
    """

    def __init__(self, *, path: Path | None = None) -> None:
        self._outcomes: list[CognitiveActionOutcome] = []
        self._path = path
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, outcome: CognitiveActionOutcome) -> None:
        self._outcomes.append(outcome)
        if self._path is not None:
            with self._path.open("a", encoding="utf-8") as f:
                f.write(outcome.model_dump_json() + "\n")

    def all(self) -> list[CognitiveActionOutcome]:
        return list(self._outcomes)

    def by_action(self, action_type: str) -> list[CognitiveActionOutcome]:
        return [o for o in self._outcomes if o.action_type == action_type]

    def by_episode(self, episode_id: str) -> list[CognitiveActionOutcome]:
        return [o for o in self._outcomes if o.episode_id == episode_id]

    def episode_ids(self) -> set[str]:
        return {o.episode_id for o in self._outcomes}

    def __len__(self) -> int:
        return len(self._outcomes)

    # ---------------------------------------------------------------
    # Analysis methods
    # ---------------------------------------------------------------

    def mean_gain_by_action(self, weights: dict[str, float] | None = None) -> dict[str, float]:
        """Average scalarized gain per action type."""
        totals: dict[str, float] = {}
        counts: dict[str, int] = {}
        for o in self._outcomes:
            s = o.realized_gain.scalarize(weights)
            totals[o.action_type] = totals.get(o.action_type, 0.0) + s
            counts[o.action_type] = counts.get(o.action_type, 0) + 1
        return {k: totals[k] / counts[k] for k in totals}

    def bid_vs_realized_correlation(self) -> float:
        """Rank correlation between bid scores and realized gains."""
        if len(self._outcomes) < 3:
            return 0.0

        bids = [o.bid_score for o in self._outcomes]
        gains = [o.realized_gain.scalarize() for o in self._outcomes]

        bid_ranks = _rank(bids)
        gain_ranks = _rank(gains)

        n = len(bid_ranks)
        d_sq_sum = sum((bid_ranks[i] - gain_ranks[i]) ** 2 for i in range(n))
        rho = 1.0 - (6.0 * d_sq_sum) / (n * (n * n - 1)) if n > 1 else 0.0
        return rho

    def action_confusion_matrix(self) -> dict[str, dict[str, int]]:
        """Which action types tend to co-occur in high vs low gain."""
        high_gain: dict[str, int] = {}
        low_gain: dict[str, int] = {}
        median = self._median_gain()

        for o in self._outcomes:
            s = o.realized_gain.scalarize()
            target = high_gain if s >= median else low_gain
            target[o.action_type] = target.get(o.action_type, 0) + 1

        return {"high_gain": high_gain, "low_gain": low_gain}

    def feature_importance_proxy(self) -> dict[str, float]:
        """Simple correlation between each state feature and realized gain.

        Uses absolute Spearman rank correlation as a proxy.
        """
        if len(self._outcomes) < 5:
            return {}

        gains = [o.realized_gain.scalarize() for o in self._outcomes]
        gain_ranks = _rank(gains)

        feature_names = [
            "hypothesis_entropy", "top_hypothesis_margin", "belief_volatility",
            "contradiction_density", "highest_ignorance_priority",
            "mean_ignorance_priority", "workspace_saturation",
            "budget_fraction", "evidence_count", "hypothesis_count",
            "step_count", "self_model_expected_success",
        ]

        importances: dict[str, float] = {}
        for fname in feature_names:
            values = [getattr(o.state_features, fname, 0.0) for o in self._outcomes]
            val_ranks = _rank(values)
            n = len(val_ranks)
            if n < 3:
                continue
            d_sq_sum = sum((val_ranks[i] - gain_ranks[i]) ** 2 for i in range(n))
            rho = 1.0 - (6.0 * d_sq_sum) / (n * (n * n - 1))
            importances[fname] = abs(rho)

        return dict(sorted(importances.items(), key=lambda x: x[1], reverse=True))

    def _median_gain(self) -> float:
        gains = sorted(o.realized_gain.scalarize() for o in self._outcomes)
        n = len(gains)
        if n == 0:
            return 0.0
        return gains[n // 2]


def _rank(values: list[float]) -> list[float]:
    """Compute ranks for a list of values (average ranks for ties)."""
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + j - 1) / 2.0 + 1.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j
    return ranks


# ---------------------------------------------------------------
# Counterfactual fork runner
# ---------------------------------------------------------------

class CounterfactualForkRunner:
    """Runs counterfactual forks from a given epistemic state.

    For each candidate operator, forks the state, executes the operator,
    measures realized epistemic gain, and records the outcome.
    """

    def __init__(
        self,
        *,
        dataset: CognitiveActionOutcomeDataset,
        continuation_budget: BudgetState | None = None,
    ) -> None:
        self._dataset = dataset
        self._cont_budget = continuation_budget or BudgetState(
            max_tokens=2000, max_steps=5,
        )

    async def run_fork(
        self,
        state: EpistemicState,
        operators: list[Any],
        *,
        selected_action: str | None = None,
        selected_bid_score: float = 0.0,
    ) -> list[CognitiveActionOutcome]:
        """Execute all candidate operators from the same state and record outcomes."""
        features = extract_state_features(state)
        outcomes: list[CognitiveActionOutcome] = []

        for operator in operators:
            try:
                new_state, cost = await fork_and_execute(state, operator)
            except Exception:
                continue

            if new_state.version == state.version:
                continue

            gain = compute_realized_gain(state, new_state, cost)

            outcome = CognitiveActionOutcome(
                outcome_id=generate_id("cao"),
                episode_id=state.process.episode_id,
                step=state.process.step_count,
                state_features=features,
                action_type=operator.name,
                operator_name=operator.name,
                bid_score=selected_bid_score if operator.name == selected_action else 0.0,
                realized_gain=gain,
                resource_cost_tokens=cost.total_tokens,
                continuation_budget_tokens=self._cont_budget.max_tokens,
            )
            self._dataset.add(outcome)
            outcomes.append(outcome)

        return outcomes

    def compute_regret(
        self,
        outcomes: list[CognitiveActionOutcome],
        selected_action: str,
        *,
        weights: dict[str, float] | None = None,
    ) -> CognitiveActionRegret | None:
        """Compute cognitive action regret from forked outcomes."""
        if not outcomes:
            return None

        gains_by_action = {
            o.action_type: o.realized_gain for o in outcomes
        }

        ep_id = outcomes[0].episode_id
        version = outcomes[0].state_features.state_version

        return CognitiveActionRegret.compute(
            fork_state_version=version,
            episode_id=ep_id,
            selected_action=selected_action,
            outcomes=gains_by_action,
            weights=weights,
        )
