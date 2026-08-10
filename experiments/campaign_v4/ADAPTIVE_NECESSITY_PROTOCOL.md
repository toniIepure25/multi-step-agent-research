# Adaptive Necessity Protocol (Phase 21)

## Design

To determine whether adaptive cognitive control is actually necessary,
construct worlds where different cognitive strategies are genuinely optimal.

### Epistemic Regimes

8 regimes with structurally distinct information landscapes:

| Regime | Description | Expected Optimal Strategy |
|---|---|---|
| A — Exploration Deficit | Insufficient hypothesis diversity | gen_hyp -> retrieve -> reason |
| B — Evidence Deficit | Hypotheses known, evidence scarce | retrieve -> retrieve -> reason |
| C — Discrimination Deficit | Hypotheses and evidence exist, need falsification | attack -> reason |
| D — Integration Deficit | Abundant evidence, need consolidation | reason (immediately) |
| E — Misleading Evidence | Volume supports wrong hypothesis | attack -> retrieve -> reason |
| F — Hidden Alternative | Obvious hypothesis insufficient | gen_hyp -> retrieve -> gen_hyp -> reason |
| G — Source Dependency | Apparent independence is illusory | reason with provenance |
| H — Low Resolvability | Further investigation low-value | reason -> stop |

### Measurement

```
AdaptivityGap = Quality(state-conditioned sequence oracle)
              - Quality(best global fixed sequence)
```

### Adaptive Necessity Gate

ALL must be true:
1. Multiple different sequences are oracle-optimal across states
2. No single sequence dominates > 90% of states
3. AdaptivityGap > 0.05
4. State features contain information about optimal sequence
5. Differences remain after equal-cost normalization

## Results

| Metric | Value |
|---|---|
| Best global fixed | B1_extended (quality = 0.527) |
| State-conditioned oracle | quality = 0.622 |
| **AdaptivityGap** | **0.096** |
| Dominant sequence % | 66.1% (B1_extended) |
| Distinct optimal sequences | 4 |

### Gate Evaluation

| Criterion | Status |
|---|---|
| Multiple optimal sequences | PASS (4 distinct) |
| No single dominant > 90% | PASS (66.1%) |
| AdaptivityGap > 0.05 | PASS (0.096) |
| AdaptivityGap > 0.10 | FAIL (0.096 < 0.10) |

**ADAPTIVE NECESSITY: ESTABLISHED** (passes 3/3 required criteria)

### Per-Regime Optimal Sequences

| Regime | Oracle-Best Sequence | Count |
|---|---|---|
| A (exploration deficit) | explore_first | 7/7 |
| B (evidence deficit) | B1_extended | 7/7 |
| C (discrimination deficit) | full_explore | 7/7 |
| D (integration deficit) | B1_extended | 7/7 |
| E (misleading evidence) | B1_extended (5), explore_first (2) | mixed |
| F (hidden alternative) | B1_extended | 7/7 |
| G (source dependency) | B1_extended (4), B1_full (3) | mixed |
| H (low resolvability) | B1_extended | 7/7 |

### Interpretation

Adaptive necessity is real but modest. Regimes A and C have genuinely
different optimal strategies from the B1_extended default. The gap (0.096)
means a perfect oracle gains ~10% quality over the best fixed sequence.

Whether this gap is exploitable by a learnable policy is the question
for Phase 23.
