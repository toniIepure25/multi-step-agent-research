# ASAR-REE Scientific Certification — Final Report (v2)

**Campaign date**: 2026-08-10
**Starting SHA**: `2c44f09`
**Ending SHA**: see final commit
**Branch**: `feature/asar-ree-v2`

---

## 1. Abstract

We executed a controlled empirical campaign to determine whether the ASAR-REE (Reflexive Epistemic Ecology) architecture produces measurably better epistemic intelligence than simpler research architectures. The campaign ran 600 holdout benchmark trials across 5 architectures × 4 budget levels × 6 scenario families, 162 ablation trials across 9 configurations, and 2,100 counterfactual cognitive action outcomes from 60 episodes.

**Primary finding**: Under deterministic controlled benchmarks with mock operators, all architectures achieve identical ground-truth accuracy (33%). No architecture produces better *answer quality*. The architectural differences manifest in *structural behavior*: REE generates hypotheses and ignorance items, uses more diverse operator sequences, and scales compute with budget — but these structural differences do not improve correctness on the tested scenarios.

**Significant secondary findings**:

1. **The ignorance/attack mechanism crowds out hypothesis generation** under budget constraints (full REE: 1 hypothesis, REE-without-ignorance: 4 hypotheses). This is a genuine interaction effect with practical implications.

2. **Operator bids are anti-calibrated** (r = -0.083): the epistemic market slightly prefers lower-value actions. The reason and attack operators produce negative mean realized gain (-0.05 each), while retrieve (+0.15) and generate_hypothesis (+0.27) produce positive gain.

3. **Ablation flags now produce measurable behavioral differences**: removing hypothesis ecology eliminates hypothesis generation; removing ignorance eliminates attack behavior and releases budget for hypothesis generation.

4. **Budget scaling differs across architectures**: B0 is budget-invariant (1000 tokens), B3 uses fixed 1500, B1 scales linearly, while B4/full_ree scale sub-linearly (2000–14000 tokens across 2000–20000 budget).

---

## 2. Research Thesis

> Autonomous research intelligence can be improved not merely by allocating more reasoning compute, but by maintaining an explicit ecology of competing epistemic representations and using metacognitive control to select the most valuable cognitive operation under bounded resources.

**Verdict**: NOT SUPPORTED by the current controlled experiments. All architectures produce identical ground-truth accuracy. The structural differences (hypothesis generation, ignorance tracking) do not translate to quality improvement in the mock-operator framework. The experiment does NOT disprove the thesis — it establishes that the thesis cannot be tested with mock operators that produce deterministic, content-independent outputs.

---

## 3. Architecture Conditions

| Code | Description | Operators in Benchmark | Budget Behavior |
|------|-------------|----------------------|-----------------|
| B0 | Direct — single call | 1 synthetic step | Fixed 1000 tokens |
| B1 | Reflection — answer/critique/revision | 3 synthetic steps | Linear with budget |
| B3 | Fixed REE — predetermined sequence | retrieve→reason→hypothesis→stop | Fixed 1500 tokens |
| B4 | Adaptive REE — heuristic market | retrieve, reason, hypothesis, attack, stop | Sub-linear scaling |
| B5/full_ree | Full REE — all mechanisms | retrieve, reason, hypothesis, attack, stop | Sub-linear scaling |

---

## 4. Experimental Design

- **600 holdout records**: 30 holdout scenarios × 4 budgets × 5 architectures
- **162 ablation records**: 18 dev scenarios × 9 configs
- **2,100 counterfactual outcomes**: 60 dev episodes × state-forking with 4+ action types
- **Frozen protocol**: `experiments/protocols/FROZEN_PROTOCOL.md`

---

## 5. Benchmark Construction

6 families, 15 scenarios each (10 dev, 5 holdout), seed-deterministic, 0 leakage violations.

| Family | Ground Truth Type | Holdout GT Match Rate |
|--------|-------------------|----------------------|
| false_majority | Single letter (A/B) | 100% all architectures* |
| duplicated_source | Single letter (Y) | 100% all architectures* |
| assumption_flip | Full phrase | 0% all architectures |
| hypothesis_ecology | Short string (H2) | 0% all architectures |
| ignorance_discovery | Full sentence | 0% all architectures |
| stopping_quality | Full phrase | 0% all architectures |

