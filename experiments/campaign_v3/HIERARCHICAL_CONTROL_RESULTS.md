# Hierarchical Metacognitive Control Results (Phase 19)

## Prerequisite Check

Phase 18 found strong temporal complementarity:
- gen_hyp + reason complementarity: +0.228 (super-additive)
- Order effects: B1 forward vs reversed = +0.223
- ret+hyp+reason vs ret+ret+reason: +0.310

These effects justify testing hierarchical control.

## Design

### Cognitive Options

| Option | Sequence | Initiation | Expected Cost |
|---|---|---|---|
| EXPLORE | retrieve -> gen_hyp | ev_count < 2 or hyp_count < 2 | 1000 |
| DISCRIMINATE | retrieve -> gen_hyp -> reason | hyp >= 1 and ev >= 1 | 1500 |
| CONSOLIDATE | reason | hyp >= 2 and ev >= 2 | 500 |
| INVESTIGATE | attack -> reason | hyp >= 2 and ev >= 3 | 1000 |
| EXPAND | retrieve -> retrieve -> gen_hyp | ev < 3 | 1500 |

### Two-Level Controller

High level: select cognitive option based on state.
Low level: execute bounded sequence within option.

## Results

### Dev Comparison (N=50)

| Condition | Mean Quality | Std |
|---|---|---|
| B1_extended | **0.6304** | 0.176 |
| hierarchical_options (5k) | **0.6304** | 0.176 |
| B1_full | 0.5731 | 0.228 |
| round_robin | 0.4427 | 0.284 |
| full_ree | 0.3579 | 0.162 |
| hierarchical_3k | 0.3435 | 0.154 |
| hierarchical_2k | 0.3435 | 0.154 |

### V3 Locked Test (N=25)

| Condition | Mean Quality | Std |
|---|---|---|
| B1_extended | **0.6721** | 0.109 |
| hierarchical_options (5k) | **0.6721** | 0.109 |
| B1_full | 0.5944 | 0.216 |
| round_robin_ree | 0.4384 | 0.250 |
| full_ree | 0.3243 | 0.168 |
| B0_direct | 0.2886 | 0.223 |
| full_ree_no_ecology | 0.0376 | 0.016 |

### Adaptivity Test

Only 2 distinct sequences observed across 60 trials:
- 40x: `[retrieve, gen_hyp, retrieve, gen_hyp]` (budget <= 3k)
- 20x: `[retrieve, gen_hyp, retrieve, gen_hyp, retrieve, gen_hyp, reason, reason, reason, reason]` (budget=5k)

## Analysis

### Hierarchical control MATCHES but does not EXCEED best fixed strategy

hierarchical_options = B1_extended = 0.672 on locked test (identical).
The option selector, given sufficient budget, converges to the same
explore->discriminate->consolidate trajectory that B1_extended implements
as a fixed sequence.

### Limited adaptivity demonstrated

Only 2 distinct sequences in 60 trials. The controller is deterministic
given the budget: at 5k it always runs EXPLORE + EXPLORE + EXPLORE + 
CONSOLIDATE (x4). Budget is the only variable that changes behavior.

### Budget sensitivity

At lower budgets (2k, 3k), hierarchical drops to 0.344 because it can
only fit EXPLORE options, missing the critical reason step.

## Interpretation

The hierarchical controller succeeds in the sense that it discovers the
effective motif structure (explore then reason). But it does not demonstrate
true **adaptive** advantage — it converges to a single trajectory.

For hierarchical control to beat fixed sequences, it would need to:
1. Encounter diverse state-dependent conditions where different options are optimal
2. Correctly discriminate those conditions
3. Select options that fixed sequences cannot

The current semantic simulator does not generate sufficient state diversity
to test this. All 5 families follow a similar information-gathering trajectory
(retrieve evidence, generate hypotheses, reason about consistency).

## Hypothesis Verdicts

**H-REE-13 (Greedy control fails because it can't capture sequence structure)**:
**SUPPORTED**. Greedy market (0.324) dramatically underperforms both fixed
sequences (0.594-0.672) and option-based control (0.672). The market evaluates
operations independently and cannot capture the gen_hyp->reason synergy.

**C4 (Hierarchical control improves over primitive greedy)**:
**SUPPORTED vs greedy** (0.672 vs 0.324). **NOT SUPPORTED vs fixed** (0.672 = 0.672).

## Conclusion

Hierarchical metacognitive control recovers the quality of the best fixed
strategy and dramatically outperforms primitive greedy scheduling. However,
it does not demonstrate adaptive advantage over a well-chosen fixed sequence.

The practical implication: for the current task distribution, a fixed
cognitive sequence (B1_extended) is sufficient. Hierarchical control
becomes valuable only when task diversity demands different cognitive
strategies for different problem types.
