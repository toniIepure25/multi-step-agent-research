# Dataset Release

## Overview

The dataset contains trajectories from controlled cognitive-sequence experiments across five campaign phases. Each record captures the epistemic state, cognitive sequence applied, realized quality gain, and evaluator metadata.

## Schema

### Agent-Visible Fields (Safe to Release)

```json
{
  "world_id": "regime_b_271828_0",
  "regime": "B",
  "seed": 271828,
  "split": "dev",
  "sequence_name": "B1_extended",
  "sequence": ["retrieve", "gen_hyp", "retrieve", "gen_hyp", "reason", "retrieve", "reason"],
  "token_budget": 3500,
  "tokens_used": 2104,
  "n_evidence_retrieved": 4,
  "n_hypotheses_generated": 2,
  "n_operations": 7,
  "realized_quality": 0.700,
  "quality_components": {
    "hypothesis_correctness": 0.800,
    "evidence_coverage": 0.600,
    "calibration": 0.700
  }
}
```

### Evaluator-Only Fields (Separate File, for Benchmark Operators Only)

```json
{
  "world_id": "regime_b_271828_0",
  "true_hypothesis_id": "h_3",
  "n_latent_hypotheses": 5,
  "evidence_structure": "independent",
  "deception_level": "none",
  "oracle_sequence": "B1_extended",
  "oracle_quality": 0.700,
  "causal_edges": [["e_1", "h_3", 0.9], ["e_2", "h_1", 0.3]]
}
```

**SEPARATION IS CRITICAL.** Agent-visible data must never include true hypothesis, oracle sequence, or causal structure. This separation preserves the benchmark's validity for future evaluation.

## Dataset Statistics

| Campaign | Worlds | Sequences/World | Total Records | Source |
|----------|--------|-----------------|---------------|--------|
| V2 | 25 (locked) | 3 conditions | ~75 | `campaign_v2/results/` |
| V3 | 100 (dev+val+locked) | 4+ conditions | ~600 | `campaign_v3/results/` |
| V4 | 56 (dev) + 40 (locked) | 9 sequences | ~864 | `campaign_v4/results/` |
| V5 Phase 26 | 16 | 8 sequences × 2 models | 256 | `campaign_v5/results/phase26_*.jsonl` |
| V5 Phase 27 | 14 packs | 5 conditions | 70 | `campaign_v5/results/phase27_*.jsonl` |

## Complementarity Dataset

Derived from the trajectory data, the complementarity dataset provides pairwise operation-value measurements:

```json
{
  "first_op": "generate_hypothesis",
  "second_op": "retrieve",
  "world_id": "regime_b_271828_0",
  "pair_quality": 0.323,
  "first_standalone": 0.273,
  "second_standalone": 0.050,
  "additive_baseline": 0.162,
  "complementarity": 0.162,
  "relation": "synergy",
  "regime": "B"
}
```

## Access

Raw result artifacts are in `experiments/campaign_*/results/`. The dataset can be regenerated from committed code and configuration using the reproduction scripts.

## License

Dataset released under the same license as the repository.

## Citation

If you use this dataset, please cite the accompanying paper.
