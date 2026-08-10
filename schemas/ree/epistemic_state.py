"""
EpistemicState — the central typed state for the REE architecture.

EpistemicState is immutable. New states are produced by the reducer applying events.
Every important state mutation is observable and replayable.

MaterializedViews are the authoritative rich projections produced by the reducer
from the event stream. Replay must reconstruct equivalent rich state.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime


class ResourceCost(BaseModel):
    """Tracks compute resources consumed by an operation."""

    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    latency_ms: float = Field(default=0.0, ge=0.0)
    api_cost_usd: float = Field(default=0.0, ge=0.0)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class BudgetState(BaseModel):
    """Remaining compute budget for an episode."""

    max_tokens: int = Field(default=100_000, ge=0)
    max_steps: int = Field(default=50, ge=0)
    max_cost_usd: float = Field(default=10.0, ge=0.0)
    max_latency_ms: float = Field(default=300_000.0, ge=0.0)
    tokens_used: int = Field(default=0, ge=0)
    steps_used: int = Field(default=0, ge=0)
    cost_used_usd: float = Field(default=0.0, ge=0.0)
    latency_used_ms: float = Field(default=0.0, ge=0.0)

    @property
    def tokens_remaining(self) -> int:
        return max(0, self.max_tokens - self.tokens_used)

    @property
    def steps_remaining(self) -> int:
        return max(0, self.max_steps - self.steps_used)

    @property
    def budget_fraction_remaining(self) -> float:
        if self.max_tokens == 0:
            return 0.0
        return self.tokens_remaining / self.max_tokens

    @property
    def is_exhausted(self) -> bool:
        return self.tokens_remaining <= 0 or self.steps_remaining <= 0


class ProcessState(BaseModel):
    """Tracks the progression of a research episode."""

    episode_id: str = Field(..., description="Unique identifier for this research episode")
    goal: str = Field(..., description="The research question being investigated")
    step_count: int = Field(default=0, ge=0)
    status: str = Field(default="active", description="active | completed | stopped | abstained")
    stop_reason: Optional[str] = Field(default=None)
    started_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkspaceSlot(BaseModel):
    """An artifact occupying a slot in the bounded workspace."""

    artifact_id: str
    artifact_type: str
    salience: float = Field(default=0.5, ge=0.0, le=1.0)
    added_at_version: int = Field(ge=0)
    content_summary: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkspaceState(BaseModel):
    """The bounded epistemic workspace state."""

    capacity: int = Field(default=20, ge=1)
    slots: list[WorkspaceSlot] = Field(default_factory=list)

    @property
    def occupancy(self) -> int:
        return len(self.slots)

    @property
    def is_full(self) -> bool:
        return self.occupancy >= self.capacity


# ---------------------------------------------------------------------------
# Materialized Views — projected by the reducer from the event stream
# ---------------------------------------------------------------------------

class HypothesisView(BaseModel):
    """Authoritative materialized view of a hypothesis."""

    hypothesis_id: str
    statement: str = ""
    ontology_frame: str = "default"
    prior: float = Field(default=0.5, ge=0.0, le=1.0)
    posterior: float = Field(default=0.5, ge=0.0, le=1.0)
    status: str = "proposed"
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    attacking_evidence_ids: list[str] = Field(default_factory=list)
    assumption_ids: list[str] = Field(default_factory=list)
    prediction_ids: list[str] = Field(default_factory=list)
    falsifier_ids: list[str] = Field(default_factory=list)
    generation_method: str = ""


class BeliefSnapshot(BaseModel):
    """A single point in a hypothesis's belief trajectory."""

    hypothesis_id: str
    version: int
    posterior: float
    status: str


class IgnoranceView(BaseModel):
    """Authoritative materialized view of an ignorance item."""

    ignorance_id: str
    ignorance_type: str = "unknown"
    description: str = ""
    priority: float = Field(default=0.0, ge=0.0)
    status: str = "open"
    related_hypothesis_ids: list[str] = Field(default_factory=list)
    impact_if_resolved: float = Field(default=0.5, ge=0.0, le=1.0)
    resolvability: float = Field(default=0.5, ge=0.0, le=1.0)


