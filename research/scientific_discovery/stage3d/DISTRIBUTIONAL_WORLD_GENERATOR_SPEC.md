# Distributional World Generator Specification

## Date: 2026-08-14
## Purpose: Replace hand-authored worlds with parametric generation

---

## Motivation
Hand-authored worlds created inadvertent ceiling effects:
- Stage 3C hardened worlds: 80% JSD-Oracle agreement (too easy)
- Distributional worlds: 73% agreement (healthier benchmark)
- 14% of generated worlds have genuinely hard oracle margins

---

## Generator Architecture

```
WorldGeneratorConfig (frozen hyperparameters)
    → generate_world(seed, config)
        → ExperimentWorld + GeneratedWorldMetadata
```

### Hyperparameters (frozen before evaluation)

| Parameter | Range | Description |
|-----------|-------|-------------|
| n_hypotheses | [3, 8] | Number of competing hypotheses |
| n_experiments | [3, 10] | Number of candidate experiments |
| n_outcomes | [2, 4] | Possible outcomes per experiment |
| prior_concentration | 1.0 | Dirichlet parameter (lower = more skewed priors) |
| prediction_noise | 0.1-0.15 | Gaussian noise on prediction likelihoods |
| overlap_range | [0.1, 0.8] | How much hypotheses agree in predictions |
| cost_range | [0.5, 3.0] | Experiment cost |

---

## Validation Rules

A generated world is VALID if:
- Prediction likelihoods sum to [0.5, 2.0] per hypothesis per experiment
- No duplicate hypothesis IDs
- At least one experiment exists
- True hypothesis is in the belief set
- At least one experiment has non-degenerate predictions

A world is NOT rejected because:
- Confirmation wins
- JSD loses
- Effect is small
- Oracle margin is tiny

---

## Metadata (evaluator-side only)

Each world produces diagnostic metadata:
- `prior_entropy`: Shannon entropy of initial beliefs
- `min_pairwise_divergence`: lowest JSD between any hypothesis pair
- `max_pairwise_divergence`: highest JSD between any hypothesis pair
- `oracle_action_margin`: Value(best) - Value(second_best)
- `jsd_oracle_agreement`: boolean — does JSD pick same experiment as oracle?
- `difficulty_score`: composite (higher = harder)

---

## Difficulty Classification

| Stratum | Criterion | Expected Rate |
|---------|-----------|---------------|
| EASY | oracle_margin > 0.10 | ~40% |
| MEDIUM | 0.01 < oracle_margin <= 0.10 | ~45% |
| HARD | oracle_margin <= 0.01 | ~15% |

---

## Implementation
File: `asar/scientific_discovery/world_generator.py`
Tests: `tests/scientific_discovery/test_stage3d.py::TestDistributionalWorldGenerator`
