# SD-H9C Protocol — Complexity-Conditional Active Control

## Date: 2026-08-14
## Status: NEW/PROSPECTIVE — motivated by Stage 3C heterogeneity, NOT preregistered

---

## Research Question (Reformulated)
> Does the advantage of discrimination-oriented experiment selection over confirmation
> seeking increase with hypothesis-space ambiguity/complexity?

## Motivation
Stage 3C observed:
- multi_hypothesis_branch: +0.150 discrimination advantage
- simple worlds: ~0 advantage

This suggested complexity moderates the effect. Stage 3D tested this formally.

---

## Complexity Measure (EX ANTE, from world structure)

```
Complexity = prior_entropy × (1 - max_pairwise_divergence) × (n_hypotheses / 3)
```

Components:
- `prior_entropy`: Shannon entropy of belief distribution (higher = more uncertain)
- `max_pairwise_divergence`: maximum JSD between any two hypothesis predictions
  (lower max divergence = harder to distinguish = more ambiguous)
- `n_hypotheses / 3`: normalized hypothesis count

**All computed from world structure. No policy outcomes used.**

---

## Results (N=150 distributional worlds)

### Overall
- Discrimination recovery: 0.717
- Confirmation recovery: 0.641
- Mean advantage: +0.076 (discrimination better overall)

### By Complexity Tercile
| Tercile | N | Advantage |
|---------|---|-----------|
| LOW | 50 | +0.100 |
| MID | 50 | +0.044 |
| HIGH | 50 | +0.084 |

### Regression: Advantage ~ Complexity
- Slope: -0.013
- 95% CI: [-0.060, +0.034]
- r = -0.045
- p = 0.587

---

## Verdict: NOT_SUPPORTED

The discrimination advantage does NOT increase with hypothesis-space complexity.
The advantage exists broadly (+0.076 overall) but is not moderated by our complexity
measure.

---

## Interpretation
1. The Stage 3C multi_hypothesis_branch finding was world-specific, not generalizable
2. Discrimination helps broadly but the WHEN question remains open
3. The complexity measure may not capture the relevant dimension
4. Alternative: discrimination may matter more for SEQUENTIAL problems (horizon > 1)

---

## Implications for SD-H9B
SD-H9B (discrimination > confirmation) is PARTIALLY_SUPPORTED:
- +0.076 on distributional worlds (meaningful but modest)
- +0.017 on locked active worlds (CI crosses zero)
- The effect exists but is not large or reliable enough for strong claims