class SelfModelSummary(BaseModel):
    """Cross-episode capability summary injected into initial state."""

    operator_success_rates: dict[str, float] = Field(default_factory=dict)
    operator_mean_cost: dict[str, float] = Field(default_factory=dict)
    domain_competence: dict[str, float] = Field(default_factory=dict)
    overall_success_rate: float = 0.5
    overall_calibration_error: float = 0.5
    episode_count: int = 0


class MaterializedViews(BaseModel):
    """Rich epistemic views projected from the event stream by the reducer.

    These are the AUTHORITATIVE representations. No component other than
    the reducer writes to views. Operators read but never mutate.
    Replay from (initial_state, events) reconstructs identical views.
    """

    hypotheses: dict[str, HypothesisView] = Field(default_factory=dict)
    belief_trajectory: list[BeliefSnapshot] = Field(default_factory=list)
    ignorance_items: dict[str, IgnoranceView] = Field(default_factory=dict)
    self_model: SelfModelSummary = Field(default_factory=SelfModelSummary)

    # Derived features recomputed each step by the reducer
    hypothesis_entropy: float = Field(default=0.0, ge=0.0)
    top_hypothesis_margin: float = Field(default=0.0, ge=0.0)
    contradiction_density: float = Field(default=0.0, ge=0.0)
    highest_ignorance_priority: float = Field(default=0.0, ge=0.0)
    mean_ignorance_priority: float = Field(default=0.0, ge=0.0)
    workspace_saturation: float = Field(default=0.0, ge=0.0, le=1.0)
    decision_stability: float = Field(default=0.0, ge=0.0, le=1.0)

    def compute_derived(
        self,
        workspace: WorkspaceState,
        contradiction_count: int,
        evidence_count: int,
    ) -> "MaterializedViews":
        """Recompute derived features from current view state."""
        posteriors = [h.posterior for h in self.hypotheses.values()
                      if h.status not in ("rejected", "superseded")]

        entropy = 0.0
        margin = 0.0
        if posteriors:
            total = sum(posteriors) or 1.0
            probs = [p / total for p in posteriors]
            entropy = -sum(p * math.log2(p) for p in probs if p > 0)
            sorted_p = sorted(probs, reverse=True)
            margin = (sorted_p[0] - sorted_p[1]) if len(sorted_p) >= 2 else 1.0

        ign_priorities = [i.priority for i in self.ignorance_items.values()
                          if i.status == "open"]
        highest_ign = max(ign_priorities) if ign_priorities else 0.0
        mean_ign = (sum(ign_priorities) / len(ign_priorities)) if ign_priorities else 0.0

        ws_sat = workspace.occupancy / workspace.capacity if workspace.capacity > 0 else 0.0
        c_density = contradiction_count / max(1, evidence_count)

        return self.model_copy(update={
            "hypothesis_entropy": entropy,
            "top_hypothesis_margin": margin,
            "contradiction_density": min(1.0, c_density),
            "highest_ignorance_priority": highest_ign,
            "mean_ignorance_priority": mean_ign,
            "workspace_saturation": ws_sat,
        })


class EpistemicState(BaseModel):
    """
    Central state for the Reflexive Epistemic Ecology.

    Immutable: the reducer produces new instances by applying events.
    Each version is monotonically increasing and unique within an episode.
    """

    version: int = Field(default=0, ge=0, description="Monotonically increasing state version")
    process: ProcessState
    budget: BudgetState = Field(default_factory=BudgetState)
    workspace: WorkspaceState = Field(default_factory=WorkspaceState)
    views: MaterializedViews = Field(default_factory=MaterializedViews)

    evidence_ids: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    hypothesis_ids: list[str] = Field(default_factory=list)
    assumption_ids: list[str] = Field(default_factory=list)
    ignorance_ids: list[str] = Field(default_factory=list)
    contradiction_ids: list[str] = Field(default_factory=list)

    artifacts: dict[str, Any] = Field(
        default_factory=dict,
        description="All typed artifacts indexed by ID (hypotheses, evidence, claims, etc.)",
    )

    operator_history: list[str] = Field(
        default_factory=list,
        description="Ordered list of operator names invoked so far",
    )
