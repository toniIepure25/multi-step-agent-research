"""
Value Model schemas — epistemic values, norm conflicts, and reflective equilibrium.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime


class ValuePrinciple(BaseModel):
    """A task-level epistemic value/principle."""

    principle_id: str
    name: str
    description: str = Field(default="")
    weight: float = Field(default=0.5, ge=0.0, le=1.0)
    category: str = Field(
        default="epistemic",
        description="epistemic | practical | ethical | stakeholder",
    )
    revisable: bool = Field(
        default=True,
        description="False for hard external constraints that cannot be self-revised",
    )
    revision_history: list[str] = Field(default_factory=list)


class NormConflict(BaseModel):
    """An explicit conflict between two or more value principles."""

    conflict_id: str
    principle_a_id: str
    principle_b_id: str
    context: str = Field(default="")
    affected_stakeholders: list[str] = Field(default_factory=list)
    proposed_resolution: Optional[str] = Field(default=None)
    resolution_accepted: bool = Field(default=False)
    residual_disagreement: Optional[str] = Field(default=None)
    created_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))
