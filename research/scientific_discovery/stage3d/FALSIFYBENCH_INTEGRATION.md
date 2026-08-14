# FalsifyBench Integration — Stage 3D

## Date: 2026-08-14
## Status: FEASIBILITY ASSESSMENT

---

## FalsifyBench Overview

- **Paper:** Bertolazzi, Tentori, Bernardi (arXiv:2606.04751, June 2026)
- **Task:** Discover hidden semantic category from WordNet taxonomy
- **Protocol:** Agent proposes examples, receives YES/NO oracle feedback, guesses rule
- **Benchmark:** 100 games across 5 categories (animal, artifact, body part, food, plant)
- **Key finding:** Negative testing (falsification) strongly predicts success
- **Code:** https://github.com/leobertolazzi/FalsifyBench.git (PUBLIC)

---

## Integration Feasibility

| Requirement | Status |
|-------------|--------|
| Code publicly available | YES |
| License permits evaluation | NEEDS VERIFICATION |
| Compatible with local models | LIKELY (JSON-constrained interaction) |
| Evaluation metric defined | YES (accuracy, turns, negative testing rate) |
| Can evaluate Gemma/Llama | YES (supports custom models) |

---

## Planned Evaluation Design

### Models
1. PRIMARY: gemma3:27b-it-qat (base model, no ASAR control)
2. TRANSFER: llama3.2-vision:11b-instruct-q8_0 (base model)
3. PRIMARY + ASAR Scientific Control (structured hypothesis management)

### Conditions
- BASE: Standard model with FalsifyBench default prompts
- BASE + NEGATIVE: Model prompted to prioritize negative testing
- ASAR CONTROL: Model guided by ASAR's scientific controller (if architecturally compatible)

### Budget Matching
- Match total interaction turns across conditions
- Do NOT give ASAR extra observations

### Metrics (FalsifyBench native)
- Success rate (correct rule identification)
- Negative testing rate (proportion of falsification attempts)
- Conclusive falsification rate
- Turns to success
- Turn-level hypothesis navigation patterns

---

## What This Tests

FalsifyBench directly validates:
- Does active negative testing improve inductive reasoning? (overlaps ASAR SD-H1)
- Does the model revise hypotheses after disconfirmation?

FalsifyBench does NOT test:
- Self-authorship / provenance effects
- Experiment DESIGN (choice of which test)
- Multi-hypothesis ecology maintenance
- Theory abandonment as explicit decision
- Rationalization detection
- Cost-aware experimentation

---

## ASAR-Specific Capabilities to Report Separately

After running FalsifyBench native metrics, separately report ASAR-only evaluations:
1. Did the model maintain multiple hypothesis candidates? (ecology)
2. Did it explicitly mark hypotheses as abandoned? (abandonment)
3. Did it attempt ad-hoc rescue after falsification? (rationalization)
4. Did it select tests for discrimination vs confirmation? (experiment design)

These are NOT measured by FalsifyBench and represent ASAR's distinct contribution.

---

## Execution Dependencies
- Clone FalsifyBench repository
- Verify license compatibility
- Adapt model interface for Ollama/OpenAI-compatible endpoint
- Run on 100 benchmark games per condition
- Estimated: ~300 games × ~10 turns × ~15s = ~12.5 hours inference

---

## GO/NO-GO Decision
If FalsifyBench code is incompatible with local Ollama models or license prohibits:
- Document as NOT_EXECUTABLE
- This does not block Stage 3D
- External validation becomes a limitation, not a failure
