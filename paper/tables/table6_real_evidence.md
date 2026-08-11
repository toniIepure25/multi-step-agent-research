# Table 6: Static Real-Evidence Results (V5 Phase 27, N = 14 packs)

## Overall

| Condition | Sequence | Mean | Std | N |
|-----------|----------|------|-----|---|
| greedy_primitive | [retrieve, generate_hypothesis, synthesize] | **0.718** | 0.074 | 14 |
| direct | [retrieve_all, synthesize] | 0.696 | 0.058 | 14 |
| reflection | [retrieve_all, synthesize, critique, revise] | 0.696 | 0.058 | 14 |
| B1_extended | [retrieve, gen_hyp, retrieve, gen_hyp, reason, retrieve, reason, synthesize] | 0.691 | 0.112 | 14 |
| FULL_EXPLORE | [retrieve, gen_hyp, reason, retrieve, gen_hyp, reason, attack, synthesize] | 0.688 | 0.112 | 14 |

*Condition range = 0.030. Model: Gemma 3 27B QAT. Source: `campaign_v5/results/phase27_summary_gemma3.json`.*

## By Domain

| Domain | N | direct | reflection | B1_extended | FULL_EXPLORE | greedy |
|--------|---|--------|-----------|-------------|-------------|--------|
| Cognitive science | 5 | 0.735 | 0.735 | 0.685 | 0.675 | **0.768** |
| AI research | 5 | 0.660 | 0.660 | 0.690 | **0.700** | 0.690 |
| Biomedical | 1 | 0.700 | 0.700 | 0.700 | 0.700 | 0.700 |
| Economics | 1 | 0.700 | 0.700 | 0.700 | 0.700 | 0.700 |
| History of science | 1 | 0.663 | 0.663 | **0.700** | 0.650 | 0.663 |
| Social science | 1 | 0.700 | 0.700 | 0.700 | 0.700 | 0.700 |

*Four domains with N = 1 show limited or zero condition sensitivity.*
