# Stage 3 Preregistration — Generative Scientist + Active Discovery

**Frozen:** 2026-08-14  
**Status:** DEV (not yet locked)

---

## Research Questions

### SD-H3B — Robust Discriminative Experiment Selection
A discrimination-oriented policy reduces oracle regret relative to random,
cheap, and confirmation-seeking policies under noisy, costly, multi-step
scientific environments.

### SD-H4 — Self-Correction of Self-Generated Hypotheses
The system can abandon hypotheses it generated itself after decisive 
falsification, without significant self-authorship bias.

### SD-H9 — Active Scientific Control
A policy combining falsification-oriented hypothesis challenge with
discriminative experiment selection improves scientific recovery under
endogenous evidence acquisition.

---

## Hardened Stage 2 Worlds

| World Type | Difficulty Source | N per seed |
|---|---|---|
| noisy_predictions | Agent predictions miscalibrated | 1 |
| cost_information_tradeoff | Best discrimination costs 5× | 1 |
| multi_hypothesis | 5 hypotheses in clusters | 1 |
| deceptive_confirmation | Cheap experiments non-discriminating | 1 |
| partial_identifiability | No experiment is decisive | 1 |

## Active Science Worlds

| World Type | Key Feature | N per seed |
|---|---|---|
| active_confirmation_trap | Cheap confirms vs costly discriminates | 1 |
| active_reverse_causality | Only intervention reveals direction | 1 |
| active_null | No causal effect; converge to null | 1 |

---

## Policies

### Hardened Stage 2
- E0: Random
- E2: Confirmation Seeker
- E3: Greedy JSD Discrimination (ASAR)
- E5: Oracle (one-step)

### Active Science
- Passive (first available)
- Random
- Confirmation Seeker
- Discrimination (ASAR)

---

## Splits

- **DEV:** seeds 1-20
- **VALIDATION:** seeds 41-60
- **LOCKED:** seeds 61-80

---

## Primary Metrics

### SD-H3B
- Oracle regret (IG_oracle - IG_policy)
- Zero-regret rate (% optimal selections)

### SD-H9
- Recovery accuracy
- Cost to recovery
- Experiments to recovery

### SD-H4 (when LLM integrated)
- Correct abandonment rate
- False abandonment rate
- Self-authorship bias
- Rationalization rate

---

## SESOIs

- SD-H3B: E3 regret < E2 regret by at least 0.05
- SD-H9: Discrimination recovery > random by at least 0.10
- SD-H4: Self-authorship bias < 0.10

---

## Statistical Procedure

- Independent unit: World × Seed
- Paired bootstrap CI (10000 resamples)
- Sign-flip permutation test for p-values
- Family-wise correction if > 3 primary comparisons tested simultaneously

---

## GO Criteria

Stage 3 GO requires:
1. SD-H3B: E3 < E2 regret (non-ceiling)
2. SD-H9: Discrimination > random recovery
3. SD-H4: Self-authorship bias < 0.10 (or honestly documented limitation)
4. No oracle leakage
5. False abandonment controlled