*100% match rate is a substring-matching artifact: single-character ground truths match widely.

---

## 6. Compute Controls

| Architecture | Budget 2k | Budget 5k | Budget 10k | Budget 20k |
|---|---|---|---|---|
| B0 | 1,000 | 1,000 | 1,000 | 1,000 |
| B1 | 1,998 | 4,998 | 9,996 | 19,998 |
| B3 | 1,500 | 1,500 | 1,500 | 1,500 |
| B4 | 2,000 | 5,000 | 5,500 | 14,000 |
| full_ree | 2,000 | 5,000 | 5,500 | 14,000 |

Token costs are now normalized at 500 tokens per operator step (250 input + 250 output).

B4 and full_ree show identical compute profiles because they use the same controller with the same operator set. The only difference is that full_ree captures hypothesis/ignorance state in results.

---

## 7. Primary Confirmatory Results

### Table 26: Hypothesis Verdict Table

| Hypothesis | N | Baseline | REE Condition | Effect | 95% CI | Compute Diff | Verdict | Evidence |
|---|---|---|---|---|---|---|---|---|
| H-REE-01 Self-model | 600 | B0 (33% GT) | full_ree (33% GT) | 0% quality difference | — | +5625 tokens | INCONCLUSIVE | Quality identical |
| H-REE-02 Ignorance foresight | 162 | full_ree (ign=8.0) | no_ignorance (ign=0.0) | -8.0 ignorance items | — | 0 steps diff | PARTIALLY_SUPPORTED | Ignorance produced; utility unproven |
| H-REE-03 Evidence independence | 600 | All 33% GT | All 33% GT | 0% quality difference | — | — | INCONCLUSIVE | No correctness impact |
| H-REE-04 Hypothesis ecology | 162 | no_ecology (hyp=0) | full_ree (hyp=1) | +1 hypothesis | — | 0 steps diff | PARTIALLY_SUPPORTED | Hypotheses produced; crowded by ignorance |
| H-REE-05 Pareto frontier | 600 | All 33% GT | All 33% GT | No quality diff at any budget | — | Variable | NOT_SUPPORTED | Same quality, higher compute for REE |
| H-REE-06 Predicts action value | 2100 | Random | Heuristic bid | r=-0.083 | — | — | NOT_SUPPORTED | Anti-calibrated bids |
| H-REE-07 Counterfactual | 600 | All 33% GT | All 33% GT | 0% | — | — | INCONCLUSIVE | Mock operator limitation |
| H-REE-08 Memory | 0 | — | — | — | — | — | INCONCLUSIVE | Not tested |
| H-REE-09 Synergy | 162 | Full (hyp=1,ign=8) | No-ign (hyp=4,ign=0) | Negative interaction | — | 0 | NEGATIVE | Ignorance crowds out hypothesis |
| H-REE-10 Ontology | 0 | — | — | — | — | — | INCONCLUSIVE | Not tested |

### Verdict Summary
- **SUPPORTED**: 0
- **PARTIALLY_SUPPORTED**: 2 (H-REE-02, H-REE-04 — mechanism functions, utility unproven)
- **NOT_SUPPORTED**: 2 (H-REE-05, H-REE-06)
- **NEGATIVE**: 1 (H-REE-09 — ignorance × hypothesis interaction is harmful)
- **INCONCLUSIVE**: 5

---

## 8. Quality–Compute Frontier

### Table 27: Quality-Compute Table

