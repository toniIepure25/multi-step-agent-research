# Table 3: Pairwise Complementarity Matrix (V4, N = 56)

| First → Second | Complementarity | Quality | Relation | State-Dep. |
|----------------|----------------|---------|----------|------------|
| gen_hyp → retrieve | **+0.162** | 0.323 | Synergy | Yes |
| gen_hyp → attack | **+0.137** | 0.273 | Synergy | Yes |
| gen_hyp → reason | **+0.137** | 0.273 | Synergy | Yes |
| attack → gen_hyp | **+0.137** | 0.273 | Synergy | Yes |
| reason → gen_hyp | **+0.137** | 0.273 | Synergy | Yes |
| retrieve → gen_hyp | +0.078 | 0.240 | Synergy | Yes |
| retrieve → attack | +0.025 | 0.050 | Redundancy | No |
| retrieve → reason | +0.025 | 0.050 | Redundancy | No |
| attack → retrieve | +0.025 | 0.050 | Redundancy | No |
| reason → retrieve | +0.025 | 0.050 | Redundancy | No |
| retrieve → retrieve | −0.002 | 0.048 | Redundancy | Yes |
| gen_hyp → gen_hyp | **−0.050** | 0.223 | Interference | Yes |
| attack → attack | 0.000 | 0.000 | Redundancy | No |
| attack → reason | 0.000 | 0.000 | Redundancy | No |
| reason → attack | 0.000 | 0.000 | Redundancy | No |
| reason → reason | 0.000 | 0.000 | Redundancy | No |

*Complementarity = Q(pair) − mean(Q(op_1 alone), Q(op_2 alone)). Synergy: pair exceeds additive prediction. Interference: pair underperforms additive prediction. Source: `campaign_v4/results/complementarity_matrix.json`.*

**Key pattern:** Hypothesis generation is the catalytic operation. Every pair involving gen_hyp shows synergy; pairs without it show redundancy or interference.
