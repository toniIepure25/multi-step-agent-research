# Negative Findings — Campaign V3

## N1: Hypothesis ecology is NOT a cross-architecture benefit

**Claim tested**: H-REE-12 — Hypothesis ecology improves quality across architectures.

**Result**: NOT_SUPPORTED. B1 = B1+ecology = 0.573. The ecology flag has no
effect when the policy already generates hypotheses. The V2 d≈1.4 effect reflects
"enable hypothesis generation," not persistent ecology management.

## N2: Hierarchical control does NOT exceed best fixed strategy

**Claim tested**: C4 — Adaptive selection among cognitive options reduces regret
relative to fixed sequences.

**Result**: NOT_SUPPORTED (vs fixed sequences). hierarchical_options = B1_extended
= 0.672. Only 2 distinct trajectories in 60 trials. The controller converges to the
same pattern as B1_extended.

## N3: Self-model ablation remains non-causal in V3

**Finding**: The self_model ablation pathway was not rewired for V3.
No data exists on whether self-model provides value because the ablation
never produces behavioral change. This is an engineering failure, not a scientific one.

## N4: Stopping policy ablation remains non-causal in V3

Same as N3. The stopping_policy flag does not produce causal intervention.

## N5: Attack is useless on 46% of market-selected states

**Finding**: In Full REE, attack is selected on states where it produces
zero quality contribution. This is not an attack failure — it is a scheduling
failure. The market does not check prerequisite conditions.

## N6: Full REE is Pareto-dominated

**Finding**: B1_full achieves 0.594 quality at 2500 tokens. Full REE achieves
0.324 quality at ~5000 tokens. Full REE has lower quality at higher cost across
all budget levels and task families.

## N7: DiversityAwareMarket provides no benefit

**V2 finding carried forward**: DiversityAwareMarket (0.33) is worse than
heuristic market (0.35). Adding diversity penalties to an already-flawed
bid system does not help.

## N8: Primitive action-value prediction is weak

**V2 finding**: Action-value correlation r = 0.137. This is insufficient for
adaptive scheduling. Sequence-level prediction was not tested due to the
hierarchical controller converging to a single trajectory, preventing
meaningful variance for modeling.

## N9: Ordering effects are smaller than composition effects

**Expected**: Strong non-commutativity would show that A->B >> B->A.

**Observed**: The largest pure ordering effect is +0.044 (hyp_ret_reason vs
ret_hyp_reason). This is real but much smaller than the composition effect
(replacing hypothesis with retrieval: +0.310). The dominant source of sequence
value is *what* operations are included, not *what order* they're executed in.

## N10: Ignorance is not independently testable

**Expected**: Conditional ignorance gating would show state-dependent value.

**Observed**: Ignorance is only produced by the attack operator, so testing
"ignorance ON/OFF" is equivalent to "attack ON/OFF." Independent testing
requires separating ignorance discovery from attack, which is not currently
implemented.
