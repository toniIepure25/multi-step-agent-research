# Paper Claim Ladder — Campaign V5

## Claim Evidence Levels

| Level | Definition | Requirements |
|-------|-----------|-------------|
| LEVEL 0 | Theoretical/conjectural | No empirical support |
| LEVEL 1 | Simulator-supported | V3/V4 deterministic simulator evidence |
| LEVEL 2 | LLM-in-loop replicated | Phase 26 real model inference replicates |
| LEVEL 3 | Static-real replicated | Phase 27 real document evidence replicates |

## Claims and Their Evidence Levels

### LEVEL 2 — LLM-Replicated (Strongest)

| # | Claim | V3/V4 | Phase 26 | Phase 27 | Level |
|---|-------|-------|----------|----------|-------|
| C1 | Temporal complementarity exists between cognitive operations (gen_hyp->retrieve synergy) | SUPPORTED | REPLICATED (+0.111) | WEAK directional | **LEVEL 2** |
| C2 | Attack timing is state-dependent (early=destructive, late=constructive) | SUPPORTED | REPLICATED (+0.276) | N/A | **LEVEL 2** |
| C3 | Sequence effects are structural (model-invariant) | N/A | CONFIRMED (identical across gemma3/llama3.2) | N/A | **LEVEL 2** |

### LEVEL 1 — Simulator-Only

| # | Claim | V3/V4 | Phase 26 | Phase 27 | Level |
|---|-------|-------|----------|----------|-------|
| C4 | Operation order matters (A->B != B->A) | SUPPORTED | NOT_REPLICATED | NOT_REPLICATED | **LEVEL 1** |
| C5 | Fixed cognitive sequences outperform greedy scheduling | SUPPORTED | INCONCLUSIVE | NOT_REPLICATED | **LEVEL 1** |
| C6 | Long sequences outperform matched primitives | SUPPORTED | INCONCLUSIVE | NOT_REPLICATED | **LEVEL 1** |

### LEVEL 0 — Not Supported

| # | Claim | Status | Level |
|---|-------|--------|-------|
| C7 | Learned adaptive metacognitive control outperforms fixed sequences | NOT_SUPPORTED (H-REE-17) | **LEVEL 0** |
| C8 | Adaptive scheduling is necessary for epistemic tasks | LOW EVIDENCE | **LEVEL 0** |

## Headline Claims for Paper

### Supported at LEVEL 2 (publishable with LLM evidence)
> "Temporal complementarity between cognitive operations is a structural property of epistemic reasoning tasks that persists when operations are executed by real language models."

> "The value of hypothesis attack is strongly state-dependent: destructive when applied before evidence accumulation, constructive when applied after hypothesis formation."

### Supported at LEVEL 1 only (publishable with caveats)
> "Operation ordering effects observed in controlled simulator environments do not straightforwardly transfer to real LLM execution."

### Negative findings (publishable and important)
> "Elaborate multi-step cognitive sequences do not reliably outperform focused single-operation strategies when executed by real models on real documents."

> "Greedy primitive scheduling matches or exceeds structured sequence performance on static real evidence tasks."

## Promotion/Demotion Rules
- No claim may be promoted above its evidence level
- Phase 27 negative results DEMOTE claims, not promote them
- Cross-model invariance STRENGTHENS structural claims
- Identical Phase 26 scores across models confirms structural (not execution) effects
