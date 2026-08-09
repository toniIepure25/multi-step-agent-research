# Research Hypotheses

> See also: [research-agenda.md](research-agenda.md) · [open-questions.md](open-questions.md) · [experiment templates](../../experiments/templates/)

Testable hypotheses. Each should be falsifiable and connected to an experiment.

## Format

```
### H-NNN: <Title>
**Claim:** <Falsifiable statement>
**Rationale:** <Why we believe this might be true>
**Test:** <How to test — reference experiment template>
**Layer(s):** <Which layer(s) this tests>
**Status:** untested | supported | refuted | inconclusive
**Evidence:** <Link to experiment results or failed direction note>
```

---

### H-001: Structured Plans Outperform Linear Execution
**Claim:** A planner that decomposes research goals into structured sub-tasks produces higher-quality outputs than a single-pass LLM prompt, as measured by factual accuracy and completeness.
**Rationale:** Decomposition reduces the cognitive load per step and allows targeted tool use.
**Test:** Compare single-pass vs. planned execution on benchmark. Use [experiment_template.md](../../experiments/templates/experiment_template.md).
**Layer(s):** `planning`, `orchestration`
**Status:** untested
**Evidence:** —

### H-002: Memory Compression Preserves Research Utility
**Claim:** Compressed memory summaries retain sufficient information to support multi-step research without significant quality degradation (< 10% drop on downstream metrics).
**Rationale:** LLM-generated summaries can capture key facts while reducing token count by 5–10x.
**Test:** Ablation: full-context vs. compressed-context. Use [ablation_template.md](../../experiments/templates/ablation_template.md).
**Layer(s):** `memory`
**Status:** untested
**Evidence:** —

### H-003: Verification Catches Meaningful Errors
**Claim:** A separate verification layer catches at least 30% of factual errors that pass through generation unchecked.
**Rationale:** Separation of generation and verification introduces an independent check.
**Test:** Inject known errors, measure verification recall. Use [experiment_template.md](../../experiments/templates/experiment_template.md).
**Layer(s):** `verification`
**Status:** untested
**Evidence:** —

### H-004: Evidence Grounding Reduces Hallucination
**Claim:** Requiring all claims to link to `EvidenceItem`s reduces hallucination rate by at least 50% compared to ungrounded generation.
**Rationale:** Grounding forces citation, making unsupported claims structurally impossible.
**Test:** Compare grounded vs. ungrounded on hallucination benchmark. Use [experiment_template.md](../../experiments/templates/experiment_template.md).
**Layer(s):** `grounding`
**Status:** untested
**Evidence:** —

### H-005: Multi-Perspective Deliberation Improves Synthesis
**Claim:** Deliberation using multiple perspectives (advocate/critic) produces more balanced and accurate syntheses than single-perspective generation.
**Rationale:** Adversarial perspectives surface blind spots and conflicts.
**Test:** Compare single vs. multi-perspective on nuanced topics. Use [ablation_template.md](../../experiments/templates/ablation_template.md).
**Layer(s):** `deliberation`
**Status:** untested
**Evidence:** —

---

## ASAR-REE Hypotheses

The following hypotheses are specific to the Reflexive Epistemic Ecology (REE) architecture. Each defines independent variables, dependent variables, baseline, evaluation approach, success criterion, and falsification condition.

### H-REE-01: Empirical Self Model Outperforms Verbal Confidence
**Claim:** An empirical self model that learns from historical outcomes predicts ASAR correctness better than raw LLM verbal confidence.
**Rationale:** LLMs are known to be poorly calibrated when reporting their own confidence. An empirical model trained on actual success/failure data should achieve better calibration.
**Independent variables:** Prediction source (empirical self model vs. LLM verbal confidence)
**Dependent variables:** Brier score, Expected Calibration Error (ECE)
**Baseline:** LLM verbal confidence on the same tasks
**Evaluation dataset:** Controlled task suite with known correct answers across multiple domains
**Success criterion:** Self model achieves lower Brier score and ECE than verbal confidence
**Falsification condition:** Self model Brier score >= verbal confidence Brier score across 3+ task domains
**Layer(s):** `self_model`, `metacognition`
**Status:** untested
**Evidence:** —

