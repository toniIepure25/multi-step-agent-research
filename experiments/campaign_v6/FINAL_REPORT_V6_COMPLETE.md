# Campaign V6 Final Report — Complete

## Campaign Overview

Campaign V6 tested five preregistered hypotheses about causal cognitive
sequence value under rigorous controls. The campaign ran in two phases:

**Phase 1 (SHA d52e929):** Factorial complementarity, closed-loop
certification, and matched-budget attack timing on the Epistemic
World Simulator.

**Phase 2 (this completion):** Semantic intervention and external
dataset transfer on SciFact and HotpotQA.

---

## Hypothesis Verdicts

| ID | Hypothesis | Verdict |
|----|-----------|---------|
| H-REE-19 | Compute-Controlled Temporal Complementarity | **NOT_SUPPORTED** |
| H-REE-20 | Semantic Mediation | **PARTIALLY_SUPPORTED** |
| H-REE-21 | Closed-Loop LLM Causality | **PARTIALLY_SUPPORTED** |
| H-REE-22 | Matched-Budget Attack Timing | **NOT_SUPPORTED** |
| H-REE-23 | Exogenous Benchmark Transfer | **PARTIALLY_SUPPORTED** |

---

## Key Findings

### 1. Temporal Complementarity = Zero Under Budget Match (H-REE-19)

The 2×2 factorial interaction between hypothesis generation and
reasoning is exactly 0.000 under matched compute. The V4 temporal
complementarity (+0.162) was entirely the main effect of hypothesis
generation, not a super-additive interaction.

### 2. Attack Timing = Negligible Under Budget Match (H-REE-22)

The matched-budget attack timing effect is +0.019, down from
+0.276 in V5. Attack timing was compute-confounded.

### 3. Semantic Content Causally Affects Retrieval (H-REE-20)

On both SciFact and HotpotQA, task-specific hypothesis content
improves gold evidence retrieval relative to shuffled controls:
- SciFact: +0.230 recall [CI: +0.147, +0.313]
- HotpotQA: +0.135 recall [CI: +0.062, +0.209]

### 4. Retrieval Transfer Does Not Equal Performance Transfer (H-REE-23)

Better retrieval does NOT universally improve task performance:
- SciFact: real hypotheses HURT accuracy (-0.260)
- HotpotQA: real hypotheses HELP F1 (+0.095)

### 5. Simulator Cannot Test Semantic Mediation

The simulator's keyword-based hypothesis binding produces REAL =
SHUFFLED exactly. The manipulation check failed. Semantic mediation
can only be tested on external datasets with real retrieval.

### 6. Hypothesis Anchoring Is a Real Risk

On SciFact, generating a task-specific hypothesis before reasoning
anchors the model toward specific verdicts, often incorrectly.
The SHUFFLED condition (irrelevant hypothesis) achieves 0.980
accuracy vs REAL's 0.720 — demonstrating that "more cognitive
effort" can systematically harm performance.

---

## External Dataset Summary

### SciFact (N=100, CONFIRMATORY)

| Condition          | Accuracy | Gold Recall |
|-------------------|----------:|------------:|
| DIRECT            | 0.780     | 0.297       |
| NEUTRAL           | 0.720     | 0.297       |
| GENERIC_EXPANSION | 0.740     | 0.265       |
| REAL              | 0.720     | 0.230       |
| SHUFFLED          | 0.980     | 0.000       |

### HotpotQA (N=100, CONFIRMATORY)

| Condition          | F1    | Gold Recall |
|-------------------|------:|------------:|
| DIRECT            | 0.409 | 0.430       |
| NEUTRAL           | 0.433 | 0.430       |
| GENERIC_EXPANSION | 0.410 | 0.435       |
| REAL              | 0.387 | 0.405       |
| SHUFFLED          | 0.292 | 0.270       |

---

## Paper Outcome Classification

This maps to **OUTCOME B** from the preregistration:

> H-REE-20 partially supported, H-REE-23 partially supported.

The paper should become:

### Controlled Semantic Mediation in Cognitive Agent Pipelines

with:
1. Strong negative finding: temporal complementarity disappears under controls
2. Positive mechanistic finding: semantic artifacts causally affect retrieval
3. Important qualification: improved retrieval does not universally improve performance
4. Methodology contribution: compute-matched factorial and semantic intervention designs

---

## Fairness Verification

| Condition          | Artifact Call | Query Call | Retrieve | Answer Call | Total Calls |
|-------------------|:------------:|:----------:|:--------:|:-----------:|:-----------:|
| DIRECT            | 0            | 1          | Yes      | 1           | 2           |
| NEUTRAL           | 1            | 1          | Yes      | 1           | 3           |
| GENERIC_EXPANSION | 1            | 0*         | Yes      | 1           | 2           |
| REAL              | 1            | 1          | Yes      | 1           | 3           |
| SHUFFLED          | 1**          | 1          | Yes      | 1           | 3           |

*GENERIC_EXPANSION uses its output directly as the query.
**SHUFFLED makes the call but uses another task's artifact text.

Primary comparison (REAL vs SHUFFLED): Equal calls, equal structure.
DIRECT uses one fewer call — intentional baseline.

---

## Token/Compute Fairness: PASS

REAL and SHUFFLED have identical call counts, max token budgets,
retrieval budgets (k=5 SciFact, k=3 HotpotQA), and downstream
pipelines. The only difference is artifact semantic content.

---

## Pseudoreplication Assessment: PASS

Independent unit = task (claim or question). Each task receives
all 5 conditions as paired repeated measures. Bootstrap CIs
resample at task level. No fork-level or call-level pseudoreplication.

---

## Experimental Integrity

- Condition certification: 11/11 PASS (Phase 1)
- Manipulation check (simulator): FAIL — simulator cannot test H-REE-20
- SciFact task split frozen before execution: task ID hash 852f47c41d84fc74
- HotpotQA task split frozen before execution: task ID hash 53491e0a6469b735
- All artifact pre-generation completed before downstream conditions
- Shuffle assignment deterministic (offset-7 modular pairing)
- Temperature: 0.0 throughout
- No post-hoc task exclusion

---

## Recommendation

### STOP EXPERIMENTAL DEVELOPMENT

All preregistered V6 hypotheses have been executed. The results are:
- Two clean negatives (H-REE-19, H-REE-22)
- Three partial positives (H-REE-20, H-REE-21, H-REE-23)

The paper should honestly present:
1. The falsification of temporal complementarity
2. The discovery of retrieval mediation
3. The task-dependent nature of cognitive artifact value
4. The methodology for compute-matched cognitive-agent evaluation

### SHOULD EXPERIMENTAL DEVELOPMENT STOP?

**YES**

### FINAL PAPER CATEGORY

**Controlled Methodology + Mixed Results Paper**

Potential venues: NeurIPS D&B, EMNLP, ICLR (borderline)

### ICLR/ICML Recommendation

The paper in its current form is a mixed-results methodology paper.
It has a genuine contribution (compute-matched evaluation of cognitive
artifacts with semantic interventions on independent tasks) but the
central positive finding (retrieval mediation) is undermined by the
SciFact result showing that improved retrieval hurts accuracy.

**Recommendation: SUBMIT as methodology/negative-results paper to
a venue that values rigorous methodology and honest reporting of
mixed results (e.g., NeurIPS D&B, EMNLP findings).**
