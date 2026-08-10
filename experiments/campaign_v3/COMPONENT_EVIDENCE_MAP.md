# Component Evidence Map

Final classification of all ASAR-REE architectural components based on
Campaigns V1, V2, and V3. Uses only development/validation/locked-test evidence.

## Classification Key

| Status | Meaning |
|---|---|
| SUPPORTED_GENERAL | Benefits quality across architectures and task families |
| SUPPORTED_CONDITIONAL | Benefits quality only under specific state conditions |
| USEFUL_ONLY_IN_COMBINATION | No independent value; useful only when combined with other components |
| NO_BENEFIT | No measured quality improvement in any tested condition |
| HARMFUL | Reduces quality when active |
| INCONCLUSIVE | Not tested or insufficient data |

## Evidence Map

| Component | Status | V1 | V2 | V3 | Key Evidence |
|---|---|---|---|---|---|
| Hypothesis Generation | **SUPPORTED_GENERAL** | INC | d≈1.4 | CORE | Required for all quality > 0.04. B1 decomposition: removing causes -0.193 |
| Reasoning (consistency scoring) | **SUPPORTED_GENERAL** | INC | — | CORE | Removing causes -0.230. Core quality-producing operation |
| Multiple Hypotheses (>=2) | **SUPPORTED_GENERAL** | INC | — | CORE | 0.573 (2 hyps) vs 0.381 (1 hyp). Enables discriminative reasoning |
| Evidence Retrieval | **SUPPORTED_GENERAL** | INC | — | CORE | Required before hypothesis generation. Removing either retrieve: -0.141 |
| Sequence Structure | **SUPPORTED_GENERAL** | INC | — | CORE | Forward vs reversed: +0.223. Order matters strongly |
| Cognitive Options | **SUPPORTED_CONDITIONAL** | — | — | matches fixed | Matches B1_extended (0.672) but doesn't exceed it. Only 2 distinct trajectories |
| Attack Hypothesis | **SUPPORTED_CONDITIONAL** | INC | crowding | state-dep | Useless early (0.000). Marginal mid (+0.030). Best late (+0.250) |
| Ignorance Discovery | **SUPPORTED_CONDITIONAL** | INC | d≈0.2 | via attack | Only produced by attack operator. Value depends on attack timing |
| Persistent EpistemicState | **USEFUL_ONLY_IN_COMBINATION** | INC | — | — | Required by REE but B1 achieves higher quality without it |
| Hypothesis Ecology (persistent) | **USEFUL_ONLY_IN_COMBINATION** | INC | d≈1.4 | no cross-arch effect | V2 effect is really "enable hypothesis generation." B1+ecology = B1 |
| Epistemic Market (heuristic) | **HARMFUL** | INC | anti-calibrated | 0.324 vs 0.594 | Selects attack 46% of time on states where attack = 0.000 quality |
| Self-Model | **NO_BENEFIT** | INC | non-causal | non-causal | Ablation never properly wired. Cannot distinguish ON from OFF |
| Stopping Policy | **NO_BENEFIT** | INC | non-causal | non-causal | Same issue as self-model |
| DiversityAwareMarket | **NO_BENEFIT** | — | 0.33 vs 0.35 | — | No improvement over heuristic market |
| Ontology Forge | **INCONCLUSIVE** | INC | INC | INC | Not implemented in semantic simulator |
| Sealed Tribunal | **INCONCLUSIVE** | INC | INC | INC | Not implemented in semantic simulator |
| Federated Memory | **INCONCLUSIVE** | INC | INC | INC | Not implemented in semantic simulator |
| Evidence Independence | **INCONCLUSIVE** | INC | INC | INC | Source duplication family exists but no causal ablation |

## Minimal Effective Architecture (REE-Minimal-Empirical)

Based on the evidence, the smallest configuration that retains useful effects:

```
retrieve -> generate_hypothesis -> retrieve -> generate_hypothesis -> reason -> retrieve -> reason
```

This is B1_extended. It requires:
1. Evidence retrieval (from any source)
2. Hypothesis generation (at least 2)
3. Consistency reasoning
4. Correct temporal ordering

It does NOT require:
- Persistent EpistemicState management
- Epistemic Market / any scheduler
- Self-model
- Stopping policy
- Attack operator (in the standard sequence)
- Hypothesis ecology (persistent tracking)

## Quality-Compute Frontier (V3 Locked Test)

| Architecture | Quality | Tokens | Quality/kToken |
|---|---|---|---|
| B1_extended | **0.672** | 3500 | 0.192 |
| hierarchical_options | 0.672 | 5000 | 0.134 |
| B1_full | 0.594 | 2500 | **0.238** |
| round_robin_ree | 0.438 | ~4000 | 0.110 |
| full_ree | 0.324 | ~5000 | 0.065 |
| B0_direct | 0.289 | 1000 | 0.289 |
| full_ree_no_ecology | 0.038 | ~5000 | 0.008 |

B1_full is Pareto-optimal for quality/compute. B1_extended is best absolute quality.
Full REE is dominated on all metrics.
