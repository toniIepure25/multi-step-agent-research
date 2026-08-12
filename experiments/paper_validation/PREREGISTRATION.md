# Paper Validation Preregistration

**Frozen before locked execution. Do not modify after commit.**

## Study Title

Causal Auditing of Intermediate Semantic Artifacts in LLM Retrieval Pipelines

## Discovery SHA

`f603a9ca22483e54bfaf798a4b5fe5a6fc960c8e` (Campaign V6 endpoint)

## Primary Research Question

What causal value does an explicit semantic cognitive artifact add to an
LLM retrieval pipeline once compute, information opportunity, retrieval
budget, and downstream exposure are controlled?

## Secondary Research Question

Why can a semantic artifact improve retrieval while helping downstream
reasoning on one task and harming it on another?

---

## Confirmatory Hypotheses

### PV-H1 — Semantic Retrieval Effect

A task-specific hypothesis artifact improves retrieval of dataset-native
gold/supporting evidence relative to a matched shuffled hypothesis.

- Primary DV: gold evidence recall (document-level for SciFact, title-level for HotpotQA)
- Experimental unit: task (claim or question)
- Comparison: REAL vs SHUFFLED
- SESOI: 0.06 absolute recall difference
- Statistical test: paired bootstrap (10,000 resamples), Holm-corrected

### PV-H2 — Semantic Specificity

REAL hypothesis outperforms GENERIC query expansion on evidence acquisition.

- Primary DV: gold evidence recall
- Comparison: REAL vs GENERIC_EXPANSION
- SESOI: 0.04 absolute recall difference
- Statistical test: paired bootstrap, Holm-corrected

### PV-H3 — Downstream Utility Heterogeneity

The downstream effect of semantic intervention differs systematically
across task structures/datasets.

- Primary DV: task accuracy (SciFact) / answer F1 (HotpotQA)
- Comparison: interaction of REAL-vs-SHUFFLED effect × dataset
- SESOI: 0.10 interaction magnitude
- Statistical test: bootstrap interaction test

### PV-H4 — Model Transfer

The primary semantic retrieval effect (PV-H1) replicates directionally
on the second model family (Llama 3.2 11B).

- Primary DV: gold evidence recall
- Comparison: sign of REAL-SHUFFLED effect on Llama
- SESOI: same-sign replication
- Statistical test: sign test + paired bootstrap

### PV-H5 — SciFact Failure Mechanism

SciFact degradation can be localized to specific stages through
diagnostic conditions (parametric-only, gold-rationale-only, etc.)

- This is a mechanistic decomposition, not a single-test hypothesis
- Primary analyses: answer flip rates (CC/CW/WC/WW), gold-rationale vs
  retrieved-context accuracy, artifact-visible vs artifact-hidden comparison
- Exploratory unless specific contrasts are frozen below

---

## Datasets

### SciFact (CONFIRMATORY)
- Source: allenai/scifact, dev split
- Evaluable claims: 188 (with gold evidence)
- V6-seen: 100 (first 100 by sort order)
- Locked validation set: claims 101-188 (N=88 unseen)
- Same-task transfer: claims 1-100 (V6 tasks, Llama only)
- Metric: accuracy, gold_document_recall, rationale_sentence_recall

### HotpotQA (CONFIRMATORY)
- Source: hotpot_dev_distractor_v1.json (Wayback archive)
- Total dev: 7,405
- V6-seen: 100 (first 100)
- Locked validation set: tasks 101-300 (N=200 unseen)
- Same-task transfer: tasks 1-100 (V6 tasks, Llama only)
- Metric: answer_F1, exact_match, supporting_fact_title_recall

### Qasper (EXPLORATORY)
- Source: allenai/qasper
- Target: ~200 papers, 1 question per paper
- Metric: answer_F1, evidence_F1

---

## Models

- Primary: gemma3:27b-it-qat (frozen from V6)
- Transfer: llama3.2-vision:11b-instruct-q8_0 (frozen from V5)
- Endpoint: OpenAI-compatible, temperature=0.0, max_tokens=512

---

## Conditions

| ID | Artifact | Query Source | Calls | Description |
|----|----------|-------------|-------|-------------|
| REAL | Task-specific hypothesis | From hypothesis | 3 | Full pipeline |
| SHUFFLED | Other-task hypothesis | From shuffled artifact | 3 | Semantic control |
| NEUTRAL | Factual restatement | From neutral artifact | 3 | Compute control |
| GENERIC_EXPANSION | Query expansion | Expansion as query | 2+1* | Query-rewrite control |
| DIRECT | None | From task directly | 2+1* | Minimal baseline |

*DIRECT and GENERIC_EXPANSION get matched control calls for fairness.

---

## Exclusion Rules

- Tasks where ALL conditions fail to generate parseable output: exclude
- Tasks where retriever returns 0 results for ALL conditions: exclude
- Maximum exclusion rate: 5% (if exceeded, investigate)
- No exclusion based on outcome

## Retry Rules

- Network/timeout error: retry up to 3 times
- Malformed LLM output: use raw text, do NOT retry for better formatting
- Model refusal: record as failure, do NOT retry

## Failure Handling

- Failed LLM calls recorded with error type
- Analysis uses intent-to-treat: all locked tasks included

---

## Multiple Comparison Family

Primary confirmatory (Holm-corrected):
1. PV-H1 SciFact REAL vs SHUFFLED recall
2. PV-H1 HotpotQA REAL vs SHUFFLED recall
3. PV-H2 SciFact REAL vs GENERIC recall
4. PV-H2 HotpotQA REAL vs GENERIC recall
5. PV-H1 SciFact REAL vs SHUFFLED accuracy
6. PV-H1 HotpotQA REAL vs SHUFFLED F1

All other analyses: EXPLORATORY (BH-FDR or CIs only)

---

## Artifact Length Matching

Acceptable range: 0.90 <= control_tokens / real_tokens <= 1.10
Measured on DEV set before locked execution.
If violated, truncate/pad control artifacts on DEV, not locked set.

## Shuffle Pairing

Deterministic offset-7 modular pairing within dataset.
Persisted in artifact_shuffle_map.json before locked execution.
No task paired with itself. No high-semantic-overlap pairs.

---

## Preregistration Frozen At

SHA: [TO BE FILLED AFTER COMMIT]
Timestamp: [TO BE FILLED AFTER COMMIT]
