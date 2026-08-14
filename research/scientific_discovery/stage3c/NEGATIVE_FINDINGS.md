# Negative Findings — Stage 3C

## Finding 9: Transfer Model Structured Output Fragility
**Date:** 2026-08-14  
**Context:** LLama 3.2 Vision (11B) as transfer model  
**Expected:** Comparable structured output quality to primary  
**Actual:** 67% schema compliance (vs 100% for Gemma)  
**Reason:** Model prepends conversational text before JSON  
**Implication:** Smaller models require more aggressive parsing; C3 (prediction) fails  
**Action:** Transfer model classified as PARTIAL_SUBSTRATE

## Finding 10: Self-Authorship Bias — Weak But Nonzero
**Date:** 2026-08-14  
**Context:** SD-H4 provenance manipulation  
**Expected:** Zero SAB (identical behavior regardless of provenance)  
**Actual:** +5 confidence points mean SAB difference (SELF retains slightly more)  
**Specific case:** Reverse causality world shows SAB=+15  
**Implication:** LLMs may show weak self-protection bias, but still abandon correctly  
**Caveat:** N=3, insufficient for formal significance testing

## Finding 11: SD-H9B — Discrimination vs Confirmation Not Significant  
**Date:** 2026-08-14  
**Context:** Locked active science benchmark  
**Expected:** Discrimination > Confirmation  
**Actual:** +0.017 (p=0.53, CI crosses zero)  
**Heterogeneity:** Multi-hypothesis worlds show +0.150 advantage for discrimination  
**Implication:** Discrimination only matters when hypothesis space is complex  
**Preserved:** This is a genuine finding about when active science policies differ

## Finding 12: Factorial — No Interaction Between Hypothesis Source and Active Policy
**Date:** 2026-08-14  
**Context:** Generative × Active 2x2 factorial  
**Expected:** Possible interaction (active less valuable with noisy LLM hypotheses)  
**Actual:** Interaction = 0.000 (both +0.100 active effect)  
**Implication:** Active experiment control is equally valuable regardless of hypothesis provenance  
**Caveat:** True mechanism was present in generated ecology; interaction might emerge when it's absent
