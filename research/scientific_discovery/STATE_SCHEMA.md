# Scientific Belief State Schema

**Purpose:** Define the machine-readable state that the Scientific Discovery Engine maintains and updates throughout a research episode.

---

## Central State Object

```python
ScientificState = (
    W_t,  # World model / causal model
    H_t,  # Competing hypothesis ecology
    A_t,  # Explicit assumptions
    E_t,  # Evidence + provenance
    I_t,  # Ignorance / unresolved questions
    C_t,  # Contradictions / confounders
    M_t,  # Method/tool reliability model
    B_t,  # Remaining scientific budget
)
```

Every component is typed, versioned, and event-sourced.

---

## 1. StructuredHypothesis

```python
@dataclass
class StructuredHypothesis:
    hypothesis_id: str
    claim: str
    causal_mechanism: str
    scope: str
    assumptions: list[str]  # assumption_ids
    derived_predictions: list[str]  # prediction_ids
    expected_observations_if_true: list[str]
    expected_observations_if_false: list[str]
    potential_falsifiers: list[str]  # falsifier_ids
    known_supporting_evidence: list[str]  # evidence_ids
    known_conflicting_evidence: list[str]  # evidence_ids
    alternative_explanations: list[str]  # hypothesis_ids
    confounders: list[str]
    uncertainties: list[str]
    novelty_status: NoveltyClass
    confidence: float  # [0, 1]
    confidence_basis: str
    maturity: HypothesisMaturity
    created_from: str  # provenance
    revision_history: list[RevisionEvent]
    created_at: datetime
    last_updated_at: datetime
    status: HypothesisStatus
    authorship: Authorship  # self-generated vs external
```

---

## 2. Hypothesis Maturity Levels

```python
class HypothesisMaturity(Enum):
    H0_SPECULATIVE = "speculative_idea"
    H1_MECHANISTIC = "mechanistic_hypothesis"
    H2_FALSIFIABLE = "falsifiable_hypothesis"
    H3_DISCRIMINATIVE = "discriminatively_testable"
    H4_TESTED = "empirically_tested"
    H5_SURVIVED = "survived_independent_challenge"
```

A hypothesis advances ONLY when specific criteria are met:
- H0 → H1: Causal mechanism specified
- H1 → H2: At least one falsifiable prediction derived
- H2 → H3: Predictions differ from competing hypotheses
- H3 → H4: Experiment executed, results observed
- H4 → H5: Independent replication/challenge survived

---

## 3. HypothesisEcology

```python
@dataclass
class HypothesisEcology:
    hypotheses: dict[str, StructuredHypothesis]
    diversity_metrics: DiversityMetrics
    pairwise_discriminability: dict[tuple[str, str], float]
    
    def mechanism_diversity(self) -> float: ...
    def prediction_diversity(self) -> float: ...
    def assumption_diversity(self) -> float: ...
    def is_genuine_ecology(self) -> bool: ...  # vs. paraphrase list
```

**Diversity requirements:**
- Mechanism diversity: hypotheses must invoke different causal paths
- Prediction diversity: hypotheses must make different observable predictions
- Assumption diversity: hypotheses must differ in key assumptions
- Minimum pairwise discriminability threshold

---

## 4. Prediction

```python
@dataclass
class Prediction:
    prediction_id: str
    hypothesis_id: str
    statement: str
    observable: bool
    discriminating_power: float  # [0, 1] - how much this distinguishes from alternatives
    expected_if_true: str
    expected_if_false: str
    observed: Optional[bool]
    observation_evidence: list[str]  # evidence_ids
```

---

## 5. Falsifier

```python
@dataclass
class Falsifier:
    falsifier_id: str
    hypothesis_id: str
    statement: str  # "What observation would make H substantially less likely?"
    observation_feasibility: float  # [0, 1]
    impact_if_observed: float  # [0, 1] - belief drop magnitude
    attack_vector: str  # which assumption or mechanism it attacks
    observed: Optional[bool]
    observation_evidence: Optional[str]  # evidence_id
```

---

## 6. Assumption

```python
@dataclass
class Assumption:
    assumption_id: str
    text: str
    criticality: float  # [0, 1] - how much conclusion depends on this
    dependent_hypotheses: list[str]
    tested: bool
    confidence: float  # [0, 1]
    category: AssumptionCategory  # auxiliary | measurement | source | ontological | methodological
    test_strategy: Optional[str]
```

---

## 7. Evidence with Provenance

```python
@dataclass
class ScientificEvidence:
    evidence_id: str
    content: str
    source: str
    source_type: SourceType  # literature | computation | observation | expert | meta-analysis
    reliability: float  # [0, 1]
    relevance_to_hypotheses: dict[str, float]  # hypothesis_id → relevance
    direction: EvidenceDirection  # supporting | contradicting | neutral | ambiguous
    independence_group: str  # for tracking shared root sources
    provenance: EvidenceProvenance
    timestamp: datetime
```

```python
@dataclass
class EvidenceProvenance:
    original_source: str
    derived_from: list[str]  # parent evidence_ids
    shared_dataset: Optional[str]
    shared_experiment: Optional[str]
    citation_chain: list[str]
```

---

## 8. BeliefState

