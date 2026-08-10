# ASAR-REE Scientific Campaign — Negative Findings

**Campaign date**: 2026-08-10
**Starting SHA**: 2c44f09
**Branch**: feature/asar-ree-v2

This document records negative results, methodological limitations, and mechanisms that did not demonstrate the claimed benefits. Per protocol: negative findings are not buried.

---

## 1. Ablation Flags Are Metadata-Only (CRITICAL)

**What was expected**: Leave-one-out ablation configs (e.g., `ree_no_hypothesis_ecology`) would disable the corresponding mechanism, producing measurably different behavior.

**What actually happened**: All 9 ablation conditions (full_ree, ree_core, baseline_none, and 6 leave-one-out variants) produced **identical behavior** (0.00 effect size across all comparisons).

**Root cause**: `BenchmarkRunner._build_registry()` always creates the same three operators (`ScenarioRetrieveOperator`, `ScenarioHypothesisOperator`, `StopOperator`) regardless of the `ablation` dictionary. The flags are recorded in `ExperimentManifest` metadata but do not influence which operators are registered or how the controller behaves.

**Consequence**: No ablation hypothesis can be tested. H-REE-09 (synergy), all leave-one-out comparisons, and all additive comparisons are **INCONCLUSIVE** by design, not by result.

**Status**: METHODOLOGICAL DEFECT — requires wiring ablation flags into operator registration and controller behavior before any ablation experiment is valid.

---

## 2. Quality Metrics Are Incomparable Across Architectures (CRITICAL)

**What was expected**: A common quality metric allowing fair comparison between B0, B1, and REE.

**What actually happened**: 
- B0 and B1 produce `claims` (text strings in `BaselineResult`) but zero `hypotheses` and zero items in `evidence_ids`.
- REE produces structured `hypothesis` and `evidence` artifacts tracked in `state.views.hypotheses` and `state.evidence_ids`.
- The quality metric `hypothesis_count + evidence_count + claim_count` trivially returns 0 for B0/B1 and ~7.4 for REE at every budget.

**Root cause**: B0 and B1 are implemented as separate code paths (`DirectModelBaseline`, `SimpleReflectionBaseline`) that produce `BaselineResult` with claims, not `ScenarioResult` with hypothesis/evidence/ignorance counts. The wrapping function `_wrap_baseline()` creates a `ScenarioResult` with empty lists for hypotheses and ignorance.

**Consequence**: The 120-0-0 win/tie/loss and infinite effect sizes in hypotheses are **measurement artifacts, not scientific findings**. No valid quality comparison between REE and baselines has been performed.

**Status**: METHODOLOGICAL DEFECT — requires either (a) comparable answer-level quality evaluation against ground truth, or (b) baselines that produce comparable structured artifacts.

---

## 3. Token Accounting Is Fundamentally Asymmetric (CRITICAL)

**Observed data**:
| Architecture | Budget 2k | Budget 5k | Budget 10k | Budget 20k |
|---|---|---|---|---|
| B0_direct | 1,000 | 1,000 | 1,000 | 1,000 |
| B1_reflection | 1,998 | 4,998 | 9,996 | 19,998 |
| full_ree | 1,133 | 1,143 | 1,143 | 1,143 |

**Problem**: 
- B0 uses `min(500, budget/2)` tokens — always 1000.
- B1 uses `budget/3` per step × 3 — nearly the full budget.
- REE's mock operators use fixed small costs (50–100 tokens each) — uses ~1143 regardless of budget.

**Consequence**: REE appears maximally compute-efficient, but this is because mock operators have unrealistically low costs. In reality, each REE step would require substantial LLM inference. The "equal budget" protocol is satisfied but the comparison is meaningless because different architectures interpret the budget differently.

---

## 4. Budget Never Constrains REE Behavior

**Observed**: REE produces identical behavior at 2k, 5k, 10k, and 20k token budgets (mean steps: 8.3, 8.4, 8.4, 8.4; mean tokens: 1133, 1143, 1143, 1143).

**Root cause**: Mock operators have fixed tiny costs. The controller stops when (a) the retrieve operator exhausts the evidence pool, (b) the hypothesis operator caps at 4 hypotheses, and (c) the stop operator activates. Budget exhaustion never triggers.

**Consequence**: The Quality–Compute Pareto frontier analysis is uninformative. REE occupies one point regardless of budget. Scaling behavior cannot be studied.

---

## 5. Heuristic Bid Calibration Is Near-Zero (GENUINE FINDING)

**Observed**: Spearman correlation between operator bids (estimated information gain) and realized scalarized epistemic gain: **r = 0.039**.

**Interpretation**: The current heuristic bidding system contains **essentially no predictive signal** about which cognitive action will produce the greatest epistemic gain. The epistemic market is selecting actions effectively at random with respect to realized value.

**This is a genuine negative finding**, not a methodological artifact. The mock operators' bids are influenced by `state.views.self_model` and `state.views.ignorance_items` (verified by mechanism influence tests), but these influences do not correlate with actual gain.

