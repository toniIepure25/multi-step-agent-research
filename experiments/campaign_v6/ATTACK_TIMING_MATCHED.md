# V6 Matched-Budget Attack Timing Results

## Design

Three conditions using the SAME multiset of operations:
- Early: attack → retrieve → generate_hypothesis → reason → synthesis
- Mid: retrieve → generate_hypothesis → attack → reason → synthesis
- Late: retrieve → generate_hypothesis → reason → attack → synthesis

All conditions: 5 operations, 4 LLM calls, 1 retrieval.
Only attack position varies.

## Results (N = 32 worlds, gemma3:27b-it-qat)

| Condition | Mean Q | Std |
|-----------|--------|-----|
| Early attack | 0.700 | 0.000 |
| Mid attack | 0.719 | 0.050 |
| Late attack | 0.719 | 0.050 |
| **Range** | **0.019** | |

## Comparison with V5

| Metric | V5 (unmatched budget) | V6 (matched budget) |
|--------|----------------------|---------------------|
| Early attack | 0.000 (1 op, 308 tok) | 0.700 (5 ops, ~4 calls) |
| Late attack | 0.276 (6 ops, 1761 tok) | 0.719 (5 ops, ~4 calls) |
| Effect | +0.276 | +0.019 |
| Budget matched? | NO (5.7x difference) | YES |

## Interpretation

**H-REE-22 (Matched-Budget Attack Timing): NOT SUPPORTED**

Under matched-budget conditions, the attack-timing effect shrinks from
+0.276 to +0.019. The V5 effect was almost entirely driven by the
compute/information difference between conditions (1 op vs 6 ops),
not by the timing of attack within a fixed-length sequence.

The small remaining effect (+0.019) is directionally consistent with
later attack being slightly more useful, but is not significant and
is within noise.

## Scientific Conclusion

The original attack-timing finding was confounded with resource allocation.
When all conditions use the same operations and same budget, attack
position has negligible effect on downstream quality.

This invalidates the V5 claim that "attack/falsification has
state-dependent value." Under proper controls, it appears that
attack value depends on whether OTHER operations (gen_hyp, retrieve)
are present, not on attack timing per se.
