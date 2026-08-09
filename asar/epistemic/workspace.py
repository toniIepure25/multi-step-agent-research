"""
Bounded epistemic workspace with salience scoring.

Artifacts compete for workspace inclusion based on relevance, surprise,
contradiction, expected uncertainty reduction, decision impact, novelty,
urgency, and redundancy penalty.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from schemas.ree.epistemic_state import EpistemicState, WorkspaceSlot, WorkspaceState


@dataclass(frozen=True)
class SalienceWeights:
    """Configurable weights for salience scoring."""

    relevance: float = 0.25
    surprise: float = 0.15
    contradiction: float = 0.20
    uncertainty_reduction: float = 0.15
    decision_impact: float = 0.10
    novelty: float = 0.10
    urgency: float = 0.05


@dataclass
class SalienceSignals:
    """Signals used to compute an artifact's workspace salience."""

    relevance: float = 0.5
    surprise: float = 0.0
    contradiction: float = 0.0
    uncertainty_reduction: float = 0.0
    decision_impact: float = 0.0
    novelty: float = 0.5
    urgency: float = 0.0
    redundancy_penalty: float = 0.0


class SalienceScorer:
    """Scores artifacts for workspace inclusion."""

    def __init__(self, weights: SalienceWeights | None = None) -> None:
        self._weights = weights or SalienceWeights()

    def score(self, signals: SalienceSignals) -> float:
        """Compute a salience score in [0, 1]."""
        w = self._weights
        raw = (
            w.relevance * signals.relevance
            + w.surprise * signals.surprise
            + w.contradiction * signals.contradiction
            + w.uncertainty_reduction * signals.uncertainty_reduction
            + w.decision_impact * signals.decision_impact
            + w.novelty * signals.novelty
            + w.urgency * signals.urgency
        )
        penalized = raw * (1.0 - signals.redundancy_penalty)
        return max(0.0, min(1.0, penalized))


class WorkspaceManager:
    """Manages the bounded workspace, adding/removing artifacts by salience."""

    def __init__(self, scorer: SalienceScorer | None = None) -> None:
        self._scorer = scorer or SalienceScorer()

    def add_artifact(
        self,
        workspace: WorkspaceState,
        artifact_id: str,
        artifact_type: str,
        signals: SalienceSignals,
        version: int,
        content_summary: str = "",
    ) -> WorkspaceState:
        """Try to add an artifact to the workspace. Evicts lowest salience if full."""
        salience = self._scorer.score(signals)
        new_slot = WorkspaceSlot(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            salience=salience,
            added_at_version=version,
            content_summary=content_summary,
        )

        for existing in workspace.slots:
            if existing.artifact_id == artifact_id:
                slots = [s if s.artifact_id != artifact_id else new_slot for s in workspace.slots]
                return workspace.model_copy(update={"slots": slots})

        if not workspace.is_full:
            return workspace.model_copy(update={"slots": [*workspace.slots, new_slot]})

        sorted_slots = sorted(workspace.slots, key=lambda s: s.salience)
        if sorted_slots[0].salience < salience:
            remaining = [s for s in workspace.slots if s.artifact_id != sorted_slots[0].artifact_id]
            return workspace.model_copy(update={"slots": [*remaining, new_slot]})

        return workspace

    def remove_artifact(self, workspace: WorkspaceState, artifact_id: str) -> WorkspaceState:
        """Remove an artifact from the workspace."""
        return workspace.model_copy(
            update={"slots": [s for s in workspace.slots if s.artifact_id != artifact_id]}
        )

    def update_salience(
        self,
        workspace: WorkspaceState,
        artifact_id: str,
        signals: SalienceSignals,
    ) -> WorkspaceState:
        """Recompute salience for an artifact."""
        new_salience = self._scorer.score(signals)
        slots = []
        for s in workspace.slots:
            if s.artifact_id == artifact_id:
                slots.append(s.model_copy(update={"salience": new_salience}))
            else:
                slots.append(s)
        return workspace.model_copy(update={"slots": slots})
