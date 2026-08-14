# Remote Provider Discovery — Stage 3C

## Discovery Date
2026-08-14

## Base URL
```
https://inference.ccrolabs.com
```

## Working Endpoints

| Endpoint | Protocol | Status |
|----------|----------|--------|
| `GET /api/tags` | Ollama native | WORKING |
| `GET /v1/models` | OpenAI-compatible | WORKING |
| `POST /v1/chat/completions` | OpenAI-compatible | WORKING |

## Provider Protocol
Dual-interface: Ollama native + OpenAI-compatible layer.

The `/v1/chat/completions` endpoint accepts standard OpenAI chat format and returns
standard OpenAI-compatible responses with `usage` metadata.

## Response Schema (v1/chat/completions)
```json
{
  "id": "chatcmpl-<N>",
  "object": "chat.completion",
  "created": <unix_timestamp>,
  "model": "<model_name>",
  "system_fingerprint": "fp_ollama",
  "choices": [{
    "index": 0,
    "message": {"role": "assistant", "content": "<text>"},
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": <N>,
    "completion_tokens": <N>,
    "total_tokens": <N>
  }
}
```

## Timeout Behavior
- Default server timeout: appears unlimited (completions for 27B model take 5-35s)
- Client timeout recommended: 120s

## Usage Metadata Availability
- `prompt_tokens`: YES
- `completion_tokens`: YES  
- `total_tokens`: YES
- `eval_count`/`prompt_eval_count`: available via Ollama native API (not tested)

## Critical Note: User-Agent Required
Python's `urllib` default user-agent receives HTTP 403. 
Requests must include a `User-Agent` header (e.g., `ASAR/1.0`).

## Available Models (at discovery time)
1. `gemma3:27b-it-qat` — 27.4B params, Q4_0, Gemma3 family
2. `llama3.2-vision:11b-instruct-q8_0` — 10.7B params, Q8_0, MLlama family
3. `nomic-embed-text:latest` — 137M params, F16, embedding only
4. `mxbai-embed-large:latest` — 334M params, F16, embedding only
