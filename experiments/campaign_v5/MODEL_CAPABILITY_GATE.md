# Phase 25 — Model Capability Gate

**Campaign:** V5
**Status:** BLOCKED — No model server available
**Date:** 2026-08-10

## 25.1 — Available Local Models

### Infrastructure Inspection

| Component | Status |
|-----------|--------|
| Ollama | NOT INSTALLED |
| vLLM | NOT INSTALLED |
| LM Studio | NOT DETECTED |
| GGUF model files | NONE FOUND |
| Safetensors model files | NONE FOUND |
| `OPENAI_API_KEY` | NOT SET |
| `ASAR_OPENAI_BASE_URL` | NOT SET |
| `ASAR_MODEL_NAME` | NOT SET |
| LoRA adapters | NONE FOUND |

### Available Models

**None.** No local or remote model infrastructure is configured.

## 25.2 — Model Server Availability

All probed endpoints returned timeout or connection refused:

| Endpoint | Port | Status |
|----------|------|--------|
| Ollama | 11434 | NOT RUNNING |
| vLLM | 8000 | NOT RUNNING |
| LM Studio | 1234 | NOT RUNNING |

## 25.3 — Capability Gate Protocol (Ready for Execution)

### Operations to Test

| # | Operation | Minimum N | Scoring Method |
|---|-----------|-----------|----------------|
| 1 | Evidence interpretation | 28 | Ground-truth consistency |
| 2 | Relevant hypothesis generation | 28 | True hypothesis recovery rate |
| 3 | Alternative hypothesis generation | 28 | Novelty + evidence consistency |
| 4 | Causal/conditional reasoning | 28 | Direction correctness |
| 5 | Contradiction identification | 28 | Ground-truth contradiction match |
| 6 | Hypothesis attack / falsifier generation | 28 | Relevant falsifier rate |
| 7 | Missing-information identification | 28 | Information-value alignment |
| 8 | Targeted retrieval-query generation | 28 | Discriminating power |
| 9 | Evidence-grounded synthesis | 28 | Multi-metric composite |
| 10 | Typed structured-output compliance | 28 | JSON validity + schema match |

### Pass/Fail Threshold

- **PASS:** Mean score > 0.30 across all core operations (generate_hypothesis, reason, interpret_evidence, structured_output)
- **FAIL:** Any core operation mean ≤ 0.30 → `INVALID_EXPERIMENTAL_SUBSTRATE`

### Scoring Rubrics

#### Hypothesis Generation
- True hypothesis recovered: 0.4 weight
- Evidence consistent: 0.3 weight
- Structured output: 0.3 weight

#### Reasoning
- True hypothesis mentioned: 0.3 weight
- Correct directional assessment: 0.4 weight
- Structured output: 0.3 weight

#### Structured Output
- Is JSON: 0.3 weight
- Valid JSON: 0.4 weight
- Has required keys: 0.3 weight

## 25.4 — Operation-Level Success Definitions

### Hypothesis Generation
| Metric | Definition |
|--------|-----------|
| True recovered | ≥2 key words from true hypothesis statement appear in output |
| Novel generated | Hypothesis not identical to any visible hypothesis |
| Evidence-consistent | References at least one evidence item correctly |
| Duplicate | Repeats a previously generated hypothesis |
| Unsupported | Makes claims with no evidence basis |

### Reasoning
| Metric | Definition |
|--------|-----------|
| Valid implication | Logical step follows from premises |
| Correct causal relation | Consistency score direction matches ground truth |
| Unsupported inference | Conclusion not warranted by evidence |

### Attack
| Metric | Definition |
|--------|-----------|
| Relevant falsifier | Identifies genuine weakness in target hypothesis |
| Discriminating | Falsifier would distinguish target from alternative |
| Correct target | Attacks the specified hypothesis, not a strawman |
| Hallucinated contradiction | Invents non-existent evidence or logic error |

### Retrieval Query
| Metric | Definition |
|--------|-----------|
| Decision-relevant | Query would retrieve evidence with information_value > 0.5 |

## 25.5 — Capability Threshold

A model is classified as:
- **VALID_EXPERIMENTAL_SUBSTRATE**: All core operations above threshold
- **MARGINAL_SUBSTRATE**: 3/4 core operations pass; results flagged
- **INVALID_EXPERIMENTAL_SUBSTRATE**: <3 core operations pass; architecture results NOT valid evidence

## 25.6 — Multi-Model Protocol

If multiple models become available:
- Test each model independently through the full gate
- Report per-model capability profiles
- Analyze architecture × base-model capability interaction
- Do NOT pool results across models

## Required Action to Proceed

```bash
# Option A: Ollama
ollama pull qwen2.5:7b
ollama serve
set ASAR_OPENAI_BASE_URL=http://localhost:11434/v1
set ASAR_MODEL_NAME=qwen2.5:7b
python experiments/campaign_v5/run_phases25_26.py

# Option B: LM Studio
# Start LM Studio, load a model
set ASAR_OPENAI_BASE_URL=http://localhost:1234/v1
set ASAR_MODEL_NAME=your-model-name
python experiments/campaign_v5/run_phases25_26.py

# Option C: Remote API
set OPENAI_API_KEY=your-key
set ASAR_OPENAI_BASE_URL=https://api.openai.com/v1
set ASAR_MODEL_NAME=gpt-4o-mini
python experiments/campaign_v5/run_phases25_26.py
```
