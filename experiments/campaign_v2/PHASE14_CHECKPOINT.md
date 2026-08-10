# Phase 14 Checkpoint — Causal Mechanism Certification & Semantic Benchmark Rebuild

```
PHASE: 14
STATUS: COMPLETE

STARTING SHA: 120a576
ENDING SHA: (to be committed)
BRANCH: feature/asar-ree-v2

TESTS: 446 passed, 1 skipped, 0 failed
```

## Architecture Changes

1. **EpistemicWorldSimulator** (`asar/evaluation/simulator.py`):
   - Deterministic latent world with hidden hypotheses, causal graph, evidence, sources
   - Cognitive operations return results dependent on world + agent state
   - Oracle action values computable as evaluation-only metrics
   - EpistemicQualityVector: 10-dimensional structured scoring

2. **Semantic Scenario Generators** (`asar/evaluation/scenarios/semantic_generators.py`):
   - 5 families: hypothesis_ecology, false_majority, ignorance_discovery, stopping_quality, source_duplication
   - Each with deterministic information structure favoring different cognitive strategies
   - dev/validation/locked_test splits with fresh seeds (base_seed=7777)

3. **SemanticBenchmarkRunner** (`asar/evaluation/semantic_runner.py`):
   - True causal ablation: hypothesis_ecology, ignorance_ledger flags remove operators
   - True causal ablation: self_model flag switches to neutral prior (1.0)
   - True causal ablation: stopping_policy flag disables StoppingPolicy
   - B0_direct and B1_reflection baselines integrated

4. **Campaign V1 preserved** (`experiments/campaign_v1/PROVENANCE.md`):
   - SHA 120a576 frozen
   - Results not overwritten

## Data Splits

| Split | Worlds | Hash | Usage |
|-------|--------|------|-------|
| dev | 50 | 6d835082c9db3ed0 | Tuning, development |
| validation | 25 | a22d9de26318686a | Validation |
| locked_test | 25 | 5f571ff5eac1bf7f | Final confirmatory |

## Campaign V2 Results (Dev, N=1250)

### Holdout Quality (5k budget)

| Family | B0_direct | B1_reflection | full_ree |
|--------|-----------|---------------|----------|
| hyp_ecology | 0.080 | **0.700** | 0.130 |
| false_majority | 0.316 | **0.484** | 0.366 |
| ignorance | 0.475 | **0.700** | 0.528 |
| stopping | 0.050 | **0.700** | 0.433 |
| duplication | **0.478** | 0.228 | 0.433 |

**Critical finding: B1_reflection outperforms full_ree on 4 of 5 families.**

### Ablation Impact

| Config | Quality | Hypotheses | Ignorance |
|--------|---------|------------|-----------|
| full_ree (all ON) | 0.3645 | 2.0 | 0.2 |
| no_hypothesis | **0.0371** | 0.0 | 0.0 |
| no_ignorance | 0.3246 | 2.0 | 0.0 |
| no_self_model | 0.3645 | 2.0 | 0.2 |
| no_stopping | 0.3645 | 2.0 | 0.2 |
| no_market | 0.3645 | 2.0 | 0.2 |
| no_hyp_no_ign | **0.0371** | 0.0 | 0.0 |

**Causal ablation verified**: hypothesis_ecology has massive effect (d≈1.4).
**Non-causal findings**: self_model, stopping_policy, epistemic_market produce identical behavior.

### Pareto Analysis

B0_direct: 0.2797 quality at 1000 tokens (budget-independent)
B1_reflection: 0.5623 quality at 2000 tokens (budget-independent)
full_ree: 0.3778 quality at 2000-5500 tokens (budget-sensitive)

**B1 Pareto-dominates full_ree**: higher quality, lower cost.

## Identifiability Gate (14.11)

1. ✅ random policy < sensible fixed policy (oracle > random on hypothesis_ecology)
2. ✅ sensible fixed < oracle (quality variance across strategies confirmed)
3. ✅ different cognitive operations have different oracle values
4. ✅ 5/5 families show quality variance between B0 and full_ree
5. ✅ hypothesis_ecology and ignorance_ledger are true runtime interventions
6. ⚠️ B4 and Full REE not distinguishable (self_model/market ablation has no effect)
7. ⚠️ self_model ON/OFF does not affect action choice with default parameters

## Negative Findings

1. B1_reflection beats full_ree because B1 uses a fixed strategy that happens to align
   well with the scenario generators (retrieve → generate × 2 → reason)
2. REE's heuristic bid-based selection overweights retrieve relative to hypothesis generation
3. self_model, stopping_policy, and market ablation are still effectively non-causal
   because the controller defaults mask the intervention
4. full_ree quality is budget-sensitive but plateaus at ~5500 tokens without improvement

## GO/NO-GO

- ✅ Environment is semantically identifiable (quality varies by strategy)
- ✅ hypothesis_ecology ablation is causal and large
- ⚠️ Need to diagnose why REE < B1 (Phase 15)
- ⚠️ Need to make remaining ablations causal (Phase 15)

## Next Phase: 15 — Empirical Metacognitive Calibration
