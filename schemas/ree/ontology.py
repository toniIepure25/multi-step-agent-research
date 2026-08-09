"""
Ontology schemas — frames, possible worlds, counterfactuals, and experiment design.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime


class OntologyFrame(BaseModel):
    """A conceptual frame through which the research question is interpreted."""

    frame_id: str
    name: str
    description: str = Field(default="")
    key_variables: list[str] = Field(default_factory=list)
    key_relations: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    parent_frame_id: Optional[str] = Field(
        default=None,
        description="ID of the frame this was derived from (lineage)",
    )
    active: bool = Field(default=True)
    created_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConclusionInvariance(str, Enum):
    """Classification of a conclusion's dependency on ontological framing."""
    INVARIANT = "invariant_across_worlds"
    ONTOLOGY_DEPENDENT = "ontology_dependent"
    ASSUMPTION_SENSITIVE = "assumption_sensitive"
    UNDERDETERMINED = "underdetermined"


class CounterfactualWorld(BaseModel):
    """A possible world with altered assumptions, evidence, or causal structure."""

    world_id: str
    base_world_id: Optional[str] = Field(default=None, description="World this was derived from")
    frame_id: str = Field(default="default")
    description: str = Field(default="")
    perturbation_type: str = Field(
        default="assumption_change",
        description="assumption_change | evidence_removal | source_reliability | causal | ontology | value",
    )
    perturbation_details: dict[str, Any] = Field(default_factory=dict)
    modified_assumptions: dict[str, Any] = Field(default_factory=dict)
    modified_evidence_ids: list[str] = Field(default_factory=list)
    conclusion: Optional[str] = Field(default=None)
    conclusion_changed: Optional[bool] = Field(default=None)
    invariance_classification: Optional[ConclusionInvariance] = Field(default=None)


class SensitivityResult(BaseModel):
    """Result of testing assumption/evidence sensitivity."""

    target_id: str = Field(description="ID of the assumption or evidence being tested")
    target_type: str = Field(description="assumption | evidence | source | ontology")
    perturbation: str
    original_conclusion: str = Field(default="")
    perturbed_conclusion: str = Field(default="")
    conclusion_changed: bool = Field(default=False)
    change_magnitude: float = Field(default=0.0, ge=0.0, le=1.0)
    is_causally_decisive: bool = Field(default=False)


class ExperimentCandidate(BaseModel):
    """A proposed experiment or evidence-gathering action."""

    experiment_id: str
    description: str
    target_hypotheses: list[str] = Field(default_factory=list)
    expected_information_gain: float = Field(default=0.5, ge=0.0, le=1.0)
    discrimination_power: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="How strongly outcomes differ across competing hypotheses",
    )
    falsification_value: float = Field(default=0.5, ge=0.0, le=1.0)
    estimated_cost: float = Field(default=0.5, ge=0.0)
    estimated_latency_ms: float = Field(default=0.0, ge=0.0)
    feasibility: float = Field(default=0.5, ge=0.0, le=1.0)
    risk: float = Field(default=0.1, ge=0.0, le=1.0)
    priority_score: float = Field(default=0.0, ge=0.0)
