# Statistical Independence Audit

## Critical Findings

### 1. True Experimental Units

| Analysis | Claimed Unit | True Unit | Issue |
|----------|-------------|-----------|-------|
| V3 complementarity (+0.228) | World (N=50) | World, but clustered by family | Anti-conservative CIs |
| V4 complementarity (+0.162) | World (N=56) | World, clustered by regime (8 groups × 7) | Regime clustering |
| V5 Phase 26 replication | World (N=16) | World, clustered by regime (8 groups × 2) | Severe clustering; effective N < 16 |
| V5 Phase 27 real evidence | Pack (N=14) | Pack, but within-pack conditions are repeated measures | Conditions not independent across packs |

### 2. Pseudoreplication Assessment

**Phase 26 (V5):** 16 worlds = 8 regimes × 2 seeds. Within each regime, the two worlds share the same generator parameters. Treating all 16 as independent overestimates statistical power. Effective independent N is closer to 8 (regimes).

**Phase 27 (V5):** 14 packs × 5 conditions = 70 observations, but conditions within a pack are correlated (same evidence, same LLM, same ground truth). Proper analysis requires paired/repeated-measures design.

### 3. Confidence Intervals

| # | Effect | Point Est. | 95% CI (naive) | CI excludes 0? | Clustering adjustment needed? |
|---|--------|-----------|---------------|---------------|------|
| 1 | V3 +0.228 | +0.228 | [+0.187, +0.270] | Yes | Yes (family) |
| 2 | V4 +0.162 | +0.162 | [+0.135, +0.188] | Yes | Yes (regime) |
| 3 | V4 −0.050 | −0.050 | [−0.136, +0.035] | **No** | Yes (regime) |
| 5 | V5 +0.111 | +0.111 | [+0.067, +0.156] | Yes | Yes (regime) |
| 6 | V5 +0.276 | +0.276 | [+0.179, +0.373] | Yes | Yes (regime) |
| 7 | V5 +0.003 | +0.003 | [−0.160, +0.166] | **No** | Yes |
| 8 | V5 −0.050 | −0.050 | [−0.128, +0.028] | **No** | Yes |

### 4. Paper Implications

- **gen_hyp→gen_hyp interference (−0.050):** CI crosses zero. Cannot be claimed as "established interference" — must be "directional evidence of interference, not statistically significant at α=0.05."
- **Phase 26 replications:** Only effects with large magnitudes (+0.111, +0.276) survive naive CI; smaller effects (+0.003, −0.050) do not.
- **Clustering correction would widen CIs** for all estimates. The two effects that survive naive CIs (+0.162, +0.111) likely survive clustering too, but this should be stated.

### 5. Recommended Treatment for Paper

1. Report naive CIs but acknowledge regime clustering as a limitation.
2. Downgrade interference (−0.050) from "established" to "directional."
3. Present Phase 26 N=16 prominently; do not bury sample size.
4. For Phase 27, use paired comparisons (condition differences within-pack) rather than unpaired condition means.
