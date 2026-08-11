# V6 External Dataset Selection Audit

## Objective

Select 2-3 public evidence-grounded datasets defined independently of the
temporal-complementarity hypothesis. Tasks must be solvable by evidence
reasoning, not pure knowledge recall.

## Candidate Datasets

### 1. SciFact (Wadden et al., 2020)

| Dimension | Assessment |
|-----------|-----------|
| Real source documents | Yes — 5,183 scientific abstracts from S2ORC |
| External gold labels | Yes — claim verification labels (SUPPORTS/REFUTES/NOT_ENOUGH_INFO) |
| Evidence reasoning | Yes — requires finding and reasoning over evidence sentences |
| License | Apache 2.0 |
| Stable version | v1.0, publicly hosted |
| Suitability | HIGH — evidence-grounded, multi-step reasoning, external gold |
| Task format | Given a scientific claim, retrieve evidence from abstract corpus, determine support/refutation |

**Why suitable:** Requires hypothesis (claim) → targeted retrieval → evidence evaluation → verdict.
This maps naturally to our cognitive operation vocabulary.

**Cognitive operation mapping:**
- generate_hypothesis → formulate claim interpretation
- retrieve → find relevant abstract passages
- reason → evaluate evidence-claim consistency
- attack → identify contradictory evidence

### 2. HotpotQA (Yang et al., 2018)

| Dimension | Assessment |
|-----------|-----------|
| Real source documents | Yes — Wikipedia paragraphs |
| External gold labels | Yes — answer + supporting facts |
| Evidence reasoning | Yes — multi-hop reasoning required |
| License | CC BY-SA 4.0 |
| Stable version | Distractor setting, publicly hosted |
| Suitability | MEDIUM-HIGH — multi-hop but less evidence-focused |
| Task format | Answer multi-hop question using retrieved passages |

**Why suitable:** Multi-hop reasoning requires composing information across documents.
Hypothesis generation could help target retrieval for the second hop.

**Limitation:** Some questions are answerable from knowledge alone.

### 3. FEVER (Thorne et al., 2018)

| Dimension | Assessment |
|-----------|-----------|
| Real source documents | Yes — Wikipedia (June 2017 dump) |
| External gold labels | Yes — SUPPORTED/REFUTED/NOT ENOUGH INFO + gold evidence |
| Evidence reasoning | Yes — evidence retrieval + verification |
| License | Research use |
| Stable version | v1.0, shared task dataset |
| Suitability | MEDIUM — simpler claims, some synthetic generation |

**Limitation:** Many claims are simple negations/modifications; less naturalistic.

## Recommended Selection

### Primary: SciFact
- Strongest evidence-reasoning match
- External gold evidence annotations
- Scientific domain aligns with cognitive operation semantics
- Manageable corpus size (~5K abstracts)

### Secondary: HotpotQA (distractor setting)
- Multi-hop reasoning tests hypothesis → retrieval chain
- Large evaluation pool
- Well-established benchmark

### Excluded: FEVER
- Too simple for cognitive-sequence value to manifest
- Claim construction is partially synthetic

## Implementation Plan

### SciFact
1. Download corpus and claims from official release
2. Build BM25 index over abstracts using rank_bm25
3. Freeze DEV/LOCKED splits (60%/40% of claims)
4. Cognitive operations:
   - retrieve: BM25 search conditioned on LLM query
   - generate_hypothesis: interpret claim, formulate evidence prediction
   - reason: evaluate retrieved abstracts against claim
   - attack: identify contradictory evidence
   - synthesis: produce final verdict (SUPPORTS/REFUTED/NEI)
5. Metric: label accuracy (3-class), evidence sentence F1

### HotpotQA
1. Use distractor setting (10 paragraphs per question, 2 gold)
2. Freeze DEV/LOCKED splits
3. Cognitive operations:
   - retrieve: select relevant paragraph(s) from distractor set
   - generate_hypothesis: formulate intermediate answer for hop 1
   - reason: combine hop 1 answer with hop 2 evidence
   - synthesis: produce final answer
4. Metric: answer F1, supporting fact F1

## Budget Matching on External Datasets

All conditions must use identical:
- Number of LLM calls
- Maximum retrieval calls (k passages)
- Maximum token budget

Control operations replace absent cognitive operations with
matched-compute paraphrase calls.

## Split Hashing

Task IDs for DEV and LOCKED splits will be committed and SHA-256 hashed
before any model output is generated on LOCKED tasks.
