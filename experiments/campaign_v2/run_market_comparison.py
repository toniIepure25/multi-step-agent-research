"""
Phase 15 — Market variant comparison on DEV scenarios.

Compares: original heuristic market, diversity-aware market, round-robin (no market).
Diagnoses why B1 > full_ree and whether diversity constraint helps.
"""

from __future__ import annotations

import asyncio
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from asar.evaluation.scenarios.semantic_generators import SEMANTIC_FAMILY_GENERATORS
from asar.evaluation.semantic_runner import SemanticBenchmarkRunner
from schemas.ree.epistemic_state import BudgetState, SelfModelSummary

RESULTS_DIR = Path(__file__).parent / "results"
CAMPAIGN_V2_BASE_SEED = 7777


async def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    runner = SemanticBenchmarkRunner(
        default_budget=BudgetState(max_tokens=5000, max_steps=25),
    )

    architectures = ["B0_direct", "B1_reflection", "full_ree", "B4_diversity_ree"]
    budget = BudgetState(max_tokens=5000, max_steps=25)

    sm = SelfModelSummary(
        overall_success_rate=0.6,
        operator_success_rates={
            "retrieve": 0.7, "generate_hypothesis": 0.65,
            "attack_hypothesis": 0.5, "reason": 0.6,
        },
    )

    all_results = []
    print("=" * 60)
    print("PHASE 15 — MARKET VARIANT COMPARISON")
    print("=" * 60)

    for family_name, gen_fn in SEMANTIC_FAMILY_GENERATORS.items():
        print(f"\n--- Family: {family_name} ---")
        for arch in architectures:
            qualities = []
            op_sequences = []
            for idx in range(10):
                world = gen_fn(index=idx, seed=CAMPAIGN_V2_BASE_SEED + idx)
                result = await runner.run(
                    world, architecture=arch, budget=budget, self_model=sm,
                )
                qualities.append(result.scalar_quality)
                op_sequences.append(result.operator_sequence)
                all_results.append({
                    "family": family_name,
                    "architecture": arch,
                    "world_id": result.world_id,
                    "scalar_quality": result.scalar_quality,
                    "hypothesis_count": result.hypothesis_count,
                    "ignorance_count": result.ignorance_count,
                    "evidence_count": result.evidence_count,
                    "steps": result.steps_used,
                    "tokens": result.tokens_used,
                    "operator_sequence": result.operator_sequence,
                })

            mean_q = statistics.mean(qualities)
            std_q = statistics.stdev(qualities) if len(qualities) > 1 else 0

            all_ops = []
            for seq in op_sequences:
                all_ops.extend(seq)
            op_dist = Counter(all_ops)
            total_ops = sum(op_dist.values())
            op_str = ", ".join(f"{k}:{v}" for k, v in op_dist.most_common(4))

            print(f"  {arch:25s}: q={mean_q:.4f} +/- {std_q:.4f}  ops: {op_str}")

    # Summary table
    print("\n" + "=" * 60)
    print("SUMMARY BY ARCHITECTURE")
    print("=" * 60)

    by_arch = defaultdict(list)
    for r in all_results:
        by_arch[r["architecture"]].append(r["scalar_quality"])

    for arch in architectures:
        scores = by_arch[arch]
        mean_q = statistics.mean(scores) if scores else 0
        std_q = statistics.stdev(scores) if len(scores) > 1 else 0
        print(f"  {arch:25s}: quality={mean_q:.4f} +/- {std_q:.4f} (n={len(scores)})")

    # Save detailed results
    (RESULTS_DIR / "market_comparison.json").write_text(
        json.dumps(all_results, indent=2)
    )
    print(f"\nResults saved to {RESULTS_DIR / 'market_comparison.json'}")

    # Ablation comparison: full_ree vs no_market (round-robin)
    print("\n" + "=" * 60)
    print("ABLATION: full_ree vs no_market (round-robin)")
    print("=" * 60)

    for family_name, gen_fn in SEMANTIC_FAMILY_GENERATORS.items():
        ree_q = []
        rr_q = []
        for idx in range(10):
            world = gen_fn(index=idx, seed=CAMPAIGN_V2_BASE_SEED + idx)
            ree_result = await runner.run(
                world, architecture="full_ree", budget=budget, self_model=sm,
            )
            rr_result = await runner.run(
                world, architecture="full_ree", budget=budget, self_model=sm,
                ablation={"epistemic_market": False},
            )
            ree_q.append(ree_result.scalar_quality)
            rr_q.append(rr_result.scalar_quality)

        print(f"  {family_name:25s}: market={statistics.mean(ree_q):.4f} vs round_robin={statistics.mean(rr_q):.4f}")


if __name__ == "__main__":
    asyncio.run(main())
