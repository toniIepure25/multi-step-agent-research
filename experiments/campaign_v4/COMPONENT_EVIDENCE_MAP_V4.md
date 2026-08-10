# Component Evidence Map — V4 (Updated)

Final classification across Campaigns V1-V4.

## Classification

| Component | V3 Status | V4 Status | Key V4 Evidence |
|---|---|---|---|
| Hypothesis Generation | CORE_SUPPORTED | **CORE_SUPPORTED** | Required for all quality > 0. Synergy hub (+0.137 to +0.162 with all partners) |
| Reasoning | CORE_SUPPORTED | **CORE_SUPPORTED** | Reason alone = 0.000, but with hyp + evidence = critical quality driver |
| Multiple Hypotheses | CORE_SUPPORTED | **CORE_SUPPORTED** | FULL_EXPLORE (2 hyp) = 0.518 vs EXPLORE (1 hyp) = 0.323 |
| Evidence Retrieval | CORE_SUPPORTED | **CORE_SUPPORTED** | Required for reasoning to have inputs |
| Sequence Structure | CORE_SUPPORTED | **CORE_SUPPORTED** | Order effect up to -0.083. Composition effect up to +0.310 (V3) |
| Cognitive Options/Motifs | CONDITIONALLY_USEFUL | **SUPPORTED_CONCEPT** | Sequence motifs beat primitives 100% of time. But adaptive selection fails |
| Attack Hypothesis | CONDITIONALLY_USEFUL | **CONDITIONALLY_USEFUL** | Still state-dependent (0.000 early, synergy late) |
| Ignorance Discovery | CONDITIONALLY_USEFUL | **CONDITIONALLY_USEFUL** | Via attack; value depends on hidden variables |
| Adaptive Motif Selection | NEW | **NOT_SUPPORTED** | Policy (0.323) << fixed (0.518). Features insufficient |
| Epistemic Market | HARMFUL | **HARMFUL** | Confirmed. Primitive greedy scheduling = anti-calibrated |
| Self-Model | NO_BENEFIT | **INCONCLUSIVE** | Ablation still non-causal. Potentially useful with real LLM |
| Stopping Policy | NO_BENEFIT | **NO_BENEFIT** | No causal effect in any campaign |
| Persistent Hypothesis Ecology | USEFUL_IN_COMBINATION | **NOT_INDEPENDENTLY_USEFUL** | Only rescues Full REE from its own scheduler failure |
| Ontology Forge | INCONCLUSIVE | **INCONCLUSIVE** | Not implemented in simulator |
| Sealed Tribunal | INCONCLUSIVE | **INCONCLUSIVE** | Not implemented in simulator |
| Federated Memory | INCONCLUSIVE | **INCONCLUSIVE** | Not implemented in simulator |

## Minimal Effective Architecture (Updated V4)

```
FULL_EXPLORE motif:
  generate_hypothesis
  -> retrieve
  -> generate_hypothesis
  -> retrieve
  -> reason
```

Quality: 0.518 (V4 dev), competitive with B1_extended (0.527).

For regimes where B1_extended is not optimal (A, C), FULL_EXPLORE or
explore_first would be better. But we cannot reliably predict which regime
we're in from state features alone.

## Quality-Compute Frontier (V4 Locked Test)

| Strategy | Quality | Tokens |
|---|---|---|
| Oracle (state-conditioned) | 0.584 | variable |
| Best fixed (FULL_EXPLORE) | 0.510 | 2500 |
| B1_extended | ~0.527 | 3500 |
| Learned policy | 0.323 | variable |
| Primitive (best single action) | 0.273 | 500 |
