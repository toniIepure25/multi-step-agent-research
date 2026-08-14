"""
Stage 1 State Certification Tests.

These certify the event-sourced architecture correctness:
1. Deterministic replay — same events produce same state
2. Immutability — applying events never mutates prior state
3. Fork independence — branching produces independent histories
4. Serialization round-trip — serialize → deserialize preserves semantics
5. Event provenance — every belief-changing event retains full provenance
6. No hidden mutation — controller does not alter shared state outside events
"""

import copy
import json

import pytest

from asar.scientific_discovery.belief_updater import BeliefUpdater
from asar.scientific_discovery.controller import EvidenceRound, ScientificController
from asar.scientific_discovery.controlled_worlds import (
    create_confirmation_trap_world,
    create_confounded_causality_world,
    create_non_identifiable_world,
)
from asar.scientific_discovery.events import ScientificEvent, ScientificEventType
from asar.scientific_discovery.state import (
    BeliefState,
    EvidenceDirection,
    HypothesisEcology,
    HypothesisStatus,
    ScientificEvidence,
    ScientificState,
    StructuredHypothesis,
)


class TestDeterministicReplay:
    """Given S0 + event sequence E1...En, replay must reconstruct the same state."""

    def test_same_world_same_seed_same_result(self):
        """Two runs from identical initial state produce identical final state."""
        world = create_confirmation_trap_world(seed=42)
        ctrl = ScientificController()

        result1 = ctrl.run_episode(world.initial_state, world.evidence_rounds)
        result2 = ctrl.run_episode(world.initial_state, world.evidence_rounds)

        # Final beliefs must be identical
        assert result1.belief_trajectory == result2.belief_trajectory
        assert result1.conclusion == result2.conclusion
        assert result1.rounds_completed == result2.rounds_completed
        assert len(result1.events) == len(result2.events)

    def test_replay_produces_same_belief_trajectory(self):
        """Running the same episode twice gives same belief at every round."""
        for seed in [1, 7, 42, 99, 123]:
            world = create_confirmation_trap_world(seed=seed)
            ctrl = ScientificController()

            r1 = ctrl.run_episode(world.initial_state, world.evidence_rounds)
            r2 = ctrl.run_episode(world.initial_state, world.evidence_rounds)

            for i, (b1, b2) in enumerate(zip(r1.belief_trajectory, r2.belief_trajectory)):
                for hid in b1:
                    assert abs(b1[hid] - b2.get(hid, 0)) < 1e-10, (
                        f"Replay diverged at round {i}, hypothesis {hid}, seed {seed}"
                    )

    def test_event_types_are_deterministic(self):
        """Event sequence types must match across replays."""
        world = create_confounded_causality_world(seed=7)
        ctrl = ScientificController()

        r1 = ctrl.run_episode(world.initial_state, world.evidence_rounds)
        r2 = ctrl.run_episode(world.initial_state, world.evidence_rounds)

        types1 = [e.event_type for e in r1.events]
        types2 = [e.event_type for e in r2.events]
        assert types1 == types2


class TestImmutability:
    """Applying an event must not mutate prior ScientificState."""

    def test_initial_state_unchanged_after_episode(self):
        """Running an episode must not modify the initial state object."""
        world = create_confirmation_trap_world(seed=42)
        initial_copy = world.initial_state.model_dump()

        ctrl = ScientificController()
        ctrl.run_episode(world.initial_state, world.evidence_rounds)

        # Initial state must be unchanged
        after_copy = world.initial_state.model_dump()
        assert initial_copy == after_copy

    def test_belief_state_set_does_not_mutate(self):
        """BeliefState.set_belief returns new object without mutating original."""
        bs = BeliefState(beliefs={"h1": 0.5, "h2": 0.3})
        original_beliefs = dict(bs.beliefs)

        bs2 = bs.set_belief("h1", 0.9)

        assert bs.beliefs == original_beliefs
        assert bs2.get_belief("h1") == 0.9
        assert bs.get_belief("h1") == 0.5

    def test_ecology_not_mutated_by_controller(self):
        """Controller must not mutate the ecology passed to it."""
        world = create_confirmation_trap_world(seed=42)
        eco_before = world.initial_state.ecology.model_dump()

        ctrl = ScientificController()
        ctrl.run_episode(world.initial_state, world.evidence_rounds)

        eco_after = world.initial_state.ecology.model_dump()
        assert eco_before == eco_after


class TestForkIndependence:
    """Fork state at event k. Apply different evidence to each branch. Branches must diverge."""

    def test_forked_episodes_diverge(self):
        """Two episodes from same initial state but different evidence must diverge."""
        world = create_confirmation_trap_world(seed=42)
        ctrl = ScientificController()

        # Branch A: full evidence
        result_a = ctrl.run_episode(world.initial_state, world.evidence_rounds)

        # Branch B: only first round (different trajectory)
        result_b = ctrl.run_episode(world.initial_state, world.evidence_rounds[:1])

        # Must have different conclusions/beliefs
        final_a = result_a.belief_trajectory[-1]
        final_b = result_b.belief_trajectory[-1]

        # At least one hypothesis must differ
        some_differ = any(
            abs(final_a.get(k, 0) - final_b.get(k, 0)) > 0.01
            for k in set(final_a) | set(final_b)
        )
        assert some_differ, "Forked branches should diverge with different evidence"

    def test_fork_does_not_contaminate_other_branch(self):
        """Processing evidence on one branch must not affect the other."""
        world = create_confirmation_trap_world(seed=42)
        state_snapshot = world.initial_state.model_dump()

        ctrl = ScientificController()

        # Run Branch A (full)
        ctrl.run_episode(world.initial_state, world.evidence_rounds)

        # Original state must be unchanged for Branch B
        assert world.initial_state.model_dump() == state_snapshot


