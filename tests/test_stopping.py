"""
Tests for the stopping policy and trajectory dataset.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from asar.metacognition.stopping import StoppingDecision, StoppingPolicy
from asar.metacognition.trajectory import TrajectoryDataset, TrajectoryStep
from schemas.ree.epistemic_state import (
    BudgetState,
    EpistemicState,
    ProcessState,
)


def _make_state(
    step_count: int = 0,
    evidence_ids: list[str] | None = None,
    claim_ids: list[str] | None = None,
    hypothesis_ids: list[str] | None = None,
    ignorance_ids: list[str] | None = None,
    contradiction_ids: list[str] | None = None,
    operator_history: list[str] | None = None,
    tokens_used: int = 0,
    max_tokens: int = 10000,
    max_steps: int = 50,
    artifacts: dict | None = None,
) -> EpistemicState:
    return EpistemicState(
        version=step_count,
        process=ProcessState(
            episode_id="ep_test",
            goal="test",
            step_count=step_count,
        ),
        budget=BudgetState(
            max_tokens=max_tokens,
            max_steps=max_steps,
            tokens_used=tokens_used,
            steps_used=step_count,
        ),
        evidence_ids=evidence_ids or [],
        claim_ids=claim_ids or [],
        hypothesis_ids=hypothesis_ids or [],
        ignorance_ids=ignorance_ids or [],
        contradiction_ids=contradiction_ids or [],
        operator_history=operator_history or [],
        artifacts=artifacts or {},
    )


class TestStoppingPolicy:
    def test_continue_below_min_steps(self) -> None:
        policy = StoppingPolicy(min_steps_before_stop=3)
        state = _make_state(step_count=1)
        result = policy.evaluate(state)
        assert result.decision == StoppingDecision.CONTINUE

    def test_stop_on_budget_exhaustion(self) -> None:
        policy = StoppingPolicy()
        state = _make_state(tokens_used=10000, max_tokens=10000, claim_ids=["c1"])
        result = policy.evaluate(state)
        assert result.decision == StoppingDecision.STOP

    def test_return_partial_on_budget_no_claims(self) -> None:
        policy = StoppingPolicy()
        state = _make_state(tokens_used=10000, max_tokens=10000)
        result = policy.evaluate(state)
        assert result.decision == StoppingDecision.RETURN_PARTIAL

    def test_stop_after_synthesis_low_ignorance(self) -> None:
        policy = StoppingPolicy()
        state = _make_state(
            step_count=5,
            evidence_ids=["e1"],
            claim_ids=["c1"],
            operator_history=["retrieve", "synthesize"],
        )
        result = policy.evaluate(state)
        assert result.decision == StoppingDecision.STOP

    def test_abstain_no_evidence_after_many_steps(self) -> None:
        policy = StoppingPolicy(min_steps_before_stop=2)
        state = _make_state(step_count=6, evidence_ids=[])
        result = policy.evaluate(state)
        assert result.decision == StoppingDecision.ABSTAIN

    def test_continue_when_work_needed(self) -> None:
        policy = StoppingPolicy(min_steps_before_stop=2)
        state = _make_state(
            step_count=3,
            evidence_ids=["e1"],
            claim_ids=[],
            operator_history=["retrieve"],
        )
        result = policy.evaluate(state)
        assert result.decision == StoppingDecision.CONTINUE

    def test_near_budget_exhaustion(self) -> None:
        policy = StoppingPolicy(budget_exhaustion_threshold=0.1)
        state = _make_state(tokens_used=9600, max_tokens=10000, step_count=3)
        result = policy.evaluate(state)
        assert result.decision == StoppingDecision.STOP


class TestTrajectoryDataset:
    def _make_step(
        self,
        episode_id: str = "ep_001",
        step: int = 0,
        action_type: str = "retrieve",
        reward: float = 0.5,
    ) -> TrajectoryStep:
        return TrajectoryStep(
            episode_id=episode_id,
            step=step,
            state_version=step,
            action_type=action_type,
            operator_name=action_type,
            bid_score=0.5,
            outcome="success",
            evidence_count_before=0,
            hypothesis_count_before=0,
            claim_count_before=0,
            budget_fraction_before=1.0,
            tokens_consumed=100,
            reward=reward,
        )

    def test_record_and_retrieve(self) -> None:
        ds = TrajectoryDataset()
        ds.record(self._make_step())
        assert len(ds) == 1

    def test_by_episode(self) -> None:
        ds = TrajectoryDataset()
        ds.record(self._make_step("ep_a"))
        ds.record(self._make_step("ep_b"))
        ds.record(self._make_step("ep_a", step=1))
        assert len(ds.by_episode("ep_a")) == 2

    def test_episode_ids(self) -> None:
        ds = TrajectoryDataset()
        ds.record(self._make_step("ep_a"))
        ds.record(self._make_step("ep_b"))
        ds.record(self._make_step("ep_a", step=1))
        assert ds.episode_ids() == ["ep_a", "ep_b"]

    def test_mean_reward_by_action(self) -> None:
        ds = TrajectoryDataset()
        ds.record(self._make_step(action_type="retrieve", reward=0.8))
        ds.record(self._make_step(action_type="retrieve", reward=0.6))
        ds.record(self._make_step(action_type="reason", reward=0.4))
        means = ds.mean_reward_by_action()
        assert means["retrieve"] == pytest.approx(0.7)
        assert means["reason"] == pytest.approx(0.4)

    def test_generate_training_rows(self) -> None:
        ds = TrajectoryDataset()
        ds.record(self._make_step())
        rows = ds.generate_training_rows()
        assert len(rows) == 1
        assert "action_type" in rows[0]

    def test_persistence_to_file(self, tmp_path: Path) -> None:
        path = tmp_path / "trajectories.jsonl"
        ds = TrajectoryDataset(path=path)
        ds.record(self._make_step("ep_a"))
        ds.record(self._make_step("ep_a", step=1))
        assert path.exists()
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 2
