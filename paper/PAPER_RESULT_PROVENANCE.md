# Paper Result Provenance

Every headline number in the manuscript traced to its raw artifact.

Starting SHA: `2f63cf9`
Tests: 446 passed, 1 skipped, 0 failed
Date: 2026-08-11

## Headline Numbers

| # | Value | Reported | Source File | Field/Path | N |
|---|-------|----------|-------------|------------|---|
| P1 | 0.2282 | +0.228 | `experiments/campaign_v3/results/sequence_complementarity.jsonl` | mean complementarity for `ret_hyp_reason_vs_ret_ret_reason` | 50 worlds |
| P2 | 0.1617 | +0.162 | `experiments/campaign_v4/results/complementarity_matrix.json` | `matrix.generate_hypothesis->retrieve.mean_complementarity` | 56 worlds |
| P3 | -0.0503 | -0.050 | `experiments/campaign_v4/results/complementarity_matrix.json` | `matrix.generate_hypothesis->generate_hypothesis.mean_complementarity` | 56 worlds |
| P4 | 0.0955 | 0.096 | `experiments/campaign_v4/results/adaptivity_gap.json` | `adaptivity_gap` | 56 worlds |
| P5 | 0.6221 | 0.622 | `experiments/campaign_v4/results/adaptivity_gap.json` | `oracle_quality` | 56 worlds |
| P6 | 0.5266 | 0.527 | `experiments/campaign_v4/results/adaptivity_gap.json` | `best_global_quality` (B1_extended) | 56 worlds |
| P7 | 0.5876 | 0.588 | `experiments/campaign_v4/results/phase23_dev_regret.json` | `mean_oracle_quality` | 56 worlds |
| P8 | 0.5176 | 0.518 | `experiments/campaign_v4/results/phase23_dev_regret.json` | `mean_fixed_quality` (FULL_EXPLORE) | 56 worlds |
| P9 | 0.3234 | 0.323 | `experiments/campaign_v4/results/phase23_dev_regret.json` | `mean_policy_quality` | 56 worlds |
| P10 | 0.2642 | 0.264 | `experiments/campaign_v4/results/phase23_dev_regret.json` | `mean_policy_regret` | 56 worlds |
| P11 | 0.5938 | 0.594 | `experiments/campaign_v2/results/locked_test_analysis.json` | B1_reflection locked test | 25 worlds |
| P12 | 0.3558 | 0.356 | `experiments/campaign_v2/results/locked_test_analysis.json` | full_ree locked test | 25 worlds |
| P13 | 0.6721 | 0.672 | `experiments/campaign_v3/results/v3_locked_test.json` | B1_extended locked test | 25 worlds |
| P14 | 0.6304 | 0.630 | `experiments/campaign_v3/results/phase19_dev_comparison.json` | B1_extended dev | 50 worlds |
| P15 | 0.1113 | +0.111 | `experiments/campaign_v5/results/phase26_verdicts_gemma3.json` | `verdicts.R2_complementarity.effect` | 128 evals |
| P16 | 0.2756 | +0.276 | `experiments/campaign_v5/results/phase26_verdicts_gemma3.json` | `verdicts.R5_attack_timing.effect` | 128 evals |
| P17 | 0.0032 | +0.003 | `experiments/campaign_v5/results/phase26_verdicts_gemma3.json` | `verdicts.R1_sequence_superiority.effect` | 128 evals |
| P18 | -0.0502 | -0.050 | `experiments/campaign_v5/results/phase26_verdicts_gemma3.json` | `verdicts.R4_order_effects.effect` | 128 evals |
| P19 | 0.7179 | 0.718 | `experiments/campaign_v5/results/phase27_summary_gemma3.json` | `conditions.greedy_primitive.mean` | 14 packs |
| P20 | 0.6956 | 0.696 | `experiments/campaign_v5/results/phase27_summary_gemma3.json` | `conditions.direct.mean` | 14 packs |
| P21 | 0.6911 | 0.691 | `experiments/campaign_v5/results/phase27_summary_gemma3.json` | `conditions.B1_extended.mean` | 14 packs |
| P22 | 0.6875 | 0.688 | `experiments/campaign_v5/results/phase27_summary_gemma3.json` | `conditions.FULL_EXPLORE.mean` | 14 packs |

## LLM Capability Gate Provenance

