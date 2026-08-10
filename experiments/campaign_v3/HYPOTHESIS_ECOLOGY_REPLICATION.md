# Hypothesis Ecology Replication (Phase 17.2)

## Objective

V2 reported hypothesis ecology ablation effect d≈1.4 within Full REE.
Question: does hypothesis ecology improve quality across architectures,
or is its effect specific to Full REE?

## Method

Tested hypothesis ecology in multiple architectural contexts on V3 dev worlds.

## Results

| Configuration | Mean Quality | Std | N |
|---|---|---|---|
| B1 (inherently generates 2 hypotheses) | 0.5731 | 0.228 | 50 |
| B1 + extra hypothesis generation | 0.5731 | 0.228 | 50 |
| Full REE with ecology | 0.3579 | 0.162 | 50 |
| B0 direct | 0.2889 | 0.222 | 50 |
| No hypothesis at all (fixed ret->ret->ret->reason) | 0.0413 | 0.012 | 50 |
| Full REE without ecology | 0.0372 | 0.016 | 50 |

## Key Findings

### Finding 1: Ecology does NOT help B1

B1 = B1+ecology = 0.5731 (identical). B1 already generates two hypotheses in
its fixed sequence, so adding extra hypothesis generation provides no marginal
benefit.

### Finding 2: Ecology effect is specific to Full REE

Full REE with ecology (0.358) vs without (0.037) shows the familiar d≈1.4 effect.
But this occurs because without the ecology flag, the hypothesis generation
operator is removed entirely from the registry, and the market never selects
hypothesis generation. The ecology flag is essentially an "enable hypothesis
generation" flag in the current implementation.

### Finding 3: The mechanism is simpler than it appeared

The massive V2 ecology effect is not evidence for "persistent hypothesis ecology"
as an architectural principle. It is evidence that **hypothesis generation is
necessary for epistemic quality** and that Full REE's market, when denied the
hypothesis operator, produces near-zero quality.

## V3 Locked Test Replication

| Configuration | Locked Quality | Std |
|---|---|---|
| Full REE with ecology | 0.3243 | 0.168 |
| Full REE without ecology | 0.0376 | 0.016 |
| Ecology ablation effect (difference) | 0.287 | - |

The effect replicates on fresh locked worlds. But the interpretation changes:
ecology ON/OFF is essentially hypothesis_generation ON/OFF.

## Revised Interpretation

V2 claim: "Explicit persistent hypothesis ecology improves quality (d≈1.4)"

V3 revision: "Hypothesis generation is a necessary cognitive operation. The
V2 ecology effect reflects the removal of hypothesis generation from the
operator registry, not the value of persistent hypothesis tracking per se."

The distinction matters: B1 achieves higher quality than Full REE+ecology
(0.573 vs 0.358) using simple two-hypothesis generation without any persistent
ecology management.

## Hypothesis Verdict

**H-REE-10 (Hypothesis ecology outperforms single-trajectory reasoning)**:
PARTIALLY_SUPPORTED. Having multiple hypotheses is clearly better than none
(d≈1.4), but the persistent ecology mechanism is not what provides the value.
Simple two-hypothesis generation in a fixed sequence suffices and is more
effective.

**H-REE-12 (Ecology improves quality across architectures)**: NOT_SUPPORTED.
The ecology flag has no effect on B1, which already generates hypotheses.
