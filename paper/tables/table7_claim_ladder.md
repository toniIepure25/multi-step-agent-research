# Table 7: Cross-Level Claim Ladder

| Finding | Simulator (V3/V4) | LLM Replication (V5) | Static Real Evidence (V5) | Evidence Level |
|---------|-------------------|---------------------|--------------------------|---------------|
| Temporal complementarity (gen_hyp→retrieve) | SUPPORTED (+0.162) | REPLICATED (+0.111) | Not detected (range=0.030) | **Level 2** |
| Attack timing (early=0, late>0) | SUPPORTED | REPLICATED (+0.276) | N/A | **Level 2** |
| Cross-model structural consistency | N/A | Confirmed (2 models) | N/A | **Level 2** |
| gen_hyp + reason super-additivity | SUPPORTED (+0.228) | Consistent | N/A | **Level 1** |
| gen_hyp→gen_hyp interference | SUPPORTED (−0.050) | Consistent | N/A | **Level 1** |
| Adaptivity gap exists | SUPPORTED (0.096) | N/A | N/A | **Level 1** |
| Sequence > single operation | SUPPORTED | INCONCLUSIVE (+0.003) | NOT SUPPORTED | **Level 1** |
| Order effects (A→B ≠ B→A) | SUPPORTED | NOT REPLICATED (−0.050) | NOT SUPPORTED | **Level 1** |
| Fixed > greedy scheduling | SUPPORTED | INCONCLUSIVE (+0.003) | NOT SUPPORTED | **Level 1** |
| Adaptive motif control | Oracle exists | Policy FAILS (0.323 << 0.518) | N/A | **Level 0** |
| Real-document transfer | N/A | N/A | NOT SUPPORTED | **Level 0** |

*Level 0: unsupported. Level 1: simulator-supported only. Level 2: LLM-replicated. Level 3: static-real replicated (none achieved).*
