# ASAR-REE Scientific Campaign V2 — Final Report

## 1. Research Thesis

> Autonomous research intelligence can be improved by maintaining an explicit
> ecology of competing epistemic representations and using metacognitive control
> to select the most valuable cognitive operation under bounded resources.

Campaign V2 tests this thesis using a semantically meaningful controlled environment
where cognitive strategy meaningfully affects outcome quality.

## 2. Experimental Design

### Environment
**EpistemicWorldSimulator**: deterministic latent world with hidden hypotheses,
causal graphs, evidence pools, source reliabilities, and hidden variables.
Agents interact only through cognitive operations whose results depend on
(latent world + epistemic state + action), never seeing ground truth.

### Quality Metric
**EpistemicQualityVector** (10-dimensional):
correct_final_hypothesis, posterior_mass_on_true, hypothesis_ranking_quality,
causal_edge_precision/recall, hidden_variable_discovery, critical_assumption_identification,
evidence_provenance_quality, calibration, appropriate_abstention.

Headline scalar: preregistered weighted sum (correctness 25%, posterior 15%, ranking 15%, etc.)

### Scenario Families (5)
| Family | What it tests | # Worlds |
|--------|---------------|----------|
| hypothesis_ecology | Minority hypothesis preservation, anomaly recovery | 20 |
| false_majority | Source independence, confidence inflation resistance | 20 |
| ignorance_discovery | Hidden variable identification, confound detection | 20 |
| stopping_quality | When to stop (decisive vs noisy evidence) | 20 |
| source_duplication | Duplicate source detection, provenance tracking | 20 |

### Data Splits
| Split | N | Hash | Usage |
|-------|---|------|-------|
| dev | 50 | 6d835082c9db3ed0 | Tuning, development, ablation |
| validation | 25 | a22d9de26318686a | Validation |
| locked_test | 25 | 5f571ff5eac1bf7f | Final confirmatory (one-shot) |

### Architectures
- **B0_direct**: Single retrieve + generate hypothesis
- **B1_reflection**: Retrieve, generate, retrieve, generate, reason
- **full_ree**: EpistemicController with heuristic EpistemicMarket
- **B4_diversity_ree**: REE with DiversityAwareMarket penalty

## 3. Baselines

B0 is a minimal 2-step agent (retrieve one evidence, generate one hypothesis).
B1 uses a fixed 5-step strategy that is near-optimal for most scenario families.
B1 was not tuned against these specific scenarios — its strategy is generic.

## 4. Compute Controls

All operators use identical PER_STEP_TOKENS = 500. Default budget: 5000 tokens, 25 steps.
B0 uses ~1000 tokens. B1 uses ~2000 tokens. full_ree uses 2000-5500 tokens.
Pareto analysis at budgets: 2000, 5000, 10000, 20000 tokens.

## 5. Primary Results (Dev, N=150)

| Family | B0_direct | B1_reflection | full_ree |
|--------|-----------|---------------|----------|
| hypothesis_ecology | 0.080 | **0.700** | 0.130 |
| false_majority | 0.316 | **0.484** | 0.366 |
| ignorance_discovery | 0.475 | **0.700** | 0.528 |
| stopping_quality | 0.050 | **0.700** | 0.433 |
| source_duplication | **0.478** | 0.228 | 0.433 |
| **Overall** | 0.280 | **0.562** | 0.378 |

**B1 outperforms full_ree on 4 of 5 families.** Full REE beats B1 only on source_duplication.

## 6. Locked Test Results (N=75, one-shot)

| Family | B0 | B1 | REE |
|--------|-----|-----|-----|
| hyp_ecology | 0.080 | **0.700** | 0.130 |
| false_majority | **0.500** | 0.484 | 0.366 |
| ignorance | 0.475 | **0.700** | 0.323 |
| stopping | 0.050 | **0.700** | 0.480 |
| duplication | 0.335 | 0.385 | **0.480** |
| **Overall** | 0.288 | **0.594** | 0.356 |

