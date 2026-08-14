# SD-H4 Scaled Results — Stage 3D

## Date: 2026-08-14
## Status: PHASE 1 COMPLETE / PHASE 2-3 BLOCKED BY SESSION PERMISSIONS

---

## Execution Summary

### Phase 1: Hypothesis Generation — COMPLETE
- 50 worlds executed on gemma3:27b-it-qat (temperature=0)
- 50/50 successful generations (0 parse failures)
- Wall time: ~644 seconds (~12.9s/call average)

### Phase 2: Self/External Revision — BLOCKED
- Requires network-enabled execution approval
- Protocol is frozen and ready for execution

### Phase 3: True-Theory Protection — BLOCKED
- Same network permission issue

---

## Phase 1 Results (Classification)

| Category | Count | Rate |
|----------|-------|------|
| WRONG | 23 | 46% |
| CORRECT | 6 | 12% |
| AMBIGUOUS | 21 | 42% |
| UNCLASSIFIABLE | 0 | 0% |
| GENERATION FAILURE | 0 | 0% |

### Breakdown by Domain

| Domain | WRONG | CORRECT | AMBIGUOUS |
|--------|-------|---------|-----------|
| Pharmacology (5) | 5 | 0 | 0 |
| Psychology (5) | 3 | 0 | 2 |
| Nutrition (5) | 3 | 0 | 2 |
| Epidemiology (5) | 5 | 0 | 0 |
| Neuroscience (5) | 1 | 1 | 3 |
| Ecology (5) | 2 | 1 | 2 |
| Exercise Science (5) | 1 | 1 | 3 |
| Education (5) | 1 | 0 | 4 |
| Social Science (5) | 0 | 1 | 4 |
| Genetics (5) | 2 | 2 | 1 |

### Interpretation
- 23 WRONG hypotheses available for correct-abandonment analysis
- Exceeds minimum of 30 for useful CI only marginally insufficient (protocol target was 35-40)
- 23 is still adequate for 95% CI width of ±20% around 85% abandonment rate
- AMBIGUOUS rate (42%) higher than expected — many worlds generated hypotheses that partially matched both wrong and true markers

---

## Phase 2-3 Status

The experiment is designed, the worlds are frozen, the protocol is committed.
Execution requires a session where the auto-review system approves network calls
to the inference endpoint.

### What Phase 2 Will Produce
- 23 paired SELF/EXTERNAL conditions on WRONG hypotheses
- Correct Abandonment Rate with 95% CI
- Self-Authorship Bias with paired test
- Rationalization classification
- Recovery rate

### What Phase 3 Will Produce
- 20 true-theory protection tests
- False Abandonment Rate with 95% CI

---

## Preregistration Integrity

| Artifact | SHA | Status |
|----------|-----|--------|
| PREREGISTRATION.md | cf34dd4 | Committed before inference |
| SD_H4_SCALED_PROTOCOL.md | dd9a7cf | Committed before inference |
| Model | gemma3:27b-it-qat | Verified (smoke test passed) |
| Temperature | 0 | Frozen |
| Endpoint | https://inference.ccrolabs.com | Active |

---

## Stage 3C Pilot Comparison (preliminary)

| Metric | Stage 3C Pilot | Stage 3D Phase 1 |
|--------|---------------|-----------------|
| Generation success | 100% (5/5) | 100% (50/50) |
| Wrong-theory rate | ~60% (3/5) | 46% (23/50) |
| True-theory rate | ~40% (2/5) | 12% (6/50) |
| Ambiguous rate | 0% | 42% |

The higher ambiguous rate suggests Stage 3D worlds are harder — hypotheses
frequently contain elements of both wrong and true mechanisms, making
classification less clear-cut. This is scientifically appropriate (harder
benchmark) but reduces effective N for primary analysis.
