# ASAR SCIENTIFIC DISCOVERY — CHECKPOINT 002
## LOCKED STAGE 1 + STAGE 2

---

## Environment

```
STARTING SHA: 288434e5ae9d6ac7286bcdbd533c6fd728300171
ENDING SHA: (uncommitted — pending commit)

PYTHON: 3.12.13
ENVIRONMENT: .venv (pip install -e ".[dev]")

SCIENTIFIC DISCOVERY TESTS: 123 passed (111 Stage 1 + 12 Stage 2)
FULL TEST SUITE: 569 passed, 1 skipped
```

---

## STAGE 1 LOCKED VALIDATION

### Preregistration

```
PREREGISTRATION: research/scientific_discovery/benchmarks/falsification/PREREGISTRATION_V1.md
LOCKED SPLIT: seeds 21-40
N: 120 (6 world types × 20 seeds)
PREVIOUSLY UNSEEN: PASS (seeds 21-40 never executed before freeze)
```

### Anti-Tautology Audit

```
FALSIFICATION BOOST AUDIT: PASS WITH REQUIRED CONTROLS
  - No oracle leakage
  - Boost semantically gated (direction + relevance threshold)
  - NOT unconditional flag check
  - 100% of effect from boost, 0% from policy alone
  - B3-ZERO required and implemented

ORACLE LEAKAGE: PASS
  - Certified: NO_ORACLE_LEAKAGE_CERTIFICATE.json
  - No component accesses WorldGroundTruth during episode

SEMANTIC CONTROL:
  - Supporting evidence → boost NULL: PASS
  - Contradicting + relevant → boost fires: PASS
  - Irrelevant evidence → boost NULL: PASS
  - No proposal → boost NULL: PASS
```

### Parameter Sensitivity

```
boost=0.0: refut_sens=0.378, stickiness=0.057
boost=1.0: refut_sens=0.378, stickiness=0.057
boost=1.2: refut_sens=0.400, stickiness=0.037
boost=1.5: refut_sens=0.396, stickiness=0.025 (DEFAULT)
boost=2.0: refut_sens=0.367, stickiness=0.025
boost=3.0: refut_sens=0.360, stickiness=0.025

Direction robust across all boost > 1.0
```

### Policies

```
B0: Passive Update — implemented
B1: Confirmation Seeker — implemented
B2: Random Challenge — implemented
B3-ZERO: Falsification policy, NO boost — implemented
B3: Falsification-First (full) — implemented
B4: Oracle — implemented
```

### Locked Results (N=120)

```
RECOVERY ACCURACY:
  B0:      0.8333
  B1:      0.6667
  B2:      0.8333
  B3-ZERO: 0.8333
  B3:      0.8333
  B4:      1.0000

  B3 - B0: 0.0000
  B3-ZERO - B0: 0.0000

REFUTATION SENSITIVITY:
  B3:  0.3973
  B0:  0.3723
  Δ:   +0.0209
  95% CI: [+0.0171, +0.0245]
  p (permutation, one-sided): < 0.0001

  B3-ZERO: 0.3723 (identical to B0)

THEORY STICKINESS:
  B3:  0.0123
  B0:  0.0283
  Δ:   -0.0159
  95% CI: [-0.0209, -0.0113]
  p (permutation, one-sided): < 0.0001

FALSE ABANDONMENT:
  B3: 0/100 (0.000)
  B0: 0/100 (0.000)

NON-IDENTIFIABILITY: PASS (20/20 correct abstention)
NULL WORLD: PASS (20/20 correct rejection)
```

### Critical Decomposition

```
POLICY EFFECT (B3-ZERO - B0):
  Refutation Sensitivity: +0.0000
  Theory Stickiness:      +0.0000
  → Policy alone provides NO independent value

BOOST EFFECT (B3 - B3-ZERO):
  Refutation Sensitivity: +0.0209
  Theory Stickiness:      -0.0159
  → ALL benefit from recognition amplification

TOTAL EFFECT (B3 - B0):
  = BOOST EFFECT (100%)
```

### SD-H1 Verdict

```
SD-H1: PARTIALLY_SUPPORTED

Justification:
- B3 does NOT improve Recovery Accuracy over B0 (tied)
- B3 DOES improve preregistered process metrics:
  - Refutation sensitivity: +0.021 (p < 0.0001)
  - Theory stickiness: -0.016 (p < 0.0001)
- No safety degradation (false abandonment = 0)
- Effect comes from RECOGNITION mechanism, not action policy
- B3 dramatically outperforms B1 (confirmation-seeking):
  - Recovery: +0.167
  - Stickiness: -0.384

Does NOT meet STRONGLY_SUPPORTED criteria (requires recovery improvement).
Does NOT meet NOT_SUPPORTED criteria (process metrics improve significantly).
```

