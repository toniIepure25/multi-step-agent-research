# Simulated ICLR Reviews — Pre-Hardening

---

## Reviewer 1 — Mechanistic Reasoning Expert

**Summary:** The paper introduces a controlled epistemic benchmark for measuring temporal complementarity among heterogeneous cognitive operations in LLM research agents. The central finding is that hypothesis generation catalyzes subsequent retrieval (+0.162), and that attack timing is state-dependent. These effects replicate under two LLM substrates but not on curated evidence summaries.

**Strengths:**
- Counterfactual same-state evaluation is a genuinely useful methodological contribution.
- The complementarity matrix (Table 3) provides concrete, interpretable evidence of operation interactions.
- Negative findings (adaptive control failure, non-transfer) are commendably prominent.
- The paper does not overclaim.

**Weaknesses:**
1. **The complementarity definition is not consistent across experiments.** V3 uses `Q(seq) − mean(Q(ops))` over 3-op sequences; V4 uses `Q(A→B) − 0.5×(Q(A)+Q(B))` over 2-op pairs; V5 R2 uses a 4-condition composite. The paper should settle on one definition and use it throughout.
2. **gen_hyp→gen_hyp interference (−0.050) has a CI crossing zero** [−0.136, +0.035]. Claiming "interference" is overstated.
3. **The complementarity effect (+0.162) conflates temporal structure with information advantage.** A 2-op sequence sees more information than a single operation. Without matched-budget controls, "complementarity" could partially be "more compute."
4. **No formal significance testing.** CIs are mentioned but no p-values, effect-size measures (Cohen's d), or non-parametric tests.

**Technical correctness:** Mostly sound, but the fairness issues are real. 6/10.

**Novelty:** Moderate-high. Same-state counterfactual evaluation of heterogeneous ops is genuinely novel. 7/10.

**Clarity:** Good overall, but the formalism section needs tightening. 7/10.

**Overall:** 5 (Marginally below acceptance threshold)

**Confidence:** 4 (High)

---

## Reviewer 2 — LLM Agents Expert

**Summary:** The paper measures how different cognitive operations compose in a controlled simulator, then tests whether these effects replicate with real LLMs. The LLM replication is the key selling point.

**Strengths:**
- The research question is timely and relevant to the agent-building community.
- Using two materially different models (27B QAT vs 11B Q8_0) for replication is good practice.
- The attack-timing result is intuitive and potentially actionable for agent design.

**Weaknesses:**
1. **The LLM replication is not what it appears.** Phase 26 quality scores come from the deterministic simulator, not from LLM output quality. The LLM generates text, but the simulator independently advances state and scores quality. The "replication" confirms that the simulator's structural effects persist when an LLM is present, but it does NOT test whether LLM-generated hypotheses/reasoning/attacks have temporal complementarity. This distinction is fundamental.
2. **The "cross-model consistency" result is trivially expected.** If quality scores come from the deterministic simulator and the same sequences are applied, the scores MUST be identical regardless of which model runs. This is not evidence of model invariance — it's an artifact of the evaluation design.
3. **Prompt dependence is not analyzed.** The LLM's contribution is through prompts, but no prompt sensitivity analysis is performed. How much do results change with different prompts?
4. **The capability gate rubric scores (many at 1.0) are superficial.** Scoring 1.0 for "attack" by checking for keywords like "weakness" or "flaw" does not establish that the model generates scientifically useful falsification.
5. **Phase 27 "real evidence" is author-curated summaries**, not real documents. The claim of "static real-evidence transfer" is misleading.

**Technical correctness:** The evaluation framework has a fundamental design issue: the LLM doesn't actually affect the measured quality. 4/10.

**Novelty:** The benchmark idea is novel; the LLM "replication" adds less than claimed. 5/10.

**Significance:** If the LLM replication is reinterpreted, the paper is primarily a simulator study with limited external validity. 4/10.

**Overall:** 4 (Below acceptance threshold)

**Confidence:** 4 (High)

---

## Reviewer 3 — Benchmark/Evaluation Expert

**Summary:** A controlled epistemic benchmark for measuring cognitive operation value, with simulator experiments and two validation attempts (LLM, curated evidence).

**Strengths:**
- Event-sourcing/state-forking for counterfactual evaluation is a clean design.
- The benchmark is deterministic and reproducible.
- Negative results are not hidden.

**Weaknesses:**
1. **The benchmark may be constructed so complementarity MUST appear.** If `generate_hypothesis` is the only operation that creates hypotheses, and quality partially depends on having correct hypotheses, then gen_hyp must precede reasoning for non-zero quality. This is a design property, not an empirical discovery.
2. **N=14 for Phase 27 is extremely underpowered.** With a condition range of 0.030 and standard deviations of 0.06-0.11, this experiment cannot detect effects smaller than ~0.05 with reasonable power. The "NOT_SUPPORTED" verdict may simply be a power failure.
3. **The reflection condition is broken** (synthesize returns before critique/revise execute). This invalidates one of five Phase 27 conditions.
4. **R6 (fixed vs greedy) is a code duplicate of R1.** No greedy baseline was actually tested in Phase 26.
5. **The evidence packs are synthetic** despite being labeled "real evidence." Ground truth is not independently established.
6. **The quality metric is a composite with arbitrary weights.** Different weighting would produce different complementarity patterns.

**Technical correctness:** Multiple implementation bugs (R6, reflection). 4/10.

**Novelty:** The benchmark idea has merit but the execution has significant flaws. 5/10.

**Reproducibility:** Seeds, configs, and code are provided. 7/10.

**Overall:** 4 (Below acceptance threshold)

**Confidence:** 5 (Very high)

---

## Reviewer 4 — Hostile but Fair General ML Reviewer

**Summary:** This paper presents a synthetic benchmark for measuring temporal interactions among cognitive operations in LLM agents. The main finding is that hypothesis generation helps downstream retrieval and reasoning in the benchmark.

**Strengths:**
- The question is worth asking.
- The paper is honest about what didn't work.

**Weaknesses:**
1. **Is the result trivial?** That hypothesis generation before retrieval helps find relevant evidence is common sense in information retrieval (query formulation helps search). The paper dresses up a well-known principle (formulate a question before searching) in novel terminology. What specific new knowledge does the ML community gain?
2. **The benchmark proves a property of the benchmark.** If the simulator rewards hypothesis-correct retrieval and only gen_hyp creates hypotheses, then sequences starting with gen_hyp must outperform. This is tautological, not empirical.
3. **"Complementarity" or just "prerequisites"?** Attack has zero value without hypotheses because there's nothing to attack. This is a prerequisite relationship, not temporal complementarity in any interesting sense. The options/RL literature has studied prerequisite structures extensively.
4. **The LLM "replication" replicates the simulator, not the LLM effect.** Since scores come from the deterministic simulator regardless of LLM output, the LLM is irrelevant to the quality measurement. The paper should honestly state this.
5. **Two local models on one Mac Studio are not a convincing cross-model study.** Both models were served from the same hardware with the same backend, using the same prompts. This is not the diversity needed for a "cross-model" claim.
6. **Why should the ICLR community care?** The paper discovers properties of its own benchmark and fails to show transfer to anything practical. The benchmark-validity argument is circular.
7. **The adaptive control section is underdeveloped.** A single transparent rule-based policy is tested and fails. This tells us almost nothing about whether adaptive control is possible.

**Technical correctness:** Sound arithmetic, but the interpretation of "replication" is misleading. 5/10.

**Novelty:** The counterfactual evaluation method has some novelty. The findings are less novel than presented. 4/10.

**Significance:** Limited without evidence of practical value. 3/10.

**Overall:** 3 (Clear reject)

**Confidence:** 4 (High)

---

## Score Summary

| Reviewer | Overall | Confidence |
|----------|---------|-----------|
| R1 (Mechanistic) | 5 | 4 |
| R2 (LLM Agents) | 4 | 4 |
| R3 (Benchmark) | 4 | 5 |
| R4 (Hostile Fair) | 3 | 4 |
| **Mean** | **4.0** | **4.25** |
