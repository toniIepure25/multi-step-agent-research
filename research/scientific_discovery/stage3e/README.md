# Stage 3E — Post-Falsification Abductive Recovery

## Purpose

SD-H4 established that gemma3:27b-it-qat correctly abandons wrong hypotheses
(95.7%) but recovers the true mechanism in only 18.2% of cases. This stage
investigates WHY recovery fails and tests whether structured abductive
reconstruction can improve it.

## Key Finding from Forensics

The recovery failure is NOT caused by:
- Insufficient domain knowledge
- Insufficient evidence
- Selection failure

It IS caused by:
- The model treating theory replacement as optional after abandonment
- Single-step prompt combining falsification decision and reconstruction
- 94.4% of failures: model returned empty `new_explanation` field

## Hypothesis

**SD-H10** (PROSPECTIVE — motivated by SD-H4 results):
> Structured generation and evaluation of mechanistically distinct alternative
> hypotheses improves recovery after falsification relative to one-shot theory
> replacement, without increasing false commitment or unnecessary hypothesis
> proliferation.

## Experimental Conditions

| Condition | Description | Purpose |
|-----------|-------------|---------|
| R0 | One-shot replacement (SD-H4 baseline) | Baseline |
| R1 | Compute-matched generic reflection | Control for extra tokens |
| R2 | Post-falsification structured ecology (generate→select) | Test structured generation |
| R4 | Oracle candidate set (true present, must select) | Diagnostic upper bound |

## Primary Contrast

R2 (structured ecology) vs R1 (compute-matched reflection)

This isolates the benefit of structured multi-candidate generation from
simply having more inference compute available.

## Files

- `run_recovery_experiment.py` — Execution script (resumable, checkpointed)
- `RECOVERY_FAILURE_FORENSICS.md` — Per-case analysis of SD-H4 failures
- `RECOVERY_FAILURES.csv` — Structured failure classification
- `SEEN_RECOVERY_CASES.json` — Cases used for DEV only (not confirmatory)
- `SD_H10_CHECKPOINT.json` — Execution checkpoint (created at runtime)
