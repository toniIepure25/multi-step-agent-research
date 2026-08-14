# ASAR SCIENTIFIC DISCOVERY PROGRAM — CHECKPOINT 001

**Date:** 2026-08-14
**Stage:** 0 (Audit + Design) COMPLETE → Stage 1 (Core Implementation) COMPLETE

---

## STATUS

```
STARTING SHA: 82683e486bd3d5de670b8a0558595244c7ab7429
BRANCH:       feature/asar-ree-v2

TESTS: Cannot execute (Python 3.11 toolchain unavailable — corporate proxy blocks download)
       All 12 new files pass AST parsing (syntax valid)
       Structural validation deferred to next session with working Python env
```

---

## CURRENT REUSABLE COMPONENTS

From forensic audit — verified, tested, directly usable:
- `AppendOnlyEventStore` — event-sourced persistence pattern
- `schemas/ree/world_model.py` — `Hypothesis`, `Assumption`, `Prediction`, `Falsifier`, `Contradiction`
- `schemas/ree/ontology.py` — `ExperimentCandidate`, `CounterfactualWorld`, `SensitivityResult`
- `asar/ontology/forge.py` — Ontology frame management
- `asar/ontology/counterfactual.py` — Counterfactual reasoning
- `asar/ontology/experiment_designer.py` — Experiment prioritization
- `asar/world_model/research_graph.py` — DAG representation
- `asar/evaluation/statistical.py` — Statistical tests
- `EpistemicMarket` pattern — market-based action selection
- `StoppingPolicy` pattern — stopping decisions
- `BudgetState` / `ResourceCost` — budget tracking

---

## CURRENT BROKEN/INACTIVE COMPONENTS

- `asar/operators/retrieve.py` — IMPLEMENTED_BUT_NOT_CAUSAL (eval uses Scenario copies)
- `asar/operators/reason.py` — IMPLEMENTED_BUT_NOT_CAUSAL
- `asar/operators/synthesize.py` — IMPLEMENTED_BUT_NOT_CAUSAL
- `asar/social/tribunal.py` — IMPLEMENTED_BUT_NOT_CAUSAL (zero production callers)
- `asar/social/trust.py` — IMPLEMENTED_BUT_NOT_CAUSAL
- `asar/value_model/` — IMPLEMENTED_BUT_NOT_CAUSAL
- `asar/ignorance/ledger.py` — REUSABLE_AFTER_REDESIGN (parallel to active IgnoranceView)
- `asar/self_model/` — REUSABLE_AFTER_REDESIGN (static injection, not empirical)
- `asar/memory_federation/` — STANDALONE_LIBRARY (complete but isolated)
- `asar/world_model/hypothesis_graph.py` — REUSABLE_AFTER_REDESIGN (duplicates reducer)
- `asar/world_model/belief_tracker.py` — REUSABLE_AFTER_REDESIGN (duplicates views)

---

## CURRENT SCIENTIFIC THESIS

> Can an AI system reliably identify which hypotheses deserve to survive — through falsification, discriminative experiment design, and principled belief revision — rather than merely generating plausible explanations?

Distinguishing contribution: **Falsification + Belief Revision + Theory Abandonment + Ontology Recovery** as an integrated, measurable scientific process evaluated against controlled benchmarks.

---

## PRIOR ART

| Dimension | Closest system | ASAR distinction |
|-----------|---------------|-----------------|
| Closest direct system | AI Co-Scientist | ASAR evaluates what happens AFTER generation |
| Closest benchmark | ProjectionBench + ResearchBench | ASAR measures falsification, not similarity |
| Closest self-correction | Reflexion / Self-Refine | Theory-level revision, not output refinement |

---

## NOVELTY GAP

The specific measurement of scientific SELF-CORRECTION — whether AI systems can reliably identify and abandon wrong hypotheses after decisive falsification — under controlled conditions where ground truth is known.

No existing benchmark (as of 2026-08) specifically measures: falsification behavior, belief revision after contradictory evidence, theory abandonment, self-authorship bias, or ontology revision.

---

## PROPOSED CENTRAL CAPABILITY

Scientific self-correction: the ability to update, revise, or abandon scientific beliefs in response to evidence — especially when that evidence contradicts the system's current leading hypothesis.

---

## SCIENTIFIC STATE

Implemented in `asar/scientific_discovery/state.py`:
- `ScientificState` — immutable, event-sourced, versioned
- `StructuredHypothesis` — full maturity model, falsifiability metadata, rescue assumption tracking
- `HypothesisEcology` — diversity enforcement, belief distribution, entropy
- `BeliefState` — explicit beliefs with history
- `Prediction`, `Falsifier`, `Assumption` — supporting typed objects
- `ScientificBudget`, `IgnoranceItem`, `Contradiction`

---

## HYPOTHESIS SCHEMA

`StructuredHypothesis` with 25+ fields including:
- `causal_mechanism`, `scope`, `maturity` (H0–H5)
- `potential_falsifiers`, `derived_predictions`
- `alternative_explanations`, `confounders`
- `rescue_assumptions` (ad-hoc complexity tracking)
- `authorship` (self-generated vs external — for bias measurement)
- `novelty_status` (10-level classification)

