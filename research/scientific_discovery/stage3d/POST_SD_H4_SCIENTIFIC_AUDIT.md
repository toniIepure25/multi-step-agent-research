# Post-SD-H4 Scientific Audit

## Date: 2026-08-14
## Experiment: SD-H4 SCALED (Self-Correction of Self-Generated Theories)
## Model: gemma3:27b-it-qat

---

## Primary Question

> What is the actual bottleneck in scientific self-correction?

---

## Evidence Summary

| Dimension | Performance | Bottleneck? |
|-----------|-------------|-------------|
| Correct Abandonment | 95.7% | No — near ceiling |
| False Abandonment | 0% | No — perfect protection |
| Self-Authorship Bias | -0.43 (p=0.49) | No — no bias |
| Rationalization | 0% effective | No — clean abandonment |
| Theory Proliferation | 0% | No — no rescue chains |
| **Recovery** | **18.2%** | **YES — primary bottleneck** |
| Belief Calibration | PASS | No — appropriate response |

---

## Primary Bottleneck: RECOVERY AFTER ABANDONMENT

### What This Means

The model is an **excellent scientific critic** but a **limited scientific discoverer**:
- It reliably recognizes when its hypothesis is wrong (95.7%)
- It does not rationalize or rescue failed theories (0%)
- It does not show ownership bias (p=0.49)
- But it rarely identifies the correct alternative (18.2%)

### Why Recovery Is Low

1. **Single-stage protocol**: The model sees decisive evidence once and must immediately abandon AND propose alternative. No iterative exploration.
2. **True markers are specific**: Recovery requires identifying specific domain terminology that may not be in the model's training data for this particular context.
3. **Abandonment is easier than discovery**: Recognizing contradiction requires only logical consistency checking. Proposing alternatives requires domain knowledge and creative hypothesis generation.

### Implications

- Self-correction is **asymmetric**: falsification >> discovery
- This motivates **hypothesis ecology** (SD-H2): if the correct alternative is already in the hypothesis space before falsification, recovery should improve
- This motivates **active experiment design**: iterative evidence gathering might scaffold recovery
- This is consistent with philosophy of science: "Falsification is easy; scientific discovery is hard" — Popper

---

## Secondary Findings

### 1. eco_04 — The Model That Outsmarted the Trap

World eco_04 presented misleading observations suggesting "fire is bad." The model generated the CORRECT hypothesis ("fire suppression causes worse fires") directly from misleading observations. When presented with "decisive" evidence that actually confirmed its hypothesis, it correctly retained it.

This reveals a **world-design vulnerability**: when the model has strong background knowledge, it can resist observation traps. This is scientifically correct behavior, not a failure.

### 2. Zero Rationalization

The model never:
- Invented unsupported rescue assumptions
- Ignored evidence
- Created near-duplicate theories
- Retained confidence while evidence contradicted

This is remarkably clean. It may reflect temperature=0 (deterministic) behavior or the model's strong instruction-following on structured output.

### 3. Uniform SAB Distribution

SAB values: mostly 0 (17/23), with small deviations (-10 to +5). The model treats provenance framing as irrelevant information, which is scientifically correct.

---

## Stage 4 Readiness Assessment

| Prerequisite | Status | Notes |
|--------------|--------|-------|
| Self-correction characterized | ✓ | Robust at 95.7% |
| False abandonment bounded | ✓ | <13.9% (95% CI) |
| Recovery measured | ✓ | 18.2% — the bottleneck |
| Rationalization absent | ✓ | 0% effective |
| Self-authorship absent | ✓ | p=0.49 |
| Proliferation absent | ✓ | 0% |

**All prerequisites met for CONDITIONAL GO.**

---

## Exact Next Actions (Ordered)

1. **SD-H2 Formal Test**: Does hypothesis ecology improve recovery rate?
2. **Multi-stage evidence trajectory**: Does iterative evidence improve recovery?
3. **Stage 4 Planning**: Ontology revision design (detection → generation → validation)
4. **Transfer model test**: Does Llama show same pattern?
5. **Recovery enhancement**: Can we scaffold discovery without oracle leakage?

---

## What We Do NOT Yet Know

- Whether recovery improves with iterative evidence (multi-stage)
- Whether hypothesis ecology meaningfully increases recovery
- Whether the pattern transfers to other models
- Whether temperature > 0 changes rationalization rates
- Whether longer/richer true_markers would improve recovery classification
