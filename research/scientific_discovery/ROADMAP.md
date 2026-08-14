# ASAR Scientific Discovery Engine — Roadmap

**Date:** 2026-08-14
**Philosophy:** Each stage earns complexity through demonstrated behavioral influence. No stage advances without passing its GO/NO-GO gate.

---

## Stage 0: Audit + Design (CURRENT)

**Deliverables:**
- [x] FORENSIC_ARCHITECTURE_AUDIT.md
- [x] SCIENTIFIC_THESIS.md
- [x] PRIOR_ART_2026.md
- [x] BENCHMARK_GAP_ANALYSIS.md
- [x] SD_HYPOTHESES.md
- [x] STATE_SCHEMA.md
- [x] FALSIFICATIONBENCH_SPEC.md
- [x] ROADMAP.md (this file)

**Duration:** 1 session
**GO condition:** All documents complete, no architectural blocker identified

---

## Stage 1: Scientific State + Falsification Core

**Implements:**
- `ScientificState` — persistent typed belief state
- `StructuredHypothesis` — hypothesis with maturity, predictions, falsifiers
- `HypothesisEcology` — competing hypothesis management with diversity metrics
- `BeliefUpdater` — quantitative belief revision
- `FalsificationEngine` — generates falsifiers, searches for disconfirmation
- `ScientificController` — minimal loop: propose → falsify → update → stop

**Benchmarks built:**
- Confirmation Trap worlds (Type A) — 5 minimum
- Confounded Causality worlds (Type B) — 5 minimum
- Non-Identifiable worlds (Type H) — 5 minimum

**Metrics implemented:**
- Refutation Sensitivity (RS)
- Theory Stickiness (TS)
- Recovery Accuracy (RA)
- Abandonment Latency (AL)
- Irrelevant Perturbation Robustness (IPR)

**Baselines:**
- Single-pass LLM
- Reflection (generate → critique → revise)

**GO/NO-GO criteria:**
- [ ] State replay PASSES (event → state reconstruction is deterministic)
- [ ] Behavioral influence PASSES (FalsificationEngine ON vs OFF produces measurable metric change)
- [ ] Belief revision tests PASS (metamorphic invariants hold)
- [ ] At least one metric shows meaningful difference from single-pass baseline

**Estimated duration:** 2–3 sessions

---

## Stage 2: Experiment Design

**Implements:**
- `ExperimentDesigner` — discrimination-based experiment selection
- `PredictedOutcomeTable` — per-hypothesis outcome predictions
- `DiscriminationScore` — pairwise hypothesis distinguishability
- `InformationGain` — expected information gain computation

**Benchmarks built:**
- Experiment Design worlds (provide hypotheses + candidate experiments, measure selection quality)
- Oracle regret computation

**Metrics added:**
- Oracle Regret
- Hypothesis Discrimination Score
- Cost-adjusted Information Gain

**Baselines added:**
- Random experiment selector
- Confirmation-seeking selector (always test leading hypothesis)
- Greedy information seeker

**GO/NO-GO criteria:**
- [ ] Experiment selection beats random (p < .05, d > 0.3)
- [ ] Experiment selection beats confirmation-seeking (p < .05)
- [ ] Oracle regret decreases vs baselines under locked worlds

**Estimated duration:** 2 sessions

---

## Stage 3: Theory Abandonment + Ontology

**Implements:**
- `ABANDON_HYPOTHESIS` action with explicit threshold + complexity penalty
- `REVISE_ONTOLOGY` action (expensive, rare)
- Ad-hoc complexity penalty for rescue assumptions
- Self-authorship bias measurement

**Benchmarks built:**
- False-Theory Recovery (Type A enhanced with authorship conditions)
- Ontology Failure worlds (Type G) — 5 minimum
- Self-authorship bias matched conditions

**Metrics added:**
- Self-Authorship Bias (SAB)
- Ontology Revision Rate (ORR)
- False Ontology Revision Rate (FORR)
- Ad-hoc assumption count

**GO/NO-GO criteria:**
- [ ] Correct abandonment improves over baseline
- [ ] False abandonment remains controlled (< 10% of valid hypotheses)
- [ ] Ontology recovery rate > 0 on failure worlds (system can do it at all)
- [ ] False ontology revision rate < 20% on non-failure worlds

