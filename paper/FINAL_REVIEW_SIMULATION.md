# Simulated Reviewer Feedback

## Reviewer 1 — RAG Expert

**Score:** 6/10 (Weak Accept)
**Confidence:** 4/5

**Strongest reject argument:** "This is essentially a study of query expansion variants. The authors generate different types of queries (hypothesis-based, generic, shuffled) and evaluate retrieval + downstream performance. The intervention is at the query level, not a fundamentally new cognitive architecture. HyDE (2023) already showed that hypothetical documents improve retrieval."

**Strongest accept argument:** "Unlike HyDE and Query2Doc, this paper decomposes the effect at each pipeline stage and discovers that retrieval improvements can reverse downstream. The preregistered design with matched compute is methodologically stronger than most RAG evaluation papers. The generic expansion negative result (PV-H2) is genuinely useful for the field."

**Questions:**
1. How does BM25 vs dense retrieval affect the dissociation?
2. Would the findings hold with a state-of-the-art retriever?
3. Can you provide examples of SciFact tasks where retrieved evidence caused harmful flips?

**Required clarification:** Explicitly compare the experimental design to HyDE and explain what is measured differently.

---

## Reviewer 2 — Causal Inference Expert

**Score:** 5/10 (Borderline)
**Confidence:** 3/5

**Strongest reject argument:** "The stage-level claims are observational, not causal in the formal sense. The authors randomize the artifact content (good) but then observe correlations between retrieval quality and reasoning quality. They cannot claim evidence integration is 'the cause' of SciFact failure without formal mediation analysis. The answer flip analysis is descriptive, not causal."

**Strongest accept argument:** "The randomized intervention on artifact content is a genuine experiment, not observational. The authors appropriately label the mechanism as 'associated with' rather than 'proves.' The paired within-task design with multiple controls is stronger than most LLM evaluation papers."

**Questions:**
1. Could you run a formal causal mediation analysis?
2. What is the causal graph you are assuming?
3. Could confounds like BM25 corpus bias explain the SciFact results?

**Required clarification:** Explicitly state the assumed causal DAG and where the causal claims hold vs where they are associational.

---

## Reviewer 3 — Agent Researcher

**Score:** 6/10 (Weak Accept)
**Confidence:** 3/5

**Strongest reject argument:** "The term 'cognitive artifacts' is misleading for what are essentially prompt variations. These are not analogous to human cognitive artifacts in any meaningful way. The paper would be clearer if it simply said 'intermediate prompt reformulations' or 'generated query expansions.'"

**Strongest accept argument:** "Regardless of terminology, the empirical finding is valuable. The dissociation between retrieval quality and task performance is important for anyone building multi-step LLM systems. The controlled design is unusually rigorous for this area."

**Questions:**
1. Why not use 'prompt variations' or 'intermediate reformulations'?
2. How do these results apply to real agent systems with tool use?
3. Would the dissociation hold with more sophisticated reasoning models?

**Required clarification:** Justify the 'cognitive artifact' terminology or replace it with less loaded language.

---

## Reviewer 4 — Statistics/Evaluation Expert

**Score:** 7/10 (Accept)
**Confidence:** 4/5

**Strongest reject argument:** "N=88 for SciFact primary is small. The SciFact effects are large enough to detect, but the study may miss smaller but meaningful effects. The HotpotQA×Llama F1 contrast is non-significant (p_Holm=0.38) with N=100 — this cell is underpowered."

**Strongest accept argument:** "The statistical methodology is excellent by ML standards: preregistered hypotheses, Holm correction over 14 tests, paired bootstrap with 10,000 resamples, task-level independence, and independent reproduction from frozen traces. 9/14 tests significant after correction. The claim ladder approach is unusually careful."

**Questions:**
1. What is the minimum detectable effect for the underpowered cells?
2. Why not use a hierarchical model pooling across models?
3. Can you report equivalence tests for the non-significant results?

**Required clarification:** Report post-hoc power for the non-significant cells and discuss what effect sizes they cannot rule out.

---

## Reviewer 5 — Hostile ICLR/ICML Reviewer

**Score:** 4/10 (Reject)
**Confidence:** 4/5

**Strongest reject argument:** "This paper's core finding — that better retrieval can hurt generation — is well-known in the RAG literature. Context distraction, position bias, and parametric-vs-retrieval conflict have been studied extensively. The specific task-dependent direction of the effect (helps QA, hurts verification) is mildly interesting but not surprising: verification requires careful reasoning about evidence, while QA requires extracting facts. The contribution is incremental."

**Strongest accept argument:** "The systematic, preregistered demonstration across two datasets and two models IS new even if the general phenomenon is known. The specific finding that hypothesis-conditioned retrieval is no better than generic expansion is a corrective to HyDE-style work. The methodology is a genuine contribution."

**Questions:**
1. What specific new knowledge does this paper provide beyond 'context can hurt'?
2. Why should I care about the SciFact result given that SciFact accuracy metrics are known to be problematic?
3. Two datasets is insufficient for claiming the dissociation is 'task-dependent' — you've shown exactly one positive and one negative case.

**Required clarification:** Clearly articulate what is known vs what is new. The paper must distinguish 'bad retrieval hurts' (known) from 'improved retrieval hurts' (claimed to be new).

---

## Area Chair Meta-Review

**Recommendation:** Accept (conditional on revisions)

**Summary:** This paper presents a preregistered causal audit of intermediate cognitive artifacts in LLM retrieval pipelines, finding a robust dissociation between retrieval improvement and downstream task performance. The experimental methodology is strong (randomized conditions, matched compute, Holm correction). The primary finding — that the same retrieval improvement helps multi-hop QA while harming scientific claim verification — is replicated across two model families.

**Strengths:**
1. Unusually rigorous methodology for ML/NLP evaluation
2. Clean experimental design with meaningful controls
3. Preregistered with honest reporting of negative results
4. The generic expansion negative result is important

**Weaknesses:**
1. Only two datasets, making 'task-dependent' claims somewhat thin
2. BM25 only — unclear if findings generalize to dense retrieval
3. Terminology ('cognitive artifacts') may be contentious
4. The core observation (context can hurt) has precedent, even if the specific form is novel

**Required revisions:**
1. Explicitly compare to and distinguish from context distraction literature
2. Acknowledge the 'two datasets' limitation more prominently
3. Consider softening 'cognitive artifact' to 'intermediate reformulation' or similar
4. Add post-hoc power analysis for underpowered cells

**Final assessment:** The paper's strength is methodological rigor applied to an important practical question. The finding that optimizing a local proxy (retrieval quality) can harm the global objective (task performance) is timely and relevant to the agent/RAG community. With revisions addressing the above points, this is a solid contribution.

---

## Top 5 Remaining Rejection Risks

1. **"Isn't this obvious?"** — The core observation that context can hurt is known. The paper must clearly distinguish improved-retrieval-harm from bad-retrieval-harm.

2. **"Only two datasets"** — The task-dependent claim rests on exactly one positive and one negative case. A third dataset would substantially strengthen this.

3. **"BM25 is not representative"** — Modern RAG uses dense retrieval. Results may not generalize.

4. **"Terminology disagreement"** — "Cognitive artifacts" may invite dismissal from reviewers who find it pretentious for what are prompt reformulations.

5. **"Incremental over HyDE + distraction work"** — Combining two known ideas (hypothesis-based retrieval + context distraction) may be seen as predictable rather than novel.
