"""
Tests for the REE EpistemicState, BudgetState, and ProcessState schemas.
"""

from __future__ import annotations

import pytest

from schemas.ree.epistemic_state import (
    BudgetState,
    EpistemicState,
    ProcessState,
    ResourceCost,
    WorkspaceSlot,
    WorkspaceState,
)


class TestResourceCost:
    def test_total_tokens(self) -> None:
        cost = ResourceCost(input_tokens=100, output_tokens=200)
        assert cost.total_tokens == 300

    def test_defaults_are_zero(self) -> None:
        cost = ResourceCost()
        assert cost.total_tokens == 0
        assert cost.api_cost_usd == 0.0


class TestBudgetState:
    def test_tokens_remaining(self) -> None:
        budget = BudgetState(max_tokens=1000, tokens_used=300)
        assert budget.tokens_remaining == 700

    def test_is_exhausted_when_tokens_gone(self) -> None:
        budget = BudgetState(max_tokens=100, tokens_used=100)
        assert budget.is_exhausted

    def test_is_exhausted_when_steps_gone(self) -> None:
        budget = BudgetState(max_steps=5, steps_used=5)
        assert budget.is_exhausted

    def test_not_exhausted_with_remaining(self) -> None:
        budget = BudgetState(max_tokens=1000, max_steps=10)
        assert not budget.is_exhausted

    def test_budget_fraction(self) -> None:
        budget = BudgetState(max_tokens=1000, tokens_used=250)
        assert budget.budget_fraction_remaining == pytest.approx(0.75)


class TestProcessState:
    def test_creation(self) -> None:
        ps = ProcessState(episode_id="ep_001", goal="test goal")
        assert ps.status == "active"
        assert ps.step_count == 0
        assert ps.stop_reason is None


class TestWorkspaceState:
    def test_capacity_and_occupancy(self) -> None:
        ws = WorkspaceState(capacity=5)
        assert ws.occupancy == 0
        assert not ws.is_full

    def test_is_full(self) -> None:
        slots = [
            WorkspaceSlot(artifact_id=f"a_{i}", artifact_type="test", added_at_version=0)
            for i in range(3)
        ]
        ws = WorkspaceState(capacity=3, slots=slots)
        assert ws.is_full


class TestEpistemicState:
    def test_initial_state(self) -> None:
        state = EpistemicState(
            version=0,
            process=ProcessState(episode_id="ep_001", goal="test"),
        )
        assert state.version == 0
        assert state.evidence_ids == []
        assert state.artifacts == {}
        assert state.operator_history == []

    def test_state_is_serializable(self) -> None:
        state = EpistemicState(
            version=3,
            process=ProcessState(episode_id="ep_001", goal="test"),
            evidence_ids=["evidence_001"],
            artifacts={"evidence_001": {"content": "test evidence"}},
        )
        json_str = state.model_dump_json()
        restored = EpistemicState.model_validate_json(json_str)
        assert restored.version == 3
        assert restored.evidence_ids == ["evidence_001"]

    def test_state_copy_does_not_mutate_original(self) -> None:
        state = EpistemicState(
            version=0,
            process=ProcessState(episode_id="ep_001", goal="test"),
        )
        new_state = state.model_copy(update={"version": 1})
        assert state.version == 0
        assert new_state.version == 1
