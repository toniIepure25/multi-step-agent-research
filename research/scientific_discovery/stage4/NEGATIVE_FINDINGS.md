# Negative Findings — Stage 4

## Finding 24: Detection Specificity Is Poor (60% False Alarm)
**Date:** 2026-08-15
**Context:** ASAR detection step applied to negative control + decoy worlds
**Expected:** System correctly identifies R0-sufficient worlds as not needing revision
**Actual:** 3/5 control worlds incorrectly flagged as needing revision (60% false alarm)
**Detail:** NEG01, DEC01, DEC02 all triggered "INADEQUATE" verdict despite R0 being sufficient
**Mitigation:** Validation gate catches 2 of 3 (DEC01, DEC02 rejected). NEG01 is a true false acceptance.
**Root cause:** The detector has strong pattern-matching for anomaly but lacks rigorous
test of whether anomaly is SYSTEMATIC vs. noise.
**Action:** Detection needs stricter criteria (e.g., require anomaly to be systematic across
multiple observations, not just a single data point).

## Finding 25: Generic Reflection (B2) Has ZERO False-Revision Control
**Date:** 2026-08-15
**Context:** B2 baseline asked "do your assumptions need revision?" on all 15 worlds
**Expected:** Some discrimination between genuine inadequacy and noise
**Actual:** B2 said "needs_revision: true" for ALL 15 worlds (100% false alarm on controls)
**Implication:** Unconstrained LLM reflection CANNOT be used for regime decisions.
When told "consider whether your framework needs revision," the model ALWAYS says yes.
This is analogous to SD-H10's finding that prompting for alternatives always produces them.
**Action:** NEVER use open-ended "should you revise?" prompts without structured evidence gates.

## Finding 26: Recovery Is Near-Ceiling on Current Tasks
**Date:** 2026-08-15
**Context:** Both ASAR (100%) and B2 (90%) achieve near-perfect regime recovery
**Expected:** Regime revision would be genuinely difficult
**Actual:** The model has strong background knowledge of all tested patterns
(confounds, interactions, thresholds, measurement error)
**Implication:** Current benchmark does not stress-test generation capability.
Future versions need genuinely novel representational challenges.
**Action:** Develop synthetic/abstract worlds where correct structure is NOT in
model's training distribution.
