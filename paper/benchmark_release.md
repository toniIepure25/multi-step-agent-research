# Benchmark Release Package

## Overview

The Epistemic World Simulator benchmark enables controlled evaluation of cognitive operation sequences from matched epistemic states in LLM research agents.

## Package Contents

```
benchmark/
├── README.md                    # This file
├── schemas/                     # Typed data structures
│   ├── evidence.py              # EvidenceItem, EvidenceCorpus
│   ├── hypotheses.py            # Hypothesis, HypothesisSet
│   ├── epistemic_state.py       # EpistemicState, QualityMetric
│   └── experiment.py            # ExperimentRecord, SequenceResult
├── simulator/
│   ├── epistemic_world.py       # EpistemicWorldSimulator core
│   ├── regime_generators.py     # 8 epistemic regime generators
│   ├── quality_evaluator.py     # Evaluator-only quality function
│   └── state_fork.py            # Event sourcing / counterfactual fork
├── sequences/
│   ├── primitives.py            # 4 primitive cognitive operations
│   ├── fixed_sequences.py       # Named sequences (B1_extended, explore, etc.)
│   └── complementarity.py       # Pairwise complementarity computation
├── evaluation/
│   ├── metrics.py               # Quality, coverage, calibration
│   ├── complementarity_matrix.py # Matrix computation
│   └── timing_analysis.py       # Attack timing / stage analysis
├── baselines/
│   ├── greedy_primitive.py      # Greedy single-operation baseline
│   ├── fixed_B1.py              # B1_extended fixed sequence
│   └── oracle.py                # Hindsight-optimal oracle
├── config/
│   ├── v3_config.toml           # V3 experiment configuration
│   ├── v4_config.toml           # V4 experiment configuration
│   └── v5_config.toml           # V5 LLM execution configuration
└── examples/
    ├── run_complementarity.py   # Compute complementarity matrix
    ├── run_timing_analysis.py   # Attack timing experiment
    └── run_llm_replication.py   # LLM-in-loop replication
```

## Source Mapping

The benchmark code is assembled from existing repository modules:

| Benchmark Component | Repository Source |
|--------------------|------------------|
| `simulator/epistemic_world.py` | `asar/core/epistemic_world_simulator.py` |
| `simulator/regime_generators.py` | `asar/core/v4_regime_generators.py` |
| `sequences/primitives.py` | `asar/core/cognitive_operations.py` |
| `evaluation/metrics.py` | `asar/evaluation/` |
| `config/*.toml` | `config/pipeline.toml` + experiment configs |

## Usage

```python
from benchmark.simulator import EpistemicWorldSimulator
from benchmark.sequences import fixed_sequences

sim = EpistemicWorldSimulator(regime="B", seed=42)
world = sim.generate_world()

# Same-state counterfactual evaluation
state = sim.get_state()

# Fork A: hypothesis then retrieve
sim.restore_state(state)
sim.execute_operation("generate_hypothesis")
sim.execute_operation("retrieve")
quality_A = sim.evaluate()

# Fork B: retrieve then hypothesis
sim.restore_state(state)
sim.execute_operation("retrieve")
sim.execute_operation("generate_hypothesis")
quality_B = sim.evaluate()

complementarity = quality_A - quality_B  # order effect
```

## Splits

| Split | Worlds | Purpose | Seed Range |
|-------|--------|---------|-----------|
| Dev | 50-56 | Development and analysis | 271828–271834 |
| Validation | 25 | Hyperparameter selection | 271835–271859 |
| Locked test | 25 | One-shot final evaluation | 271860–271884 |

## Evaluation Protocol

1. Configure regime and seed.
2. Generate world.
3. Execute cognitive sequence under fixed token budget.
4. Evaluate quality using evaluator-only function.
5. For complementarity: fork from same state, execute alternatives, compare.

## Reproducibility

- Python 3.11+
- Seeds are deterministic within Python version
- No external API calls required for simulator-only experiments
- LLM replication requires OpenAI-compatible inference endpoint
