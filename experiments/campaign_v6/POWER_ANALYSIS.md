# V6 Power Analysis

## Simulator Experiments (Factorial, Attack Timing)

### Effect size estimates from V4

| Effect | V4 Point | V4 Std | Cohen's d |
|--------|---------|--------|-----------|
| gen_hyp→retrieve complementarity | +0.162 | 0.101 | 1.60 |
| gen_hyp→gen_hyp interference | −0.050 | 0.327 | 0.15 |
| gen_hyp→attack complementarity | +0.137 | ~0.15 | ~0.91 |
| Adaptivity gap | +0.096 | ~0.12 | ~0.80 |

### SESOI

Preregistered SESOI for H-REE-19: **0.05** on the 0-1 quality scale.

### Required N for Factorial Interaction

For a paired design with SESOI = 0.05:

Assuming interaction effect std ≈ 0.15 (conservative from V4 pair-level variance):

```
d = SESOI / std = 0.05 / 0.15 = 0.33
```

For 80% power with α = 0.0125 (Holm-corrected across 4 primary tests):

```
N ≈ (z_α/2 + z_β)² / d² ≈ (2.50 + 0.84)² / 0.33² ≈ 103
```

### Available N

V6 design: 8 regimes × 4 seeds = **32 worlds**

32 < 103 → **underpowered** for SESOI = 0.05 with conservative variance.

**At N=32:**
- MDE at 80% power ≈ 0.05 × √(103/32) ≈ 0.09

### Recommendation

- With N=32 simulator worlds, MDE ≈ 0.09.
- V4 gen_hyp→retrieve effect (+0.162) would be detectable.
- Smaller effects (interference at -0.05) would NOT be detectable.
- Increase to 8 seeds per regime (N=64) if compute permits.
- Document power limitation for all analyses.

## External Dataset Experiments (H-REE-23)

### SciFact

Available claims: ~1,400 in test set.

Using 200 LOCKED claims: well-powered for effects ≥ 0.05 accuracy difference.

### HotpotQA

Available questions: ~7,000+ in dev set.

Using 200 LOCKED questions: well-powered for effects ≥ 0.04 F1 difference.

### Power for External Transfer

External effects are expected to be SMALLER than simulator effects.

SESOI for H-REE-23: **dataset-specific** (set after DEV phase).

With N=200:
- MDE ≈ 0.04 for accuracy differences (assuming std ≈ 0.3)
- Sufficient for meaningful effects

## Summary

| Hypothesis | N Available | MDE (80% power) | Powered for SESOI? |
|-----------|------------|------------------|-------------------|
| H-REE-19 (factorial) | 32 | 0.09 | Marginal |
| H-REE-20 (intervention) | 32 | 0.09 | Marginal |
| H-REE-21 (causality) | 32 | qualitative | Yes (binary test) |
| H-REE-22 (attack timing) | 32 | 0.09 | Marginal |
| H-REE-23 (SciFact) | 200 | 0.04 | Yes |
| H-REE-23 (HotpotQA) | 200 | 0.04 | Yes |
