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

## Campaign Summary

### Campaign V1 (SHA: 120a576) — Frozen
Mock operators with substring matching. Non-discriminative. Negative baseline.

### Campaign V2 (SHA: c94e9a9) — Frozen
Semantic benchmark. B1 (0.594) > Full REE (0.356). Hypothesis ecology d~1.4.

### Campaign V3 (SHA: cd91d54) — Frozen
Temporal complementarity. B1_extended (0.672) = best. gen_hyp+reason = +0.228.

### Campaign V4 (Current)
Adaptive necessity established (gap=0.096). Motif policy NOT SUPPORTED.
Controlled paper JUSTIFIED. LLM-in-loop UNTESTED.

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
| LLM effects untested | — | Critical gap |

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
| H-REE-15, 18: LLM transfer | UNTESTED |

## Next Steps (Future Work)

1. **LLM-in-the-loop validation** — Run cognitive operations with actual LLM (ChatCompletionsLLMClient is built). Test whether temporal complementarity survives.
2. **Nonlinear motif selector** — Test tree/neural models for motif prediction. Current transparent rules fail.
3. **Richer state features** — Information-theoretic features, uncertainty estimates, evidence graph statistics.
4. **External validation** — Static evidence packs and live research with blinded architecture IDs.
5. **Paper preparation** — Controlled-mechanism paper on epistemic sequence benchmark is justified.
