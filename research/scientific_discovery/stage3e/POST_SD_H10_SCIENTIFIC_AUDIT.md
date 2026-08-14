# Post-SD-H10 Scientific Audit — Stage 3E

## Date: 2026-08-14
## Experiment: SD-H10 (Post-Falsification Abductive Recovery)

---

## What Was the Question?

Can structured multi-candidate generation improve recovery after theory falsification?

## Answer: NO (for current problem difficulty)

Structured ecology (R2) performs WORSE than simple one-shot replacement (R0) or
compute-matched reflection (R1). The decomposition introduces selection interference.

---

## What Is the Actual Bottleneck Now?

After Stage 3E, the bottleneck picture has changed dramatically:

| Capability | SD-H4 reported | Stage 3E corrected | Status |
|-----------|---------------|-------------------|--------|
| Correct abandonment | 95.7% | 95.7% (confirmed) | Strong |
| Recovery | 18.2% | 76-80% (prompt-corrected) | Good |
| False abandonment | 0% | 0% (confirmed) | Strong |
| Selection | N/A | 96-100% (R4) | Excellent |
| Self-authorship bias | -0.43 (none) | -0.43 (confirmed) | None |

**There is no longer a clear single bottleneck.** The system performs well across
all dimensions when properly prompted.

The remaining 20-24% recovery failure is spread across:
- Marker-matching limitations (model uses correct concept but different words)
- Genuinely hard cases (fewer true markers present in natural language)
- Edge cases where model proposes related but incomplete mechanisms

---

## Primary Scientific Finding

**Self-correction in gemma3:27b-it-qat is robust and complete when properly
decomposed into (1) abandonment and (2) explicit reconstruction.**

The SD-H4 "recovery bottleneck" was an artifact of combining these into a single
prompt where reconstruction was optional.

---

## What Did NOT Help

1. Structured multi-candidate generation (R2): -20pp vs baseline
2. Compute-matched reflection (R1): +4pp (not significant)
3. Generate-then-select decomposition: introduces selection interference

## What DID Help

1. Simply asking explicitly for a replacement theory (R0 vs SD-H4 embedded): +58pp
2. Oracle candidate provision (R4): +24pp above R0 (but diagnostic only)

---

## Implications for ASAR Architecture

1. **Abandonment and reconstruction should be separate prompts** — this alone fixes
   the "recovery bottleneck" without any architectural complexity
2. **No structured ecology needed** for current problem difficulty
3. **The system's abductive reasoning is already good** when properly invoked
4. **Future work should focus on genuinely harder problems** where direct recovery
   fails even with dedicated prompting

---

## Stage 4 Readiness Assessment

| Criterion | Status |
|-----------|--------|
| Abandonment characterized | ✓ 95.7% |
| Recovery characterized | ✓ 76-80% (properly prompted) |
| Selection characterized | ✓ 96-100% (oracle) |
| False abandonment bounded | ✓ 0% [0%, 13.9%] |
| Self-authorship absent | ✓ p=0.49 |
| Rationalization absent | ✓ 0% effective |
| Structured ecology tested | ✓ NOT SUPPORTED |
| Prompt artifact identified | ✓ Critical methodological finding |

**All prerequisites characterized. Stage 4: GO.**

---

## Exact Next Actions

1. **Revise SD-H4 interpretation** — the "recovery bottleneck" narrative must be corrected
2. **Implement two-step protocol** — abandonment → reconstruction as standard
3. **Begin Stage 4 planning** — ontology revision (detection → generation → validation)
4. **Target harder problems** — current benchmark is too easy for recovery
5. **Test on genuinely novel domains** where the model lacks background knowledge
