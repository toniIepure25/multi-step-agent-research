"""
EpistemicEvent — typed records of every state transition in a REE episode.

Events are append-only and never overwritten. They enable replay,
state reconstruction, forking, and belief trajectory analysis.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime
from schemas.ree.epistemic_state import ResourceCost


class ActionType(str, Enum):
    """Categories of cognitive actions available to the REE controller."""

    REASON = "reason"
    RETRIEVE = "retrieve"
    GENERATE_HYPOTHESIS = "generate_hypothesis"
    ATTACK_HYPOTHESIS = "attack_hypothesis"
    CHECK_SOURCE = "check_source"
    SIMULATE_COUNTERFACTUAL = "simulate_counterfactual"
    DESIGN_EXPERIMENT = "design_experiment"
    RUN_EXPERIMENT = "run_experiment"
    REVISIT_ONTOLOGY = "revisit_ontology"
    RESOLVE_CONTRADICTION = "resolve_contradiction"
    CONSOLIDATE_MEMORY = "consolidate_memory"
    RECALL_MEMORY = "recall_memory"
    SEEK_MINORITY_VIEW = "seek_minority_view"
    SYNTHESIZE = "synthesize"
    VERIFY = "verify"
    ABSTAIN = "abstain"
    STOP = "stop"


class EpistemicAction(BaseModel):
    """A specific cognitive action to be executed by an operator."""

    action_id: str = Field(..., description="Unique identifier")
    action_type: ActionType
    operator_name: str = Field(..., description="Name of the operator that will execute this")
    parameters: dict[str, Any] = Field(default_factory=dict)
    description: str = Field(default="", description="Human-readable description of what this action does")


class EpistemicActionBid(BaseModel):
    """A bid from an operator proposing a cognitive action with estimated value."""

    action: EpistemicAction
    expected_information_gain: float = Field(default=0.0, ge=0.0, le=1.0)
    probability_changes_decision: float = Field(default=0.0, ge=0.0, le=1.0)
    expected_falsification_value: float = Field(default=0.0, ge=0.0, le=1.0)
    novelty_gain: float = Field(default=0.0, ge=0.0, le=1.0)
    expected_uncertainty_reduction: float = Field(default=0.0, ge=0.0, le=1.0)
    expected_calibration_gain: float = Field(default=0.0, ge=0.0, le=1.0)
    estimated_token_cost: int = Field(default=0, ge=0)
    estimated_latency_ms: float = Field(default=0.0, ge=0.0)
    estimated_cost_usd: float = Field(default=0.0, ge=0.0)
    failure_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    rationale: str = Field(default="")


class EpistemicDecision(BaseModel):
    """The controller's decision selecting one action from competing bids."""

    selected_bid: EpistemicActionBid
    competing_bids: list[EpistemicActionBid] = Field(default_factory=list)
    selection_score: float = Field(default=0.0)
    selection_rationale: str = Field(default="")


class OperatorOutcome(str, Enum):
    """Result status of an operator execution."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    NO_OP = "no_op"


class OperatorResult(BaseModel):
    """Typed result returned by a cognitive operator after execution."""

    operator_name: str
    action_id: str
    outcome: OperatorOutcome
    artifacts_produced: dict[str, Any] = Field(
        default_factory=dict,
        description="New artifacts (evidence, hypotheses, claims, etc.) keyed by ID",
    )
    artifacts_modified: dict[str, Any] = Field(
        default_factory=dict,
        description="Modified artifact states keyed by ID",
    )
    state_updates: dict[str, Any] = Field(
        default_factory=dict,
        description="Explicit state field updates for the reducer to apply",
    )
    workspace_additions: list[str] = Field(
        default_factory=list,
        description="Artifact IDs to consider adding to workspace",
    )
    workspace_removals: list[str] = Field(
        default_factory=list,
        description="Artifact IDs to consider removing from workspace",
    )
    resource_cost: ResourceCost = Field(default_factory=ResourceCost)
    error_message: Optional[str] = Field(default=None)
    notes: str = Field(default="")


class EpistemicEvent(BaseModel):
    """
    A single immutable record of a state transition in the epistemic loop.

    Events are append-only. The full event log enables replay,
    state reconstruction, forking, and belief trajectory analysis.
    """

    event_id: str = Field(..., description="Unique event identifier")
    episode_id: str = Field(..., description="Episode this event belongs to")
    timestamp: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version_before: int = Field(..., ge=0)
    version_after: int = Field(..., ge=0)
    action: EpistemicAction
    decision: Optional[EpistemicDecision] = Field(default=None)
    result: OperatorResult
    resource_cost: ResourceCost = Field(default_factory=ResourceCost)
    rationale: str = Field(default="", description="Why this action was selected")
