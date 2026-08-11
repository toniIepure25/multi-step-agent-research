# Table 4: LLM Capability Gate Results (V5 Phase 25, N = 24 worlds per model)

| Operation | Gemma 3 27B QAT | Llama 3.2 11B Q8_0 | Threshold | Status |
|-----------|----------------|-------------------|-----------|--------|
| Evidence interpretation | 1.000 | 1.000 | 0.30 | PASS |
| Hypothesis generation | 0.750 | 0.733 | 0.30 | PASS |
| Alternative hypothesis | 0.800 | 0.833 | 0.30 | PASS |
| Causal/conditional reasoning | 0.929 | 0.950 | 0.30 | PASS |
| Contradiction identification | 1.000 | 1.000 | 0.30 | PASS |
| Attack / falsification | 1.000 | 1.000 | 0.30 | PASS |
| Missing-information identification | 1.000 | 1.000 | 0.30 | PASS |
| Retrieval query generation | 1.000 | 1.000 | 0.30 | PASS |
| Evidence-grounded synthesis | 1.000 | 1.000 | 0.30 | PASS |
| Structured output compliance | 1.000 | 1.000 | 0.30 | PASS |

*Both models classified as VALID_EXPERIMENTAL_SUBSTRATE. Rubric scores measure keyword presence, JSON compliance, and ground-truth alignment — they are not deep semantic evaluations. Source: `campaign_v5/results/phase25_gate_gemma3.json`, `phase25_gate_llama3_2-vision.json`.*

**Model specifications:**
- Gemma 3 27B: 27.4B parameters, Q4_0 quantization, GGUF format, Ollama on Mac Studio
- Llama 3.2 Vision 11B: 10.7B parameters, Q8_0 quantization, GGUF format, Ollama on Mac Studio
- Configuration: temperature = 0, max_tokens = 512 (operations) / 1024 (synthesis)
