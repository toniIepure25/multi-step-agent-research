"""
Append-only event store for REE epistemic events.

Uses JSON Lines as the storage backend — simple, inspectable,
sufficient for single-process operation. Events are never overwritten.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from schemas.ree.epistemic_event import EpistemicEvent


class AppendOnlyEventStore:
    """Stores epistemic events in append-only sequence."""

    def __init__(self, *, path: Optional[Path] = None) -> None:
        self._events: list[EpistemicEvent] = []
        self._path = path
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: EpistemicEvent) -> None:
        """Append an event. Never overwrites existing events."""
        self._events.append(event)
        if self._path is not None:
            with self._path.open("a", encoding="utf-8") as f:
                f.write(event.model_dump_json() + "\n")

    def get_all(self) -> list[EpistemicEvent]:
        """Return all events in chronological order."""
        return list(self._events)

    def get_by_episode(self, episode_id: str) -> list[EpistemicEvent]:
        """Return events for a specific episode."""
        return [e for e in self._events if e.episode_id == episode_id]

    def get_range(self, start_version: int, end_version: int) -> list[EpistemicEvent]:
        """Return events in a version range (inclusive)."""
        return [
            e for e in self._events
            if start_version <= e.version_before and e.version_after <= end_version
        ]

    def get_event(self, event_id: str) -> Optional[EpistemicEvent]:
        """Return a specific event by ID."""
        for e in self._events:
            if e.event_id == event_id:
                return e
        return None

    def __len__(self) -> int:
        return len(self._events)

    @classmethod
    def load_from_file(cls, path: Path) -> "AppendOnlyEventStore":
        """Load events from a JSON Lines file."""
        store = cls(path=path)
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        event = EpistemicEvent.model_validate_json(line)
                        store._events.append(event)
        return store

    def fork(self, from_version: int) -> "AppendOnlyEventStore":
        """Create a new store containing only events up to the given version."""
        forked = AppendOnlyEventStore()
        forked._events = [e for e in self._events if e.version_after <= from_version]
        return forked