```python
@dataclass
class BeliefState:
    beliefs: dict[str, float]  # hypothesis_id → P(H)
    history: list[BeliefSnapshot]
    
    def update(
        self,
        hypothesis_id: str,
        evidence: ScientificEvidence,
        likelihood_ratio: float,
        independence_weight: float,
    ) -> "BeliefState": ...
    
    def abandonment_check(self, hypothesis_id: str, threshold: float) -> bool: ...
```

```python
@dataclass
class BeliefSnapshot:
    hypothesis_id: str
    prior: float
    posterior: float
    evidence_id: str  # what caused the update
    update_magnitude: float
    timestamp: datetime
    version: int
```

---

## 9. Ignorance Ledger

```python
@dataclass
class IgnoranceItem:
    unknown_id: str
    question: str
    decision_relevance: float  # [0, 1]
    expected_impact: float  # [0, 1]
    resolvability: float  # [0, 1]
    estimated_cost: float
    dependencies: list[str]
    blocking_hypotheses: list[str]
    status: IgnoranceStatus  # open | resolved | accepted | intractable
    
    @property
    def priority(self) -> float:
        """Priority = (relevance × impact × resolvability) / cost"""
        if self.estimated_cost <= 0:
            return 0.0
        return (self.decision_relevance * self.expected_impact * self.resolvability) / self.estimated_cost
```

---

## 10. Experiment Candidate

```python
@dataclass
class ExperimentCandidate:
    experiment_id: str
    description: str
    target_hypotheses: list[str]
    predicted_outcomes: PredictedOutcomeTable
    expected_information_gain: float
    discrimination_power: float
    falsification_value: float
    estimated_cost: float
    feasibility: float
    risk: float
    confound_controls: list[str]
    priority_score: float  # EIG - λ₁·Cost - λ₂·Risk
```

```python
@dataclass
class PredictedOutcomeTable:
    """For each hypothesis, what outcome is expected."""
    outcomes: dict[str, dict[str, float]]  # hypothesis_id → {outcome: probability}
    
    def discrimination_score(self) -> float:
        """How much outcomes differ across hypotheses."""
        ...
```

---

## 11. Scientific Budget

```python
@dataclass
class ScientificBudget:
    max_llm_calls: int
    max_search_queries: int
    max_compute_seconds: int
    max_cost_usd: float
    max_experiment_rounds: int
    used: ResourceUsage
    
    @property
    def is_exhausted(self) -> bool: ...
    
    @property
    def fraction_remaining(self) -> float: ...
```

---

## 12. Conclusion Types

```python
class ConclusionType(Enum):
    SUPPORTED = "supported"
    REFUTED = "refuted"
    MIXED = "mixed"
    UNDERDETERMINED = "underdetermined"
    NOT_IDENTIFIABLE = "not_identifiable"
    ABSTAIN = "abstain"
    NEEDS_EXPERIMENT = "needs_experiment"
```

---

## 13. Novelty Classification

```python
class NoveltyClass(Enum):
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
```

---

## 14. Event Types (Event-Sourced Science)

```python
class ScientificEventType(Enum):
    PROBLEM_FRAMED = "problem_framed"
    HYPOTHESIS_PROPOSED = "hypothesis_proposed"
    ALTERNATIVE_GENERATED = "alternative_generated"
    ASSUMPTION_ADDED = "assumption_added"
    PREDICTION_DERIVED = "prediction_derived"
    FALSIFIER_PROPOSED = "falsifier_proposed"
    EXPERIMENT_DESIGNED = "experiment_designed"
    EXPERIMENT_EXECUTED = "experiment_executed"
    EVIDENCE_OBSERVED = "evidence_observed"
    EVIDENCE_CHALLENGED = "evidence_challenged"
    BELIEF_UPDATED = "belief_updated"
    HYPOTHESIS_REFUTED = "hypothesis_refuted"
    HYPOTHESIS_ABANDONED = "hypothesis_abandoned"
    ONTOLOGY_REVISED = "ontology_revised"
    NOVELTY_DOWNGRADED = "novelty_downgraded"
    RESEARCH_STOPPED = "research_stopped"
```

---

## 15. Full ScientificState

```python
@dataclass
class ScientificState:
    version: int
    episode_id: str
    research_question: str
    
    # Core scientific objects
    ecology: HypothesisEcology
    assumptions: dict[str, Assumption]
    predictions: dict[str, Prediction]
    falsifiers: dict[str, Falsifier]
    evidence: dict[str, ScientificEvidence]
    beliefs: BeliefState
    ignorance: dict[str, IgnoranceItem]
    contradictions: dict[str, Contradiction]
    experiments: dict[str, ExperimentCandidate]
    
    # Process tracking
    budget: ScientificBudget
    conclusion: Optional[ConclusionType]
    ontology_frame: str
    event_log: list[ScientificEvent]
    
    # Metadata
    created_at: datetime
    last_updated_at: datetime
```

---

## Design Principles

1. **Immutable state** — new states produced by applying events to previous state
2. **Event-sourced** — every transition recorded; full replay support
3. **Typed boundaries** — all inter-component data uses these schemas
4. **No hidden mutation** — components read state, propose actions, produce events
5. **Forkable** — scientific trajectories can be branched for counterfactual analysis
6. **Machine-readable** — never free-form prose as authoritative state
