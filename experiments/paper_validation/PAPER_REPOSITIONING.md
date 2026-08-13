# Paper Repositioning Based on Validated Results

## Previous Framing (V1-V5)
"Multi-step cognitive artifacts improve LLM research performance through semantic mediation."

## New Framing (After Causal Validation)
"The Retrieval-Reasoning Dissociation: How Intermediate Cognitive Artifacts Reveal Evidence Integration as the Bottleneck in LLM-Based Research Pipelines"

---

## Title Options

1. **"Retrieval Helps, Reasoning Hurts: A Causal Audit of Cognitive Artifacts in LLM Research Pipelines"**
2. **"The Evidence Integration Bottleneck: When Better Retrieval Leads to Worse Answers"**
3. **"Semantic Artifacts in LLM Pipelines: A Preregistered Study of the Retrieval-Reasoning Dissociation"**

---

## Abstract Draft

Intermediate cognitive artifacts — hypothesis documents, analysis plans, reasoning chains — are widely used in multi-step LLM systems to mediate between task formulation and evidence retrieval. We present a preregistered causal audit of their value across two public benchmarks (SciFact, HotpotQA), two model families (Gemma 27B, Llama 11B), and five controlled conditions (Real, Shuffled, Neutral, Generic Expansion, Direct).

Our primary finding is a robust retrieval-reasoning dissociation: real semantic artifacts significantly improve evidence retrieval over shuffled controls (Δ = +0.18 to +0.51, all p < .002 after Holm correction), but this retrieval gain translates to improved task performance ONLY on open-domain QA (HotpotQA F1: +0.12, p < .002). On scientific claim verification (SciFact), improved retrieval actually HARMS accuracy (Δ = -0.23 to -0.39, p < .002), because the model cannot reliably integrate retrieved scientific evidence.

Furthermore, we show that generic query expansion — without any task-specific hypothesis content — achieves comparable or better retrieval than real hypotheses (2/4 cells significant in the reverse direction), challenging the assumption that semantic specificity matters for retrieval quality.

Our causal analysis, using parametric-only baselines, artifact visibility ablations, and answer flip decomposition, identifies evidence integration as the primary bottleneck: the model defaults to high-accuracy patterns when no evidence is retrieved, but introduces errors when asked to assess complex evidence. These findings replicate across model families and generalize to unseen tasks.

---

## Contribution Summary

### C1: Methodology
A rigorous causal audit framework for evaluating intermediate artifacts in LLM pipelines, including:
- 5-condition semantic intervention design (REAL/SHUFFLED/NEUTRAL/GENERIC/DIRECT)
- Parametric-only baseline for answer flip decomposition
- Artifact visibility ablation for hypothesis anchoring assessment
- Holm-corrected paired bootstrap inference
- Preregistered analysis on unseen tasks

### C2: Empirical Finding — Retrieval-Reasoning Dissociation
Demonstrated across 2 datasets × 2 models that improved retrieval helps some tasks but harms others, driven by the model's evidence integration capability, not retrieval quality.

### C3: Empirical Finding — Generic Expansion Sufficiency
Generic query expansion achieves comparable or superior retrieval to task-specific hypotheses, questioning the necessity of elaborate intermediate reasoning for retrieval improvement.

### C4: Empirical Finding — Evidence Integration Bottleneck
Identified through answer flip analysis that the SciFact failure mode is NOT hypothesis anchoring but evidence integration: when the model receives more evidence, it makes more errors on complex claim assessment.

---

## Section Outline

### 1. Introduction (1 page)
- Multi-step LLM systems use intermediate artifacts
- Unclear if semantic content matters or if any query reformulation suffices
- We conduct a preregistered causal audit

### 2. Related Work (1 page)
- RAG and query expansion
- Multi-step reasoning systems
- Causal evaluation of pipeline components

### 3. Methodology (2 pages)
- Task design: 5 conditions + 2 diagnostic
- Fairness contract: matched compute/calls
- Benchmarks: SciFact (claim verification), HotpotQA (open-domain QA)
- Models: Gemma 27B (primary, unseen tasks), Llama 11B (transfer, seen tasks)
- Statistical methods: paired bootstrap, Holm correction, 14 tests

### 4. Results (2 pages)
- Table 1: Condition performance summary
- Table 2: Primary effects with CIs and Holm p-values
- Table 3: Answer flip analysis
- Figure 1: Retrieval-reasoning dissociation visualization

### 5. Analysis (1.5 pages)
- 5.1 The retrieval-reasoning dissociation
- 5.2 Generic expansion sufficiency
- 5.3 Evidence integration bottleneck (mechanistic pathway)
- 5.4 Artifact visibility and hypothesis anchoring (null after correction)

### 6. Discussion (1 page)
- Implications for multi-step LLM system design
- When intermediate reasoning helps vs hurts
- Limitations: 2 datasets, 2 models, BM25 retrieval

### 7. Conclusion (0.5 pages)

---

## Key Numbers for the Paper

| Claim | Evidence | Strength |
|-------|----------|----------|
| Semantic artifacts improve retrieval | 4/4 cells significant, p < .002 | Strong |
| Generic expansion ≥ Real for retrieval | 2/4 significant reverse, 0/4 Real better | Strong |
| Dissociation: helps HotpotQA, hurts SciFact | 3/4 significant, 1/4 trending | Strong |
| Replicates across models | All qualitative patterns match | Strong |
| Artifact anchoring (visibility) | 0/2 significant after correction | Null |
| SHUFFLED zero recall on SciFact | Both models, recall = 0.000 | Diagnostic |
| Parametric-only accuracy low | 0.125 (Gemma), 0.320 (Llama) | Diagnostic |

---

## Venue Recommendation

**ICLR 2027** remains appropriate. The paper now offers:
1. Preregistered design (uncommon in ML)
2. Clear negative finding (specificity doesn't help retrieval)
3. Mechanistic analysis (evidence integration bottleneck)
4. Cross-model replication (2 families)
5. Unseen task generalization (88 + 300 tasks)

The story is stronger as a "careful causal audit that overturns a common assumption" than as "our artifact helps."

Alternative: **ACL 2027** (more NLP-focused venue, may appreciate the RAG analysis angle).
