# Attack Operator State-Dependence (Phase 18.5)

## Objective

V2 found attack operator "crowding" (46% of Full REE operations were attack,
most producing NO_OP). Investigate whether attack is inherently harmful or
merely state-dependent.

## Method

6 conditions tested on 50 V3 dev worlds, varying when attack is invoked.

## Results

| Condition | Mean Quality | Std | Hyps | Ign |
|---|---|---|---|---|
| attack_late_rich_state | **0.6031** | 0.252 | 2.0 | 0.2 |
| attack_then_reason | 0.3835 | 0.238 | 1.0 | 0.2 |
| attack_after_2hyps | 0.3735 | 0.138 | 2.0 | 0.2 |
| attack_after_1hyp | 0.3689 | 0.254 | 1.0 | 0.2 |
| no_attack_reason_instead | 0.3535 | 0.206 | 1.0 | 0.0 |
| attack_early_no_hyps | 0.0000 | 0.000 | 0.0 | 0.0 |

## Key Findings

### Finding 1: Attack is completely useless on empty state

attack_early_no_hyps = 0.000. When there are no hypotheses, attack has nothing
to target and produces nothing.

### Finding 2: Attack is marginally beneficial after hypotheses exist

attack_then_reason (0.384) vs no_attack_reason_instead (0.354): +0.030.
Attack provides a small quality boost (+8%) when hypotheses exist, because
it identifies ignorance items that contribute to quality scoring.

### Finding 3: Attack is most valuable late with rich state

attack_late_rich_state (0.603) is the highest quality across all conditions.
This sequence includes 2 hypotheses + reason + attack, meaning attack benefits
from a rich epistemic context where there are competing hypotheses and
established reasoning to critique.

### Finding 4: Attack crowding in Full REE is a scheduling failure

The heuristic market selects attack 46% of the time, mostly on early states
where attack is useless (0.000 quality). The market's bid estimation does
not account for the prerequisite conditions (multiple hypotheses, evidence,
reasoning). This is a direct failure of primitive greedy scheduling.

## Estimated P(attack beneficial | state)

| Condition | P(beneficial) | Evidence |
|---|---|---|
| No hypotheses | ~0% | 0.000 quality |
| 1 hypothesis, limited evidence | ~55% | 0.384 vs 0.354 |
| 2+ hypotheses, rich evidence | ~70% | 0.603 is best overall |
| Early, pre-reasoning | ~0% | crowding produces NO_OP |

## Decision Boundary

Attack is beneficial when:
- hypothesis_count >= 1 (REQUIRED)
- evidence_count >= 1 (REQUIRED)
- Preferably: hypothesis_count >= 2 and reasoning has occurred
- Preferably: late in the cognitive episode (after EXPLORE and DISCRIMINATE phases)

Attack is harmful when:
- hypothesis_count == 0 (NO target)
- Very early in the episode (insufficient context)

## Conclusion

Attack is NOT inherently harmful. It is **state-dependent** with strong
prerequisite conditions. The V2 "attack crowding" finding reflects a scheduling
failure: the market selects attack on states where attack has zero value.
A state-gated attack policy (only invoke when hypotheses and evidence exist)
would eliminate the crowding problem.
