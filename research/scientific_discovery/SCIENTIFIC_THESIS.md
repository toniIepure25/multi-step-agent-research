# Scientific Thesis — ASAR Scientific Discovery Engine

## Central Research Question

> Can an AI system reliably identify which hypotheses deserve to survive — through falsification, discriminative experiment design, and principled belief revision — rather than merely generating plausible explanations?

---

## Thesis Statement

Modern LLM-based research agents excel at hypothesis generation but systematically fail at hypothesis elimination. They exhibit:

1. **Confirmation bias** — preferentially seeking evidence consistent with leading hypotheses
2. **Theory stickiness** — retaining high confidence in hypotheses after decisive refutation
3. **Discrimination failure** — selecting experiments that confirm rather than discriminate
4. **Ontology rigidity** — never questioning whether the hypothesis space itself is wrong

The ASAR Scientific Discovery Engine tests whether explicit falsification-first reasoning, structured hypothesis ecology, and quantitative belief revision can produce measurably better scientific self-correction compared to standard LLM reasoning, reflection, and debate approaches.

---

## What This Project Is

A research system that implements and evaluates the scientific process as a computational loop:

```
Problem formulation
→ Competing hypothesis ecology
→ Prediction derivation
→ Falsification attack
→ Discriminative experiment selection
→ Evidence gathering / computational experiment
→ Quantitative belief update
→ Theory revision or abandonment
→ Ontology revision when the framing itself fails
→ Stop when appropriately uncertain
```

---

## What This Project Is NOT

- Not a search engine or RAG pipeline
- Not a report-writing agent
- Not a chatbot that generates plausible hypotheses
- Not an architecture paper claiming novelty from complexity
- Not a system optimized to sound like a brilliant scientist

---

## Core Scientific Capabilities Under Evaluation

### Capability 1: Falsification-First Reasoning
Given a leading hypothesis, can the system identify its strongest falsifier and search specifically for disconfirming evidence?

### Capability 2: Hypothesis Ecology Maintenance
Can the system maintain genuinely diverse competing explanations (not paraphrases) and appropriately distribute belief?

### Capability 3: Discriminative Experiment Design
Given competing hypotheses, can the system select experiments that maximally distinguish between them (rather than confirm the leading theory)?

### Capability 4: Quantitative Belief Revision
After receiving decisive evidence, does the system appropriately update beliefs — including abandoning hypotheses with evidence-based thresholds?

### Capability 5: Self-Correction Under Self-Authorship
Does the system apply equal scrutiny to hypotheses it generated itself vs. externally provided hypotheses?

### Capability 6: Ontology Recovery
When all candidate hypotheses share a false premise, can the system detect that the hypothesis space itself is inadequate?

### Capability 7: Calibrated Uncertainty
Does the system correctly abstain, declare non-identifiability, or request experiments rather than forcing a conclusion?

---

## Distinguishing Contribution

The project's potential novelty lies not in any single mechanism but in the integrated, measurable evaluation of:

**Falsification + Belief Revision + Theory Abandonment + Ontology Recovery**

as a unified scientific process, evaluated against controlled benchmarks where ground truth is known.

This differs from prior work that evaluates:
- Hypothesis generation only (HypoBench, Co-Scientist)
- Research ability broadly (AstaBench, PaperBench)
- Retrieval quality (standard RAG benchmarks)
- Single-step reasoning (standard QA)

---

## Success Criteria

The project succeeds if it demonstrates at least ONE of:

1. **Falsification advantage**: Falsification-first workflow measurably improves recovery from misleading evidence vs. strong baselines under controlled conditions
2. **Discrimination advantage**: Information-based experiment selection reduces oracle regret vs. confirmation-seeking selection
3. **Self-correction demonstration**: System reliably abandons wrong hypotheses (including self-generated ones) after decisive falsification
4. **Ontology recovery**: System detects shared false premises at a rate significantly above baseline
5. **Calibrated uncertainty**: System correctly abstains under non-identifiability more often than baselines that force conclusions

The project also succeeds as negative science if it demonstrates:

6. **Theory stickiness finding**: Frontier LLMs systematically fail to abandon hypotheses after falsification — quantified and characterized

---

## Strongest Possible Negative Result

If frontier LLM agents generate good hypotheses but fail to abandon them after falsification, that is itself an important finding:

> Modern AI scientists are better hypothesis generators than hypothesis killers.

This would reframe the field's focus from generation quality to self-correction capability.

---

## Evaluation Philosophy

- Define scientific capability BEFORE building mechanisms
- Design externally meaningful evaluation BEFORE implementation
- Establish baselines BEFORE claiming improvement
- Use controlled worlds where ground truth is known
- Do NOT design benchmarks around the ASAR policy
- Design benchmarks around scientific failure modes
- Behavioral influence gate: every mechanism must measurably change outcomes
