# Error Taxonomy — V6 Completion

## Classification of Failure Modes

### 1. HYPOTHESIS ANCHORING (SciFact primary failure)

The model generates a task-specific hypothesis that anchors subsequent
reasoning toward a specific verdict. When the hypothesis is wrong,
it biases the final classification.

Evidence: REAL accuracy (0.720) < SHUFFLED accuracy (0.980) on SciFact.
Shuffled hypotheses don't anchor reasoning and let the model use its
internal knowledge more effectively.

### 2. RETRIEVAL NOISE INTRODUCTION

Retrieving actual documents introduces information that may conflict
with the model's correct internal assessment. On SciFact, the retrieved
abstracts sometimes contain nuanced language that the model misinterprets.

Evidence: DIRECT (0.780) > REAL (0.720) on SciFact accuracy, despite
REAL having better gold evidence recall.

### 3. QUERY DEGRADATION FROM SHUFFLED ARTIFACTS

When the hypothesis is from a different task, the generated query
targets irrelevant evidence. This is the primary mechanism by which
SHUFFLED harms performance on HotpotQA.

Evidence: SHUFFLED gold recall (0.000 SciFact, 0.270 HotpotQA) is
lowest across all conditions.

### 4. FORMAT/PARSING FAILURES

Some LLM responses fail JSON parsing, leading to fallback text
extraction. This affects all conditions equally and is not
condition-dependent.

### 5. RETRIEVAL CEILING ON GOLD EVIDENCE

BM25 keyword retrieval has limited recall for gold evidence.
Baseline DIRECT recall is already modest (0.297 SciFact, 0.430 HotpotQA),
limiting the room for hypothesis-guided improvement.

## Error Distribution by Condition

| Error Type              | REAL  | SHUFFLED | NEUTRAL | DIRECT |
|------------------------|-------|----------|---------|--------|
| Hypothesis anchoring   | HIGH  | LOW      | LOW     | NONE   |
| Retrieval noise        | MED   | HIGH     | MED     | MED    |
| Query degradation      | LOW   | HIGH     | LOW     | LOW    |
| Format failures        | EQUAL | EQUAL    | EQUAL   | EQUAL  |
| Retrieval ceiling      | EQUAL | EQUAL    | EQUAL   | EQUAL  |
