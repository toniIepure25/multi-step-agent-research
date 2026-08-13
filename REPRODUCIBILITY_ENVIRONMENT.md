# Reproducibility Environment

## Tested Environment

- **Python:** 3.11+
- **OS:** Windows 10 (10.0.19045), also tested on macOS 14.x
- **Package manager:** pip / uv

## Replay (No LLM Required)

Replay mode reproduces all statistics, tables, and figures from frozen inference traces. No API access or model inference is needed.

```bash
# Install dependencies
pip install matplotlib

# Run full test suite
python -m pytest -x -q

# Reproduce all paper artifacts
python paper/scripts/reproduce_all.py

# Generate figures
python paper/scripts/generate_figures.py

# Generate tables
python paper/scripts/generate_tables.py

# Verify freeze integrity
python _verify_freeze.py
```

## Live Inference (Optional)

To re-run the experiments from scratch, you need:

1. An OpenAI-compatible inference endpoint serving:
   - `gemma3:27b-it-qat`
   - `llama3.2-vision:11b-instruct-q8_0`
   - `nomic-embed-text:latest`

2. Set the endpoint in environment or modify `run.py`:
   ```
   INFERENCE_ENDPOINT=http://localhost:11434/v1
   ```

3. Install Ollama and pull models:
   ```bash
   ollama pull gemma3:27b-it-qat
   ollama pull llama3.2-vision:11b-instruct-q8_0
   ollama pull nomic-embed-text
   ```

4. Run:
   ```bash
   python experiments/paper_validation/run.py --dataset scifact --mode locked --model gemma3:27b-it-qat
   python experiments/paper_validation/run.py --dataset hotpotqa --mode locked --model gemma3:27b-it-qat
   ```

## Key Dependencies

- `matplotlib` (figures only)
- Standard library only for statistics/analysis

## Trace Integrity

All raw traces are stored in `experiments/paper_validation/results/raw/` with SHA256 hashes verified by `_verify_freeze.py`. The preregistration was committed at SHA `8950ba9` before any locked inference.
