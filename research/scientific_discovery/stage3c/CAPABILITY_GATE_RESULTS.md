# Capability Gate Results — Stage 3C

## Date: 2026-08-14
## Protocol: C1-C7 executed against real LLM inference

---

## PRIMARY MODEL: gemma3:27b-it-qat (27.4B, Q4_0)

| Capability | Result | Detail |
|-----------|--------|--------|
| C1: Hypothesis Generation | PASS | Generates structured hypothesis with claim, mechanism, scope, assumptions, predictions, falsifiers |
| C2: Mechanistic Alternatives | PASS | Produces genuinely distinct alternative mechanisms (e.g., BDNF neuroplasticity vs oxytocin) |
| C3: Prediction Derivation | PASS | Correct directional predictions from hypothesis + experiment |
| C4: Falsifier Generation | PASS | Specific, testable falsification criteria (e.g., OXTR knockout) |
| C5: Confound Detection | NOT TESTED | Deferred (requires controlled confound worlds) |
| C6: Experiment Proposal | PASS | 2x2 factorial design with hypothesis-specific predictions |
| C7: Structured Output | 5/5 = 100% | All outputs parse as valid JSON after markdown fence removal |

### VERDICT: VALID_EXPERIMENTAL_SUBSTRATE

### Performance Characteristics
- Mean latency: 14.1s per call
- Token usage: 70-412 tokens per response
- Parse repair: markdown fence stripping required (100% of responses)
- Retry rate: 0%

---

## TRANSFER MODEL: llama3.2-vision:11b-instruct-q8_0 (10.7B, Q8_0)

| Capability | Result | Detail |
|-----------|--------|--------|
| C1: Hypothesis Generation | PASS | Valid structured hypothesis |
| C3: Prediction Derivation | FAIL | Prepends text before JSON ("Here is the JSON output:") |
| C4: Falsifier Generation | PASS | Valid falsification criteria |
| C7: Structured Output | 2/3 = 67% | Lower schema compliance due to text preambles |

### VERDICT: PARTIAL_EXPERIMENTAL_SUBSTRATE

### Note on Transfer Self-Correction
Despite partial schema compliance, the transfer model demonstrates PERFECT self-correction:
- Confidence drops to 0 after decisive falsification
- Correctly abandons wrong hypothesis
- Identifies correct new explanation

---

## CAPABILITY GATE THRESHOLD DECISIONS (frozen before LOCKED execution)
- VALID requires: C1 PASS, C2 PASS, C3 PASS, C4 PASS, C7 >= 80%
- PARTIAL requires: C1 PASS, C4 PASS, C7 >= 50%
- Below PARTIAL: INVALID_EXPERIMENTAL_SUBSTRATE → Stage 3C blocked
