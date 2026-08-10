# V4 Benchmark Identifiability

## Does the V4 benchmark distinguish strategies?

### Gate 1: Different regimes produce different optimal sequences

| Regime | Oracle-Best | Different from B1_extended? |
|---|---|---|
| A (exploration deficit) | explore_first | YES |
| B (evidence deficit) | B1_extended | no |
| C (discrimination deficit) | full_explore | YES |
| D (integration deficit) | B1_extended | no |
| E (misleading evidence) | mixed | PARTIALLY |
| F (hidden alternative) | B1_extended | no |
| G (source dependency) | mixed | PARTIALLY |
| H (low resolvability) | B1_extended | no |

**Result**: 2 regimes have strictly different optimal strategies, 2 are mixed.
**PASS** (though margin is modest).

### Gate 2: Quality variance across strategies

| Strategy | Mean | Std | Min | Max |
|---|---|---|---|---|
| B1_extended | 0.527 | — | — | — |
| full_explore | 0.518 | — | — | — |
| explore_first | 0.379 | — | — | — |
| evidence_heavy | 0.048 | — | — | — |

Spread from best (0.527) to worst (0.048) is 10x. **PASS**.

### Gate 3: Oracle exceeds best fixed

AdaptivityGap = 0.096 > 0.05. **PASS**.

### Gate 4: Single-operation values differ

| Operation | Value |
|---|---|
| gen_hyp | 0.273 |
| retrieve | 0.050 |
| attack | 0.000 |
| reason | 0.000 |

Clear differentiation. **PASS**.

### Gate 5: Complementarity is non-zero

gen_hyp -> retrieve = +0.162. **PASS**.

## Overall: V4 benchmark is identifiable

5/5 identifiability gates pass. The benchmark distinguishes cognitive
strategies across heterogeneous epistemic regimes.

## Comparison with V3

V3 identifiability was established on 5 homogeneous families. V4 extends
this to 8 heterogeneous regimes where different strategies are genuinely
optimal, creating a more demanding and informative benchmark.
