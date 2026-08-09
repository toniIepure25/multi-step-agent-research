"""
Tests for the append-only event store.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from schemas.ree.epistemic_event import (
    ActionType,
    EpistemicAction,
    EpistemicEvent,
    OperatorOutcome,
    OperatorResult,
)
from schemas.ree.epistemic_state import ResourceCost
from asar.epistemic.store import AppendOnlyEventStore


def _make_event(
    event_id: str = "event_001",
    episode_id: str = "ep_001",
    version_before: int = 0,
    version_after: int = 1,
) -> EpistemicEvent:
    return EpistemicEvent(
        event_id=event_id,
        episode_id=episode_id,
        version_before=version_before,
        version_after=version_after,
        action=EpistemicAction(
            action_id="action_001",
            action_type=ActionType.RETRIEVE,
            operator_name="retrieve",
        ),
        result=OperatorResult(
            operator_name="retrieve",
            action_id="action_001",
            outcome=OperatorOutcome.SUCCESS,
        ),
        resource_cost=ResourceCost(input_tokens=10, output_tokens=20),
    )


class TestAppendOnlyEventStore:
    def test_append_and_get_all(self) -> None:
        store = AppendOnlyEventStore()
        event = _make_event()
        store.append(event)
        assert len(store) == 1
        assert store.get_all()[0].event_id == "event_001"

    def test_get_by_episode(self) -> None:
        store = AppendOnlyEventStore()
        store.append(_make_event(event_id="e1", episode_id="ep_A"))
        store.append(_make_event(event_id="e2", episode_id="ep_B"))
        store.append(_make_event(event_id="e3", episode_id="ep_A"))

        ep_a_events = store.get_by_episode("ep_A")
        assert len(ep_a_events) == 2
        assert all(e.episode_id == "ep_A" for e in ep_a_events)

    def test_get_event_by_id(self) -> None:
        store = AppendOnlyEventStore()
        store.append(_make_event(event_id="e1"))
        store.append(_make_event(event_id="e2"))

        assert store.get_event("e1") is not None
        assert store.get_event("e1").event_id == "e1"
        assert store.get_event("nonexistent") is None

    def test_get_range(self) -> None:
        store = AppendOnlyEventStore()
        store.append(_make_event(event_id="e1", version_before=0, version_after=1))
        store.append(_make_event(event_id="e2", version_before=1, version_after=2))
        store.append(_make_event(event_id="e3", version_before=2, version_after=3))

        events = store.get_range(0, 2)
        assert len(events) == 2
        assert events[0].event_id == "e1"
        assert events[1].event_id == "e2"

    def test_fork_creates_subset(self) -> None:
        store = AppendOnlyEventStore()
        store.append(_make_event(event_id="e1", version_before=0, version_after=1))
        store.append(_make_event(event_id="e2", version_before=1, version_after=2))
        store.append(_make_event(event_id="e3", version_before=2, version_after=3))

        forked = store.fork(from_version=2)
        assert len(forked) == 2
        assert forked.get_all()[-1].event_id == "e2"

    def test_persistence_to_file(self, tmp_path: Path) -> None:
        path = tmp_path / "events.jsonl"
        store = AppendOnlyEventStore(path=path)
        store.append(_make_event(event_id="e1"))
        store.append(_make_event(event_id="e2"))

        loaded = AppendOnlyEventStore.load_from_file(path)
        assert len(loaded) == 2
        assert loaded.get_all()[0].event_id == "e1"
        assert loaded.get_all()[1].event_id == "e2"

    def test_append_only_invariant(self) -> None:
        store = AppendOnlyEventStore()
        store.append(_make_event(event_id="e1"))
        store.append(_make_event(event_id="e2"))
        assert len(store) == 2
        assert store.get_all()[0].event_id == "e1"
