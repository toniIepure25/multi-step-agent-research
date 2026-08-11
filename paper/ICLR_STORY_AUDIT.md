# ICLR Story Audit

## C1. One-Sentence Test

> What did this paper discover that we did not know before?

**Attempt 1:** "Cognitive operations in LLM research agents exhibit measurable temporal complementarity that is a structural property of the epistemic task."

*Problem:* Requires qualification — the "structural property" claim rests on a simulator where the LLM doesn't affect quality measurement.

**Attempt 2:** "In a controlled epistemic benchmark, hypothesis generation before retrieval yields super-additive epistemic gain (+0.162), while attack before hypothesis formation yields zero gain — and this asymmetry is a property of the task structure, not the operator implementation."

*Problem:* Too long, and "task structure" may be seen as tautological.

**Best one-sentence answer:**

> **In controlled epistemic tasks, the downstream value of cognitive operations like retrieval, reasoning, and falsification depends on their temporal context — specifically, hypothesis generation catalyzes subsequent operations, and attack/falsification has zero value without prior hypothesis formation — and this dependence persists under real LLM execution.**

## C2. Reviewer-Memory Test

> Six months after reading this paper, what ONE result should a researcher remember?

**Answer:** The complementarity matrix (Table 3 / Figure 2). It shows concretely which operation pairs are synergistic, redundant, or interfering. This is actionable for agent designers: "hypothesize before you search; don't attack before you hypothesize."

This should be Figure 1 or prominently placed.

## C3. Benchmark vs Mechanistic Emphasis

### Option A: Benchmark/Methodology
*Story:* "We built a controlled way to measure operation-pair interactions."
- Strengths: Novel methodology, reproducible, extensible.
- Weakness: The benchmark alone is a methods paper; contribution feels thin without interesting findings.

### Option B: Mechanistic Temporal Complementarity
*Story:* "We discovered that cognitive operations interact temporally."
- Strengths: Concrete finding, actionable, surprising (attack timing).
- Weakness: Finding may be seen as obvious or tautological; confounded by compute.

### Recommendation: **B with A as enabler**

The paper should lead with the FINDING (complementarity and timing dependence) and present the benchmark as the METHODOLOGICAL CONTRIBUTION that enables it. Neither alone is strong enough, but together they work.

The title supports this: "Measuring the Value of Cognitive Sequences" emphasizes the finding, while "measuring" signals methodology.

## Title Evaluation Post-Audit

The working title "Measuring the Value of Cognitive Sequences in LLM Research Agents" remains strong. It:
- Does not overclaim
- Emphasizes measurement (methodology) and value (finding)
- Is specific to the domain (LLM agents)
- Does not promise "superior architecture" or "solved problem"

**Keep it.**

## Post-Audit Central Claim (revised)

> In a controlled epistemic benchmark that enables same-state counterfactual evaluation, we measure super-additive temporal complementarity between specific cognitive operation pairs (hypothesis generation → retrieval: +0.162) and strong timing dependence of falsification value. These structural effects persist when cognitive operations are accompanied by real LLM inference. However, general sequence superiority, adaptive control, and transfer to curated evidence tasks are not supported.

Key revision: "accompanied by" instead of "replicated under" — because the LLM does not affect the measured quality.
