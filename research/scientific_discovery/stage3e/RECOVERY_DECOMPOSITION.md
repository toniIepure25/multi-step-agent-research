# Recovery Decomposition — Generation vs Selection

## Core Framework

Recovery = Coverage × Selection

Where:
- Coverage (C) = P(true mechanism appears in output/candidate set)
- Selection (S|C) = P(true mechanism selected when present)
- Recovery (R) = C × S|C

## Results by Condition and Dataset

### DEV (22 seen cases)

| Condition | C | S\|C | R |
|-----------|---|------|---|
| R0 (one-shot) | 82.6% (= R, trivially) | 100% (single output) | 82.6% |
| R1 (reflection) | 91.3% (= R) | 100% | 91.3% |
| R2 (ecology) | 82.6% | 84.2% | 69.6% |
| R4 (oracle) | 100% (guaranteed) | 95.7% | 95.7% |

### LOCKED (25 new worlds)

| Condition | C | S\|C | R |
|-----------|---|------|---|
| R0 (one-shot) | 76.0% (= R) | 100% | 76.0% |
| R1 (reflection) | 80.0% (= R) | 100% | 80.0% |
| R2 (ecology) | 88.0% | 68.2% | 60.0% |
| R4 (oracle) | 100% | 100% | 100% |

## Key Finding

**R2 increases Coverage (88% vs 76-80% direct) but dramatically reduces Selection
(68% vs 100% oracle).**

The net effect is NEGATIVE because Selection degrades more than Coverage improves.

## Why Selection Fails in R2 but Not R4

| Property | R2 (self-generated) | R4 (oracle) |
|----------|-------------------|-------------|
| Candidate quality | Variable, some ambiguous | Clean, distinct |
| Candidate count | 4-6 | 4 |
| True mechanism phrasing | Model's own words | Precise formulation |
| Distractor quality | Other plausible mechanisms | Standard confound/null/artifact |
| Selection accuracy | 68-84% | 96-100% |

The model's own generated candidates create a harder selection problem than
oracle-crafted candidates. This is likely because:
1. Self-generated text has coherence with the model's internal representations
2. Multiple self-generated alternatives create mutual interference
3. Oracle candidates are cleaner and more orthogonal

## Bottleneck Diagnosis

For the SD-H4-class problems (well-known scientific misconceptions):

| Bottleneck | Evidence | Verdict |
|-----------|----------|---------|
| Generation (model can't produce answer) | R0=76-83%, R1=80-91% | NOT the bottleneck |
| Selection (model can't pick right answer) | R4=96-100% | NOT the bottleneck |
| Prompt design (model not asked properly) | SD-H4=18% vs R0=76% | **THIS IS IT** |
| Evidence insufficiency | All evidence contains true mechanism | NOT the bottleneck |

## Implication

The "recovery bottleneck" identified in SD-H4 was a METHODOLOGICAL ARTIFACT.
When the model is simply asked to propose a replacement theory (separate from
the abandonment decision), it performs well without any architectural intervention.

The remaining 20-24% failure rate represents cases where:
- The true mechanism markers are not in the model's natural phrasing
- The model proposes a related but not marker-matching explanation
- The model genuinely doesn't identify the correct mechanism