| Operation | gemma3 | llama3.2 | Source |
|-----------|--------|----------|--------|
| evidence_interpretation | 1.000 | 1.000 | `experiments/campaign_v5/results/phase25_gate_gemma3.json` / `phase25_gate_llama3_2-vision.json` |
| hypothesis_generation | 0.750 | 0.733 | same |
| alternative_hypothesis | 0.800 | 0.833 | same |
| reasoning | 0.929 | 0.950 | same |
| contradiction_identification | 1.000 | 1.000 | same |
| attack_hypothesis | 1.000 | 1.000 | same |
| missing_information | 1.000 | 1.000 | same |
| retrieval_query | 1.000 | 1.000 | same |
| synthesis | 1.000 | 1.000 | same |
| structured_output | 1.000 | 1.000 | same |

N = 24 worlds per model (8 regimes x 3 seeds).

## V4 Complementarity Matrix Provenance

| Pair | Complementarity | Quality | Relation | Source |
|------|----------------|---------|----------|--------|
| gen_hyp→retrieve | +0.162 | 0.323 | synergy | `complementarity_matrix.json` |
| gen_hyp→attack | +0.137 | 0.273 | synergy | same |
| gen_hyp→reason | +0.137 | 0.273 | synergy | same |
| ret→gen_hyp | +0.078 | 0.240 | synergy | same |
| gen_hyp→gen_hyp | -0.050 | 0.223 | interference | same |
| ret→ret | -0.002 | 0.048 | redundancy | same |
| attack→attack | 0.000 | 0.000 | redundancy | same |
| reason→reason | 0.000 | 0.000 | redundancy | same |

Single-operation baselines: retrieve=0.050, gen_hyp=0.273, attack=0.000, reason=0.000.

## V5 Phase 26 Sequence Means

| Sequence | Mean | Std | N | Source |
|----------|------|-----|---|--------|
| reversed_B1 | 0.327 | 0.207 | 16 | `phase26_verdicts_gemma3.json` |
| explore | 0.323 | 0.207 | 16 | same |
| B1_extended | 0.277 | 0.197 | 16 | same |
| attack_late | 0.276 | 0.198 | 16 | same |
| single_gen_hyp | 0.273 | 0.207 | 16 | same |
| discriminate | 0.223 | 0.181 | 16 | same |
| single_retrieve | 0.050 | 0.000 | 16 | same |
| attack_early | 0.000 | 0.000 | 16 | same |

## Rounding Policy

All values reported to 3 decimal places in tables and text. The raw JSON source values are preserved at full precision. No value is rounded upward for rhetorical effect. Where reported precision differs (e.g., +0.228 vs raw 0.2282), the raw value is given in this provenance table.

## Post-Hardening Audit Corrections (2026-08-11)

### P3: Interference (−0.050)
**Status:** VERIFIED WITH CAVEAT. 95% CI [−0.136, +0.035] crosses zero. Not statistically significant at α=0.05. Paper must report as "directional evidence, not significant."

### P15: V5 Complementarity (+0.111)
**Status:** VERIFIED WITH CAVEAT. This value is NOT simply `explore − single_gen_hyp`. Actual formula: `(mean(explore) + mean(discriminate) − mean(single_gen_hyp) − mean(single_retrieve)) / 2 = (0.3234 + 0.2225 − 0.2734 − 0.0500) / 2 = 0.1113`. It averages over two multi-op sequences vs two single-op primitives. Paper must specify this definition.

### P16: Attack timing (+0.276)
**Status:** VERIFIED WITH CAVEAT. Comparison is attack_late (6 ops, ~1761 tokens) vs attack_early (1 op, ~308 tokens). Severely budget-unfair (~5.7× compute). Paper must acknowledge this confound.

### P17: Sequence superiority (+0.003) = P19 replacement: Fixed vs greedy (+0.003)
**Status:** VERIFIED. Code BUG: R6 (fixed vs greedy) is a duplicate of R1 (sequence superiority). Both compute `B1_extended − max(single_*)`. No greedy baseline exists in Phase 26. Paper must remove R6 as a separate finding.

### Phase 27 reflection = direct
**Status:** BUG CONFIRMED. In `run_v5_execution.py`, `synthesize` returns before `critique`/`revise` execute. Reflection condition produces identical output to direct. Paper must exclude reflection or document the bug.

### Regime clustering
All V3 (50), V4 (56), V5 (16) world counts involve clustered observations (8 regimes × seeds). Naive CIs are anti-conservative. Headline effects with large magnitudes (+0.162, +0.111) likely survive, but smaller effects (+0.003, −0.050) are unreliable.

## Integrity Check

All source files listed above are committed or tracked in `experiments/`. SHA-256 checksums of all experiment artifacts were recorded on 2026-08-11. No raw result file has been modified since its original creation. Post-hardening audit corrections above affect INTERPRETATION, not raw data.