**Locked test confirms dev findings.** B1 wins 3/5 families. REE wins duplication only.

## 7. Quality-Compute Pareto Frontier

| Architecture | Budget | Quality | Tokens Used |
|---|---|---|---|
| B0_direct | any | 0.280 | 1000 |
| **B1_reflection** | **any** | **0.562** | **2000** |
| full_ree | 2k | 0.378 | 2000 |
| full_ree | 5k | 0.378 | 5000 |
| full_ree | 10k | 0.378 | 5500 |
| full_ree | 20k | 0.378 | 5500 |

**B1 Pareto-dominates full_ree**: higher quality at lower cost.
REE quality does not improve with additional budget (plateaus at ~5500 tokens).

## 8. Causal Ablation Results

| Config | Quality | Hypotheses | Ignorance | vs Full REE |
|--------|---------|------------|-----------|-------------|
| full_ree (all ON) | 0.365 | 2.0 | 0.2 | baseline |
| **no_hypothesis** | **0.037** | **0.0** | **0.0** | **-90%** |
| no_ignorance | 0.325 | 2.0 | 0.0 | -11% |
| no_self_model | 0.365 | 2.0 | 0.2 | 0% (non-causal) |
| no_stopping | 0.365 | 2.0 | 0.2 | 0% (non-causal) |
| no_market | 0.365 | 2.0 | 0.2 | 0% (non-causal) |

**Hypothesis ecology is causally critical** (d ≈ 1.4, quality drops 90%).
Ignorance has small measured effect. Self-model, stopping, and market
ablation produce identical behavior (remain non-causal in practice).

## 9. Market Variant Comparison

| Architecture | Quality | Compute |
|---|---|---|
| B0_direct | 0.280 | 1000 |
| **B1_reflection** | **0.562** | **2000** |
| full_ree (heuristic) | 0.352 | ~4000 |
| B4_diversity_ree | 0.333 | ~4000 |
| full_ree + round_robin | varies by family | ~4000 |

**Round-robin beats market** on ignorance_discovery (0.79 vs 0.34)
and false_majority (0.42 vs 0.19). The Epistemic Market is anti-calibrated
at the system level.

### Root Cause: Attack Operator Crowding

Operator distribution in full_ree (dev):
| Operator | Selections | Share |
|---|---|---|
| attack_hypothesis | 2600 | 46% |
| retrieve | 1897 | 34% |
| generate_hypothesis | 650 | 12% |
| stop | 500 | 9% |

The attack operator's falsification_value bonus (0.4) dominates the market
after the first hypothesis. Attack is selected 46% of the time but produces
NO_OP results most of the time.

B1's fixed strategy avoids this by interleaving retrieve and generate_hypothesis.

## 10. Counterfactual Cognitive Action Study

2000 outcomes from 500 distinct epistemic source states.
Each state forked into 5 actions (retrieve, generate_hypothesis, attack, reason, stop).

### Mean Quality by Forced Action

| Action | hyp_ecology | false_majority | ignorance | stopping | duplication |
|---|---|---|---|---|---|
| retrieve | 0.225 | 0.196 | 0.306 | 0.443 | 0.407 |
| gen_hypothesis | 0.190 | 0.198 | 0.326 | 0.454 | 0.467 |
| attack | 0.200 | 0.213 | 0.317 | 0.478 | 0.495 |
| **reason** | **0.323** | **0.336** | **0.429** | **0.500** | 0.466 |
| stop | 0.145 | 0.211 | 0.260 | 0.279 | 0.304 |

**Reason is the best action across most families.** This is consistent with B1's
superiority — B1 always reasons about its hypotheses.

### Oracle Best Action Distribution
| Action | % Best |
|---|---|
| retrieve | 51.6% |
| stop | 19.2% |
| reason | 17.8% |
| generate_hypothesis | 8.4% |
| attack_hypothesis | 3.0% |

Retrieve dominates because most forked states are early (no evidence yet).

