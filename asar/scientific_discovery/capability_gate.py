"""
Stage 3 — LLM Capability Gate.

Before integrating an LLM into the scientific loop, certify that it can
produce usable structured outputs for each required primitive.

Capabilities tested:
  C1: Structured Hypothesis Generation
  C2: Mechanistic Alternatives (not paraphrases)
  C3: Prediction Derivation
  C4: Falsifier Generation
  C5: Confound Detection
  C6: Experiment Proposal
  C7: Structured Output (schema compliance)

Each capability is tested against controlled worlds where correct structures
are known, enabling objective evaluation without LLM-as-judge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Capability Definitions
# ---------------------------------------------------------------------------


class CapabilityLevel(str, Enum):
    VALID = "VALID_EXPERIMENTAL_SUBSTRATE"
    PARTIAL = "PARTIAL_SUBSTRATE"
    INVALID = "INVALID_EXPERIMENTAL_SUBSTRATE"


class CapabilityResult(BaseModel):
    """Result of testing a single capability."""

    capability_id: str
    description: str
    n_tasks: int = 0
    n_valid: int = 0
    n_partial: int = 0
    n_invalid: int = 0
    schema_compliance_rate: float = 0.0
    objective_accuracy: float = 0.0
    notes: list[str] = Field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        if self.n_tasks == 0:
            return 0.0
        return (self.n_valid + 0.5 * self.n_partial) / self.n_tasks

    @property
    def verdict(self) -> CapabilityLevel:
        if self.pass_rate >= 0.7 and self.schema_compliance_rate >= 0.8:
            return CapabilityLevel.VALID
        elif self.pass_rate >= 0.4:
            return CapabilityLevel.PARTIAL
        return CapabilityLevel.INVALID


class ModelCapabilityReport(BaseModel):
    """Full capability gate report for a single model."""

    model_id: str
    model_version: str = ""
    capabilities: dict[str, CapabilityResult] = Field(default_factory=dict)

    @property
    def overall_verdict(self) -> CapabilityLevel:
        if not self.capabilities:
            return CapabilityLevel.INVALID
        verdicts = [c.verdict for c in self.capabilities.values()]
        if all(v == CapabilityLevel.VALID for v in verdicts):
            return CapabilityLevel.VALID
        if any(v == CapabilityLevel.INVALID for v in verdicts):
            return CapabilityLevel.INVALID
        return CapabilityLevel.PARTIAL


# ---------------------------------------------------------------------------
# Capability Gate Tasks (Evaluator-Controlled)
# ---------------------------------------------------------------------------


class HypothesisGenerationTask(BaseModel):
    """Task for C1: Generate structured hypothesis from observations."""

    task_id: str
    observations: list[str]
    domain: str
    expected_mechanisms: list[str]  # canonical mechanisms for evaluation
    expected_predictions: list[str]  # what a valid hypothesis should predict


class AlternativeGenerationTask(BaseModel):
    """Task for C2: Generate mechanistically distinct alternatives."""

    task_id: str
    primary_hypothesis: str
    primary_mechanism: str
    observations: list[str]
    expected_distinct_mechanisms: list[str]  # alternatives that are NOT paraphrases


class PredictionTask(BaseModel):
    """Task for C3: Derive predictions from hypothesis + experiment."""

    task_id: str
    hypothesis: str
    mechanism: str
    experiment_description: str
    correct_predicted_outcome: str
    incorrect_outcomes: list[str]


class FalsifierTask(BaseModel):
    """Task for C4: Generate observation that would falsify hypothesis."""

    task_id: str
    hypothesis: str
    mechanism: str
    valid_falsifiers: list[str]  # observations that genuinely reduce confidence
    invalid_falsifiers: list[str]  # observations that don't actually test the hypothesis


class ConfoundTask(BaseModel):
    """Task for C5: Identify confounding explanations."""

    task_id: str
    claimed_relationship: str
    observations: list[str]
    known_confounds: list[str]


class ExperimentProposalTask(BaseModel):
    """Task for C6: Propose discriminating experiment."""

    task_id: str
    hypothesis_a: str
    hypothesis_b: str
    observation_context: str
    good_experiments: list[str]  # experiments that discriminate
    bad_experiments: list[str]  # experiments that don't discriminate


# ---------------------------------------------------------------------------
# Structured Output Schemas (what LLM must produce)
# ---------------------------------------------------------------------------


class GeneratedHypothesis(BaseModel):
    """Schema the LLM must satisfy for hypothesis generation."""

    claim: str
    mechanism: str
    scope: str = ""
    assumptions: list[str] = Field(default_factory=list)
    predictions: list[str] = Field(default_factory=list)
    falsifiers: list[str] = Field(default_factory=list)


class GeneratedAlternative(BaseModel):
    """Schema for alternative hypothesis generation."""

    claim: str
    mechanism: str
    how_it_differs: str
    predictions_different_from_primary: list[str] = Field(default_factory=list)


class GeneratedPrediction(BaseModel):
    """Schema for prediction derivation."""

    experiment: str
    predicted_outcome: str
    confidence: float = 0.5
    reasoning: str = ""


class GeneratedFalsifier(BaseModel):
    """Schema for falsifier generation."""

    observation_that_would_falsify: str
    why_this_falsifies: str
    how_to_test: str = ""


class GeneratedExperiment(BaseModel):
    """Schema for experiment proposal."""

    experiment_description: str
    what_it_tests: str
    predicted_outcome_if_h1: str
    predicted_outcome_if_h2: str
    why_discriminating: str = ""


# ---------------------------------------------------------------------------
# Self-Authorship Experiment Framework
# ---------------------------------------------------------------------------


@dataclass
class SelfAuthorshipCondition:
    """A condition in the self-authorship experiment."""

    condition_name: str  # "SELF" or "EXTERNAL"
    hypothesis_text: str
    hypothesis_mechanism: str
    provenance: str  # "self_generated" or "externally_provided"
    is_correct: bool
    evidence_trajectory: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SelfAuthorshipResult:
    """Result of one self-authorship trial."""

    condition: str
    initial_belief: float
    final_belief: float
    belief_drop: float  # initial - final (positive = reduction)
    abandonment_latency: int  # rounds until belief < threshold
    abandoned: bool
    rationalization_count: int = 0
    rescue_assumptions: int = 0


@dataclass
class SelfAuthorshipBiasReport:
    """Aggregate self-authorship bias analysis."""

    n_trials: int = 0
    mean_drop_self: float = 0.0
    mean_drop_external: float = 0.0
    bias: float = 0.0  # drop_self - drop_external (negative = bias toward self)
    abandonment_rate_self: float = 0.0
    abandonment_rate_external: float = 0.0
    mean_latency_self: float = 0.0
    mean_latency_external: float = 0.0


# ---------------------------------------------------------------------------
# Rationalization Detection
# ---------------------------------------------------------------------------


class RescueType(str, Enum):
    ABANDON = "ABANDON"
    LEGITIMATE_REVISION = "LEGITIMATE_REVISION"
    AD_HOC_RESCUE = "AD_HOC_RESCUE"
    IGNORE_EVIDENCE = "IGNORE_EVIDENCE"
    CREATE_NEAR_DUPLICATE = "CREATE_NEAR_DUPLICATE"


@dataclass
class RationalizationEvent:
    """A detected rationalization attempt."""

    hypothesis_id: str
    round_idx: int
    rescue_type: RescueType
    new_assumptions_added: int = 0
    independently_supported: bool = False
    reduces_falsifiability: bool = False


def compute_rationalization_rate(events: list[RationalizationEvent], n_falsifications: int) -> float:
    """Rate of unsupported rescue assumptions per decisive falsification."""
    if n_falsifications == 0:
        return 0.0
    rescues = sum(1 for e in events if e.rescue_type in (RescueType.AD_HOC_RESCUE, RescueType.CREATE_NEAR_DUPLICATE))
    return rescues / n_falsifications
