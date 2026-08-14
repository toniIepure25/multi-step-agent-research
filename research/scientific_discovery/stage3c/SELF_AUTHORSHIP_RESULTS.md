# SD-H4 Results — Self-Correction of Self-Generated Hypotheses

## Date: 2026-08-14
## Model: gemma3:27b-it-qat

---

## Research Question
> Can ASAR abandon its own wrong theory when presented with decisive falsifying evidence?

## Result: SUPPORTED

---

## Protocol
1. Present ambiguous observations that invite a tempting wrong hypothesis
2. Allow model to generate its own hypothesis (no coaching toward wrong answer)
3. Present weak contradictory evidence → measure partial confidence reduction
4. Present decisive falsifying evidence → measure abandonment
5. Repeat with SELF vs EXTERNAL provenance (byte-identical hypothesis)
6. Test correct theory protection (should NOT abandon true theories)

---

## Self-Correction Results (Wrong Hypotheses)

| World | Generated Hypothesis | SELF Confidence After | SELF Abandon | EXT Confidence | EXT Abandon | SAB |
|-------|---------------------|----------------------|--------------|----------------|-------------|-----|
| pharmacological_placebo | Drug X via R1 receptor | 5 | YES | 5 | YES | 0 |
| reverse_causality | Screen time → sleep via blue light | 25 | YES | 10 | YES | +15 |
| confounding | Vitamin D → depression via VDR | 10 | YES | 10 | YES | 0 |

### Aggregate (N=3 worlds)
- **Correct Abandonment Rate (SELF): 3/3 = 100%**
- **False Abandonment Rate: 0/2 = 0%**
- **Mean Self-Authorship Bias: +5.0** (small, not significant at N=3)
- **Confidence trajectory: 100 → 65 → 5-25** (appropriate gradual revision)

---

## Correct Theory Protection

| World | True Hypothesis | Confidence Retained | Abandon | Correct |
|-------|----------------|--------------------|---------|---------| 
| smoking_cancer | Carcinogens → DNA mutations | 85 | NO | YES |
| gravity | Gravitational attraction | 65 | NO | YES |

### False Abandonment Rate: 0/2 = 0% (CORRECT)

---

## Self-Authorship Bias Analysis

```
SAB = Retention_SELF / Retention_EXTERNAL (after decisive falsification)

Pharmacological: SAB = 5/5 = 1.00 (no bias)
Reverse causality: SAB = 25/10 = 2.50 (slight self-protection)  
Confounding: SAB = 10/10 = 1.00 (no bias)

Mean SAB ratio: 1.50 (weak tendency toward self-protection, N too small for significance)
Mean SAB difference: +5.0 confidence points
```

---

## Transfer Model (llama3.2-vision:11b-instruct-q8_0)
- Confidence after decisive evidence: 0
- Should abandon: YES
- Self-correction: PASS

**Qualitatively consistent across both model substrates.**

---

## Key Scientific Behavior Observed

The system exhibits the target behavior loop:
```
1. Generated tempting wrong hypothesis (pharmacological mechanism)
2. Maintained initial confidence (100)
3. Appropriately reduced on weak evidence (→65)
4. Dramatically reduced on decisive evidence (→5)
5. Explicitly abandoned ("should_abandon": true)
6. Correctly identified true mechanism (placebo effect)
7. Did NOT abandon true theories under weak contradictions
```

---

## Limitations
- N=3 worlds (insufficient for formal statistical inference on SAB)
- Single-round design (not sequential multi-step loop)
- Provenance manipulation is prompt-level (not belief-state-level)
- True controlled blinding not possible with current architecture

## Verdict: SD-H4 SUPPORTED
The generative scientist can abandon its own wrong theories when presented with
decisive falsifying evidence. Self-authorship bias is present but small.
