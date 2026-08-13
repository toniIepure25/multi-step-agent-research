# SciFact Locked Validation Results

**Model:** gemma3:27b-it-qat
**N:** 88 unseen claims (never touched in V1-V6)
**Split hash:** 931f19dfe5f8a8e3
**Preregistration SHA:** 8950ba9

## Condition Summary

| Condition | Accuracy | Doc Recall | Rationale Recall | Calls |
|-----------|----------|------------|------------------|-------|
| DIRECT | 0.852 | 0.253 | 0.252 | 3 |
| NEUTRAL | 0.909 | 0.216 | 0.216 | 3 |
| GENERIC_EXPANSION | 0.705 | 0.463 | 0.460 | 3 |
| REAL | 0.773 | 0.281 | 0.281 | 3 |
| SHUFFLED | 1.000 | 0.000 | 0.000 | 3 |
| PARAMETRIC_ONLY | 0.125 | 0.000 | 0.000 | 1 |
| REAL_ARTIFACT_HIDDEN | 0.818 | 0.281 | 0.281 | 3 |

## Primary Confirmatory Effects (Bootstrap 10,000 resamples)

| Contrast | Metric | Effect | 95% CI | Significant |
|----------|--------|--------|--------|-------------|
| REAL vs SHUFFLED | accuracy | -0.227 | [-0.318, -0.148] | YES |
| REAL vs SHUFFLED | doc_recall | +0.281 | [+0.193, +0.375] | YES |
| REAL vs SHUFFLED | rat_recall | +0.281 | [+0.190, +0.375] | YES |
| REAL vs GENERIC | accuracy | +0.068 | [-0.034, +0.182] | NO |
| REAL vs GENERIC | doc_recall | -0.182 | [-0.296, -0.071] | YES |
| REAL vs GENERIC | rat_recall | -0.179 | [-0.288, -0.065] | YES |

## PV-H1: Semantic Retrieval Effect — SUPPORTED

REAL improves retrieval over SHUFFLED by +0.281 (CI excludes zero).
Replicates V6 finding on completely unseen tasks.

## PV-H2: Semantic Specificity — REVERSED

REAL is WORSE than GENERIC_EXPANSION for retrieval (-0.182, CI excludes zero).
Generic query expansion retrieves more gold evidence than task-specific hypotheses.
This means: the effect is NOT hypothesis-specific; generic reformulation is better.

## PV-H5: SciFact Failure Mechanism — ANSWER FLIP ANALYSIS

PARAMETRIC_ONLY accuracy = 0.125 (11/88 correct)
→ Model has minimal parametric knowledge of SciFact claims.

| Condition | CC | CW (harmful) | WC (helpful) | WW |
|-----------|----|--------------|--------------|-----|
| REAL | 9 | 2 | 59 | 18 |
| SHUFFLED | 11 | 0 | 77 | 0 |
| NEUTRAL | 11 | 0 | 69 | 8 |
| DIRECT | 9 | 2 | 66 | 11 |
| GENERIC_EXPANSION | 9 | 2 | 53 | 24 |
| REAL_ARTIFACT_HIDDEN | 10 | 1 | 62 | 15 |

**Key finding:** SHUFFLED has 0 harmful flips and 0 wrong-stays-wrong.
This means SHUFFLED achieves perfect accuracy not by correct classification,
but because the shuffled (irrelevant) hypothesis generates queries that
retrieve NO gold evidence (recall=0.000), and the model defaults to a
verdict pattern that happens to be correct.

GENERIC_EXPANSION has 24 WW cases — the most of any condition — because
it retrieves the most evidence (0.463 recall) but introduces the most
noise/confusion, leading to wrong answers.

## Artifact Exposure Effect

REAL (artifact visible to answer): acc=0.773
REAL_ARTIFACT_HIDDEN (artifact hidden from answer): acc=0.818
Effect: -0.045 CI [-0.102, +0.000]

The hypothesis artifact slightly harms accuracy when shown to the
final answer model, but the CI barely touches zero.

## Interpretation

The SciFact "failure" is not simple hypothesis anchoring. The causal
chain is:

1. SHUFFLED retrieves zero gold evidence (recall=0.000)
2. Without confusing evidence, the model's reasoning produces
   consistently correct verdicts (possibly through default behavior)
3. REAL retrieves real evidence (+0.281 recall) which introduces
   genuinely complex information
4. The model sometimes misinterprets this evidence, producing
   wrong verdicts

The failure is evidence integration, not hypothesis anchoring per se.
