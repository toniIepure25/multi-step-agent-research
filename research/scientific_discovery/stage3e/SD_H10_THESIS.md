# SD-H10 — Post-Falsification Abductive Recovery

## Status: PROSPECTIVE (motivated by SD-H4 results)

## Formal Statement

> Structured generation and evaluation of mechanistically distinct alternative
> hypotheses improves recovery after falsification relative to one-shot theory
> replacement, without increasing false commitment or unnecessary hypothesis
> proliferation.

## Motivation

SD-H4 SCALED showed:
- Correct abandonment: 22/23 = 95.7%
- Recovery after abandonment: 4/22 = 18.2%

Forensic analysis revealed:
- 17/18 failures: model returned EMPTY new_explanation
- True mechanism was present in evidence for ALL 18 failed cases
- The bottleneck is GENERATION, not SELECTION

## Causal Decomposition

Recovery = Coverage × Selection

Where:
- Coverage (C) = P(true mechanism appears in candidate set)
- Selection (S|C) = P(true mechanism selected | it is in candidate set)
- Recovery (R) = C × S

SD-H4 one-shot: C = 0.182, S|C = 1.000, R = 0.182

If R2 increases C without reducing S|C, recovery improves.

## Predictions (to be tested)

1. R2 coverage > R0 coverage (structured generation produces more candidates)
2. R4 recovery > R2 recovery (guaranteed coverage → selection becomes the limit)
3. R2 recovery > R1 recovery (structure helps beyond raw compute)
4. If R4 recovery ≈ 1.0: bottleneck is purely generation
5. If R4 recovery < 1.0: selection/evidence interpretation also limits

## Not Preregistered Before SD-H4

This hypothesis was formulated AFTER observing the 18.2% recovery rate.
It is prospective for Stage 3E, not retrospective for Stage 3D.
