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

Steps 1–2 are independent. Steps 3–8 depend only on `common` + schemas and are independent of each other. Step 9 wires everything. Step 10 is the proof.

## Open Decisions Before Starting

- **OQ-P1**: Which search API? Tavily, Brave Search, or SerpAPI. Pick one, add as dependency.
- **OQ-P2**: API key management — env vars for now, revisit later.
- **OQ-A4**: Error handling in executors — decide before step 5. Recommendation: return empty `list[EvidenceItem]` on failure + log, don't raise.

## NOT in v0 (Do Not Implement Yet)

- Re-planning loop (`planning.replan()` raises `NotImplementedError`)
- Parallel execution
- `CitationRecord` generation / knowledge graph (`grounding` layer)
- LLM-based verification (v0 verification is deterministic Python only)
- Multi-perspective deliberation / debate (v0 is single-pass synthesis)
- Memory compression / eviction (`compress()` is a no-op)
- Embedding-based retrieval
- Full benchmark suite or ablation framework

See [v0-canonical-architecture.md § What is Postponed](../docs/architecture/v0-canonical-architecture.md#10-what-is-postponed-and-why) for rationale.

---

## ASAR-REE Implementation Status

All REE phases (0–9) are **completed**. The architecture is implemented, tested, and documented.

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

### Scientific Validation Campaign (Phases 10–13)

| Phase | Description | Status |
|-------|-------------|--------|
| 10A | Runtime Completion Gate (MaterializedViews, reducer projection, self-model/ignorance behavioral wiring, mechanism influence tests) | completed |
| 10B | Measurement Hardening (ExperimentManifest, RealizedEpistemicGain vector, CognitiveActionOutcome, baselines B0-B4, scenario runner, statistical plan) | completed |
| 11 | Controlled Epistemic Benchmark Campaign (6 scenario families, cross-architecture comparison, batch execution) | completed |
| 12 | Counterfactual Cognitive Policy Study (state forking, CognitiveActionOutcomeDataset, regret analysis, feature importance) | completed |
| 13 | Full Ablation + Scientific Findings (leave-one-out, additive ablation, Pareto frontier, prompt-only controls, hypothesis verdicts) | completed |

### Scientific Campaign Execution

| Campaign | Records | Status |
|----------|---------|--------|
| Holdout benchmarks (30 scenarios × 4 budgets × 3 architectures) | 360 | **executed** |
| Ablation campaign (18 dev scenarios × 9 configs) | 162 | **executed** |
| Counterfactual fork study (60 episodes) | 701 outcomes | **executed** |
| Frozen protocol | — | **filed** |
| Negative findings | — | **documented** |
| Final scientific report | — | **written** |

### Headline Results

- **H-REE hypotheses**: 0 supported, 2 not-supported, 8 inconclusive
- **Bid-value correlation**: r=0.039 (genuine negative finding)
- **Ablation effect sizes**: all 0.00 (flags non-functional — methodological defect)
- **Quality comparison**: invalid (incomparable metrics across architectures)

### Required Next Steps (Priority Order)

1. **Wire ablation flags into operator registration** — `BenchmarkRunner._build_registry()` must conditionally include/exclude operators
2. **Implement ground-truth quality evaluation** — compare system output against `scenario.ground_truth`
3. **Normalize token costs** — use realistic mock costs or live providers
4. **Add all operator types to benchmark** — reason, attack, counterfactual, ontology
5. **Include B3/B4 in holdout campaign**
6. **Run with live LLM provider** for genuine quality/compute comparison
7. **Calibrate self-model from data** before testing H-REE-01
8. **Scale counterfactual study** to 500+ distinct states with all action types
