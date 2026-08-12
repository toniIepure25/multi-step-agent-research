# Next Steps

> See also: [v0-canonical-architecture.md](../docs/architecture/v0-canonical-architecture.md) for exact v0 scope and success criteria.
> Runtime baseline: Python 3.11+ only.
> v0 naming is frozen.

## v0 Build Order (Phase 1)

| # | What | Layer | Status |
|---|------|-------|--------|
| 1 | Config loader | `common` | completed |
| 2 | ID generation + logging | `common` | completed |
| 3 | `WorkingMemory` | `memory` | completed |
| 4 | `SimplePlanner` | `planning` | completed |
| 5 | `WebSearchExecutor` | `execution` | completed |
| 6 | `SimpleSynthesizer` | `deliberation` | completed |
| 7 | `EvidenceChecker` | `verification` | completed |
| 8 | `ExperimentLogger` | `evaluation` | completed |
| 9 | `SequentialOrchestrator` | `orchestration` | completed |
| 10 | Integration test | tests | completed |
| 11 | Live run | — | not started |
| 12 | Benchmark questions | `evaluation` | not started |
| 13 | Baseline metrics | `evaluation` | not started |

## ASAR-REE Implementation Status

All REE phases (0-9) and scientific validation (10-24) are **completed**.

| Phase | Description | Status |
|-------|-------------|--------|
| 0-9 | Full REE Architecture | completed |
| 10-13 | Campaign V1 (methodological negative baseline) | completed |
| 14-16 | Campaign V2 (semantic benchmark, causal ablation) | completed |
| 17-20 | Campaign V3 (temporal complementarity, motifs) | completed |
| 21-24 | Campaign V4 (adaptive necessity, LLM protocol, policy, paper) | completed |
| 25-28 | Campaign V5 (LLM transfer, real-evidence, prior art, paper) | **COMPLETE** |
| 30-43 | Campaign V6 (causal closed-loop factorial validation) | **IN PROGRESS** |

## Campaign Summary

### Campaign V1 (SHA: 120a576) — Frozen
Mock operators with substring matching. Non-discriminative. Negative baseline.

### Campaign V2 (SHA: c94e9a9) — Frozen
Semantic benchmark. B1 (0.594) > Full REE (0.356). Hypothesis ecology d~1.4.

### Campaign V3 (SHA: cd91d54) — Frozen
Temporal complementarity. B1_extended (0.672) = best. gen_hyp+reason = +0.228.

### Campaign V4 (SHA: 2f63cf9) — Frozen
Adaptive necessity established (gap=0.096). Motif policy NOT SUPPORTED.
Controlled paper JUSTIFIED. LLM-in-loop UNTESTED.

### Campaign V5 (COMPLETE)
LLM transfer and real-evidence validation via remote Mac Studio (`inference.ccrolabs.com`).
Models: gemma3:27b-it-qat (primary), llama3.2-vision:11b-instruct-q8_0 (transfer).
Phase 25: Both models VALID_EXPERIMENTAL_SUBSTRATE. Phase 26: R2 complementarity REPLICATED (+0.111), R5 attack timing REPLICATED (+0.276). Phase 27: greedy_primitive (0.718) outperforms sequences on real evidence.
H-REE-15: PARTIALLY_SUPPORTED. H-REE-18: NOT_SUPPORTED.
Paper decision: CONTROLLED_MECHANISM / LLM PAPER (Level 2 evidence for complementarity/attack timing).

## Headline Findings Across All Campaigns

| Finding | Campaign | V6 Status | Strength |
|---------|----------|-----------|----------|
| B1_extended > Full REE | V2-V4 | Unchanged | Strong, replicated |
| gen_hyp + reason complementarity | V3-V4 | **OVERTURNED by V6** | Was strong; interaction=0 under budget controls |
| Hypothesis generation is core | V2-V6 | **STRENGTHENED** | Dominant main effect in V6 factorial |
| Epistemic Market is harmful | V2-V4 | Unchanged | Strong, replicated |
| Attack is state-dependent | V3-V5 | **OVERTURNED by V6** | Effect=0.019 under matched budget |
| Order effects exist but modest | V3-V4 | Unchanged (V5 not replicated) | Weak |
| Adaptivity gap = 0.096 | V4 | Unchanged | Moderate |
| Motif policy fails | V4 | Unchanged | Negative, important |
| LLM complementarity replicates | V5 | **Reinterpreted** | Was main effect, not interaction |
| LLM attack timing replicates | V5 | **OVERTURNED** | Compute confound |
| Real-evidence transfer weak | V5 | Unchanged | Negative, important |
| Reflection adds no value | V5 | Unchanged (was broken) | Negative |
| **Factorial complementarity = 0** | **V6** | NEW | Critical negative result |
| **Attack timing confounded** | **V6** | NEW | Critical negative result |

## Hypothesis Verdicts (Updated Post-V6)

| ID | Pre-V6 | Post-V6 |
|---|---|---|
| H-REE-05: Epistemic Market | NOT_SUPPORTED | NOT_SUPPORTED |
| H-REE-09: Full REE > sum | NOT_SUPPORTED | NOT_SUPPORTED |
| H-REE-10: Hypothesis ecology | PARTIALLY_SUPPORTED | PARTIALLY_SUPPORTED |
| H-REE-11: Temporal complementarity | **SUPPORTED** | **NOT_SUPPORTED** (V6 factorial = 0) |
| H-REE-12: Cross-arch ecology | NOT_SUPPORTED | NOT_SUPPORTED |
| H-REE-13: Greedy control failure | **SUPPORTED** | Weakened (unclear under budget controls) |
| H-REE-14: Adaptive necessity | **SUPPORTED** | **SUPPORTED** (oracle gap real) |
| H-REE-16: Sequence > primitive | PARTIALLY_SUPPORTED | Weakened (may be main effect) |
| H-REE-17: Adaptive motif control | NOT_SUPPORTED | NOT_SUPPORTED |
| H-REE-15: LLM complementarity | PARTIALLY_SUPPORTED | **NOT_SUPPORTED** |
| H-REE-18: Cross-level transfer | NOT_SUPPORTED | NOT_SUPPORTED |
| H-REE-19: Budget-controlled comp. | — | **NOT_SUPPORTED** (interaction = 0) |
| H-REE-20: Semantic mediation | — | **PARTIALLY_SUPPORTED** (retrieval yes, accuracy mixed) |
| H-REE-21: Closed-loop causality | — | **PARTIALLY_SUPPORTED** |
| H-REE-22: Attack timing (matched) | — | **NOT_SUPPORTED** (effect = 0.019) |
| H-REE-23: Exogenous transfer | — | **PARTIALLY_SUPPORTED** (retrieval transfers, performance mixed) |

### Campaign V6 — COMPLETE
Phase 1: Budget-matched factorial validation. Factorial interaction = 0.000. Attack timing = 0.019.
Phase 2: Semantic intervention on SciFact (N=100) and HotpotQA (N=100).
Key: Semantic content causally affects retrieval but improved retrieval does not universally help.

## EXPERIMENTAL DEVELOPMENT COMPLETE

All preregistered hypotheses executed. No Campaign V7.

## Next Steps (Paper Only)

1. **Freeze V6 results** — commit all V6 completion artifacts.
2. **Rewrite paper** — methodology + mixed results paper.
3. **Target venue** — NeurIPS D&B or EMNLP findings.
4. **No further experiments** — results are final.
