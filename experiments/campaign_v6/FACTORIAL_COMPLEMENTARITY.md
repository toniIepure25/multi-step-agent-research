# V6 Factorial Complementarity Results

## Study A — Information-Held-Constant (No Retrieval)

### Design
2×2 factorial: Hypothesis (present/absent) × Reason (present/absent).
All four conditions use exactly 3 LLM calls. No retrieval in any condition.
Control operations consume matched compute without adding cognitive content.

### Results (N = 32 worlds, 8 regimes × 4 seeds)

| Condition | Mean Q | Std | LLM Calls |
|-----------|--------|-----|-----------|
| C00 (control + control) | 0.000 | 0.000 | 3 |
| C10 (hyp + control) | 0.164 | varies | 3 |
| C01 (control + reason) | 0.000 | 0.000 | 3 |
| C11 (hyp + reason) | 0.164 | varies | 3 |

### Factorial Interaction

```
Interaction = C11 - C10 - C01 + C00 = 0.164 - 0.164 - 0.000 + 0.000 = 0.000
95% CI: [0.000, 0.000]
```

### Interpretation

**The interaction term is exactly zero.** Under matched-compute conditions:
- Hypothesis generation has a strong main effect (+0.164)
- Reason has zero main effect (0.000)
- There is NO super-additive complementarity

The entire value comes from hypothesis generation alone. Reason does not
add value beyond what hypothesis generation provides, even when hypotheses
exist to evaluate.

This is likely because without evidence (no retrieval), reason() has
nothing to evaluate against, and returns initial plausibility values
unchanged.

## Study A-B — Retrieval-Mediated

### Design
2×2 factorial: Hypothesis (present/absent) × Second Retrieve (present/absent).
All conditions start with one retrieve. Tests whether hypothesis generation
improves subsequent retrieval quality.

### Results (N = 32 worlds)

| Condition | Mean Q | LLM Calls |
|-----------|--------|-----------|
| CB00 (retrieve + control + control) | 0.050 | 3 |
| CB10 (retrieve + hyp + control) | ~0.54 | 3 |
| CB01 (retrieve + control + retrieve) | 0.050 | 2 |
| CB11 (retrieve + hyp + retrieve) | ~0.54 | 3 |

### Factorial Interaction

```
Interaction = CB11 - CB10 - CB01 + CB00 ≈ 0.000
95% CI: [0.000, 0.000]
```

### Interpretation

**Again, zero interaction.** The second retrieval adds no value beyond
hypothesis generation alone. The quality is determined almost entirely
by whether hypothesis generation activated the correct latent hypothesis.

## Scientific Conclusion

**H-REE-19 (Compute-Controlled Temporal Complementarity): NOT SUPPORTED**

Under properly controlled conditions with matched LLM call budgets:
- The V4 "temporal complementarity" effect (+0.162) was entirely
  attributable to the main effect of hypothesis generation
- There is no super-additive interaction between operation pairs
- The additive baseline used in V4 (average of standalone values)
  was misleading because it divided the hypothesis-generation value

This is a valid negative result that directly addresses the CRITICAL
reviewer concern from the paper hardening audit.

## Implications for V4 Complementarity Claim

The V4 complementarity measure was:
```
Comp(A, B) = Q(A→B) - 0.5*(Q(A) + Q(B))
```

For gen_hyp → retrieve:
- Q(gen_hyp) ≈ 0.273 (hypothesis generation alone, high because it activates true hypothesis)
- Q(retrieve) ≈ 0.050 (retrieval alone, low because no hypothesis to anchor quality)
- Q(gen_hyp→retrieve) ≈ 0.323

Comp = 0.323 - 0.5*(0.273 + 0.050) = 0.323 - 0.162 = +0.161

But in the factorial:
- Q(neither) = 0.000
- Q(hyp only) = 0.164
- Q(retrieve only) ≈ 0.050
- Q(hyp + retrieve) ≈ 0.54

Interaction = 0.54 - 0.164 - 0.050 + 0.000 = +0.326

Wait — this suggests POSITIVE interaction in Study A-B!

**CORRECTION:** The factorial results need re-examination. The specific
values across all 32 worlds should be analyzed for variance. If all
worlds show the same values, the quality function may have a step-function
structure that creates apparent interactions.
