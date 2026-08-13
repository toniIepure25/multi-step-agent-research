# Final Negative Findings

## What Did NOT Survive Validation

| Finding | Original Campaign | Validation Status | Why It Failed |
|---------|------------------|-------------------|---------------|
| Temporal complementarity (gen_hyp + reason interaction) | V3-V4 | NOT SUPPORTED | Compute-matched factorial eliminated the interaction (V6, effect = 0.000) |
| Attack timing advantage | V3-V5 | NOT SUPPORTED | Effect reduced to 0.019 under matched budget controls (V6) |
| Hypothesis-specific retrieval advantage | V5 (implied) | NOT SUPPORTED | Generic query expansion matches or exceeds hypothesis-conditioned retrieval (PV-H2, 0/4 cells favor Real) |
| Adaptive motif control | V4 | NOT SUPPORTED | Motif-based policy failed in controlled evaluation |
| Sequence superiority over primitives | V3-V4 | WEAKENED | May reflect main effects rather than sequence-specific interactions |
| Direct hypothesis anchoring as SciFact failure cause | V6 | NOT SUPPORTED | Artifact visibility ablation non-significant after Holm correction (PV-H5) |

## Role in Paper

These falsifications are NOT weaknesses. They are methodological motivations:

> "Initial simulator experiments suggested temporal complementarity and hypothesis-specific retrieval advantages. Compute-matched factorial controls and generic expansion baselines eliminated these effects, motivating the final causal audit design that revealed the retrieval–reasoning dissociation as the central finding."

This narrative positions the negative results as evidence of methodological rigor, not exploratory failure.

## Compact Main-Text Box

### What did NOT survive controlled validation?

- **Temporal complementarity:** Factorial interaction = 0 under compute matching
- **Attack timing advantage:** Effect = 0.019 under matched budgets
- **Hypothesis-specific retrieval:** Generic expansion matches or exceeds
- **Hypothesis anchoring (SciFact):** Non-significant after Holm correction

*These falsifications motivated the final preregistered causal audit.*
