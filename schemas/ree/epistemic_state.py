"""
EpistemicState — the central typed state for the REE architecture.

EpistemicState is immutable. New states are produced by the reducer applying events.
Every important state mutation is observable and replayable.
"""

from __future__ import annotations

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
