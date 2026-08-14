# FalsificationBench Specification

**Working title:** FalsificationBench — Evaluating Scientific Self-Correction in AI Research Agents
**Status:** Pre-implementation specification
**Date:** 2026-08-14

---

## 1. Purpose

FalsificationBench evaluates whether AI systems can:
1. Identify when their hypotheses are wrong
2. Appropriately revise beliefs after contradictory evidence
3. Abandon theories that have been falsified
4. Design experiments that discriminate between alternatives
5. Recognize when no conclusion is warranted

It does NOT primarily evaluate:
- Hypothesis generation quality (use HypoBench)
- Literature retrieval (use ResearchBench)
- Scientific knowledge (use FrontierScience)

---

## 2. Central Evaluation Object

**Scientific Self-Correction:** The ability to update, revise, or abandon scientific beliefs in response to evidence — especially when that evidence contradicts the system's current leading hypothesis.

---

## 3. Task Structure

Each task is a **controlled scientific world** with:

```
World = {
    research_question: str,
    true_hypothesis: str | None,  # None for null/non-identifiable worlds
    candidate_hypotheses: list[Hypothesis],
    evidence_sequence: list[EvidenceRound],
    ground_truth_causal_structure: CausalGraph,
    world_type: WorldType,
}

EvidenceRound = {
    round_number: int,
    available_evidence: list[Evidence],
    expected_belief_change: dict[str, float],  # hypothesis → expected direction
    decisive: bool,  # whether this round is supposed to cause major revision
}
```

---

## 4. World Types

### Type A: Confirmation Trap
```
Round 0: Moderate evidence favoring H1 (wrong)
Round 1: Weak contradictory evidence against H1
Round 2: Decisive falsifier for H1
Round 3: Strong evidence supporting H2 (correct)
```
**Correct behavior:** Abandon H1 after Round 2, adopt H2 after Round 3

### Type B: Confounded Causality
```
Setup: Observed correlation X↔Y
Hidden: Confounder Z causes both X and Y
Evidence: Z is revealed progressively
```
**Correct behavior:** Detect confounding, reduce causal H1 belief

### Type C: Reverse Causality
```
Setup: X appears to cause Y
Truth: Y causes X
Evidence: Temporal/intervention data reveals direction
```
**Correct behavior:** Generate reverse-causality alternative, revise after temporal evidence

### Type D: Measurement Artifact
```
Setup: Apparent signal in data
Truth: Signal is measurement artifact
Evidence: Calibration/control data reveals artifact
```
**Correct behavior:** Detect artifact, reduce signal belief

### Type E: Multiple Mechanisms
```
Setup: Observations suggest single cause
Truth: Two mechanisms each explain different subsets
Evidence: Subset-specific data reveals multi-causality
```
**Correct behavior:** Avoid single-theory commitment, recognize multi-mechanism

### Type F: Null World
```
Setup: Plausible-looking correlation
Truth: No causal relationship (random co-occurrence)
Evidence: Growing data shows no robust relationship
```
**Correct behavior:** Conclude "no relationship" / ABSTAIN

### Type G: Ontology Failure
```
Setup: H1, H2, H3 all use wrong framing
Truth: Correct explanation requires different variables/representation
Evidence: All hypotheses systematically fail
```
**Correct behavior:** Reject hypothesis space, propose reframing

### Type H: Non-Identifiable
```
Setup: H1 and H2 make identical predictions given available evidence
Truth: Cannot be resolved without specific experiment
Evidence: All available data is equally consistent with both
```
**Correct behavior:** ABSTAIN / declare non-identifiable / request specific experiment

---

## 5. Metrics

### Primary Metrics

#### Refutation Sensitivity (RS)
```
RS = P_before(H) - P_after_decisive_refutation(H)
```
Higher is better when refutation is valid. Measures responsiveness to falsification.

#### Irrelevant Perturbation Robustness (IPR)
```
IPR = 1 - |P_before(H) - P_after_irrelevant(H)|
```
Higher is better. Measures stability under noise.

#### Recovery Accuracy (RA)
Does the system's final hypothesis ranking match ground truth after all evidence?
```
RA = 1 if correct hypothesis is top-ranked after full evidence, 0 otherwise
```

#### Abandonment Latency (AL)
Number of evidence rounds after decisive falsifier before the system drops H below threshold.
```
AL = round_abandoned - round_decisive_falsifier
```
Lower is better (0 = ideal immediate abandonment).

#### Theory Stickiness (TS)
Excess probability retained on refuted hypothesis:
```
TS = P_final(H_refuted) - P_ground_truth(H_refuted)
```
Lower is better (0 = no stickiness).

### Secondary Metrics

#### Self-Authorship Bias (SAB)
```
SAB = ΔBelief_self_generated - ΔBelief_external
```
Under equivalent refutation. Closer to 0 is better.

#### Ontology Revision Rate (ORR)
Proportion of ontology-failure worlds where system triggers revision.

#### False Ontology Revision Rate (FORR)
Proportion of non-failure worlds where system incorrectly triggers revision.

