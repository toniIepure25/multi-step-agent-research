"""
Epistemic metrics — scientific measurement infrastructure for REE.

Computes metrics beyond answer accuracy: calibration, ignorance foresight,
minority preservation, evidence independence, counterfactual robustness,
belief revision quality, and more.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EpistemicMetricsResult:
    """Typed container for all computed epistemic metrics."""

    brier_score: float | None = None
    expected_calibration_error: float | None = None
    self_model_calibration_error: float | None = None
    ignorance_foresight_score: float | None = None
    minority_preservation_rate: float | None = None
    evidence_independence_score: float | None = None
    disconfirmation_yield: float | None = None
    belief_revision_quality: float | None = None
    counterfactual_robustness: float | None = None
    counterfactual_responsiveness: float | None = None
    assumption_sensitivity_precision: float | None = None
    hypothesis_diversity: float | None = None
    ontology_escape_rate: float | None = None
    total_tokens: int = 0
    total_steps: int = 0
    total_cost_usd: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


class EpistemicMetrics:
    """Computes epistemic metrics from episode data."""

    def ignorance_foresight_score(
        self,
        anticipated_failure_causes: list[str],
        actual_failure_causes: list[str],
        severity_weights: dict[str, float] | None = None,
    ) -> float:
        """Measure whether pre-answer ignorance items predicted actual failure causes.

        = (failure causes anticipated in advance) / (total observed failure causes)
        """
        if not actual_failure_causes:
            return 1.0

        weights = severity_weights or {}
        anticipated_set = set(anticipated_failure_causes)

        weighted_anticipated = 0.0
        weighted_total = 0.0
        for cause in actual_failure_causes:
            w = weights.get(cause, 1.0)
            weighted_total += w
            if cause in anticipated_set:
                weighted_anticipated += w

        return weighted_anticipated / weighted_total if weighted_total > 0 else 0.0

    def disconfirmation_yield(
        self,
        hypotheses_attacked: int,
        hypotheses_rejected: int,
        attack_compute_tokens: int,
    ) -> float:
        """False hypotheses eliminated per unit of compute spent attacking.

        = hypotheses_rejected / (attack_compute_tokens / 1000)
        """
        if attack_compute_tokens == 0:
            return 0.0
        return hypotheses_rejected / (attack_compute_tokens / 1000.0)

    def belief_revision_quality(
        self,
        revisions: list[tuple[float, float, bool]],
    ) -> float:
        """Measure whether belief moves appropriately after evidence.

        Each revision is (delta_posterior, evidence_strength, evidence_supports).
        Quality = fraction of revisions where direction matches evidence.
        """
        if not revisions:
            return 1.0
        correct = 0
        for delta, strength, supports in revisions:
            if supports and delta > 0:
                correct += 1
            elif not supports and delta < 0:
                correct += 1
            elif abs(delta) < 0.01:
                correct += 1
        return correct / len(revisions)

    def research_efficiency(
        self,
        quality_score: float,
        total_tokens: int,
    ) -> float:
        """Quality per kilotoken."""
        if total_tokens == 0:
            return 0.0
        return quality_score / (total_tokens / 1000.0)

    def paradigm_revision_score(
        self,
        dominant_hypothesis_abandoned: bool,
        new_hypothesis_adopted: bool,
        evidence_justified: bool,
    ) -> float:
        """Ability to abandon a once-dominant hypothesis after decisive anomalies."""
        score = 0.0
        if dominant_hypothesis_abandoned:
            score += 0.4
        if new_hypothesis_adopted:
            score += 0.3
        if evidence_justified:
            score += 0.3
        return score

    def compute_all(
        self,
        *,
        brier_score: float | None = None,
        ece: float | None = None,
        smce: float | None = None,
        anticipated_failures: list[str] | None = None,
        actual_failures: list[str] | None = None,
        mpr: float | None = None,
        eis: float | None = None,
        robustness: float | None = None,
        responsiveness: float | None = None,
        hypothesis_diversity: float | None = None,
        total_tokens: int = 0,
        total_steps: int = 0,
        total_cost_usd: float = 0.0,
    ) -> EpistemicMetricsResult:
        """Aggregate all available metrics into a single result."""
        ifs = None
        if anticipated_failures is not None and actual_failures is not None:
            ifs = self.ignorance_foresight_score(anticipated_failures, actual_failures)

        return EpistemicMetricsResult(
            brier_score=brier_score,
            expected_calibration_error=ece,
            self_model_calibration_error=smce,
            ignorance_foresight_score=ifs,
            minority_preservation_rate=mpr,
            evidence_independence_score=eis,
            counterfactual_robustness=robustness,
            counterfactual_responsiveness=responsiveness,
            hypothesis_diversity=hypothesis_diversity,
            total_tokens=total_tokens,
            total_steps=total_steps,
            total_cost_usd=total_cost_usd,
        )