| Architecture | Budget | GT Rate | Quality | Tokens | Steps | Hyps | Ign | Pareto-dominated? |
|---|---|---|---|---|---|---|---|---|
| B0 | 2k | 33% | 0.33 | 1,000 | 1 | 0 | 0 | Pareto-optimal (min cost) |
| B0 | 5k–20k | 33% | 0.33 | 1,000 | 1 | 0 | 0 | Pareto-optimal |
| B1 | 2k | 33% | 0.33 | 1,998 | 3 | 0 | 0 | Dominated by B0 |
| B1 | 5k–20k | 33% | 0.33 | 4,998–19,998 | 3 | 0 | 0 | Dominated by B0 |
| B3 | all | 33% | 0.33 | 1,500 | 4 | 0 | 0 | Dominated by B0 |
| B4 | 2k | 33% | 0.33 | 2,000 | 5 | 0 | 0 | Dominated by B0 |
| B4 | 5k–20k | 33% | 0.33 | 5,000–14,000 | 11–29 | 0 | 0 | Dominated by B0 |
| full_ree | 2k | 33% | 0.33 | 2,000 | 5 | 1 | 2 | Dominated by B0 (quality) |
| full_ree | 5k | 33% | 0.33 | 5,000 | 11 | 1 | 8 | Dominated by B0 |
| full_ree | 10k | 33% | 0.33 | 5,500 | 12 | 1 | 9 | Dominated by B0 |
| full_ree | 20k | 33% | 0.33 | 14,000 | 29 | 1 | 26 | Dominated by B0 |

### Pareto Analysis Answers

1. **Does Full REE dominate Fixed REE?** No. Same quality, more compute.
2. **Does Adaptive REE dominate Fixed REE?** No. Same quality, more compute.
3. **Break-even complexity?** Not observed. Quality is flat across all architectures.
4. **Does REE perform worse from excessive cognition?** Not in quality, but it wastes compute.
5. **Low-budget advantage?** No. B0 achieves same quality at minimum cost.
6. **Budget scaling?** More budget helps REE generate more ignorance items but not quality.

**Conclusion**: B0 (direct) Pareto-dominates all other architectures under mock conditions. This is a CRITICAL negative finding but is expected given mock operators produce content-independent outputs.

---

## 9. Hypothesis Ecology Findings

### Cross-Architecture (holdout, all budgets averaged)
| Architecture | Hypotheses | GT Match | Ignorance | Steps |
|---|---|---|---|---|
| B0 | 0 | 0% | 0 | 1 |
| B1 | 0 | 0% | 0 | 3 |
| B3 | 0 | 0% | 0 | 4 |
| B4 | 0 | 0% | 0 | 14.2 |
| full_ree | 1.0 | 0% | 11.2 | 14.2 |

### Ablation (dev, 5k budget)
| Config | Hypotheses | Ignorance | Steps |
|---|---|---|---|
| full_ree | 1.0 | 8.0 | 11 |
| ree_no_hypothesis_ecology | 0.0 | 0.0 | 11 |
| ree_no_ignorance_ledger | 4.0 | 0.0 | 11 |

### KEY FINDING: Ignorance-Hypothesis Competition
When both hypothesis ecology and ignorance/attack are active, the attack operator produces ignorance items that boost retrieve bids, consuming budget that would otherwise go to hypothesis generation. Full REE generates only 1 hypothesis while REE-without-ignorance generates 4.

This is a **genuine negative interaction effect**: the ignorance mechanism reduces hypothesis diversity under budget constraints.

---

## 10. Ignorance Findings

REE produces ignorance items when the attack operator is enabled (mean 8.0 items on dev, up to 26 at 20k budget). Removing the ignorance mechanism (`ree_no_ignorance_ledger`) eliminates all ignorance items.

**The ignorance mechanism WORKS mechanically** — it produces structured ignorance artifacts. However:
- It does not improve ground-truth accuracy
- It crowds out hypothesis generation
- Its behavioral impact (boosting retrieve bids) consumes budget without quality return

---

## 11. Self-Model Findings

The self-model is present with default `overall_success_rate=0.7`. In the `ree_no_self_model` ablation, behavior is identical to full_ree (both produce hyp=1.0, ign=8.0, steps=11, GT=100%), indicating that the self-model's bid-scaling effect does not change operator selection in practice.

---

## 12. Evidence Independence

Not differentially tested. Source lineage metadata exists but no operator uses it.

---

## 13. Social Epistemology

Tribunal not included in benchmark runner. Not tested.

---

## 14. Counterfactual/Ontology

No counterfactual or ontology operators in benchmarks. Not tested.

---

## 15. Stopping Policy

REE stopping behavior is governed by budget exhaustion and operator proposal availability, not the StoppingPolicy mechanism. At 20k budget, REE runs 29 steps (vs 5 at 2k), confirming the budget constraint is now binding. The stopping policy's `evaluate()` method runs but does not override the market.

