# Campaign V4 Final Report

```
CAMPAIGN: V4
BRANCH: feature/asar-ree-v2
V3 FROZEN AT: cd91d54
V4 BASE SEED: 271828
WORLDS: dev=56, validation=24, locked_test=40
REGIMES: 8 (exploration deficit, evidence deficit, discrimination deficit,
         integration deficit, misleading evidence, hidden alternative,
         source dependency, low resolvability)
```

## Primary Scientific Question

> WHEN IS ADAPTIVITY ACTUALLY NECESSARY?

## Answer

Adaptivity is necessary when epistemic regimes are heterogeneous
(AdaptivityGap = 0.096), but current transparent models cannot exploit
this gap. The gap exists in principle but is not practically accessible
with available feature representations and model classes.

---

## Phase 21: Adaptive Necessity — ESTABLISHED

| Metric | Value |
|---|---|
| Best global fixed sequence | B1_extended = 0.527 |
| State-conditioned oracle | 0.622 |
| AdaptivityGap | **0.096** |
| Distinct oracle-optimal sequences | 4 |
| Dominant sequence share | 66.1% |

### Regime-Specific Findings

- Regime A (exploration deficit): `explore_first` optimal (7/7)
- Regime C (discrimination deficit): `full_explore` optimal (7/7)
- Regimes B, D, E, F, G, H: B1_extended optimal (majority)

### Temporal Complementarity (V4 Replication)

| Pair | Complementarity | Relation |
|---|---|---|
| gen_hyp -> retrieve | +0.162 | synergy |
| gen_hyp -> attack | +0.137 | synergy |
| gen_hyp -> reason | +0.137 | synergy |
| gen_hyp -> gen_hyp | -0.050 | interference |
| retrieve -> retrieve | -0.002 | redundancy |

Direction of V3 complementarity effects **replicates** on V4 heterogeneous
regimes. Magnitudes are smaller because V4 includes regimes where
hypothesis generation has lower marginal value.

### Order Effects

Largest: gen_hyp -> retrieve vs retrieve -> gen_hyp = 0.083 (hyp-first better).
Most pairs show near-commutativity on 2-step sequences.
Composition effects remain larger than ordering effects.

---

## Phase 22: LLM-in-the-Loop — PROTOCOL DEFINED

### Infrastructure Status

| Component | Status |
|---|---|
| LLMClientProtocol | EXISTS |
| OpenAI Responses API adapter | EXISTS |
| Chat Completions adapter (local models) | BUILT |
| Cognitive operators | EXIST (accept LLMClientProtocol) |
| Capability gate protocol | DEFINED (10 primitive tests) |
| Leakage prevention | SPECIFIED |

### Execution Status

**REQUIRES RUNNING MODEL SERVER.** No local model was available for
execution. All V3-V4 findings remain simulator-specific until LLM-in-loop
validation is completed.

### Primitive Capability Gate

10 tests required before architecture comparisons:
interpret evidence, generate hypothesis, generate alternative, derive
implication, identify contradiction, attack hypothesis, identify missing
info, targeted retrieval, synthesize conclusion, structured output.

---

## Phase 23: Sequence-Aware Metacognitive Policy — NOT SUPPORTED

### Training

- 26 rules learned from 56 dev worlds
- Motif distribution: EXPAND (28), EXPLORE (16), FULL_EXPLORE (8), DISCRIMINATE (4)

### Regret Analysis

| Strategy | Quality | Regret |
|---|---|---|
| Oracle (state-conditioned) | 0.588 | 0.000 |
| Best fixed (FULL_EXPLORE) | 0.518 | 0.070 |
| **Learned policy** | **0.323** | **0.264** |

### GO Criterion

| Criterion | Status |
|---|---|
| Policy quality > fixed quality | **FAIL** (0.323 < 0.518) |
| Policy regret < fixed regret | **FAIL** (0.264 > 0.070) |
| Distinct trajectories >= 3 | **FAIL** (only 2) |
| Selection entropy > 0.5 | **FAIL** (0.377) |

