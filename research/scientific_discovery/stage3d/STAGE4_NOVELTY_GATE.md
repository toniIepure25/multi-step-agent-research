# Stage 4 Novelty Gate

## Date: 2026-08-14
## Question: What does ASAR's proposed ontology experiment empirically test that existing self-revising-discovery formulations do not?

---

## Prior Art: Wang & Buehler (2026) — Self-Revising Discovery Systems

### What They Provide
1. Category-theoretic formalization of "discovery = regime transition"
2. Copresheaf representation of scientific state
3. Left Kan extension for transporting evidence across schemas
4. Formal definition of novelty as residual content
5. MDL gate for accepting/rejecting regime transitions
6. Two instantiations (Builder/Breaker, CategoryScienceClaw)

### What They Do NOT Provide
1. No LLM-based empirical evaluation of detection accuracy
2. No measurement of WHEN systems detect schema insufficiency
3. No false-positive rate for unnecessary regime transitions
4. No comparison of detection with/without prior falsification experience
5. No measurement of generated representation quality vs human baselines
6. No evaluation on problems where ontology revision is NOT needed (specificity)

---

## ASAR Stage 4 Must Answer (Not Just Formalize)

### Q1: DETECTION
> Can the system empirically recognize that the current hypothesis space is structurally insufficient?

Measurement: Detection sensitivity and specificity across worlds where:
- Revision IS needed (all hypotheses share a false presupposition)
- Revision is NOT needed (correct hypothesis exists in current space)

### Q2: REPRESENTATION GENERATION
> Can it propose a representation that resolves the identified insufficiency?

Measurement: Does the proposed new schema contain the true mechanism that was
previously inexpressible?

### Q3: EMPIRICAL VALIDATION
> Does the new representation improve predictions on held-out observations?

Measurement: Prediction accuracy before/after ontology revision on unseen evidence.

---

## Novelty Claim That Survives Prior Art

ASAR Stage 4 novelty = **empirical evaluation of detection-generation-validation**
on controlled worlds where ground truth is known.

Wang & Buehler provide the FORMAL language.
ASAR would provide the EMPIRICAL characterization of an LLM-based system's ability
to actually perform these transitions under controlled conditions.

---

## Requirements Before Stage 4

1. SD-H4 at meaningful N (self-correction demonstrated)
2. SD-H2 formally evaluated (ecology helps when needed)
3. Oracle regret certified (experiment design works)
4. Failure taxonomy populated (know where system breaks)
5. External validation attempted (FalsifyBench if accessible)
6. Stage 4 experimental protocol preregistered

---

## GO/NO-GO Criteria

Stage 4 is allowed ONLY if:
- All Stage 3D prerequisites KNOWN (not necessarily positive)
- A concrete detection-generation-validation protocol exists
- Controlled worlds with schema-insufficient hypothesis spaces are designed
- Specificity test (no unnecessary revision) is included
- Prior art gap is maintained (empirical, not just formal)
