# Final Claim Ladder

Every claim in the manuscript must trace to this ladder. Each entry specifies exactly what wording is and is not allowed.

## Claim 1: Retrieval Improvement

**Claim:** Intermediate semantic reformulation improves evidence retrieval relative to semantically disrupted controls.

**Source:** PV-H1, formal_statistics.json, tests SF-G-H1-recall, SF-L-H1-recall, HP-G-H1-recall, HP-L-H1-recall

**Confirmatory:** Yes (preregistered)

**Datasets:** SciFact (N=88 unseen, N=100 transfer), HotpotQA (N=300 unseen, N=100 transfer)

**Models:** Gemma 27B, Llama 11B

**Effects:**
- SciFact×Gemma: +0.281 [+0.193, +0.372], p_Holm = 0.0014
- SciFact×Llama: +0.511 [+0.413, +0.608], p_Holm = 0.0014
- HotpotQA×Gemma: +0.182 [+0.138, +0.225], p_Holm = 0.0014
- HotpotQA×Llama: +0.315 [+0.240, +0.390], p_Holm = 0.0014

**Holm status:** 4/4 significant

**Allowed wording:**
- "improved retrieval across both evaluated datasets and models"
- "reliably improves evidence retrieval"
- "significantly improves gold evidence recall in all four cells"

**Forbidden wording:**
- "universally improves retrieval"
- "always improves retrieval"
- "guarantees better evidence"
- "hypothesis-specific retrieval advantage" (contradicted by PV-H2)

---

## Claim 2: Generic Expansion Sufficiency

**Claim:** Generic query expansion without hypothesis content achieves comparable or superior retrieval to task-specific hypothesis artifacts.

**Source:** PV-H2, formal_statistics.json, tests SF-G-H2-recall, SF-L-H2-recall, HP-G-H2-recall, HP-L-H2-recall

**Confirmatory:** Yes (preregistered)

**Effects:**
- SciFact×Gemma: -0.182 [-0.295, -0.068], p_Holm = 0.0070 (GENERIC better)
- SciFact×Llama: -0.068 [-0.190, +0.053], p_Holm = 0.4892 (n.s.)
- HotpotQA×Gemma: -0.065 [-0.108, -0.023], p_Holm = 0.0240 (GENERIC better)
- HotpotQA×Llama: +0.050 [-0.030, +0.125], p_Holm = 0.4892 (n.s.)

**Holm status:** 2/4 significant (both favor GENERIC), 0/4 favor REAL

**Allowed wording:**
- "we find no evidence that hypothesis-specific content improves retrieval beyond generic query expansion"
- "generic reformulation achieves comparable or superior retrieval"
- "the retrieval benefit is not attributable uniquely to hypothesis semantics"

**Forbidden wording:**
- "generic expansion is always better"
- "hypothesis formation is useless"
- "hypotheses never help retrieval"

---

## Claim 3: Retrieval–Reasoning Dissociation

**Claim:** The same type of retrieval improvement has opposite downstream effects depending on task structure.

**Source:** PV-H3, formal_statistics.json, tests SF-G-H3-acc, SF-L-H3-acc, HP-G-H3-f1, HP-L-H3-f1

**Confirmatory:** Yes (preregistered)

**Effects:**
- SciFact×Gemma accuracy: -0.227 [-0.318, -0.148], p_Holm = 0.0014 (HARMFUL)
- SciFact×Llama accuracy: -0.390 [-0.490, -0.300], p_Holm = 0.0014 (HARMFUL)
- HotpotQA×Gemma F1: +0.124 [+0.074, +0.175], p_Holm = 0.0014 (HELPFUL)
- HotpotQA×Llama F1: +0.086 [-0.015, +0.188], p_Holm = 0.3840 (trending helpful)

**Holm status:** 3/4 significant

**Allowed wording:**
- "the same retrieval improvement helps HotpotQA while harming SciFact"
- "retrieval gain and downstream utility are dissociated"
- "improved retrieval can degrade task performance"
- "retrieval quality is not a reliable proxy for task utility"

**Forbidden wording:**
- "retrieval always hurts reasoning"
- "better retrieval is harmful"
- "retrieval is counterproductive"

---

## Claim 4: Cross-Model Consistency

**Claim:** The qualitative patterns replicate across two model families.

**Source:** PV-H4, comparison of Gemma and Llama effect directions

**Confirmatory:** Yes (preregistered)

**Evidence:**
- Retrieval benefit (REAL > SHUFFLED): Same direction, both models, both datasets
- Downstream dissociation: Same direction, both models
- SciFact accuracy harm: Same direction, both models
- HotpotQA F1 benefit: Same direction (Gemma significant, Llama trending)

**Allowed wording:**
- "qualitatively consistent across the two evaluated model substrates"
- "the pattern replicates across Gemma and Llama"

**Forbidden wording:**
- "model invariant"
- "universal"
- "architecture independent"
- "generalizes to all models"

---

## Claim 5: Evidence Integration Mechanism

**Claim:** SciFact degradation is primarily associated with evidence integration failure, not direct hypothesis anchoring.

**Source:** PV-H5, answer flip analysis, artifact visibility ablation

**Confirmatory:** Partially (preregistered diagnostic, not strict confirmatory test)

**Evidence:**
- Artifact visibility effect (Gemma): -0.045 [-0.102, 0.000], p_Holm = 0.40 (n.s.)
- Artifact visibility effect (Llama): -0.060 [-0.120, 0.000], p_Holm = 0.33 (n.s.)
- SHUFFLED achieves ~100%/96% accuracy with 0% gold recall
- Conditions with higher recall have more WW (wrong-stays-wrong) cases

**Allowed wording:**
- "SciFact degradation is associated with evidence integration failure"
- "artifact visibility has a small, non-significant effect after correction"
- "the primary mechanism is not direct hypothesis anchoring"
- "CONSISTENT_WITH evidence integration bottleneck"

**Forbidden wording:**
- "PROVES evidence integration is the cause"
- "rules out all forms of anchoring"
- "definitively establishes the mechanism"

---

## Claim 6: Negative Findings (Historical)

**Claim:** Several initially promising findings did not survive controlled validation.

**Source:** V6 factorial, V6 matched-budget analysis

**Confirmatory:** Yes (V6 preregistered)

**Allowed wording:**
- "compute-controlled factorial eliminated the temporal complementarity interaction"
- "matched-budget controls reduced the attack timing effect to near zero"
- "these falsifications motivated the final causal audit design"

**Forbidden wording:**
- "temporal complementarity is impossible"
- "attack timing never matters"
