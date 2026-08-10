# ASAR-REE Scientific Campaign — Negative Findings (v2)

**Campaign date**: 2026-08-10
**Starting SHA**: 2c44f09
**Branch**: feature/asar-ree-v2

This document records negative results, methodological limitations, and mechanisms that did not demonstrate the claimed benefits.

---

## 1. No Quality Improvement from Any Architecture (CRITICAL)

**What was expected**: REE architectures would produce higher ground-truth accuracy than simpler baselines.

**What happened**: All 5 architectures (B0, B1, B3, B4, full_ree) achieve identical 33% ground-truth match rate across all budget levels.

**Root cause**: The 33% rate comes from substring matching: 2 of 6 families have single-character ground truths (false_majority: "A"/"B", duplicated_source: "Y") that trivially match evidence text in all architectures. The other 4 families have phrase-level ground truths that no mock operator reproduces.

**Consequence**: No quality-based hypothesis can be tested. H-REE-05 (Pareto improvement) is NOT SUPPORTED.

---

## 2. B0 (Direct) Pareto-Dominates All Other Architectures (CRITICAL)

**What was expected**: REE would achieve better quality/compute efficiency.

**What happened**: All architectures produce identical quality (0.33). B0 does so at minimum cost (1000 tokens). Every other architecture uses more compute for the same quality.

**Consequence**: Under the current experimental conditions, the simplest possible architecture is optimal.

---

## 3. Ignorance Mechanism Crowds Out Hypothesis Generation (GENUINE FINDING)

**What was expected**: Ignorance tracking would complement hypothesis ecology.

**What happened**: When both are active (full_ree), only 1 hypothesis is generated. When ignorance is disabled (ree_no_ignorance_ledger), 4 hypotheses are generated.

**Mechanism**: The ScenarioAttackOperator produces ignorance items that boost the ScenarioRetrieveOperator's bids via `ignorance_boost`. This channels budget toward retrieval (and further attacks) instead of hypothesis generation.

**This is a genuine negative interaction effect**: adding the ignorance mechanism REDUCES hypothesis diversity by approximately 75%.

---

## 4. Market Bids Are Anti-Calibrated (GENUINE FINDING)

**Bid-value correlation**: r = -0.083

**Mean realized gain by action**:
| Action | Mean Gain | Market should prefer? |
|---|---|---|
| generate_hypothesis | +0.272 | YES |
| retrieve | +0.150 | YES |
| reason | -0.050 | NO |
| attack_hypothesis | -0.050 | NO |

The market's bid system slightly PREFERS lower-value actions. This is worse than random selection.

---

## 5. Reason and Attack Operators Produce Negative Gain

**What was expected**: All cognitive operators would contribute positive epistemic value.

**What happened**: reason (-0.05) and attack_hypothesis (-0.05) produce negative mean realized gain.

**Root cause**: The mock operators produce artifacts with costs but no content-relevant quality improvement. Their gain vector components are neutral or slightly negative because they consume budget without adding to the quality-relevant dimensions.

**Caveat**: This may be entirely a mock-operator artifact. Real LLM-based reasoning and hypothesis attacking could produce very different gains.

---

## 6. Self-Model Ablation Produces No Behavioral Difference

**What was expected**: Removing the self-model would change operator selection.

**What happened**: `ree_no_self_model` produces identical behavior to full_ree (hyp=1.0, ign=8.0, steps=11, GT=100%).

**Root cause**: The self-model's `operator_success_rates` scale all bids by the same factor (default 0.7), which doesn't change the relative ranking. The ablation flag doesn't actually remove the self-model from the state — it's recorded as metadata.

---

## 7. Most Ablation Flags Have No Behavioral Effect

**Flags that change behavior**: `hypothesis_ecology` (controls ScenarioHypothesisOperator registration), `ignorance_ledger` (controls ScenarioAttackOperator registration).

**Flags with NO behavioral effect**: `self_model`, `evidence_independence`, `epistemic_market`, `stopping_policy`, `counterfactual_lab`, `ontology_forge`, `sealed_tribunal`, `federated_memory`, `trajectory_collection`, `value_model`.

**Root cause**: Only `hypothesis_ecology` and `ignorance_ledger` are checked in `_build_registry()`. The other flags are metadata-only.

---

## 8. B4 and Full REE Are Behaviorally Identical

**What was expected**: B4 (adaptive) and B5 (full) would differ in which mechanisms are active.

**What happened**: Both use `EpistemicController` with the same operator registry built from the same ablation config (empty dict → all True). B4 and full_ree produce identical steps, tokens, and GT match rates.

**Root cause**: The benchmark runner calls `_build_registry(scenario, ablation or {})` for both B4 and full_ree, producing the same registry. The only difference is how results are captured (full_ree extracts hypotheses/ignorance from final state).

---

## 9. Ground-Truth Evaluation Is Too Coarse

**Substring matching** is inappropriate for single-character ground truths ("A", "B", "Y") which match almost any text. And it's too strict for phrase-level ground truths that mock operators never reproduce verbatim.

**Needed**: Semantic similarity or structured answer comparison.

---

## 10. Feature Importance Is Dominated by Constant Features

Features at 0.572 importance (hypothesis_entropy, belief_volatility, contradiction_density, self_model_expected_success) have minimal or zero variation across states. Their high "importance" is a statistical artifact.

Only `budget_fraction` and `evidence_count` show genuine variation, and their importance values are low (0.12).

---

## Summary: What DOES Work

Despite the negative findings:

1. **Ablation flags now produce behavioral differences** for 2 of 12 mechanisms
2. **The experiment infrastructure is complete and functional** — 2,862 records collected
3. **The ignorance-hypothesis interaction is a genuine discovery** about budget competition
4. **The anti-calibration finding (r=-0.083)** is a concrete, actionable deficit
5. **Action-value decomposition** (+0.27 for hypothesis, -0.05 for reason/attack) provides clear optimization targets
6. **Token accounting is now normalized** and budget constraints are binding for REE
