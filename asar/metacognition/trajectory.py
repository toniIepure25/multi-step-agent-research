"""
Trajectory dataset — records (state, action, reward) tuples for the
learned scheduler (Level 2).

State features include rich epistemic signals (hypothesis entropy,
ignorance priorities, workspace saturation, etc.) per Amendment 7.
Raw state references/event IDs are preserved so alternative features
can be reconstructed later.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TrajectoryStep:
    """A single step with rich state features for cognitive action analysis."""

    episode_id: str
    step: int
    state_version: int
    action_type: str
    operator_name: str
    bid_score: float
    outcome: str

    # Core counts
    evidence_count_before: int = 0
    hypothesis_count_before: int = 0
    claim_count_before: int = 0
    ignorance_count_before: int = 0
    assumption_count_before: int = 0

    # Budget
    budget_fraction_before: float = 1.0
    tokens_consumed: int = 0

    # Rich state features (from MaterializedViews)
    hypothesis_entropy: float = 0.0
    top_hypothesis_margin: float = 0.0
    contradiction_density: float = 0.0
    highest_ignorance_priority: float = 0.0
    mean_ignorance_priority: float = 0.0
    workspace_saturation: float = 0.0

    # Self-model features
    self_model_expected_success: float = 0.5

    # Raw references for later reconstruction
    event_id: int = 0

    # Reward (assigned post-hoc, not during collection)
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
            "ignorance_count_before": self.ignorance_count_before,
            "assumption_count_before": self.assumption_count_before,
            "budget_fraction_before": self.budget_fraction_before,
            "tokens_consumed": self.tokens_consumed,
            "hypothesis_entropy": self.hypothesis_entropy,
            "top_hypothesis_margin": self.top_hypothesis_margin,
            "contradiction_density": self.contradiction_density,
            "highest_ignorance_priority": self.highest_ignorance_priority,
            "mean_ignorance_priority": self.mean_ignorance_priority,
            "workspace_saturation": self.workspace_saturation,
            "self_model_expected_success": self.self_model_expected_success,
            "event_id": self.event_id,
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
