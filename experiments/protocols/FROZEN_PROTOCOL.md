# FROZEN EXPERIMENTAL PROTOCOL — ASAR-REE Scientific Campaign

**Frozen at**: 2026-08-10
**Starting SHA**: 2c44f09
**Branch**: feature/asar-ree-v2
**Status**: FROZEN — do not modify primary analysis after inspecting results

## Primary Hypotheses (Confirmatory — Holm correction at α=0.05)

1. **H-REE-01**: Empirical self-model outperforms default confidence (Brier Score)
2. **H-REE-02**: Ignorance ledger predicts actual failure causes (Foresight Score > 0.3)
3. **H-REE-03**: Evidence independence prevents duplicate-source confidence inflation
4. **H-REE-04**: Hypothesis ecology prevents premature convergence (≥20% reduction)
5. **H-REE-05**: Adaptive scheduling improves Quality/Compute Pareto (≥2 budget levels)
6. **H-REE-06**: Epistemic state predicts cognitive action value (rank corr > 0.2)

## Secondary Hypotheses (Exploratory — BH-FDR at q=0.10)

7. **H-REE-07**: Counterfactual robustness/responsiveness
8. **H-REE-08**: Memory consolidation reduces repeated errors
9. **H-REE-09**: Full REE > sum of mechanism effects (synergy)
10. **H-REE-10**: Ontology revision improves frame-escape

## Architecture Conditions

| Code | Description |
|------|-------------|
| B0 | Direct model — single controlled answer |
| B1 | Simple reflection — answer + critique + revision |
| B3 | Fixed-depth REE — predetermined operator sequence |
| B4 | Adaptive REE — heuristic Epistemic Market |
| B5 | Full REE — all mechanisms active |

## Budgets (equivalent synthetic tokens)

- 2000 (low)
- 5000 (medium)
- 10000 (high)
- 20000 (very high)

## Scenario Families

| Family | Count (holdout) | Primary hypothesis |
|--------|----------------|--------------------|
| false_majority | 5 | H-REE-03, social epistemology |
| duplicated_source | 5 | H-REE-03 |
| assumption_flip | 5 | H-REE-07 |
| hypothesis_ecology | 5 | H-REE-04 |
| ignorance_discovery | 5 | H-REE-02 |
| stopping_quality | 5 | H-REE-05 |

## Metrics

- Final correctness (binary: matches ground truth answer)
- Hypothesis count, diversity
- Ignorance items produced
- Evidence items collected
- Claims produced
- Operator sequence
- Tokens consumed
- Steps used
- Hypothesis entropy (from MaterializedViews)
- Ignorance priority (from MaterializedViews)
- Workspace saturation

## Statistical Plan

- Bootstrap 95% CI for all continuous metrics
- Paired comparisons with Cohen's d
- Win/tie/loss for binary outcomes
- Holm correction for 6 primary hypotheses
- BH-FDR for exploratory ablations
- Effect sizes as primary, p-values as secondary

## Scalarizations for RealizedEpistemicGain

- Default equal weights: all dimensions weight 1.0, cost weight -0.1
- Quality-focused: task_quality=2.0, others=0.5, cost=-0.1
- Cost-penalized: task_quality=1.0, cost=-1.0

## Seeds

Base seed: 42. Scenario seeds: 42+index.
All scenarios deterministic with mock providers.

## Exclusion Criteria

- Scenarios where controller produces zero events (runtime error)
- Budget violations (tokens_used > budget_max_tokens)

## Failure Handling

- Failed operator executions recorded as NO_OP events
- Controller stop on budget exhaustion is valid termination

## DO NOT CHANGE after this point:
- Primary hypothesis definitions
- Holdout scenario definitions
- Primary analysis plan
- Metric definitions
- Scalarization weights