### H-REE-02: Ignorance Ledger Predicts Failure Causes
**Claim:** Pre-answer Ignorance Ledger entries predict post-hoc failure causes above chance.
**Rationale:** If the system correctly identifies what it does not know before answering, those identified unknowns should correlate with actual failure causes when errors occur.
**Independent variables:** Ignorance ledger content (present vs. absent)
**Dependent variables:** Ignorance Foresight Score (fraction of actual failure causes anticipated in advance, severity-weighted)
**Baseline:** Random selection of ignorance items (chance level)
**Evaluation dataset:** Tasks where the system produces incorrect or incomplete answers, with post-hoc failure analysis
**Success criterion:** Ignorance Foresight Score > 2x chance level
**Falsification condition:** Ignorance Foresight Score <= chance level across 20+ failure instances
**Layer(s):** `ignorance`
**Status:** untested
**Evidence:** —

### H-REE-03: Sealed First Round Improves Minority Preservation
**Claim:** Sealed-first-round deliberation improves Minority Preservation Rate under misleading-majority conditions compared with open debate.
**Rationale:** When participants must commit independently before seeing others' conclusions, diverse perspectives are protected from premature conformity and social influence cascades.
**Independent variables:** Deliberation protocol (sealed first round vs. open debate)
**Dependent variables:** Minority Preservation Rate (probability that a correct minority hypothesis survives deliberation)
**Baseline:** Open (unsealed) multi-agent deliberation
**Evaluation dataset:** Misleading-majority benchmark where one process has decisive evidence while others receive misleading information
**Success criterion:** Sealed protocol MPR > open protocol MPR by at least 15 percentage points
**Falsification condition:** Sealed protocol MPR <= open protocol MPR across 10+ misleading-majority scenarios
**Layer(s):** `social`
**Status:** untested
**Evidence:** —

### H-REE-04: Ontology Branching Improves Recovery from False Framing
**Claim:** Ontology branching improves recovery from false initial framing.
**Rationale:** When the initial conceptual frame is deliberately misleading, maintaining multiple alternative ontologies allows the system to escape the trap by exploring structurally different explanatory frameworks.
**Independent variables:** Ontology mode (single fixed ontology vs. ontology branching)
**Dependent variables:** Ontology Escape Rate (fraction of false-framing tasks where system recovers correct answer)
**Baseline:** Single-ontology mode on the same tasks
**Evaluation dataset:** False-initial-ontology benchmark with deliberately misleading question framing
**Success criterion:** Branching escape rate > single-ontology escape rate by at least 20 percentage points
**Falsification condition:** Branching escape rate <= single-ontology escape rate across 10+ false-framing tasks
**Layer(s):** `ontology`
**Status:** untested
**Evidence:** —

### H-REE-05: Epistemic Market Achieves Better Quality/Compute Frontier
**Claim:** Epistemic Market scheduling achieves a better quality/compute Pareto frontier than fixed-depth cognition.
**Rationale:** By dynamically allocating compute to the most epistemically valuable operation, the market should achieve higher quality per unit of compute compared to a fixed sequence of operations.
**Independent variables:** Scheduling strategy (epistemic market vs. fixed-depth vs. round-robin)
**Dependent variables:** Research quality metrics at matched compute budgets; area under quality/compute curve
**Baseline:** Fixed-depth cognition and round-robin scheduling at same total token budget
**Evaluation dataset:** Tasks across difficulty tiers with varying compute budgets
**Success criterion:** Market achieves higher quality at equal budget, or equal quality at lower budget
**Falsification condition:** Market quality/compute curve dominated by fixed-depth across 3+ budget levels
**Layer(s):** `metacognition`
**Status:** untested
**Evidence:** —

### H-REE-06: Provenance Clustering Reduces False Confidence
**Claim:** Evidence provenance clustering reduces false confidence caused by duplicated-source evidence.
**Rationale:** When multiple citations derive from a single original source, naive counting treats them as independent support. Provenance clustering detects common ancestry and adjusts effective evidence count.
**Independent variables:** Evidence handling (naive counting vs. provenance clustering)
**Dependent variables:** Evidence Independence Score (effective independent evidence roots after clustering); calibration on duplicated-source scenarios
**Baseline:** Naive evidence counting without provenance analysis
**Evaluation dataset:** Citation-duplication benchmark where the same source appears through multiple wrappers
**Success criterion:** Provenance clustering correctly identifies shared roots and reduces effective evidence count by >= 50% on duplicated scenarios
**Falsification condition:** Clustering fails to detect shared provenance in >= 50% of duplicated scenarios
**Layer(s):** `social`
**Status:** untested
**Evidence:** —

