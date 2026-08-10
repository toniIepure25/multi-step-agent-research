# Pre-Registered Experimental Protocols — ASAR-REE Scientific Validation

## Statistical Plan

### Primary analysis
- **Effect sizes and confidence intervals** are the primary reporting mechanism
- **p-values** are secondary evidence, not gatekeepers
- Bootstrap confidence intervals (95%) for all continuous metrics
- Paired comparisons for matched scenario conditions

### Multiple comparison policy
- **Confirmatory hypotheses (H-REE-01 to H-REE-06)**: Holm step-down correction at α = 0.05
- **Exploratory ablation discovery**: Benjamini-Hochberg FDR at q = 0.10
- Effect sizes reported regardless of significance

### Repeated trials
- Target 5–10 runs per condition where nondeterminism applies
- Controlled/deterministic scenarios need only 1 run
- Report mean, median, std, bootstrap CI

### Outcome types and tests
- Continuous metrics (quality scores, calibration): paired comparison with effect sizes
- Binary outcomes (correct/incorrect): exact or bootstrapped proportions
- Count data (hypotheses surviving, ignorance items): non-parametric comparison

---

## Confirmatory Hypotheses (Primary)

### H-REE-01: Self-Model Calibration
- **Claim**: Empirical CapabilityPredictor outperforms LLM verbal confidence
- **IV**: Confidence source (verbal vs empirical vs empirical+state)
- **DV**: Brier Score, ECE, selective accuracy
- **Baseline**: LLM verbal confidence
- **Success**: Brier Score reduction ≥ 0.05 (small effect)
- **Falsification**: No improvement or regression

### H-REE-02: Ignorance Foresight
- **Claim**: IgnoranceLedger items predict actual failure causes
- **IV**: Ignorance mechanism ON vs OFF
- **DV**: Ignorance Foresight Score (precision × recall)
- **Baseline**: No ignorance tracking (ablation OFF)
- **Success**: Foresight Score > 0.3 AND above baseline
- **Falsification**: Score ≤ baseline

### H-REE-03: Evidence Independence
- **Claim**: Source-lineage tracking prevents artificial confidence from duplicated evidence
- **IV**: Evidence independence analyzer ON vs OFF
- **DV**: Effective evidence count accuracy, confidence change under duplication
- **Baseline**: No independence tracking
- **Success**: Duplicate source resistance (metamorphic test passes)
- **Falsification**: System confidence scales monotonically with apparent source count

### H-REE-04: Hypothesis Ecology / Premature Convergence
- **Claim**: Explicit hypothesis ecology prevents premature convergence
- **IV**: Hypothesis ecology ON vs OFF
- **DV**: Premature convergence rate, final correctness after anomalous evidence
- **Baseline**: Single-hypothesis reasoning
- **Success**: Convergence rate reduction ≥ 20%
- **Falsification**: No difference or worse final accuracy

### H-REE-05: Epistemic Market Efficiency
- **Claim**: Adaptive metacognitive scheduling improves quality/compute Pareto efficiency
- **IV**: Adaptive scheduler vs fixed-sequence (B3 vs B4)
- **DV**: Quality at equal budget, compute at equal quality
- **Baseline**: Fixed-depth REE (B3)
- **Success**: Pareto improvement in ≥ 2 budget levels
- **Falsification**: No Pareto improvement

### H-REE-06: Cognitive Action Value Prediction
- **Claim**: Epistemic state features predict marginal value of cognitive operations
- **IV**: State feature availability
- **DV**: Rank correlation between predicted and realized epistemic gain
- **Baseline**: Uniform random action selection
- **Success**: Rank correlation > 0.2
- **Falsification**: Correlation ≤ 0

---

## Secondary Hypotheses (Exploratory)

### H-REE-07: Counterfactual Robustness
- Assumption sensitivity: robustness to irrelevant changes, responsiveness to decisive ones

### H-REE-08: Memory Consolidation
- Cross-episode memory reduces repeated errors

### H-REE-09: Synergy Test
- Full REE > sum of individual mechanism effects

### H-REE-10: Ontology Revision
- Explicit OntologyForge improves recovery from misleading framing vs prompt-only

---

## Gate Definitions

### Gate 1: Phase 10 → Phase 11
- Every mechanism passes runtime-influence matrix (6 properties verified)
- CognitiveBudget operational
- B0, B1, B3, B4 baselines runnable
- Mechanism influence tests pass
- Scenario runner functional with dev scenarios
- Held-out scenarios locked, leakage-tested
- Experiment manifests persist exact config
- All tests pass

### Gate 2: Phase 11 → Phase 12
- ≥ 80 controlled scenarios executed with complete artifacts
- ≥ 4 of 6 primary hypotheses have preliminary classifications
- Valid measurement (no critical leakage/runtime defects)
- Raw artifacts persisted and reproducible
- Statistical significance NOT required

### Gate 3: Phase 12 → Phase 13
- CognitiveActionOutcomeDataset ≥ 500 entries
- Realized epistemic gain VECTORS persisted
- Bid calibration analysis complete
- Cognitive Action Regret computed under ≥ 2 scalarizations
- Feature importance analysis complete
- Task-level train/test separation verified

### Gate 4: Phase 13 completion
- All 10 H-REE hypotheses have verdicts with evidence
- Leave-one-out ablation complete + key additive ablations
- Quality-compute Pareto frontier produced
- ≥ 3 prompt-only controls
- Final report with all sections
- Every number traceable to raw artifact
