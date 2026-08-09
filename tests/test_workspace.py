"""
Tests for the bounded epistemic workspace and salience scoring.
"""

from __future__ import annotations

import pytest

from asar.epistemic.workspace import SalienceScorer, SalienceSignals, WorkspaceManager
from schemas.ree.epistemic_state import WorkspaceSlot, WorkspaceState


class TestSalienceScorer:
    def test_high_relevance_scores_high(self) -> None:
        scorer = SalienceScorer()
        signals = SalienceSignals(relevance=1.0, novelty=0.5)
        score = scorer.score(signals)
        assert 0.0 < score <= 1.0

    def test_redundancy_penalty_reduces_score(self) -> None:
        scorer = SalienceScorer()
        base = SalienceSignals(relevance=0.8, novelty=0.5)
        penalized = SalienceSignals(relevance=0.8, novelty=0.5, redundancy_penalty=0.5)
        assert scorer.score(base) > scorer.score(penalized)

    def test_all_zero_signals_give_zero(self) -> None:
        scorer = SalienceScorer()
        signals = SalienceSignals(
            relevance=0, surprise=0, contradiction=0,
            uncertainty_reduction=0, decision_impact=0,
            novelty=0, urgency=0,
        )
        assert scorer.score(signals) == pytest.approx(0.0)

    def test_score_bounded_zero_to_one(self) -> None:
        scorer = SalienceScorer()
        signals = SalienceSignals(
            relevance=1.0, surprise=1.0, contradiction=1.0,
            uncertainty_reduction=1.0, decision_impact=1.0,
            novelty=1.0, urgency=1.0,
        )
        assert 0.0 <= scorer.score(signals) <= 1.0

    def test_contradiction_signal_raises_score(self) -> None:
        scorer = SalienceScorer()
        without = SalienceSignals(relevance=0.5)
        with_contradiction = SalienceSignals(relevance=0.5, contradiction=0.8)
        assert scorer.score(with_contradiction) > scorer.score(without)


class TestWorkspaceManager:
    def _empty_workspace(self, capacity: int = 5) -> WorkspaceState:
        return WorkspaceState(capacity=capacity)

    def test_add_to_empty_workspace(self) -> None:
        mgr = WorkspaceManager()
        ws = self._empty_workspace()
        ws2 = mgr.add_artifact(
            ws, "a1", "evidence", SalienceSignals(relevance=0.8), version=1,
        )
        assert ws2.occupancy == 1
        assert ws2.slots[0].artifact_id == "a1"

    def test_add_does_not_mutate_original(self) -> None:
        mgr = WorkspaceManager()
        ws = self._empty_workspace()
        ws2 = mgr.add_artifact(
            ws, "a1", "evidence", SalienceSignals(relevance=0.8), version=1,
        )
        assert ws.occupancy == 0
        assert ws2.occupancy == 1

    def test_eviction_when_full(self) -> None:
        mgr = WorkspaceManager()
        ws = WorkspaceState(
            capacity=2,
            slots=[
                WorkspaceSlot(artifact_id="low", artifact_type="test", salience=0.1, added_at_version=0),
                WorkspaceSlot(artifact_id="med", artifact_type="test", salience=0.5, added_at_version=0),
            ],
        )
        ws2 = mgr.add_artifact(
            ws, "high", "test", SalienceSignals(relevance=1.0, novelty=1.0), version=1,
        )
        ids = {s.artifact_id for s in ws2.slots}
        assert "high" in ids
        assert "low" not in ids
        assert ws2.occupancy == 2

    def test_irrelevant_material_does_not_enter(self) -> None:
        mgr = WorkspaceManager()
        ws = WorkspaceState(
            capacity=2,
            slots=[
                WorkspaceSlot(artifact_id="a", artifact_type="test", salience=0.6, added_at_version=0),
                WorkspaceSlot(artifact_id="b", artifact_type="test", salience=0.7, added_at_version=0),
            ],
        )
        ws2 = mgr.add_artifact(
            ws, "irrelevant", "test",
            SalienceSignals(relevance=0.0, novelty=0.0),
            version=1,
        )
        ids = {s.artifact_id for s in ws2.slots}
        assert "irrelevant" not in ids

    def test_duplicate_does_not_create_second_slot(self) -> None:
        mgr = WorkspaceManager()
        ws = self._empty_workspace()
        ws2 = mgr.add_artifact(ws, "a1", "test", SalienceSignals(relevance=0.5), version=1)
        ws3 = mgr.add_artifact(ws2, "a1", "test", SalienceSignals(relevance=0.9), version=2)
        assert ws3.occupancy == 1

    def test_remove_artifact(self) -> None:
        mgr = WorkspaceManager()
        ws = WorkspaceState(
            capacity=5,
            slots=[WorkspaceSlot(artifact_id="a1", artifact_type="test", salience=0.5, added_at_version=0)],
        )
        ws2 = mgr.remove_artifact(ws, "a1")
        assert ws2.occupancy == 0

    def test_update_salience(self) -> None:
        mgr = WorkspaceManager()
        ws = WorkspaceState(
            capacity=5,
            slots=[WorkspaceSlot(artifact_id="a1", artifact_type="test", salience=0.3, added_at_version=0)],
        )
        ws2 = mgr.update_salience(ws, "a1", SalienceSignals(relevance=1.0, novelty=1.0))
        assert ws2.slots[0].salience > 0.3