---

## 16. Counterfactual Cognitive-Policy Study

### Table 28: Counterfactual Cognition Table

| Action Type | N (high gain) | N (low gain) | Mean Gain | Bid-Value r | Classification |
|---|---|---|---|---|---|
| retrieve | 540 | 0 | +0.150 | — | Consistently positive |
| generate_hypothesis | 540 | 0 | +0.272 | — | Highest positive gain |
| reason | 0 | 540 | -0.050 | — | Consistently negative |
| attack_hypothesis | 0 | 480 | -0.050 | — | Consistently negative |
| **Overall** | **1080** | **1020** | **+0.081** | **-0.083** | **Anti-calibrated** |

### KEY FINDINGS

1. **Generate_hypothesis is the highest-value action** (+0.27 mean gain). The market should strongly prefer it.

2. **Reason and attack produce negative gain** (-0.05 each). Under the current gain scalarization, these operators actively harm epistemic utility.

3. **The market is anti-calibrated** (r=-0.083). Instead of selecting high-value actions, the bid system slightly prefers low-value ones.

4. **An optimal policy would select retrieve or generate_hypothesis exclusively**, avoiding reason and attack entirely. This contradicts the architectural intuition that diverse cognitive operations are beneficial.

5. **However**: negative gain for reason/attack may be an artifact of the mock operator implementation (they produce artifacts with fixed small costs but no quality-relevant content). With a real LLM, reasoning and hypothesis-attacking could produce genuine epistemic value.

---

## 17. State-Feature Predictive Study

### Feature Importance (from counterfactual dataset)

| Feature | Importance | Status |
|---|---|---|
| hypothesis_entropy | 0.572 | Spurious — low variation |
| belief_volatility | 0.572 | Spurious — constant |
| contradiction_density | 0.572 | Spurious — constant |
| evidence_count | 0.572 | Potentially real |
| self_model_expected_success | 0.572 | Spurious — constant at 0.7 |
| top_hypothesis_margin | 0.474 | Low variation |
| workspace_saturation | 0.474 | Low variation |
| hypothesis_count | 0.474 | Caps at 4 |

**Conclusion**: The predictive study cannot distinguish genuinely informative features from constant/low-variation ones in the mock framework. A learned scheduler is NOT justified from this data.

---

## 18. Ablation Results

### Leave-One-Out Ablation (dev scenarios, 5k budget)

| Config | Hyps | Ign | Steps | GT Match | Behavioral Difference |
|---|---|---|---|---|---|
| full_ree | 1.0 | 8.0 | 11 | 100% | Baseline |
| ree_no_hypothesis_ecology | 0.0 | 0.0 | 11 | 100% | No hypotheses, no ignorance |
| ree_no_ignorance_ledger | 4.0 | 0.0 | 11 | 100% | 4x more hypotheses, no ignorance |
| ree_no_self_model | 1.0 | 8.0 | 11 | 100% | No difference |
| ree_no_evidence_independence | 1.0 | 8.0 | 11 | 100% | No difference |
| ree_no_epistemic_market | 1.0 | 8.0 | 11 | 100% | No difference |
| ree_no_stopping_policy | 1.0 | 8.0 | 11 | 100% | No difference |
| ree_core | 1.0 | 8.0 | 11 | 100% | No difference |
| baseline_none | 0.0 | 0.0 | 11 | 100% | No hypotheses, no ignorance |

### Ablation Findings

1. **hypothesis_ecology and ignorance_ledger are the only ablation flags that change behavior**. They control whether ScenarioHypothesisOperator and ScenarioAttackOperator are registered.

2. **self_model, evidence_independence, epistemic_market, stopping_policy** — these flags don't control operator registration in the current benchmark runner, so they have no effect.

3. **Removing ignorance increases hypothesis diversity** (1→4 hypotheses), a genuine interaction effect.

---

## 19. Interaction Effects

### Confirmed Interaction: Ignorance × Hypothesis Ecology

| Ignorance | Hypothesis Ecology | Hypotheses | Ignorance Items |
|---|---|---|---|
| ON | ON | 1.0 | 8.0 |
| ON | OFF | 0.0 | 0.0* |
| OFF | ON | 4.0 | 0.0 |
| OFF | OFF | 0.0 | 0.0 |