#### Abstention Accuracy
Proportion of non-identifiable worlds where system correctly abstains.

#### Hypothesis Discrimination Score (HDS)
For experiment design evaluation:
```
HDS = variance of predicted outcomes across hypotheses for selected experiment
```

#### Oracle Regret
```
Regret = InfoGain(oracle_experiment) - InfoGain(selected_experiment)
```

---

## 6. Metamorphic Tests (Validity Checks)

These are not evaluation metrics but **benchmark validity tests**:

1. **Decisive falsifier invariant:** Adding a valid decisive refutation must NOT increase belief in target
2. **Duplicate evidence invariant:** Duplicating same source must NOT double confidence
3. **Irrelevant evidence invariant:** Adding irrelevant evidence must minimally affect belief
4. **Evidence reversal invariant:** Replacing support with contradiction must move posterior appropriately
5. **Paraphrase invariant:** Paraphrasing equivalent evidence must not materially change decision
6. **Source dependence invariant:** N articles from same root study ≠ N independent confirmations

---

## 7. Baselines

| Baseline | Implementation | Purpose |
|----------|---------------|---------|
| **Single-pass LLM** | Prompt with full evidence, ask for conclusion | Raw capability floor |
| **Reflection** | Generate → self-critique → revise (3 rounds) | Self-correction without structure |
| **Multi-agent debate** | 3 agents argue, judge decides | Adversarial dialogue benefit |
| **Greedy evidence seeker** | Always retrieve more evidence for leading hypothesis | Confirmation-seeking baseline |
| **Random experiment** | Random selection from available experiments | Experiment design floor |
| **Fixed workflow** | Deterministic: generate → falsify → revise → conclude | Structured but non-adaptive |
| **Oracle** | Always selects maximally informative action | Ceiling |

All baselines receive equal compute budget where applicable.

---

## 8. World Generation

### Requirements
- Ground truth causal structure is fully specified
- Evidence sequence is predetermined (no online generation)
- Expected belief changes are pre-computed
- Decisive rounds are explicitly marked
- Worlds are designed around failure modes, NOT around ASAR's policy

### Scale (Stage 1)
- 5 worlds per type × 8 types = 40 worlds minimum
- 3 difficulty levels per world = 120 task instances
- Each instance has fixed evidence sequence (no randomness in world)
- Stochasticity only in system's reasoning

### Difficulty Levels
- **Easy:** Decisive evidence is unambiguous; correct hypothesis clearly best after full evidence
- **Medium:** Evidence is somewhat noisy; requires careful discrimination
- **Hard:** Evidence is subtle; requires sophisticated reasoning about independence, confounding

---

## 9. Evaluation Protocol

```
For each world W:
    For each system S (ASAR + baselines):
        For each seed (N=5 minimum):
            1. Present research question
            2. For each evidence round r:
                a. Present available evidence
                b. Record system's belief state
                c. Record system's actions (if applicable)
            3. Record final conclusion
            4. Compute metrics against ground truth
    
    Statistical tests:
        - Paired comparisons (ASAR vs each baseline)
        - Effect sizes + confidence intervals
        - Multiple-testing correction across metrics
```

---

## 10. Preregistration Requirements

Before locked evaluation:
- [ ] Task set frozen (hash recorded)
- [ ] Metrics defined (no post-hoc addition)
- [ ] Baselines specified
- [ ] SESOI (smallest effect size of interest) declared
- [ ] Analysis plan written
- [ ] Exclusion criteria defined
- [ ] Multiple-testing correction specified
- [ ] Number of seeds fixed
- [ ] Dev/validation/test split declared

---

## 11. Contamination Defense

- Worlds are synthetically constructed (no real-world discovery tasks in Stage 1)
- Ground truth is by construction, not from literature
- No LLM has seen these specific causal structures in training
- World generation code is deterministic given seed
- Evidence texts can be generated or templated (not extracted from papers)

---

## 12. Development / Validation / Test Split

```
DEV worlds:      Used freely during development (20 worlds)
VALIDATION:      Used for hyperparameter tuning, max 3 uses (20 worlds)
LOCKED TEST:     Used exactly ONCE for final reported results (80 worlds)
```

Task hashes recorded in manifest. Seen-task registry maintained.

---

## 13. Reporting Requirements

For each condition report:
- Mean ± std for each metric
- Effect size (Cohen's d) for each pairwise comparison
- 95% confidence intervals
- p-values with Holm-Bonferroni correction
- Per-world-type breakdown
- Failure case analysis (qualitative)
- Compute cost per condition

---

## 14. GO/NO-GO Criteria for Stage 1

FalsificationBench Stage 1 passes GO if:
1. Metamorphic tests pass for ALL systems (benchmark validity)
2. At least one metric shows statistically significant difference between ASAR and best baseline (d > 0.3)
3. Oracle achieves ceiling performance (benchmark discriminates)
4. Single-pass LLM does NOT achieve ceiling (benchmark is non-trivial)
5. Results replicate across seeds (CV < 0.3 for primary metrics)

If these criteria are NOT met, the benchmark itself must be revised before claiming mechanism value.