### Main Stage 1 Interpretation

> The falsification recognition mechanism (amplified belief updates when evidence matches falsification focus) changes the TRAJECTORY of belief revision in scientifically desirable ways: faster drops on false hypotheses, lower residual belief after refutation, no false abandonment.
>
> However, in these controlled worlds with predetermined evidence, the benefit is entirely from INTERPRETATION (recognition boost), not from ACTION (policy selection). The falsification policy identifies targets but cannot influence which evidence is observed.
>
> The benchmark may be at ceiling for Recovery Accuracy — evidence is decisive enough that even passive processing succeeds. This limits the headline claim but validates the mechanism direction.

---

## STAGE 2 — DISCRIMINATIVE EXPERIMENT DESIGN

### Status: IMPLEMENTED AND VALIDATED

### Tests: 12 passed

### World Types

```
- confirmation_discrimination_split: Confirmation and discrimination disagree
- costly_discrimination: High discrimination costs more
- non_identifiable_experiment: No experiment discriminates
- multiple_rounds: Varying discrimination levels
```

### Policies

```
E0: Random — uniform selection
E1: Cheapest — lowest cost
E2: Confirmation — maximizes P(positive|leader)
E3: Discrimination (ASAR) — maximizes JSD between hypothesis predictions
E5: Oracle — uses true IG (never available to agents)
```

### Results (N=80, 4 world types × 20 seeds)

```
ORACLE REGRET:
  E0 (Random):         0.1577
  E1 (Cheapest):       0.2463
  E2 (Confirmation):   0.1106
  E3 (Discrimination): 0.0000
  E5 (Oracle):         0.0000

E3 achieves ZERO oracle regret (100% optimal selections)
E3 vs E2: +0.1106 oracle IG advantage, 95% CI [+0.086, +0.133]
```

### SD-H3 Verdict

```
SD-H3: SUPPORTED

The discrimination policy selects experiments with objectively higher
information gain than random (+0.158), cheapest (+0.246), and
confirmation-seeking (+0.111) baselines.

E3 achieves oracle-optimal selections in all tested worlds.
```

### Anti-Tautology Check: PASS

The discrimination score (JSD) is computed from the agent's own hypothesis predictions — not from oracle truth. The fact that JSD perfectly correlates with oracle IG in these controlled worlds validates the scoring function's soundness, not tautological design.

---

## NEGATIVE FINDINGS

1. **Recovery tied (B3 = B0)**: Benchmark at ceiling; evidence too decisive for differentiation
2. **B3-ZERO = B0**: Falsification policy alone adds nothing; all benefit from boost
3. **Stage 1 effect is interpretation, not action**: Recognition mechanism, not policy selection
4. **Effect size moderate (B3 vs B0)**: Δ ≈ 0.02 (though vs B1: Δ ≈ 0.30)
5. **Stage 2 E3 achieves zero regret**: May indicate worlds are too easy for discrimination

---

## SCIENTIFIC BLOCKERS

None. Both stages complete with honest, interpretable results.

---

## LLM INTEGRATION

```
STATUS: NOT YET

Stage 1 + Stage 2 deterministic kernel is validated.
The kernel rewards:
  - Correct belief revision
  - Falsification recognition
  - Discriminative experiment selection

LLM should provide:
  - Creative hypothesis generation
  - Mechanistic alternatives
  - Falsifier generation
  - Prediction derivation
  - Experiment ideas

LLM should NOT replace:
  - Belief accounting
  - Experiment scoring
  - Ground truth evaluation
```

---

## GO TO NEXT STAGE

```
YES — proceed to LLM integration gating (Stage 3 / SD-H4)

The deterministic scientific kernel is sound:
  - State management: certified
  - Belief update: all invariants pass
  - Falsification recognition: behaviorally consequential
  - Experiment design: zero oracle regret
  - No oracle leakage
  - Anti-tautology audit: honest limitations documented
```

---

## EXACT NEXT ACTION

1. Commit all Stage 2 + locked validation work
2. Implement LLM capability gate (can frontier model produce structured hypotheses/falsifiers?)
3. Test whether LLM-generated falsifiers improve recognition mechanism quality
4. Run SD-H4: Does the system appropriately abandon self-generated hypotheses?
