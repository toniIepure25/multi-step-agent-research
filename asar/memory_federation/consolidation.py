"""
Memory consolidation — offline replay and lifecycle management.

Implements consolidation, reconsolidation, forgetting/decay,
and schema formation. Measures whether offline consolidation
improves later performance.
"""

from __future__ import annotations

from asar.memory_federation.federation import FederatedMemory
from schemas.ree.memory import MemoryRecordStatus, MemoryStore


class MemoryConsolidator:
    """Performs offline consolidation of memory stores."""

    def __init__(
        self,
        memory: FederatedMemory,
        *,
        decay_threshold: float = 0.1,
        max_per_store: int = 100,
    ) -> None:
        self._memory = memory
        self._decay_threshold = decay_threshold
        self._max_per_store = max_per_store

    def run_consolidation(self) -> dict[str, int]:
        """Run a consolidation pass across all stores.

        Returns counts of actions taken per type.
        """
        actions: dict[str, int] = {"decayed": 0, "evicted": 0, "consolidated": 0}

        for record in list(self._memory._records.values()):
            if record.status in (MemoryRecordStatus.DECAYED, MemoryRecordStatus.EVICTED):
                continue

            if record.salience < self._decay_threshold and record.access_count == 0:
                self._memory.decay(record.record_id, "consolidation: low salience, never accessed")
                actions["decayed"] += 1

        for store in MemoryStore:
            store_records = self._memory.retrieve(store, limit=10000)
            if len(store_records) > self._max_per_store:
                sorted_records = sorted(store_records, key=lambda r: r.salience)
                excess = len(store_records) - self._max_per_store
                for record in sorted_records[:excess]:
                    self._memory.evict(record.record_id, "consolidation: store capacity exceeded")
                    actions["evicted"] += 1

        actions["consolidated"] = actions["decayed"] + actions["evicted"]
        return actions

    def detect_contradictions(self) -> list[tuple[str, str, str]]:
        """Detect potential contradictions between semantic memory records.

        Returns list of (record_id_a, record_id_b, description).
        Simple heuristic: records with overlapping tags but differing content.
        """
        semantic = self._memory.retrieve(MemoryStore.SEMANTIC)
        contradictions: list[tuple[str, str, str]] = []

        for i, a in enumerate(semantic):
            for b in semantic[i + 1:]:
                if not a.tags or not b.tags:
                    continue
                overlap = set(a.tags) & set(b.tags)
                if overlap and a.content != b.content:
                    contradictions.append((
                        a.record_id,
                        b.record_id,
                        f"Records share tags {overlap} but have different content",
                    ))

        return contradictions

    def correct_stale_belief(
        self,
        record_id: str,
        new_content: object,
        reason: str = "superseded by new evidence",
    ) -> bool:
        """Update a stale semantic belief with new content."""
        result = self._memory.update_content(record_id, new_content, reason)
        return result is not None
