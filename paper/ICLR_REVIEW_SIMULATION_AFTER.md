# Simulated ICLR Reviews — Post-Hardening

Reviews based on the hardened `main.tex` manuscript, which addresses the critical issues identified in pre-hardening review.

---

## Changes Made Between Reviews

1. **LLM "replication" reinterpreted:** Now states explicitly that the simulator controls quality measurement and the LLM does not affect scores. Claims downgraded from "LLM replication" to "structural persistence under LLM execution."
2. **Resource confound acknowledged:** Equation 1 followed by explicit caveat. Budget fairness discussed in formulation and appendix.
3. **Tautology concern addressed:** Paper now states "magnitude and state-dependence are the non-trivial findings, not the existence of prerequisite structure."
4. **Phase 27 relabeled:** "Curated evidence summaries" not "real evidence." Ground truth construction disclosed.
5. **R6 removed:** No fixed-vs-greedy claim; only 4 replication tests reported.
6. **Reflection bug removed:** Only 4 curated-evidence conditions reported (excluding broken reflection).
7. **Interference downgraded:** Reported as "directional, not significant."
8. **Confidence intervals throughout.** All headline numbers carry CIs.

---

## Reviewer 1 — Mechanistic Reasoning Expert (Post-Hardening)

**Summary:** The hardened paper is significantly more transparent about its limitations. The central methodology (same-state counterfactual evaluation) is presented clearly, and the complementarity results carry proper uncertainty.

**Strengths:**
- Resource confound now explicitly acknowledged. The complementarity definition is clean and consistent (Eq. 1).
- The paper correctly distinguishes "structural persistence" from "LLM replication." This is scientifically honest.
- Negative results are prominent, not buried.

**Weaknesses:**
1. The resource confound remains unsolved — it's now acknowledged but not eliminated. A matched-budget control would strengthen the work considerably.
2. N=16 for LLM experiment is still small. Would like to see power analysis.
3. The complementarity magnitude (+0.162) is real but the practical import for agent design is unclear.

**Overall:** 6 (Marginally above acceptance threshold)

**Confidence:** 4

---

## Reviewer 2 — LLM Agents Expert (Post-Hardening)

**Summary:** Much improved. The paper no longer misleadingly claims "LLM replication" and is transparent that quality scores are simulator-controlled.

**Strengths:**
- Honest reinterpretation of LLM experiments. "Structural persistence" is the correct framing.
- The negative results section is valuable for the community.
- Attack-timing result is intuitive and potentially actionable.

**Weaknesses:**
1. The practical implications remain thin. How should an agent designer use these findings? The paper should discuss actionable design recommendations.
2. Only two LLMs, same backend, same prompts. Remains insufficient for broad claims.
3. If the LLM doesn't affect quality, what is the LLM experiment actually testing? The simulator would produce identical scores with any model or even no model. The experimental value of the LLM phase needs sharper justification.

**Overall:** 5 (Marginally below acceptance threshold)

**Confidence:** 4

---

## Reviewer 3 — Benchmark / Evaluation Expert (Post-Hardening)

**Summary:** Good improvements. R6 bug fixed, reflection removed, curated evidence properly labeled.

**Strengths:**
- Benchmark methodology is clearly presented.
- Transparency about evidence-pack construction.
- The claim ladder (Table 4) is excellent for understanding evidence boundaries.

**Weaknesses:**
1. Still no held-out test set for the benchmark. All results are on the same worlds used during development.
2. Quality metric is still a composite with unexplored sensitivity. One figure showing complementarity under alternative weightings would help.
3. N=14 curated evidence is very small. The "non-transfer" finding could simply be low power.

**Overall:** 6 (Marginally above acceptance threshold)

**Confidence:** 4

---

## Reviewer 4 — Hostile but Fair (Post-Hardening)

**Summary:** The paper is now more honest, but the fundamental contribution question remains.

**Strengths:**
- Much harder to reject on technical grounds. Claims are properly scoped.
- Negative findings genuinely useful.
- Budget fairness acknowledged.

**Weaknesses:**
1. **The contribution may be too thin for ICLR main.** The paper discovers that in its own benchmark, hypothesis generation helps subsequent operations. This is a property of the benchmark design. What is the new ML knowledge?
2. **The paper hedges everywhere.** Every finding has a qualifier. While scientifically correct, this makes the paper read as "we tried things and most didn't work."
3. **No comparison to existing agent benchmarks.** Even a preliminary evaluation on GAIA or HotpotQA would strengthen external validity.

**Overall:** 4 (Below acceptance threshold — contribution too thin)

**Confidence:** 3

---

## Score Summary

| Reviewer | Pre-Hardening | Post-Hardening | Change |
|----------|-------------|---------------|--------|
| R1 (Mechanistic) | 5 | 6 | +1 |
| R2 (LLM Agents) | 4 | 5 | +1 |
| R3 (Benchmark) | 4 | 6 | +2 |
| R4 (Hostile) | 3 | 4 | +1 |
| **Mean** | **4.0** | **5.25** | **+1.25** |

## Post-Hardening Meta-Review

### Likely consensus
The paper has improved significantly in honesty and transparency. R1 and R3 are now at borderline accept. R2 is close. R4 remains skeptical about contribution weight.

### Main accept arguments
1. Methodology is genuinely novel and correctly presented.
2. Transparency about limitations is exemplary.
3. Negative findings have community value.

### Main reject arguments
1. Contribution may be too thin — the paper discovers properties of its own benchmark.
2. LLM experiments are structurally trivial (simulator controls quality regardless of model).
3. No external validation on existing benchmarks.

### Predicted score range
4–6 (mean 5.25). Borderline.

### Most likely decision
**Borderline — could go either way depending on reviewer discussion.** The paper is now technically defensible but the contribution weight is the remaining concern. Champion reviewer (R1 or R3) would need to advocate strongly.

### Key question for AC
> Is a well-executed controlled benchmark with negative results enough for ICLR main, or does the community need positive transfer results?
