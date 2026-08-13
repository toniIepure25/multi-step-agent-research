# Final Paper Repositioning

## From
"ASAR-REE: Multi-step cognitive architecture for LLM research agents with temporal complementarity and adaptive metacognitive scheduling"

## To
"Better Retrieval, Worse Reasoning: Auditing Intermediate Artifacts in LLM Pipelines"

## Central Scientific Claim
An intermediate cognitive operation can succeed at its local objective (improving evidence retrieval) while failing at the global task objective (improving reasoning quality). This dissociation depends on task structure: the same retrieval improvement helps open-domain QA but harms scientific claim verification. The bottleneck is evidence integration, not evidence acquisition.

## One-Sentence Contribution
A preregistered causal audit showing that intermediate reasoning artifacts reliably improve LLM retrieval but this improvement reverses sign downstream depending on task structure, revealing evidence integration as the bottleneck in retrieval-augmented systems.

## Conceptual Framework

### Pipeline
```
Task → Intermediate Artifact → Retrieval Query → Retrieved Evidence → Evidence Integration → Final Decision
```

### Stage-Level Quantities

**Retrieval Gain:** G_R(c) = R(c) - R(baseline)
**Downstream Gain:** G_Y(c) = Y(c) - Y(baseline)

### Retrieval–Reasoning Utility Matrix

| Retrieval | Downstream | Interpretation | Observed |
|-----------|-----------|----------------|----------|
| > 0 | > 0 | Positive transfer | HotpotQA (both models) |
| > 0 | < 0 | Retrieval-reasoning dissociation | SciFact (both models) |
| > 0 | ~ 0 | Retrieval gain without utility | Not observed |
| ~ 0 | > 0 | Non-retrieval reasoning gain | Not observed |
| < 0 | > 0 | Metric misrepresents utility | Not observed |

### Key Distinction
The paper should emphasize: RETRIEVAL QUALITY AND REASONING UTILITY ARE DISTINCT TARGETS. An intermediate artifact may successfully optimize evidence acquisition while harming evidence interpretation.

## Connection to Process Reward / Agent Control

If metacognitive policies optimize intermediate proxies (retrieval relevance, evidence recall, artifact quality), they may choose actions that improve the proxy while worsening final task utility. This creates an analogy to reward misspecification — but we use careful wording:

> "This finding is structurally analogous to reward misspecification: a local proxy (retrieval quality) is optimized at the expense of a global objective (task performance). We do not claim a formal Goodhart effect, but the pattern suggests that intermediate evaluation metrics in LLM pipelines may not reliably indicate end-to-end utility."

## Paper Story Arc

1. **Setup:** Multi-step LLM systems use intermediate reasoning artifacts to guide retrieval. Improved retrieval is treated as evidence of artifact utility.
2. **Question:** Does improved retrieval from cognitive artifacts reliably improve downstream reasoning?
3. **Method:** Preregistered causal audit with 5 conditions, 2 datasets, 2 models, matched compute.
4. **Finding:** Retrieval improves (4/4 cells) but downstream utility splits by task (helps QA, hurts verification).
5. **Mechanism:** The failure is evidence integration, not hypothesis anchoring.
6. **Implication:** Retrieval metrics are not reliable proxies for agent utility. Pipeline evaluation must measure at every stage.