---

## FALSIFICATIONBENCH

**Task families:**
- A: Confirmation Trap (early misleading → decisive falsification)
- B: Confounded Causality (hidden variable)
- C: Reverse Causality
- D: Measurement Artifact
- E: Multiple Mechanisms
- F: Null World
- G: Ontology Failure
- H: Non-Identifiable

**Metrics:**
- Refutation Sensitivity (RS)
- Irrelevant Perturbation Robustness (IPR)
- Recovery Accuracy (RA)
- Abandonment Latency (AL)
- Theory Stickiness (TS)
- Self-Authorship Bias (SAB)
- Hypothesis Discrimination Score (HDS)
- Oracle Regret

**Baselines:**
- Single-pass LLM
- Reflection
- Multi-agent debate
- Greedy evidence seeker
- Random experiment selector
- Fixed workflow
- Oracle

---

## SD-H1 (Falsification Advantage)
Falsification-first improves recovery from misleading theories. **Maturity: H2**

## SD-H2 (Hypothesis Ecology)
Diverse alternatives reduce premature commitment. **Maturity: H2**

## SD-H3 (Discriminative Experiment Selection)
Information-based selection reduces oracle regret. **Maturity: H2**

## SD-H4 (Self-Correction)
Explicit thresholds enable appropriate self-generated hypothesis abandonment. **Maturity: H2**

## SD-H5 (Evidence Independence)
Provenance tracking reduces confidence inflation. **Maturity: H2**

## SD-H6 (Ontology Recovery)
System detects shared false premises across ecology. **Maturity: H1**

## SD-H7 (Time-Capsule Discovery)
System reconstructs discoveries from pre-discovery evidence. **Maturity: H1**

## SD-H8 (Live Computational Discovery)
System generates and tests novel hypothesis. **Maturity: H0**

---

## TOP 5 SCIENTIFIC RISKS

1. **LLMs cannot generate valid falsifiers** — the falsification-first approach requires the model to identify meaningful ways a hypothesis could fail. If generated falsifiers are systematically weak or invalid, SD-H1 fails.

2. **Theory stickiness may not exist as measured** — if baseline LLMs already appropriately revise beliefs after contradictory evidence (i.e., the problem we're solving doesn't exist), ASAR's contribution is diminished.

3. **Controlled worlds may be too simple** — if the worlds don't require genuine scientific reasoning (just pattern matching), results won't transfer to real discovery scenarios.

4. **Compute budget insufficient for meaningful evaluation** — running frontier LLM baselines across 120+ task instances × 5 seeds is expensive.

5. **Novelty collapses under deeper prior art search** — if a 2026 system already benchmarks these exact capabilities, ASAR must reposition.

---

## STAGE 1 IMPLEMENTATION PLAN

### Completed:
- [x] `asar/scientific_discovery/state.py` — Full state schema (300+ lines)
- [x] `asar/scientific_discovery/events.py` — Event-sourced transitions (60+ lines)
- [x] `asar/scientific_discovery/belief_updater.py` — Quantitative belief revision (150+ lines)
- [x] `asar/scientific_discovery/falsification_engine.py` — Core falsification mechanism (250+ lines)
- [x] `asar/scientific_discovery/controller.py` — Scientific loop controller (220+ lines)
- [x] `asar/scientific_discovery/controlled_worlds.py` — 3 world types (530+ lines)
- [x] `asar/scientific_discovery/metrics.py` — FalsificationBench metrics (170+ lines)
- [x] `tests/scientific_discovery/test_scientific_state.py` — State tests
- [x] `tests/scientific_discovery/test_belief_updater.py` — Metamorphic invariant tests
- [x] `tests/scientific_discovery/test_falsification_engine.py` — Engine tests
- [x] `tests/scientific_discovery/test_controlled_worlds.py` — Integration + behavioral influence

### Remaining for Stage 1 GO gate:
- [ ] Run test suite (requires Python 3.11 environment)
- [ ] Verify state replay (event → state reconstruction)
- [ ] Run behavioral influence test (falsification ON vs OFF)
- [ ] Run metamorphic invariant tests
- [ ] Add 2 more world types (Reverse Causality, Null World)
- [ ] Run with actual LLM-generated evidence (manual test)

---

## GO / NO-GO

**Current status: PENDING (tests not yet executable due to environment)**

Stage 1 GO conditions:
1. ☐ State replay PASSES
2. ☐ Behavioral influence PASSES (falsification ON ≠ OFF)
3. ☐ Metamorphic invariants PASS (all 4 invariant tests)
4. ☐ At least one metric shows difference from baseline

Cannot assess yet — need working Python 3.11 environment.

---

## NEXT ACTIONS

1. **Immediate:** Set up Python 3.11 environment and run full test suite
2. **If tests pass:** Run behavioral influence comparison (falsification enabled vs disabled on confirmation trap world)
3. **If behavioral influence confirmed:** Add Reverse Causality and Null World types
4. **Then:** Implement LLM-backed hypothesis generation for live evaluation
5. **Stage 2:** Implement ExperimentDesigner with discrimination scoring
