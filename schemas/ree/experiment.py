"""
Experiment infrastructure schemas — Phase 10B.

ExperimentManifest: immutable configuration record for every run.
RealizedEpistemicGain: multi-dimensional gain vector (not prematurely scalar).
CognitiveActionOutcome: rich state/action/outcome record for policy study.
CognitiveActionRegret: hindsight oracle evaluation metric.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime


# ---------------------------------------------------------------
# ExperimentManifest — immutable architecture config per run
# ---------------------------------------------------------------

class MechanismConfig(BaseModel):
    """Configuration for a single mechanism's ablation state."""
    enabled: bool = True
    parameters: dict[str, Any] = Field(default_factory=dict)


class ExperimentManifest(BaseModel):
    """Immutable, persisted experiment configuration.

    Every run must record this — no run may merely contain
    ``architecture = "full_ree"`` without its component manifest.
    """

    experiment_id: str
    created_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))
    architecture: str = Field(description="e.g. full_ree, ree_no_tribunal, legacy, baseline_b0")
    description: str = ""

    mechanisms: dict[str, MechanismConfig] = Field(
        default_factory=dict,
        description="Per-mechanism enable/disable and parameters",
    )

    scheduler_type: str = "heuristic"
    scheduler_weights: dict[str, float] = Field(default_factory=dict)

    provider: str = "mock"
    model: str = "default"
    temperature: float = 0.0

    stopping_policy: dict[str, Any] = Field(
        default_factory=dict,
        description="StoppingPolicy constructor kwargs",
    )

    memory_regime: str = "none"
    memory_config: dict[str, Any] = Field(default_factory=dict)

    budget_max_tokens: int = 10_000
    budget_max_steps: int = 50
    budget_max_cost_usd: float = 10.0

    seed: int = 42
    scenario_split: str = Field(default="dev", description="dev | holdout")

    extra: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------
# RealizedEpistemicGain — vector, not scalar
# ---------------------------------------------------------------

class RealizedEpistemicGain(BaseModel):
    """Multi-dimensional epistemic gain vector.

    Scalarizations must be configurable and sensitivity-tested.
    """

    task_quality_delta: float = 0.0
    calibration_delta: float = 0.0
    hypothesis_discrimination_delta: float = 0.0
    contradiction_resolution_delta: float = 0.0
    ignorance_reduction_delta: float = 0.0
    provenance_quality_delta: float = 0.0
    robustness_delta: float = 0.0
    compute_cost: float = Field(default=0.0, ge=0.0)

    def scalarize(self, weights: dict[str, float] | None = None) -> float:
        """Configurable weighted scalarization. Default: equal weights minus cost."""
        default_weights = {
            "task_quality_delta": 1.0,
            "calibration_delta": 0.5,
            "hypothesis_discrimination_delta": 0.5,
            "contradiction_resolution_delta": 0.3,
            "ignorance_reduction_delta": 0.5,
            "provenance_quality_delta": 0.3,
            "robustness_delta": 0.3,
            "compute_cost": -0.1,
        }
        w = weights or default_weights
        total = 0.0
        for field_name, weight in w.items():
            total += weight * getattr(self, field_name, 0.0)
        return total

    def to_vector(self) -> list[float]:
        return [
            self.task_quality_delta,
            self.calibration_delta,
            self.hypothesis_discrimination_delta,
            self.contradiction_resolution_delta,
            self.ignorance_reduction_delta,
            self.provenance_quality_delta,
            self.robustness_delta,
            self.compute_cost,
        ]


# ---------------------------------------------------------------
# CognitiveActionOutcome — rich state/action/outcome for Phase 12
# ---------------------------------------------------------------

