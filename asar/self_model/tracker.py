"""
Episode tracker — records historical episode outcomes for self-model learning.
"""

from __future__ import annotations

from schemas.ree.self_model import CalibrationPoint, EpisodeRecord


class EpisodeTracker:
    """Records and retrieves episode history for self-model training."""

    def __init__(self) -> None:
        self._records: list[EpisodeRecord] = []

    def record(self, episode: EpisodeRecord) -> None:
        self._records.append(episode)

    def all_records(self) -> list[EpisodeRecord]:
        return list(self._records)

    def by_domain(self, domain: str) -> list[EpisodeRecord]:
        return [r for r in self._records if r.domain == domain]

    def by_task_signature(self, signature: str) -> list[EpisodeRecord]:
        return [r for r in self._records if r.task_signature == signature]

    def by_strategy(self, strategy: str) -> list[EpisodeRecord]:
        return [r for r in self._records if strategy in r.strategy_sequence]

    def calibration_points(self) -> list[CalibrationPoint]:
        """Extract (predicted, actual) pairs for calibration analysis."""
        return [
            CalibrationPoint(
                predicted=r.confidence_predicted,
                actual=r.success_actual,
                task_signature=r.task_signature,
                episode_id=r.episode_id,
            )
            for r in self._records
        ]

    def success_rate(self, threshold: float = 0.5) -> float:
        """Overall success rate (fraction of episodes above threshold)."""
        if not self._records:
            return 0.0
        return sum(1 for r in self._records if r.success_actual >= threshold) / len(self._records)

    def mean_token_cost(self) -> float:
        if not self._records:
            return 0.0
        return sum(r.total_tokens for r in self._records) / len(self._records)

    def failure_type_distribution(self) -> dict[str, int]:
        """Count episodes by failure type."""
        dist: dict[str, int] = {}
        for r in self._records:
            if r.failure_type:
                dist[r.failure_type] = dist.get(r.failure_type, 0) + 1
        return dist

    def __len__(self) -> int:
        return len(self._records)
