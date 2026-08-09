# ASAR-REE: Reflexive Epistemic Ecology — Architecture Specification

> Parent: [PROJECT_DOSSIER.md](../../PROJECT_DOSSIER.md) · [decision-log.md](decision-log.md) ADR-005, ADR-006
> See also: [system-overview.md](system-overview.md) (legacy) · [component-map.md](component-map.md)

## 1. Research Thesis

Intelligence in autonomous research may depend less on producing one excellent reasoning trajectory and more on maintaining a healthy, self-correcting ecology of competing representations under bounded cognitive resources.

ASAR-REE transforms ASAR from a sequential research pipeline into an experimental architecture for artificial epistemic intelligence. The fundamental unit is no longer a pipeline stage but an epistemic state transition:

```
E_t → a_t → o_t → E_(t+1)
```

Where `E_t` is the epistemic state at step t, `a_t` is a metacognitively selected cognitive action, and `o_t` is the observation/result.

## 2. Five Persistent Models

REE maintains five explicit, typed, inspectable models:

| Model | Question It Answers | Key Contents |
|-------|-------------------|-------------|
| **World Model** | What might be true? | Hypotheses, assumptions, predictions, falsifiers, contradictions, evidence, causal relationships, belief posteriors |
| **Self Model** | What am I good/bad at? | Empirically measured capabilities by task/strategy/model/tool, calibration history, failure patterns |
| **Other Model** | What do other actors know/believe? | Probabilistic models of sources, experts, stakeholders — beliefs, goals, knowledge, incentives |
| **Value Model** | What should matter? | Task-level epistemic values (accuracy, completeness, novelty, cost), norm conflicts, hard constraints |
| **Ignorance Model** | What do I know I don't know? | Missing evidence, untested assumptions, confounders, ontology gaps, model limitations |

## 3. Central State: EpistemicState

```
EpistemicState = {
    world_model:      HypothesisGraph + AssumptionGraph + EvidenceSet + ResearchGraph
    self_model:        CapabilityEstimates + CalibrationHistory + StrategyReliability
    other_model:      StakeholderModels + SourceTrustScores
    value_model:       ValuePrinciples + NormConflicts + HardConstraints
    ignorance_model:  IgnoranceLedger
    workspace_state:  BoundedWorkspace (active artifacts competing for attention)
    budget_state:      TokenBudget + LatencyBudget + CostBudget
    process_state:     StepCount + OperatorHistory + StoppingSignals
    version:           MonotonicallyIncreasingCounter
}
```

EpistemicState is immutable. New states are produced by the reducer applying events.

## 4. Event-Sourced Architecture

Every state transition records an `EpistemicEvent`:

```
EpistemicEvent = {
    event_id, timestamp, version,
    action: EpistemicAction,
    rationale: str,
    result: OperatorResult,
    resource_cost: ResourceCost,
    state_before_version: int,
    state_after_version: int
}
```

Properties: append-only, replayable, forkable, diffable. No state is ever overwritten.

## 5. Cognitive Operator Model

Fixed pipeline stages are replaced by swappable `CognitiveOperator`s:

```python
class CognitiveOperator(Protocol):
    def propose(self, state: EpistemicState, context: WorkspaceContext) -> list[EpistemicActionBid]: ...
    def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult: ...
```

Operators include: REASON, RETRIEVE, GENERATE_HYPOTHESIS, ATTACK_HYPOTHESIS, CHECK_SOURCE, SIMULATE_COUNTERFACTUAL, DESIGN_EXPERIMENT, CONSOLIDATE_MEMORY, SYNTHESIZE, STOP, ABSTAIN, and more.

Operators never mutate state directly. They return typed results. The reducer applies changes.

## 6. Epistemic Market / Metacognitive Controller

The signature controller. Each candidate operation submits a bid:

```
EpistemicActionBid = {
    operator, action,
    expected_information_gain, probability_changes_decision,
    expected_falsification_value, novelty_gain,
    token_cost, latency, money_cost, failure_risk
}
```

The controller selects the action maximizing expected net epistemic utility:

```
selected = argmax(epistemic_value - compute_cost - latency_cost - financial_cost - risk)
```

