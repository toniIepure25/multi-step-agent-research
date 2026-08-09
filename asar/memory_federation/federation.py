"""
Federated memory — manages seven functional stores.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from asar.common import generate_id
from schemas.ree.memory import (
    ConsolidationEvent,
    MemoryRecord,
    MemoryRecordStatus,
    MemoryStore,
)


class FederatedMemory:
    """Unified interface to all functional memory stores."""

    def __init__(self) -> None:
        self._records: dict[str, MemoryRecord] = {}
        self._consolidation_log: list[ConsolidationEvent] = []

    def store(
        self,
        store: MemoryStore,
        content: Any,
        *,
        content_type: str = "text",
        provenance: str = "",
        episode_id: str = "",
        salience: float = 0.5,
        tags: list[str] | None = None,
    ) -> MemoryRecord:
        """Store a new record in the specified functional store."""
        record = MemoryRecord(
            record_id=generate_id("mem"),
            store=store,
            content=content,
            content_type=content_type,
            provenance=provenance,
            episode_id=episode_id,
            salience=salience,
            tags=tags or [],
        )
        self._records[record.record_id] = record
        return record

    def retrieve(
        self,
        store: MemoryStore | None = None,
        *,
        tags: list[str] | None = None,
        min_salience: float = 0.0,
        status: MemoryRecordStatus | None = None,
        limit: int = 100,
    ) -> list[MemoryRecord]:
        """Retrieve records from one or all stores with optional filters."""
        results: list[MemoryRecord] = []
        for record in self._records.values():
            if store is not None and record.store != store:
                continue
            if record.salience < min_salience:
                continue
            if status is not None and record.status != status:
                continue
            if tags and not any(t in record.tags for t in tags):
                continue
            if record.status in (MemoryRecordStatus.EVICTED, MemoryRecordStatus.DECAYED):
                continue
            results.append(record)

        results.sort(key=lambda r: r.salience, reverse=True)
        return results[:limit]

    def get(self, record_id: str) -> MemoryRecord | None:
        return self._records.get(record_id)

    def access(self, record_id: str) -> MemoryRecord | None:
        """Access a record, updating access count and timestamp."""
        record = self._records.get(record_id)
        if record is None:
            return None
        updated = record.model_copy(update={
            "access_count": record.access_count + 1,
            "last_accessed_at": datetime.now(timezone.utc),
        })
        self._records[record_id] = updated
        return updated

    def update_content(
        self,
        record_id: str,
        new_content: Any,
        reason: str = "correction",
    ) -> MemoryRecord | None:
        """Update a record's content (reconsolidation). Old content is logged."""
        record = self._records.get(record_id)
        if record is None:
            return None

        event = ConsolidationEvent(
            event_id=generate_id("consolidation"),
            record_id=record_id,
            event_type="reconsolidation",
            old_content=record.content,
            new_content=new_content,
            reason=reason,
        )
        self._consolidation_log.append(event)

        updated = record.model_copy(update={
            "content": new_content,
            "version": record.version + 1,
            "status": MemoryRecordStatus.RECONSOLIDATED,
        })
        self._records[record_id] = updated
        return updated

    def decay(self, record_id: str, reason: str = "low salience") -> MemoryRecord | None:
        """Mark a record as decayed (soft deletion)."""
        record = self._records.get(record_id)
        if record is None:
            return None

        event = ConsolidationEvent(
            event_id=generate_id("consolidation"),
            record_id=record_id,
            event_type="decay",
            reason=reason,
        )
        self._consolidation_log.append(event)

        updated = record.model_copy(update={"status": MemoryRecordStatus.DECAYED})
        self._records[record_id] = updated
        return updated

    def evict(self, record_id: str, reason: str = "capacity limit") -> MemoryRecord | None:
        """Evict a record. It remains queryable with EVICTED status."""
        record = self._records.get(record_id)
        if record is None:
            return None

        event = ConsolidationEvent(
            event_id=generate_id("consolidation"),
            record_id=record_id,
            event_type="eviction",
            reason=reason,
        )
        self._consolidation_log.append(event)

        updated = record.model_copy(update={"status": MemoryRecordStatus.EVICTED})
        self._records[record_id] = updated
        return updated

    def store_counts(self) -> dict[str, int]:
        """Count active records per store."""
        counts: dict[str, int] = {}
        for record in self._records.values():
            if record.status not in (MemoryRecordStatus.DECAYED, MemoryRecordStatus.EVICTED):
                key = record.store.value
                counts[key] = counts.get(key, 0) + 1
        return counts

    def consolidation_history(self) -> list[ConsolidationEvent]:
        return list(self._consolidation_log)

    def version_history(self, record_id: str) -> list[ConsolidationEvent]:
        """Return consolidation events for a specific record."""
        return [e for e in self._consolidation_log if e.record_id == record_id]
