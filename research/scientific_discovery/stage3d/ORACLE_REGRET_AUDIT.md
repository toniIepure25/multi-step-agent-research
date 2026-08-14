# Oracle Regret Audit — Stage 3D

## Date: 2026-08-14
## Problem: Stage 3C reported 100% zero-regret on LOCKED, which was a measurement error.

---

## Incorrect Measurement (Stage 3C)

Stage 3C computed "regret" as:
```
Regret_wrong = JSD(oracle_experiment) - JSD(policy_experiment)
```

This measured how the policy's JSD compared to the oracle's JSD. Since E3 (JSD policy)
maximizes JSD by definition, it trivially achieves ~zero "regret" in JSD space.

**This is not meaningful regret.** It's a tautology.

---

## Correct Regret Definition

```
Regret(policy) = OracleIG(oracle_best_experiment) - OracleIG(policy_chosen_experiment)
```

Where:
- `OracleIG(e)` = `compute_oracle_information_gain(e, beliefs, true_hypothesis_id)`
- This uses the TRUE hypothesis's prediction distribution (evaluator-side only)
- Units: bits (Shannon information)
- Properties: always >= 0; = 0 iff policy picks the oracle-optimal experiment

---

## Corrected Results (LOCKED, seeds 21-40, 5 hardened worlds)

| Policy | True IG Regret | Zero-Regret Rate | Oracle Agreement |
|--------|---------------|------------------|------------------|
| E0 Random | 0.1114 ± 0.0128 | 34% | — |
| E2 Confirmation | 0.0916 ± 0.0128 | 40% | — |
| E3 JSD | 0.0016 ± 0.0003 | 80% | 80% |
| E4 Approx-EIG | 0.0016 ± 0.0003 | 80% | 80% |

### Key Corrections
- Stage 3C claimed "100% zero-regret" → **actual: 80%**
- The 20% where JSD ≠ Oracle are worlds where JSD ranking diverges from true IG ranking
- JSD regret is very low (0.0016 bits) but NOT zero

---

## Why DEV Had 69% and LOCKED Had 80%

| Property | DEV (seeds 1-20) | LOCKED (seeds 21-40) |
|----------|-----------------|---------------------|
| Zero-regret (JSD) | 69% | 80% |
| Oracle agreement | ~69% | 80% |

**Explanation:** The LOCKED seeds happened to produce worlds with larger oracle action margins 
(easier to identify best experiment). This is expected random variation — not a bug,
but it means LOCKED worlds are slightly easier than DEV.

---

## Oracle Action Margin Analysis

```
Oracle_Action_Margin = Value(best_experiment) - Value(second_best_experiment)
```

When margin is large → task is easy (any reasonable policy picks correctly).
When margin is small → task is hard (policies can legitimately disagree).

Hardened worlds (N=100):
- Mean margin: 0.063
- 14% of worlds have margin < 0.01 (genuinely hard)

---

## Distributional World Results (N=200, diverse generated worlds)

| Policy | True IG Regret | Zero-Regret | Oracle Agreement |
|--------|---------------|-------------|------------------|
| E0 Random | 0.0835 ± 0.0067 | 23% | — |
| E2 Confirmation | 0.0639 ± 0.0057 | 32% | — |
| E3 JSD | 0.0093 ± 0.0016 | 75% | 73% |
| E4 Approx-EIG | 0.0085 ± 0.0016 | 77% | 76% |

### JSD vs Approx-EIG
- EIG slightly better (0.0085 vs 0.0093 regret) but NOT significant (p=0.14)
- EIG has 76% oracle agreement vs JSD's 73%
- Conclusion: JSD is a strong proxy for EIG, but not identical

---

## Numerical Tolerance

For presentation purposes:
- |regret| < 0.0001 → report as zero-regret
- Negative regret beyond -0.001 → evaluator bug (STOP)
- Raw values always preserved; clipping is presentation-only

---

## Conclusion

1. Stage 3C "100% zero-regret" was incorrect — actual figure is 80%
2. Correct regret formula uses OracleIG, not JSD
3. JSD is a strong but imperfect proxy for oracle information gain
4. Hardened worlds still have relatively high agreement (80%) — more diversity needed
5. Distributional generator produces healthier 73% agreement (more room for policy differences)
