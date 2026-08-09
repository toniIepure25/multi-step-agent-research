"""
World Model schemas — hypotheses, assumptions, predictions, falsifiers,
contradictions, and the research graph.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime


class HypothesisStatus(str, Enum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    WEAKENED = "weakened"
    REJECTED = "rejected"
    UNRESOLVED = "unresolved"
    SUPERSEDED = "superseded"


class Hypothesis(BaseModel):
    """A candidate explanation or claim under investigation."""

    hypothesis_id: str
    statement: str
    ontology_frame: str = Field(default="default")
    prior: float = Field(default=0.5, ge=0.0, le=1.0)
    posterior: float = Field(default=0.5, ge=0.0, le=1.0)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    attacking_evidence_ids: list[str] = Field(default_factory=list)
    assumption_ids: list[str] = Field(default_factory=list)
    prediction_ids: list[str] = Field(default_factory=list)
    falsifier_ids: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    explanatory_scope: str = Field(default="")
    lineage: list[str] = Field(
        default_factory=list,
        description="IDs of hypotheses this was derived from or supersedes",
    )
    status: HypothesisStatus = Field(default=HypothesisStatus.PROPOSED)
    generation_method: str = Field(default="", description="How this hypothesis was generated")
    created_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Assumption(BaseModel):
    """An auxiliary assumption that hypotheses depend on."""

    assumption_id: str
    text: str
    criticality: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="How critical this assumption is; 1.0 = changing it would change the conclusion",
    )
    dependent_hypothesis_ids: list[str] = Field(default_factory=list)
    tested: bool = Field(default=False)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    category: str = Field(
        default="auxiliary",
        description="auxiliary | measurement | source_reliability | ontological | methodological",
    )


class Prediction(BaseModel):
    """A deduced prediction from a hypothesis — observable if hypothesis is true."""

    prediction_id: str
    hypothesis_id: str
    statement: str
    observable: bool = Field(default=True)
    observed: Optional[bool] = Field(default=None)
    discriminating_power: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="How much observing this prediction would discriminate between hypotheses",
    )
    evidence_ids: list[str] = Field(default_factory=list)


class Falsifier(BaseModel):
    """An observation that would meaningfully reduce belief in a hypothesis."""

    falsifier_id: str
    hypothesis_id: str
    statement: str
    observation_feasibility: float = Field(default=0.5, ge=0.0, le=1.0)
    impact_if_observed: float = Field(
        default=0.8, ge=0.0, le=1.0,
        description="How much belief would decrease if this were observed",
    )
    observed: Optional[bool] = Field(default=None)


class Contradiction(BaseModel):
    """An explicit contradiction between two or more artifacts."""

    contradiction_id: str
    artifact_ids: list[str] = Field(min_length=2)
    description: str
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    resolved: bool = Field(default=False)
    resolution: Optional[str] = Field(default=None)


class BeliefSnapshot(BaseModel):
    """A snapshot of belief for trajectory tracking."""

    hypothesis_id: str
    version: int = Field(ge=0)
    posterior: float = Field(ge=0.0, le=1.0)
    status: HypothesisStatus
    event_id: str = Field(default="")
    timestamp: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResearchNodeType(str, Enum):
    QUESTION = "question"
    SUBQUESTION = "subquestion"
    HYPOTHESIS = "hypothesis"
    ASSUMPTION = "assumption"
    PREDICTION = "prediction"
    EVIDENCE_NEED = "evidence_need"
    EVIDENCE = "evidence"
    EXPERIMENT = "experiment"
    COUNTERFACTUAL = "counterfactual"
    CONTRADICTION = "contradiction"
    IGNORANCE_ITEM = "ignorance_item"
    CONCLUSION = "conclusion"


class ResearchEdgeType(str, Enum):
    REQUIRES = "requires"
    SUPPORTS = "supports"
    ATTACKS = "attacks"
    DEPENDS_ON = "depends_on"
    EXPLAINS = "explains"
    CONTRADICTS = "contradicts"
    TESTS = "tests"
    DERIVED_FROM = "derived_from"
    ALTERNATIVE_TO = "alternative_to"
    SUPERSEDES = "supersedes"


class ResearchNode(BaseModel):
    """A node in the partial-order research graph."""

    node_id: str
    node_type: ResearchNodeType
    artifact_id: str = Field(default="", description="ID of the associated artifact")
    label: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResearchEdge(BaseModel):
    """A directed edge in the research graph."""

    source_id: str
    target_id: str
    edge_type: ResearchEdgeType
    weight: float = Field(default=1.0, ge=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
