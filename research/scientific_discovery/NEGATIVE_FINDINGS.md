# Negative Findings & Honest Limitations

**Updated:** 2026-08-14 (Stage 3 hardening)

---

## Finding 1: Recovery Accuracy Tied Between B3 and B0

**Observation:** B3 (falsification-first) achieves identical recovery accuracy (0.833) to B0 (passive update) across all world types.

**Explanation:** In the current controlled worlds, the evidence is strong enough that ALL policies (except confirmation-seeking B1) eventually identify the correct hypothesis. The decisive evidence is so decisive that even without amplification, the belief updater correctly promotes the true hypothesis.

**Implication:** The falsification advantage shows primarily in the *speed* and *completeness* of belief revision, not in the final outcome for these world difficulties. Harder worlds (weaker evidence, more noise) may show differentiation in final recovery.

**Classification:** Expected behavior for well-designed decisive evidence. Not a failure, but limits the headline claim.

---

## Finding 2: Initial FalsificationEngine Was Decorative (Fixed)

**Date:** 2026-08-14

**What happened:** The initial implementation of `ScientificController` generated falsification proposals but did NOT use them to influence belief updates. B3 and B0 produced *identical* belief trajectories. The FalsificationEngine was purely logging.

**What was tried:** Running benchmark comparison with `enable_falsification=True` vs `False`.

**Root cause:** The controller called `propose_falsification()` and recorded the proposal as an event, but the actual `update_ecology()` call used the same parameters regardless. The proposals were never fed back into the processing pipeline.

**Fix:** Added `_compute_falsification_boost()` to the controller. When evidence contradicts the target of an active falsification proposal, the effective independence score is amplified (1.5×), producing larger belief drops. This makes the proposals causally connected to outcomes.

**Lesson:** Components must be BEHAVIORALLY TESTED, not just structurally present. The behavioral influence test caught this immediately.

---

## Finding 3: Single `direction` Field Insufficient for Multi-Hypothesis Evidence

**Date:** 2026-08-14

**What happened:** Evidence that contradicts H1 may simultaneously *support* H2 (e.g., temporal precedence data contradicting "exercise → mood" supports "mood → exercise"). The original `ScientificEvidence` schema had a single `direction` field applied uniformly to all hypotheses.

**Result:** In reverse-causality and null-world scenarios, evidence that should support the correct hypothesis instead contradicted it, leading to incorrect belief trajectories.

**Fix:** Added `direction_per_hypothesis: dict[str, EvidenceDirection]` field to `ScientificEvidence`, with a `direction_for(hypothesis_id)` method that falls back to the global direction. All extended worlds use this for proper differential evidence.

**Lesson:** Scientific evidence frequently has asymmetric implications for competing hypotheses. The schema must support this.

---

## Finding 4: Effect Size B3 vs B0 is Moderate

**Observation:** The paired difference in refutation sensitivity is +0.021 (B3 > B0). While statistically significant (p < 0.0001, N=60), the magnitude is moderate.

**Context:** This is on the DEV split with predetermined evidence rounds. The effect comes entirely from a single mechanism (recognition amplification at boost=1.5). In a full system with:
- Active evidence search guided by falsification proposals
- Multi-round adaptive falsification strategies
- LLM-generated discriminative evidence

...the effect should be substantially larger. The current result establishes the *direction* and *mechanism*, not the ultimate magnitude.

**Status:** Expected for Stage 1 (minimal viable mechanism). Not a failure.

---

## Finding 5: Non-Identifiable World Shows 0% Recovery (By Design)

**Observation:** Both B3 and B0 achieve 0% recovery on non-identifiable worlds.

**This is correct behavior.** In a non-identifiable world, no hypothesis can be definitively identified as correct. The system correctly avoids creating artificial certainty. Recovery accuracy = 0 here means "correctly does not claim recovery" not "fails to recover."

---

## Finding 6: B3-ZERO = B0 (Falsification Policy Alone Has No Effect)

**Date:** 2026-08-14 (Anti-tautology audit)

**Observation:** B3-ZERO (falsification proposals generated but no recognition boost) produces IDENTICAL metrics to B0 (passive). The falsification policy contributes 0% of the total effect; 100% comes from the recognition boost (1.5× amplification).

**Root Cause:** In controlled worlds with predetermined evidence, the falsification policy can only affect behavior through:
1. Evidence *selection* (not available — evidence is fixed)
2. Evidence *interpretation* (the boost mechanism)

Since B3 cannot choose different evidence to observe, its proposals are computationally generated but never acted upon. The only pathway for behavioral influence is the boost.

**Implication:** 
- Stage 1 demonstrates that DIFFERENTIAL INTERPRETATION of evidence (recognition of falsification-relevant evidence as more decisive) improves belief trajectories
- Stage 1 does NOT demonstrate that the ACTION of identifying falsifiers provides independent value when evidence is predetermined
- Stage 2 (experiment design) is where action selection genuinely matters

**Classification:** This is an honest methodological finding, not a failure. The claim must be:
> "Recognition-enhanced belief updating improves scientific self-correction"

NOT:
> "The falsification policy improves scientific self-correction"

The latter claim requires Stage 2 validation (experiment selection).

---

## Finding 7: Active Science — Discrimination vs Confirmation Nearly Tied

**Date:** 2026-08-14 (Stage 3)

**Observation:** In active worlds, discrimination (0.900) barely outperforms confirmation (0.883) for recovery. The Δ=+0.017 with CI crossing zero.

**Interpretation:** Both policies benefit from Bayesian updating with real observations. The Bayesian update itself is powerful enough that even confirmation-seeking policies eventually identify truth. The critical gap is vs RANDOM (0.700) and PASSIVE (0.267).

**Implication:** The primary benefit of experiment selection is avoiding UNINFORMATIVE experiments (passive/random), not the specific distinction between confirmation and discrimination in these 3-hypothesis worlds. Harder worlds (more hypotheses, less budget) may widen the gap.

---

## Finding 8: Hardened Stage 2 — E3 Still Near-Optimal (69% Zero Regret)

**Date:** 2026-08-14 (Stage 3)

**Observation:** Even with noisy predictions, E3 achieves zero regret on 69% of tasks. The JSD heuristic remains a strong proxy even with miscalibrated predictions.

**Implication:** The discrimination scoring rule is robust but may still be too strong for these world designs. Sequential experiment design (where greedy ≠ optimal) would further challenge it.

---

## Future Risk Areas

1. **False abandonment under noise:** Current worlds have clean decisive evidence. Noisier evidence may reveal sensitivity.

2. **Confirmation-seeker resilience:** In active worlds, confirmation nearly matches discrimination. Harder worlds with more hypotheses needed.

3. **Sequential experiment design not yet tested:** Greedy JSD may fail when locally suboptimal experiments enable better follow-ups.

4. **LLM integration may expose generation quality as bottleneck:** If LLM generates weak hypotheses, self-correction quality is secondary.

5. **Self-authorship bias unknown:** Until LLM integration, we cannot measure whether systems protect their own hypotheses.
