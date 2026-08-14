# Forensic Architecture Audit — ASAR Scientific Discovery Program

**Date:** 2026-08-14
**Branch:** `feature/asar-ree-v2`
**Starting SHA:** `82683e486bd3d5de670b8a0558595244c7ab7429`
**Git Status:** Extensive unstaged modifications across all `asar/`, `schemas/`, `tests/`, `docs/`, `config/`, `experiments/` directories
**Test Suite:** Could not execute (Python 3.11 download blocked by corporate proxy TLS; system has Python 3.9.6 only)

---

## 1. Repository Overview

The repository contains **two distinct architectural systems** and a **frozen research paper**:

| System | Purpose | Status |
|--------|---------|--------|
| **v0 Sequential Pipeline** | `SimplePlanner → WebSearchExecutor → WorkingMemory → SimpleSynthesizer → EvidenceChecker → ExperimentLogger → SequentialOrchestrator` | Functional; the original ASAR design |
| **REE (Reflexive Epistemic Ecology)** | Event-sourced epistemic architecture with market-based operator selection | Partially active via eval runners; tied to the retrieval paper |
| **Retrieval/Reasoning Paper** | Intermediate artifacts / retrieval–reasoning dissociation study | FROZEN (campaigns v1–v6 complete) |

---

## 2. Component Classification Map

### BEHAVIORALLY_ACTIVE — Wired into runtime paths

| Module | Path | What it does |
|--------|------|--------------|
| `asar/epistemic/store.py` | `EpistemicController` → eval runners | Append-only event log |
| `asar/epistemic/reducer.py` | `EpistemicController` → eval runners | Event → state projection |
| `asar/metacognition/controller.py` | Benchmark/semantic/baseline runners | REE main loop |
| `asar/metacognition/market.py` | `EpistemicController` | Operator bid selection (EpistemicMarket, DiversityAware, RoundRobin) |
| `asar/metacognition/stopping.py` | `EpistemicController` | Rule-based stopping decisions |
| `asar/metacognition/trajectory.py` | `EpistemicController` | Trajectory recording |
| `asar/operators/registry.py` | `EpistemicController` + all eval | Operator registration/dispatch |
| `asar/operators/stop.py` (StopOperator) | Eval runners | Termination operator |
| `asar/orchestration/sequential_orchestrator.py` | v0 demo path | Sequential pipeline execution |
| `asar/planning/simple_planner.py` | v0 demo | Plan generation |
| `asar/execution/web_search_executor.py` | v0 demo | Search execution |
| `asar/memory/working_memory.py` | v0 demo | Evidence storage |
| `asar/deliberation/simple_synthesizer.py` | v0 demo | Answer synthesis |
| `asar/verification/evidence_checker.py` | v0 demo | Claim verification |
| `asar/evaluation/experiment_logger.py` | v0 demo | Experiment recording |
| `asar/evaluation/benchmark_runner.py` | REE eval | Campaign orchestration |
| `asar/evaluation/semantic_runner.py` | REE eval | Semantic intervention studies |
| `asar/evaluation/baselines.py` | REE eval | Baseline conditions |
| `asar/evaluation/counterfactual_study.py` | REE eval | Counterfactual ablation |
| `asar/evaluation/epistemic_metrics.py` | REE eval | Metric computation |
| `asar/evaluation/statistical.py` | REE eval | Statistical tests |

### IMPLEMENTED_BUT_NOT_CAUSAL — Code exists, nothing calls it in production

