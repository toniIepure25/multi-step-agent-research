# LLM Capability Gate — Stage 3

**Status:** FRAMEWORK IMPLEMENTED, AWAITING LLM INTEGRATION

---

## Required Capabilities

| ID | Capability | Schema | Status |
|----|-----------|--------|--------|
| C1 | Structured Hypothesis Generation | `GeneratedHypothesis` | Framework ready |
| C2 | Mechanistic Alternatives | `GeneratedAlternative` | Framework ready |
| C3 | Prediction Derivation | `GeneratedPrediction` | Framework ready |
| C4 | Falsifier Generation | `GeneratedFalsifier` | Framework ready |
| C5 | Confound Detection | - | Framework ready |
| C6 | Experiment Proposal | `GeneratedExperiment` | Framework ready |
| C7 | Structured Output (schema compliance) | All above | Framework ready |

---

## Evaluation Method

Each capability is tested against controlled worlds where correct structures
are objectively known. LLM-as-judge is NOT used for primary evaluation.

### C1 — Hypothesis Generation
- Input: observations from controlled world
- Evaluate: mechanism coverage vs canonical mechanisms
- Score: fraction of true mechanisms represented

### C2 — Mechanistic Alternatives
- Input: primary hypothesis
- Evaluate: structural diversity (not paraphrases)
- Score: number of genuinely distinct mechanisms / total generated

### C3 — Prediction Derivation
- Input: hypothesis + candidate experiment
- Evaluate: predicted outcome matches world generative model
- Score: accuracy of predicted outcomes

### C4 — Falsifier Generation
- Input: hypothesis
- Evaluate: proposed observation actually contradicts hypothesis in world
- Score: fraction of valid falsifiers

### C5 — Confound Detection
- Input: claimed relationship + observations
- Evaluate: recall of known confounders
- Score: fraction of true confounds identified

### C6 — Experiment Proposal
- Input: competing hypotheses
- Evaluate: discrimination score of proposed experiment
- Score: JSD between hypothesis predictions on proposed experiment

### C7 — Structured Output
- Evaluate: schema validation pass rate
- Score: fraction of outputs parseable into typed schema

---

## Verdict Criteria

| Verdict | Condition |
|---------|-----------|
| VALID_EXPERIMENTAL_SUBSTRATE | ≥ 70% pass + ≥ 80% schema compliance |
| PARTIAL_SUBSTRATE | ≥ 40% pass |
| INVALID_EXPERIMENTAL_SUBSTRATE | < 40% pass |

---

## Important Restrictions

1. LLM NEVER receives `true_hypothesis_id` or `WorldGroundTruth`
2. LLM output MUST pass typed schema parsing (no raw prose as state)
3. Model version, temperature, and prompts must be frozen before locked run
4. If model cannot produce usable outputs, classify as INVALID_SUBSTRATE
   (do not interpret as architecture failure)