### Action Regret
| Action | Mean Regret |
|---|---|
| reason | 0.108 (lowest) |
| retrieve | 0.121 |
| gen_hypothesis | 0.151 |
| attack | 0.178 |
| stop | 0.196 (highest) |

### Bid-Value Correlation
**r = 0.1371** (Campaign V2) vs r = -0.083 (Campaign V1)

Improved from anti-calibrated to weakly positive. The semantic environment
makes bids slightly more predictive of realized value.

### Oracle-Realized Correlation
**r = 0.0312** — Oracle action values are nearly uncorrelated with
realized downstream quality. The oracle is a static function of the world
but realized quality depends on the continuation policy.

## 11. Action Prediction Study

### Leave-One-Family-Out Cross-Validation
| Policy | Accuracy | Mean Regret |
|---|---|---|
| always_retrieve (majority) | **51.6%** | 0.121 |
| **simple_rule** | **34.8%** | **0.133** |
| always_reason | 17.8% | 0.189 |
| always_stop | 19.2% | 0.196 |
| always_gen_hyp | 8.4% | 0.174 |

The simple rule (retrieve when no evidence, generate when no hypotheses,
reason when both exist) underperforms majority baseline but outperforms
most fixed-action policies.

### Feature Importance
| Feature | Correlation with rule accuracy |
|---|---|
| evidence_count | -0.162 |
| workspace_saturation | -0.145 |
| top_margin | -0.125 |
| step | -0.110 |
| budget_fraction | +0.110 |
| hypothesis_entropy | +0.064 |

Rich epistemic state features have weak but non-zero predictive power.

## 12. Scientific Hypothesis Verdicts

| Hypothesis | Verdict | Evidence | Effect |
|---|---|---|---|
| H-REE-01: Self-model > verbal confidence | **INCONCLUSIVE** | Self-model ablation is non-causal | No data |
| H-REE-02: Ignorance predicts failure | **PARTIALLY_SUPPORTED** | Small quality effect (-11%) | d ≈ 0.2 |
| H-REE-03: Sealed tribunal preserves minority | **INCONCLUSIVE** | Not implemented in benchmark | No data |
| H-REE-04: Ontology revision aids recovery | **INCONCLUSIVE** | Not implemented in benchmark | No data |
| H-REE-05: Hypothesis ecology reduces convergence | **SUPPORTED** | Massive effect (d ≈ 1.4) | 90% quality drop without |
| H-REE-06: Evidence independence resists inflation | **INCONCLUSIVE** | Not causally ablated | No data |
| H-REE-07: Counterfactual robustness/responsiveness | **INCONCLUSIVE** | Not implemented in benchmark | No data |
| H-REE-08: Memory consolidation aids transfer | **INCONCLUSIVE** | Not implemented in benchmark | No data |
| H-REE-09: Full REE > additive component sum | **NOT_SUPPORTED** | Full REE < B1 fixed strategy | Negative |
| H-REE-10: Adaptive scheduling improves efficiency | **NOT_SUPPORTED** | Market is anti-calibrated; round-robin matches/beats | Negative |

## 13. Negative Findings

1. **B1 fixed strategy (0.56) outperforms full adaptive REE (0.38)** on 4/5 families
2. **The Epistemic Market is anti-calibrated at the system level**: round-robin matches or beats heuristic selection
3. **DiversityAwareMarket does not help**: 0.33 vs 0.35 for heuristic
4. **Attack operator crowding**: 46% of all REE operations are attack_hypothesis, most producing NO_OP
5. **REE quality does not improve with additional budget** (plateaus at ~5500 tokens)
6. **Self-model, stopping, and market ablations remain non-causal** (identical behavior with or without)
7. **Oracle action values are nearly uncorrelated with realized quality** (r=0.03)
8. **Simple rule policy underperforms majority baseline** (34.8% vs 51.6%)
9. **Feature importance correlations are weak** (max |r| = 0.16)

## 14. Positive Findings

