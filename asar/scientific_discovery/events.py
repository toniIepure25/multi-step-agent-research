"""
Scientific Events — typed records of every state transition in a scientific episode.

Events are append-only and enable: replay, state reconstruction, forking,
belief trajectory analysis, and counterfactual branching.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime


class ScientificEventType(str, Enum):
    """All possible state transitions in the scientific loop."""

    PROBLEM_FRAMED = "problem_framed"
    HYPOTHESIS_PROPOSED = "hypothesis_proposed"
    ALTERNATIVE_GENERATED = "alternative_generated"
    ASSUMPTION_ADDED = "assumption_added"
    PREDICTION_DERIVED = "prediction_derived"
    FALSIFIER_PROPOSED = "falsifier_proposed"
    EXPERIMENT_DESIGNED = "experiment_designed"
    EXPERIMENT_EXECUTED = "experiment_executed"
    EVIDENCE_OBSERVED = "evidence_observed"
    EVIDENCE_CHALLENGED = "evidence_challenged"
    BELIEF_UPDATED = "belief_updated"
    HYPOTHESIS_WEAKENED = "hypothesis_weakened"
    HYPOTHESIS_REFUTED = "hypothesis_refuted"
    HYPOTHESIS_ABANDONED = "hypothesis_abandoned"
    HYPOTHESIS_STRENGTHENED = "hypothesis_strengthened"
    ONTOLOGY_REVISED = "ontology_revised"
    NOVELTY_DOWNGRADED = "novelty_downgraded"
    CONTRADICTION_DETECTED = "contradiction_detected"
    CONTRADICTION_RESOLVED = "contradiction_resolved"
    IGNORANCE_ADDED = "ignorance_added"
    IGNORANCE_RESOLVED = "ignorance_resolved"
    RESEARCH_STOPPED = "research_stopped"


class ScientificEvent(BaseModel):
    """
    A single immutable record of a state transition in the scientific loop.

    Events are append-only. The full event log enables replay and analysis.
    """

    event_id: str
    episode_id: str
    event_type: ScientificEventType
    version_before: int = Field(ge=0)
    version_after: int = Field(ge=0)
    timestamp: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # What was affected
    target_ids: list[str] = Field(
        default_factory=list,
        description="IDs of hypotheses/evidence/assumptions affected",
    )

    # What was produced or changed
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific data (new artifacts, updated values, etc.)",
    )

    # Why this happened
    rationale: str = Field(default="", description="Why this transition occurred")
    triggered_by: Optional[str] = Field(
        default=None, description="Event ID or action that caused this"
    )
