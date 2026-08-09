"""
Hypothesis graph — manages competing hypotheses, assumptions, predictions, and falsifiers.

Implements the hypothesis foundry: hypothesis competition with diversity constraints,
assumption dependency tracking, and contradiction detection.
"""

from __future__ import annotations

from asar.common import generate_id
from schemas.ree.world_model import (
    Assumption,
    Contradiction,
    Falsifier,
    Hypothesis,
    HypothesisStatus,
    Prediction,
)


class HypothesisGraph:
    """Manages the ecology of competing hypotheses and their dependencies."""

    def __init__(self) -> None:
        self._hypotheses: dict[str, Hypothesis] = {}
        self._assumptions: dict[str, Assumption] = {}
        self._predictions: dict[str, Prediction] = {}
        self._falsifiers: dict[str, Falsifier] = {}
        self._contradictions: dict[str, Contradiction] = {}

    def add_hypothesis(self, hypothesis: Hypothesis) -> None:
        self._hypotheses[hypothesis.hypothesis_id] = hypothesis

    def get_hypothesis(self, hypothesis_id: str) -> Hypothesis | None:
        return self._hypotheses.get(hypothesis_id)

    def all_hypotheses(self) -> list[Hypothesis]:
        return list(self._hypotheses.values())

    def active_hypotheses(self) -> list[Hypothesis]:
        return [
            h for h in self._hypotheses.values()
            if h.status in (HypothesisStatus.PROPOSED, HypothesisStatus.ACTIVE)
        ]

    def update_posterior(self, hypothesis_id: str, new_posterior: float) -> Hypothesis | None:
        """Update belief in a hypothesis, applying status transitions."""
        h = self._hypotheses.get(hypothesis_id)
        if h is None:
            return None

        status = h.status
        if new_posterior < 0.1 and status not in (HypothesisStatus.REJECTED, HypothesisStatus.SUPERSEDED):
            status = HypothesisStatus.REJECTED
        elif new_posterior < 0.3 and status == HypothesisStatus.ACTIVE:
            status = HypothesisStatus.WEAKENED
        elif new_posterior >= 0.3 and status == HypothesisStatus.PROPOSED:
            status = HypothesisStatus.ACTIVE

        updated = h.model_copy(update={
            "posterior": max(0.0, min(1.0, new_posterior)),
            "status": status,
        })
        self._hypotheses[hypothesis_id] = updated
        return updated

    def add_supporting_evidence(self, hypothesis_id: str, evidence_id: str) -> None:
        h = self._hypotheses.get(hypothesis_id)
        if h and evidence_id not in h.supporting_evidence_ids:
            self._hypotheses[hypothesis_id] = h.model_copy(
                update={"supporting_evidence_ids": [*h.supporting_evidence_ids, evidence_id]}
            )

    def add_attacking_evidence(self, hypothesis_id: str, evidence_id: str) -> None:
        h = self._hypotheses.get(hypothesis_id)
        if h and evidence_id not in h.attacking_evidence_ids:
            self._hypotheses[hypothesis_id] = h.model_copy(
                update={"attacking_evidence_ids": [*h.attacking_evidence_ids, evidence_id]}
            )

    def add_assumption(self, assumption: Assumption) -> None:
        self._assumptions[assumption.assumption_id] = assumption

    def get_assumptions_for(self, hypothesis_id: str) -> list[Assumption]:
        return [
            a for a in self._assumptions.values()
            if hypothesis_id in a.dependent_hypothesis_ids
        ]

    def critical_assumptions(self, threshold: float = 0.7) -> list[Assumption]:
        """Return assumptions whose criticality exceeds the threshold."""
        return [a for a in self._assumptions.values() if a.criticality >= threshold]

    def add_prediction(self, prediction: Prediction) -> None:
        self._predictions[prediction.prediction_id] = prediction
        h = self._hypotheses.get(prediction.hypothesis_id)
        if h and prediction.prediction_id not in h.prediction_ids:
            self._hypotheses[prediction.hypothesis_id] = h.model_copy(
                update={"prediction_ids": [*h.prediction_ids, prediction.prediction_id]}
            )

    def add_falsifier(self, falsifier: Falsifier) -> None:
        self._falsifiers[falsifier.falsifier_id] = falsifier
        h = self._hypotheses.get(falsifier.hypothesis_id)
        if h and falsifier.falsifier_id not in h.falsifier_ids:
            self._hypotheses[falsifier.hypothesis_id] = h.model_copy(
                update={"falsifier_ids": [*h.falsifier_ids, falsifier.falsifier_id]}
            )

    def get_falsifiers_for(self, hypothesis_id: str) -> list[Falsifier]:
        return [f for f in self._falsifiers.values() if f.hypothesis_id == hypothesis_id]

    def add_contradiction(self, contradiction: Contradiction) -> None:
        self._contradictions[contradiction.contradiction_id] = contradiction

    def unresolved_contradictions(self) -> list[Contradiction]:
        return [c for c in self._contradictions.values() if not c.resolved]

    def detect_contradiction(
        self,
        artifact_id_a: str,
        artifact_id_b: str,
        description: str,
        severity: float = 0.5,
    ) -> Contradiction:
        """Create and register a new contradiction between two artifacts."""
        c = Contradiction(
            contradiction_id=generate_id("contradiction"),
            artifact_ids=[artifact_id_a, artifact_id_b],
            description=description,
            severity=severity,
        )
        self.add_contradiction(c)
        return c

    def hypothesis_diversity_score(self) -> float:
        """Measure structural diversity of active hypotheses.

        Uses ontology frame distribution as a proxy. Returns 0-1 where
        1 = all hypotheses use distinct frames.
        """
        active = self.active_hypotheses()
        if len(active) <= 1:
            return 0.0
        frames = {h.ontology_frame for h in active}
        return len(frames) / len(active)

    def to_artifacts(self) -> dict[str, object]:
        """Export all graph contents as a dict of artifacts for state storage."""
        artifacts: dict[str, object] = {}
        for h in self._hypotheses.values():
            artifacts[h.hypothesis_id] = h.model_dump()
        for a in self._assumptions.values():
            artifacts[a.assumption_id] = a.model_dump()
        for p in self._predictions.values():
            artifacts[p.prediction_id] = p.model_dump()
        for f in self._falsifiers.values():
            artifacts[f.falsifier_id] = f.model_dump()
        for c in self._contradictions.values():
            artifacts[c.contradiction_id] = c.model_dump()
        return artifacts
