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
| 4 | `SimplePlanner`: single LLM call -> `ResearchPlan` | `planning` | `common`, schemas | completed |
| 5 | `WebSearchExecutor`: search API -> `list[EvidenceItem]` | `execution` | `common`, schemas | completed |
| 6 | `SimpleSynthesizer`: single LLM call over all evidence -> `DecisionPacket` with `Claim`s | `deliberation` | schemas | completed |
| 7 | `EvidenceChecker`: deterministic verification, no LLM -> `VerificationResult` | `verification` | schemas | completed |
| 8 | `ExperimentLogger`: build `ExperimentRecord`, compute metrics, write to disk | `evaluation` | schemas | completed |
| 9 | `SequentialOrchestrator`: wire all layers -> `ResearchOutput` | `orchestration` | steps 3-8 | completed |
| 10 | Integration test: end-to-end on one Tier 1 question (mocked LLM/search) | tests | step 9 | completed |
| 11 | Live run on one Tier 1 question | — | step 10 | not started |
| 12 | 5 Tier 1 benchmark questions with ground-truth rubrics | `evaluation` | — | not started |
| 13 | Baseline metrics: run pipeline on benchmarks, record results | `evaluation` | steps 11-12 | not started |

## ASAR-REE Implementation Status

All REE phases (0-9) and scientific validation (10-20) are **completed**.

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
| 16 | Final Scientific Verdicts (Campaign V2) | completed |
| 17 | Isolate What Works — B1 decomposition, ecology replication | completed |
| 18 | Temporal Complementarity — sequence value, motifs, order | completed |
| 19 | Hierarchical Metacognitive Control | completed |
| 20 | Campaign V3 Confirmation on fresh locked test | completed |

### Scientific Campaign V1 (SHA: 120a576) — Frozen

Established that content-independent mock operators with substring matching
produce non-discriminative quality. All architectures identical at 33% GT match.
Preserved as immutable negative baseline.

### Scientific Campaign V2 (SHA: c94e9a9) — Frozen

| Dataset | Records | Families | Architectures |
|---------|---------|----------|---------------|
| Dev holdout | 150 | 5 | B0, B1, REE |
| Dev ablation | 350 | 5 | 7 ablation configs |
| Dev Pareto | 600 | 5 | 3 x 4 budgets |
| Validation | 75 | 5 | 3 |
| Locked test | 75 | 5 | 3 |
| Counterfactual | 2000 | 5 | 5 actions x 500 states |
| Market comparison | 200 | 5 | 4 market variants |
| **Total** | **3450** | | |

### Scientific Campaign V3 (Phases 17-20)

| Dataset | Records | Families | Architectures |
|---------|---------|----------|---------------|
| Dev B1 decomposition | 500 | 5 | 10 B1 variants |
| Dev ecology cross-arch | 300 | 5 | 6 configurations |
| Dev sequence complementarity | 300 | 5 | 6 sequence pairs |
| Dev attack state-dependence | 300 | 5 | 6 conditions |
| Dev hierarchical comparison | 350 | 5 | 7 architectures |
| Validation | 175 | 5 | 7 |
| Locked test (one-shot) | 175 | 5 | 7 |
| **Total** | **~2100** | | |

### Campaign V3 Headline Results

| Finding | Value | Interpretation |
|---------|-------|----------------|
| B1_extended (locked) | **0.672** | Best overall quality |
| Hierarchical options (locked) | 0.672 | Matches but does not exceed B1_extended |
| B1_full (locked) | 0.594 | Strong fixed strategy |
| Full REE (locked) | 0.324 | Dramatically underperforms fixed sequences |
| gen_hyp+reason complementarity | +0.228 | Strongly super-additive |
| Forward vs reversed B1 | +0.223 | Order matters |
| Attack early (no hyps) | 0.000 | Completely useless |
| Attack late (rich state) | 0.603 | Conditionally valuable |

### Hypothesis Verdicts (Canonical IDs — see HYPOTHESIS_CANONICAL_MAPPING.md)

| Hypothesis | V2 Verdict | V3 Verdict |
|---|---|---|
| H-REE-01: Self-model | INCONCLUSIVE | INCONCLUSIVE |
| H-REE-02: Ignorance | PARTIALLY_SUPPORTED | PARTIALLY_SUPPORTED |
| H-REE-03: Sealed tribunal | INCONCLUSIVE | INCONCLUSIVE |
| H-REE-04: Ontology branching | INCONCLUSIVE | INCONCLUSIVE |
| H-REE-05: Epistemic Market | NOT_SUPPORTED | NOT_SUPPORTED |
| H-REE-06: Provenance clustering | INCONCLUSIVE | INCONCLUSIVE |
| H-REE-07: Counterfactual reasoning | INCONCLUSIVE | INCONCLUSIVE |
| H-REE-08: Offline consolidation | INCONCLUSIVE | INCONCLUSIVE |
| H-REE-09: Full REE > additive sum | NOT_SUPPORTED | NOT_SUPPORTED |
| H-REE-10: Hypothesis ecology | SUPPORTED | PARTIALLY_SUPPORTED (revised) |
| H-REE-11: Temporal complementarity | — | **SUPPORTED** |
| H-REE-12: Cross-architecture ecology | — | NOT_SUPPORTED |
| H-REE-13: Greedy control failure | — | **SUPPORTED** |

### Answers to Primary Questions

1. **Why did B1 beat Full REE?** B1 guarantees the gen_hyp->reason synergy. Market over-selects attack (46%), under-selects reason.
2. **Is hypothesis ecology independently useful?** No. B1 = B1+ecology. The V2 d~1.4 effect reflects "enable hypothesis generation," not persistent ecology.
3. **Is ignorance useful conditionally?** Yes, marginally (+8% when hypotheses exist). But inseparable from attack.
4. **Why does attack crowd the market?** Market has no prerequisite checking. Attack bids high on states where attack = 0.
5. **Is attack harmful or mistimed?** Mistimed. Useless early, marginally useful mid, best late with rich state.
6. **Are cognitive operations non-additive?** Yes. gen_hyp + reason complementarity = +0.228.
7. **Does action ordering matter?** Yes, moderately. Forward vs reversed: +0.223. Composition > ordering.
8. **Can cognitive motifs be identified?** Yes: EXPLORE (ret->hyp), DISCRIMINATE (ret->hyp->reason), CONSOLIDATE (reason).
9. **Does sequence prediction outperform primitive prediction?** Not directly tested (controller converges to single trajectory).
10. **Does hierarchical control beat best fixed?** No. Matches (0.672 = 0.672) but doesn't exceed.
11. **Smallest empirically supported architecture?** B1_extended: ret->hyp->ret->hyp->reason->ret->reason.
12. **Is live validation justified?** Conditionally. Fixed sequence result is strong. LLM-in-the-loop would test generalization.

### Next Steps (Future Work)

1. **LLM-in-the-loop experiment**: Replace scripted operators with actual LLM calls while keeping simulator ground truth
2. **Expand task diversity**: Add families that require genuinely different strategies to test adaptive advantage
3. **Wire remaining ablations causally**: self_model, stopping_policy need controller integration
4. **Test adaptive advantage on diverse tasks**: Current families are too similar for hierarchical control to show advantage
5. **Sequence-level value prediction**: Requires sufficient trajectory variance to build predictive models
