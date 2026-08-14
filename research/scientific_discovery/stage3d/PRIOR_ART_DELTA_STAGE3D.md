# Prior Art Delta — Stage 3D

## Date: 2026-08-14
## Purpose: Position ASAR against concurrent 2026 scientific discovery systems

---

## Comparison Matrix

| System | Object Evaluated | Hypothesis Repr | Active Testing | Belief Revision | Self-Authorship | Theory Abandonment | Rationalization | Multi-Hypothesis | Experiment Cost | Ontology Revision | External Validation |
|--------|-----------------|-----------------|----------------|-----------------|-----------------|-------------------|-----------------|------------------|-----------------|-------------------|---------------------|
| **ASAR** | Scientific self-correction loop | Structured JSON schema | YES (active discrimination) | YES (Bayesian) | YES (SELF/EXT pairing) | YES (explicit) | YES (classified) | YES (ecology) | YES (cost-budget) | Planned (Stage 4) | Planned (FalsifyBench) |
| **FalsifyBench** | Inductive rule discovery | Natural language hypothesis | YES (propose examples) | Implicit (iterate) | NO | Implicit (change hypothesis) | NO | NO (single H at a time) | Fixed budget (turns) | NO | Self-contained |
| **Google Co-Scientist** | Hypothesis novelty/quality | Natural language + literature | NO (generates, doesn't test) | NO (tournament selection) | NO | NO | NO | YES (tournament) | Compute scaling | NO | Expert evaluation |
| **AI Scientist v2** | End-to-end paper generation | Code + manuscript | YES (run experiments) | Implicit (tree search) | NO | NO | NO | Implicit (tree branches) | Compute budget | NO | Peer review |
| **ResearchBench** | Hypothesis composition | Natural language | NO (static evaluation) | NO | NO | NO | NO | YES (ranking) | N/A | NO | Human validation |
| **Self-Revising Discovery** | Regime transition formalism | Category-theoretic schema | NO (theoretical) | NO (formal only) | NO | Formal definition only | NO | NO | NO | YES (core contribution) | Materials science cases |

---

## WHAT DOES ASAR TEST THAT FALSIFYBENCH DOES NOT?

### FalsifyBench Protocol
- Agent proposes examples to test a hidden semantic rule (Wason 2-4-6 generalized)
- Oracle provides YES/NO feedback per example
- Agent iterates and eventually guesses the rule
- Key metric: negative testing rate predicts success

### ASAR Distinct Contributions (must be demonstrated, not asserted)

| Claimed Gap | Status | Evidence |
|-------------|--------|----------|
| Structured multi-hypothesis ecology | DEMONSTRATED | SD-H2 protocol exists, ecology vs single comparison |
| Self vs external hypothesis provenance | DEMONSTRATED | SD-H4 SELF/EXTERNAL pairing with SAB measurement |
| Explicit theory abandonment | DEMONSTRATED | Confidence trajectory + should_abandon decision |
| False-abandonment protection | DEMONSTRATED (pilot) | Correct theories retained under noise |
| Rationalization / rescue detection | FRAMEWORK EXISTS | Classification scheme ready, needs stress testing |
| Experiment discrimination (cost-aware) | DEMONSTRATED | JSD policy with cost budget |
| Scientific failure localization | FRAMEWORK EXISTS | Taxonomy defined but not yet populated at scale |
| Provenance-aware belief state | DEMONSTRATED | Self-authorship bias measurement |
| Future ontology revision | NOT YET TESTED | Deferred to Stage 4 |

### FalsifyBench Overlap with ASAR
- Both evaluate negative testing / falsification behavior
- Both show confirmation bias is detrimental
- Both iteratively gather evidence and revise hypotheses
- FalsifyBench uses simpler task structure (semantic categories vs scientific mechanisms)

### NOVELTY ASSESSMENT
FalsifyBench substantially overlaps ASAR's core claim that "falsification-oriented behavior outperforms confirmation."

ASAR's DISTINCT value lies in:
1. **Self-authorship** — does provenance of a hypothesis affect willingness to abandon it?
2. **Theory abandonment as explicit decision** — not just changing hypothesis but explicitly marking old one as abandoned
3. **Structured hypothesis ecology** — maintaining multiple mechanistically distinct alternatives
4. **Experiment DESIGN** — choosing WHICH test to run (FalsifyBench agent only proposes examples)
5. **Failure localization** — diagnosing WHERE in the scientific loop breakdown occurs

FalsifyBench does NOT test points 1-5. These remain ASAR's primary novelty claims.

---

## STAGE 4 NOVELTY THREAT

### Self-Revising Discovery Systems (Wang & Buehler, 2026)
- Explicitly formalizes discovery as schema/regime transition
- Uses category theory (copresheaves, Kan extensions)
- Defines novelty as "residual content beyond functorial transport"
- Instantiated in materials science (Builder/Breaker, CategoryScienceClaw)

### Threat to ASAR Stage 4
Stage 4 CANNOT simply claim "our agent revises its ontology."
Wang & Buehler already provide the theoretical framework.

### ASAR Stage 4 Distinct Question (if it proceeds)
> Can an empirically-grounded generative scientist DETECT that its hypothesis space is structurally insufficient, PROPOSE a representation revision, and VALIDATE that the revision improves predictions?

This is an EMPIRICAL test of the detection-generation-validation loop.
Wang & Buehler provide formal definitions but no LLM-based empirical evaluation of detection accuracy.

---

## FalsifyBench Code Availability
Repository: https://github.com/leobertolazzi/FalsifyBench.git
License: needs verification
Status: PUBLIC, potentially integratable for external validation
