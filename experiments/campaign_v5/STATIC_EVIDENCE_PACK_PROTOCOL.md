# Phase 27 — Static Real-Evidence Pack Protocol

**Campaign:** V5
**Status:** PACKS GENERATED — LLM execution blocked
**Date:** 2026-08-10

## Purpose

Static evidence packs provide an intermediate evaluation layer between:
- **Synthetic simulator** (perfect ground truth, weak realism)
- **Live web search** (strong realism, poor control)

Each pack uses real-world research questions with curated evidence items and evaluator-only ground truth.

## Pack Statistics

| Metric | Value |
|--------|-------|
| Total packs | 30 |
| Domains | 6 |
| Packs per domain | 5 |

### Domains

| Domain | Pack IDs | Fully specified |
|--------|----------|----------------|
| Cognitive Science | cog_01 through cog_05 | Yes (rich evidence) |
| AI Research | ai_01 through ai_05 | Yes (rich evidence) |
| Biomedical | bio_01 through bio_05 | bio_01 rich; bio_02-05 template |
| Economics | econ_01 through econ_05 | econ_01 rich; econ_02-05 template |
| History of Science | hist_01 through hist_05 | hist_01 rich; hist_02-05 template |
| Social Science | soc_01 through soc_05 | soc_01 rich; soc_02-05 template |

### Evidence Structure Per Pack

Each pack contains evidence items with roles:

| Role | Description | Typical count |
|------|-------------|---------------|
| supporting | Supports the correct/best conclusion | 1-3 |
| contradictory | Contradicts the main claim | 1-2 |
| dependent | Derived from/copies another source | 0-1 |
| irrelevant | Plausible but non-discriminating | 0-1 |
| weak | Low reliability or ambiguous | 0-1 |
| decisive | Highly discriminating | 1-2 |

### Ground Truth Schema

Each pack has evaluator-only ground truth:

```
acceptable_hypotheses: list[str]   # All defensible positions
best_hypothesis: str               # Best-supported conclusion
verdict: SUPPORTED | REFUTED | MIXED | UNDERDETERMINED
support_relations: dict            # Evidence → claim support
contradiction_relations: dict      # Evidence → claim contradiction
source_dependencies: list          # Which sources are dependent
critical_assumptions: list         # What must be true
decisive_evidence: list            # Items that should change conclusions
known_ambiguity: list              # Where genuine uncertainty exists
```

## Verdict Distribution

| Verdict | Count | Proportion |
|---------|-------|------------|
| MIXED | 20 | 67% |
| SUPPORTED | 6 | 20% |
| REFUTED | 2 | 7% |
| UNDERDETERMINED | 2 | 7% |

## Experimental Conditions

| Condition | Sequence | Description |
|-----------|----------|-------------|
| direct | retrieve_all → synthesize | Dump all evidence, synthesize once |
| reflection | retrieve_all → synthesize → critique → revise | Add self-critique loop |
| B1_extended | R → GH → R → GH → Reason → R → Reason | Best V4 fixed sequence |
| FULL_EXPLORE | GH → R → GH → R → GH → R → Reason → R → Reason | Explore-heavy sequence |
| greedy_primitive | R → R → R → R → Reason | Retrieve-heavy baseline |

## Metrics

| Metric | Weight | Definition |
|--------|--------|-----------|
| claim_correctness | 0.25 | Best hypothesis identified |
| evidence_support | 0.15 | Retrieved evidence cited |
| decisive_coverage | 0.20 | Decisive evidence found and used |
| contradiction_handling | 0.15 | Contradictions acknowledged |
| calibration | 0.15 | Appropriate uncertainty expressed |
| source_independence | 0.10 | Source dependencies noted |

## Sequence Analysis Questions

1. Does hypothesis generation before targeted evidence search improve outcomes?
2. Does reasoning too early cause lock-in?
3. Does attack become useful only after a hypothesis is sufficiently specified?
4. Are repeated retrieval operations redundant?
5. Does operation order matter on actual documents?

## Counterfactual Evaluation Protocol

Where feasible, fork identical intermediate states:
- Same evidence retrieved, same hypotheses generated
- Branch into: retrieve / hypothesize / reason / attack
- Compare downstream quality

This gives real-data analogues of:
```
EpistemicState × CognitiveOperation → RealizedGain
```

## Current Status

- **Evidence packs:** 30 generated, saved as JSON
- **Protocol:** Fully specified
- **Scoring:** Implemented
- **LLM execution:** BLOCKED (no model server)

Execute `run_phase27.py` once a model server is available.
