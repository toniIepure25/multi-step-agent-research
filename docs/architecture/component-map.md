# Component Map

> Parent: [system-overview.md](system-overview.md)
> See also: [dataflow.md](dataflow.md) · [PROJECT_DOSSIER.md § System Layers](../../PROJECT_DOSSIER.md#6-system-layers)

Where code lives, what it does, and what schemas flow through it.

## Source Modules (`asar/`)

| Module | Path | Responsibility | Protocol |
|--------|------|---------------|----------|
| **core** | `asar/core/` | Protocols, base types, exceptions — no implementations | — |
| **common** | `asar/common/` | Config loading, logging, ID generation — no layer imports | — |
| **planning** | `asar/planning/` | Goal → `ResearchPlan` with `PlanStep`s | `PlannerProtocol` |
| **execution** | `asar/execution/` | `TaskPacket` → `EvidenceItem`(s) — stateless | `ExecutorProtocol` |
| **memory** | `asar/memory/` | Store, retrieve, compress typed artifacts | `MemoryProtocol` |
| **deliberation** | `asar/deliberation/` | `EvidenceItem`s → `DecisionPacket` with claims, conflicts | `DeliberationProtocol` |
| **grounding** | `asar/grounding/` | `EvidenceItem` → `CitationRecord` + graph triples | `GroundingProtocol` |
| **verification** | `asar/verification/` | `DecisionPacket` + `list[EvidenceItem]` → `VerificationResult`. v0: deterministic checks. Phase 2: also accepts `list[CitationRecord]`. | `VerificationProtocol` |
| **evaluation** | `asar/evaluation/` | Benchmarks, metrics → `ExperimentRecord` | `EvaluationProtocol` |
| **orchestration** | `asar/orchestration/` | Lifecycle, dispatch, inter-layer routing | — (coordinator) |

## Schemas (`schemas/`)

| Schema | File | Produced by | Consumed by |
|--------|------|------------|-------------|
| `ResearchPlan`, `PlanStep` | `schemas/research_plan.py` | planning | orchestration |
| `TaskPacket`, `TaskStatus` | `schemas/task_packet.py` | orchestration | execution |
| `EvidenceItem`, `SourceMetadata` | `schemas/evidence_item.py` | execution | memory, deliberation, verification |
| `CitationRecord` | `schemas/citation_record.py` | grounding | verification | Phase 2 — not used in v0 |
| `DecisionPacket`, `Claim` | `schemas/decision_packet.py` | deliberation | verification |
| `VerificationResult`, `ClaimVerification` | `schemas/verification_result.py` | verification | orchestration (output) |
| `ResearchOutput` | `schemas/research_output.py` | orchestration | (disk artifact) |
| `ExperimentRecord` | `schemas/experiment_record.py` | evaluation | evaluation (internal) |

## Config (`config/`)

| File | Purpose | Referenced by |
|------|---------|--------------|
| `config/project.toml` | Project metadata, version | `asar/common/` |
| `config/models.toml` | LLM provider settings, per-layer model routing | `asar/common/`, orchestration |
| `config/pipeline.toml` | Layer enable/disable toggles | orchestration |
| `config/experiments.toml` | Default experiment parameters | evaluation |

## REE Modules (`asar/` — Reflexive Epistemic Ecology)

| Module | Path | Responsibility |
|--------|------|---------------|
| **epistemic** | `asar/epistemic/` | Event store, state reducer, workspace manager, state diffing |
| **operators** | `asar/operators/` | Cognitive operators (retrieve, reason, synthesize, stop, hypothesis, counterfactual) + registry |
| **metacognition** | `asar/metacognition/` | Epistemic market (bid evaluation), controller (cognitive loop), stopping policy, trajectory dataset |
| **world_model** | `asar/world_model/` | Hypothesis graph, research graph, belief tracker |
| **ignorance** | `asar/ignorance/` | Ignorance ledger (known unknowns tracking + prioritisation) |
| **ontology** | `asar/ontology/` | Ontology forge (frame management), counterfactual lab, experiment designer |
| **self_model** | `asar/self_model/` | Episode tracker, calibration analyser, capability predictor |
| **social** | `asar/social/` | Dissonance tribunal, evidence independence analyser, stakeholder registry |
| **memory_federation** | `asar/memory_federation/` | Federated memory (7 stores), memory consolidation |
| **value_model** | `asar/value_model/` | Value registry (principles), reflective equilibrium |

## REE Schemas (`schemas/ree/`)

| Schema | File | Used by |
|--------|------|---------|
| `EpistemicState`, `BudgetState`, `ProcessState`, `WorkspaceState`, `WorkspaceSlot`, `ResourceCost` | `schemas/ree/epistemic_state.py` | epistemic, metacognition, operators |
| `EpistemicEvent`, `EpistemicAction`, `EpistemicActionBid`, `OperatorResult`, `OperatorOutcome` | `schemas/ree/epistemic_event.py` | epistemic, operators, metacognition |
| `Hypothesis`, `Assumption`, `Prediction`, `Falsifier`, `Contradiction`, `BeliefSnapshot` | `schemas/ree/world_model.py` | world_model |
| `IgnoranceItem`, `IgnoranceType`, `IgnoranceStatus` | `schemas/ree/ignorance.py` | ignorance |
| `OntologyFrame`, `CounterfactualWorld`, `SensitivityResult`, `ExperimentCandidate` | `schemas/ree/ontology.py` | ontology |
| `EpisodeRecord`, `CapabilityEstimate`, `CalibrationPoint` | `schemas/ree/self_model.py` | self_model |
| `TribunalRole`, `TribunalSubmission`, `TribunalVerdict`, `StakeholderModel`, `EvidenceProvenance` | `schemas/ree/social.py` | social |
| `MemoryStore`, `MemoryRecord`, `MemoryRecordStatus`, `ConsolidationEvent` | `schemas/ree/memory.py` | memory_federation |
| `ValuePrinciple`, `NormConflict` | `schemas/ree/value_model.py` | value_model |

## Import Rules

```
orchestration
  ├── imports: planning, execution, deliberation, memory, grounding, verification, evaluation
  ├── imports: core, common
  └── uses schemas: all

planning, execution, deliberation, memory, grounding, verification, evaluation
  ├── imports: core, common
  ├── uses schemas: only those in their contract (see table above)
  └── DO NOT import each other — routing goes through orchestration

core
  ├── imports: nothing from asar/
  └── defines: protocols, base types

common
  ├── imports: nothing from asar/ (except possibly core)
  └── provides: config loading, logging, ID generation
```

This import discipline enforces the invariant that **orchestration is the only router**.
