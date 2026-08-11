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

| Finding | Campaign | Strength |
|---------|----------|----------|
| B1_extended > Full REE | V2-V4 | Strong, replicated |
| gen_hyp + reason complementarity | V3-V4 | Strong, replicated |
| Hypothesis generation is core | V2-V4 | Strong, replicated |
| Epistemic Market is harmful | V2-V4 | Strong, replicated |
| Attack is state-dependent | V3-V4 | Strong, replicated |
| Ecology effect is NOT cross-arch | V3 | Moderate |
| Order effects exist but modest | V3-V4 | Moderate |
| Adaptivity gap = 0.096 | V4 | Moderate |
| Motif policy fails | V4 | Negative, important |
| LLM complementarity replicates | V5 | Strong (model-invariant) |
| LLM attack timing replicates | V5 | Strong (+0.276) |
| Real-evidence sequence effects weak | V5 | Negative, important |
| Reflection adds no value | V5 | Negative |

## Hypothesis Verdicts (Final)

| ID | Verdict |
|---|---|
| H-REE-05: Epistemic Market | NOT_SUPPORTED |
| H-REE-09: Full REE > sum | NOT_SUPPORTED |
| H-REE-10: Hypothesis ecology | PARTIALLY_SUPPORTED |
| H-REE-11: Temporal complementarity | **SUPPORTED** |
| H-REE-12: Cross-arch ecology | NOT_SUPPORTED |
| H-REE-13: Greedy control failure | **SUPPORTED** |
| H-REE-14: Adaptive necessity | **SUPPORTED** |
| H-REE-16: Sequence > primitive | **PARTIALLY_SUPPORTED** |
| H-REE-17: Adaptive motif control | NOT_SUPPORTED |
| H-REE-15: LLM complementarity | **PARTIALLY_SUPPORTED** |
| H-REE-18: Cross-level transfer | NOT_SUPPORTED |

## Next Steps (Future Work)

1. **Paper writing** — Controlled-mechanism / LLM paper is justified (Level 2 evidence for complementarity/attack timing). Frame around operation-pair-specific complementarity rather than general sequence superiority.
2. **Stronger real-evidence validation** — Increase N beyond 14 packs with more diverse/challenging tasks. Current Phase 27 may lack discriminative power.
3. **Nonlinear motif selector** — Test tree/neural models for motif prediction. Current transparent rules fail. Only pursue after preregistered experiment.
4. **Richer state features** — Information-theoretic features, uncertainty estimates, evidence graph statistics.
5. **Phase 29 (optional)** — Learned control only if H-REE-15 upgrades to SUPPORTED, adaptivity gap persists, and enough trajectories exist. H-REE-17 remains NOT_SUPPORTED.
6. **Larger model comparison** — Test with frontier-class models to determine if sequence effects strengthen with model capability.