**Possible explanations**:
1. The gain vector components are determined by operator execution mechanics, not by state features
2. The bid scaling factors (self_model rates, ignorance boost) are calibrated to abstract heuristic values, not to realized utility
3. The scalarization weights may not align with what bids predict

---

## 6. Ignorance Items Are Never Produced (METHODOLOGICAL GAP)

**Observed**: `ignorance_count = 0` across ALL holdout scenarios and ALL architectures.

**Root cause**: Neither `ScenarioRetrieveOperator` nor `ScenarioHypothesisOperator` produce artifacts classified as ignorance items. The `AttackHypothesisOperator` (which could produce ignorance items) is not used in benchmarks.

**Consequence**: H-REE-02 (Ignorance Foresight) is **entirely untestable** in the current framework.

---

## 7. Evidence Independence Is Not Exercised

**Observed**: Source lineage metadata (`parent_source` fields) exists in scenario evidence pools, but no mock operator reads or uses this metadata to influence behavior.

**Consequence**: H-REE-03 (Evidence Independence) cannot be tested.

---

## 8. Feature Importance Is Dominated by Constant Features

**Observed**: Features `belief_volatility`, `contradiction_density`, `highest_ignorance_priority`, `mean_ignorance_priority`, and `self_model_expected_success` all show importance = 0.585.

**Root cause**: These features have identical default values across most mock epistemic states (e.g., ignorance priority = 0 everywhere, self_model success = 0.7 everywhere). The high "importance" is a statistical artifact of constant-vs-constant correlation, not genuine predictive power.

**Only `budget_fraction` (0.117) and `evidence_count` (0.112) show non-spurious variation.**

---

## 9. Prompt-Only Controls Were Not Testable

**Status**: `PromptOnlyControl` classes exist but are infrastructure-only. No experiment compared architectural mechanisms against prompt-only alternatives, because the mock operators don't use LLM prompts.

---

## 10. Only Two Action Types in Counterfactual Study

**Observed**: 701 `CognitiveActionOutcome` records, but only 2 action types: `retrieve` (381 high-gain records) and `generate_hypothesis` (200 high-gain, 120 low-gain).

**Missing action types**: `reason`, `attack_hypothesis`, `counterfactual`, `ontology_revision`, `synthesize`.

**Consequence**: The counterfactual cognition table can only compare retrieve vs. generate_hypothesis. The full action space cannot be evaluated.

---

## Summary of Hypotheses Affected

| Hypothesis | Status | Reason |
|---|---|---|
| H-REE-01 (Self-model) | INCONCLUSIVE | No ground-truth quality comparison possible |
| H-REE-02 (Ignorance) | INCONCLUSIVE | No ignorance items produced |
| H-REE-03 (Evidence independence) | INCONCLUSIVE | Independence not exercised |
| H-REE-04 (Hypothesis ecology) | INCONCLUSIVE | Quality not comparable across architectures |
| H-REE-05 (Pareto frontier) | NOT_SUPPORTED | Budget never constrains REE; quality metric broken |
| H-REE-06 (State predicts action value) | NOT_SUPPORTED | Bid correlation r=0.039 |
| H-REE-07 (Counterfactual robustness) | INCONCLUSIVE | No counterfactual operator in benchmarks |
| H-REE-08 (Memory consolidation) | INCONCLUSIVE | No memory mechanisms in benchmarks |
| H-REE-09 (Synergy) | INCONCLUSIVE | Ablation flags have no behavioral effect |
| H-REE-10 (Ontology) | INCONCLUSIVE | No ontology operator in benchmarks |

---

## What IS Demonstrated

Despite the above limitations, the campaign DOES demonstrate:

1. **Infrastructure completeness**: 360 holdout records + 162 ablation records + 701 counterfactual outcomes were produced and persisted as machine-readable JSONL.
2. **Deterministic reproducibility**: All scenarios are seed-deterministic and leakage-free.
3. **Structural behavioral difference**: REE produces multi-step trajectories with hypothesis generation (mean 8.4 steps, 4 hypotheses per scenario), while baselines produce fixed-format outputs.
4. **Bid-value decorrelation**: The heuristic bidding system demonstrably fails to predict realized cognitive value (r=0.039), which is a genuine scientific observation.
5. **Event-sourcing and state-forking work**: Counterfactual forks execute correctly and produce valid outcome records.

---

## Recommendations

1. **Implement answer-level quality evaluation** that compares system outputs against `scenario.ground_truth` using string matching or semantic similarity
2. **Wire ablation flags into actual operator registration** so leave-one-out experiments change behavior
3. **Add mock operators for all action types** (reason, attack, counterfactual, etc.)
4. **Use realistic token costs** or run with a live LLM provider for valid compute comparisons
5. **Add ignorance-producing operators** to test H-REE-02
6. **Run with live providers** for Claims A-H validation — mock experiments cannot establish quality differences
