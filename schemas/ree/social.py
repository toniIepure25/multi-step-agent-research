"""
Social epistemology schemas — tribunal roles, stakeholder models, evidence provenance.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime


class TribunalRole(str, Enum):
    ADVOCATE = "advocate"
    FALSIFIER = "falsifier"
    ALTERNATIVE_THEORIST = "alternative_theorist"
    ASSUMPTION_AUDITOR = "assumption_auditor"
    SOURCE_PROSECUTOR = "source_prosecutor"
    INDEPENDENT_REPLICATOR = "independent_replicator"
    PERSPECTIVE_AUDITOR = "perspective_auditor"
    JUDGE = "judge"
    MINORITY_CURATOR = "minority_curator"


class TribunalSubmission(BaseModel):
    """An independent sealed-round submission from a tribunal participant."""

    submission_id: str
    role: TribunalRole
    hypothesis_id: str = Field(default="")
    position: str = Field(default="", description="The participant's independent assessment")
    evidence_cited: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    sealed: bool = Field(default=True, description="True until cross-examination begins")
    round_number: int = Field(default=1, ge=1)


class TribunalVerdict(BaseModel):
    """The tribunal's verdict after cross-examination."""

    verdict_id: str
    hypothesis_id: str
    surviving_positions: list[str] = Field(default_factory=list)
    rejected_positions: list[str] = Field(default_factory=list)
    minority_positions: list[str] = Field(
        default_factory=list,
        description="Plausible minority views preserved",
    )
    adjudication_basis: str = Field(default="evidence_weight")
    consensus_confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class StakeholderModel(BaseModel):
    """Probabilistic model of an epistemic actor (source, expert, stakeholder)."""

    actor_id: str
    name: str = Field(default="")
    actor_type: str = Field(default="source", description="source | expert | stakeholder | model")
    belief_hypotheses: dict[str, float] = Field(
        default_factory=dict,
        description="Mapping from hypothesis_id to estimated belief probability",
    )
    goal_hypotheses: list[str] = Field(default_factory=list)
    knowledge_domains: list[str] = Field(default_factory=list)
    incentives: list[str] = Field(default_factory=list)
    methodological_assumptions: list[str] = Field(default_factory=list)
    reliability_score: float = Field(default=0.5, ge=0.0, le=1.0)
    uncertainty: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="How uncertain we are about this model of the actor",
    )


class EvidenceProvenance(BaseModel):
    """Tracks the provenance chain of evidence for independence analysis."""

    evidence_id: str
    original_source_id: str = Field(default="")
    chain: list[str] = Field(
        default_factory=list,
        description="Ordered list of intermediaries from original to current",
    )
    independence_group: str = Field(
        default="",
        description="Group ID — evidence sharing a group shares a common ancestor",
    )
    is_derivative: bool = Field(default=False)
