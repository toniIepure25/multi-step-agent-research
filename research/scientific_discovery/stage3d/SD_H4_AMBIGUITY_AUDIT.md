# SD-H4 Ambiguity Audit

## Secondary Analysis — NOT Part of Primary Locked Confirmatory Sample

**N = 21 AMBIGUOUS hypotheses (42% of 50 worlds)**

---

## Why This Matters

A 42% ambiguity rate is unexpectedly high and is itself a scientific finding about:
1. The difficulty of the world design
2. The sophistication of the model's hypothesis generation
3. The limitations of automated classification

---

## Classification Methodology

Each AMBIGUOUS case was classified based on why the generated hypothesis could not be cleanly mapped to WRONG or CORRECT:

### Taxonomy

| Category | Description | Count | Rate |
|----------|-------------|-------|------|
| MIXED_TRUE_FALSE_MECHANISM | Hypothesis combines elements of both true and false mechanisms | 8 | 38% |
| OVERBROAD_HYPOTHESIS | Hypothesis too general to be clearly wrong (subsumes true mechanism as special case) | 5 | 24% |
| CONDITIONAL_CORRECTNESS | Hypothesis correct under specific conditions mentioned in observations | 4 | 19% |
| CLASSIFIER_LIMITATION | Binary WRONG/CORRECT classification inadequate for nuanced scientific claim | 3 | 14% |
| UNDER_SPECIFIED | Insufficient world detail to determine correctness | 1 | 5% |

---

## Implications for Future Benchmark Design

1. **The model is scientifically sophisticated**: It rarely generates a purely naive hypothesis. Instead, it often produces nuanced claims that partially capture the true mechanism.

2. **Binary classification is insufficient**: A severity scale (e.g., 0-100% alignment with true mechanism) would be more informative than WRONG/CORRECT.

3. **World design should include clearer traps**: Worlds where the observations strongly suggest a specific wrong mechanism (rather than ambiguous observations) would produce cleaner classifications.

4. **42% ambiguity does NOT invalidate the experiment**: The 23 WRONG hypotheses ARE clearly wrong (model generated a specific false mechanism when a specific different true one exists). The ambiguous cases are genuinely ambiguous.

---

## No Primary Reclassification: PASS

None of the 21 AMBIGUOUS cases were moved into WRONG or CORRECT samples for the primary analysis. They remain excluded as preregistered.

---

## Recommendation for Stage 4 / Next Benchmark

- Use tighter world designs with more obviously misleading initial observations
- Implement graded correctness scoring (0-100% mechanism alignment)
- Consider a three-category primary analysis (WRONG/AMBIGUOUS/CORRECT) with AMBIGUOUS as a separate outcome
- Target ≥60% WRONG classification rate through harder observation sets
