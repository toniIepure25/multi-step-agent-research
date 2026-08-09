"""
Ignorance Ledger — persistent, prioritizable registry of known unknowns.

Priority is approximately: decision_relevance * impact * resolvability / cost.
"""

from __future__ import annotations

from schemas.ree.ignorance import IgnoranceItem, IgnoranceStatus, IgnoranceType


class IgnoranceLedger:
    """Manages the ignorance model — explicit tracking of known unknowns."""

    def __init__(self) -> None:
        self._items: dict[str, IgnoranceItem] = {}

    def add(self, item: IgnoranceItem) -> None:
        self._items[item.ignorance_id] = item

    def get(self, ignorance_id: str) -> IgnoranceItem | None:
        return self._items.get(ignorance_id)

    def all_items(self) -> list[IgnoranceItem]:
        return list(self._items.values())

    def open_items(self) -> list[IgnoranceItem]:
        return [i for i in self._items.values() if i.status == IgnoranceStatus.OPEN]

    def by_type(self, ignorance_type: IgnoranceType) -> list[IgnoranceItem]:
        return [i for i in self._items.values() if i.ignorance_type == ignorance_type]

    def prioritized(self, top_k: int | None = None) -> list[IgnoranceItem]:
        """Return open items sorted by priority score (descending)."""
        open_items = self.open_items()
        sorted_items = sorted(open_items, key=lambda i: i.priority_score, reverse=True)
        if top_k is not None:
            return sorted_items[:top_k]
        return sorted_items

    def resolve(self, ignorance_id: str, resolution: str) -> IgnoranceItem | None:
        """Mark an ignorance item as resolved."""
        item = self._items.get(ignorance_id)
        if item is None:
            return None
        updated = item.model_copy(update={
            "status": IgnoranceStatus.RESOLVED,
            "resolution": resolution,
        })
        self._items[ignorance_id] = updated
        return updated

    def accept(self, ignorance_id: str) -> IgnoranceItem | None:
        """Accept an ignorance item as an acknowledged limitation."""
        item = self._items.get(ignorance_id)
        if item is None:
            return None
        updated = item.model_copy(update={"status": IgnoranceStatus.ACCEPTED})
        self._items[ignorance_id] = updated
        return updated

    def decision_relevant_items(self, threshold: float = 0.5) -> list[IgnoranceItem]:
        """Return open items likely to affect the final decision."""
        return [
            i for i in self.open_items()
            if i.probability_decision_relevant >= threshold
        ]

    def total_unresolved_impact(self) -> float:
        """Sum of impact_if_resolved across all open items."""
        return sum(i.impact_if_resolved for i in self.open_items())

    def to_artifacts(self) -> dict[str, object]:
        """Export all items as artifacts for state storage."""
        return {item.ignorance_id: item.model_dump() for item in self._items.values()}
