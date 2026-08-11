# Remote Model Inventory

**Service:** https://inference.ccrolabs.com/
**Backend:** Ollama (behind Cloudflare proxy)
**Discovery Date:** 2026-08-10
**Endpoints Verified:** `/v1/models` (OpenAI-compatible), `/api/tags` (Ollama-native), `/api/ps` (loaded models)

## Discovered Models

| # | Model ID | Family | Parameters | Quantization | Format | Type | Suitable |
|---|----------|--------|-----------|--------------|--------|------|----------|
| 1 | `gemma3:27b-it-qat` | Gemma 3 | 27.4B | Q4_0 | GGUF | Generation | YES |
| 2 | `llama3.2-vision:11b-instruct-q8_0` | Llama 3.2 (mllama) | 10.7B | Q8_0 | GGUF | Generation (multimodal) | YES |
| 3 | `nomic-embed-text:latest` | Nomic-BERT | 137M | F16 | GGUF | Embedding | NO |
| 4 | `mxbai-embed-large:latest` | BERT | 334M | F16 | GGUF | Embedding | NO |

## Model Details

### gemma3:27b-it-qat (Model A — PRIMARY CANDIDATE)
- **Digest:** `29eb0b9aeda35295ed728124d341b27e0c6771ea5c586fcabfb157884224fa93`
- **Size on disk:** 18.1 GB
- **Modified:** 2025-09-08
- **Capabilities:** Instruction-following, reasoning, structured output, multilingual
- **Quantization:** Q4_0 (4-bit quantized with QAT — quantization-aware training)
- **Context length:** Standard Gemma 3 context
- **Smoke test:** PASSED (correct arithmetic, JSON compliance, ~30s latency)

### llama3.2-vision:11b-instruct-q8_0 (Model B — TRANSFER CANDIDATE)
- **Digest:** `a5b7471a68aad08b09bc1e6203d895ff89410a7d04a1d04a328dcdf80576a23d`
- **Size on disk:** 12.3 GB
- **Modified:** 2026-04-21
- **Capabilities:** Instruction-following, reasoning, vision (text+image), structured output
- **Quantization:** Q8_0 (8-bit quantization — higher precision per parameter)
- **Context length:** Standard Llama 3.2 context (128K)
- **Smoke test:** PASSED (correct arithmetic, ~30s latency)

## API Configuration

| Setting | Value |
|---------|-------|
| OpenAI-compatible base URL | `https://inference.ccrolabs.com/v1` |
| Ollama-native base URL | `https://inference.ccrolabs.com/api` |
| Authentication | Not required (open access from current network) |
| Cloudflare proxy | Active — requires non-default User-Agent header |
| Streaming | Available but not used for experiments |
| Typical latency | 30-60 seconds per request |

## Notes

- Embedding models (nomic-embed-text, mxbai-embed-large) are not suitable for generation tasks
- Two generation-capable models from different families at different capability levels — ideal for two-model protocol
- The Q4_0 quantization on gemma3 uses QAT (quantization-aware training), which typically preserves more capability than post-training quantization
- The Q8_0 quantization on llama3.2-vision is higher precision but the base model is smaller
