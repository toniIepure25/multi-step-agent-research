# Limitations

1. **Synthetic controlled environment.** All controlled experiments use a semantic epistemic world simulator, not live information-seeking tasks. The simulator enables counterfactual evaluation but introduces design assumptions about evidence structure, hypothesis space, and quality measurement that may not hold in unconstrained settings.

2. **Only two LLM substrates.** LLM replication used Gemma 3 27B (Q4_0) and Llama 3.2 11B (Q8_0), both served from the same Ollama backend. Results may not generalize to frontier-class models, API-served models, or architectures with substantially different reasoning characteristics.

3. **Limited static real-evidence evaluation.** Phase 27 used only 14 fully-specified evidence packs across 6 domains. This sample size limits statistical power for detecting small but real condition effects. The condition range of 0.030 may reflect insufficient task difficulty or strategy pressure rather than true non-transfer.

4. **No live-web replication.** We did not evaluate cognitive sequences on live information retrieval tasks with dynamic, noisy, or adversarial evidence. Transfer to production research settings remains untested.

5. **Adaptive policy failure.** The learned motif controller used transparent rule-based features and produced only 2 distinct trajectories across 56 worlds. More expressive policy classes (neural, tree-based) with richer state representations might succeed where the tested controller failed. We cannot conclude that adaptive control is impossible, only that our specific approach failed.

6. **Finite operation vocabulary.** We tested four primitive cognitive operations (retrieve, generate_hypothesis, attack_hypothesis, reason). Real research agents may employ a broader repertoire. Complementarity patterns may differ with additional operation types.

7. **Quality metric dependence.** Epistemic quality is measured via a composite scalar combining hypothesis correctness, evidence coverage, and calibration. Different scalarizations might yield different complementarity patterns. The absolute quality values are benchmark-specific and not directly comparable to external metrics.

8. **No Level 3 replication.** No finding achieves Level 3 (static real-evidence replicated) status. The strongest claims remain at Level 2 (LLM-replicated in controlled environments).

9. **Possible internal-reasoning confound.** Modern LLMs may perform implicit hypothesis generation, reasoning, or self-critique within a single forward pass. Explicit cognitive operations may partially duplicate internal model computation, potentially explaining the weak sequence superiority finding under LLM execution.

10. **Benchmark design assumptions.** The epistemic regime generators, hypothesis structures, and evidence dependencies were designed by the experimenters. The distribution of tasks may not represent the natural distribution of research problems encountered by deployed agents.

11. **Deterministic simulator scoring.** In Phase 26, quality scores come from the deterministic simulator regardless of LLM output content. This confirms structural invariance but means we cannot measure whether LLM execution quality modulates sequence effects.

12. **Remote inference reproducibility.** The remote Mac Studio inference service may not be permanently available. Model weights are identified by Ollama digest but exact reproduction requires the same quantization, runtime, and hardware.
