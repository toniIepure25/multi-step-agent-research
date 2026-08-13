# HotpotQA Locked Validation Results

**Model:** gemma3:27b-it-qat
**N:** 300 unseen tasks (never touched in V1-V6)
**Split hash:** 03a4b9fe90988271
**Preregistration SHA:** 8950ba9

## Condition Summary

| Condition | F1 | Gold Title Recall | Calls |
|-----------|-----|-------------------|-------|
| DIRECT | 0.336 | 0.437 | 2+1 |
| NEUTRAL | 0.357 | 0.413 | 3 |
| GENERIC_EXPANSION | 0.372 | 0.525 | 2+1 |
| REAL | 0.393 | 0.460 | 3 |
| SHUFFLED | 0.269 | 0.278 | 3 |

## Primary Confirmatory Effects (Bootstrap 10,000 resamples)

| Contrast | Metric | Effect | 95% CI | Significant |
|----------|--------|--------|--------|-------------|
| REAL vs SHUFFLED | F1 | +0.124 | [+0.073, +0.175] | YES |
| REAL vs SHUFFLED | recall | +0.182 | [+0.138, +0.225] | YES |
| REAL vs GENERIC | F1 | +0.021 | [-0.028, +0.071] | NO |
| REAL vs GENERIC | recall | -0.065 | [-0.107, -0.023] | YES |

## PV-H1: Semantic Retrieval Effect — SUPPORTED

REAL improves retrieval over SHUFFLED by +0.182 (CI excludes zero).
REAL also improves F1 over SHUFFLED by +0.124 (CI excludes zero).
Both effects replicate on 300 unseen tasks.

## PV-H2: Semantic Specificity — REVERSED (SAME AS SCIFACT)

REAL is WORSE than GENERIC_EXPANSION for retrieval (-0.065, CI excludes zero).
On F1, REAL ≈ GENERIC (not significantly different).
Generic query expansion retrieves more gold evidence than task-specific hypotheses.

## Interpretation

On HotpotQA, REAL hypotheses help vs SHUFFLED but hurt vs GENERIC.
The benefit over SHUFFLED appears to be generic query quality rather
than hypothesis-specific semantic content. GENERIC_EXPANSION achieves
the best retrieval (0.525) without committing to any hypothesis.

The REAL advantage over SHUFFLED on F1 (+0.124) is larger than on
recall (+0.182 × scaling), suggesting that hypothesis semantics may
help reasoning even when retrieval is not optimal. But GENERIC
achieves comparable F1 (+0.021 difference, not significant).
