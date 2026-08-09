"""
Self Model schemas — empirical capability tracking and calibration.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime


class EpisodeRecord(BaseModel):
    """Record of a single research episode for self-model training."""

    episode_id: str
    task_signature: str = Field(default="", description="Domain/task type fingerprint")
    domain: str = Field(default="general")
    model_provider: str = Field(default="")
    strategy_sequence: list[str] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    confidence_predicted: float = Field(default=0.5, ge=0.0, le=1.0)
    success_actual: float = Field(default=0.0, ge=0.0, le=1.0)
    hypothesis_diversity: float = Field(default=0.0, ge=0.0, le=1.0)
    contradictions_encountered: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    latency_ms: float = Field(default=0.0, ge=0.0)
    failure_type: Optional[str] = Field(default=None)
    abstained: bool = Field(default=False)
    timestamp: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class CapabilityEstimate(BaseModel):
    """Estimated capability for a task/strategy/model combination."""

    task_signature: str
    strategy: str = Field(default="")
    model_provider: str = Field(default="")
    estimated_success_rate: float = Field(default=0.5, ge=0.0, le=1.0)
    sample_count: int = Field(default=0, ge=0)
    confidence_interval_lower: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_interval_upper: float = Field(default=1.0, ge=0.0, le=1.0)
    last_updated: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CalibrationPoint(BaseModel):
    """A single (predicted_confidence, actual_success) pair for calibration analysis."""

    predicted: float = Field(ge=0.0, le=1.0)
    actual: float = Field(ge=0.0, le=1.0)
    task_signature: str = Field(default="")
    episode_id: str = Field(default="")
