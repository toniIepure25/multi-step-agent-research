"""
Federated memory schemas — functional stores with provenance and lifecycle.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime


class MemoryStore(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    SELF_MODEL = "self_model"
    PROSPECTIVE = "prospective"
    IGNORANCE = "ignorance"


class MemoryRecordStatus(str, Enum):
    ACTIVE = "active"
    CONSOLIDATED = "consolidated"
    RECONSOLIDATED = "reconsolidated"
    DECAYED = "decayed"
    EVICTED = "evicted"


class MemoryRecord(BaseModel):
    """A record in any functional memory store."""

    record_id: str
    store: MemoryStore
    content: Any
    content_type: str = Field(default="text")
    provenance: str = Field(default="", description="Where this memory came from")
    episode_id: str = Field(default="")
    version: int = Field(default=1, ge=1)
    status: MemoryRecordStatus = Field(default=MemoryRecordStatus.ACTIVE)
    salience: float = Field(default=0.5, ge=0.0, le=1.0)
    access_count: int = Field(default=0, ge=0)
    created_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))
    superseded_by: Optional[str] = Field(default=None)
    tags: list[str] = Field(default_factory=list)


class ConsolidationEvent(BaseModel):
    """Record of a memory consolidation/reconsolidation event."""

    event_id: str
    record_id: str
    event_type: str = Field(
        default="consolidation",
        description="consolidation | reconsolidation | decay | eviction | correction",
    )
    old_content: Any = Field(default=None)
    new_content: Any = Field(default=None)
    reason: str = Field(default="")
    timestamp: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))
