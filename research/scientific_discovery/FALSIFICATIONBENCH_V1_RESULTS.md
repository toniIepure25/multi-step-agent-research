# FalsificationBench V1 — Results

**Date:** 2026-08-14  
**Split:** DEV (seeds 1–10)  
**N:** 60 (6 world types × 10 seeds)

---

## Summary Table

| Policy | Recovery Acc | Refut. Sens. | Theory Stickiness | Correct Conc. |
|--------|:---:|:---:|:---:|:---:|
| B0 Passive | 0.833 | 0.372 | 0.028 | 0.167 |
| B1 Confirmation | 0.667 | 0.095 | 0.397 | 0.167 |
| B2 Random Challenge | 0.833 | 0.268 | 0.155 | 0.167 |
| **B3 Falsification-First** | **0.833** | **0.397** | **0.012** | 0.167 |
| B4 Oracle | 1.000 | 0.000 | 0.148 | 1.000 |

---

## Per World Type (B3 vs B0)

| World | B3 Recovery | B0 Recovery | B3 Refut | B0 Refut | B3 Stick | B0 Stick |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|
| confirmation_trap | 1.000 | 1.000 | 0.387 | 0.400 | 0.000 | 0.072 |
| confounded_causality | 1.000 | 1.000 | 0.400 | 0.358 | 0.000 | 0.000 |
| measurement_artifact | 1.000 | 1.000 | 0.400 | 0.369 | 0.000 | 0.000 |
| non_identifiable | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| null_world | 1.000 | 1.000 | 0.400 | 0.376 | 0.074 | 0.098 |
| reverse_causality | 1.000 | 1.000 | 0.400 | 0.358 | 0.000 | 0.000 |

---

## Statistical Comparison (B3 - B0, paired)

| Metric | Mean Δ | 95% CI | p (permutation) | Direction |
|--------|:---:|:---:|:---:|---|
| Recovery Accuracy | +0.000 | [0, 0] | — | Tied |
| Refutation Sensitivity | **+0.021** | [+0.015, +0.026] | **< 0.0001** | B3 better |
| Theory Stickiness | **-0.016** | [-0.023, -0.010] | **< 0.0001** | B3 better |
| False Abandonment | 0.000 | — | — | Both zero |

---

## Interpretation

1. **Recovery is matched**: Both B3 and B0 correctly identify the true hypothesis. The evidence in these worlds is strong enough that even passive processing succeeds. This is appropriate for establishing safety (falsification doesn't hurt).

2. **Refutation is faster with B3**: Falsification-first produces 5.6% larger belief drops after decisive evidence (0.397 vs 0.372). This means the system recognizes refuting evidence more efficiently.

3. **Stickiness is lower with B3**: After decisive refutation, B3 retains only 1.2% residual belief on false hypotheses vs 2.8% for B0. This 57% reduction demonstrates cleaner theory abandonment.

4. **Confirmation bias is catastrophic**: B1 (confirmation seeker) has 30× higher stickiness (0.397 vs 0.012) and fails to recover in 33% of worlds. This validates the importance of falsification as an antidote to confirmation bias.

5. **No false abandonment**: Both B3 and B0 achieve 0% false abandonment — falsification is safe.

---

## Known Limitations

- DEV split only (locked test not yet run)
- All evidence is predetermined (no active evidence search)
- No LLM-generated hypotheses or evidence
- Effect size moderate for B3 vs B0 (large for B3 vs B1)
- Conclusion type metric not differentiated (both use simple threshold)