**ADAPTIVE METACOGNITION: NOT SUPPORTED**

### But: Sequence Motifs Categorically Beat Primitives

| Comparison | Win Rate |
|---|---|
| Sequence motif vs repeated primitive | **100%** (56/56) |

The concept of cognitive motifs is correct — sequences are categorically
better than primitives. But adaptively selecting the right motif from state
features fails with transparent models.

### Locked Test Confirmation

| Strategy | Locked Quality | Locked Regret |
|---|---|---|
| Oracle | 0.584 | 0.000 |
| Best fixed | 0.510 | 0.074 |
| Learned policy | 0.323 | 0.261 |

---

## Phase 24: Prior-Art Audit and Paper Decision

### Novelty Assessment

| Contribution | Novel? | Strength |
|---|---|---|
| A. Temporal epistemic complementarity | YES | MODERATE |
| B. Greedy metacognitive failure | NO | WEAK (known from RL) |
| C. State-dependent cognitive motifs | YES | MODERATE |
| D. Epistemic sequence benchmark | YES | **STRONG** |
| E. Minimal architecture finding | YES | MODERATE |

### Paper Decision

| Paper Level | Justified? | Missing |
|---|---|---|
| Controlled-mechanism paper | **YES** | — |
| Stronger agent paper | NO | LLM-in-loop, working adaptive policy |
| Conference-level claim | NO | + external validation |

### Recommended Central Claim

**D — Epistemic Sequence Benchmark**: A controlled environment for
measuring the temporal complementarity of cognitive operations in
epistemic research. The benchmark reveals that:
1. Cognitive operations exhibit measurable non-additive value
2. Greedy primitive-level scheduling fails when operations are complementary
3. Simple fixed sequences outperform complex adaptive architectures
4. The gap between oracle-adaptive and best-fixed is modest (~10%)

---

## Hypothesis Verdicts (All Canonical IDs)

| ID | Statement | V4 Verdict |
|---|---|---|
| H-REE-01 | Self-model > verbal confidence | INCONCLUSIVE |
| H-REE-02 | Ignorance predicts failure | PARTIALLY_SUPPORTED |
| H-REE-03 | Sealed tribunal preserves minority | INCONCLUSIVE |
| H-REE-04 | Ontology branching aids recovery | INCONCLUSIVE |
| H-REE-05 | Epistemic Market quality/compute | **NOT_SUPPORTED** |
| H-REE-06 | Provenance clustering | INCONCLUSIVE |
| H-REE-07 | Counterfactual reasoning | INCONCLUSIVE |
| H-REE-08 | Offline consolidation | INCONCLUSIVE |
| H-REE-09 | Full REE > additive sum | **NOT_SUPPORTED** |
| H-REE-10 | Hypothesis ecology | **PARTIALLY_SUPPORTED** (not independent) |
| H-REE-11 | Temporal complementarity | **SUPPORTED** (replicates V3->V4) |
| H-REE-12 | Cross-architecture ecology | **NOT_SUPPORTED** |
| H-REE-13 | Greedy control failure | **SUPPORTED** |
| H-REE-14 | Adaptive necessity | **SUPPORTED** (gap=0.096) |
| H-REE-15 | LLM temporal complementarity | **UNTESTED** |
| H-REE-16 | Sequence-aware value | **PARTIALLY_SUPPORTED** (motifs > primitives 100%) |
| H-REE-17 | Adaptive motif control | **NOT_SUPPORTED** (policy fails) |
| H-REE-18 | Cross-level transfer | **UNTESTED** |

---

## Answers to Final Questions

1. **Does the benchmark genuinely require adaptive cognition?**
   YES. AdaptivityGap = 0.096. Different regimes have different optimal sequences.

2. **What is the Adaptivity Gap?**
   0.096 (modest but real). Oracle gains ~18% relative improvement over best fixed.

