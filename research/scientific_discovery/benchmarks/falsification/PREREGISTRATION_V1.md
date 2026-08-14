# FalsificationBench V1 — Preregistration

**Date frozen:** 2026-08-14  
**SHA at freeze:** (to be filled at commit)  
**Status:** LOCKED — do not tune controller against these worlds after this date.

---

## 1. Central Research Question

> Does falsification-first scientific control improve recovery from misleading initial theories relative to passive and confirmation-seeking baselines?

## 2. Primary Hypothesis (SD-H1)

**Claim:** A scientific controller that actively identifies and amplifies falsification signals recovers correct beliefs faster and more reliably than policies lacking this mechanism, while maintaining robustness to false abandonment.

## 3. Worlds

| World Type | Count per seed | Latent Structure |
|---|---|---|
| confirmation_trap | 1 | Early evidence supports false H; later decisive evidence refutes it |
| confounded_causality | 1 | Correlation supports H1 but hidden variable explains both |
| non_identifiable | 1 | Evidence cannot distinguish H1/H2; correct answer is ABSTAIN |
| reverse_causality | 1 | X↔Y correlation but direction is opposite to leading explanation |
| null_world | 1 | No causal relationship; correlation is reporting bias |
| measurement_artifact | 1 | Signal is measurement process artifact, not biology |

**Total world types:** 6  
**Independent unit:** WORLD × SEED

## 4. Seeds

### DEV split (for tuning, freely re-run):
Seeds: 1–10

### VALIDATION split (limited use):
Seeds: 11–20

### LOCKED TEST split (run exactly once):
Seeds: 21–40

**Locked test N per world type:** 20  
**Total locked units:** 120

## 5. Initial Hypotheses Per World

Each world provides 2–3 initial hypotheses with:
- Pre-specified beliefs (one initially favored, typically wrong)
- Typed evidence rounds with per-hypothesis direction
- Known ground truth (correct hypothesis ID)
- Marked decisive round

## 6. Evidence Rounds

Each world contains 2–3 evidence rounds:
- Round 0: Ambiguous/supporting evidence (may mislead)
- Round 1+: Decisive contradicting evidence

Evidence uses `direction_per_hypothesis` for differential updating.

## 7. Policies (Baselines)

| ID | Name | Description |
|---|---|---|
| B0 | Passive Update | No falsification. Standard belief updater. |
| B1 | Confirmation Seeker | Discounts contradictions (falsification_multiplier=0.5). Reluctant to abandon. |
| B2 | Random Challenge | Falsification ON but no amplification (multiplier=1.0). Controls for extra actions. |
| B3 | Falsification-First | Full ASAR Stage 1: falsification proposals amplify recognition of decisive evidence. |
| B4 | Oracle | Uses ground truth for ceiling. Never exposed to agents. |

## 8. Primary Metrics

| Metric | Definition | Better is... |
|---|---|---|
| Recovery Accuracy | Final highest-belief hypothesis == correct hypothesis | Higher |
| Refutation Sensitivity | Belief drop magnitude after decisive evidence | Higher |
| Theory Stickiness | Mean belief on false hypothesis after decisive round | Lower |
| Conclusion Correct Rate | Controller's explicit conclusion matches ground truth | Higher |

## 9. Secondary / Diagnostic Metrics

| Metric | Definition |
|---|---|
| Abandonment Latency | Rounds after decisive evidence before false H abandoned |
| False-Abandonment Rate | Rate of abandoning correct hypothesis |
| Rationalization Rate | New assumptions added after refutation (future) |
| Theory Proliferation | Post-refutation variant creation (future) |

## 10. Smallest Effect Size of Interest (SESOI)

- Recovery Accuracy: Δ ≥ 0.10 (B3 vs B0)
- Refutation Sensitivity: Δ ≥ 0.02 (B3 vs B0)
- Theory Stickiness: Δ ≤ -0.01 (B3 lower than B0)
- False Abandonment Rate: Δ < 0.10 (B3 not catastrophically worse)

## 11. Statistical Analysis

- **Unit:** World × seed (paired across policies)
- **Comparison:** Paired differences (B3 - B0) on each unit
- **Primary test:** Paired permutation test (10,000 permutations)
- **CI:** Bootstrap 95% CI (10,000 resamples)
- **Effect size:** Cohen's d for paired samples
- **Multiple comparisons:** Holm-Bonferroni across 4 primary metrics
- **One-sided tests:** Where direction is preregistered (refutation sensitivity: B3 > B0; stickiness: B3 < B0)

## 12. GO/NO-GO Criteria

### Stage 1 GO requires ALL:

1. **STATE_REPLAY:** PASS (deterministic replay certified)
2. **IMMUTABILITY:** PASS (no hidden mutation)
3. **BELIEF_METAMORPHIC:** ALL 9 invariants PASS
4. **BEHAVIORAL_INFLUENCE:** B3 ≠ B0 belief trajectories (p < 0.05)
5. **NO_ORACLE_LEAKAGE:** PASS
6. **FALSIFICATION_CONTENT_INFLUENCE:** Targeted falsification produces faster drops than untargeted
7. **SD-H1 (Recovery):** B3 ≥ B0 on recovery accuracy (not worse)
8. **SD-H1 (Sensitivity):** B3 > B0 on refutation sensitivity (Δ > SESOI or p < 0.05)
9. **FALSE_ABANDONMENT:** B3 false-abandonment rate < 0.10
10. **NON_IDENTIFIABLE:** System does not create artificial separation (max-min < 0.5)
11. **NULL_WORLD:** Null hypothesis ends with highest belief

### Stage 1 NO-GO if ANY:

- B3 recovery accuracy < B0 (falsification hurts)
- B3 false-abandonment rate > 0.15
- No measurable belief trajectory difference between ON/OFF
- State certification fails

## 13. Contamination Defense

- Worlds are synthetic (no training-data leakage possible)
- Oracle policy never shares information with other policies
- Locked test seeds not used during development
- Controller tuned only on DEV split

## 14. Immutable Record

This preregistration is version-controlled.
Any post-hoc changes to analysis must be documented in NEGATIVE_FINDINGS.md and marked as exploratory.
