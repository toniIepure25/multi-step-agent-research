# Statistical Analysis Plan

## Independent Experimental Unit

**TASK** (claim or question) is the independent unit.
Multiple conditions on the same task are paired/repeated measures.
Multiple models on the same task are nested observations.

## Primary Paired Effect

For each task i and contrast (REAL vs CONTROL):

```
D_i = Y_i^REAL - Y_i^CONTROL
Δ = (1/N) Σ D_i
```

## Confidence Intervals

10,000 task-level paired bootstrap resamples.
Resample task indices, NOT conditions independently.
Report 95% bootstrap percentile CI.

## Hypothesis Tests

### Continuous outcomes (recall, F1)
- Paired bootstrap CI
- Paired permutation test (sign-flip, 10,000 permutations) as sensitivity

### Binary outcomes (accuracy)
- Paired risk difference with bootstrap CI
- McNemar test for marginal homogeneity

## Multiple Comparison Correction

### Primary family (6 tests, Holm correction)
1. SciFact REAL vs SHUFFLED gold_document_recall
2. HotpotQA REAL vs SHUFFLED supporting_fact_title_recall
3. SciFact REAL vs GENERIC gold_document_recall
4. HotpotQA REAL vs GENERIC supporting_fact_title_recall
5. SciFact REAL vs SHUFFLED accuracy
6. HotpotQA REAL vs SHUFFLED answer_F1

### Exploratory analyses
- BH-FDR where useful
- Otherwise: effect sizes + CIs, no formal testing

## Evidence Granularity Metrics

### SciFact
- gold_document_recall@k: fraction of gold doc IDs in top-k
- rationale_sentence_recall@k: fraction of gold rationale sentences
  whose source document appears in top-k
- rationale_precision@k: fraction of retrieved docs that contain
  gold rationale sentences
- evidence_F1: harmonic mean of rationale recall and precision

### HotpotQA
- supporting_fact_title_recall@k: fraction of gold supporting-fact
  titles in retrieved titles
- supporting_fact_precision@k: fraction of retrieved titles that
  are gold supporting facts
- evidence_F1: harmonic mean

## SciFact Harm Decomposition

### Answer Flip Analysis
For each task, obtain parametric-only answer (no retrieval).
Classify each (task, condition) as:
- CC: parametric correct → condition correct
- CW: parametric correct → condition wrong (HARMFUL FLIP)
- WC: parametric wrong → condition correct (HELPFUL FLIP)
- WW: parametric wrong → condition wrong

Compare flip rates across conditions with bootstrap CIs.

### Diagnostic Conditions (DEV subset)
- PARAMETRIC_ONLY: answer without any retrieval
- GOLD_DOCUMENT_FULL: gold doc abstract as context
- GOLD_RATIONALE_ONLY: only gold rationale sentences as context
- GOLD_RATIONALE_PLUS_DISTRACTORS: gold rationales + non-gold passages

## Mechanistic Pathway Analysis

Report associations (NOT formal causal mediation):
1. Artifact condition → query quality (topical relevance score)
2. Query quality → gold evidence recall
3. Gold evidence recall → final task quality

Randomized intervention (artifact condition) supports causal claims
for treatment → outcome. Post-treatment variables (query, evidence)
are pathway descriptors only.

## Power / Sample Size

See POWER_ANALYSIS.json for per-dataset calculations.
Based on V6 DEV variance with target 80% power.

## Null-Result Interpretation

For null results report:
- 95% CI
- SESOI
- Whether CI excludes SESOI (equivalence)
- Minimum detectable effect at 80% power
