# Cognitive Motifs (Phase 18.6)

## Objective

Identify recurrent useful multi-step cognitive patterns from Phase 18 data.

## Method

Analyze sequence complementarity, order effects, and B1 decomposition data
to identify stable motifs — sequences that consistently produce super-additive
quality gains.

## Identified Motifs

### EXPLORE: retrieve -> generate_hypothesis

**Evidence**: B1 decomposition shows removing either retrieve or hypothesis
causes -0.14 quality drop. The pair is the foundational building block.

**When useful**: Always. This is the minimum viable cognitive sequence.
Quality goes from 0.038 (retrieve-only) to 0.376 when hypothesis is added.

**Complementarity**: +0.188 (super-additive)

### DISCRIMINATE: retrieve -> generate_hypothesis -> reason

**Evidence**: Complementarity analysis shows this 3-step sequence has +0.228
super-additivity. Reason integrates evidence with hypotheses, enabling
consistency scoring.

**When useful**: After initial evidence collection. This is the core
quality-producing motif.

**Complementarity**: +0.228 (strongly super-additive)

### CONSOLIDATE: reason (on existing hypotheses and evidence)

**Evidence**: B1 decomposition shows removing reason causes the largest
single-step quality drop (-0.230). But reason alone (without hypotheses)
produces near-zero quality.

**When useful**: ONLY after hypotheses and evidence exist. Prerequisite:
hypothesis_count >= 1 AND evidence_count >= 1.

**Complementarity**: +0.163 when paired with gen_hyp

### INVESTIGATE: attack_hypothesis -> reason

**Evidence**: Phase 18.5 shows attack adds +0.030 over reason alone when
hypotheses exist. The pair is marginally useful.

**When useful**: Late in episode, with 2+ hypotheses and evidence.
The attack identifies ignorance; reason integrates it.

**Complementarity**: +0.030 (weakly super-additive, state-dependent)

## Motifs NOT Supported

### ESCAPE: ontology_revision -> generate_hypothesis

Not implemented in the semantic simulator. INCONCLUSIVE.

### RESOLVE_UNKNOWN: ignorance-driven retrieve -> reason

Not separately measurable. Ignorance identification happens within attack,
and its downstream effect on targeted retrieval is not currently modeled.
INCONCLUSIVE.

### Attack-first patterns

attack -> anything on empty state = 0.000. Not a viable motif without
prerequisite conditions.

## Motif Composition in Winning Sequences

| Sequence | Motifs Used | Quality |
|---|---|---|
| B1_full | EXPLORE + EXPLORE + CONSOLIDATE | 0.573 |
| B1_extended | EXPLORE + DISCRIMINATE + CONSOLIDATE | **0.630** |
| B1_ret_hyp_ret_hyp_atk_reason | EXPLORE + EXPLORE + INVESTIGATE | 0.603 |
| attack_late_rich_state | EXPLORE + EXPLORE + CONSOLIDATE + INVESTIGATE | 0.603 |

## Conclusions

1. **EXPLORE (ret->hyp) is the foundational motif**. All quality > 0.3 requires it.
2. **DISCRIMINATE (ret->hyp->reason) is the core quality-producing motif**.
   Adding reason to EXPLORE is the single highest-value addition.
3. **CONSOLIDATE (reason) is critical but prerequisite-dependent**.
4. **INVESTIGATE (atk->reason) is conditionally useful**,
   adding ~8% quality when rich state exists.
5. **Motifs compose well**: B1_extended = EXPLORE + DISCRIMINATE + CONSOLIDATE
   achieves 0.630, the highest quality observed.
6. **The winning strategy is: explore first, then discriminate, then consolidate**.
   This is the empirically optimal cognitive trajectory.
