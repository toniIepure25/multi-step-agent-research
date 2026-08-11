# Benchmark Card: Epistemic World Simulator

## What is measured

Downstream epistemic quality of cognitive operation sequences from
controlled starting states. The benchmark enables counterfactual
comparison: from the same epistemic state, different operations/sequences
are applied, and their downstream quality is measured against latent
ground truth.

## What is NOT measured

- Real-world research task performance
- Multi-turn agent interaction quality
- Open-ended generation quality
- Knowledge retrieval accuracy against web-scale corpora

## Experimental unit

**World** — a self-contained epistemic reasoning task with latent hypotheses,
evidence corpus, causal structure, and hidden variables.

## Task families

Eight epistemic regimes (A-H) varying:
- Evidence informativeness (high/low)
- Hypothesis discriminability (easy/hard)
- Source independence (independent/dependent)
- Deception structure (present/absent)

## Gold construction

Latent ground truth is specified programmatically in the world generator.
Each world has:
- One true hypothesis (evaluator-only)
- Multiple evidence items with known support/contradiction relationships
- Hidden variables discoverable through attack
- Causal edges with known strengths

## Known confounds

1. **Resource confound:** Longer sequences consume more compute.
   V6 addresses this with matched-budget factorial designs.
2. **Prerequisite structure:** Some operations (attack, reason) have zero
   standalone value because they require prior hypothesis generation.
   This is a design property, not an independent discovery.
3. **Deterministic selection:** Evidence retrieval uses hash-based selection
   (V4/V5) or keyword-overlap selection (V6). Neither is semantic search.

## Failure modes

- Quality metric depends on scalarization weights
- Worlds are generated from templates; limited diversity
- No open-ended evidence acquisition (fixed corpus)
- Hypothesis space is discrete and finite

## Appropriate use

- Controlled measurement of operation-pair interactions
- Counterfactual sequence comparison from matched states
- Ablation studies of cognitive architecture components

## Inappropriate use

- Claims about real-world research agent performance
- Claims about general LLM reasoning capability
- Claims about optimal agent architecture
