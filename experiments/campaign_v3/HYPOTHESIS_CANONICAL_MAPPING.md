# Hypothesis Canonical Mapping

Immutable mapping from canonical IDs (in `docs/research/hypotheses.md`) to
all experimental verdicts. All future reports MUST use these canonical IDs.

| Canonical ID | Canonical Statement | V1 Verdict | V2 Verdict | Current Status |
|---|---|---|---|---|
| H-REE-01 | Empirical self-model outperforms verbal confidence (Brier/ECE) | INCONCLUSIVE (non-causal ablation) | INCONCLUSIVE (ablation still non-causal) | INCONCLUSIVE |
| H-REE-02 | Pre-answer ignorance ledger predicts post-hoc failure causes | INCONCLUSIVE (mock-env non-discriminative) | PARTIALLY_SUPPORTED (small quality effect d≈0.2) | PARTIALLY_SUPPORTED |
| H-REE-03 | Sealed first-round deliberation improves minority preservation rate | INCONCLUSIVE (not in benchmark) | INCONCLUSIVE (not in benchmark) | INCONCLUSIVE |
| H-REE-04 | Ontology branching improves recovery from false framing | INCONCLUSIVE (not in benchmark) | INCONCLUSIVE (not in benchmark) | INCONCLUSIVE |
| H-REE-05 | Epistemic Market achieves better quality/compute Pareto frontier than fixed-depth cognition | INCONCLUSIVE (mock-env non-discriminative) | **NOT_SUPPORTED** (market anti-calibrated; round-robin ≥ heuristic) | NOT_SUPPORTED |
| H-REE-06 | Provenance clustering reduces false confidence from duplicated sources | INCONCLUSIVE (not causally ablated) | INCONCLUSIVE (not causally ablated) | INCONCLUSIVE |
| H-REE-07 | Counterfactual reasoning improves responsiveness without reducing robustness | INCONCLUSIVE (not in benchmark) | INCONCLUSIVE (not in benchmark) | INCONCLUSIVE |
| H-REE-08 | Offline consolidation improves subsequent strategy selection | INCONCLUSIVE (not in benchmark) | INCONCLUSIVE (not in benchmark) | INCONCLUSIVE |
| H-REE-09 | Full REE produces positive interaction effects beyond sum of components | INCONCLUSIVE (mock-env non-discriminative) | **NOT_SUPPORTED** (Full REE < B1 fixed strategy) | NOT_SUPPORTED |
| H-REE-10 | Hypothesis ecology outperforms single-trajectory reasoning | INCONCLUSIVE (mock-env non-discriminative) | **SUPPORTED** (d≈1.4, 90% quality drop when ablated) | SUPPORTED |

## V2 Report Numbering Error

The V2 FINAL_REPORT_V2.md and PHASE14_CHECKPOINT.md used swapped IDs:
- V2 labeled hypothesis ecology as "H-REE-05" → canonical is **H-REE-10**
- V2 labeled adaptive scheduling as "H-REE-10" → canonical is **H-REE-05**

The scientific content and verdicts were correct; only the ID labels were swapped.
This mapping resolves the inconsistency permanently.

## New Hypotheses (Campaign V3)

| ID | Statement | V3 Verdict | V4 Verdict |
|---|---|---|---|
| H-REE-11 | Cognitive operations exhibit temporal complementarity: sequence value ≠ sum of primitive values | **SUPPORTED** (+0.228 gen_hyp+reason) | **SUPPORTED** (replicates at +0.137) |
| H-REE-12 | Hypothesis ecology improves quality across architectures (not only within Full REE) | NOT_SUPPORTED | NOT_SUPPORTED |
| H-REE-13 | Greedy primitive-action scheduling fails because it cannot capture cognitive sequence structure | **SUPPORTED** | **SUPPORTED** |

## New Hypotheses (Campaign V4)

| ID | Statement | V4 Verdict |
|---|---|---|
| H-REE-14 | In heterogeneous epistemic regimes, the state-conditioned sequence oracle exceeds the best global fixed cognitive sequence | **SUPPORTED** (gap=0.096) |
| H-REE-15 | Temporal complementarity between cognitive operations persists when operations are executed by an actual LLM | UNTESTED |
| H-REE-16 | Epistemic-state features predict the downstream value of temporally extended cognitive motifs better than primitive actions | **PARTIALLY_SUPPORTED** (motifs > primitives 100%, but selection fails) |
| H-REE-17 | A state-conditioned motif selector reduces oracle regret relative to the best global fixed policy on held-out heterogeneous worlds | **NOT_SUPPORTED** (policy regret 0.264 >> fixed regret 0.070) |
| H-REE-18 | At least one major temporal-control effect observed in the semantic simulator transfers to LLM-in-loop and real-evidence settings | UNTESTED |
