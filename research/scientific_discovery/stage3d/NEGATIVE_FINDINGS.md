# Negative Findings — Stage 3D

## Finding 13: Stage 3C "100% Zero-Regret" Was a Measurement Error
**Date:** 2026-08-14  
**Context:** Oracle regret audit of Stage 3C LOCKED results  
**Claimed:** JSD achieves 100% zero-regret on locked hardened worlds  
**Actual:** 80% zero-regret when measured with correct formula (OracleIG - PolicyIG)  
**Root cause:** Stage 3C measured regret in JSD-space (tautological for JSD policy)  
**Implication:** JSD is strong but imperfect; 20% of worlds show JSD ≠ Oracle  
**Action:** All Stage 3C regret numbers reclassified; correct formula documented

## Finding 14: Approx-EIG Does NOT Significantly Outperform JSD
**Date:** 2026-08-14  
**Context:** E4 (Approx-EIG) vs E3 (JSD) on 200 distributional worlds  
**Expected:** EIG might significantly outperform JSD (JSD = "shortcut")  
**Actual:** EIG regret 0.0085 vs JSD regret 0.0093 (p=0.14, not significant)  
**Implication:** JSD IS a strong proxy for expected information gain  
**Why:** JSD and EIG are mathematically related — JSD between predictions approximates mutual information  
**Action:** Report both but do not claim EIG is necessary

## Finding 15: SD-H9C Complexity Moderation — NOT SUPPORTED
**Date:** 2026-08-14  
**Context:** Does discrimination advantage increase with hypothesis-space complexity?  
**Hypothesis:** Advantage concentrates in complex worlds (motivated by multi_hypothesis_branch)  
**Actual:** Slope = -0.013 (p=0.59, CI crosses zero widely)  
**Detail:** LOW complexity: +0.100 advantage; MID: +0.044; HIGH: +0.084  
**Implication:** The Stage 3C multi_hypothesis_branch observation was world-specific, not generalizable  
**Note:** Discrimination DOES outperform confirmation overall (+0.076 on distributional worlds)  
**Action:** SD-H9C downgraded; the Stage 3C heterogeneity finding does not replicate at scale

## Finding 16: Distributional Worlds Reduce JSD Ceiling
**Date:** 2026-08-14  
**Context:** Comparing handcrafted vs distributional world generators  
**Hardened worlds:** 80% JSD-Oracle agreement (near ceiling)  
**Distributional worlds:** 73% JSD-Oracle agreement (healthier for benchmarking)  
**Implication:** Hand-authored worlds inadvertently created easy structure; parametric generation better  
**Action:** Stage 3D primary benchmark uses distributional generator

## Finding 17: Recovery After Abandonment Is the Primary Bottleneck
**Date:** 2026-08-14  
**Context:** SD-H4 SCALED — Full execution (N=23 WRONG, N=20 TRUE protection)  
**Expected:** Self-correction = abandonment + discovery of correct alternative  
**Actual:** 95.7% correct abandonment but only 18.2% recovery of true mechanism  
**Implication:** The model is a reliable falsifier but a poor autonomous discoverer  
**Detail:** Self-correction is asymmetric: knowing what's wrong ≠ knowing what's right  
**Action:** Recovery enhancement is the next research priority (hypothesis ecology, iterative evidence)

## Finding 18: Self-Authorship Bias Does Not Exist (at N=23)
**Date:** 2026-08-14  
**Context:** SD-H4 SCALED — Paired SELF/EXTERNAL conditions  
**Expected:** Models might retain self-generated hypotheses more (SAB > 0)  
**Actual:** SAB = -0.43 (p=0.49), 95% CI [-1.7, +0.8]  
**Implication:** Provenance framing is irrelevant to this model's belief revision  
**Detail:** Stage 3C pilot SAB of +5 was noise at N=3  
**Action:** Self-authorship is not a concern for gemma3; no defensive measures needed

## Finding 19: High Ambiguity Rate (42%) Limits WRONG Sample Size
**Date:** 2026-08-14  
**Context:** 50 worlds yielded only 23 WRONG (expected 35-40)  
**Expected:** Most generated hypotheses would be clearly wrong  
**Actual:** 42% were AMBIGUOUS (mixed true/false mechanisms, overbroad, conditional)  
**Implication:** The model is scientifically sophisticated — it rarely generates purely naive hypotheses  
**Action:** Future benchmarks need tighter trap designs or graded correctness scoring
