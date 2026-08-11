# Primary Model Selection Record

**Campaign:** V5
**Date:** 2026-08-10
**Selection Timestamp:** Before Phase 25 capability gate execution

## Candidate Models Discovered

| Model | Family | Size | Quant | Generation | Smoke Test |
|-------|--------|------|-------|------------|------------|
| gemma3:27b-it-qat | Gemma 3 | 27.4B | Q4_0 | Yes | PASSED |
| llama3.2-vision:11b-instruct-q8_0 | Llama 3.2 | 10.7B | Q8_0 | Yes | PASSED |
| nomic-embed-text:latest | BERT | 137M | F16 | No | N/A |
| mxbai-embed-large:latest | BERT | 334M | F16 | No | N/A |

## Selection Criterion

Models selected based on:
1. Generation capability (must support chat completions)
2. Instruction-following ability (verified via smoke test)
3. Scientific usefulness for cognitive operation evaluation
4. Availability of two different capability levels for transfer analysis

## Selected Models

### Model A — PRIMARY: gemma3:27b-it-qat
- **Rationale:** Largest available model (27.4B). Gemma 3 is a strong instruction-following model. QAT quantization preserves capability better than post-training quantization. Best candidate for demonstrating cognitive operation capability.
- **Capability gate:** To be determined by Phase 25

### Model B — TRANSFER: llama3.2-vision:11b-instruct-q8_0
- **Rationale:** Different model family (Llama vs Gemma), different parameter scale (10.7B vs 27.4B), different quantization (Q8_0 vs Q4_0). Provides a meaningful capability contrast for testing architecture × model interaction.
- **Capability gate:** To be determined by Phase 25

## Confirmation

- [x] All candidate models discovered and documented
- [x] Capability-tested candidates identified by smoke test only
- [x] Selection based on capability criteria, NOT on Phase 26 outcomes
- [x] Phase 26 locked results have NOT been examined
- [x] Selection frozen before capability gate execution

## Generation Configuration (Frozen)

| Parameter | Value |
|-----------|-------|
| temperature | 0.0 (deterministic) |
| max_tokens | 512 (operations), 256 (structured output) |
| top_p | (server default) |
| seed | Not supported by Ollama backend |
| stream | false |
| timeout | 120s |
| retry_policy | Network/timeout: retry 1x; Semantic failure: no retry |
| concurrency | Sequential (1 request at a time) |
