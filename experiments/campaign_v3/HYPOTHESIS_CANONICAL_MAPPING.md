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

| ID | Statement | Status |
|---|---|---|
| H-REE-11 | Cognitive operations exhibit temporal complementarity: sequence value ≠ sum of primitive values | UNTESTED |
| H-REE-12 | Hypothesis ecology improves quality across architectures (not only within Full REE) | UNTESTED |
| H-REE-13 | Greedy primitive-action scheduling fails because it cannot capture cognitive sequence structure | UNTESTED |
