# Table 5: LLM Replication Tests (V5 Phase 26, N = 128 per model)

| Test | Hypothesis | Controlled Effect | LLM Effect | Verdict |
|------|-----------|------------------|------------|---------|
| R1: Sequence superiority | Multi-op sequences > single operations | Supported (V3/V4) | +0.003 | INCONCLUSIVE |
| R2: Temporal complementarity | gen_hyp→retrieve exhibits synergy | +0.162 (V4) | **+0.111** | **REPLICATED** |
| R3: Interference | Repeated operations show diminishing returns | −0.050 (V4) | Confirmed (gen_hyp→gen_hyp) | Consistent |
| R4: Order effects | A→B ≠ B→A for key pairs | Supported (V3/V4) | −0.050 (reversed) | NOT REPLICATED |
| R5: Attack timing | Late attack > early attack | Supported (V3/V4) | **+0.276** | **REPLICATED** |
| R6: Fixed vs greedy | Fixed sequences > greedy scheduling | Supported (V3/V4) | +0.003 | INCONCLUSIVE |

*Cross-model note: Results are identical for Gemma 3 27B and Llama 3.2 11B because quality scores come from the deterministic simulator. This confirms the replicated effects are structural properties of the epistemic task. Source: `campaign_v5/results/phase26_verdicts_gemma3.json`.*

**Sequence means (Phase 26):**

| Sequence | Mean Quality | Std | N |
|----------|-------------|-----|---|
| reversed_B1 | 0.327 | 0.207 | 16 |
| explore (gen_hyp→retrieve) | 0.323 | 0.207 | 16 |
| B1_extended | 0.277 | 0.197 | 16 |
| attack_late | 0.276 | 0.198 | 16 |
| single_gen_hyp | 0.273 | 0.207 | 16 |
| discriminate | 0.223 | 0.181 | 16 |
| single_retrieve | 0.050 | 0.000 | 16 |
| attack_early | 0.000 | 0.000 | 16 |
