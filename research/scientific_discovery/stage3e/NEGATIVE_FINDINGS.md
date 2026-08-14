# Negative Findings — Stage 3E

## Finding 20: Structured Ecology HURTS Recovery (SD-H10 NOT SUPPORTED)
**Date:** 2026-08-14
**Context:** SD-H10 — does structured multi-candidate generation improve post-falsification recovery?
**Expected:** R2 (generate multiple candidates then select) > R1 (simple reflection)
**Actual (LOCKED):** R2 = 60.0% vs R1 = 80.0% (effect = -0.200, p = 0.096)
**Actual (DEV):** R2 = 69.6% vs R1 = 91.3% (effect = -0.217, p = 0.057)
**Root cause:** Self-generated candidate sets are harder to select from than oracle sets.
Selection|Coverage = 68% (self) vs 100% (oracle). The two-step decomposition adds noise.
**Implication:** DO NOT add structured ecology as a default recovery mechanism for this
model and problem difficulty level. Simple direct prompting outperforms.
**Action:** SD-H10 marked NOT_SUPPORTED. Architecture recommendation reversed.

## Finding 21: SD-H4 "Recovery Bottleneck" Was a Prompt Artifact
**Date:** 2026-08-14
**Context:** SD-H4 reported 18.2% recovery, interpreted as fundamental abductive failure
**Expected:** Low recovery = model cannot identify correct mechanism
**Actual:** Same model, same evidence, different prompt → 76-80% recovery
**Root cause:** SD-H4 embedded `new_explanation` as an optional field in the abandonment JSON.
Model focused on abandonment decision, treating reconstruction as secondary.
**Implication:** Prompt structure has dramatic effects on measured capabilities. A 57pp difference
from prompt design alone should caution against interpreting single-protocol results as
fundamental capability measurements.
**Action:** Revised interpretation: model CAN recover when properly prompted. The "recovery
bottleneck" is an evaluation methodology issue, not a model limitation.

## Finding 22: Self-Generated Candidates Create Selection Interference
**Date:** 2026-08-14
**Context:** R2 generates 4-6 candidates then selects; R4 uses oracle candidates
**Expected:** Selection|Coverage should be similar whether candidates are self-generated or oracle
**Actual:** Selection|Coverage: 68% (self-generated) vs 100% (oracle)
**Root cause:** Model's own text creates coherent but potentially misleading alternatives.
Oracle candidates are more orthogonal and distinctly phrased.
**Implication:** Generate-then-select architectures may introduce selection interference that
doesn't exist in direct generation. This is a general caution for multi-step reasoning systems.
**Action:** Do not assume decomposition always helps. Test empirically.

## Finding 23: Compute-Matched Reflection Provides No Significant Benefit
**Date:** 2026-08-14
**Context:** R1 adds "reflect carefully" instruction and ~200 more tokens vs R0
**Actual (LOCKED):** R1 = 80% vs R0 = 76% (difference not significant at N=25)
**Implication:** For this problem type, simple direct prompting is nearly optimal.
Additional tokens for reflection provide marginal or no benefit.
**Action:** Default to simple recovery prompts unless problem difficulty warrants more.
