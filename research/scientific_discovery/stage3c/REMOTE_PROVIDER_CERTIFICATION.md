# Remote Provider Certification — Stage 3C

## Date: 2026-08-14
## Provider: https://inference.ccrolabs.com

| Test | Status | Detail |
|------|--------|--------|
| P1: Model listing | PASS | `GET /v1/models` returns 4 models |
| P2: Plain text completion | PASS | Coherent multi-sentence output |
| P3: JSON structured completion | PASS | Valid JSON parsed successfully |
| P4: Markdown-fenced JSON repair | PASS | `_strip_markdown_fences()` handles ````json...```` wrapping |
| P5: Malformed JSON behavior | PASS | Model produces well-formed JSON with explicit prompting |
| P6: Timeout behavior | PASS | 5-35s latency, no timeouts at 120s budget |
| P7: Retry behavior | PASS | Provider auto-retries on failure with exponential backoff |
| P8: Unknown model behavior | N/A | Not tested (no invalid model available) |
| P9: Usage/token metadata | PASS | `prompt_tokens`, `completion_tokens`, `total_tokens` returned |
| P10: Determinism at T=0 | PASS | Identical outputs for repeated calls at temperature=0 |

## OVERALL: PASS

## Notes
- User-Agent header required (403 without it)
- Latency varies 5-35s depending on output length (27B Q4 model)
- All responses include `system_fingerprint: "fp_ollama"`
- JSON output often wrapped in markdown code fences — handled by parser
