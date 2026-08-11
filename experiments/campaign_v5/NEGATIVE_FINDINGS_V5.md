# Negative Findings — Campaign V5

## N1: Sequence Superiority Does Not Replicate Cleanly

**Expected:** Multi-step cognitive sequences (B1_extended) should significantly outperform single primitive operations.

**Observed (Phase 26):** B1_extended (0.277) vs single_gen_hyp (0.273) — difference of +0.003, statistically indistinguishable. The explore sequence (0.323) does outperform single primitives, but B1_extended does not.

**Observed (Phase 27):** greedy_primitive (0.718) outperforms all sequence-based conditions including B1_extended (0.691) and FULL_EXPLORE (0.688).

**Interpretation:** The value of long sequences may be an artifact of deterministic scripted operators. When real models execute operations, the per-operation execution noise may exceed the structural sequence benefit.

---

## N2: Order Effects Reverse Direction

**Expected:** B1_extended should outperform reversed_B1, confirming operation order matters.

**Observed (Phase 26):** reversed_B1 (0.327) > B1_extended (0.277) — the predicted direction is REVERSED.

**Interpretation:** B1's specific ordering may not be privileged when operations are executed by real models. The reversed sequence might benefit from later hypothesis generation building on earlier evidence, counteracting the predicted advantage.

---

## N3: Real-Evidence Condition Sensitivity is Low

**Expected:** Different cognitive strategies should produce meaningfully different outcomes on real documents.

**Observed (Phase 27):** Condition means range from 0.688 to 0.718 (range = 0.030). Three domains (biomedical, economics, social_science) show ZERO condition variation.

**Interpretation:** On many real-document tasks, the quality of the LLM's reasoning dominates the cognitive strategy. This is scientifically important: it bounds the practical value of cognitive sequencing research.

---

## N4: Reflection Adds No Value Over Direct Processing

**Expected:** The reflection condition (adding explicit self-evaluation) should improve synthesis quality.

**Observed (Phase 27):** reflection (0.696) = direct (0.696) — identical means across all 14 packs.

**Interpretation:** Self-reflection prompting does not improve outcomes for this class of evidence-synthesis tasks. This is consistent with recent literature questioning the reliability of LLM self-evaluation.

---

## N5: Fixed vs Greedy Remains Inconclusive

**Expected (V3/V4):** Fixed sequences should outperform greedy scheduling.

**Observed (Phase 26):** Effect = +0.003, verdict = INCONCLUSIVE.

**Interpretation:** The fixed-vs-greedy comparison requires more statistical power or more diverse epistemic environments to resolve.

---

## N6: Learned Adaptive Control Remains NOT_SUPPORTED

**Status:** H-REE-17 remains NOT_SUPPORTED. No learned adaptive controller was trained in V5 (by design — V5 is a replication campaign).

---

## Summary

Campaign V5's negative findings are as scientifically important as its positive findings. They bound the practical relevance of cognitive sequencing:

1. **Temporal complementarity exists** (positive) but is **operation-pair-specific**, not a general principle
2. **Elaborate sequences do not outperform focused operations** on real tasks with real models
3. **Cognitive strategy matters less than model capability** on real documents
4. The strongest effects (complementarity, attack timing) are **structural** and model-invariant