class TestSerializationRoundTrip:
    """Scientific state and events must preserve semantics after serialize → deserialize."""

    def test_state_json_roundtrip(self):
        """ScientificState survives JSON serialization."""
        world = create_confirmation_trap_world(seed=42)
        state = world.initial_state

        json_str = state.model_dump_json()
        restored = ScientificState.model_validate_json(json_str)

        assert restored.version == state.version
        assert restored.episode_id == state.episode_id
        assert restored.research_question == state.research_question
        assert len(restored.ecology.hypotheses) == len(state.ecology.hypotheses)
        assert restored.beliefs.beliefs == state.beliefs.beliefs

    def test_event_json_roundtrip(self):
        """ScientificEvent survives JSON serialization."""
        event = ScientificEvent(
            event_id="evt_test",
            episode_id="ep_test",
            event_type=ScientificEventType.BELIEF_UPDATED,
            version_before=0,
            version_after=1,
            target_ids=["h1"],
            payload={"prior": 0.5, "posterior": 0.3, "magnitude": 0.2},
            rationale="Test evidence reduced belief",
        )

        json_str = event.model_dump_json()
        restored = ScientificEvent.model_validate_json(json_str)

        assert restored.event_id == event.event_id
        assert restored.event_type == ScientificEventType.BELIEF_UPDATED
        assert restored.target_ids == ["h1"]
        assert restored.payload["prior"] == 0.5

    def test_full_episode_result_serializable(self):
        """Complete episode result can be serialized to JSON."""
        world = create_confirmation_trap_world(seed=42)
        ctrl = ScientificController()
        result = ctrl.run_episode(world.initial_state, world.evidence_rounds)

        # State must serialize
        state_json = result.final_state.model_dump_json()
        assert len(state_json) > 0

        # Events must serialize
        for event in result.events:
            event_json = event.model_dump_json()
            restored = ScientificEvent.model_validate_json(event_json)
            assert restored.event_type == event.event_type


class TestEventProvenance:
    """Every belief-changing event must retain source, reason, target, evidence linkage."""

    def test_belief_events_have_target_ids(self):
        """BELIEF_UPDATED events must reference which hypothesis changed."""
        world = create_confirmation_trap_world(seed=42)
        ctrl = ScientificController()
        result = ctrl.run_episode(world.initial_state, world.evidence_rounds)

        belief_events = [
            e for e in result.events
            if e.event_type == ScientificEventType.BELIEF_UPDATED
        ]
        assert len(belief_events) > 0

        for event in belief_events:
            assert len(event.target_ids) > 0, "BELIEF_UPDATED must reference target hypothesis"
            assert event.rationale != "", "BELIEF_UPDATED must have rationale"
            assert "prior" in event.payload, "BELIEF_UPDATED must record prior"
            assert "posterior" in event.payload, "BELIEF_UPDATED must record posterior"

    def test_evidence_events_have_content(self):
        """EVIDENCE_OBSERVED events must reference evidence details."""
        world = create_confirmation_trap_world(seed=42)
        ctrl = ScientificController()
        result = ctrl.run_episode(world.initial_state, world.evidence_rounds)

        evidence_events = [
            e for e in result.events
            if e.event_type == ScientificEventType.EVIDENCE_OBSERVED
        ]
        assert len(evidence_events) > 0

        for event in evidence_events:
            assert len(event.target_ids) > 0, "EVIDENCE_OBSERVED must reference evidence_id"
            assert "direction" in event.payload

    def test_abandonment_events_have_threshold_rationale(self):
        """HYPOTHESIS_ABANDONED events must explain why."""
        world = create_confirmation_trap_world(seed=42)
        ctrl = ScientificController(
            belief_updater=BeliefUpdater(
                base_update_strength=0.4,
                falsification_multiplier=3.0,
                abandonment_threshold=0.15,
            )
        )
        result = ctrl.run_episode(world.initial_state, world.evidence_rounds)

        abandon_events = [
            e for e in result.events
            if e.event_type == ScientificEventType.HYPOTHESIS_ABANDONED
        ]
        # May or may not trigger depending on parameters; if it does, check provenance
        for event in abandon_events:
            assert len(event.target_ids) > 0
            assert "threshold" in event.rationale.lower() or "dropped" in event.rationale.lower()


class TestNoHiddenMutation:
    """Controller must not alter shared state outside event application."""

    def test_evidence_list_not_shared(self):
        """Evidence rounds passed to controller must not be modified."""
        world = create_confirmation_trap_world(seed=42)
        rounds_before = [len(r.evidence) for r in world.evidence_rounds]

        ctrl = ScientificController()
        ctrl.run_episode(world.initial_state, world.evidence_rounds)

        rounds_after = [len(r.evidence) for r in world.evidence_rounds]
        assert rounds_before == rounds_after

    def test_controller_instances_independent(self):
        """Two controller instances must not share state."""
        world = create_confirmation_trap_world(seed=42)

        ctrl1 = ScientificController()
        ctrl2 = ScientificController()

        r1 = ctrl1.run_episode(world.initial_state, world.evidence_rounds)
        r2 = ctrl2.run_episode(world.initial_state, world.evidence_rounds)

        assert r1.belief_trajectory == r2.belief_trajectory
