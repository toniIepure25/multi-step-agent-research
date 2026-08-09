"""
Tests for the state reducer — applying events to produce new states.
"""

from __future__ import annotations

import pytest

from asar.epistemic.reducer import StateReducer
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


def _make_state(version: int = 0) -> EpistemicState:
    return EpistemicState(
        version=version,
        process=ProcessState(episode_id="ep_001", goal="test"),
        budget=BudgetState(max_tokens=10000, max_steps=20),
    )


def _make_event(
    state: EpistemicState,
    action_type: ActionType = ActionType.RETRIEVE,
    artifacts_produced: dict | None = None,
    resource_cost: ResourceCost | None = None,
) -> EpistemicEvent:
    action = EpistemicAction(
        action_id="action_001",
        action_type=action_type,
        operator_name="test_op",
    )
    result = OperatorResult(
        operator_name="test_op",
        action_id="action_001",
        outcome=OperatorOutcome.SUCCESS,
        artifacts_produced=artifacts_produced or {},
        resource_cost=resource_cost or ResourceCost(),
    )
    return EpistemicEvent(
        event_id="event_001",
        episode_id=state.process.episode_id,
        version_before=state.version,
        version_after=state.version + 1,
        action=action,
        result=result,
        resource_cost=result.resource_cost,
    )


class TestStateReducer:
    def test_apply_increments_version(self) -> None:
        reducer = StateReducer()
        state = _make_state(version=0)
        event = _make_event(state)
        new_state = reducer.apply(state, event)
        assert new_state.version == 1

    def test_apply_does_not_mutate_original(self) -> None:
        reducer = StateReducer()
        state = _make_state(version=0)
        event = _make_event(state)
        new_state = reducer.apply(state, event)
        assert state.version == 0
        assert new_state.version == 1

    def test_apply_adds_artifacts(self) -> None:
        reducer = StateReducer()
        state = _make_state()
        event = _make_event(state, artifacts_produced={
            "evidence_001": {"content": "some evidence"},
        })
        new_state = reducer.apply(state, event)
        assert "evidence_001" in new_state.artifacts
        assert "evidence_001" in new_state.evidence_ids

    def test_apply_classifies_artifact_types(self) -> None:
        reducer = StateReducer()
        state = _make_state()
        event = _make_event(state, artifacts_produced={
            "evidence_01": {"content": "ev"},
            "claim_01": {"text": "claim"},
            "hypothesis_01": {"statement": "hyp"},
            "assumption_01": {"text": "assumption"},
            "ignorance_01": {"text": "unknown"},
            "contradiction_01": {"text": "conflict"},
        })
        new_state = reducer.apply(state, event)
        assert "evidence_01" in new_state.evidence_ids
        assert "claim_01" in new_state.claim_ids
        assert "hypothesis_01" in new_state.hypothesis_ids
        assert "assumption_01" in new_state.assumption_ids
        assert "ignorance_01" in new_state.ignorance_ids
        assert "contradiction_01" in new_state.contradiction_ids

    def test_apply_updates_budget(self) -> None:
        reducer = StateReducer()
        state = _make_state()
        cost = ResourceCost(input_tokens=100, output_tokens=200, api_cost_usd=0.01)
        event = _make_event(state, resource_cost=cost)
        new_state = reducer.apply(state, event)
        assert new_state.budget.tokens_used == 300
        assert new_state.budget.steps_used == 1

    def test_apply_stop_action_completes_process(self) -> None:
        reducer = StateReducer()
        state = _make_state()
        event = _make_event(state, action_type=ActionType.STOP)
        new_state = reducer.apply(state, event)
        assert new_state.process.status == "completed"
        assert new_state.process.stop_reason is not None

    def test_apply_abstain_action(self) -> None:
        reducer = StateReducer()
        state = _make_state()
        event = _make_event(state, action_type=ActionType.ABSTAIN)
        new_state = reducer.apply(state, event)
        assert new_state.process.status == "abstained"

    def test_apply_tracks_operator_history(self) -> None:
        reducer = StateReducer()
        state = _make_state()
        event = _make_event(state)
        new_state = reducer.apply(state, event)
        assert "test_op" in new_state.operator_history

    def test_replay_reconstructs_equivalent_state(self) -> None:
        reducer = StateReducer()
        initial = _make_state()

        events = []
        state = initial
        for i in range(3):
            event = _make_event(
                state,
                artifacts_produced={f"evidence_{i:03d}": {"content": f"ev{i}"}},
                resource_cost=ResourceCost(input_tokens=50, output_tokens=50),
            )
            event = event.model_copy(update={
                "event_id": f"event_{i:03d}",
                "version_before": state.version,
                "version_after": state.version + 1,
            })
            events.append(event)
            state = reducer.apply(state, event)

        replayed = reducer.replay(initial, events)
        assert replayed.version == state.version
        assert replayed.evidence_ids == state.evidence_ids
        assert replayed.budget.tokens_used == state.budget.tokens_used
        assert replayed.budget.steps_used == state.budget.steps_used
