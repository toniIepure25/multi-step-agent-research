# Stage 3D Preregistration

## Date: 2026-08-14
## Status: FROZEN before inference execution

---

## Models
- PRIMARY: gemma3:27b-it-qat (digest: 29eb0b9a...)
- TRANSFER: llama3.2-vision:11b-instruct-q8_0 (digest: a5b7471a...)

## Generation Settings
- temperature: 0
- max_tokens: 2048
- endpoint: https://inference.ccrolabs.com/v1/chat/completions

## Deterministic Benchmark Parameters (COMPLETED)

### World Generator (frozen)
- n_hypotheses: [3, 8]
- n_experiments: [3, 10]
- n_outcomes: [2, 4]
- prior_concentration: 1.0
- prediction_noise: 0.1-0.15
- overlap_range: [0.1, 0.8]
- seed_offset: 5000+ (non-overlapping with Stage 3C)

### Locked Seeds
- DEV: 1-20
- LOCKED Stage 3C: 21-40
- LOCKED Stage 3D: 41-60

---

## Confirmatory Family (Holm-corrected)

| Hypothesis | Primary Outcome | SESOI |
|-----------|----------------|-------|
| SD-H3B | JSD regret < Confirmation regret | 0.01 bits |
| SD-H3C | Sequential oracle regret > 0 | 0.005 bits |
| SD-H4 | Correct abandonment > 70% AND False abandonment < 30% | Rates |
| SD-H9 | Discrimination recovery > Passive recovery | 0.10 |
| SD-H9C | Complexity × Policy interaction slope > 0 | Exploratory |

---

## SD-H4 Protocol

### Total Worlds: 50 (preregistered, frozen before inference)
### Classification: automatic (wrong_markers / true_markers matching)
### Paired analysis: SELF vs EXTERNAL on identical hypotheses
### Correct-theory protection: 20 additional worlds with weak contradictions

### Primary Metrics
- Correct Abandonment Rate (wrong hypotheses): binomial 95% CI
- False Abandonment Rate (correct hypotheses): binomial 95% CI
- Self-Authorship Bias: paired t-test, 95% CI
- Recovery (correct new explanation): binomial 95% CI

---

## SD-H3C Protocol

### N: 200 random worlds (frozen seeds starting at 3000)
### Policies: Greedy JSD, Greedy EIG, Oracle 2-step
### Primary: Sequential regret (paired t-test)
### Horizon: 2 steps

---

## SD-H9C Protocol (EXPLORATORY — post-hoc motivated)

### N: 150 distributional active worlds
### Complexity measure: entropy × (1-max_div) × (n_h/3)
### Analysis: Linear regression of advantage ~ complexity
### Status: Exploratory (NOT confirmatory)

---

## Multiple Comparisons
- Primary family: SD-H3B, SD-H3C, SD-H4, SD-H9 (4 tests)
- Correction: Holm-Bonferroni
- SD-H9C: exploratory (not included in primary family)
- Capability gate: descriptive (no formal hypothesis test)

---

## Repair Rules
- JSON parse failure → retry once with same prompt
- Second failure → mark as UNRECOVERABLE, exclude from scientific metrics
- All repairs logged with first-pass output preserved
- Unrecoverable rate reported as C7 metric

---

## Failure Rules
- If correct abandonment < 50% on PRIMARY: Stage 3D reports NEGATIVE
- If LLM inference fails > 20% of calls: BLOCKED_BY_INFRASTRUCTURE
- If < 30 wrong hypotheses naturally generated: INSUFFICIENT_PRECISION (not failure)
