# Benchmark Gap Analysis

**Purpose:** Identify what existing benchmarks measure and what ASAR's FalsificationBench must add.

---

## Existing Benchmark Coverage Matrix

| Capability | HypoBench | ResearchBench | ProjectionBench | AstaBench | PaperBench | FrontierScience |
|-----------|:---------:|:-------------:|:---------------:|:---------:|:----------:|:---------------:|
| Hypothesis generation | ✓ | ✓ | ✓ | ✓ | — | — |
| Hypothesis diversity | ✓ | — | — | — | — | — |
| Hypothesis ranking | — | ✓ | — | — | — | — |
| Literature retrieval | — | ✓ | — | ✓ | — | — |
| Progressive revelation | — | — | ✓ | — | — | — |
| Experiment execution | — | — | — | — | ✓ | — |
| Scientific reasoning | — | — | — | ✓ | — | ✓ |
| Code implementation | — | — | — | — | ✓ | — |
| Expert-level problems | — | — | — | — | — | ✓ |

---

## GAP: What NO existing benchmark measures

| Capability | Status | ASAR addresses? |
|-----------|--------|:---------------:|
| **Falsification** — does the system seek disconfirming evidence? | UNMEASURED | ✓ |
| **Belief revision** — does belief appropriately change after evidence? | UNMEASURED | ✓ |
| **Theory abandonment** — does the system kill wrong hypotheses? | UNMEASURED | ✓ |
| **Self-authorship bias** — differential treatment of own vs. external hypotheses? | UNMEASURED | ✓ |
| **Discriminative experiment design** — does experiment distinguish hypotheses? | UNMEASURED | ✓ |
| **Ontology revision** — can system recognize wrong framing? | UNMEASURED | ✓ |
| **Non-identifiability recognition** — does system correctly abstain? | UNMEASURED | ✓ |
| **Evidence independence** — does system detect redundant sources? | UNMEASURED | ✓ |
| **Theory stickiness** — excess confidence retained after refutation? | UNMEASURED | ✓ |
| **Recovery accuracy** — correct ranking after decisive evidence? | UNMEASURED | ✓ |

---

## FalsificationBench Task Families

### Family A: Confirmation Trap
**Gap filled:** Measures whether system recovers from initially misleading evidence
**Ground truth:** Known correct hypothesis + known misleading early evidence
**Metric:** Refutation Sensitivity, Recovery Accuracy, Abandonment Latency

### Family B: Confounded Causality
**Gap filled:** Measures whether system detects hidden confounders
**Ground truth:** Known confounding variable explaining apparent correlation
**Metric:** Confound detection rate, false-causality belief drop

### Family C: Reverse Causality
**Gap filled:** Measures whether system considers direction reversal
**Ground truth:** Known causal direction opposite to initial evidence
**Metric:** Reverse-causality alternative generation rate, direction-correction accuracy

### Family D: Measurement Artifact
**Gap filled:** Measures whether system questions measurement validity
**Ground truth:** Known artifact vs. genuine signal
**Metric:** Artifact detection rate, false-signal belief drop

### Family E: Multiple Mechanisms
**Gap filled:** Measures whether system recognizes multi-causal explanations
**Ground truth:** Two mechanisms each explaining different subsets
**Metric:** Mechanism count accuracy, subset attribution

### Family F: Null World
**Gap filled:** Measures whether system correctly concludes "no relationship"
**Ground truth:** No causal relationship exists
**Metric:** Null conclusion rate, false-discovery rate

### Family G: Ontology Failure
**Gap filled:** Measures whether system rejects the hypothesis space
**Ground truth:** All candidate hypotheses wrong due to shared false premise
**Metric:** Ontology revision rate, false-revision rate

### Family H: Non-Identifiable World
**Gap filled:** Measures whether system correctly abstains
**Ground truth:** Available evidence cannot distinguish hypotheses
**Metric:** Abstention rate, false-conclusion rate

---

## Comparison with Existing Benchmark Design

| Design principle | Existing benchmarks | FalsificationBench |
|-----------------|--------------------|--------------------|
| Ground truth | Often expert labels or similarity | Synthetic/controlled worlds with known causal structure |
| Evaluation | Final answer quality | Process quality across multiple rounds |
| Focus | Generation or retrieval | Self-correction and revision |
| Temporal aspect | Single-shot or progressive | Multi-round with belief tracking |
| Failure modes | Wrong answer | Failure to correct, theory stickiness, premature conclusion |
| Success criteria | Match expected output | Appropriate belief change + correct conclusion type |

---

## Integration Points with External Benchmarks

| External benchmark | How ASAR uses it | What ASAR adds |
|-------------------|-----------------|----------------|
| HypoBench | Raw hypothesis generation capability baseline | Post-generation falsification + revision |
| ResearchBench | Literature retrieval + ranking capability baseline | Prediction + experiment design |
| ProjectionBench | Progressive hypothesis generation comparison | Falsification behavior under equivalent revelation |
| AstaBench | Broad scientific competence reference | Deep self-correction evaluation |
| PaperBench | Downstream experiment execution capability | Hypothesis-driven experiment selection |

---

## Baselines for FalsificationBench

| Baseline | What it tests | Expected behavior |
|----------|--------------|-------------------|
| Single-pass frontier LLM | Can raw LLM reason correctly without structured process? | Good generation, poor revision |
| Reflection (generate → critique → revise) | Does self-critique help? | Moderate improvement, still theory-sticky |
| Multi-agent debate | Does adversarial dialogue help? | Better critique, unclear revision |
| Greedy evidence seeker | What about maximum retrieval? | Confirms leading theory, poor at falsification |
| Random experiment selector | What's the floor? | Baseline oracle regret |
| Fixed scientific workflow | What about a deterministic process? | Competent but inflexible |
| Oracle best-response | What's the ceiling? | Upper bound on all metrics |

---

## Metric Coverage

| Metric | Family A | B | C | D | E | F | G | H |
|--------|:--------:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Refutation Sensitivity | ✓ | ✓ | ✓ | ✓ | — | — | — | — |
| Recovery Accuracy | ✓ | ✓ | ✓ | ✓ | ✓ | — | — | — |
| Abandonment Latency | ✓ | — | — | — | — | — | — | — |
| Theory Stickiness | ✓ | ✓ | ✓ | — | — | — | — | — |
| Discrimination Score | — | — | — | — | — | — | — | — |
| Oracle Regret | — | — | — | — | — | — | — | — |
| Confound Detection | — | ✓ | — | ✓ | — | — | — | — |
| Null Accuracy | — | — | — | — | — | ✓ | — | — |
| Ontology Revision Rate | — | — | — | — | — | — | ✓ | — |
| Abstention Accuracy | — | — | — | — | — | ✓ | — | ✓ |
| IPR (Irrelevant Perturbation Robustness) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

---

## Key Design Constraint

> Do NOT design worlds around the ASAR policy. Design worlds around scientific failure modes.

The benchmark must be fair to ALL baselines, including approaches we haven't built. Worlds should represent genuine scientific challenges, not scenarios engineered to reward a specific architecture.
