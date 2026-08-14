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
