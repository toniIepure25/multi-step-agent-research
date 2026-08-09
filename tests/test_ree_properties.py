"""
Property and invariant tests for the REE architecture.

These verify architectural invariants that must always hold:
- 0 <= belief <= 1
- State replay reconstructs equivalent state
- Operators cannot mutate shared state outside the reducer
- Historical belief versions remain queryable
- Duplicating a source does not increase effective independence
- A rejected hypothesis cannot silently become active
"""

from __future__ import annotations

import pytest

from asar.epistemic.reducer import StateReducer
from asar.epistemic.store import AppendOnlyEventStore
from asar.social.trust import EvidenceIndependenceAnalyzer
from asar.world_model.hypothesis_graph import HypothesisGraph
from asar.world_model.belief_tracker import BeliefTracker
from schemas.ree.epistemic_event import (
    ActionType,
    EpistemicAction,
    EpistemicEvent,
    OperatorOutcome,
    OperatorResult,
)
from schemas.ree.epistemic_state import (
    BudgetState,
    EpistemicState,
    ProcessState,
    ResourceCost,
)
from schemas.ree.social import EvidenceProvenance
from schemas.ree.world_model import Hypothesis, HypothesisStatus


class TestBeliefBounds:
    """0 <= belief <= 1"""

    def test_hypothesis_posterior_bounded(self) -> None:
        g = HypothesisGraph()
        g.add_hypothesis(Hypothesis(hypothesis_id="h1", statement="test"))
        updated = g.update_posterior("h1", 1.5)
        assert 0.0 <= updated.posterior <= 1.0
        updated = g.update_posterior("h1", -0.5)
        assert 0.0 <= updated.posterior <= 1.0

    def test_schema_enforces_bounds(self) -> None:
        with pytest.raises(Exception):
            Hypothesis(hypothesis_id="h1", statement="test", posterior=1.5)
        with pytest.raises(Exception):
            Hypothesis(hypothesis_id="h1", statement="test", posterior=-0.1)


class TestStateReplayInvariant:
    """State replay reconstructs equivalent state."""

    def test_replay_equivalence(self) -> None:
        reducer = StateReducer()
        initial = EpistemicState(
            version=0,
            process=ProcessState(episode_id="ep_001", goal="test"),
            budget=BudgetState(max_tokens=10000),
        )

        events = []
        state = initial
        for i in range(5):
            action = EpistemicAction(
                action_id=f"a{i}", action_type=ActionType.RETRIEVE,
                operator_name="test",
            )
            result = OperatorResult(
                operator_name="test", action_id=f"a{i}",
                outcome=OperatorOutcome.SUCCESS,
                artifacts_produced={f"evidence_{i:03d}": {"content": f"ev{i}"}},
                resource_cost=ResourceCost(input_tokens=10, output_tokens=10),
            )
            event = EpistemicEvent(
                event_id=f"ev{i}", episode_id="ep_001",
                version_before=state.version, version_after=state.version + 1,
                action=action, result=result, resource_cost=result.resource_cost,
            )
            events.append(event)
            state = reducer.apply(state, event)

        replayed = reducer.replay(initial, events)
        assert replayed.version == state.version
        assert replayed.evidence_ids == state.evidence_ids
        assert replayed.budget.tokens_used == state.budget.tokens_used


class TestAppendOnlyInvariant:
    """Historical events and belief versions remain queryable."""

    def test_events_never_deleted(self) -> None:
        store = AppendOnlyEventStore()
        action = EpistemicAction(
            action_id="a1", action_type=ActionType.REASON,
            operator_name="test",
        )
        result = OperatorResult(
            operator_name="test", action_id="a1",
            outcome=OperatorOutcome.SUCCESS,
        )
        for i in range(10):
            store.append(EpistemicEvent(
                event_id=f"e{i}", episode_id="ep",
                version_before=i, version_after=i + 1,
                action=action, result=result,
            ))
        assert len(store) == 10
        for i in range(10):
            assert store.get_event(f"e{i}") is not None

    def test_belief_trajectory_queryable(self) -> None:
        tracker = BeliefTracker()
        tracker.record("h1", 0, 0.5, HypothesisStatus.PROPOSED)
        tracker.record("h1", 1, 0.7, HypothesisStatus.ACTIVE)
        tracker.record("h1", 2, 0.3, HypothesisStatus.WEAKENED)
        traj = tracker.trajectory("h1")
        assert len(traj) == 3
        assert traj[0].posterior == 0.5
        assert traj[2].posterior == 0.3


class TestRejectedHypothesisInvariant:
    """A rejected hypothesis cannot silently become active without a recorded event."""

    def test_rejected_stays_rejected_without_explicit_update(self) -> None:
        g = HypothesisGraph()
        g.add_hypothesis(Hypothesis(
            hypothesis_id="h1", statement="test",
            status=HypothesisStatus.REJECTED,
        ))
        g.add_supporting_evidence("h1", "e1")
        h = g.get_hypothesis("h1")
        assert h.status == HypothesisStatus.REJECTED


class TestDuplicateSourceInvariant:
    """Duplicating a source must not increase effective source independence."""

    def test_duplicating_does_not_increase_independence(self) -> None:
        analyzer = EvidenceIndependenceAnalyzer()
        analyzer.register_provenance(EvidenceProvenance(
            evidence_id="e1", original_source_id="src_a",
        ))

        initial_count = analyzer.effective_evidence_count(["e1"])

        analyzer.register_provenance(EvidenceProvenance(
            evidence_id="e2", original_source_id="src_a", is_derivative=True,
        ))
        analyzer.register_provenance(EvidenceProvenance(
            evidence_id="e3", original_source_id="src_a", is_derivative=True,
        ))

        after_count = analyzer.effective_evidence_count(["e1", "e2", "e3"])
        assert after_count == initial_count
