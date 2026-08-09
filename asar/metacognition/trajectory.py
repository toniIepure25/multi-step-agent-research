"""
Trajectory dataset — records (state, action, reward) tuples for the
learned scheduler (Level 2).

Collects training data from historical episodes. The learned scheduler
trains on: Q(E, action) from logged trajectories.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TrajectoryStep:
    """A single step in a trajectory: state summary, action taken, outcome."""

    episode_id: str
    step: int
    state_version: int
    action_type: str
    operator_name: str
    bid_score: float
    outcome: str
    evidence_count_before: int
    hypothesis_count_before: int
    claim_count_before: int
    budget_fraction_before: float
    tokens_consumed: int
    reward: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "step": self.step,
            "state_version": self.state_version,
            "action_type": self.action_type,
            "operator_name": self.operator_name,
            "bid_score": self.bid_score,
            "outcome": self.outcome,
            "evidence_count_before": self.evidence_count_before,
            "hypothesis_count_before": self.hypothesis_count_before,
            "claim_count_before": self.claim_count_before,
            "budget_fraction_before": self.budget_fraction_before,
            "tokens_consumed": self.tokens_consumed,
            "reward": self.reward,
        }


class TrajectoryDataset:
    """Collects and persists trajectory data for learned scheduler training."""

    def __init__(self, *, path: Path | None = None) -> None:
        self._steps: list[TrajectoryStep] = []
        self._path = path
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, step: TrajectoryStep) -> None:
        self._steps.append(step)
        if self._path is not None:
            with self._path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(step.to_dict()) + "\n")

    def all_steps(self) -> list[TrajectoryStep]:
        return list(self._steps)

    def by_episode(self, episode_id: str) -> list[TrajectoryStep]:
        return [s for s in self._steps if s.episode_id == episode_id]

    def episode_ids(self) -> list[str]:
        seen: set[str] = set()
        ids: list[str] = []
        for s in self._steps:
            if s.episode_id not in seen:
                seen.add(s.episode_id)
                ids.append(s.episode_id)
        return ids

    def mean_reward_by_action(self) -> dict[str, float]:
        """Average reward per action type."""
        totals: dict[str, float] = {}
        counts: dict[str, int] = {}
        for s in self._steps:
            totals[s.action_type] = totals.get(s.action_type, 0.0) + s.reward
            counts[s.action_type] = counts.get(s.action_type, 0) + 1
        return {k: totals[k] / counts[k] for k in totals}

    def generate_training_rows(self) -> list[dict[str, Any]]:
        """Generate training dataset rows for the learned scheduler."""
        return [s.to_dict() for s in self._steps]

    def __len__(self) -> int:
        return len(self._steps)
