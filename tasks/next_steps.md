# Next Steps

> See also: [v0-canonical-architecture.md](../docs/architecture/v0-canonical-architecture.md) for exact v0 scope and success criteria.
> Runtime baseline: Python 3.11+ only. Validation observed under Python 3.10.12 was non-canonical and does not change the repository requirement.
> v0 naming is frozen. Do not rename the canonical v0 components while implementing Phase 1 foundations.

## v0 Build Order (Phase 1)

Each step produces a testable artifact. Each step should be one commit. Do them in order — later steps depend on earlier ones.

| # | What | Layer | Depends on | Status |
|---|------|-------|-----------|--------|
| 1 | Config loader: read `config/*.toml`, return typed settings | `common` | — | completed |
| 2 | ID generation + logging setup | `common` | — | completed |
| 3 | `WorkingMemory`: dict store/retrieve, `compress()` no-op | `memory` | schemas | completed |
| 4 | `SimplePlanner`: single LLM call → `ResearchPlan` | `planning` | `common`, schemas | completed |
| 5 | `WebSearchExecutor`: search API → `list[EvidenceItem]` | `execution` | `common`, schemas | completed |
| 6 | `SimpleSynthesizer`: single LLM call over all evidence → `DecisionPacket` with `Claim`s | `deliberation` | schemas | completed |
| 7 | `EvidenceChecker`: deterministic verification, no LLM → `VerificationResult` | `verification` | schemas | completed |
| 8 | `ExperimentLogger`: build `ExperimentRecord`, compute metrics, write to disk | `evaluation` | schemas | completed |
| 9 | `SequentialOrchestrator`: wire all layers → `ResearchOutput` | `orchestration` | steps 3–8 | completed |
| 10 | Integration test: end-to-end on one Tier 1 question (mocked LLM/search) | tests | step 9 | completed |
| 11 | Live run on one Tier 1 question | — | step 10 | not started |
| 12 | 5 Tier 1 benchmark questions with ground-truth rubrics | `evaluation` | — | not started |
| 13 | Baseline metrics: run pipeline on benchmarks, record results | `evaluation` | steps 11–12 | not started |

## ASAR-REE Implementation Status

All REE phases (0–9) and scientific validation (10–13) are **completed**.

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Forensic Baseline + V2 Architecture Contract | completed |
| 1 | Epistemic State + Event Sourcing + Workspace + Operator Kernel | completed |
| 2 | World Model + Hypothesis Ecology + Ignorance + Research Graph | completed |
| 3 | Ontology Evolution + Counterfactual Lab + Active Experiment Design | completed |
| 4 | Empirical Self Model + Metacognition + Calibration | completed |
| 5 | Dissonance Tribunal + Social Epistemology + Other Model | completed |
| 6 | Epistemic Market + Full Metacognitive Control + Stopping | completed |
| 7 | Federated Memory + Consolidation + Replay Learning | completed |
| 8 | Value Model + Reflective Equilibrium + Full Integration | completed |
| 9 | Scientific Evaluation Suite + Ablations + Release Candidate | completed |
| 10-13 | Scientific Campaign V1 (methodological negative baseline) | completed |
| 14 | Semantic Benchmark Rebuild (EpistemicWorldSimulator) | completed |
| 15 | Metacognitive Calibration + Counterfactual Study V2 | completed |
| 16 | Final Scientific Verdicts | completed |

### Scientific Campaign V1 (SHA: 120a576) — Frozen

Established that content-independent mock operators with substring matching
produce non-discriminative quality. All architectures identical at 33% GT match.
Preserved as immutable negative baseline.

### Scientific Campaign V2 (SHA: 23e0774) — Current

| Dataset | Records | Families | Architectures |
|---------|---------|----------|---------------|
| Dev holdout | 150 | 5 | B0, B1, REE |
| Dev ablation | 350 | 5 | 7 ablation configs |
| Dev Pareto | 600 | 5 | 3 × 4 budgets |
| Validation | 75 | 5 | 3 |
| Locked test | 75 | 5 | 3 |
| Counterfactual | 2000 | 5 | 5 actions × 500 states |
| Market comparison | 200 | 5 | 4 market variants |
| **Total** | **3450** | | |

### Headline Results (Campaign V2)

| Finding | Value | Interpretation |
|---------|-------|----------------|
| B1 vs REE (locked test) | 0.594 vs 0.356 | B1 fixed strategy wins |
| Hypothesis ecology ablation | d ≈ 1.4 | Causally critical mechanism |
| Market anti-calibration | round-robin ≥ market | Market scheduling hurts |
| Bid-value correlation | r = 0.137 | Weak positive (improved from V1's -0.083) |
| Oracle-realized correlation | r = 0.031 | Nearly zero |
| Best action prediction | 34.8% (rule) vs 51.6% (always-retrieve) | Simple rule underperforms majority |

### Hypothesis Verdicts

| Hypothesis | Verdict |
|---|---|
| H-REE-05: Hypothesis ecology reduces convergence | **SUPPORTED** (d ≈ 1.4) |
| H-REE-02: Ignorance predicts failure | **PARTIALLY_SUPPORTED** (small effect) |
| H-REE-09: Full REE > additive sum | **NOT_SUPPORTED** |
| H-REE-10: Adaptive scheduling improves efficiency | **NOT_SUPPORTED** |
| H-REE-01, 03, 04, 06, 07, 08 | **INCONCLUSIVE** |

### Required Next Steps (Priority Order)

1. **Fix the Epistemic Market** — use counterfactual data to build calibrated scheduler
2. **Force reasoning into REE** — the reason operator is consistently best but underselected
3. **Make remaining ablations causal** — self-model, stopping, evidence independence need deeper controller integration
4. **Model-in-the-loop campaign** — use real LLM with simulator ground truth
5. **Expand scenario families** — tribunal, ontology, memory scenarios
6. **Larger N** — 50+ worlds per family for statistical power
7. **Learned scheduler** — if enough counterfactual data supports it
