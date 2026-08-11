# Phase 26 — LLM-in-the-Loop Sequence Replication

**Campaign:** V5
**Status:** BLOCKED — Depends on Phase 25 model availability
**Date:** 2026-08-10

## Protocol

### Agent-Visible vs Evaluator-Only Boundary

| Boundary | Items |
|----------|-------|
| **Agent-visible** | Task question, current evidence, current hypotheses, current assumptions, visible ignorance, previous cognitive artifacts, requested operation |
| **Evaluator-only** | True hypothesis, hidden regime, oracle action, oracle sequence, oracle value, latent evidence graph, future evidence, locked-test label, quality target |

### Leakage Prevention

The LLM prompt construction in `run_phases25_26.py`:
- Never includes `world.true_hypothesis_id`
- Never includes regime labels
- Never includes oracle sequences
- Never includes `information_value` from evidence items
- Evidence `supports`/`contradicts` fields are NOT shown to the agent

### Preregistered Replication Tests

| Test | V3/V4 Finding | Replication Criterion |
|------|---------------|----------------------|
| **R1: Sequence superiority** | B1_extended > single primitive | Direction: multi-step > single-step |
| **R2: Complementarity** | gen_hyp→retrieve synergy +0.162 | Direction: positive synergy for gen_hyp→retrieve |
| **R3: Interference** | gen_hyp→gen_hyp interference -0.050 | Direction: negative interaction for repeated gen_hyp |
| **R4: Order effects** | Forward B1 > Reversed B1 (+0.223) | Direction: forward > reversed |
| **R5: Attack timing** | Attack late > Attack early | Direction: late > early |
| **R6: Fixed beats greedy** | B1_extended > primitive greedy | Direction: fixed sequence > greedy schedule |

### Replication Status Categories

| Status | Definition |
|--------|-----------|
| REPLICATED | Same direction, comparable effect size, CI excludes zero |
| PARTIALLY_REPLICATED | Same direction, smaller effect, or marginal CI |
| NOT_REPLICATED | Different direction or effect indistinguishable from zero |
| INCONCLUSIVE | Insufficient statistical power or execution failures |

### Sequences Under Test

| Name | Sequence |
|------|----------|
| B1_extended | retrieve → gen_hyp → retrieve → gen_hyp → reason → retrieve → reason |
| single_retrieve | retrieve |
| single_gen_hyp | generate_hypothesis |
| explore | gen_hyp → retrieve |
| discriminate | retrieve → gen_hyp → reason |
| reversed_B1 | reason → gen_hyp → retrieve → gen_hyp → retrieve |
| attack_early | attack_hypothesis |
| attack_late | retrieve → gen_hyp → retrieve → gen_hyp → reason → attack_hypothesis |

### Worlds

- 8 V4 epistemic regimes × 3 seeds = 24 worlds per sequence
- Total evaluations: 24 × 8 sequences = 192

### Cost Recording

For each evaluation, record:
- `input_tokens`
- `output_tokens`
- `model_calls`
- `latency_ms`
- `wall_time_ms`

## 26.5 — Empirical Operator Reliability

Estimate from Phase 25 gate data + Phase 26 sequence data:

```
P(operation succeeds | operation, state, regime, model)
```

Scientific questions:
1. Is Reason uniformly reliable across regimes?
2. Is Attack only useful late because of epistemic timing, or because the LLM cannot execute it early?
3. Does hypothesis generation quality decline after repeated generation?
4. Does retrieval-query quality depend on current hypothesis structure?

## 26.6 — Structural Value vs Execution Reliability

For each sequence A → B, decompose:

```
ExpectedSequenceValue ≈ StructuralValue × ExecutionReliability - Cost
```

This is an analysis decomposition, not an assumed formula.

## 26.7 — Core Scientific Test

**H-REE-15: LLM Temporal Complementarity**

> Temporal complementarity is a property of the epistemic task structure
> rather than merely the scripted simulator implementation.

Verdict criteria:
- SUPPORTED: ≥4/6 replication tests replicate
- PARTIALLY_SUPPORTED: 2-3/6 replicate
- NOT_SUPPORTED: ≤1/6 replicates

## Current Status

**BLOCKED.** Awaiting model server availability.

All infrastructure is ready:
- `ChatCompletionsLLMClient` tested and functional
- Prompt templates defined for all operations
- Scoring rubrics implemented
- Worlds generated
- Results paths configured

Execute `run_phases25_26.py` once a model server is available.