class EpistemicStateFeatures(BaseModel):
    """Rich state features extracted from EpistemicState + MaterializedViews.

    Avoids leaking final outcomes into state features.
    """

    hypothesis_entropy: float = 0.0
    top_hypothesis_margin: float = 0.0
    belief_volatility: float = 0.0
    support_strength: float = 0.0
    contradiction_density: float = 0.0
    highest_ignorance_priority: float = 0.0
    mean_ignorance_priority: float = 0.0
    evidence_independence: float = 1.0
    workspace_saturation: float = 0.0
    workspace_diversity: float = 0.0
    ontology_count: int = 1
    ontology_disagreement: float = 0.0
    assumption_graph_depth: int = 0
    recent_prediction_error: float = 0.0
    self_model_expected_success: float = 0.5
    operator_historical_reliability: float = 0.5
    budget_fraction: float = 1.0
    decision_stability: float = 0.0
    recent_operator_sequence: list[str] = Field(default_factory=list)

    evidence_count: int = 0
    hypothesis_count: int = 0
    claim_count: int = 0
    ignorance_count: int = 0
    assumption_count: int = 0
    step_count: int = 0

    state_version: int = 0
    episode_id: str = ""
    event_ids: list[int] = Field(
        default_factory=list,
        description="Raw event references for reconstruction",
    )


class CognitiveActionOutcome(BaseModel):
    """A single (state, action, outcome) record for cognitive policy study.

    This is the core data type for Phase 12. Each record contains:
    - Rich state features at time of action selection
    - The action taken (type + operator)
    - The realized epistemic gain VECTOR
    - The bid that was submitted
    - The resource cost
    """

    outcome_id: str
    episode_id: str
    step: int

    state_features: EpistemicStateFeatures
    action_type: str
    operator_name: str
    bid_score: float = 0.0
    bid_information_gain: float = 0.0

    realized_gain: RealizedEpistemicGain = Field(default_factory=RealizedEpistemicGain)
    resource_cost_tokens: int = 0
    resource_cost_usd: float = 0.0

    continuation_budget_tokens: int = 0

    @property
    def scalarized_gain(self) -> float:
        return self.realized_gain.scalarize()


# ---------------------------------------------------------------
# CognitiveActionRegret — hindsight oracle metric
# ---------------------------------------------------------------

class CognitiveActionRegret(BaseModel):
    """Hindsight oracle evaluation construct.

    regret = RealizedUtility(best_tested_action) - RealizedUtility(selected_action)

    The oracle is an evaluation construct, NOT a deployable policy.
    """

    fork_state_version: int
    episode_id: str

    selected_action: str
    selected_gain: RealizedEpistemicGain
    selected_scalar: float = 0.0

    best_action: str
    best_gain: RealizedEpistemicGain
    best_scalar: float = 0.0

    regret: float = Field(default=0.0, ge=0.0)

    all_tested_actions: dict[str, float] = Field(
        default_factory=dict,
        description="action_type → scalarized realized gain",
    )

    scalarization_weights: dict[str, float] = Field(default_factory=dict)

    @classmethod
    def compute(
        cls,
        *,
        fork_state_version: int,
        episode_id: str,
        selected_action: str,
        outcomes: dict[str, RealizedEpistemicGain],
        weights: dict[str, float] | None = None,
    ) -> "CognitiveActionRegret":
        """Compute regret from a set of forked action outcomes."""
        scalars = {a: g.scalarize(weights) for a, g in outcomes.items()}
        best_action = max(scalars, key=scalars.get)  # type: ignore[arg-type]
        selected_scalar = scalars.get(selected_action, 0.0)
        best_scalar = scalars[best_action]

        return cls(
            fork_state_version=fork_state_version,
            episode_id=episode_id,
            selected_action=selected_action,
            selected_gain=outcomes.get(selected_action, RealizedEpistemicGain()),
            selected_scalar=selected_scalar,
            best_action=best_action,
            best_gain=outcomes[best_action],
            best_scalar=best_scalar,
            regret=max(0.0, best_scalar - selected_scalar),
            all_tested_actions=scalars,
            scalarization_weights=weights or {},
        )
