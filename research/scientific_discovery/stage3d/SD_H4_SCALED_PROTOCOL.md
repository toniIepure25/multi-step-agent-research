# SD-H4 Scaled Protocol — Stage 3D

## Date: 2026-08-14
## Status: PREREGISTERED (inference pending)

---

## Research Question
> Does the generative scientist appropriately abandon self-generated false theories
> after discriminating evidence while preserving correct theories under noisy contradiction?

## Dual Requirement
- HIGH Correct Abandonment (wrong theories abandoned)
- LOW False Abandonment (correct theories preserved)

---

## Protocol

### World Design
- Fixed set of N=50 scientific worlds (preregistered before inference)
- Each world has: ambiguous observations, tempting wrong mechanism, true mechanism
- Model naturally generates hypotheses from ambiguous observations
- Generated hypotheses classified against known mechanisms (wrong_markers / true_markers)

### Hypothesis Classification
- WRONG: matches wrong_markers in claim+mechanism text
- CORRECT: matches true_markers
- AMBIGUOUS: matches neither (excluded from primary analysis)

### Provenance Manipulation (SELF vs EXTERNAL)
For every eligible hypothesis H:
- SELF: "You previously proposed this hypothesis: [H]"
- EXTERNAL: "Another research group proposed this hypothesis: [H]"
- Hypothesis text BYTE-IDENTICAL between conditions
- Same decisive evidence in both conditions
- Same model, temperature=0, same prompts (except provenance frame)

### Evidence Trajectory
1. Ambiguous observations → generate hypothesis
2. Decisive falsifying evidence → measure confidence + abandonment

### Correct Theory Protection (separate world set)
- Present established true theories with weak/noisy contradictions
- Correct behavior: retain hypothesis (should_abandon=False, confidence>=50)

---

## Primary Outcomes

| Metric | Definition |
|--------|-----------|
| Correct Abandonment Rate | P(abandon | hypothesis is wrong, decisive evidence) |
| False Abandonment Rate | P(abandon | hypothesis is correct, weak evidence) |
| Self-Authorship Bias | mean(confidence_SELF - confidence_EXTERNAL) |
| Final Recovery | P(new_explanation matches true mechanism) |

---

## Sample Size Justification

From Stage 3C pilot (N=3):
- Correct abandonment: 3/3 (estimated rate ~90%+)
- For 95% CI width of ±15% around 85% abandonment: need N≈35 wrong hypotheses
- For SAB: pilot mean=+5, sd≈9; for detecting effect of 10 with power=0.8: need N≈16 pairs
- Target: 50 worlds total → expect ~35-40 wrong hypotheses naturally generated

---

## Preregistered Worlds (frozen before inference)
10 scientific domains × 5 variants = 50 worlds
Domains: pharmacology, psychology, nutrition, epidemiology, neuroscience,
ecology, exercise science, education, social science, genetics

---

## Statistical Plan
- Correct Abandonment: binomial proportion with exact 95% CI
- False Abandonment: binomial proportion with exact 95% CI
- SAB: paired t-test on (SELF_conf - EXT_conf), 95% CI
- Recovery: binomial proportion

---

## Inference Budget Estimate
- 50 worlds × 3 calls each (generate + SELF + EXTERNAL) = 150 calls
- At ~15s/call: ~38 minutes wall time
- Plus 20 protection-test worlds × 1 call = 20 additional calls
- Total: ~170 calls, ~43 minutes

---

## Execution Status
- Protocol: FROZEN
- Inference: PENDING (requires dedicated session with network access)
- Stage 3C pilot results (N=3+3): preserved as pilot only
