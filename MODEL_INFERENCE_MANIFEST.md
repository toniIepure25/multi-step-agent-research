# Model Inference Manifest

## Remote Service

| Field | Value |
|-------|-------|
| Endpoint | `https://inference.ccrolabs.com/v1` |
| Backend | Ollama on Mac Studio |
| Proxy | Cloudflare |
| API type | OpenAI-compatible |
| Authentication | None required |

## Primary Model (V5-V6)

| Field | Value |
|-------|-------|
| Model ID | `gemma3:27b-it-qat` |
| Family | Gemma 3 |
| Parameters | 27B |
| Quantization | QAT (Quantization-Aware Training) |
| Context length | 8192 (used) |
| Temperature | 0.0 |
| Max output tokens | 512 (operations), 256 (structured) |
| Timeout | 120s |
| Retry policy | Network errors only; no semantic retries |

## Transfer Model (V5-V6)

| Field | Value |
|-------|-------|
| Model ID | `llama3.2-vision:11b-instruct-q8_0` |
| Family | Llama 3.2 (mllama) |
| Parameters | 11B |
| Quantization | Q8_0 |
| Context length | 8192 (used) |
| Temperature | 0.0 |
| Max output tokens | 512 |

## Generation Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| temperature | 0.0 | Deterministic generation for reproducibility |
| top_p | 1.0 (default) | No nucleus sampling at temp 0 |
| seed | Not set (Ollama nondeterminism) | Documented as limitation |

## Concurrency

Sequential requests only during scientific execution.
No parallel model loading.

## Cost

Monetary API cost: $0 (private infrastructure).
Compute consumption recorded per-call: input_tokens, output_tokens, latency.

## Credentials

No credentials committed or logged.
Service accessible without authentication from authorized networks.
