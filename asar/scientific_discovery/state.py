"""
Scientific Belief State — the central typed state for the Scientific Discovery Engine.

Immutable: new states are produced by applying events to the previous state.
Every transition is observable and replayable.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class HypothesisStatus(str, Enum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    WEAKENED = "weakened"
    REJECTED = "rejected"
    ABANDONED = "abandoned"
    SUPERSEDED = "superseded"


class HypothesisMaturity(str, Enum):
    H0_SPECULATIVE = "speculative_idea"
    H1_MECHANISTIC = "mechanistic_hypothesis"
    H2_FALSIFIABLE = "falsifiable_hypothesis"
    H3_DISCRIMINATIVE = "discriminatively_testable"
    H4_TESTED = "empirically_tested"
    H5_SURVIVED = "survived_independent_challenge"


class NoveltyClass(str, Enum):
    KNOWN = "known"
    DIRECT_REDISCOVERY = "direct_rediscovery"
    CLOSE_VARIANT = "close_variant"
    KNOWN_COMPONENTS_NEW_COMBINATION = "known_components_new_combination"
    METHOD_NOVELTY = "method_novelty"
    MECHANISM_NOVELTY = "mechanism_novelty"
    PREDICTION_NOVELTY = "prediction_novelty"
    EMPIRICAL_NOVELTY = "empirical_novelty"
    POSSIBLY_NOVEL = "possibly_novel"
    NOVELTY_UNRESOLVED = "novelty_unresolved"


class AssumptionCategory(str, Enum):
    AUXILIARY = "auxiliary"
    MEASUREMENT = "measurement"
    SOURCE_RELIABILITY = "source_reliability"
    ONTOLOGICAL = "ontological"
    METHODOLOGICAL = "methodological"


class SourceType(str, Enum):
    LITERATURE = "literature"
    COMPUTATION = "computation"
    OBSERVATION = "observation"
    EXPERT = "expert"
    META_ANALYSIS = "meta_analysis"
    SIMULATION = "simulation"


class EvidenceDirection(str, Enum):
    SUPPORTING = "supporting"
    CONTRADICTING = "contradicting"
    NEUTRAL = "neutral"
    AMBIGUOUS = "ambiguous"


class ConclusionType(str, Enum):
    SUPPORTED = "supported"
    REFUTED = "refuted"
    MIXED = "mixed"
    UNDERDETERMINED = "underdetermined"
    NOT_IDENTIFIABLE = "not_identifiable"
    ABSTAIN = "abstain"
    NEEDS_EXPERIMENT = "needs_experiment"


class IgnoranceStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    ACCEPTED = "accepted"
    INTRACTABLE = "intractable"


class Authorship(str, Enum):
    SELF_GENERATED = "self_generated"
    EXTERNAL = "external"
    INHERITED = "inherited"


# ---------------------------------------------------------------------------
# Core Scientific Objects
# ---------------------------------------------------------------------------


class Prediction(BaseModel):
    """A deduced prediction from a hypothesis — observable if hypothesis is true."""

    prediction_id: str
    hypothesis_id: str
    statement: str
    observable: bool = True
    discriminating_power: float = Field(default=0.5, ge=0.0, le=1.0)
    expected_if_true: str = ""
    expected_if_false: str = ""
    observed: Optional[bool] = None
    observation_evidence_ids: list[str] = Field(default_factory=list)


class Falsifier(BaseModel):
    """An observation that would meaningfully reduce belief in a hypothesis."""

    falsifier_id: str
    hypothesis_id: str
    statement: str
    attack_vector: str = Field(default="", description="Which assumption or mechanism this attacks")
    observation_feasibility: float = Field(default=0.5, ge=0.0, le=1.0)
    impact_if_observed: float = Field(default=0.8, ge=0.0, le=1.0)
    observed: Optional[bool] = None
    observation_evidence_id: Optional[str] = None


class Assumption(BaseModel):
    """An auxiliary assumption that hypotheses depend on."""

    assumption_id: str
    text: str
    criticality: float = Field(default=0.5, ge=0.0, le=1.0)
    dependent_hypothesis_ids: list[str] = Field(default_factory=list)
    tested: bool = False
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    category: AssumptionCategory = AssumptionCategory.AUXILIARY


class EvidenceProvenance(BaseModel):
    """Tracks source independence for evidence."""

    original_source: str = ""
    derived_from: list[str] = Field(default_factory=list)
    shared_dataset: Optional[str] = None
    shared_experiment: Optional[str] = None
    independence_group: str = ""


class ScientificEvidence(BaseModel):
    """A piece of evidence with full provenance tracking."""

    evidence_id: str
    content: str
    source: str = ""
    source_type: SourceType = SourceType.LITERATURE
    reliability: float = Field(default=0.7, ge=0.0, le=1.0)
    relevance_to_hypotheses: dict[str, float] = Field(default_factory=dict)
    direction: EvidenceDirection = EvidenceDirection.NEUTRAL
    provenance: EvidenceProvenance = Field(default_factory=EvidenceProvenance)
    timestamp: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RevisionEvent(BaseModel):
    """Records a revision to a hypothesis."""

    timestamp: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))
    field_changed: str
    old_value: Any = None
    new_value: Any = None
    reason: str = ""
    evidence_id: Optional[str] = None


class StructuredHypothesis(BaseModel):
    """A structured scientific hypothesis with full falsifiability metadata."""

    hypothesis_id: str
    claim: str
    causal_mechanism: str = ""
    scope: str = ""
    assumptions: list[str] = Field(default_factory=list)
    derived_predictions: list[str] = Field(default_factory=list)
    expected_observations_if_true: list[str] = Field(default_factory=list)
    expected_observations_if_false: list[str] = Field(default_factory=list)
    potential_falsifiers: list[str] = Field(default_factory=list)
    known_supporting_evidence: list[str] = Field(default_factory=list)
    known_conflicting_evidence: list[str] = Field(default_factory=list)
    alternative_explanations: list[str] = Field(default_factory=list)
    confounders: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    novelty_status: NoveltyClass = NoveltyClass.NOVELTY_UNRESOLVED
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence_basis: str = ""
    maturity: HypothesisMaturity = HypothesisMaturity.H0_SPECULATIVE
    authorship: Authorship = Authorship.SELF_GENERATED
    created_from: str = ""
    revision_history: list[RevisionEvent] = Field(default_factory=list)
    rescue_assumptions: int = Field(default=0, ge=0)
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    created_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_falsifiable(self) -> bool:
        return len(self.potential_falsifiers) > 0

    @property
    def is_discriminative(self) -> bool:
        return len(self.derived_predictions) > 0 and len(self.alternative_explanations) > 0

    @property
    def ad_hoc_complexity(self) -> int:
        return self.rescue_assumptions


class DiversityMetrics(BaseModel):
    """Metrics for hypothesis ecology diversity."""

    mechanism_diversity: float = Field(default=0.0, ge=0.0, le=1.0)
    prediction_diversity: float = Field(default=0.0, ge=0.0, le=1.0)
    assumption_diversity: float = Field(default=0.0, ge=0.0, le=1.0)
    causal_structure_diversity: float = Field(default=0.0, ge=0.0, le=1.0)
    mean_pairwise_discriminability: float = Field(default=0.0, ge=0.0, le=1.0)


class HypothesisEcology(BaseModel):
    """Maintains competing hypotheses with diversity enforcement."""

    hypotheses: dict[str, StructuredHypothesis] = Field(default_factory=dict)
    diversity_metrics: DiversityMetrics = Field(default_factory=DiversityMetrics)

    @property
    def active_hypotheses(self) -> dict[str, StructuredHypothesis]:
        return {
            hid: h
            for hid, h in self.hypotheses.items()
            if h.status not in (HypothesisStatus.ABANDONED, HypothesisStatus.REJECTED)
        }

    @property
    def count(self) -> int:
        return len(self.hypotheses)

    @property
    def active_count(self) -> int:
        return len(self.active_hypotheses)

    def belief_distribution(self) -> dict[str, float]:
        """Current belief distribution over active hypotheses."""
        return {hid: h.confidence for hid, h in self.active_hypotheses.items()}

    def entropy(self) -> float:
        """Shannon entropy of belief distribution (higher = more uncertain)."""
        beliefs = list(self.belief_distribution().values())
        if not beliefs:
            return 0.0
        total = sum(beliefs) or 1.0
        probs = [b / total for b in beliefs]
        return -sum(p * math.log2(p) for p in probs if p > 0)

    def top_hypothesis(self) -> Optional[StructuredHypothesis]:
        active = self.active_hypotheses
        if not active:
            return None
        return max(active.values(), key=lambda h: h.confidence)

    def margin(self) -> float:
        """Confidence margin between top two hypotheses."""
        confs = sorted(
            [h.confidence for h in self.active_hypotheses.values()], reverse=True
        )
        if len(confs) < 2:
            return 1.0 if confs else 0.0
        return confs[0] - confs[1]


# ---------------------------------------------------------------------------
# Belief State
# ---------------------------------------------------------------------------


class BeliefSnapshot(BaseModel):
    """A single point in a hypothesis's belief trajectory."""

    hypothesis_id: str
    prior: float = Field(ge=0.0, le=1.0)
    posterior: float = Field(ge=0.0, le=1.0)
    evidence_id: str = ""
    update_magnitude: float = 0.0
    version: int = 0
    timestamp: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BeliefState(BaseModel):
    """Persistent belief state with update history."""

    beliefs: dict[str, float] = Field(default_factory=dict)
    history: list[BeliefSnapshot] = Field(default_factory=list)

    def get_belief(self, hypothesis_id: str) -> float:
        return self.beliefs.get(hypothesis_id, 0.5)

    def set_belief(self, hypothesis_id: str, value: float) -> "BeliefState":
        new_beliefs = dict(self.beliefs)
        new_beliefs[hypothesis_id] = max(0.0, min(1.0, value))
        return self.model_copy(update={"beliefs": new_beliefs})

    def record_update(
        self,
        hypothesis_id: str,
        prior: float,
        posterior: float,
        evidence_id: str,
        version: int,
    ) -> "BeliefState":
        snapshot = BeliefSnapshot(
            hypothesis_id=hypothesis_id,
            prior=prior,
            posterior=posterior,
            evidence_id=evidence_id,
            update_magnitude=abs(posterior - prior),
            version=version,
        )
        new_history = list(self.history) + [snapshot]
        return self.model_copy(update={"history": new_history})


