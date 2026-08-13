# Final Abstract

## Version 1 (Primary — 198 words)

Intermediate reasoning artifacts — hypotheses, analysis plans, reformulated queries — are increasingly used to guide evidence retrieval in multi-step LLM systems. Improved retrieval is commonly treated as evidence that such cognitive interventions are beneficial. We challenge this assumption through a preregistered causal audit across SciFact (claim verification) and HotpotQA (multi-hop QA), using Gemma 27B and Llama 11B under five matched-resource conditions that isolate artifact semantics from generic query quality.

We find a robust retrieval–reasoning dissociation: real hypothesis artifacts significantly improve gold evidence recall over shuffled controls across all four dataset-model cells (+0.18 to +0.51, all p < .002 after Holm correction over 14 tests). However, this retrieval gain improves downstream F1 on HotpotQA (+0.12, p < .002) while degrading accuracy on SciFact (-0.23 to -0.39, p < .002). Generic query expansion — without any hypothesis content — matches or exceeds hypothesis-conditioned retrieval, indicating the benefit is not hypothesis-specific. Answer flip analysis and artifact visibility ablation localize the SciFact failure to evidence integration rather than hypothesis anchoring: more retrieved evidence introduces more reasoning errors. These findings demonstrate that retrieval improvement is not a reliable proxy for end-to-end agent utility.

## Key Numbers (from formal_statistics.json only)

- Retrieval effect range: +0.18 to +0.51
- All 4 retrieval cells: p_Holm < .002
- HotpotQA F1 gain: +0.124 [+0.074, +0.175], p_Holm = 0.0014
- SciFact accuracy loss: -0.227 [-0.318, -0.148], p_Holm = 0.0014 (Gemma)
- SciFact accuracy loss: -0.390 [-0.490, -0.300], p_Holm = 0.0014 (Llama)
- Generic vs Real retrieval: 2/4 cells significantly favor Generic, 0/4 favor Real
- Artifact visibility (Gemma): -0.045, p_Holm = 0.40 (n.s.)
- Total experimental units: 588 tasks × 5-7 conditions
- 14 tests, Holm corrected, 9 significant