**Estimated duration:** 2 sessions

---

## Stage 4: External Benchmark Integration

**Activities:**
- Integrate HypoBench (raw generation capability)
- Integrate ResearchBench subset (retrieval + ranking)
- Integrate ProjectionBench subset (progressive hypothesis)
- Run AstaBench subset if feasible

**Purpose:** Verify ASAR doesn't regress on standard capabilities while adding self-correction

**GO/NO-GO criteria:**
- [ ] No catastrophic regression on standard benchmarks
- [ ] ASAR shows distinct advantage on self-correction metrics not measured by external benchmarks
- [ ] External benchmark results are not used to modify ASAR (locked evaluation)

**Estimated duration:** 1–2 sessions

---

## Stage 5: Time-Capsule Discovery (Flagship Evaluation)

**Implements:**
- Historical discovery task construction (10–20 high-quality tasks)
- Contamination defense: cutoff manifest, document whitelist, leakage detection
- Future-oracle evaluation using post-discovery literature
- Manual leakage audit for subset

**Domain selection criteria:**
- Clear cutoff date before major discovery
- Sufficient pre-cutoff literature accessible
- Post-cutoff evidence usable as oracle
- Low contamination risk (post-2023 discoveries preferred)
- Scientific significance

**GO/NO-GO criteria:**
- [ ] At least 10 tasks pass contamination audit
- [ ] ASAR generates hypotheses with non-trivial overlap with eventual discovery
- [ ] ASAR proposes experiments that are retrospectively validated
- [ ] Performance exceeds single-pass baseline on at least 2/3 metrics

**Estimated duration:** 3–4 sessions

---

## Stage 6: Live Computational Discovery

**Activities:**
- Select ONE domain based on: data availability, experiment cost, objective metrics, novelty opportunity, replication feasibility
- Run genuine end-to-end study: literature → hypothesis → prediction → experiment → analysis → revision
- Preregistered analysis
- Holdout/replication attempt

**Candidate domains (to be evaluated):**
- Neuroscience (public datasets, testable hypotheses)
- ML systems behavior (public models, cheap experiments)
- Bioinformatics (public datasets, statistical testing)
- Scientific machine learning (reproducible, computational)

**GO/NO-GO criteria:**
- [ ] At least one hypothesis survives preregistered statistical test
- [ ] Effect replicates on holdout specification
- [ ] Novelty audit shows no direct prior art
- [ ] Independent expert assessment (if feasible)

**Estimated duration:** 4+ sessions

---

## Paper Decision Points

Papers are NOT predetermined. They emerge from results:

| After Stage | Possible paper | Condition |
|-------------|---------------|-----------|
| 1–2 | "FalsificationBench: Evaluating Scientific Self-Correction in AI" | If benchmark itself is strong and reveals interesting system differences |
| 2–3 | "Can AI Scientists Abandon Wrong Theories?" | If falsification/belief revision shows clear empirical finding |
| 3–4 | "From Hypothesis Generation to Scientific Self-Correction" | If integrated process strongly outperforms baselines |
| 6 | Live discovery paper | If genuine hypothesis survives testing |
| Any | Negative finding paper | If frontier LLMs systematically fail at self-correction |

---

## Resource Constraints

- Primary compute: LLM API calls (GPT-4o / Claude as primary models)
- Budget per stage: ~$50–200 in API costs
- Development: 2–3 sessions per stage
- Total timeline to Stage 4: ~8–12 sessions
- Total to Stage 6: ~15–20 sessions

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|-----------|
| LLMs can't generate valid falsifiers | HIGH | Test early in Stage 1; if failing, investigate prompt engineering or decomposition |
| Controlled worlds are too simple / too hard | MEDIUM | Use difficulty levels; calibrate on dev set |
| Self-authorship bias doesn't exist in LLMs | MEDIUM | Important negative finding; publish if well-measured |
| Ontology revision is beyond current LLM capability | MEDIUM | Accept as negative finding; characterize failure mode |
| Time-capsule contamination is unavoidable | HIGH | Use post-2023 discoveries; manual audit subset |
| Compute budget insufficient for full evaluation | MEDIUM | Prioritize Stage 1–3; defer expensive stages |
| No improvement over single-pass LLM | HIGH | Characterize WHY; negative finding is still valuable |
