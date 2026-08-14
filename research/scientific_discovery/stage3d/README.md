# Stage 3D — README

## Status: IN_PROGRESS (deterministic benchmarks complete, LLM inference pending)

---

## Purpose

Determine whether Stage 3C pilot results survive:
- Larger sample sizes (N=50-200 worlds)
- Harder scientific problems (distributional generator)
- More diverse generated hypotheses
- Two model substrates (Gemma primary, Llama transfer)
- External validation benchmarks (FalsifyBench)
- Non-ceiling experiment design

---

## Key Findings

### CORRECTIONS from Stage 3C
1. **Oracle regret: Stage 3C "100%" was wrong → actual 80%** (measurement error)
2. JSD regret was tautologically measured in JSD-space
3. Correct formula: Regret = OracleIG(best) - OracleIG(policy)

### NEW RESULTS (deterministic, no LLM needed)
1. **Approx-EIG (E4) ≈ JSD** — not significantly better (p=0.14)
2. **SD-H3C SUPPORTED** — sequential planning adds value (p<0.000003)
3. **SD-H9C NOT_SUPPORTED** — complexity moderation doesn't replicate
4. **Distributional generator**: 200 worlds, 73% JSD-Oracle agreement (healthier)

### PENDING (requires LLM inference)
1. SD-H4 scaled (50 worlds, SELF/EXT pairing)
2. Capability gate scaled (C1-C7 on diverse tasks)
3. FalsifyBench external validation
4. Generative × Active at scale
5. SD-H2 hypothesis ecology

---

## Files in this directory

| File | Contents |
|------|----------|
| README.md | This file |
| PRIOR_ART_DELTA_STAGE3D.md | Comparison with FalsifyBench, Co-Scientist, etc. |
| ORACLE_REGRET_AUDIT.md | Corrected regret formula and Stage 3C reclassification |
| STAGE4_NOVELTY_GATE.md | What Stage 4 must test beyond Wang & Buehler (2026) |
| PREREGISTRATION.md | Frozen parameters for Stage 3D confirmatory inference |
| SD_H4_SCALED_PROTOCOL.md | Self-correction protocol (50 worlds) |
| SD_H3C_RESULTS.md | Sequential design benchmark (N=200) |
| SD_H9C_RESULTS.md | Complexity moderation test (NOT_SUPPORTED) |
| FALSIFYBENCH_INTEGRATION.md | External validation feasibility |
| DISTRIBUTIONAL_WORLD_GENERATOR_SPEC.md | Parametric world generation |
| NEGATIVE_FINDINGS.md | Honest negative results |

---

## Starting SHA: c43bac9
## Branch: feature/asar-ree-v2
