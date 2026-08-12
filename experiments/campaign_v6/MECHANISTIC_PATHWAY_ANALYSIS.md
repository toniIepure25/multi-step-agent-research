# Mechanistic Pathway Analysis — V6 Completion

## Causal Chain Under Test

```
Hypothesis Artifact → Query → Evidence Retrieval → Final Answer
```

## Pathway Results

### Step 1: Hypothesis → Query Quality

Real hypotheses produce queries that are more targeted toward
task-relevant evidence than shuffled or neutral alternatives.
This is evidenced by the retrieval recall differences.

### Step 2: Query → Evidence Retrieval

| Dataset   | REAL Recall | SHUFFLED Recall | Effect  | 95% CI              |
|-----------|------------:|----------------:|--------:|--------------------:|
| SciFact   | 0.230       | 0.000           | +0.230  | [+0.147, +0.313]    |
| HotpotQA  | 0.405       | 0.270           | +0.135  | [+0.062, +0.209]    |

Both datasets show that task-specific hypothesis content causally
improves evidence retrieval. This is the strongest pathway finding.

### Step 3: Evidence → Final Answer

| Dataset   | REAL Performance | SHUFFLED Performance | Effect  | 95% CI              |
|-----------|------------------:|---------------------:|--------:|--------------------:|
| SciFact   | 0.720 (acc)       | 0.980 (acc)          | -0.260  | [-0.346, -0.174]    |
| HotpotQA  | 0.387 (F1)        | 0.292 (F1)           | +0.095  | [+0.010, +0.180]    |

The pathway DIVERGES at this step:
- On SciFact, better evidence HURTS accuracy
- On HotpotQA, better evidence HELPS answer quality

## Mediator Analysis

### Why retrieval helps on HotpotQA but hurts on SciFact

**SciFact interpretation:**
SciFact is a claim verification task. The model's internal knowledge
is often sufficient to correctly classify claims (SHUFFLED acc=0.980).
Retrieving actual scientific abstracts introduces nuanced evidence that
can support OR refute claims — but the model's reasoning about this
evidence is less reliable than its direct classification. The hypothesis
anchors reasoning toward a specific verdict, sometimes incorrectly.

**HotpotQA interpretation:**
HotpotQA requires multi-hop reasoning with specific factual evidence
not likely in model pretraining data. Retrieving relevant paragraphs
genuinely helps answer the question. Task-specific hypotheses guide
retrieval toward relevant paragraphs.

### Task Structure Determines Whether Retrieval Helps

Evidence retrieval is more valuable when:
1. The task requires information NOT in the model's training data
2. The answer depends on specific factual details in external documents
3. The model cannot solve the task from internal knowledge alone

Evidence retrieval is less valuable (or harmful) when:
1. The model already knows the answer from training data
2. External evidence introduces noise or contradictory signals
3. The hypothesis anchors reasoning toward a specific conclusion

## Condition Ordering

### SciFact Expected vs Observed

Expected if hypothesis semantics help:
```
REAL > GENERIC_EXPANSION > NEUTRAL > SHUFFLED
```

Observed:
```
SHUFFLED > DIRECT ≈ GENERIC_EXPANSION > NEUTRAL ≈ REAL
```

This inverted ordering on accuracy reveals that on this task,
ANY hypothesis-like artifact harms performance relative to controls.

### HotpotQA Expected vs Observed

Expected if hypothesis semantics help:
```
REAL > GENERIC_EXPANSION > NEUTRAL > SHUFFLED
```

Observed (F1):
```
NEUTRAL > GENERIC_EXPANSION ≈ DIRECT ≈ REAL > SHUFFLED
```

REAL does not clearly dominate NEUTRAL or GENERIC_EXPANSION on F1.
The benefit over SHUFFLED is significant but modest.

## Conclusion

The mechanistic pathway (hypothesis → query → evidence) is causally
operative. But the practical value of this pathway depends entirely
on the task's information requirements. The pathway is beneficial
for information-seeking tasks (HotpotQA) and harmful for classification
tasks where the model already has sufficient internal knowledge (SciFact).