| Module | What it implements | Why it's inactive |
|--------|-------------------|-------------------|
| `asar/epistemic/diff.py` | State comparison utility (`compute_diff`) | Only used in one test; not exported |
| `asar/operators/retrieve.py` | Real search-backed retrieval operator | Eval uses `ScenarioRetrieveOperator` / `SimRetrieveOperator` instead |
| `asar/operators/reason.py` | LLM reasoning operator | Eval uses `ScenarioReasonOperator` / `SimReasonOperator` |
| `asar/operators/synthesize.py` | LLM synthesis operator | Never registered in any eval runner |
| `asar/operators/stop.py` (AbstainOperator) | Abstention under uncertainty | Only in mechanism influence tests |
| `asar/social/stakeholder.py` | Stakeholder trust registry | Zero production callers |
| `asar/social/tribunal.py` | Sealed-round dissonance tribunal | Zero production callers (ablation flag name exists but isn't wired) |
| `asar/social/trust.py` | Evidence independence analysis | Zero production callers (used in property tests only) |
| `asar/value_model/principles.py` | Epistemic value registry | Zero production callers |
| `asar/value_model/equilibrium.py` | Reflective equilibrium engine | Zero production callers |

### STANDALONE_LIBRARY — Complete, isolated, usable

| Module | What it implements | Quality |
|--------|-------------------|---------|
| `asar/ontology/forge.py` | Ontology frame management + lineage | Complete, tested |
| `asar/ontology/counterfactual.py` | Counterfactual world creation + sensitivity scoring | Complete, tested |
| `asar/ontology/experiment_designer.py` | Experiment candidate prioritization | Complete, tested |
| `asar/world_model/research_graph.py` | Partial-order research DAG | Complete, tested |
| `asar/memory_federation/federation.py` | 7-store federated memory | Complete, tested |
| `asar/memory_federation/consolidation.py` | Memory decay/consolidation | Complete, tested |

### REUSABLE_AFTER_REDESIGN — Good concepts, needs new integration

| Module | Concept | Gap |
|--------|---------|-----|
| `asar/epistemic/workspace.py` | Bounded workspace with salience scoring | Reducer uses fixed salience 0.5 instead |
| `asar/world_model/hypothesis_graph.py` | Hypothesis CRUD with assumptions/predictions/falsifiers | Duplicates `StateReducer._project_hypothesis` |
| `asar/world_model/belief_tracker.py` | Belief trajectory recording | Duplicates `MaterializedViews.belief_trajectory` |
| `asar/operators/hypothesis.py` | LLM hypothesis generation/attack | Eval uses parallel `Scenario*` copies |
| `asar/operators/counterfactual.py` | Heuristic sensitivity flagging | Not connected to `CounterfactualLab` |
| `asar/ignorance/ledger.py` | Structured ignorance ledger with prioritization | Runtime uses `IgnoranceView` artifacts instead |
| `asar/self_model/tracker.py` | Episode outcome tracking | Runtime uses static `SelfModelSummary` injection |
| `asar/self_model/calibration.py` | Brier score / ECE computation | Not fed by live data |
| `asar/self_model/predictor.py` | Capability prediction + abstention | Not connected to controller |

### BROKEN — None identified

All code is syntactically valid and schema-aligned. No import errors detected in static analysis.

### OBSOLETE — None formally, but:

The v0 sequential pipeline (`SimplePlanner` etc.) was superseded by the REE architecture for the paper. It remains functional but is not the direction for the Scientific Discovery Engine.

---

## 3. Schema Inventory

### v0 Schemas (`schemas/`)

| Schema | Used by |
|--------|---------|
| `ResearchPlan`, `PlanStep` | v0 planner/orchestrator |
| `TaskPacket` | v0 orchestration routing |
| `EvidenceItem` | v0 + REE (shared) |
| `DecisionPacket` | v0 deliberation |
| `VerificationResult` | v0 verification |
| `ResearchOutput` | v0 final output |
| `ExperimentRecord` | v0 evaluation |
| `CitationRecord` | Postponed to Phase 2 |

### REE Schemas (`schemas/ree/`)

| Schema file | Key types | Status |
|-------------|-----------|--------|
| `epistemic_state.py` | `EpistemicState`, `MaterializedViews`, `HypothesisView`, `BeliefSnapshot`, `IgnoranceView`, `SelfModelSummary`, `BudgetState`, `ProcessState`, `WorkspaceState` | Active core |
| `epistemic_event.py` | `EpistemicEvent`, `EpistemicAction`, `ActionType`, `EpistemicActionBid`, `EpistemicDecision`, `OperatorResult`, `OperatorOutcome` | Active core |
| `world_model.py` | `Hypothesis`, `Assumption`, `Prediction`, `Falsifier`, `Contradiction`, `BeliefSnapshot`, `ResearchNode`, `ResearchEdge` | Library-only |
| `ontology.py` | `OntologyFrame`, `CounterfactualWorld`, `SensitivityResult`, `ExperimentCandidate`, `ConclusionInvariance` | Library-only |
| `ignorance.py` | `IgnoranceItem`, `IgnoranceType` | Library-only |
| `memory.py` | `MemoryRecord`, `MemoryStore` types | Library-only |
| `self_model.py` | `EpisodeOutcome`, `CalibrationPoint`, `CapabilityEstimate` | Library-only |
| `social.py` | `StakeholderModel`, `TribunalVerdict`, `EvidenceProvenance` | Library-only |
| `value_model.py` | `EpistemicPrinciple`, `ValueConflict` | Library-only |
| `experiment.py` | Experiment tracking for campaigns | Active (eval) |

---

## 4. Evaluation Infrastructure (Paper-Tied)

The evaluation system was built specifically for the retrieval/reasoning paper:

| Component | Purpose | Reusability |
|-----------|---------|-------------|
| `benchmark_runner.py` | Campaign orchestration with `ScenarioEpisode` | Paper-specific; reusable pattern |
| `semantic_runner.py` | Semantic intervention protocol | Paper-specific methodology |
| `baselines.py` | Single-pass / fixed-order conditions | Reusable baseline pattern |
| `counterfactual_study.py` | Ablation framework | Reusable pattern |
| `epistemic_metrics.py` | REE metric computation | Partially reusable |
| `statistical.py` | Statistical significance tests | Fully reusable |
| `scenarios/generators.py` | Scenario generation | Paper-specific |
| `scenarios/semantic_generators.py` | Semantic scenarios | Paper-specific |
| `scenarios/v4_regimes.py` | Regime-specific generation | Paper-specific |

---

## 5. Duplicate Concept Map (Integration Debt)

| Concept | Active implementation | Parallel (inactive) | Resolution needed |
|---------|---------------------|--------------------|--------------------|
| Hypothesis tracking | `StateReducer._project_hypothesis` → `HypothesisView` | `HypothesisGraph` | Unify or replace |
| Belief trajectories | `MaterializedViews.belief_trajectory` | `BeliefTracker` | Merge schemas |
| Workspace management | `StateReducer._update_workspace` (fixed 0.5) | `WorkspaceManager + SalienceScorer` | Wire or supersede |
| Ignorance tracking | `IgnoranceView` via reducer | `IgnoranceLedger` | Merge |
| Self-model | Static `SelfModelSummary` injection | `EpisodeTracker + CapabilityPredictor + CalibrationAnalyzer` | Wire or supersede |
| Operator implementations | `Scenario*/Sim*` duplicates in eval | Canonical LLM operators in `asar/operators/` | Unify |

---

## 6. What Can Be Reused for Scientific Discovery

### Directly reusable (proven, tested):

1. **Event-sourced state architecture** — `AppendOnlyEventStore` + `StateReducer` pattern
2. **Typed schemas** — `Hypothesis`, `Assumption`, `Prediction`, `Falsifier`, `Contradiction` (from `schemas/ree/world_model.py`)
3. **Experiment design primitives** — `ExperimentCandidate`, `ExperimentDesigner`, `SensitivityResult` (from `schemas/ree/ontology.py`)
4. **Ontology frames** — `OntologyFrame`, `OntologyForge`, `ConclusionInvariance`
5. **Counterfactual worlds** — `CounterfactualWorld`, `CounterfactualLab`
6. **Research graph** — `ResearchNode`, `ResearchEdge`, `ResearchGraph`
7. **Market-based action selection** — `EpistemicMarket` pattern (adapt for scientific actions)
8. **Stopping policy** — `StoppingPolicy` pattern
9. **Statistical utilities** — `asar/evaluation/statistical.py`
10. **Budget management** — `BudgetState`, `ResourceCost`

### Reusable after adaptation:

1. **Hypothesis graph** — needs richer scientific fields (mechanism, scope, maturity level)
2. **Belief tracker** — needs quantitative Bayesian-inspired update, not just recording
3. **Evidence independence** — `EvidenceIndependenceAnalyzer` is exactly what's needed
4. **Ignorance ledger** — needs priority function aligned with research value
5. **Tribunal** — `DissonanceTribunal` sealed-round protocol is the right pattern for Red Team
6. **Self-model** — `CalibrationAnalyzer` + `CapabilityPredictor` are the right shape

### Paper-specific (do not reuse logic, only patterns):

1. Scenario generators — specific to retrieval experiments
2. Campaign scripts — paper-specific conditions
3. Semantic intervention protocol — paper methodology

---

## 7. Critical Architectural Gap for Scientific Discovery

The existing REE architecture has these fundamental limitations for building a Scientific Discovery Engine:

1. **No falsification operator** — hypotheses are generated and attacked but there's no explicit `FALSIFY_HYPOTHESIS` action that derives predictions and searches for disconfirmation
2. **No belief update mechanism** — posteriors are set by operators producing artifacts, not by a principled update rule
3. **No experiment execution** — `ExperimentDesigner` proposes but nothing executes computational experiments
4. **No theory abandonment** — status transitions exist (`REJECTED`) but no explicit abandonment logic with threshold
5. **No ontology revision trigger** — `OntologyForge` exists but nothing detects when revision is needed
6. **No hypothesis maturity model** — all hypotheses are equal regardless of testability
7. **No discrimination scoring** — experiment selection doesn't compute information gain across competing hypotheses
8. **No sealed-round independence** — tribunal exists but isn't wired; no enforcement of independent evaluation
9. **No novelty audit** — no prior-art checking pipeline
10. **No reproducible scientific loop** — the REE loop is optimized for retrieval tasks, not scientific investigation

---

## 8. Runtime Path Trace

### v0 Demo Path
```
SequentialOrchestrator.run()
  → SimplePlanner.create_plan()        → ResearchPlan
  → for step in plan:
      → WebSearchExecutor.execute()    → [EvidenceItem]
      → WorkingMemory.store()
  → SimpleSynthesizer.synthesize()     → ResearchOutput
  → EvidenceChecker.verify()           → VerificationResult
  → ExperimentLogger.log()             → ExperimentRecord
```

### REE Evaluation Path
```
EpistemicController.run_episode()
  → Initialize EpistemicState
  → Loop:
      → All operators: .propose(state) → [EpistemicActionBid]
      → EpistemicMarket.select(bids)   → EpistemicDecision
      → Winning operator: .execute()   → OperatorResult
      → StateReducer.apply(event)      → new EpistemicState
      → StoppingPolicy.should_stop()   → StoppingDecision
      → Record trajectory
  → Return final state + events
```

Neither path implements the Scientific Discovery Loop described in the prompt.

---

## 9. Test Coverage Summary

| Category | Test files | Count |
|----------|-----------|-------|
| v0 pipeline | `test_common_foundations.py`, `test_planning.py`, `test_execution.py`, `test_memory_foundations.py`, `test_deliberation.py`, `test_verification.py`, `test_evaluation.py`, `test_orchestration.py`, `test_schemas.py`, `test_v0_integration.py`, `test_demo.py` | 11 |
| REE architecture | `test_ree_controller.py`, `test_ree_integration.py`, `test_ree_properties.py`, `test_ree_metamorphic.py`, `test_mechanism_influence.py`, `test_baselines_scenario.py`, `test_counterfactual_study.py` | 7 |
| REE components | `test_epistemic_market.py`, `test_epistemic_metrics.py`, `test_epistemic_state.py`, `test_stopping.py`, `test_world_model.py`, `test_ontology.py`, `test_ignorance.py`, `test_memory_federation.py`, `test_self_model.py`, `test_social.py`, `test_value_model.py` | 11 |
| Live providers | `test_live_providers.py` | 1 |

**Total: 30 test files**

---

## 10. Conclusion

The repository contains substantial implemented infrastructure, most of which was built for the retrieval/reasoning paper. The key finding is:

**Many components exist but are not behaviorally active.** The scientific concepts needed for the Discovery Engine (hypothesis ecology, falsification, belief revision, experiment design, ontology revision) exist as schemas and standalone libraries but are NOT integrated into any runtime loop that performs actual scientific reasoning.

The path forward is NOT to wire these into the old REE controller. Instead, build a new `ScientificController` that:
1. Reuses proven primitives (event store, typed schemas, market pattern, stopping)
2. Extends the type system for scientific maturity, falsifiability, discrimination
3. Implements the falsification-first loop as a genuinely new research capability
4. Uses controlled benchmarks to validate each mechanism's behavioral influence

The existing code provides a strong foundation of typed, tested primitives. What's missing is the scientific reasoning logic that connects them into a falsification-driven discovery process.
