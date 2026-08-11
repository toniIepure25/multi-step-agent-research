# Reproducibility Guide

## Overview

This document describes how to reproduce all experiments reported in the paper.

## Requirements

- Python 3.11+
- Package manager: `uv` (recommended) or `pip`
- For LLM experiments: OpenAI-compatible inference endpoint

## Installation

```bash
git clone https://github.com/toniIepure25/LLMs-multi-step-research-agents.git
cd LLMs-multi-step-research-agents
git checkout feature/asar-ree-v2
uv sync
```

## Experiment Reproduction

### 1. Controlled Simulator Experiments (No LLM Required)

**Benchmark identifiability (Experiment A):**
```bash
python experiments/campaign/run_full_campaign.py
```
Reproduces V1/V2 results: B1 vs Full REE comparison.

**Complementarity analysis (Experiments B-D):**
```bash
python experiments/campaign_v3/run_campaign_v3.py
python experiments/campaign_v4/run_campaign_v4.py
```
Reproduces V3 complementarity (+0.228) and V4 pairwise matrix.

**Adaptive necessity and policy (Experiments E-F):**
```bash
python experiments/campaign_v4/run_campaign_v4.py
```
Reproduces adaptivity gap (0.096) and policy failure results.

### 2. LLM Replication (Requires Inference Endpoint)

**Setup:**
```bash
export ASAR_OPENAI_BASE_URL="https://your-endpoint/v1"
export ASAR_MODEL_NAME="your-model-id"
```

**Run Phase 25 (capability gate) + Phase 26 (replication):**
```bash
python experiments/campaign_v5/run_v5_execution.py --phase 25
python experiments/campaign_v5/run_v5_execution.py --phase 26
```

**Original execution used:**
- Remote: `https://inference.ccrolabs.com/v1`
- Primary: `gemma3:27b-it-qat` (Ollama, Mac Studio)
- Transfer: `llama3.2-vision:11b-instruct-q8_0` (Ollama, Mac Studio)
- Temperature: 0
- Max tokens: 512 (operations), 1024 (synthesis)

### 3. Static Real-Evidence (Requires Inference Endpoint)

```bash
python experiments/campaign_v5/run_v5_execution.py --phase 27
```

Evidence packs are in `experiments/campaign_v5/evidence_packs/`.

### 4. Test Suite

```bash
uv run pytest  # or: python -m pytest
```

Expected: 446 passed, 1 skipped, 0 failed.

## Configuration

| Parameter | V3 | V4 | V5 (LLM) |
|-----------|----|----|-----------|
| Dev worlds | 50 | 56 | 24 (Phase 25), 16 (Phase 26) |
| Regimes | 1 | 8 | 8 |
| Seeds per regime | 50 | 7 | 2-3 |
| Base seed | 42 | 271828 | 272028 |
| Token budget | 3500 | 3500 | 512/1024 per op |
| Evaluation | Deterministic | Deterministic | Deterministic (simulator) |

## Seed Reproducibility

All experiments use deterministic seeds. Results are reproducible within the same Python version (3.11+). Cross-version reproducibility is not guaranteed due to potential changes in random number generation.

## Remote LLM Dependency

Phase 26 and 27 results depend on a specific remote inference service that may not be permanently available. To reproduce:

1. Deploy the same model weights (identified by Ollama digest in `experiments/campaign_v5/results/remote_models.json`)
2. Use temperature=0 and matching generation parameters
3. Exact numerical reproduction is not guaranteed due to model nondeterminism, but qualitative patterns should replicate

## Result Verification

All headline numbers can be verified from raw JSON/JSONL artifacts in `experiments/campaign_*/results/`. See `paper/PAPER_RESULT_PROVENANCE.md` for the exact field paths.

## Known Issues

- Phase 25 evidence_interpretation was initially scored with a JSON-compliance rubric inappropriate for natural-language output. Corrected scores use a substance-and-relevance rubric. Both original and corrected scores are preserved. See `_rescore_p25.py`.
- Python stdout buffering caused output delays during V5 execution. Fixed with `functools.partial(print, flush=True)`.
- Cloudflare proxy on remote inference required custom User-Agent header (`ASAR-REE/1.0`).
