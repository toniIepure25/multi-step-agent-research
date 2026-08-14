# Failure Localization — Stage 3D

## Date: 2026-08-14
## Status: EVALUATOR-LEVEL (deterministic benchmark)

---

## Benchmark: 150 distributional worlds × 4 policies

### Failure Type Distribution (Discrimination policy)

| Failure Type | Count | Rate |
|-------------|-------|------|
| Budget exhausted | 48 | 100% of failures |
| Wrong hypothesis selected | 0 | 0% |
| No experiment run | 0 | 0% |

### All Policies

| Policy | Success | Failure | Failure Rate |
|--------|---------|---------|-------------|
| Passive | 81 | 69 | 46% |
| Random | 83 | 67 | 45% |
| Confirmation | 84 | 66 | 44% |
| Discrimination | 102 | 48 | 32% |

---

## Interpretation

The ONLY failure mode in the evaluator-level benchmark is **budget exhaustion** —
the agent runs out of experiments before achieving sufficient belief concentration.

This means:
1. The hypothesis set always CONTAINS the truth (no generation failure)
2. The belief update always WORKS (no interpretation failure)
3. The experiment selection always RUNS (no abstention)
4. The ONLY bottleneck is INFORMATION RATE per experiment

---

## Implication for LLM-Level Failures

When the generative scientist (LLM) is added, ADDITIONAL failure types should emerge:

| Expected LLM Failure Type | Example |
|--------------------------|---------|
| FRAMING | Problem misunderstood |
| HYPOTHESIS COVERAGE | True mechanism not generated |
| PREDICTION | Incorrect causal predictions |
| FALSIFIER | Invalid falsification test |
| EXPERIMENT | Non-discriminating experiment chosen |
| OBSERVATION INTERPRETATION | Evidence misread |
| BELIEF UPDATE | Inconsistent confidence revision |
| ABANDONMENT | Wrong theory retained / correct theory dropped |
| ABSTENTION | Premature stopping |

The LLM-level failure taxonomy will be populated during SD-H4 scaled inference.
Currently: **FRAMEWORK EXISTS, NOT YET POPULATED**.

---

## Key Finding

At the evaluator level, discrimination reduces failure rate from 44-46% to 32%.
The entire effect comes from faster information accumulation within the budget.
All 48 discrimination failures occurred because 5 experiments were insufficient
to resolve uncertainty in hard worlds, NOT because of wrong choices.
