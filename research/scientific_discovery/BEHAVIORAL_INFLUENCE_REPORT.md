# Stage 1: Behavioral Influence Report

**Date:** 2026-08-14  
**Python:** 3.12.13  
**DEV Split:** Seeds 1–10, 6 world types, N=60 independent units

---

## Core Question

> Does the FalsificationEngine actually change scientific behavior, or is it decorative?

## Answer: The FalsificationEngine IS behaviorally consequential.

---

## 1. Event-Level Influence — PASS

When `enable_falsification=True`:
- Controller generates `FALSIFIER_PROPOSED` events (absent when OFF)
- Proposals target the current leading hypothesis
- Each proposal records expected_information_gain > 0

When `enable_falsification=False`:
- No falsification events
- Evidence processed identically without recognition amplification

## 2. Belief Trajectory Influence — PASS

ON and OFF produce measurably different belief trajectories.
The difference arises through the falsification recognition boost:
when decisive evidence matches the active falsification proposal,
the update is amplified (effective independence = 1.5 vs 1.0).

## 3. Statistical Results (DEV Split, N=60)

### B3 (Falsification-First) vs B0 (Passive Update)

| Metric | B3 | B0 | Δ | 95% CI | p |
|--------|----|----|---|--------|---|
| Recovery Accuracy | 0.833 | 0.833 | 0.000 | [0.000, 0.000] | — |
| Refutation Sensitivity | 0.397 | 0.372 | +0.021 | [+0.015, +0.026] | < 0.0001 |
| Theory Stickiness | 0.012 | 0.028 | -0.016 | [-0.023, -0.010] | < 0.0001 |
| False Abandonment | 0.000 | 0.000 | 0.000 | — | — |

### B3 vs B1 (Confirmation Seeker)

| Metric | B3 | B1 | Δ |
|--------|----|----|---|
| Recovery Accuracy | 0.833 | 0.667 | +0.167 |
| Refutation Sensitivity | 0.397 | 0.095 | +0.302 |
| Theory Stickiness | 0.012 | 0.397 | -0.384 |

### B3 vs B2 (Random Challenge)

| Metric | B3 | B2 | Δ |
|--------|----|----|---|
| Recovery Accuracy | 0.833 | 0.833 | 0.000 |
| Refutation Sensitivity | 0.397 | 0.268 | +0.130 |
| Theory Stickiness | 0.012 | 0.155 | -0.143 |

## 4. Mechanism: How Falsification Changes Behavior

The behavioral pathway:

1. Controller identifies current leading hypothesis
2. FalsificationEngine proposes what would falsify it
3. When incoming evidence contradicts the target (matching the falsification focus), the controller recognizes this as decision-relevant
4. Recognition amplifies the effective independence score (1.5× for target, 1.2× for supporting alternatives)
5. Amplified update produces larger belief drop on false hypothesis
6. Lower residual belief → faster correct recovery

Without falsification: evidence processed uniformly, no targeted recognition, no amplification.

## 5. Content Influence — PASS

The falsification engine targets SPECIFICALLY the leading hypothesis. This is not random — it identifies:
- The strongest falsifier for the current leader
- Critical assumptions being attacked
- Predictions that would be violated

The targeted nature means the boost fires only when evidence aligns with the proposed attack vector.

## 6. False Abandonment — PASS

B3 false-abandonment rate: **0.000** (0 out of 50 recoverable worlds)
B0 false-abandonment rate: **0.000**

Falsification does NOT increase false abandonment.

## 7. Non-Identifiable World — PASS

In non-identifiable worlds:
- Both B3 and B0 correctly produce 0.0 recovery accuracy (cannot identify correct hypothesis)
- Belief separation remains moderate (< 0.5)
- System does not invent certainty where none exists

## 8. Null World — PASS

In null worlds:
- The null hypothesis (no causal relationship) ends with highest belief
- Both causal hypotheses correctly lose belief
- Theory stickiness on false causal hypotheses is appropriately low

---

## Conclusion

**Falsification-first control is behaviorally consequential.**

It produces:
1. Larger belief drops on false hypotheses after decisive evidence (+0.021 refutation sensitivity)
2. Lower residual belief on refuted hypotheses (-0.016 theory stickiness)
3. No increase in false abandonment
4. Correct abstention under non-identifiability

The effect is moderate vs. B0 (passive) but massive vs. B1 (confirmation-seeking), which is the scientifically important contrast: the system actively resists confirmation bias.
