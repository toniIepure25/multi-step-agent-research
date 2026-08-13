# Self-Adversarial Review of Validated Results

## Review Criteria: ICLR 2027 Standards

### Reviewer 1: "The SHUFFLED accuracy anomaly undermines the entire study"

**Concern:** SHUFFLED achieves 100% accuracy on SciFact Gemma and 96% on Llama. This is suspicious — perfect accuracy from a completely irrelevant artifact suggests a measurement artifact, not a real finding.

**Response:** This IS a measurement artifact, and we characterize it as such. SHUFFLED generates queries from irrelevant biomedical text, which retrieves zero gold evidence. Without evidence to confuse it, the model defaults to verdict patterns that happen to be correct on this specific dataset. The PARAMETRIC_ONLY condition (12.5-32% accuracy) shows the model has minimal knowledge WITHOUT retrieval. The SHUFFLED result reveals that SciFact's default-verdict behavior is dataset-specific — not a confound but a finding about the interaction between evidence availability and task structure.

**Mitigation:** We report this transparently and use it as evidence FOR the evidence integration bottleneck thesis. HotpotQA does NOT show this pattern (SHUFFLED is worst there), confirming it's task-specific.

### Reviewer 2: "BM25 is not representative of modern retrieval"

**Concern:** All retrieval uses BM25. Modern RAG systems use dense retrievers (Contriever, BGE, etc.). The results may not generalize.

**Response:** Valid limitation. However: (1) BM25 is our controlled retrieval where query quality directly affects results — with dense retrieval, the embedding model adds a confound; (2) our claim is about the retrieval-reasoning dissociation, which is downstream of retrieval method; (3) better retrieval would likely AMPLIFY the SciFact problem (more gold evidence = more integration errors).

**Mitigation:** Acknowledge as limitation. Note that the dissociation would likely persist or worsen with stronger retrieval.

### Reviewer 3: "N=88 for SciFact primary is underpowered"

**Concern:** Only 88 unseen SciFact claims. Power may be insufficient for small effects.

**Response:** (1) Our SciFact effects are large (0.23-0.28), easily detected at N=88; (2) All SciFact primary contrasts are significant after Holm correction; (3) We supplement with N=100 Llama transfer (same tasks, different model) showing consistent patterns; (4) HotpotQA primary uses N=300 unseen tasks.

**Mitigation:** Already addressed. The combination of 88 unseen (Gemma) + 100 seen (Llama) + 300 unseen HotpotQA provides sufficient evidence.

### Reviewer 4: "The claim that 'generic expansion suffices' needs more support"

**Concern:** Only 2/4 cells show GENERIC significantly better. The other 2 are null. This is not strong enough to claim generic suffices.

**Response:** Fair. We should frame this as "hypothesis specificity provides no ADDITIONAL benefit over generic expansion" rather than "generic is better." The evidence: 2/4 GENERIC significantly better, 0/4 REAL significantly better, 2/4 null. The weight of evidence is against specificity.

**Mitigation:** Soften claim to "we find no evidence that hypothesis-specific content improves retrieval beyond generic query expansion."

### Reviewer 5: "Two model families is not enough for model transfer claims"

**Concern:** Gemma 27B and Llama 11B differ in both architecture AND size. Cannot separate model family from model capability.

**Response:** Valid. The claim is deliberately modest: "qualitative patterns replicate across model families." We show direction consistency, not magnitude consistency. A third model family would strengthen but is not essential.

**Mitigation:** Acknowledge limitation. If compute allows, add a third family (Mistral, Phi).

### Reviewer 6: "The endpoint is private — no one can reproduce this"

**Concern:** https://inference.ccrolabs.com/v1 is a private endpoint. Reproducibility is claimed but not verifiable.

**Response:** (1) We release all raw inference traces (complete LLM inputs/outputs) for every task × condition; (2) All datasets are public (SciFact, HotpotQA from published sources); (3) The models (Gemma, Llama) are open-weight and can be run locally; (4) Our code is released. Anyone with Ollama can replicate.

**Mitigation:** Include a reproducibility section with instructions for running with a local Ollama instance. Provide frozen traces for verification.

---

## Overall Assessment

**Strengths:**
- Preregistered design (rare in ML)
- Clear, validated negative finding (specificity doesn't help)
- Mechanistic analysis with diagnostic conditions
- Cross-dataset and cross-model replication
- Transparent reporting of anomalies (SHUFFLED accuracy)

**Weaknesses (acknowledged):**
- BM25 only
- 2 model families
- N=88 for SciFact primary (but effects are large)
- Private inference endpoint (but traces released)

**Verdict:** The paper is suitable for ICLR 2027 as a **negative-result / methodological contribution**. The story is: "We thought hypothesis artifacts help. They help retrieval but not task performance. Here's why, and here's a rigorous methodology for finding out."
