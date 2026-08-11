# ICLR Rejection Risk Ranking

## CRITICAL

### Risk 1: LLM "replication" does not test what it claims
**Objection:** Phase 26 quality scores come from the deterministic simulator, not LLM output quality. The LLM generates text but does not affect the measured epistemic state transitions or quality evaluation. "Cross-model consistency" is trivially expected because both models trigger the same simulator state evolution.
**Valid?** Yes. This is a fundamental design limitation.
**Existing evidence:** The design is documented; the identical cross-model scores confirm it.
**Paper-only fix?** Yes — reinterpret the claim. State: "Phase 26 confirms that temporal complementarity effects are structural properties of the epistemic task that persist when cognitive operations are accompanied by real LLM inference." Do NOT claim "LLM replication of complementarity."
**Requires new science?** No, but the claim must be substantially weakened.

### Risk 2: Compute/information fairness violated
**Objection:** Longer sequences use more tokens, retrieve more evidence, and generate more hypotheses. "Complementarity" may simply mean "more compute."
**Valid?** Partially. 2-op pairs vs 1-op singles have ~2× budget difference; multi-op sequences vs singles have ~10× difference.
**Paper-only fix?** Partially — emphasize V4 pairwise comparisons (2× difference) over Phase 26 sequence comparisons (10× difference). Add a fairness table. Acknowledge the confound.
**Requires new science?** Ideally, matched-budget controls. But the V4 2-op data is the closest approximation available.

### Risk 3: Benchmark tautology concern
**Objection:** If only gen_hyp creates hypotheses and quality requires correct hypotheses, then gen_hyp-first sequences must outperform by construction.
**Valid?** Partially. The benchmark design does create a prerequisite relationship. However, the MAGNITUDE of complementarity varies by pair and regime, which is non-trivial.
**Paper-only fix?** Yes — reframe. "The benchmark measures the magnitude and state-dependence of prerequisite-like interactions, not their existence per se."
**Requires new science?** No.

## HIGH

### Risk 4: R6 misimplemented (code duplicate of R1)
**Objection:** The "fixed vs greedy" test was never performed. The reported effect is B1_extended vs best single — identical to R1.
**Valid?** Yes. Clear implementation bug.
**Paper-only fix?** Yes — remove R6 as a separate test. Report 4 replication tests, not 5. Or relabel R6 as "sequence vs best primitive" and note no greedy baseline was tested.

### Risk 5: Phase 27 reflection broken
**Objection:** The reflection condition never executes critique/revise. reflection = direct is an artifact, not a finding.
**Valid?** Yes. Clear implementation bug.
**Paper-only fix?** Yes — remove "reflection adds no value" from negative findings. Report 4 conditions, not 5. Acknowledge the bug.

### Risk 6: Phase 27 "real evidence" is synthetic
**Objection:** Author-curated summaries with author-defined ground truth and keyword scoring ≠ real-evidence transfer.
**Valid?** Yes. The label is misleading.
**Paper-only fix?** Yes — relabel as "curated literature-themed evidence summaries." Downgrade claims accordingly.

### Risk 7: N=14/16 is very small
**Objection:** Phase 26 (N=16) and Phase 27 (N=14) have low statistical power. "INCONCLUSIVE" verdicts may simply reflect underpowered tests.
**Valid?** Yes. Cannot distinguish "no effect" from "undetectable effect."
**Paper-only fix?** Partially — acknowledge power limitations explicitly. Report what power the study has for given effect sizes.

## MEDIUM

### Risk 8: Interference CI crosses zero
**Objection:** gen_hyp→gen_hyp −0.050 is not significant. CI: [−0.136, +0.035].
**Valid?** Yes.
**Paper-only fix?** Yes — downgrade from "established interference" to "directional evidence, not significant."

### Risk 9: No formal hypothesis testing
**Objection:** No p-values, no effect sizes (Cohen's d), no bootstrap CIs, no non-parametric tests.
**Valid?** Yes. ICLR empirical papers typically include more rigorous statistics.
**Paper-only fix?** Yes — compute bootstrap CIs and report Cohen's d for key effects.

### Risk 10: Complementarity definitions inconsistent across campaigns
**Objection:** V3, V4, and V5 use different formulas for "complementarity."
**Valid?** Yes.
**Paper-only fix?** Yes — use one definition in the paper and note variations. Report V4 formula as canonical.

## LOW

### Risk 11: Two models on same hardware ≠ diverse cross-model study
**Objection:** Both models served from same Ollama/Mac Studio, same prompts.
**Paper-only fix?** Yes — qualify language.

### Risk 12: Options/RL terminology already covers "temporal abstraction"
**Objection:** The contribution may be incremental over existing RL theory.
**Paper-only fix?** Yes — discuss the relationship explicitly in related work.
