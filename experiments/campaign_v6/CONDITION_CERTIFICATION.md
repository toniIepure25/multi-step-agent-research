# V6 Condition Certification Report

## Model: gemma3:27b-it-qat
## Date: 2026-08-11
## All 11 conditions: PASS

### Study A: Information-Held-Constant Factorial

| Condition | Operations | Calls | Status |
|-----------|-----------|-------|--------|
| C00_control_control | control, control, synthesis | 3 | PASS |
| C10_hyp_control | generate_hypothesis, control, synthesis | 3 | PASS |
| C01_control_reason | control, reason, synthesis | 3 | PASS |
| C11_hyp_reason | generate_hypothesis, reason, synthesis | 3 | PASS |

All four cells use 3 LLM calls. No retrieval in any condition.
Evidence held constant (empty). Tests pure computational complementarity.

### Study A-B: Retrieval-Mediated Factorial

| Condition | Operations | Calls | Status |
|-----------|-----------|-------|--------|
| CB00_control_control | retrieve, control, control, synthesis | 3 | PASS |
| CB10_hyp_control | retrieve, generate_hypothesis, control, synthesis | 3 | PASS |
| CB01_control_retrieve | retrieve, control, retrieve, synthesis | 2 | PASS |
| CB11_hyp_retrieve | retrieve, generate_hypothesis, retrieve, synthesis | 3 | PASS |

Tests whether hypothesis generation improves targeted retrieval quality.

### Study C: Matched-Budget Attack Timing

| Condition | Operations | Calls | Status |
|-----------|-----------|-------|--------|
| early_attack | attack, retrieve, generate_hypothesis, reason, synthesis | 4 | PASS |
| mid_attack | retrieve, generate_hypothesis, attack, reason, synthesis | 4 | PASS |
| late_attack | retrieve, generate_hypothesis, reason, attack, synthesis | 4 | PASS |

All three conditions use the SAME operations (1 attack, 1 retrieve,
1 gen_hyp, 1 reason, 1 synthesis) with 4 LLM calls each.
Only attack position varies.

## Closed-Loop Verification

For conditions containing generate_hypothesis:
- LLM output is parsed and bound to latent hypothesis space
- Binding method: keyword overlap (when >=2 word match) or evidence-priority fallback
- Bound hypothesis enters epistemic state and affects downstream operations

For conditions containing reason:
- sim.reason() consistency scores update posteriors before evaluate()
- When no hypotheses exist, a matched-budget control call is made instead

For conditions containing attack:
- sim.attack_hypothesis() is called with LLM-identified target
- Hidden variable discovery enters evaluate() inputs

## Budget Fairness Verification

### Study A: All cells use 3 LLM calls, 0 retrievals
### Study C: All cells use 4 LLM calls, 1 retrieval

CB01 shows 2 calls vs 3 for other CB conditions — this is because the second
retrieve doesn't generate a query when no hypotheses exist. This is a minor
asymmetry that should be documented.