### H-REE-07: Counterfactual Reasoning Improves Responsiveness Without Reducing Robustness
**Claim:** Counterfactual reasoning improves responsiveness to causally decisive assumption changes without reducing robustness to irrelevant perturbations.
**Rationale:** A well-calibrated system should change its mind when causally relevant assumptions change and remain stable when irrelevant factors are perturbed.
**Independent variables:** Architecture mode (with counterfactual reasoning vs. without)
**Dependent variables:** Counterfactual Robustness (stability under irrelevant perturbations); Counterfactual Responsiveness (sensitivity to causally decisive perturbations)
**Baseline:** System without counterfactual reasoning module
**Evaluation dataset:** Paired scenarios: irrelevant perturbation (conclusion should hold) and causally decisive perturbation (conclusion should change)
**Success criterion:** With counterfactuals: responsiveness improves by >= 15pp while robustness does not decrease by more than 5pp
**Falsification condition:** Responsiveness does not improve, or robustness decreases by >= 10pp
**Layer(s):** `ontology`
**Status:** untested
**Evidence:** —

### H-REE-08: Offline Consolidation Improves Subsequent Performance
**Claim:** Offline consolidation improves subsequent strategy selection and contradiction recovery without changing the underlying foundation model.
**Rationale:** By replaying episodes, compressing patterns, and updating procedural/self-model memory between episodes, the system should make better strategy choices on later related tasks.
**Independent variables:** Consolidation (with offline replay vs. without)
**Dependent variables:** Strategy selection accuracy and contradiction recovery rate on subsequent tasks
**Baseline:** Same system without offline consolidation between episodes
**Evaluation dataset:** Sequential task pairs where the second task benefits from lessons learned in the first
**Success criterion:** Consolidation improves second-task performance by >= 10% relative
**Falsification condition:** No measurable improvement across 10+ task pairs
**Layer(s):** `memory_federation`
**Status:** untested
**Evidence:** —

### H-REE-09: Full REE Architecture Produces Positive Interaction Effects
**Claim:** The full REE architecture produces positive interaction effects beyond the sum of isolated components.
**Rationale:** If the architecture is well-designed, components should enhance each other: self-model improves scheduling, scheduling improves hypothesis testing, hypothesis testing improves ignorance tracking, etc.
**Independent variables:** Architecture condition (full REE vs. sum-of-individual-ablations)
**Dependent variables:** Overall research quality metrics
**Baseline:** Best individual component ablation
**Evaluation dataset:** Comprehensive task suite across difficulty tiers
**Success criterion:** Full REE outperforms best individual ablation by >= 5% on at least 2 quality metrics
**Falsification condition:** Full REE does not outperform best individual ablation on any quality metric
**Layer(s):** all REE modules
**Status:** untested
**Evidence:** —

### H-REE-10: Hypothesis Ecology Outperforms Single-Trajectory Reasoning
**Claim:** At equal inference budget, preserving a healthy ecology of competing hypotheses improves research quality over single-trajectory reasoning.
**Rationale:** Maintaining multiple competing explanations protects against premature commitment and enables the system to recover when the initial hypothesis is wrong.
**Independent variables:** Reasoning mode (hypothesis ecology vs. single-trajectory)
**Dependent variables:** Answer quality (accuracy, completeness, groundedness); Paradigm Revision Score
**Baseline:** Single-trajectory reasoning at equal token budget
**Evaluation dataset:** Tasks where the initially obvious answer is wrong or incomplete
**Success criterion:** Ecology mode achieves higher accuracy on misleading-initial-hypothesis tasks with <= 10% quality drop on straightforward tasks
**Falsification condition:** Ecology mode does not outperform single-trajectory on misleading tasks, or loses >= 15% on straightforward tasks
**Layer(s):** `world_model`, `operators`
**Status:** untested
**Evidence:** —
