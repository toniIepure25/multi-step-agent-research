# Campaign V3 Final Report

```
CAMPAIGN: V3
BRANCH: feature/asar-ree-v2
V2 FROZEN AT: c94e9a9
V3 BASE SEED: 31415
WORLDS: dev=50, validation=25, locked_test=25
FAMILIES: hypothesis_ecology, false_majority, ignorance_discovery,
          stopping_quality, source_duplication
```

## Primary Scientific Question

> WHY DOES A FIXED COGNITIVE SEQUENCE OUTPERFORM GREEDY ADAPTIVE
> METACOGNITIVE CONTROL?

## Answer

A fixed cognitive sequence outperforms greedy adaptive control because:

1. **Cognitive operations have strong compositional complementarity**.
   generate_hypothesis + reason produces super-additive quality (+0.228)
   because reasoning requires hypotheses to evaluate and hypotheses
   require reasoning to integrate with evidence.

2. **The greedy market evaluates operations independently**, which
   structurally prevents it from capturing the gen_hyp→reason synergy.
   It selects the operation with the highest immediate bid, not the
   sequence with the highest downstream value.

3. **The market over-selects attack**, which has zero value on early states
   (46% of selections, 0.000 quality contribution). Attack requires
   prerequisite conditions (multiple hypotheses + evidence) that the
   market does not check.

4. **B1's fixed sequence guarantees the synergistic combination**:
   retrieve→hypothesize→retrieve→hypothesize→reason always includes
   the critical gen_hyp→reason pairing, while the market may never
   schedule this combination.

## V3 Locked Test Results

| Condition | Mean Quality | Std | N |
|---|---|---|---|
| B1_extended | **0.672** | 0.109 | 25 |
| hierarchical_options | **0.672** | 0.109 | 25 |
| B1_full | 0.594 | 0.216 | 25 |
| round_robin_ree | 0.438 | 0.250 | 25 |
| full_ree | 0.324 | 0.168 | 25 |
| B0_direct | 0.289 | 0.223 | 25 |
| full_ree_no_ecology | 0.038 | 0.016 | 25 |

## Confirmatory Claims

### C1 — Hypothesis Ecology: PARTIALLY_SUPPORTED

Hypothesis generation is critical (quality drops from 0.594 to 0.038 without it).
But the "persistent ecology" mechanism specifically provides no measured benefit
above simply generating multiple hypotheses in sequence. B1 = B1+ecology.

**Effect on locked test**: Full REE with ecology (0.324) vs without (0.038) = d≈1.4.
This replicates V2. But B1 (0.594) without persistent ecology exceeds Full REE
with ecology (0.324).

### C2 — Temporal Complementarity: SUPPORTED

Cognitive operations exhibit strong non-additive downstream value:
- gen_hyp + reason complementarity: +0.228 (dev, N=50)
- ret+hyp+reason vs ret+ret+reason: +0.310 (dev, N=50)
- Forward vs reversed B1: +0.223 (dev, N=50)

Sequence value is not the sum of primitive values.

### C3 — Greedy-Control Failure: SUPPORTED

Primitive greedy scheduling (Full REE: 0.324) dramatically underperforms
fixed sequences (B1_full: 0.594, B1_extended: 0.672) because the market
evaluates operations independently and cannot capture temporal structure.

The mechanism of failure: attack crowding (46% of selections) on states
where attack has zero value, combined with under-selection of reason
(the most valuable terminal operation).

### C4 — Hierarchical Control: PARTIALLY_SUPPORTED

Hierarchical control matches the best fixed strategy (0.672 = 0.672) and
dramatically outperforms primitive greedy (0.672 vs 0.324). But it does NOT
demonstrate adaptive advantage over a well-chosen fixed sequence. Only 2
distinct trajectories observed in 60 trials.

### C5 — Minimal Architecture: SUPPORTED

B1_extended (retrieve→gen_hyp→retrieve→gen_hyp→reason→retrieve→reason) achieves
the highest quality (0.672) with 3500 tokens. This is the REE-Minimal-Empirical
configuration. It requires no market, no self-model, no stopping policy, no
persistent state management.

Full REE is Pareto-dominated: lower quality (0.324) at higher cost (~5000 tokens).

## Hypothesis Verdicts (Canonical IDs)