*Hypothesis ecology OFF means no ScenarioHypothesisOperator, so ScenarioAttackOperator (which requires hypotheses to attack) cannot function.

**Effect**: When both are active, ignorance/attack consumes budget that would go to hypothesis generation. This is a **negative interaction**: the full system produces fewer hypotheses than the hypothesis-only system.

---

## 20. Minimal Effective REE

Based on ablation results, the **minimal configuration that produces all observed behavioral features** is:

```
EpistemicState
+ ScenarioRetrieveOperator
+ ScenarioHypothesisOperator  (hypothesis_ecology=True)
+ ScenarioReasonOperator
+ StopOperator
```

WITHOUT the attack/ignorance mechanism, since it crowds out hypotheses. However, this finding may not generalize to live LLM settings.

---

## 21. Task-Conditional Effects

| Family | REE Behavioral Difference |
|---|---|
| false_majority | 100% GT match regardless (substring artifact) |
| duplicated_source | 100% GT match regardless |
| assumption_flip | 0% GT match regardless |
| hypothesis_ecology | 0% GT match regardless |
| ignorance_discovery | 0% GT match regardless |
| stopping_quality | 0% GT match regardless |

REE does not show task-conditional quality advantages. The 100% matches on false_majority and duplicated_source are substring-matching artifacts (ground truth is a single letter).

---

## 22. Live Validation

Not executed. Prerequisite: live LLM provider credentials.

---

## 23. Negative Findings

See `NEGATIVE_FINDINGS.md` for detailed documentation. Key negatives:

1. **No quality improvement**: All architectures achieve identical GT accuracy
2. **B0 Pareto-dominates all others**: Simplest architecture is most efficient
3. **Ignorance crowds out hypothesis generation**: Genuine negative interaction
4. **Market bids are anti-calibrated** (r=-0.083)
5. **Reason and attack operators produce negative gain** in mock framework
6. **Self-model ablation produces no behavioral difference**
7. **Most ablation flags have no behavioral effect** (only hypothesis_ecology and ignorance_ledger are wired)

---

## 24. Limitations

### Fundamental
- Mock operators produce content-independent outputs — they cannot test semantic quality
- Ground-truth evaluation uses substring matching — too coarse for some families, too permissive for others
- B4 and full_ree use identical controllers — they only differ in result capture, not behavior
- Ablation flags only control 2 of 12 mechanisms via operator registration

### What Would Change with Live LLMs
- Operator outputs would depend on question content and evidence
- Quality differences between architectures could emerge
- Reason and attack operators could produce genuine analytical value
- Hypothesis generation could produce content-relevant hypotheses
- Self-model could calibrate from actual success/failure patterns

---

## 25. Novel Contributions

### A. Empirical Interaction Discovery
The ignorance-hypothesis competition finding is genuine: explicit ignorance tracking consumes cognitive budget that would otherwise produce hypothesis diversity. This is a meaningful architectural insight.

### B. Market Anti-Calibration Finding
The heuristic bidding system (r=-0.083) is worse than random at selecting high-value actions. This is a concrete, measurable deficit that future work should address.

### C. Counterfactual Cognitive Action Dataset
2,100 (state, action, gain) records demonstrate the feasibility of counterfactual cognitive-action evaluation via event-sourced state forking.

### D. Validated Experiment Infrastructure
The complete pipeline — scenario generation, architecture dispatch, ablation, counterfactual forking, statistical analysis — runs end-to-end and produces machine-readable artifacts.

### E. Action-Value Decomposition
The finding that retrieve (+0.15) and generate_hypothesis (+0.27) produce positive gain while reason (-0.05) and attack (-0.05) produce negative gain provides a concrete target for metacognitive improvement.

---

## 26. Claims NOT Supported

