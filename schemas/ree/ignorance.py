"""
Ignorance Model schemas — persistent tracking of known unknowns.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime


class IgnoranceType(str, Enum):
    MISSING_EVIDENCE = "missing_evidence"
    UNKNOWN_VARIABLE = "unknown_variable"
    CONFOUND = "confound"
    SOURCE_DEPENDENCY = "source_dependency"
    UNTESTED_ASSUMPTION = "untested_assumption"
    ONTOLOGY_GAP = "ontology_gap"
    CONTRADICTION = "contradiction"
    MODEL_LIMITATION = "model_limitation"
    UNRESOLVED_CAUSAL_DIRECTION = "unresolved_causal_direction"
    UNREPRESENTED_STAKEHOLDER = "unrepresented_stakeholder"


class IgnoranceStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    ACCEPTED = "accepted"


class IgnoranceItem(BaseModel):
    """An explicit representation of something the system knows it doesn't know."""

    ignorance_id: str
    ignorance_type: IgnoranceType
    description: str
    probability_decision_relevant: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Probability that resolving this would change the final decision",
    )
    impact_if_resolved: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="How much resolving this would improve the answer",
    )
    resolvability: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="How feasible it is to resolve this ignorance",
    )
    estimated_cost: float = Field(
        default=0.5, ge=0.0,
        description="Estimated token/compute cost to investigate",
    )
    proposed_actions: list[str] = Field(
        default_factory=list,
        description="Suggested actions to address this ignorance",
    )
    related_hypothesis_ids: list[str] = Field(default_factory=list)
    related_assumption_ids: list[str] = Field(default_factory=list)
    status: IgnoranceStatus = Field(default=IgnoranceStatus.OPEN)
    resolution: Optional[str] = Field(default=None)
    created_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def priority_score(self) -> float:
        """Approximate priority: decision_relevance * impact * resolvability / cost."""
        cost = max(self.estimated_cost, 0.01)
        return (
            self.probability_decision_relevant
            * self.impact_if_resolved
            * self.resolvability
            / cost
        )
