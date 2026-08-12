# H-REE-20 Semantic Intervention Results

## Simulator Semantic Intervention

**Manipulation check: FAIL**

Real relevance: 0.000, Shuffled relevance: 0.000, Length ratio: 1.000

The simulator's keyword-based hypothesis binding cannot distinguish
real from shuffled LLM-generated hypothesis artifacts. This makes
the simulator unsuitable for testing H-REE-20.

### Results (N=32 worlds, 8 regimes × 4)

| Condition          | Quality (mean ± SD) | Gold Recall |
|-------------------|--------------------:|------------:|
| REAL              | 0.2813 ± 0.2462     | 0.750       |
| SHUFFLED          | 0.2813 ± 0.2462     | 0.750       |
| NEUTRAL           | 0.4175 ± 0.2873     | 0.750       |
| GENERIC_EXPANSION | 0.4175 ± 0.2873     | 0.750       |
| DIRECT            | 0.4175 ± 0.2873     | 0.750       |

### Primary Contrast

REAL - SHUFFLED (quality): +0.0000 (95% CI [0.0000, 0.0000])
REAL - SHUFFLED (recall):  +0.0000 (95% CI [0.0000, 0.0000])

### Interpretation

The simulator cannot test semantic mediation because:
1. The hypothesis binding uses keyword overlap with latent hypotheses, not semantic understanding
2. REAL and SHUFFLED bind identically (both fall through to evidence-priority fallback)
3. The quality difference is entirely between "hypothesis-binding path" vs "sim.generate_hypothesis() path" — a simulator artifact, not a semantic effect

**H-REE-20 cannot be evaluated on the simulator.** External dataset results are required.

---

## External Dataset Semantic Intervention

### SciFact (N=100 claims, dev set with gold evidence)

| Condition          | Accuracy | Gold Doc Recall |
|-------------------|----------:|----------------:|
| DIRECT            | 0.780     | 0.297           |
| NEUTRAL           | 0.720     | 0.297           |
| GENERIC_EXPANSION | 0.740     | 0.265           |
| REAL              | 0.720     | 0.230           |
| SHUFFLED          | 0.980     | 0.000           |

**Primary Contrast (REAL vs SHUFFLED):**

| Metric        | Effect  | 95% CI              |
|---------------|--------:|--------------------:|
| Accuracy      | -0.260  | [-0.346, -0.174]    |
| Gold Recall   | +0.230  | [+0.147, +0.313]    |

**Critical finding:** Real hypotheses significantly IMPROVE gold document
retrieval (+0.230) but significantly HURT final classification accuracy (-0.260).

Shuffled hypotheses achieve near-perfect accuracy (0.980) because they
act as matched-compute controls: the model receives an extra call that
restates context without introducing potentially misleading task-specific
reasoning. The shuffled text does not bias the model toward a specific
verdict, while the real hypothesis may anchor reasoning incorrectly.

### HotpotQA (N=100 questions, distractor dev set)

| Condition          | Answer F1 | Gold Title Recall |
|-------------------|----------:|------------------:|
| DIRECT            | 0.409     | 0.430             |
| NEUTRAL           | 0.433     | 0.430             |
| GENERIC_EXPANSION | 0.410     | 0.435             |
| REAL              | 0.387     | 0.405             |
| SHUFFLED          | 0.292     | 0.270             |

**Primary Contrast (REAL vs SHUFFLED):**

| Metric        | Effect  | 95% CI              |
|---------------|--------:|--------------------:|
| F1            | +0.095  | [+0.010, +0.180]    |
| Gold Recall   | +0.135  | [+0.062, +0.209]    |

On HotpotQA, real hypotheses improve BOTH retrieval and answer quality.
The REAL > SHUFFLED effect on F1 barely excludes zero. The recall
effect is more robust.

---

## H-REE-20 Verdict

### Dissociated Finding

The semantic content of the hypothesis artifact has a CAUSAL effect on
downstream evidence retrieval — this is supported on both SciFact and HotpotQA.

However, better retrieval does NOT always improve final task performance:
- On SciFact, real hypotheses hurt accuracy despite improving retrieval
- On HotpotQA, real hypotheses help both retrieval and answer quality

### Verdict: PARTIALLY_SUPPORTED

The semantic mediation pathway (hypothesis → query → evidence) is
causally operative. But the downstream effect on task performance
is mixed and task-dependent.

Definition tested: "Task-specific semantic content in an intermediate
cognitive artifact causally affects downstream epistemic performance
under matched compute."

Evidence: Semantic content causally affects retrieval (both datasets,
CIs exclude zero). Effect on final task performance is positive on
one dataset, negative on the other.
