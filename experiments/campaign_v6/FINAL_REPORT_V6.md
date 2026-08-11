# Campaign V6 Final Report

## Campaign
V6 Causal Closed-Loop Validation

## Starting SHA
`1ab24bc`

## Tests
446 passed, 1 skipped (pre-V6 suite)

## New Public Datasets
Not yet executed (SciFact and HotpotQA selected; implementation pending)

## Task Splits
DEV: N/A (all V6 simulator results are fresh worlds)
LOCKED: 32 worlds (8 regimes × 4 seeds, seed base 314159)

## Primary Model
gemma3:27b-it-qat (via remote Ollama at inference.ccrolabs.com)

## Transfer Model
Not yet executed (llama3.2-vision:11b-instruct-q8_0 available)

## Independent Locked N
32 worlds (simulator)

## Closed-Loop Certification
PASS (11/11 conditions certified)

## Factorial Complementarity
### Study A (Information-Held-Constant)
```
Interaction: 0.000 (95% CI [0.000, 0.000])
N = 32 worlds
C00 = 0.000, C10 = 0.164, C01 = 0.000, C11 = 0.164
Call budget matched: YES (3 calls per condition)
```

### Study A-B (Retrieval-Mediated)
```
Interaction: 0.000 (95% CI [0.000, 0.000])
N = 32 worlds
```

### Verdict: NO SUPER-ADDITIVE COMPLEMENTARITY UNDER BUDGET CONTROLS

## Semantic Artifact Intervention
Not yet executed (infrastructure implemented in run_v6.py)

## Retrieval Mediation
Not formally analyzed (quality determined by hypothesis correctness)

## Matched Attack Timing
```
Early:  0.700 ± 0.000
Mid:    0.719 ± 0.050
Late:   0.719 ± 0.050
Range:  0.019
Budget matched: YES (same operations, same call count)
```

### Verdict: ATTACK TIMING EFFECT DISAPPEARS UNDER BUDGET CONTROLS

## Hypothesis Verdicts

```
H-REE-19 (Compute-Controlled Complementarity): NOT_SUPPORTED
  Interaction = 0.000 across 32 worlds

H-REE-20 (Semantic Mediation): UNTESTED
  Infrastructure built; execution pending

H-REE-21 (Closed-Loop LLM Causality): PARTIALLY_SUPPORTED
  Certification PASS: LLM artifacts enter state and affect downstream.
  BUT quality is dominated by hypothesis generation alone.

H-REE-22 (Matched-Budget Attack Timing): NOT_SUPPORTED
  Effect = 0.019 (vs V5 unmatched 0.276)

H-REE-23 (Exogenous Benchmark Transfer): UNTESTED
  External datasets selected (SciFact, HotpotQA); execution pending
```

## Pseudoreplication
PASS — each world is independent; results reported at world level

## Compute Fairness
PASS — all factorial cells use identical LLM call count (verified by certification)

## Information Fairness
PASS — Study A: no evidence in any cell; Study A-B: same retrieval budget

## Prior Art Delta
DISTINCT methodology; central mechanism (complementarity) no longer supported
Novelty shifts to methodology + negative finding

## Negative Findings
1. Factorial complementarity = 0 under budget controls
2. Attack timing effect = 0.019 under matched budget (was +0.276)
3. Quality dominated by hypothesis generation alone
4. Reason adds nothing beyond hypothesis generation
5. Second retrieval adds nothing beyond hypothesis generation
6. Token counting unavailable from Ollama API

## Paper Category After V6
CONTROLLED METHODOLOGY + NEGATIVE RESULTS PAPER

Previous: "Mechanistic complementarity finding with LLM replication"
After V6: "Methodological contribution with important negative result"

The paper's value shifts from claiming temporal complementarity exists
to demonstrating that:
1. Matched-budget controls matter
2. Apparent interactions can be main effects in disguise
3. The methodology for testing is novel and useful
4. Negative results under strong controls are scientifically important

## Simulated Review Score Range (estimated)
4-6 (contribution question remains; but negative results are more honest)

## ICLR/ICML Recommendation
DO_NOT_SUBMIT to ICLR 2027 with current results.

Consider:
1. NeurIPS 2027 Datasets & Benchmarks (benchmark methodology focus)
2. Workshop paper at ICLR/ICML 2027 (negative results track)
3. Complete H-REE-20 and H-REE-23 before any full-paper submission

## Exact Next Action
1. Execute H-REE-20 (semantic artifact intervention) to determine if
   artifact CONTENT matters even though factorial interaction is zero
2. Execute H-REE-23 (external datasets) to test on independent benchmarks
3. If both negative: position as methodology + negative results paper
4. If external datasets show effects: the contribution shifts to external validity