3. **How diverse are oracle-optimal cognitive sequences?**
   4 distinct sequences. B1_extended dominates (66.1%) but explore_first (16.1%)
   and full_explore (12.5%) are regime-specific alternatives.

4. **Which operation pairs exhibit order effects?**
   gen_hyp -> retrieve vs retrieve -> gen_hyp: 0.083 (hyp-first better).
   Most pairs near-commutative on 2-step sequences.

5. **Which sequences exhibit complementarity?**
   All gen_hyp pairs show synergy (+0.137 to +0.162). gen_hyp -> gen_hyp
   shows interference (-0.050).

6. **Do these effects persist with LLM-based cognition?**
   UNTESTED. Infrastructure built but no model available.

7. **Does attack remain state-dependent?**
   YES. Attack alone = 0.000. Attack synergizes with gen_hyp (+0.137) only
   when hypotheses exist.

8. **Can epistemic state predict optimal cognitive motifs?**
   POORLY. Transparent rule-based policy achieves only 0.323 vs fixed 0.518.
   Features are insufficient or model class too simple.

9. **Does motif-level prediction beat primitive-action prediction?**
   YES categorically. Motif sequences win 100% against repeated best primitive.

10. **Does adaptive motif control beat the best fixed policy?**
    NO. The learned policy (0.323) dramatically underperforms FULL_EXPLORE (0.518).

11. **Does a Self Model add anything?**
    INCONCLUSIVE. Self-model ablation remains non-causal in all campaigns.

12. **What is the new minimal effective architecture?**
    FULL_EXPLORE: gen_hyp -> retrieve -> gen_hyp -> retrieve -> reason.
    Quality 0.518 at 2500 tokens. B1_extended (0.527 at 3500 tokens) is
    marginally better but costlier.

13. **Which findings survive static-real/live validation?**
    UNTESTED. No external validation was performed.

14. **Which claims remain simulator-specific?**
    ALL claims are simulator-specific until LLM-in-loop or external
    validation is completed.

15. **What is genuinely novel relative to 2024-2026 prior art?**
    The strongest novel contribution is the **epistemic sequence benchmark**
    itself — a controlled environment for counterfactual evaluation of
    cognitive operation sequences.

16. **Is there enough evidence for a paper?**
    YES for a controlled-mechanism paper. NOT YET for a stronger agent paper.

17. **What should that paper's central claim actually be?**
    "We present EpistemicWorldSimulator, a controlled benchmark for measuring
    the temporal complementarity of cognitive operations in epistemic research.
    Using counterfactual sequence evaluation across 8 epistemic regimes, we
    find that: (1) cognitive operations exhibit measurable non-additive value;
    (2) greedy primitive-level scheduling fails when operations are complementary;
    (3) simple fixed sequences outperform complex adaptive architectures; and
    (4) the gap between oracle-adaptive and best-fixed is real but modest."

---

## Companion Documents

- `ADAPTIVE_NECESSITY_PROTOCOL.md` — Phase 21 protocol and gate
- `ADAPTIVITY_GAP_RESULTS.md` — Phase 21 quantitative results
- `TEMPORAL_COMPLEMENTARITY_V4.md` — Phase 21.8 complementarity matrix
- `NEGATIVE_FINDINGS_V4.md` — All negative results
- `COMPONENT_EVIDENCE_MAP_V4.md` — Final component classification
- `results/` — Machine-readable JSON/JSONL data
- `../campaign_v3/HYPOTHESIS_CANONICAL_MAPPING.md` — Canonical hypothesis IDs

---

## Open Questions for Future Work

1. Can a nonlinear model (tree, neural) exploit the adaptivity gap?
2. Do temporal complementarity effects survive with LLM cognition?
3. Does the epistemic benchmark transfer to real research tasks?
4. Can richer state features (uncertainty estimates, information-theoretic)
   improve motif prediction?
5. Would regimes with larger information structure differences produce
   a larger adaptivity gap?
