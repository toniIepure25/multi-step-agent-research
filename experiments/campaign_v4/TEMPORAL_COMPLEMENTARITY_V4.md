# Temporal Complementarity — V4 Heterogeneous Regimes (Phase 21.8)

## Single Operation Values (V4 Dev, N=56)

| Operation | Mean Quality |
|---|---|
| generate_hypothesis | 0.2734 |
| retrieve | 0.0500 |
| attack_hypothesis | 0.0000 |
| reason | 0.0000 |

## Complementarity Matrix

| Pair | Quality | Complementarity | Relation | State-Dep |
|---|---|---|---|---|
| gen_hyp -> retrieve | 0.3234 | +0.162 | **synergy** | YES |
| gen_hyp -> attack | 0.2734 | +0.137 | **synergy** | YES |
| gen_hyp -> reason | 0.2734 | +0.137 | **synergy** | YES |
| attack -> gen_hyp | 0.2734 | +0.137 | **synergy** | YES |
| reason -> gen_hyp | 0.2734 | +0.137 | **synergy** | YES |
| retrieve -> gen_hyp | 0.2401 | +0.078 | **synergy** | YES |
| gen_hyp -> gen_hyp | 0.2231 | -0.050 | interference | YES |
| retrieve -> attack | 0.0500 | +0.025 | redundancy | no |
| retrieve -> reason | 0.0500 | +0.025 | redundancy | no |
| retrieve -> retrieve | 0.0482 | -0.002 | redundancy | YES |
| attack -> attack | 0.0000 | 0.000 | redundancy | no |
| attack -> reason | 0.0000 | 0.000 | redundancy | no |
| reason -> reason | 0.0000 | 0.000 | redundancy | no |

## Key Findings

### 1. generate_hypothesis is the synergy hub

Every pair involving gen_hyp shows synergy. Gen_hyp transforms empty
states into states where other operations become productive.

### 2. gen_hyp -> gen_hyp shows INTERFERENCE (-0.050)

Repeated hypothesis generation is mildly harmful — a second hypothesis
generation from the same state produces a less useful hypothesis than
using that budget for retrieval or reasoning.

### 3. Operations without hypotheses are nearly worthless

retrieve alone = 0.050, attack alone = 0.000, reason alone = 0.000.
None of these produce quality without hypotheses to evaluate.

### 4. Complementarity is state-dependent

All synergistic pairs are marked state-dependent: their complementarity
varies across the 8 regime types. gen_hyp->retrieve is strongly
synergistic in Regime A (exploration deficit) but less so in Regime D
(integration deficit) where hypotheses already exist.

## Comparison with V3

| Metric | V3 (5 families) | V4 (8 regimes) |
|---|---|---|
| gen_hyp + reason complementarity | +0.228 | +0.137 |
| gen_hyp -> retrieve complementarity | +0.188 | +0.162 |
| gen_hyp -> gen_hyp | not measured | -0.050 (interference) |
| State dependence | noted | confirmed across regimes |

The V4 complementarity values are lower than V3 because the V4 regimes
include states (D, H) where hypothesis generation has less marginal value.
The direction of effects replicates.
