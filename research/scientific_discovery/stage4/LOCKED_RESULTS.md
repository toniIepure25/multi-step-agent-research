# Stage 4A — LOCKED Results

## Representational Regime Revision

---

## Summary

ASAR's structured pipeline (Detect → Generate → Validate) achieves **100% end-to-end
regime recovery** on true regime-failure worlds while providing meaningful **false-revision
control** that generic reflection (B2) completely lacks.

---

## ASAR Results (Structured Pipeline)

### SD-H11: Detection

| World Type | N | Correct | Rate |
|-----------|---|---------|------|
| Regime-failure (A-F) | 10 | 10 | 100% |
| Negative controls | 3 | 2 | 66.7% |
| Decoy | 2 | 0 | 0% |

- **True detection rate**: 10/10 = 100%
- **False revision rate (detection-level)**: 3/5 = 60%
- **Net false acceptance (after validation gate)**: 1/5 = 20%

The detection step has perfect sensitivity but imperfect specificity. The validation
gate provides a second line of defense, catching 2 of 3 false alarms.

### SD-H12: Generation

| Metric | Value |
|--------|-------|
| Correct structure (among detected) | 10/10 = 100% |
| Revision types correctly identified | 10/10 |

When the regime IS inadequate, the model correctly identifies the missing structure
every time. Generation capability is not the bottleneck.

### SD-H13: Validated Transition

| Metric | Value |
|--------|-------|
| End-to-end regime recovery | 10/10 = 100% |
| Correct validation (accept correct) | 10/10 |
| Correct rejection (decoy) | 2/2 |
| False acceptance (NEG01) | 1/5 |

### End-to-End by Family

| Family | Type | Detection | Generation | End-to-End |
|--------|------|-----------|------------|------------|
| A (×3) | Hidden variable | 3/3 ✓ | 3/3 ✓ | 3/3 ✓ |
| B (×2) | Interaction | 2/2 ✓ | 2/2 ✓ | 2/2 ✓ |
| C (×2) | Nonlinear/threshold | 2/2 ✓ | 2/2 ✓ | 2/2 ✓ |
| D (×1) | Temporal memory | 1/1 ✓ | 1/1 ✓ | 1/1 ✓ |
| E (×1) | Measurement model | 1/1 ✓ | 1/1 ✓ | 1/1 ✓ |
| F (×1) | Latent mixture | 1/1 ✓ | 1/1 ✓ | 1/1 ✓ |
| NEG (×3) | Sufficient (control) | 2/3 | — | 2/3 |
| DEC (×2) | Decoy (overfit) | 0/2 | — | 2/2 |

---

## B2 Results (Generic Reflection Baseline)

| Metric | Value |
|--------|-------|
| True detection | 10/10 = 100% |
| False revision rate | 5/5 = 100% |
| End-to-end regime recovery | 9/10 = 90% |
| Negative control pass | 0/3 = 0% |
| Decoy control pass | 0/2 = 0% |

**B2 always says "needs revision"** — it has zero discrimination between genuine
regime failure and noise/outliers/overfitting.

---

## Primary Contrast: ASAR vs B2

| Metric | ASAR | B2 | Advantage |
|--------|------|----|-----------|
| End-to-end recovery (regime-failure) | 10/10 = 100% | 9/10 = 90% | +10% |
| False revision control | 4/5 = 80% | 0/5 = 0% | **+80%** |
| Negative control pass | 2/3 = 67% | 0/3 = 0% | +67% |
| Decoy rejection | 2/2 = 100% | 0/2 = 0% | +100% |

**The critical difference is NOT in regime recovery** (both are high) **but in
FALSE REVISION CONTROL** — knowing when NOT to revise.

---

## SD-H11 Verdict: PARTIALLY SUPPORTED

Detection is perfect (10/10) but false-alarm rate is too high (3/5 = 60%).
The validation gate compensates (net false acceptance = 1/5 = 20%).
Detection needs improvement but the pipeline structure provides safety.

## SD-H12 Verdict: SUPPORTED

Generation is perfect when detection triggers appropriately (10/10).
The model correctly identifies all missing structural types.

## SD-H13 Verdict: SUPPORTED

The validation gate correctly accepts 10/10 valid revisions and rejects
2/3 invalid ones that bypass detection. One false acceptance (NEG01).

## SD-H14 Verdict: NOT TESTED

Active regime discrimination was not implemented in this round
(would require additional experiment design step).

---

## Negative Findings

1. **Detection specificity is poor** (60% false alarm on controls).
   The detector is too eager to declare inadequacy.

2. **B2 has ZERO false-revision control**. Generic "rethink your assumptions"
   always produces a revision, even when none is needed. This confirms that
   unconstrained LLM reflection cannot be trusted for regime decisions.

3. **Small sample size** (N=10 regime-failure, N=5 control). Results are
   promising but not yet statistically powerful.

---

## Resources

| Metric | Value |
|--------|-------|
| Total calls | 56 |
| Total tokens | 37,206 |
| Wall time | ~13 min |
| Calls per ASAR world | 3 (detect + generate + validate) |
| Calls per B2 world | 1 |

---

## Implications

1. **Structured pipeline IS valuable** — not for recovery (which is already high)
   but for **false-revision protection**

2. **The validation gate is the key component** — it catches false alarms that
   bypass detection

3. **Detection needs hardening** — currently too sensitive (perfect recall,
   poor precision on controls)

4. **Generic reflection is dangerous** — it ALWAYS revises, making it unreliable
   for production use

5. **Stage 4 mechanism works** — the model CAN detect inadequacy, generate
   correct structure, and validate transitions when the task is properly framed
