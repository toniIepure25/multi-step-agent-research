# Negative Findings — Campaign V4

## N1: Learned motif policy UNDERPERFORMS best fixed strategy

**Claim tested**: H-REE-17 — A state-conditioned motif selector reduces
oracle regret relative to the best fixed policy.

**Result**: NOT_SUPPORTED. The transparent rule-based policy achieves
quality 0.323 vs fixed FULL_EXPLORE at 0.518. Policy regret (0.264) is
nearly 4x higher than fixed regret (0.070).

**Root cause**: The policy learns 26 rules but applies only 2 motifs in
practice (EXPLORE: 49, DISCRIMINATE: 7). First-rule dominance: the first
matching rule (evidence_count > 6) captures most states, preventing the
policy from selecting FULL_EXPLORE or EXPAND, which are actually optimal
for 28/56 dev worlds.

**Implication**: Either the feature space is insufficient for motif
prediction, or the transparent rule model class is too simple. A nonlinear
model might succeed, but this has not been tested.

## N2: Adaptive metacognition GO criterion FAILS on all 4 criteria

| Criterion | Status |
|---|---|
| Policy quality > fixed quality | FAIL (0.323 < 0.518) |
| Policy regret < fixed regret | FAIL (0.264 > 0.070) |
| Distinct trajectories >= 3 | FAIL (only 2) |
| Selection entropy > 0.5 | FAIL (0.377) |

**Interpretation**: Despite adaptive necessity being established (gap=0.096),
current methods cannot exploit it. The gap exists but is not exploitable
with transparent linear models on available features.

## N3: LLM-in-the-loop remains untested

**Status**: Infrastructure built (ChatCompletionsLLMClient adapter,
capability gate protocol), but no model server was available for execution.

**Implication**: All V3 and V4 findings remain simulator-specific. The
central question — whether temporal complementarity survives with LLM
cognition — is UNANSWERED.

**This is the most important open question.**

## N4: Paper readiness is limited to controlled-mechanism level

**Missing for stronger paper**: LLM-in-loop replication, working adaptive
policy, external validation.

**What IS justified**: A controlled-mechanism paper centered on the
epistemic benchmark and temporal complementarity measurement.

## N5: gen_hyp -> gen_hyp shows interference

Repeated hypothesis generation from the same state produces complementarity
of -0.050 (mildly harmful). The second hypothesis is less informative than
the first, and the budget would be better spent on retrieval or reasoning.

## N6: Adaptivity gap is modest (0.096)

While statistically identifiable, the gap between oracle and best fixed
is only ~10% of the best fixed quality. A more capable adaptive controller
could theoretically capture this, but the reward for doing so is limited
compared to simply using B1_extended or FULL_EXPLORE everywhere.

## N7: Order effects are weaker in V4 than V3

V4 order effects are smaller than V3 (largest: -0.083 for ret->hyp vs
hyp->ret). The V3 finding of +0.223 for forward vs reversed B1 was
stronger, but V3 tested complete 5-step sequences while V4 tests 2-step
pairs. Composition effects (what operations) still dominate ordering
effects (what order).

## N8: Attack and reason alone produce zero quality

Both attack and reason require hypotheses as prerequisites. Without
prior hypothesis generation, they produce 0.000 quality. This reinforces
the finding that gen_hyp is the enabling operation for all subsequent
cognition.
