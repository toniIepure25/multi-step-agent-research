# Human Audit Protocol — Stage 3D

## Date: 2026-08-14
## Status: PROTOCOL DEFINED (execution deferred until sufficient LLM traces)

---

## Purpose
Prepare blinded human evaluation material for a small high-value subset
of generated hypotheses and revisions.

---

## Material Preparation

For each case in the audit set, prepare:
1. **Observations** (blinded — no model identity, no timestamp)
2. **Generated hypothesis** (the model's output, stripped of metadata)
3. **Decisive evidence** (the falsifying observations)
4. **Model's revision** (new explanation, confidence, abandonment decision)

---

## Evaluation Criteria

### 1. Mechanistic Distinctness
> Is the generated hypothesis a genuine mechanistic explanation (not a paraphrase
> of the observations)?

Rating: 1 (trivial restatement) to 5 (novel mechanistic claim)

### 2. Falsifiability
> Does the hypothesis make specific, testable predictions that could be disproven?

Rating: 1 (unfalsifiable) to 5 (specific testable predictions)

### 3. Legitimacy of Theory Revision
> Is the model's response to falsifying evidence appropriate?

Options:
- LEGITIMATE ABANDONMENT: correctly rejects hypothesis, identifies alternative
- APPROPRIATE HEDGE: correctly reduces confidence, notes limitations
- AD-HOC RESCUE: invents unsupported assumptions to save hypothesis
- DENIAL: ignores or dismisses evidence
- OVER-ABANDONMENT: abandons too hastily without genuine contradiction

### 4. Quality of New Explanation
> Does the revised explanation better fit the evidence?

Rating: 1 (worse than original) to 5 (clearly superior fit)

---

## Evaluator Requirements
- Domain knowledge in relevant scientific area (if domain-specific worlds used)
- OR general scientific literacy (if abstract/general worlds used)
- Blinded to: model identity, provenance condition, expected result
- Independent rating (no discussion between evaluators)

---

## Sample Selection
- Prioritize cases where the model showed INTERESTING behavior:
  - Low-confidence abandonment (borderline decisions)
  - Partial revision (not clear abandon/retain)
  - Novel alternative explanations
  - Potential rationalizations
- Target: 20-30 cases for pilot human evaluation

---

## Inter-Rater Reliability
- Cohen's kappa for categorical judgments (legitimacy)
- ICC for ordinal ratings (distinctness, falsifiability, quality)
- Minimum acceptable kappa: 0.60

---

## When to Execute
This protocol executes AFTER:
1. SD-H4 scaled inference complete (50+ worlds)
2. Sufficient diversity of model responses collected
3. At least some borderline/interesting cases identified
