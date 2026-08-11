# V6 Preregistration

## Hypotheses

### H-REE-19 — Compute-Controlled Temporal Complementarity

**Statement:** After matching total model calls, token budget, and task
information, selected heterogeneous cognitive-operation pairs exhibit
non-additive downstream epistemic value.

| Field | Value |
|-------|-------|
| Primary DV | Scalar epistemic quality Q(E) |
| Experimental unit | World / task |
| Comparison | 2×2 factorial interaction: Y11 − Y10 − Y01 + Y00 |
| Effect definition | Interaction term from paired factorial |
| SESOI | 0.05 (on 0-1 quality scale) |
| Success criterion | 95% CI for interaction excludes 0, point estimate ≥ SESOI |
| Failure criterion | 95% CI includes 0 or point estimate < SESOI |
| Statistical test | Paired bootstrap CI (task-level resampling); mixed-effects model as sensitivity |
| Multiple-comparison family | Primary confirmatory (Holm-corrected across H-REE-19 through H-REE-22) |

### H-REE-20 — Semantic Mediation

**Statement:** The benefit of a cognitive sequence depends on the semantic
content produced by its intermediate cognitive artifact, not merely on
performing an extra model call.

| Field | Value |
|-------|-------|
| Primary DV | Scalar epistemic quality Q(E) |
| Experimental unit | World / task |
| Comparison | Real artifact vs shuffled artifact (matched budget) |
| Effect definition | mean(Q_real) − mean(Q_shuffled) |
| SESOI | 0.03 |
| Success criterion | 95% CI excludes 0, real > shuffled |
| Failure criterion | 95% CI includes 0 |
| Statistical test | Paired bootstrap CI (task-level) |
| Multiple-comparison family | Primary confirmatory |

### H-REE-21 — Closed-Loop LLM Causality

**Statement:** LLM-generated cognitive artifacts causally affect subsequent
evidence acquisition/state transitions and therefore final task outcomes.

| Field | Value |
|-------|-------|
| Primary DV | Change in downstream quality when artifact content varies |
| Experimental unit | World / task |
| Comparison | Perturbation study: same task, different artifact → different outcome |
| Effect definition | Variance in Q(E) attributable to artifact content |
| SESOI | Detectable outcome variation (non-zero variance) |
| Success criterion | Downstream Q varies with artifact content across ≥ 50% of tasks |
| Failure criterion | Downstream Q is constant regardless of artifact content |
| Statistical test | Friedman test across artifact conditions per task |
| Multiple-comparison family | Primary confirmatory |

### H-REE-22 — Matched-Budget Attack Timing

**Statement:** Attack/falsification has state-dependent value even when
early/mid/late conditions use the same operations, model calls, and budget.

| Field | Value |
|-------|-------|
| Primary DV | Scalar epistemic quality Q(E) |
| Experimental unit | World / task |
| Comparison | Early vs mid vs late attack (same operations, same budget) |
| Effect definition | max(condition means) − min(condition means) |
| SESOI | 0.03 |
| Success criterion | Friedman p < 0.05 (Holm-corrected), effect ≥ SESOI |
| Failure criterion | p ≥ 0.05 or effect < SESOI |
| Statistical test | Friedman test with Nemenyi post-hoc; paired bootstrap for pairwise CIs |
| Multiple-comparison family | Primary confirmatory |

### H-REE-23 — Exogenous Benchmark Transfer

**Statement:** At least one temporal-interaction effect appears on independently
defined public evidence-grounded tasks.

| Field | Value |
|-------|-------|
| Primary DV | Task-native metric (accuracy, F1, or evidence recall depending on dataset) |
| Experimental unit | Task |
| Comparison | Factorial interaction or best cognitive sequence vs matched primitive |
| Effect definition | Interaction term or sequence − primitive difference |
| SESOI | Dataset-specific (set after DEV phase power analysis) |
| Success criterion | 95% CI excludes 0 for at least one dataset |
| Failure criterion | No dataset shows significant interaction |
| Statistical test | Paired bootstrap CI |
| Multiple-comparison family | Exploratory (Bonferroni across datasets) |

## Analysis Plan

### Primary analyses (confirmatory)
1. Factorial interaction (H-REE-19) — paired bootstrap, 10000 resamples
2. Real vs shuffled artifact (H-REE-20) — paired bootstrap
3. Closed-loop causality certification (H-REE-21) — Friedman test
4. Attack timing (H-REE-22) — Friedman + pairwise bootstrap

### Secondary analyses (exploratory)
- Cross-model comparison (Gemma 3 vs Llama 3.2)
- Per-regime interaction heterogeneity
- Mediation analysis: artifact quality → query quality → evidence recall → final quality
- Scalarization sensitivity (alternative Q weights)
- Per-operation reliability estimation

### Multiple comparisons
- Holm correction across H-REE-19 through H-REE-22 (4 primary tests)
- H-REE-23 treated separately as exploratory

### Null-result protocol
For null results, report:
- 95% CI
- SESOI
- Minimum detectable effect (MDE) at 80% power
- Two-one-sided-tests (TOST) equivalence test where appropriate
