# V6 External Dataset Results

## Status: NOT YET EXECUTED

## Selected Datasets

### SciFact
- 5,183 scientific abstracts
- Claim verification (SUPPORTS / REFUTES / NOT_ENOUGH_INFO)
- External gold evidence sentence annotations
- Apache 2.0 license

### HotpotQA (distractor setting)
- Wikipedia paragraphs
- Multi-hop reasoning questions
- Gold answer + supporting facts
- CC BY-SA 4.0 license

## Implementation Required

1. Download datasets and build retrieval indices
2. Freeze DEV/LOCKED task splits
3. Implement cognitive operation mapping for evidence-grounded tasks
4. Run factorial complementarity on external tasks
5. Compare with matched primitive controls

## Dependency

Execution is pending completion of simulator-level V6 analysis.
Given that simulator factorial complementarity is zero, external
transfer testing may be less urgent than initially planned.

However, if hypothesis generation's standalone value transfers to
external datasets, that finding alone would be significant.
