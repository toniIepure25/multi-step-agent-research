# Generative × Active Scaled — Stage 3D

## Date: 2026-08-14
## Status: EVALUATOR-LEVEL RESULTS (LLM integration pending)

---

## Research Question
> Does active scientific control retain its value when hypothesis space is
> generated imperfectly by an LLM?

---

## Stage 3C Pilot (N=20/cell)
| Condition | Recovery |
|-----------|----------|
| Canonical + Passive | 0.750 |
| Canonical + Active | 0.850 |
| Generated + Passive | 0.750 |
| Generated + Active | 0.850 |

Interaction: 0 (active effect identical regardless of hypothesis source)

---

## Stage 3D Evaluator-Level Replication (N=150)

The distributional generator produces worlds with known ecology.
This tests the EVALUATOR-LEVEL factorial:

| Condition | Recovery |
|-----------|----------|
| Full ecology (passive) | 0.540 |
| Full ecology (discrimination) | 0.680 |

Active advantage: +0.140, p<0.001

### Interpretation for LLM Integration
When LLM generates hypotheses:
- If true mechanism IS in generated set → active control adds ~+0.14
- If true mechanism NOT generated → both conditions fail (generation bottleneck)
- The interaction depends on LLM generation quality

---

## True-Mechanism Coverage Mediator

Before policy starts, record: **is true mechanism present in hypothesis set?**

Decomposition:
- If TRUE PRESENT: policy matters (active > passive)
- If TRUE ABSENT: policy irrelevant (both fail)

From Stage 3C: LLM generated true mechanism in 100% of test cases (N=5)
This was likely too easy. Stage 3D distributional worlds should be harder.

---

## Pending: LLM-Level Factorial (requires inference)

When scaled SD-H4 inference is run:
1. Record which worlds the LLM's generated ecology covers the truth
2. Compute recovery conditional on coverage
3. Report interaction between generation quality and active control value
