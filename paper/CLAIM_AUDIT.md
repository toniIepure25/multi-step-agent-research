# Claim Audit

Every meaningful claim in the manuscript, with evidence source, level, and risk assessment.

## Supported Claims

| # | Claim | Evidence Artifact | Evidence Level | Status |
|---|-------|-------------------|---------------|--------|
| C1 | Temporal complementarity exists between cognitive operations (gen_hyp→retrieve synergy: +0.162) | `campaign_v4/results/complementarity_matrix.json` | Level 1 (simulator) | **SAFE** |
| C2 | Temporal complementarity replicates under real LLM execution (+0.111) | `campaign_v5/results/phase26_verdicts_gemma3.json` | Level 2 (LLM) | **SAFE** |
| C3 | Repeated hypothesis generation shows directional interference (-0.050, CI crosses zero) | `campaign_v4/results/complementarity_matrix.json` | Level 1 (simulator) | **NEEDS_QUALIFICATION** — not significant at α=0.05 |
| C4 | Attack/falsification value is timing-dependent (0.000 early, +0.276 late) | `campaign_v5/results/phase26_verdicts_gemma3.json` | Level 2 (LLM) | **SAFE** |
| C5 | Complementarity and timing effects are consistent across two LLM substrates | `phase26_verdicts_gemma3.json` + `phase26_verdicts_llama3_2-vision.json` | Level 2 (LLM) | **SAFE** |
| C6 | An adaptivity gap exists (oracle - best fixed = 0.096) | `campaign_v4/results/adaptivity_gap.json` | Level 1 (simulator) | **SAFE** |
| C7 | The benchmark enables counterfactual same-state evaluation | Architectural property of `EpistemicWorldSimulator` | Methodological | **SAFE** |
| C8 | B1_extended outperforms Full REE (0.594 vs 0.356) | `campaign_v2/results/locked_test_analysis.json` | Level 1 (simulator) | **SAFE** |
| C9 | gen_hyp + reason shows +0.228 super-additive complementarity (V3) | `campaign_v3/results/sequence_complementarity.jsonl` | Level 1 (simulator) | **SAFE** |

## Claims Requiring Qualification

| # | Claim | Evidence | Status | Qualification Needed |
|---|-------|----------|--------|---------------------|
| Q1 | "structural properties of the epistemic task" (cross-model invariance) | Phase 26 identical results across 2 models | **NEEDS_QUALIFICATION** | Only 2 models tested; say "consistent across the two evaluated substrates" not "universal" |
| Q2 | Operation reliability scores near 1.0 | `phase25_gate_*.json` | **NEEDS_QUALIFICATION** | Rubric measures keyword presence and JSON compliance, not deep semantic correctness |
| Q3 | Adaptivity gap is "meaningful" | gap = 0.096 | **NEEDS_QUALIFICATION** | Passes >0.05 threshold but fails stricter >0.10; say "modest but measurable" |

## Unsupported Claims (Must Not Appear)

| # | Claim | Evidence Against | Status |
|---|-------|-----------------|--------|
| U1 | Cognitive sequences universally beat primitive reasoning | Phase 26: +0.003, Phase 27: greedy highest | **UNSUPPORTED** |
| U2 | Adaptive motif control works | Policy 0.323 << fixed 0.518 << oracle 0.588 | **UNSUPPORTED** |
| U3 | REE/Full REE is superior to simpler agents | V2: B1 (0.594) >> Full REE (0.356) | **UNSUPPORTED** |
| U4 | Fixed cognition universally beats greedy | Phase 26: +0.003, INCONCLUSIVE | **UNSUPPORTED** |
| U5 | Operation ordering universally matters | Phase 26: NOT_REPLICATED (-0.050) | **UNSUPPORTED** |
| U6 | Temporal complementarity transfers to real research tasks | Phase 27: range=0.030, greedy highest | **UNSUPPORTED** |
| U7 | Adaptive metacognition is solved | Policy failure (H-REE-17 NOT_SUPPORTED) | **UNSUPPORTED** |
| U8 | Persistent hypothesis ecology improves all architectures | V3: NOT_SUPPORTED cross-architecture | **UNSUPPORTED** |
| U9 | Self-modeling/reflection improves performance | Phase 27: reflection = direct (0.696 = 0.696) — BUT this is an implementation bug (critique/revise never executed), not a scientific finding | **UNSUPPORTED / BUG** |

## Manuscript Wording Checks

| Section | Risk | Mitigation |
|---------|------|-----------|
| Abstract | Overclaiming complementarity scope | Include "operation-pair-specific" qualifier |
| Title | Grandiose framing | Avoid "superior", "revolutionary"; use "measuring" or "evaluating" |
| Introduction | Implying all sequence effects replicate | Enumerate which replicate and which do not |
| Results | Hiding negative findings | Dedicate subsection to negative results |
| Discussion | Implying adaptive control will work with better methods | State it as hypothesis, not conclusion |
| Conclusion | Promoting claims above evidence level | Use claim ladder (Level 0-2) explicitly |

## Post-Hardening Corrections (2026-08-11)

| Issue | Correction |
|-------|-----------|
| C3 interference | Downgraded from SAFE to NEEDS_QUALIFICATION — CI [−0.136, +0.035] crosses zero |
| C4 attack timing | +0.276 is budget-confounded (~5.7× compute). SAFE as directional finding; must acknowledge confound |
| C5 cross-model | Scores are simulator-controlled; cross-model "consistency" is trivially expected. Reword: structural persistence |
| U9 reflection | Implementation bug, not scientific finding. Remove from negative findings |
| R6 fixed vs greedy | Code duplicate of R1. Remove as separate test |
| Complementarity definition | V3/V4/V5 use different formulas. Paper uses V4 formula (Eq. 1) as canonical |
| Phase 27 "real evidence" | Relabeled to "curated literature-themed summaries" |

## Overall Audit Status: PASS (with corrections)

All supported claims trace to raw artifacts. Hardening exposed 5 issues requiring claim adjustment. All corrections preserve existing evidence; no new experiments were conducted.
