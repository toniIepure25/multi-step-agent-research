# Campaign V6 — Causal Closed-Loop Validation of Cognitive Sequence Value

## Starting SHA
`1ab24bc`

## Central Question

Do semantically meaningful compositions of cognitive operations causally improve
downstream epistemic performance beyond compute, information exposure, and
operation-count controls?

## Prior State

Campaign V5 + paper hardening revealed three CRITICAL weaknesses:

1. **LLM non-causality:** Simulator-side structure determines quality;
   LLM output is never parsed into epistemic state.
2. **Compute unfairness:** Most headline comparisons use different amounts
   of computation.
3. **Benchmark tautology:** Complementarity may be a design property of
   the simulator rather than an independent discovery.

Additional HIGH issues: R6 duplicate, reflection bug, synthetic "real evidence,"
small N, clustering in CIs.

## V6 Studies

### Study A — Compute-Controlled Factorial Complementarity
2×2 factorial design: all four cells use identical LLM call count,
token budget, and evidence. Tests interaction term free of resource confound.

### Study B — Semantic Artifact Intervention
Real vs shuffled vs neutral intermediate artifacts. Same downstream budget.
Tests whether cognitive artifact CONTENT matters.

### Study C — Matched-Budget Attack Timing
Same multiset of operations, same budget; only attack position varies.
Tests state-dependent value without resource confound.

### Study D — Exogenous Benchmark Transfer
Public evidence-grounded datasets (not constructed for this hypothesis).
Tests whether effects appear on independently defined tasks.

## Design Principles

1. **Closed-loop LLM cognition:** LLM artifacts causally affect state transitions.
2. **Compute-matched controls:** Every comparison uses equal LLM calls and token budget.
3. **Condition certification:** Every condition verified via behavioral trace before execution.
4. **Task-level independence:** The experimental unit is the task/world, not the fork.
5. **Preregistered analysis:** All primary comparisons defined before locked execution.
6. **Negative results preserved:** Null findings are valid scientific outcomes.

## Execution Order

```
1. Fix reflection bug and R6 in V6 runner (Phase 30)
2. Build closed-loop LLM infrastructure (Phase 31)
3. Condition certification (Phase 30.2-30.3)
4. Factorial design implementation (Phase 32)
5. Semantic intervention system (Phase 33)
6. Matched-budget attack timing (Phase 34)
7. External dataset selection and audit (Phase 35)
8. Power analysis (Phase 36)
9. DEV validation
10. Protocol freeze → locked execution
11. Results and analysis
```
