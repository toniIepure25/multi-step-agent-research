# Adaptivity Gap Results (Phase 21.2-21.6)

## Global Sequence Ranking (V4 Dev, N=56)

| Sequence | Mean Quality |
|---|---|
| B1_extended | 0.5266 |
| full_explore | 0.5176 |
| B1_full | 0.4350 |
| discriminate | 0.4350 |
| atk_late | 0.4350 |
| explore_first | 0.3792 |
| attack_then_reason | 0.2579 |
| integrate_only | 0.2579 |
| evidence_heavy | 0.0479 |

## Oracle Sequence Distribution

| Oracle-Best Sequence | Worlds | Percentage |
|---|---|---|
| B1_extended | 37 | 66.1% |
| explore_first | 9 | 16.1% |
| full_explore | 7 | 12.5% |
| B1_full | 3 | 5.4% |

## Key Metrics

| Metric | Value |
|---|---|
| Best global fixed | B1_extended = 0.527 |
| Oracle | 0.622 |
| **AdaptivityGap** | **0.096** |
| Oracle sequence diversity | 4 distinct |
| Dominant sequence share | 66.1% |

## Interpretation

The gap of 0.096 means an oracle that knows which sequence is optimal
for each world gains approximately 18% relative improvement over always
using B1_extended. This is meaningful but not overwhelming.

The gap is primarily driven by Regime A (exploration deficit), where
`explore_first` is strictly better than B1_extended (7/7 worlds), and
Regime C (discrimination deficit), where `full_explore` dominates.

For 5 of 8 regimes, B1_extended is oracle-optimal, confirming that
the V3 finding (B1_extended as REE-Minimal) was correct for those
information structures.
