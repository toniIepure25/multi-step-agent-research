# Recovery Failure Forensics — Stage 3E

## Source Data
SD-H4 SCALED Phase 2: 22 abandoned WRONG hypotheses.
Of these, 4 recovered the true mechanism (18.2%) and 18 did not (81.8%).

---

## Critical Observation

In ALL 18 failed recovery cases, the TRUE MECHANISM was **explicitly present
in the decisive evidence** shown to the model. The model did not lack information.

The failure is not "insufficient evidence" — it is "failure to extract and
reformulate the correct mechanism from evidence that already contains it."

---

## Per-Case Forensic Classification

| Case ID | self_new content | True mechanism in evidence? | Classification |
|---------|-----------------|---------------------------|----------------|
| pharm_01 | "" (empty) | YES: "metabolite Y directly inhibits COX-2" | TRUE_NOT_GENERATED |
| pharm_02 | "" (empty) | YES: "Z binds 30S ribosomal subunit" | TRUE_NOT_GENERATED |
| pharm_03 | "" (empty) | YES: "insulin resistance and lipogenesis" | TRUE_NOT_GENERATED |
| psych_02 | "" (empty) | YES: "Total vocabulary across BOTH languages exceeds" | TRUE_NOT_GENERATED |
| psych_03 | "" (empty) | YES: "weather explains <1% of mood variance" | TRUE_NOT_GENERATED |
| psych_04 | "" (empty) | YES: "40% reduction, switch cost accumulates" | TRUE_NOT_GENERATED |
| nutr_02 | "no discernible health benefit" | YES: "confounding — exercise, income, lifestyle" | TRUE_PARTIALLY_GENERATED |
| nutr_04 | "" (empty) | YES: "sugar concentration, fiber removal, glycemic" | TRUE_NOT_GENERATED |
| epi_01 | "" (empty) | YES: "entirely explained by GDP per capita" | TRUE_NOT_GENERATED |
| epi_02 | "" (empty) | YES: "Simpson's paradox, sicker patients" | TRUE_NOT_GENERATED |
| epi_03 | "no longer supported" | YES: "broadened diagnostic criteria, fraud" | TRUE_NOT_GENERATED |
| epi_04 | "" (empty) | YES: "socioeconomic factors" | TRUE_NOT_GENERATED |
| epi_05 | "" (empty) | YES: "sick quitter bias, Mendelian randomization" | TRUE_NOT_GENERATED |
| neuro_05 | "" (empty) | YES: "prefrontal and insular cortex" | TRUE_NOT_GENERATED |
| eco_01 | "" (empty) | YES: "began BEFORE wolves, dam removal, climate" | TRUE_NOT_GENERATED |
| edu_05 | "" (empty) | YES: "distraction, no improvement, decline" | TRUE_NOT_GENERATED |
| gen_02 | "" (empty) | YES: "Epigenetic inheritance, methylation, histone" | TRUE_NOT_GENERATED |
| gen_05 | "not supported by current evidence" | YES: "safe, thousands of studies, no harm" | TRUE_NOT_GENERATED |

---

## Aggregate Classification

| Category | Count | Rate |
|----------|-------|------|
| TRUE_NOT_GENERATED | 17 | 94.4% |
| TRUE_PARTIALLY_GENERATED | 1 | 5.6% |
| TRUE_GENERATED_NOT_SELECTED | 0 | 0.0% |
| INSUFFICIENT_EVIDENCE | 0 | 0.0% |
| WRONG_RECOMMITMENT | 0 | 0.0% |
| ABSTAINED_APPROPRIATELY | 0 | 0.0% |
| EVALUATOR_AMBIGUITY | 0 | 0.0% |

---

## Root Cause Analysis

### The failure is NOT:
- Insufficient domain knowledge (model clearly uses the evidence to falsify)
- Insufficient evidence (true mechanism is explicitly stated in all 18 cases)
- Selection failure (model never generates multiple candidates to select from)
- Wrong recommitment (model never proposes an incorrect alternative)

### The failure IS:
**EXTRACTION/REFORMULATION FAILURE**

The model excels at recognizing WHY its hypothesis is wrong (using the decisive
evidence to justify abandonment). But it does not take the additional step of
reformulating WHAT IS RIGHT based on that same evidence.

Behaviorally: the model treats `new_explanation` as an optional field and leaves
it empty once it has decided to abandon. It performs falsification but not
abductive reconstruction.

---

## Mechanistic Interpretation

The SD-H4 prompt asks simultaneously:
1. Should you abandon? (YES/NO)
2. What confidence do you retain?
3. What is your new explanation?

The model focuses entirely on (1) and (2), treating (3) as secondary. In 15/18
cases it returns `""` for new_explanation. In 3/18 it provides a tautological
restatement ("no longer supported").

This suggests **prompt structure** as a proximate cause and **abductive reasoning
as a separate cognitive step** as a deeper cause.

---

## Formal Abductive Decomposition (Phase 3)

Given:
- C = 1 if true mechanism is represented in candidate set
- S = 1 if true mechanism is selected (conditional on C=1)
- R = 1 if final theory is correct

For the SD-H4 one-shot protocol:

| Metric | Value | Interpretation |
|--------|-------|----------------|
| P(C) | 4/22 = 0.182 | True mechanism generated in only 18.2% of cases |
| P(S \| C) | 4/4 = 1.000 | When generated, always "selected" (trivially: single output) |
| P(R) | 4/22 = 0.182 | Overall recovery rate |

**The bottleneck is unambiguously GENERATION, not SELECTION.**

When the model produces the true mechanism at all, it gets it right (4/4).
The problem is that it almost never produces it (18/22 = 81.8% coverage failure).

---

## Implications for Stage 3E Design

1. **R2 (Structured Ecology)** should dramatically improve P(C) by forcing
   multiple candidate generation as a separate explicit step
2. **R4 (Oracle Candidate Set)** will confirm whether P(S|C) remains high
   when candidates are guaranteed-available
3. **R1 (Compute-Matched Reflection)** tests whether simply asking "try harder
   to propose an alternative" improves generation without structured ecology
4. The evidence-to-hypothesis extraction step needs to be EXPLICITLY prompted
   rather than embedded as an optional field in the abandonment decision

---

## Key Finding

> The 18.2% recovery rate in SD-H4 is not caused by insufficient evidence,
> insufficient knowledge, or selection failure. It is caused by the model
> not being asked to perform abductive reconstruction as a distinct cognitive
> step separate from the abandonment decision.

This is promising: the fix may be architectural (separate abandonment from
reconstruction) rather than requiring fundamental capability improvements.