# ---------------------------------------------------------------------------
# Ignorance Ledger
# ---------------------------------------------------------------------------


class IgnoranceItem(BaseModel):
    """An explicitly tracked unknown with research-control priority."""

    unknown_id: str
    question: str
    decision_relevance: float = Field(default=0.5, ge=0.0, le=1.0)
    expected_impact: float = Field(default=0.5, ge=0.0, le=1.0)
    resolvability: float = Field(default=0.5, ge=0.0, le=1.0)
    estimated_cost: float = Field(default=1.0, gt=0.0)
    dependencies: list[str] = Field(default_factory=list)
    blocking_hypotheses: list[str] = Field(default_factory=list)
    status: IgnoranceStatus = IgnoranceStatus.OPEN

    @property
    def priority(self) -> float:
        return (
            self.decision_relevance * self.expected_impact * self.resolvability
        ) / self.estimated_cost


# ---------------------------------------------------------------------------
# Scientific Budget
# ---------------------------------------------------------------------------


class ScientificBudget(BaseModel):
    """Tracks remaining scientific compute/cost budget."""

    max_steps: int = Field(default=50, ge=1)
    max_llm_calls: int = Field(default=100, ge=1)
    max_cost_usd: float = Field(default=10.0, ge=0.0)
    steps_used: int = Field(default=0, ge=0)
    llm_calls_used: int = Field(default=0, ge=0)
    cost_used_usd: float = Field(default=0.0, ge=0.0)

    @property
    def is_exhausted(self) -> bool:
        return self.steps_used >= self.max_steps or self.llm_calls_used >= self.max_llm_calls

    @property
    def fraction_remaining(self) -> float:
        step_frac = max(0, self.max_steps - self.steps_used) / self.max_steps
        call_frac = max(0, self.max_llm_calls - self.llm_calls_used) / self.max_llm_calls
        return min(step_frac, call_frac)


