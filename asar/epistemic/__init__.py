"""
Epistemic — Core state management for the REE architecture.

Responsibilities:
- Immutable EpistemicState construction and versioning
- Append-only event store
- State reducer (applies events to produce new states)
- State diffing and trajectory analysis
- Bounded epistemic workspace with salience scoring
"""

from asar.epistemic.store import AppendOnlyEventStore
from asar.epistemic.reducer import StateReducer
from asar.epistemic.workspace import SalienceScorer, WorkspaceManager

__all__ = [
    "AppendOnlyEventStore",
    "StateReducer",
    "SalienceScorer",
    "WorkspaceManager",
]
