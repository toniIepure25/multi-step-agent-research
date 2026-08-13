# Final Contributions

## Contribution 1 — Evaluation Methodology

A resource-matched, trace-certified intervention framework for auditing the downstream effects of intermediate cognitive artifacts in retrieval-augmented LLM pipelines. Five randomized conditions (Real Hypothesis, Shuffled Hypothesis, Neutral Artifact, Generic Query Expansion, Direct Query) isolate artifact semantics from query quality. Compute, retrieval budget, and model calls are equalized across conditions. Preregistered analysis with Holm-corrected inference over 14 simultaneous tests.

**Distinguishes from prior work:** Unlike standard RAG evaluation (retrieval relevance + answer quality), our framework experimentally manipulates the connection between artifact intervention and downstream utility at each pipeline stage.

## Contribution 2 — Retrieval–Reasoning Dissociation

Empirical evidence across SciFact (claim verification, N=88 unseen + 100 transfer) and HotpotQA (multi-hop QA, N=300 unseen + 100 transfer) that improved evidence retrieval does not imply improved downstream reasoning. Real hypothesis artifacts improve gold evidence recall by +0.18 to +0.51 across all four dataset-model cells (all p_Holm < .002), but this same retrieval gain improves HotpotQA F1 (+0.12, p_Holm < .002) while harming SciFact accuracy (-0.23 to -0.39, p_Holm < .002).

**Why this matters:** Retrieval metrics are commonly used as proxies for system utility. This demonstrates they can be directionally misleading.

## Contribution 3 — Cross-Model Replication

All qualitative patterns — retrieval benefit, task-dependent downstream utility, and generic expansion sufficiency — replicate across Gemma 27B and Llama 11B model families. Direction consistency is observed on all primary contrasts, though effect magnitudes vary.

**What this does NOT claim:** We do not claim model invariance, universality, or architecture independence. The claim is qualitative consistency across two evaluated substrates.

## Contribution 4 — Mechanistic Diagnosis

A stagewise decomposition showing that SciFact degradation is associated with evidence integration failure rather than direct hypothesis anchoring. Key evidence: (a) artifact visibility ablation shows small, non-significant accuracy harm after Holm correction; (b) answer flip analysis shows that conditions retrieving more evidence produce more harmful flips (correct-to-wrong transitions); (c) the Shuffled condition achieves near-perfect accuracy precisely because it retrieves zero gold evidence, avoiding integration errors.

**Methodological contribution:** The answer flip decomposition (CC/CW/WC/WW relative to parametric-only baseline) provides a diagnostic tool for distinguishing retrieval effects from reasoning effects.

## Assessment: Four contributions

A fifth contribution (reproducible benchmark/protocol) could be listed if reviewers value the open trace dataset and replay infrastructure, but it is not a standalone scientific contribution and is better presented as a supplementary strength.