# ---------------------------------------------------------------------------
# Contradiction
# ---------------------------------------------------------------------------


class Contradiction(BaseModel):
    """An explicit contradiction between two or more scientific artifacts."""

    contradiction_id: str
    artifact_ids: list[str] = Field(min_length=2)
    description: str = ""
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    resolved: bool = False
    resolution: Optional[str] = None


# ---------------------------------------------------------------------------
# Full Scientific State
# ---------------------------------------------------------------------------


class ScientificState(BaseModel):
    """
    Central state for the Scientific Discovery Engine.

    Immutable: the controller produces new instances by applying events.
    Each version is monotonically increasing within an episode.
    """

    version: int = Field(default=0, ge=0)
    episode_id: str = ""
    research_question: str = ""

    ecology: HypothesisEcology = Field(default_factory=HypothesisEcology)
    assumptions: dict[str, Assumption] = Field(default_factory=dict)
    predictions: dict[str, Prediction] = Field(default_factory=dict)
    falsifiers: dict[str, Falsifier] = Field(default_factory=dict)
    evidence: dict[str, ScientificEvidence] = Field(default_factory=dict)
    beliefs: BeliefState = Field(default_factory=BeliefState)
    ignorance: dict[str, IgnoranceItem] = Field(default_factory=dict)
    contradictions: dict[str, Contradiction] = Field(default_factory=dict)

    budget: ScientificBudget = Field(default_factory=ScientificBudget)
    conclusion: Optional[ConclusionType] = None
    ontology_frame: str = "default"

    created_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def with_version(self, new_version: int) -> "ScientificState":
        return self.model_copy(
            update={"version": new_version, "last_updated_at": datetime.now(timezone.utc)}
        )
