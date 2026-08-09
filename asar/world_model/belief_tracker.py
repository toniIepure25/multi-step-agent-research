"""
Belief tracker — records and analyzes belief trajectories over time.
"""

from __future__ import annotations

from datetime import datetime, timezone

from schemas.ree.world_model import BeliefSnapshot, HypothesisStatus


class BeliefTracker:
    """Tracks belief snapshots for trajectory analysis."""

    def __init__(self) -> None:
        self._snapshots: list[BeliefSnapshot] = []

    def record(
        self,
        hypothesis_id: str,
        version: int,
        posterior: float,
        status: HypothesisStatus,
        event_id: str = "",
    ) -> BeliefSnapshot:
        """Record a belief snapshot."""
        snap = BeliefSnapshot(
            hypothesis_id=hypothesis_id,
            version=version,
            posterior=posterior,
            status=status,
            event_id=event_id,
        )
        self._snapshots.append(snap)
        return snap

    def trajectory(self, hypothesis_id: str) -> list[BeliefSnapshot]:
        """Return the belief trajectory for a hypothesis, ordered by version."""
        return sorted(
            [s for s in self._snapshots if s.hypothesis_id == hypothesis_id],
            key=lambda s: s.version,
        )

    def latest(self, hypothesis_id: str) -> BeliefSnapshot | None:
        """Return the most recent snapshot for a hypothesis."""
        traj = self.trajectory(hypothesis_id)
        return traj[-1] if traj else None

    def all_snapshots(self) -> list[BeliefSnapshot]:
        return list(self._snapshots)

    def belief_delta(self, hypothesis_id: str) -> float | None:
        """Return total change in posterior from first to last snapshot."""
        traj = self.trajectory(hypothesis_id)
        if len(traj) < 2:
            return None
        return traj[-1].posterior - traj[0].posterior

    def revision_count(self, hypothesis_id: str) -> int:
        """Count how many times belief was revised."""
        traj = self.trajectory(hypothesis_id)
        if len(traj) < 2:
            return 0
        return sum(
            1 for i in range(1, len(traj))
            if abs(traj[i].posterior - traj[i - 1].posterior) > 0.01
        )

    def monotonic_change(self, hypothesis_id: str) -> bool:
        """Check if belief only moved in one direction."""
        traj = self.trajectory(hypothesis_id)
        if len(traj) < 2:
            return True
        deltas = [traj[i].posterior - traj[i - 1].posterior for i in range(1, len(traj))]
        nonzero = [d for d in deltas if abs(d) > 0.001]
        if not nonzero:
            return True
        all_positive = all(d > 0 for d in nonzero)
        all_negative = all(d < 0 for d in nonzero)
        return all_positive or all_negative
