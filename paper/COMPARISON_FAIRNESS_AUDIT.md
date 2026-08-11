# Comparison Fairness Audit

## Critical Finding: Most comparisons are NOT compute-matched

### Phase 26 Sequence Budgets

| Sequence | # Ops | ~Tokens (gemma3) | Evidence Retrievals | Hypotheses Generated |
|----------|-------|------------------|--------------------|--------------------|
| single_retrieve | 1 | 258 | 1 | 0 |
| single_gen_hyp | 1 | 207 | 0 | 1 |
| attack_early | 1 | 308 | 0 | 0 |
| explore | 2 | 485 | 1 | 1 |
| discriminate | 3 | 710 | 1 | 1 |
| reversed_B1 | 5 | 1120 | 2 | 2 |
| attack_late | 6 | 1761 | 2 | 2 |
| B1_extended | 7 | 2042 | 3 | 2 |

### Headline Comparisons and Fairness

| Comparison | Condition A | Condition B | Budget Match? | Issue |
|-----------|------------|------------|---------------|-------|
| R2: Complementarity (+0.111) | explore (2 ops, 485 tok) | single_gen_hyp + single_retrieve (1 op each) | **NO** | Explore gets 2 ops combined; controls get 1 each |
| R5: Attack timing (+0.276) | attack_late (6 ops, 1761 tok) | attack_early (1 op, 308 tok) | **NO** | 5.7× compute difference |
| R1: Sequence superiority (+0.003) | B1_extended (7 ops, 2042 tok) | single_gen_hyp (1 op, 207 tok) | **NO** | 9.9× compute difference |
| R4: Order effect (−0.050) | B1_extended (7 ops) | reversed_B1 (5 ops) | **NO** | Different number of operations |
| R6: Fixed vs greedy (+0.003) | B1_extended | single_gen_hyp | **DUPLICATE OF R1** | R6 is misimplemented — same computation as R1 |

### Phase 27 Condition Budgets

| Condition | # LLM Calls | ~Tokens | Evidence Retrieved |
|-----------|------------|---------|-------------------|
| direct | ~1 | ~693 | All |
| reflection | ~1 | ~693 | All |
| greedy_primitive | ~2 | ~640 | Incremental |
| B1_extended | ~4-5 | ~1900 | Incremental |
| FULL_EXPLORE | ~4-5 | ~1900 | Incremental |

### Critical Bug: Reflection = Direct

In `run_v5_execution.py`, the `synthesize` operation returns the result immediately upon completion. In the reflection condition sequence `[retrieve_all, synthesize, critique, revise]`, execution terminates at `synthesize` because it returns a result dict. The `critique` and `revise` operations never execute. Therefore reflection and direct produce IDENTICAL outputs.

**Impact:** The finding "reflection = direct (0.696)" is an implementation artifact, not a scientific result. The paper must NOT claim "reflection adds no value" — the reflection condition was never actually executed.

### Key Fairness Violations for Paper

1. **Attack timing (+0.276):** This is the paper's second-strongest effect. A reviewer will immediately note that attack_late has ~6× the compute and information of attack_early. The effect conflates timing with resource allocation. The paper must acknowledge this prominently.

2. **Complementarity (+0.111):** The V5 R2 computation uses `(explore + discriminate − single_gen_hyp − single_retrieve) / 2`, mixing multi-op and single-op conditions. This is not purely "gen_hyp→retrieve complementarity" — it averages over two multi-op sequences vs two single-op primitives.

3. **R6 is misimplemented:** The code at line ~555 computes `B1_extended − max(single_*)` — identical to R1. There is no greedy baseline in Phase 26. The verdict "fixed vs greedy: INCONCLUSIVE" is based on the wrong comparison.

### Recommended Paper Treatment

1. **Acknowledge budget unfairness explicitly** in the methodology section. State: "Longer sequences necessarily consume more compute; complementarity effects include a resource confound that we cannot fully separate in the current design."
2. **Focus on V4 pairwise comparisons** (2-op pairs vs 1-op singles) where the budget difference is smallest (2× not 10×).
3. **Remove R6 or relabel it** as identical to R1. Do not claim a "fixed vs greedy" comparison was performed in Phase 26.
4. **Remove "reflection adds no value"** from negative findings. Replace with: "The reflection condition was not correctly implemented in Phase 27 (synthesis returned before critique/revise executed), precluding evaluation."
5. **For attack timing**, emphasize the V4 pairwise matrix where gen_hyp→attack vs standalone attack is a fairer 2-op vs 1-op comparison (+0.137).
