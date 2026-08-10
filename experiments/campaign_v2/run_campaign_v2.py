"""
Scientific Campaign V2 — Semantic Epistemic Benchmark.

Uses EpistemicWorldSimulator with true causal ablation.
All results evaluated via EpistemicQualityVector against latent world ground truth.

Data splits: dev / validation / locked_test
Campaign V1 holdout is permanently contaminated (observed).
Fresh seeds and scenario instances used throughout.

Usage:
    python experiments/campaign_v2/run_campaign_v2.py
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import statistics
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from asar.evaluation.scenarios.semantic_generators import (
    SEMANTIC_FAMILY_GENERATORS,
    generate_all_semantic_worlds,
)
from asar.evaluation.semantic_runner import SemanticBenchmarkRunner, SemanticRunResult
from asar.evaluation.simulator import LatentWorld
from schemas.ree.epistemic_state import BudgetState, SelfModelSummary


CAMPAIGN_V2_BASE_SEED = 7777
DEV_SEED_OFFSET = 0
VAL_SEED_OFFSET = 1000
LOCKED_SEED_OFFSET = 2000

ARCHITECTURES = ["B0_direct", "B1_reflection", "full_ree"]

ABLATION_CONFIGS: dict[str, dict[str, bool]] = {
    "full_ree": {},
    "no_hypothesis": {"hypothesis_ecology": False},
    "no_ignorance": {"ignorance_ledger": False},
    "no_self_model": {"self_model": False},
    "no_stopping": {"stopping_policy": False},
    "no_market": {"epistemic_market": False},
    "no_hyp_no_ign": {"hypothesis_ecology": False, "ignorance_ledger": False},
}

BUDGETS = [2000, 5000, 10000, 20000]

SCENARIOS_PER_FAMILY = 20
RESULTS_DIR = Path(__file__).parent / "results"


def generate_splits() -> dict[str, list[tuple[LatentWorld, str]]]:
    """Generate dev/validation/locked_test splits with fresh seeds."""
    all_worlds = generate_all_semantic_worlds(
        count_per_family=SCENARIOS_PER_FAMILY,
        base_seed=CAMPAIGN_V2_BASE_SEED,
    )
    splits: dict[str, list[tuple[LatentWorld, str]]] = {
        "dev": [], "validation": [], "locked_test": [],
    }
    for world, split in all_worlds:
        splits[split].append((world, split))
    return splits


def hash_split(worlds: list[tuple[LatentWorld, str]]) -> str:
    """Compute a hash of the world IDs for reproducibility checking."""
    ids = sorted(w.world_id for w, _ in worlds)
    return hashlib.sha256("|".join(ids).encode()).hexdigest()[:16]


async def run_holdout_campaign(
    worlds: list[tuple[LatentWorld, str]],
    runner: SemanticBenchmarkRunner,
    budget: BudgetState,
    architectures: list[str],
) -> list[SemanticRunResult]:
    """Run all architectures on all worlds."""
    results: list[SemanticRunResult] = []
    for world, split in worlds:
        for arch in architectures:
            result = await runner.run(
                world, architecture=arch, budget=budget,
            )
            results.append(result)
    return results


async def run_ablation_campaign(
    worlds: list[tuple[LatentWorld, str]],
    runner: SemanticBenchmarkRunner,
    budget: BudgetState,
) -> list[SemanticRunResult]:
    """Run ablation conditions on all worlds."""
    results: list[SemanticRunResult] = []
    for world, split in worlds:
        for config_name, ablation in ABLATION_CONFIGS.items():
            sm = SelfModelSummary(
                overall_success_rate=0.6,
                operator_success_rates={
                    "retrieve": 0.7, "generate_hypothesis": 0.65,
                    "attack_hypothesis": 0.5, "reason": 0.6,
                },
            )
            result = await runner.run(
                world, architecture="full_ree",
                ablation=ablation, budget=budget, self_model=sm,
            )
            results.append(result)
    return results


async def run_pareto_campaign(
    worlds: list[tuple[LatentWorld, str]],
    runner: SemanticBenchmarkRunner,
) -> list[SemanticRunResult]:
    """Run at multiple budget levels for Pareto analysis."""
    results: list[SemanticRunResult] = []
    for world, split in worlds:
        for budget_tokens in BUDGETS:
            budget = BudgetState(max_tokens=budget_tokens, max_steps=30)
            for arch in ARCHITECTURES:
                result = await runner.run(
                    world, architecture=arch, budget=budget,
                )
                results.append(result)
    return results


def analyze_by_family(
    results: list[SemanticRunResult],
) -> dict[str, dict[str, Any]]:
    """Group and analyze results by scenario family and architecture."""
    by_family: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for r in results:
        parts = r.world_id.split("_")
        family = "_".join(parts[:-2]) if len(parts) > 2 else parts[0]
        by_family[family][r.architecture].append(r.scalar_quality)

    analysis: dict[str, dict[str, Any]] = {}
    for family, arch_scores in by_family.items():
        fam_analysis: dict[str, Any] = {}
        for arch, scores in arch_scores.items():
            n = len(scores)
            mean_q = statistics.mean(scores) if scores else 0
            std_q = statistics.stdev(scores) if len(scores) > 1 else 0
            fam_analysis[arch] = {
                "n": n,
                "mean_quality": round(mean_q, 4),
                "std_quality": round(std_q, 4),
                "min": round(min(scores), 4) if scores else 0,
                "max": round(max(scores), 4) if scores else 0,
            }
        analysis[family] = fam_analysis
    return analysis


def analyze_ablations(
    results: list[SemanticRunResult],
) -> dict[str, dict[str, Any]]:
    """Analyze ablation impact."""
    by_config: dict[str, list[SemanticRunResult]] = defaultdict(list)
    for r in results:
        config_key = json.dumps(r.ablation_config, sort_keys=True)
        by_config[config_key].append(r)

    analysis: dict[str, dict[str, Any]] = {}
    for config_key, runs in by_config.items():
        qualities = [r.scalar_quality for r in runs]
        tokens = [r.tokens_used for r in runs]
        hyp_counts = [r.hypothesis_count for r in runs]
        ign_counts = [r.ignorance_count for r in runs]

        analysis[config_key] = {
            "n": len(runs),
            "mean_quality": round(statistics.mean(qualities), 4) if qualities else 0,
            "std_quality": round(statistics.stdev(qualities), 4) if len(qualities) > 1 else 0,
            "mean_tokens": round(statistics.mean(tokens), 1) if tokens else 0,
            "mean_hypotheses": round(statistics.mean(hyp_counts), 2) if hyp_counts else 0,
            "mean_ignorance": round(statistics.mean(ign_counts), 2) if ign_counts else 0,
        }
    return analysis


def analyze_pareto(
    results: list[SemanticRunResult],
) -> list[dict[str, Any]]:
    """Compute quality-compute Pareto points."""
    by_arch_budget: dict[str, list[SemanticRunResult]] = defaultdict(list)
    for r in results:
        key = f"{r.architecture}_{r.budget_tokens}"
        by_arch_budget[key].append(r)

    points: list[dict[str, Any]] = []
    for key, runs in by_arch_budget.items():
        qualities = [r.scalar_quality for r in runs]
        tokens = [r.tokens_used for r in runs]
        arch = runs[0].architecture
        budget = runs[0].budget_tokens

        points.append({
            "architecture": arch,
            "budget_tokens": budget,
            "mean_quality": round(statistics.mean(qualities), 4) if qualities else 0,
            "mean_tokens_used": round(statistics.mean(tokens), 1) if tokens else 0,
            "n": len(runs),
        })

    points.sort(key=lambda p: (p["architecture"], p["budget_tokens"]))
    return points


async def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("SCIENTIFIC CAMPAIGN V2 — SEMANTIC EPISTEMIC BENCHMARK")
    print("=" * 60)

    # Generate and hash splits
    splits = generate_splits()
    split_hashes = {name: hash_split(worlds) for name, worlds in splits.items()}
    print(f"\nSplit sizes: dev={len(splits['dev'])}, val={len(splits['validation'])}, locked={len(splits['locked_test'])}")
    print(f"Split hashes: {split_hashes}")

    # Save split manifest
    manifest = {
        "base_seed": CAMPAIGN_V2_BASE_SEED,
        "scenarios_per_family": SCENARIOS_PER_FAMILY,
        "families": list(SEMANTIC_FAMILY_GENERATORS.keys()),
        "split_sizes": {k: len(v) for k, v in splits.items()},
        "split_hashes": split_hashes,
        "architectures": ARCHITECTURES,
        "budgets": BUDGETS,
        "ablation_configs": ABLATION_CONFIGS,
    }
    (RESULTS_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))

    runner = SemanticBenchmarkRunner()
    default_budget = BudgetState(max_tokens=5000, max_steps=25)

    # --- Dev Campaign ---
    print("\n--- DEV CAMPAIGN (tuning allowed) ---")
    dev_holdout = await run_holdout_campaign(
        splits["dev"], runner, default_budget, ARCHITECTURES,
    )
    print(f"  Dev holdout: {len(dev_holdout)} runs")

    dev_analysis = analyze_by_family(dev_holdout)
    (RESULTS_DIR / "dev_family_analysis.json").write_text(json.dumps(dev_analysis, indent=2))

    # Print dev quality by architecture
    for family, archs in dev_analysis.items():
        print(f"\n  Family: {family}")
        for arch, stats in archs.items():
            print(f"    {arch}: quality={stats['mean_quality']:.4f} ± {stats['std_quality']:.4f} (n={stats['n']})")

    # --- Ablation Campaign on Dev ---
    print("\n--- ABLATION CAMPAIGN (dev) ---")
    dev_ablations = await run_ablation_campaign(splits["dev"], runner, default_budget)
    print(f"  Ablation runs: {len(dev_ablations)}")

    abl_analysis = analyze_ablations(dev_ablations)
    (RESULTS_DIR / "dev_ablation_analysis.json").write_text(json.dumps(abl_analysis, indent=2))

    for config, stats in abl_analysis.items():
        print(f"  {config}: quality={stats['mean_quality']:.4f}, hyps={stats['mean_hypotheses']:.1f}, ign={stats['mean_ignorance']:.1f}")

    # --- Pareto Campaign on Dev ---
    print("\n--- PARETO CAMPAIGN (dev) ---")
    dev_pareto = await run_pareto_campaign(splits["dev"], runner)
    print(f"  Pareto runs: {len(dev_pareto)}")

    pareto_points = analyze_pareto(dev_pareto)
    (RESULTS_DIR / "dev_pareto_analysis.json").write_text(json.dumps(pareto_points, indent=2))

    print("\n  Quality-Compute Pareto Points:")
    for pt in pareto_points:
        print(f"    {pt['architecture']:20s} budget={pt['budget_tokens']:6d} quality={pt['mean_quality']:.4f} tokens={pt['mean_tokens_used']:.0f}")

    # --- Validation Campaign ---
    print("\n--- VALIDATION CAMPAIGN ---")
    val_holdout = await run_holdout_campaign(
        splits["validation"], runner, default_budget, ARCHITECTURES,
    )
    val_analysis = analyze_by_family(val_holdout)
    (RESULTS_DIR / "validation_family_analysis.json").write_text(json.dumps(val_analysis, indent=2))
    print(f"  Validation holdout: {len(val_holdout)} runs")

    # --- LOCKED TEST (run once, do not re-analyze) ---
    print("\n--- LOCKED TEST CAMPAIGN ---")
    locked_holdout = await run_holdout_campaign(
        splits["locked_test"], runner, default_budget, ARCHITECTURES,
    )
    locked_analysis = analyze_by_family(locked_holdout)
    (RESULTS_DIR / "locked_test_analysis.json").write_text(json.dumps(locked_analysis, indent=2))
    print(f"  Locked test: {len(locked_holdout)} runs")

    # Save all raw records
    all_records = dev_holdout + dev_ablations + dev_pareto + val_holdout + locked_holdout
    records_path = RESULTS_DIR / "all_records.jsonl"
    with open(records_path, "w") as f:
        for r in all_records:
            f.write(json.dumps(r.to_dict()) + "\n")
    print(f"\nTotal records: {len(all_records)} -> {records_path}")

    print("\n" + "=" * 60)
    print("CAMPAIGN V2 COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
