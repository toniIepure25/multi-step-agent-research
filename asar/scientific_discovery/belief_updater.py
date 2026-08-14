"""
Belief Updater — quantitative belief revision for the Scientific Discovery Engine.

Uses Bayesian-inspired updating with calibrated heuristics where exact
likelihoods are unknown. The key requirement is:

    EVIDENCE MUST CAUSE EXPLICIT BELIEF CHANGE.

Does not pretend to perform exact Bayesian inference. Uses likelihood-ratio
approximation with reliability and independence weighting.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from asar.scientific_discovery.state import (
    BeliefState,
    EvidenceDirection,
    HypothesisEcology,
    HypothesisStatus,
    ScientificEvidence,
    StructuredHypothesis,
)


@dataclass
class BeliefUpdateResult:
    """Result of a belief update operation."""

    hypothesis_id: str
    prior: float
    posterior: float
    magnitude: float
    evidence_id: str
    rationale: str


class BeliefUpdater:
    """
    Performs quantitative belief revision.

    Principles:
    - Decisive falsification should produce large belief drops
    - Duplicate evidence from same source should NOT double confidence
    - Irrelevant evidence should minimally affect beliefs
    - Supporting evidence should increase belief proportionally to reliability and independence
    """

    def __init__(
        self,
        *,
        base_update_strength: float = 0.3,
        reliability_weight: float = 0.8,
        independence_weight: float = 0.7,
        falsification_multiplier: float = 2.0,
        max_single_update: float = 0.4,
        abandonment_threshold: float = 0.1,
        rescue_penalty_per_assumption: float = 0.05,
    ) -> None:
        self._base_strength = base_update_strength
        self._reliability_weight = reliability_weight
        self._independence_weight = independence_weight
        self._falsification_mult = falsification_multiplier
        self._max_update = max_single_update
        self._abandonment_threshold = abandonment_threshold
        self._rescue_penalty = rescue_penalty_per_assumption

    @property
    def abandonment_threshold(self) -> float:
        return self._abandonment_threshold

    def update_belief(
        self,
        hypothesis: StructuredHypothesis,
        evidence: ScientificEvidence,
        current_belief: float,
        independence_score: float = 1.0,
    ) -> BeliefUpdateResult:
        """
        Update belief in a hypothesis given new evidence.

        The update uses a simplified likelihood-ratio approach:
            posterior ∝ prior × likelihood_ratio

        where likelihood_ratio is approximated from evidence direction,
        reliability, and relevance.
        """
        relevance = evidence.relevance_to_hypotheses.get(hypothesis.hypothesis_id, 0.5)

        # Compute effective update strength
        strength = self._base_strength * relevance
        strength *= (
            self._reliability_weight * evidence.reliability
            + (1 - self._reliability_weight) * 0.5
        )
        strength *= (
            self._independence_weight * independence_score
            + (1 - self._independence_weight) * 0.5
        )

        # Direction determines sign
        if evidence.direction == EvidenceDirection.CONTRADICTING:
            strength *= self._falsification_mult
            delta = -strength
            rationale = f"Contradicting evidence (reliability={evidence.reliability:.2f}) reduces belief"
        elif evidence.direction == EvidenceDirection.SUPPORTING:
            delta = strength
            rationale = f"Supporting evidence (reliability={evidence.reliability:.2f}) increases belief"
        elif evidence.direction == EvidenceDirection.AMBIGUOUS:
            delta = strength * 0.1  # Minimal effect
            rationale = "Ambiguous evidence has minimal effect"
        else:
            delta = 0.0
            rationale = "Neutral evidence has no effect"

        # Apply ad-hoc complexity penalty
        if hypothesis.rescue_assumptions > 0:
            penalty = hypothesis.rescue_assumptions * self._rescue_penalty
            delta -= penalty
            rationale += f" (complexity penalty: {penalty:.3f} for {hypothesis.rescue_assumptions} rescue assumptions)"

        # Clamp magnitude
        delta = max(-self._max_update, min(self._max_update, delta))

        # Compute posterior
        posterior = max(0.0, min(1.0, current_belief + delta))

        return BeliefUpdateResult(
            hypothesis_id=hypothesis.hypothesis_id,
            prior=current_belief,
            posterior=posterior,
            magnitude=abs(posterior - current_belief),
            evidence_id=evidence.evidence_id,
            rationale=rationale,
        )

    def should_abandon(self, hypothesis: StructuredHypothesis, belief: float) -> bool:
        """Check if a hypothesis should be abandoned based on belief threshold."""
        return belief <= self._abandonment_threshold

    def update_ecology(
        self,
        ecology: HypothesisEcology,
        evidence: ScientificEvidence,
        beliefs: BeliefState,
        independence_scores: dict[str, float] | None = None,
    ) -> list[BeliefUpdateResult]:
        """Update beliefs for all active hypotheses given new evidence."""
        results = []
        for hid, hyp in ecology.active_hypotheses.items():
            ind_score = (independence_scores or {}).get(hid, 1.0)
            current = beliefs.get_belief(hid)
            result = self.update_belief(hyp, evidence, current, ind_score)
            results.append(result)
        return results

    def normalize_beliefs(self, beliefs: dict[str, float]) -> dict[str, float]:
        """Optionally normalize beliefs to sum to 1 (probability distribution)."""
        total = sum(beliefs.values())
        if total <= 0:
            return beliefs
        return {k: v / total for k, v in beliefs.items()}
