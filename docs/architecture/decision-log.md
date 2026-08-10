# Architecture Decision Log

> See also: [system-overview.md](system-overview.md) · [PROJECT_DOSSIER.md § Invariants](../../PROJECT_DOSSIER.md#10-invariants)

Record all non-trivial architectural decisions here. **Any change to schemas, protocols, layer boundaries, or invariants must have an entry before implementation.** See [AGENTS.md § How to Propose Architecture Changes](../../AGENTS.md#how-to-propose-architecture-changes).

## Format

```
## ADR-NNN: <Title>

**Date:** YYYY-MM-DD
**Status:** proposed | accepted | superseded | deprecated
**Context:** What prompted this decision?
**Options considered:**
1. Option A — pros/cons
2. Option B — pros/cons
**Decision:** What we chose and why.
**Consequences:** What this means for the codebase.
**Invariants affected:** none | list which
```

---

## ADR-001: Layer-Based Architecture

**Date:** 2026-03-16
**Status:** accepted
**Context:** Need a structure that separates concerns cleanly for a multi-step research agent.
**Options considered:**
1. Monolithic agent loop — simple but hard to test, swap, or evaluate individual components
2. Pipeline architecture — clean but too rigid for re-planning loops
3. Layer architecture with orchestrator — flexible, testable, supports re-planning
**Decision:** Layer architecture with a central orchestrator. Eight layers with typed interfaces, swappable independently.
**Consequences:** Requires explicit schema definitions for all inter-layer communication. Adds boilerplate but dramatically improves testability and modularity. Orchestration is the sole router between layers.
**Invariants affected:** Establishes invariants #2 (typed boundaries), #6 (swappable modules), #7 (orchestration-only routing).

## ADR-002: Pydantic for Schema Layer

**Date:** 2026-03-16
**Status:** accepted
**Context:** Need typed, validated data structures for inter-layer communication.
**Options considered:**
1. Plain dataclasses — lightweight but no validation
2. Pydantic v2 — validation, serialization, JSON schema generation
3. Protocol Buffers — strong typing but heavy toolchain, poor Python ergonomics
**Decision:** Pydantic v2. Provides validation, serialization, and JSON schema generation with minimal overhead.
**Consequences:** All schemas live in `schemas/` as Pydantic models. Contributors must use these — no parallel type systems.
**Invariants affected:** Reinforces invariant #2 (typed boundaries).

## ADR-003: Python + uv for Project Management

**Date:** 2026-03-16
**Status:** accepted
**Context:** Need a language and dependency management approach for the prototype.
**Options considered:**
1. Python + pip — universal but dependency resolution is slow and fragile
2. Python + Poetry — good but slower than uv
3. Python + uv — fast, modern, good lockfile support
**Decision:** Python 3.11+ with uv for dependency management.
**Consequences:** `pyproject.toml` is the single source of truth for dependencies. Use `uv sync` and `uv run`.
**Invariants affected:** none.

## ADR-004: Normalize Schema Timestamps to UTC at Validation Boundaries

**Date:** 2026-03-17
**Status:** accepted
**Context:** v0 requires timezone-aware UTC timestamps only, but schema fields accepted naive or non-UTC datetimes as user input. This made defaults UTC-aware while still allowing inconsistent runtime data across artifacts.
**Options considered:**
1. Keep UTC defaults only and rely on contributors to pass valid datetimes — simple, but correctness depends on convention and naive timestamps can leak into artifacts.
2. Validate every timestamp field at the schema boundary and normalize aware inputs to UTC — slightly more boilerplate, but makes timestamp handling deterministic and inspectable.
**Decision:** Add a shared schema timestamp type that rejects naive datetimes and normalizes aware datetimes to UTC for all typed timestamp fields.
**Consequences:** All serialized artifacts store timestamps consistently in UTC. Callers must provide timezone-aware datetimes when overriding timestamps. Existing UTC defaults continue to work unchanged.
**Invariants affected:** Reinforces invariant #2 (typed boundaries) and invariant #3 (reproducible experiments).

## ADR-005: ASAR-REE Architecture — Scoped Invariants and Migration

**Date:** 2026-08-09
**Status:** accepted
**Context:** ASAR-REE (Reflexive Epistemic Ecology) replaces the fixed sequential pipeline with an event-sourced, metacognitively controlled architecture. The fundamental unit becomes an epistemic state transition loop: `E_t -> action -> observation -> E_(t+1)`. This conflicts with invariant #7 ("orchestration is the only router") and the frozen canonical layer list, because REE uses a dynamic epistemic controller selecting from swappable cognitive operators rather than routing through a central orchestrator.

**Options considered:**
1. Modify existing invariants globally — risks breaking the working v0 baseline and makes the invariants incoherent (they would try to serve two contradictory architectures simultaneously).
2. Scope invariants by runtime — each invariant specifies whether it applies to `legacy`, `ree`, or `both`. The legacy v0 runtime continues to enforce its invariants exactly as before. REE defines equivalent invariants suited to its architecture. Both runtimes coexist via a config flag.

**Decision:** Option 2 — scope invariants by runtime. Specifically:

- Invariant #7 ("orchestration-only routing") is scoped to `legacy`. The REE equivalent is: *"Operators return typed `OperatorResult`s; only the state reducer mutates `EpistemicState`; the epistemic controller selects operations. No operator directly imports or invokes another operator."*
- Invariants #1 (grounded output), #2 (typed boundaries), #3 (reproducible experiments), #4 (generation ≠ verification), #6 (swappable modules) apply to `both` runtimes. REE strengthens #1 and #3 via event sourcing and provenance graphs.
- The canonical 8-layer names remain valid for the legacy runtime. REE introduces additional modules (`epistemic`, `operators`, `metacognition`, `social`, `world_model`, `ontology`, `self_model`, `value_model`, `ignorance`, `memory_federation`) without renaming existing layers.
- A `runtime` configuration key in `config/pipeline.toml` selects which runtime is active. Default: `legacy`.
- `SequentialOrchestrator` moves to `asar/orchestration/legacy/` with backward-compatible re-exports.
- Legacy components are never deleted until: (a) REE reaches functional parity, (b) tests prove migration safety, (c) an ADR records the retirement decision, (d) historical experiments remain reproducible.

**Consequences:** The codebase supports two runtime modes. All new REE code lives in new modules; existing v0 code is not modified. Test suites run both runtimes. The `schemas/` directory gains a `ree/` subdirectory for REE-specific schemas; existing schemas are preserved unchanged.

**Invariants affected:** #7 (scoped to legacy; REE equivalent defined). Adds REE-specific invariants.

## ADR-006: Federated Memory Replaces Three-Tier Memory Model in REE

**Date:** 2026-08-09
**Status:** accepted
**Context:** The legacy memory model defines three tiers: working, compressed, evicted. REE requires functionally distinct memory stores: working, episodic, semantic/belief, procedural, self-model, prospective, and ignorance — each with different access patterns, provenance requirements, and lifecycle semantics (consolidation, reconsolidation, forgetting).

**Options considered:**
1. Extend the three-tier model with sub-tiers — conceptually simpler but forces unrelated concerns (e.g., procedural strategy memory and episodic event memory) into the same abstraction.
2. Federate memory into distinct functional stores — each store has its own protocol, schema, and lifecycle. The working/compressed/evicted tier concept can still exist within individual stores if needed.

**Decision:** Option 2 — federated memory for REE. The legacy `MemoryProtocol` with `store()/retrieve()/compress()` continues to work for the v0 runtime. REE defines a `FederatedMemoryProtocol` with typed access to each functional store. RAG/vector retrieval may serve as a backend for individual stores but is not the architectural foundation.

**Consequences:** Invariant #5 is scoped: legacy retains "working/compressed/evicted always queryable"; REE uses "every record's functional store and temporal state are always queryable". Memory consolidation, reconsolidation, and forgetting become explicit operations with event-sourced provenance.

**Invariants affected:** #5 (scoped to legacy; REE equivalent defined).

## ADR-007: B1 Fixed Sequence as REE-Minimal-Empirical Baseline

**Date:** 2026-08-10
**Status:** accepted
**Context:** Campaign V3 (Phases 17-20) systematically decomposed the winning B1 strategy and tested temporal complementarity, cognitive motifs, hierarchical control, and ecology cross-architecture effects. Results demonstrate that B1_extended (retrieve->gen_hyp->retrieve->gen_hyp->reason->retrieve->reason) achieves the highest quality (0.672) with 3500 tokens, while Full REE achieves 0.324 at ~5000 tokens. The Epistemic Market is anti-calibrated (attack crowding, no prerequisite checking). Cognitive operations exhibit strong compositional complementarity (gen_hyp+reason: +0.228 super-additive). Hierarchical cognitive options match but do not exceed B1_extended.

**Options considered:**
1. Fix the Epistemic Market with calibrated bids — addresses scheduling failure but the market architecture may be fundamentally mismatched to sequence-structured cognition.
2. Replace market with cognitive options — hierarchical control via EXPLORE/DISCRIMINATE/CONSOLIDATE motifs. Matches B1_extended quality but adds complexity without measurable benefit.
3. Adopt B1_extended as REE-Minimal-Empirical — the simplest architecture that retains all empirically supported mechanisms. No market, no self-model, no stopping policy.

**Decision:** Option 3 — adopt B1_extended as the empirical baseline for REE. Future adaptive controllers must demonstrate improvement over this baseline on diverse task families, not merely match it. The market is classified HARMFUL. Self-model and stopping policy are classified NO_MEASURED_BENEFIT. Hypothesis generation and reasoning are classified CORE_SUPPORTED.

**Consequences:** The minimal effective REE configuration requires only evidence retrieval, hypothesis generation (at least 2), and consistency reasoning in a fixed temporal order. Persistent EpistemicState, market scheduling, self-model, and stopping policy are not required. Attack is conditionally useful late in episodes.

**Invariants affected:** None changed. REE modularity (swappable components) is preserved — B1_extended is a specific operator sequence, not a change to the protocol system.