Two levels: (1) heuristic/calibrated scheduler working immediately, (2) learnable scheduler infrastructure for training from logged trajectories.

## 7. Bounded Epistemic Workspace

A typed workspace where artifacts compete for active inclusion based on: relevance, surprise, contradiction, expected uncertainty reduction, decision impact, novelty, urgency, redundancy penalty.

The workspace is bounded. Tests verify: irrelevant material does not improve priority; duplicates do not dominate; contradictions receive appropriate salience.

## 8. Hypothesis Ecology

Explicit hypothesis competition with typed tracking: statement, ontology frame, prior, posterior, supporting/attacking evidence, assumptions, predictions, falsifiers, lineage, status (proposed/active/weakened/rejected/superseded).

Hypothesis generation optimizes for both plausibility and useful diversity.

## 9. Abduction-Deduction-Testing Cycle

```
observation → abduction → candidate explanation → deduced predictions
→ potential discriminating evidence → observation → belief revision
```

For every high-value hypothesis: "What observation would meaningfully reduce belief in this?"

## 10. Assumption Graph / Duhem-Quine Handling

When evidence conflicts with prediction, the system identifies which combination of hypothesis, auxiliary assumptions, measurement assumptions, source reliability, and ontology could explain the failure.

## 11. Ontology Forge and Possible Worlds

Multiple candidate ontologies/model frames. Conclusions are tracked as: invariant across worlds, ontology-dependent, assumption-sensitive, underdetermined.

## 12. Counterfactual Laboratory

Perturbation engine testing robustness (stability under irrelevant perturbations) and responsiveness (change under causally decisive perturbations).

## 13. Ignorance Ledger

Persistent, prioritizable. Types: missing_evidence, unknown_variable, confound, source_dependency, untested_assumption, ontology_gap, contradiction, model_limitation. Priority ≈ decision_relevance × impact × resolvability / cost.

## 14. Dissonance Tribunal

Not ordinary multi-agent debate. Sealed first round (independent reasoning before cross-examination). Transient epistemic roles (Advocate, Falsifier, Judge, Minority Curator, etc.). Evidence-based adjudication, not majority vote.

## 15. Social Epistemology

Track evidence independence, copied evidence, common source ancestry. Do not treat N citations as N independent pieces of evidence if they share a common source.

## 16. Federated Memory

Seven functional stores: working, episodic, semantic/belief, procedural, self-model, prospective, ignorance. Each with provenance and temporal state. Consolidation, reconsolidation, forgetting are explicit operations.

## 17. Module Map

```
asar/
    epistemic/       State, events, reducer, store, workspace, diff
    world_model/     Hypotheses, assumptions, predictions, contradictions, research graph
    ontology/        Frames, counterfactual engine, sensitivity analysis
    operators/       CognitiveOperator implementations
    metacognition/   Controller, market, stopping, calibration
    self_model/      Capability model, tracker, predictor
    social/          Tribunal, roles, trust, evidence independence, stakeholders
    value_model/     Principles, reflective equilibrium
    ignorance/       Ledger
    memory_federation/ 7 stores + consolidation + replay
    orchestration/ree/ REE orchestration entry point
    evaluation/      Epistemic metrics, benchmarks, metamorphic tests, ablations
```

## 18. Invariants (REE Runtime)

1. **Grounded output** — every claim traces to evidence with provenance (strengthened by event sourcing)
2. **Typed boundaries** — all inter-component data uses Pydantic schemas
3. **Reproducible experiments** — event sourcing enables deterministic replay
4. **Generation ≠ verification** — separate operators produce and check claims
5. **Queryable memory** — every record's functional store and temporal state are always queryable
6. **Swappable operators** — any operator replaceable if protocol contract holds
7. **Reducer-only mutation** — operators return typed results; only the reducer mutates state; no operator imports or invokes another operator
8. **Append-only history** — epistemic events are never overwritten; historical belief versions remain queryable

## 19. Coexistence with Legacy

Both runtimes coexist via `config/pipeline.toml` `[runtime] mode = "legacy" | "ree"`. Legacy components are preserved at their original paths. REE modules are additive. Retirement requires ADR, functional parity proof, and historical reproducibility.
