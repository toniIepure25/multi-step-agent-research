"""
Active Experiment Designer — identifies evidence or experiments with
high expected discriminatory value.

Prefers observations whose possible outcomes differ strongly across
competing hypotheses rather than collecting more generic information.
"""

from __future__ import annotations

from asar.common import generate_id
from schemas.ree.ontology import ExperimentCandidate


class ExperimentDesigner:
    """Designs experiments that maximize information gain and discrimination."""

    def __init__(self) -> None:
        self._candidates: list[ExperimentCandidate] = []

    def propose_experiment(
        self,
        description: str,
        target_hypotheses: list[str],
        expected_information_gain: float = 0.5,
        discrimination_power: float = 0.5,
        falsification_value: float = 0.5,
        estimated_cost: float = 0.5,
        feasibility: float = 0.5,
        risk: float = 0.1,
    ) -> ExperimentCandidate:
        """Create and register an experiment candidate."""
        priority = self._compute_priority(
            expected_information_gain,
            discrimination_power,
            falsification_value,
            estimated_cost,
            feasibility,
            risk,
        )
        candidate = ExperimentCandidate(
            experiment_id=generate_id("experiment"),
            description=description,
            target_hypotheses=target_hypotheses,
            expected_information_gain=expected_information_gain,
            discrimination_power=discrimination_power,
            falsification_value=falsification_value,
            estimated_cost=estimated_cost,
            feasibility=feasibility,
            risk=risk,
            priority_score=priority,
        )
        self._candidates.append(candidate)
        return candidate

    def ranked_candidates(self) -> list[ExperimentCandidate]:
        """Return experiments sorted by priority (descending)."""
        return sorted(self._candidates, key=lambda c: c.priority_score, reverse=True)

    def best_candidate(self) -> ExperimentCandidate | None:
        """Return the highest-priority experiment."""
        ranked = self.ranked_candidates()
        return ranked[0] if ranked else None

    def all_candidates(self) -> list[ExperimentCandidate]:
        return list(self._candidates)

    def _compute_priority(
        self,
        info_gain: float,
        discrimination: float,
        falsification: float,
        cost: float,
        feasibility: float,
        risk: float,
    ) -> float:
        """Compute experiment priority score.

        Approximately: (info_gain + discrimination + falsification) * feasibility / (cost + risk)
        """
        value = 0.4 * info_gain + 0.35 * discrimination + 0.25 * falsification
        denominator = max(0.01, 0.5 * cost + 0.5 * risk)
        return value * feasibility / denominator
