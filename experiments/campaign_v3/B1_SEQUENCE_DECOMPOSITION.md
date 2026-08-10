# B1 Sequence Decomposition (Phase 17.1)

## Objective

B1 (retrieve -> gen_hyp -> retrieve -> gen_hyp -> reason) achieved 0.594 quality
on V2 locked test, outperforming Full REE (0.356). Decompose B1 to identify
which structural features drive this advantage.

## Method

10 B1 variants tested on 50 V3 dev worlds (5 families x 10 worlds).

## Results

| Variant | Mean Quality | Std | N | Tokens |
|---|---|---|---|---|
| B1_extended (B1 + retrieve + reason) | **0.6304** | 0.176 | 50 | 3500 |
| B1_ret_hyp_ret_hyp_atk_reason | 0.6031 | 0.252 | 50 | 3000 |
| B1_full | 0.5731 | 0.228 | 50 | 2500 |
| B1_no_1st_ret | 0.4319 | 0.260 | 50 | 2000 |
| B1_no_2nd_ret | 0.4319 | 0.260 | 50 | 2000 |
| B1_hyp_ret_reason | 0.3975 | 0.217 | 50 | 1500 |
| B1_one_hyp | 0.3805 | 0.267 | 50 | 2000 |
| B1_reversed | 0.3500 | 0.157 | 50 | 2500 |
| B1_no_reason | 0.3435 | 0.154 | 50 | 2000 |
| B1_ret_only | 0.0384 | 0.014 | 50 | 2500 |

## Analysis

### Every step of B1 is necessary

| Ablation | Quality Drop | Effect |
|---|---|---|
| Remove first retrieve | -0.141 | Large |
| Remove second retrieve | -0.141 | Large (identical) |
| Remove second hypothesis | -0.193 | Large |
| Remove reason | -0.230 | **Largest** |

### Reason is the most critical operation

Removing reason causes the largest single-step degradation (-0.230). Without reason,
the system generates hypotheses and collects evidence but never integrates them via
consistency scoring.

### Two hypotheses are substantially better than one

B1_one_hyp (0.381) vs B1_full (0.573) shows that generating a second hypothesis
adds +0.193 quality. Hypothesis diversity enables discriminative reasoning.

### Order matters strongly

B1_full (0.573) vs B1_reversed (0.350): the forward sequence outperforms the
reversed sequence by +0.223. This is direct evidence that cognitive operations
are **non-commutative**: retrieve-before-hypothesize is better than
hypothesize-before-retrieve.

### Extension helps

B1_extended (0.630) adds one retrieve + one reason after the standard B1 sequence,
gaining +0.057. Diminishing but positive returns from further integration.

### Retrieve alone is nearly useless

B1_ret_only (0.038) shows that evidence collection without hypothesis generation
or reasoning produces near-zero quality.

## Mechanism Classification

| Mechanism | Status | Evidence |
|---|---|---|
| Reasoning | **CORE** | -0.230 when removed |
| Multiple hypotheses | **CORE** | -0.193 when reduced to 1 |
| Retrieve before hypothesize | **CORE** | -0.223 when reversed |
| First retrieve | IMPORTANT | -0.141 |
| Second retrieve | IMPORTANT | -0.141 |
| Extended reasoning | USEFUL | +0.057 |
| Retrieval without hypothesis/reason | USELESS | 0.038 quality |

## Conclusion

B1's advantage arises from three structural features: (1) reason as terminal
integration, (2) multiple hypothesis generation, and (3) proper temporal ordering
(retrieve -> hypothesize -> reason). All three are necessary.
