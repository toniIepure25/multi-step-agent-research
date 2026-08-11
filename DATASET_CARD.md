# Dataset Card

## Epistemic World Simulator Dataset

### Sources
Programmatically generated worlds using `asar/evaluation/scenarios/v4_regimes.py`.
Eight epistemic regime families, each generating worlds with deterministic seeds.

### License
Research use (part of this repository).

### Splits

| Split | Purpose | World IDs | Frozen? |
|-------|---------|-----------|---------|
| V4 DEV | Architecture development | v4_regimes × seeds 100-106 | Yes (SHA 2f63cf9) |
| V6 DEV | V6 validation | v6_regimes × seeds 314159+ | Freeze before locked |
| V6 LOCKED | Confirmatory tests | To be defined | Freeze before locked |

### Task IDs
World IDs follow pattern: `{regime}_{seed}_{index}`

### Provenance
- V3: 50 worlds, seed base 100
- V4: 56 worlds (8 regimes × 7), seed base 271828
- V5 Phase 26: 16 worlds (8 × 2), seed base 271828
- V6: 32 worlds (8 × 4), seed base 314159

### Gold Labels
Evaluator-only fields per world:
- `true_hypothesis_id`: which hypothesis is correct
- `is_true` on each hypothesis
- `supports_hypotheses` / `contradicts_hypotheses` on evidence
- `information_value` on evidence
- Hidden variables and causal edges

### Agent-Visible vs Evaluator-Only

**Agent sees:**
- Evidence content, source ID, source reliability
- Hypothesis statement, initial plausibility
- Reason output: consistency scores
- Attack output: weaknesses, ignorance items (descriptions)

**Agent NEVER sees:**
- `is_true` flag
- `true_hypothesis_id`
- Full causal graph
- `information_value`
- `correct_conclusion`

**V6 fix:** Evidence `supports` and `contradicts` labels are stripped from
agent-visible retrieve output (V4/V5 leaked these).

## External Datasets (V6)

### SciFact (planned)
- Source: Wadden et al., 2020
- License: Apache 2.0
- Gold: Claim verification labels + evidence sentences
- Agent-visible: Abstract text
- Evaluator-only: SUPPORTS/REFUTES/NEI labels, gold evidence sentence IDs

### HotpotQA (planned)
- Source: Yang et al., 2018
- License: CC BY-SA 4.0
- Gold: Answer + supporting facts
- Agent-visible: Distractor paragraphs
- Evaluator-only: Gold answer, supporting fact indices
