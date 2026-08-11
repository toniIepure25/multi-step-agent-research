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

## Honest Assessment

These negative results mean the paper's central mechanism
(temporal complementarity) does not survive the strongest controls.
The phenomenon that V4 measured was real but was primarily the
main effect of hypothesis generation on quality, inflated by an
additive baseline that mixed high-value and zero-value operations.

This is a valid and important finding. It demonstrates that
careful budget-matched experimental design can distinguish
main effects from interactions — and in this case, the
interactions disappear.
