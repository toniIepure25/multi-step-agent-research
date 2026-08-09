# ASAR-REE Implementation Plan

> Architecture specification: [docs/architecture/ree-architecture.md](../docs/architecture/ree-architecture.md)
> ADRs: [ADR-005, ADR-006](../docs/architecture/decision-log.md)
> Hypotheses: [H-REE-01 through H-REE-10](../docs/research/hypotheses.md)

## Phases

| Phase | Goal | Status |
|-------|------|--------|
| 0 | Forensic baseline, ADRs, config, hypotheses, architecture docs | in progress |
| 1 | Epistemic state + event sourcing + workspace + operator kernel | not started |
| 2 | World model + hypothesis ecology + ignorance + research graph | not started |
| 3 | Ontology evolution + counterfactual lab + active experiment design | not started |
| 4 | Empirical self model + metacognition + calibration | not started |
| 5 | Dissonance tribunal + social epistemology + other model | not started |
| 6 | Epistemic market + full metacognitive control + stopping | not started |
| 7 | Federated memory + consolidation + replay learning | not started |
| 8 | Value model + reflective equilibrium + full integration | not started |
| 9 | Scientific evaluation suite + ablations + release candidate | not started |

## Starting State

- Branch: `feature/asar-ree-v2`
- Base SHA: `c88fa1ce5b4f1925defa325a07cf7a127fbb69a0`
- Base commit: `feat(infra): bootstrap frozen v0 pipeline baseline`
- Tests: 78 passed (v0 baseline)
- Runtime: Python 3.11+ (canonical), running on Python 3.13.5

## Dependency Order

```
P0 → P1 → P2 → P3 → P4 → P5 → P6 → P7 → P8 → P9
```

P0 must complete first. P1 is the substrate. P2-P7 build on P1. P8 integrates. P9 evaluates.

## Key Architectural Decisions

- ADR-005: Scoped invariants — legacy vs REE runtime modes
- ADR-006: Federated memory replaces three-tier model in REE
- EpistemicState is immutable; new states via reducer
- Events are append-only; never overwritten
- Operators never mutate state directly
- Two scheduler levels: heuristic (immediate) + learnable (infrastructure)