| ID | Verdict | Evidence |
|---|---|---|
| H-REE-01 | INCONCLUSIVE | Self-model ablation remains non-causal |
| H-REE-02 | PARTIALLY_SUPPORTED | Ignorance via attack adds ~8% quality conditionally |
| H-REE-03 | INCONCLUSIVE | Not in benchmark |
| H-REE-04 | INCONCLUSIVE | Not in benchmark |
| H-REE-05 | **NOT_SUPPORTED** | Market is anti-calibrated; heuristic < round-robin < fixed |
| H-REE-06 | INCONCLUSIVE | Not causally ablated |
| H-REE-07 | INCONCLUSIVE | Not in benchmark |
| H-REE-08 | INCONCLUSIVE | Not in benchmark |
| H-REE-09 | **NOT_SUPPORTED** | Full REE (0.324) < B1 (0.594) on locked test |
| H-REE-10 | **PARTIALLY_SUPPORTED** | Hypothesis generation is critical, but persistent ecology is not |
| H-REE-11 | **SUPPORTED** | Complementarity = +0.228, order effects = +0.223 |
| H-REE-12 | **NOT_SUPPORTED** | Ecology flag has no effect on B1 |
| H-REE-13 | **SUPPORTED** | Market cannot capture gen_hyp→reason synergy |

## Answers to Final Questions

1. **Why did B1 beat Full REE?**
   B1 guarantees the gen_hyp→reason synergy. The market over-selects attack
   (46%, zero-value on early states) and under-selects reason.

2. **Is hypothesis ecology independently useful or only necessary inside Full REE?**
   It is necessary inside Full REE (without it: 0.038). It is not independently
   useful — B1 already generates hypotheses and gains nothing from the ecology flag.

3. **Is ignorance useful conditionally?**
   Yes, marginally (+8% quality when hypotheses exist). But ignorance is only
   produced by attack, which has strong prerequisite conditions.

4. **Why does attack crowd the heuristic market?**
   Attack's bid does not decay based on state prerequisites. The market has
   no mechanism to evaluate whether an operation's prerequisites are met.

5. **Is attack actually harmful, or merely mistimed?**
   Mistimed. Attack is useless on early states (0.000) but marginally useful
   late (+0.030). With rich state and late timing: best overall (0.603).

6. **Are cognitive operations non-additive?**
   Yes. gen_hyp + reason complementarity = +0.228 (strongly super-additive).

7. **Does action ordering matter?**
   Yes, moderately. Forward vs reversed B1: +0.223. But composition effects
   (what operations) dominate over ordering effects (what order).

8. **Can useful multi-step cognitive motifs be identified?**
   Yes: EXPLORE (ret→hyp), DISCRIMINATE (ret→hyp→reason), CONSOLIDATE (reason).
   The optimal trajectory is: explore first, then discriminate, then consolidate.

9. **Does sequence-level value prediction outperform primitive-action prediction?**
   Not directly tested because the hierarchical controller converges to a single
   trajectory, preventing meaningful variance for modeling. Primitive prediction
   remains weak (r=0.137 from V2).

10. **Does hierarchical metacognitive control beat the best fixed strategy?**
    No. It matches (0.672 = 0.672) but does not exceed. True adaptive advantage
    was not demonstrated.

11. **What is the smallest empirically supported architecture?**
    B1_extended: retrieve→gen_hyp→retrieve→gen_hyp→reason→retrieve→reason.
    No market, no self-model, no stopping policy, no persistent state.

12. **Is external live validation now scientifically justified?**
    Conditionally. The fixed sequence result is strong and should generalize.
    The hierarchical control result needs task diversity to test adaptivity.
    A local-model experiment would test whether findings hold with actual
    LLM reasoning (vs scripted simulator operations).

## REE-Minimal-Empirical Configuration

```
B1_extended:
  retrieve
  -> generate_hypothesis
  -> retrieve
  -> generate_hypothesis
  -> reason
  -> retrieve
  -> reason

Required components: evidence retrieval, hypothesis generation (x2), reasoning
Optional components: attack (if state is rich), ignorance (via attack)
Not required: market, self-model, stopping, persistent ecology, diversity market
```

## Companion Documents

- `CAMPAIGN_V2_AUDIT.md` — V2 identifiability gate analysis
- `HYPOTHESIS_CANONICAL_MAPPING.md` — Canonical hypothesis ID mapping
- `B1_SEQUENCE_DECOMPOSITION.md` — Phase 17.1 results
- `HYPOTHESIS_ECOLOGY_REPLICATION.md` — Phase 17.2 results
- `COGNITIVE_COMPLEMENTARITY_ANALYSIS.md` — Phase 18.2-18.4 results
- `ATTACK_OPERATOR_STATE_DEPENDENCE.md` — Phase 18.5 results
- `COGNITIVE_MOTIFS.md` — Phase 18.6 results
- `HIERARCHICAL_CONTROL_RESULTS.md` — Phase 19 results
- `COMPONENT_EVIDENCE_MAP.md` — Final component classification
- `NEGATIVE_FINDINGS_V3.md` — Negative results
- `results/` — Machine-readable backing data (JSON/JSONL)
