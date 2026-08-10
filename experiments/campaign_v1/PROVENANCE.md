# Campaign V1 — Structural/Methodological Negative Baseline

**Immutable endpoint SHA**: `120a576`
**Branch**: `feature/asar-ree-v2`
**Date**: 2026-08-10

## Status: FROZEN — Do not modify

This campaign established that under content-independent mock operators
with coarse substring quality evaluation, all tested architectures achieve
identical 33% ground-truth accuracy. B0 (Direct) Pareto-dominates.

## Key findings preserved in experiments/campaign/results/:
- holdout_records.jsonl (600 records)
- ablation_records.jsonl (162 records)
- counterfactual_outcomes.jsonl (2,100 records)
- family_analysis.json, pairwise_comparisons.json, pareto_data.json

## Reports:
- experiments/ree_scientific_certification/FINAL_REPORT.md
- experiments/ree_scientific_certification/NEGATIVE_FINDINGS.md
- experiments/protocols/FROZEN_PROTOCOL.md

## Correct interpretation:
> Under a content-independent deterministic mock environment with coarse
> substring evaluation, all tested architectures achieved identical measured
> quality while REE consumed more compute; therefore Direct was Pareto-optimal
> under that specific measurement regime.

This does NOT demonstrate that Direct prompting is universally superior.
It demonstrates that the measurement regime was non-discriminative.
