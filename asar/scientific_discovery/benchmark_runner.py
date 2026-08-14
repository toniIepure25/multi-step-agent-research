"""
FalsificationBench V1 Runner — executes all policies across all worlds and computes metrics.

Independent unit: WORLD × SEED
Primary outcomes: Recovery Accuracy, Refutation Sensitivity, Theory Stickiness,
                  Abandonment Latency, False-Abandonment Rate.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from asar.scientific_discovery.baselines import (
    PolicyResult,
    run_all_policies,
    run_b0_passive,
    run_b1_confirmation,
    run_b2_random_challenge,
    run_b3_falsification_first,
    run_b4_oracle,
)
from asar.scientific_discovery.controlled_worlds import (
    ControlledWorld,
    create_confirmation_trap_world,
    create_confounded_causality_world,
    create_non_identifiable_world,
)
from asar.scientific_discovery.metrics import BenchmarkMetrics, evaluate_episode
from asar.scientific_discovery.worlds_extended import (
    create_measurement_artifact_world,
    create_null_world,
    create_reverse_causality_world,
)


@dataclass
class PolicyMetrics:
    """Aggregated metrics for a single policy across worlds."""

    policy_name: str
    metrics: list[BenchmarkMetrics] = field(default_factory=list)

    @property
    def mean_recovery_accuracy(self) -> float:
        if not self.metrics:
            return 0.0
        return sum(m.recovery_accuracy for m in self.metrics) / len(self.metrics)

    @property
    def mean_refutation_sensitivity(self) -> float:
        valid = [m for m in self.metrics if m.refutation_sensitivity > 0]
        if not valid:
            return 0.0
        return sum(m.refutation_sensitivity for m in valid) / len(valid)

    @property
    def mean_theory_stickiness(self) -> float:
        valid = [m for m in self.metrics if m.theory_stickiness >= 0]
        if not valid:
            return 0.0
        return sum(m.theory_stickiness for m in valid) / len(valid)

    @property
    def conclusion_correct_rate(self) -> float:
        if not self.metrics:
            return 0.0
        return sum(1 for m in self.metrics if m.conclusion_correct) / len(self.metrics)


@dataclass
class BenchmarkReport:
    """Complete benchmark comparison report."""

    worlds_run: int
    seeds_per_world: int
    policies: dict[str, PolicyMetrics]
    world_types_run: list[str]

    def summary_table(self) -> dict[str, dict[str, float]]:
        """Generate summary table: policy → metric → value."""
        table = {}
        for name, pm in self.policies.items():
            table[name] = {
                "recovery_accuracy": pm.mean_recovery_accuracy,
                "refutation_sensitivity": pm.mean_refutation_sensitivity,
                "theory_stickiness": pm.mean_theory_stickiness,
                "conclusion_correct_rate": pm.conclusion_correct_rate,
            }
        return table


def generate_worlds(seeds: list[int]) -> list[ControlledWorld]:
    """Generate all controlled worlds across seeds."""
    worlds = []
    for seed in seeds:
        worlds.append(create_confirmation_trap_world(seed=seed))
        worlds.append(create_confounded_causality_world(seed=seed))
        worlds.append(create_non_identifiable_world(seed=seed))
        worlds.append(create_reverse_causality_world(seed=seed))
        worlds.append(create_null_world(seed=seed))
        worlds.append(create_measurement_artifact_world(seed=seed))
    return worlds


def run_benchmark(seeds: list[int] | None = None) -> BenchmarkReport:
    """Run full FalsificationBench V1 across all worlds and policies."""
    if seeds is None:
        seeds = [1, 2, 3, 4, 5]

    worlds = generate_worlds(seeds)

    policy_metrics: dict[str, PolicyMetrics] = {
        "B0_passive": PolicyMetrics(policy_name="B0_passive"),
        "B1_confirmation": PolicyMetrics(policy_name="B1_confirmation"),
        "B2_random_challenge": PolicyMetrics(policy_name="B2_random_challenge"),
        "B3_zero": PolicyMetrics(policy_name="B3_zero"),
        "B3_falsification_first": PolicyMetrics(policy_name="B3_falsification_first"),
        "B4_oracle": PolicyMetrics(policy_name="B4_oracle"),
    }

    world_types_seen: set[str] = set()

    for world in worlds:
        world_types_seen.add(world.world_type)
        results = run_all_policies(world, seed=hash(world.world_id) % 1000)

        for pr in results:
            metrics = evaluate_episode(pr.result, world)
            policy_metrics[pr.policy_name].metrics.append(metrics)

    return BenchmarkReport(
        worlds_run=len(worlds),
        seeds_per_world=len(seeds),
        policies=policy_metrics,
        world_types_run=sorted(world_types_seen),
    )
