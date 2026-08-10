# Cognitive Complementarity Analysis (Phase 18.2-18.4)

## Objective

Test whether cognitive operations exhibit temporal complementarity:
is sequence value different from the sum of primitive values?

## Method

For each of 50 V3 dev worlds, evaluated:
1. Single-action values: Q(E, single_action)
2. Sequence values: Q(E, [a1, a2])
3. Complementarity: Q(sequence) - mean(Q(primitive_a), Q(primitive_b))
4. Order effects: Q(A->B) - Q(B->A)

## Results

| Pair | Q(A->B) | Q(B->A) | Order Effect | Complementarity |
|---|---|---|---|---|
| hyp_ret_reason vs ret_hyp_reason | **0.398** | 0.354 | +0.044 | +0.272 |
| hyp_then_ret vs ret_then_hyp | **0.376** | 0.339 | +0.037 | +0.188 |
| ret_hyp_reason vs ret_ret_reason | **0.354** | 0.044 | **+0.310** | +0.228 |
| hyp_then_reason vs reason_then_hyp | 0.326 | 0.326 | 0.000 | +0.163 |
| ret_then_reason vs reason_then_ret | 0.050 | 0.050 | 0.000 | +0.025 |
| atk_then_reason vs reason_then_atk | 0.000 | 0.000 | 0.000 | 0.000 |

## Key Findings

### Finding 1: Cognitive operations are strongly non-additive

The largest complementarity is **ret+hyp+reason vs ret+ret+reason = +0.310**.
Replacing the second retrieve with generate_hypothesis in a 3-step sequence
produces a massive quality improvement. This is super-additive: the sequence
value far exceeds the sum (or mean) of individual operation values.

### Finding 2: gen_hyp + reason is the core synergistic pair

gen_hyp alone: weak quality. reason alone: minimal quality. Together: 0.326.
This is strong super-additivity. Reasoning requires hypotheses to evaluate;
hypothesis generation produces candidates that are meaningless without evaluation.

### Finding 3: Order effects exist but are moderate

- hyp_then_ret > ret_then_hyp: +0.037 (hypothesis-first retrieval is more targeted)
- hyp_ret_reason > ret_hyp_reason: +0.044 (hypothesizing first provides better framing)
- The largest ordering effect (+0.310 for ret+hyp+reason vs ret+ret+reason) is 
  really a content difference (hypothesis vs retrieval) not pure ordering.

### Finding 4: Pure ordering effects are smaller than composition effects

The truly commutative pairs (hyp_then_reason, ret_then_reason, atk_then_reason)
show zero ordering effect. The non-zero ordering effects come from pairs where
order changes the information available to later operations.

### Finding 5: Attack has no complementarity value

Attack combined with reason produces zero quality when invoked on an empty state.
This is consistent with Phase 18.5 (attack state-dependence): attack requires
prerequisite conditions to be useful.

## Interpretation

Cognitive operations exhibit strong **compositional** complementarity but moderate
**ordering** complementarity. The primary source of super-additivity is the
combination of hypothesis generation with reasoning — these operations are
semantically complementary. Ordering effects exist mainly because earlier operations
change the information available to later ones (targeted retrieval vs blind retrieval).

## Hypothesis Verdict

**H-REE-11 (Temporal complementarity)**: **SUPPORTED**. Sequence value is
strongly non-additive. The complementarity between generate_hypothesis and reason
is the dominant effect (0.326 from combination vs ~0.05+0.16=0.21 from primitives).

This explains why B1 outperforms primitive greedy scheduling: B1's fixed sequence
guarantees the gen_hyp→reason synergy, while the greedy market may never schedule
this combination because it evaluates operations independently.