| Claim | Status | Evidence |
|---|---|---|
| A. Epistemic state outperforms prompt-only | NOT TESTABLE | Mock operators don't use prompts |
| B. Self-model predicts failure | NOT SUPPORTED | No behavioral difference when ablated |
| C. Sealed deliberation preserves minorities | NOT TESTABLE | Tribunal not in benchmarks |
| D. Source-lineage prevents false confidence | NOT TESTABLE | Independence not exercised |
| E. Ontology revision improves frame-escape | NOT TESTABLE | No ontology operator |
| F. Metacognitive scheduling improves Pareto | NOT SUPPORTED | B0 Pareto-dominates |
| G. Epistemic state predicts cognitive value | NOT SUPPORTED | r=-0.083 |
| H. Mechanism synergy | NEGATIVE | Ignorance-hypothesis negative interaction |

---

## 27. Next Research Directions

### Immediate Requirements for Valid Quality Testing
1. **Run with live LLM provider** — the only path to genuine quality comparison
2. **Replace substring matching with semantic evaluation** for ground truth
3. **Wire remaining ablation flags** (self_model, market, stopping, etc.) into actual controller behavior
4. **Make B4 behaviorally distinct from full_ree** — B4 should use a subset of operators

### Based on Findings
5. **Fix bid calibration** — the r=-0.083 finding provides a concrete improvement target
6. **Address ignorance-hypothesis budget competition** — either increase budget, prioritize hypothesis generation, or interleave attack more efficiently
7. **Remove or recalibrate reason/attack operators** — they produce negative gain under current settings
8. **Test with larger scenario pools** — current 5 holdout per family limits statistical power

---

## Appendix A: Raw Artifact Locations

| Artifact | Path | Records |
|---|---|---|
| Holdout records | `experiments/campaign/results/holdout_records.jsonl` | 600 |
| Ablation records | `experiments/campaign/results/ablation_records.jsonl` | 162 |
| Counterfactual outcomes | `experiments/campaign/results/counterfactual_outcomes.jsonl` | 2,100 |
| Family analysis | `experiments/campaign/results/family_analysis.json` | — |
| Pairwise comparisons | `experiments/campaign/results/pairwise_comparisons.json` | — |
| Pareto data | `experiments/campaign/results/pareto_data.json` | — |
| Counterfactual analysis | `experiments/campaign/results/counterfactual_analysis.json` | — |

## Appendix B: Campaign Checkpoint

```text
CAMPAIGN: ASAR-REE Full Scientific Campaign (v2)
STATUS: COMPLETE

STARTING SHA: 2c44f09
BRANCH: feature/asar-ree-v2

CONDITIONS: B0, B1, B3, B4, full_ree + 9 ablation configs
N: 600 holdout + 162 ablation + 2100 counterfactual = 2862 total records
SEEDS: 42-56 (base 42 + index)
BUDGETS: 2000, 5000, 10000, 20000

PRIMARY RESULTS:
  - GT match rate: 33% across ALL architectures (no quality difference)
  - Ablation: hypothesis_ecology and ignorance_ledger produce behavioral changes
  - Ignorance-hypothesis negative interaction confirmed
  - Bid-value correlation: r=-0.083 (anti-calibrated)

EFFECT SIZES:
  - Quality: d=0.00 (all conditions identical)
  - Steps: d=1.48 (full_ree vs B0), d=1.25 (vs B1), d=1.14 (vs B3)
  - Tokens: d=0.72 (full_ree vs B0)
  - Hypothesis ecology ablation: d=undefined (0 → 4 hypotheses)

NEGATIVE RESULTS:
  - B0 Pareto-dominates all other architectures
  - Market anti-calibration (r=-0.083)
  - Reason/attack operators produce negative gain
  - Self-model ablation produces no behavioral difference
  - No quality improvement from any mechanism

METHODOLOGICAL ISSUES:
  - Mock operators produce content-independent output
  - Ground-truth evaluation uses crude substring matching
  - B4 and full_ree are behaviorally identical (same controller)
  - Only 2 of 12 ablation flags are wired to operator registration

HYPOTHESES UPDATED:
  - H-REE-05: NOT_SUPPORTED
  - H-REE-06: NOT_SUPPORTED
  - H-REE-09: NEGATIVE (ignorance-hypothesis competition)
  - H-REE-02: PARTIALLY_SUPPORTED (mechanism functions)
  - H-REE-04: PARTIALLY_SUPPORTED (mechanism functions)

NEXT CAMPAIGN: Live LLM validation (requires provider credentials)
```
