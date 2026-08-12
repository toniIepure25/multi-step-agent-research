# V6 Negative Findings

## 1. Compute-Controlled Complementarity = Zero

Under matched-budget factorial conditions (same LLM calls per cell),
the interaction term for gen_hyp × reason is exactly 0.000.
The V4 "temporal complementarity" (+0.162) was the main effect of
hypothesis generation, not a super-additive interaction.

**Implication:** The central claim of the paper (temporal complementarity)
does not survive budget-matched factorial controls.

## 2. Retrieval-Mediated Complementarity = Zero

Under matched-budget conditions with retrieval, the interaction term
for gen_hyp × second_retrieve is also 0.000.
The second retrieval adds nothing beyond hypothesis generation.

## 3. Matched-Budget Attack Timing = Negligible

Under matched-budget conditions (same operations, different order),
the attack timing effect shrinks from +0.276 to +0.019.
Attack timing value was an artifact of compute/information confound.

## 4. Hypothesis Generation Dominates Quality

Across all V6 conditions, the primary determinant of quality is
whether `generate_hypothesis` activated the correct latent hypothesis.
All other operations (reason, attack, second retrieve) contribute
negligibly once a hypothesis is present.

This suggests the quality function has a threshold structure:
correct hypothesis → high quality; no hypothesis → zero quality.

## 5. Token Counting Not Available

The Ollama API returns 0 for token counts in all conditions.
This is a limitation for compute accounting.

## Summary

| V4/V5 Claim | V6 Verdict | Explanation |
|-------------|-----------|-------------|
| Temporal complementarity +0.162 | ZERO under budget match | Main effect, not interaction |
| Attack timing +0.276 | 0.019 under budget match | Compute confound |
| Hypothesis generation catalyzes retrieval | Partial — gen_hyp value is standalone, not synergistic | Quality dominated by hypothesis correctness |

## 6. Simulator Cannot Test Semantic Mediation

H-REE-20 manipulation check FAILED on the simulator. REAL = SHUFFLED
exactly (Q=0.2813, recall=0.750 for both). The simulator's keyword-based
hypothesis binding cannot distinguish task-relevant from irrelevant
LLM-generated hypothesis text. This makes it unsuitable for testing
whether semantic content matters.

## 7. Real Hypotheses Can HURT Task Performance

On SciFact (N=100), real task-specific hypotheses significantly
degrade classification accuracy:
- REAL accuracy: 0.720
- SHUFFLED accuracy: 0.980
- Effect: -0.260 (95% CI [-0.346, -0.174])

Real hypotheses anchor the model toward a specific verdict,
which is often wrong. Shuffled (irrelevant) hypotheses act as
matched-compute controls that don't bias reasoning.

## 8. Retrieval Transfer Is Positive But Disconnected From Performance

On SciFact, real hypotheses improve gold evidence retrieval
(+0.230, CI excludes zero) but this improved retrieval HURTS
accuracy. Better evidence is not always better for the task.

## 9. DIRECT Baseline Often Competitive

On both SciFact (acc=0.780) and HotpotQA (F1=0.409), the DIRECT
condition (no hypothesis at all, one fewer LLM call) performs
comparably to or better than REAL. The extra LLM call for
hypothesis generation does not consistently improve outcomes.

## Summary (Updated)

| V4/V5 Claim | V6 Verdict | Explanation |
|-------------|-----------|-------------|
| Temporal complementarity +0.162 | ZERO under budget match | Main effect, not interaction |
| Attack timing +0.276 | 0.019 under budget match | Compute confound |
| Hypothesis generation catalyzes retrieval | Mixed | Improves retrieval but not always task accuracy |
| Semantic content matters | PARTIALLY — retrieval yes, accuracy mixed | Task-dependent |
| External benchmark transfer | PARTIALLY — retrieval transfers, performance does not universally | SciFact negative, HotpotQA marginal |

## Honest Assessment

The V6 completion reveals a nuanced picture:

1. The original temporal complementarity was NOT a super-additive interaction
2. Attack timing was compute-confounded
3. Semantic hypothesis content DOES causally affect retrieval on external tasks
4. But improved retrieval does NOT reliably improve task performance
5. The strongest finding is methodological: apparent cognitive-agent effects
   can be decomposed into retrieval mediation (real) and reasoning anchoring
   (harmful on some tasks)

The project has produced an unusually detailed falsification of its
original mechanism combined with a genuine discovery about retrieval
mediation — but the practical value of that mediation is task-dependent.
