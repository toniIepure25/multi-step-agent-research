# Phase 14.1 — Causal Mechanism Audit

## 14.2 Discrepancy Root Cause

Phase 10 reported 13 mechanism influence tests passing.
Campaign V1 reported only 2 of 12 ablation flags causally controlling runtime behavior.

**Root cause**: The two test regimes operate at different levels.

| Aspect | Mechanism influence tests | Ablation flags in campaigns |
|--------|--------------------------|----------------------------|
| Entry point | Direct `operator.propose()`, `policy.evaluate()`, `reducer.apply()` | `BenchmarkRunner._build_registry()` → `EpistemicController.run()` |
| What varies | Hand-constructed `EpistemicState` with different `views.self_model`, `views.ignorance_items`, etc. | Whether an operator class is added to `OperatorRegistry` |
| ON/OFF mechanism | Input state fields are toggled | Only `hypothesis_ecology` and `ignorance_ledger` are checked in `_build_registry()` |
| Limitation | Tests prove LOCAL causal wiring (operator reads state field correctly) but do NOT prove the mechanism influences SYSTEM-LEVEL outcomes through the experiment pipeline | Ablation flags are metadata-only for 10 of 12 mechanisms |

**Specific gaps per mechanism**:

- **self_model**: Influence test varies `views.self_model.operator_success_rates` and shows bid changes. But `_build_registry()` does not check the `self_model` flag. The controller always injects the same `self_model_summary`. The flag is metadata.
- **stopping_policy**: Influence test varies ignorance in state and shows `StoppingPolicy.evaluate()` returns different decisions. But `_build_registry()` does not check the flag. The controller always creates a `StoppingPolicy()`.
- **epistemic_market**: Never toggled. Controller always uses `EpistemicMarket()`.
- **evidence_independence**: Never toggled. No operator in benchmarks reads source lineage.
- **counterfactual_lab**: Influence test shows `CounterfactualOperator.propose()` needs hypothesis views. But operator is not registered in benchmarks.
- **sealed_tribunal**: Not tested in either regime.
- **ontology_forge**: Not registered in benchmarks.
- **federated_memory**: Not tested.
- **trajectory_collection**: Records data but does not change behavior.
- **value_model**: Not used in benchmarks.

## 14.1 Mechanism Causal Audit Table

| Mechanism | Runtime enabled? | Reads state? | Changes bids? | Changes actions? | Changes state transition? | Changes outcome on scenario? | Ablation disables? | Influence test? | Classification |
|---|---|---|---|---|---|---|---|---|---|
| hypothesis_ecology | YES (ScenarioHypothesisOperator) | YES (views.hypotheses) | YES (entropy-based) | YES (generates hypotheses) | YES (adds hypothesis artifacts) | YES (verified: 0→4 hyps) | YES (flag checked in _build_registry) | YES (projection test) | **CAUSAL** |
| ignorance_ledger | YES (ScenarioAttackOperator) | YES (views.ignorance_items) | YES (ignorance_boost) | YES (generates ignorance items) | YES (adds ignorance artifacts) | YES (verified: 0→8 ign) | YES (flag checked in _build_registry) | YES (bid boost, stopping) | **CAUSAL** |
| self_model | YES (views.self_model in all operators) | YES | YES (scales bid by p_success) | NO | NO | NO (identical behavior when ablated*) | NO (flag not checked) | YES (bid reduction) | **NON_CAUSAL_SCAFFOLD** |
| stopping_policy | YES (StoppingPolicy.evaluate()) | YES | NO | YES (can halt episode) | YES (can stop early) | NO (never triggers in practice*) | NO (flag not checked) | YES (stop/continue) | **NON_CAUSAL_SCAFFOLD** |
| epistemic_market | YES (EpistemicMarket.select()) | YES | N/A (IS the bidder) | YES (selects action) | YES (determines sequence) | Untested | NO (flag not checked) | NO | **NON_CAUSAL_SCAFFOLD** |
| evidence_independence | NO (no operator reads lineage) | NO | NO | NO | NO | NO | NO | NO | **NON_CAUSAL_SCAFFOLD** |
| counterfactual_lab | NO (operator not registered) | YES (when present) | YES (when present) | YES (when present) | YES (when present) | NO (not in benchmarks) | NO | YES (proposal test) | **NON_CAUSAL_SCAFFOLD** |
| ontology_forge | NO (operator not registered) | N/A | N/A | N/A | N/A | NO | NO | NO | **NON_CAUSAL_SCAFFOLD** |
| sealed_tribunal | NO (not in benchmarks) | N/A | N/A | N/A | N/A | NO | NO | NO | **NON_CAUSAL_SCAFFOLD** |
| federated_memory | NO (not in benchmarks) | N/A | N/A | N/A | N/A | NO | NO | NO | **NON_CAUSAL_SCAFFOLD** |
| trajectory_collection | YES (records steps) | YES | NO | NO | NO | NO (observational only) | NO | YES (feature capture) | **OBSERVATIONAL** |
| value_model | NO (not in benchmarks) | N/A | N/A | N/A | N/A | NO | NO | NO | **NON_CAUSAL_SCAFFOLD** |

*self_model bid-scaling does not change operator relative ranking because all operators use the same success rate.
*stopping_policy thresholds are never met in practice because mock scenarios don't produce enough evidence/claims.

## Summary

- **CAUSAL** (ablation verified): 2 (hypothesis_ecology, ignorance_ledger)
- **NON_CAUSAL_SCAFFOLD** (exists but cannot be ablated via experiments): 8
- **OBSERVATIONAL** (records data, no behavior change): 1

## Phase 14.3 Requirement

To make mechanisms causal, ablation must propagate through:
1. `_build_registry()` — operator presence (already done for 2)
2. `EpistemicController.__init__()` — self_model, stopping_policy, market selection
3. `state.views` propagation — neutral self_model when OFF
4. `operator.propose()` — each operator must read ablation-relevant state fields
