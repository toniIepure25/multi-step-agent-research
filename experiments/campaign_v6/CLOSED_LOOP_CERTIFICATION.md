# V6 Closed-Loop Certification

## Design

V6 establishes causal LLM → state → outcome pathways:

### 1. Hypothesis Generation → State
LLM generates hypothesis text → parsed → keyword-matched to nearest latent
hypothesis → latent hypothesis activated in simulator state → affects all
downstream operations.

The LLM's hypothesis quality determines WHICH latent hypothesis gets
activated (keyword overlap scoring), creating causal dependence.

### 2. Retrieval → Query-Conditioned Evidence
LLM generates retrieval query JSON → query keywords extracted →
evidence pool scored by keyword overlap with query → highest-scoring
unrevealed evidence selected.

Different queries causally produce different evidence, which affects
all downstream reasoning and evaluation.

### 3. Reasoning → Posterior Update
LLM performs reasoning → sim.reason() computes consistency scores →
consistency scores UPDATE hypothesis posteriors → updated posteriors
affect evaluate() and synthesis decisions.

### 4. Attack → Hidden Variable Discovery
LLM identifies attack target hypothesis → sim.attack_hypothesis()
called with LLM-specified target → may discover hidden variables →
discovered variables enter evaluate() inputs.

### 5. Synthesis → Final Prediction
LLM produces synthesis with best_hypothesis_id → if valid, updates
posterior confidence for identified hypothesis → affects final
evaluation via posteriors.

## Causal Chain Test

To verify causality, an artifact-swap experiment (Phase 33) will
compare:
- Real task-specific hypothesis → downstream trajectory A
- Shuffled hypothesis from different task → downstream trajectory B

If A ≠ B on the same task, the LLM artifact causally affects outcomes.

## Remaining Limitation

The simulator's evidence pool is finite and pre-generated.
Query-conditioned retrieval selects from this pool based on keyword
overlap. This is a controlled approximation of semantic search, not
true information retrieval. The causal chain is:

LLM query → keyword selection → evidence item → state change

This is causally meaningful but not equivalent to web-scale retrieval.