1. **Hypothesis ecology is causally critical**: removing it drops quality 90% (d ≈ 1.4)
2. **The semantic simulator is identifiable**: different strategies produce different qualities
3. **Reason is the most valuable cognitive action** across most families
4. **Bid-value correlation improved** from -0.083 (V1) to +0.137 (V2)
5. **Event-sourced state forking enables counterfactual policy evaluation** — methodological contribution
6. **Quality evaluation against latent world ground truth** is far more informative than substring matching

## 15. Minimal Effective Architecture (REE-Minimal-Empirical)

Based on ablation evidence, the smallest system retaining most benefit is:

```
EpistemicState
+ Hypothesis Ecology (causally verified, d ≈ 1.4)
+ Fixed Strategy: retrieve → gen_hyp → retrieve → gen_hyp → reason
```

The adaptive market, stopping policy, self-model, and ignorance mechanisms
do not contribute measurably to quality in this environment.

## 16. Task-Conditional Architecture Value

| Condition | Best Architecture | Why |
|---|---|---|
| Simple tasks (clear evidence) | B0_direct | Lower overhead |
| Multiple hypotheses needed | B1_reflection | Fixed strategy optimal |
| Source duplication | full_ree | Evidence tracking helps |
| General | B1_reflection | Best overall quality/cost |

REE only justifies its overhead when source provenance tracking matters.

## 17. Limitations

1. **Deterministic simulator**: No stochastic noise means zero variance across seeds for some families
2. **No model-in-the-loop**: All cognition is scripted, not LLM-generated
3. **5 families only**: Limited scenario diversity
4. **Small N**: 5-10 worlds per family per split
5. **No tribunal/ontology/memory**: Several REE mechanisms not in benchmark
6. **Self-model is non-causal**: Cannot test H-REE-01 under current architecture
7. **Continuation policy dominates counterfactual outcomes**: The forced first action matters less than the 10-step continuation

## 18. Claims We Are NOT Justified In Making

- "Direct prompting is universally better than REE" — B1 beats REE, not B0
- "Hypothesis ecology is sufficient" — it's necessary but doesn't match B1 alone
- "The Epistemic Market concept is flawed" — the implementation may be flawed but the concept is untested with calibrated bids
- "State features don't predict action value" — weak correlation may strengthen with more data and better features
- "REE can never improve" — the current heuristic market is a poor scheduler; a better one might change outcomes

## 19. Novel Contributions

### Strong
1. **Counterfactual cognitive policy evaluation** via event-sourced state forking
2. **EpistemicQualityVector**: structured quality evaluation against latent world
3. **Negative result**: adaptive heuristic scheduling can underperform fixed strategies

### Moderate
4. **Causal mechanism audit methodology**: distinguishing causal from scaffold ablations
5. **Attack-operator crowding phenomenon** as a failure mode of bid-based scheduling

### Weak
6. **EpistemicWorldSimulator** as a benchmark construction methodology

## 20. Next Research Directions

1. **Fix the market**: Use counterfactual data (r=0.14) to build a calibrated scheduler
2. **Integrate reasoning into REE**: The reason operator is consistently best but underselected
3. **Test with real LLMs**: Model-in-the-loop campaign with simulator ground truth
4. **Expand scenario families**: Ontology, memory, tribunal scenarios
5. **Make remaining ablations causal**: Self-model, stopping, evidence independence
6. **Larger N**: 50+ worlds per family for statistical power
7. **Learned scheduler**: With enough counterfactual data, train action-value predictor

## Appendix: Reproducibility

Campaign V1: SHA `120a576` (immutable negative baseline)
Campaign V2: SHA `23e0774`
Base seed: 7777
Python: 3.11+
Tests: 446 passed, 0 failed

All raw data in `experiments/campaign_v2/results/`:
- `all_records.jsonl` (1250 records)
- `counterfactual_v2.jsonl` (2000 outcomes)
- `market_comparison.json`
- `prediction_study_v2.json`
- `regret_analysis_v2.json`
- `dev_family_analysis.json`
- `dev_ablation_analysis.json`
- `dev_pareto_analysis.json`
- `validation_family_analysis.json`
- `locked_test_analysis.json`
