"""
Phases 17-18 — B1 Decomposition, Ecology Cross-Architecture, and Temporal Complementarity.

Phase 17: Isolate what actually works
  - B1 sequence decomposition (which steps matter?)
  - Hypothesis ecology outside Full REE (does it help B0/B1?)
  - Derive REE-Minimal-Empirical

Phase 18: Temporal complementarity of cognition
  - Sequence-level counterfactual forking
  - Cognitive complementarity measurement
  - Order effects
  - Attack operator state-dependence
  - Cognitive motif discovery
"""

from __future__ import annotations

import asyncio
import json
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from asar.common import generate_id
from asar.epistemic.reducer import StateReducer
from asar.epistemic.store import AppendOnlyEventStore
from asar.evaluation.scenarios.semantic_generators import SEMANTIC_FAMILY_GENERATORS
from asar.evaluation.semantic_runner import (
    SemanticBenchmarkRunner,
    SemanticRunResult,
    SimAttackOperator,
    SimHypothesisOperator,
    SimReasonOperator,
    SimRetrieveOperator,
)
from asar.evaluation.simulator import (
    EpistemicQualityVector,
    EpistemicWorldSimulator,
    LatentWorld,
)
from asar.metacognition.controller import EpistemicController
from asar.metacognition.market import EpistemicMarket
from asar.metacognition.stopping import StoppingPolicy
from asar.operators.registry import OperatorRegistry
from asar.operators.stop import StopOperator
from schemas.ree.epistemic_state import BudgetState, SelfModelSummary

RESULTS_DIR = Path(__file__).parent / "results"
V3_BASE_SEED = 31415

# ---------------------------------------------------------------
# Fixed-sequence runner (Phase 17.1)
# ---------------------------------------------------------------

def run_fixed_sequence(
    world: LatentWorld,
    sequence: list[str],
    *,
    seed: int = 42,
) -> SemanticRunResult:
    """Execute a fixed cognitive sequence without any market/controller."""
    sim = EpistemicWorldSimulator(world, seed=seed)
    ev_ids: list[str] = []
    hyps: dict[str, float] = {}
    ignorance_items: list[dict] = []
    evidence_sources: dict[str, str | None] = {}
    tokens = 0
    executed = []

    for op_name in sequence:
        if op_name == "retrieve":
            ev = sim.retrieve("")
            if ev:
                ev_ids.append(ev["evidence_id"])
                evidence_sources[ev["source_id"]] = ev.get("parent_source")
            tokens += 500
            executed.append("retrieve")

        elif op_name == "generate_hypothesis":
            h = sim.generate_hypothesis(ev_ids)
            if h:
                hyps[h["hypothesis_id"]] = h["initial_plausibility"]
            tokens += 500
            executed.append("generate_hypothesis")

        elif op_name == "attack_hypothesis":
            targets = list(hyps.keys())
            if targets:
                result = sim.attack_hypothesis(targets[0])
                ignorance_items.extend(result.get("ignorance_items", []))
            tokens += 500
            executed.append("attack_hypothesis")

        elif op_name == "reason":
            if hyps and ev_ids:
                reasoning = sim.reason(list(hyps.keys()), ev_ids)
                for hid, score in reasoning["consistency_scores"].items():
                    if hid in hyps:
                        hyps[hid] = score
            tokens += 500
            executed.append("reason")

    identified_hidden = set()
    for item in ignorance_items:
        desc = item.get("description", "").lower()
        for hv_id in world.hidden_variables:
            if hv_id.lower() in desc:
                identified_hidden.add(hv_id)

    quality = sim.evaluate(hyps, identified_hidden, set(), evidence_sources)

    return SemanticRunResult(
        world_id=world.world_id,
        architecture=f"seq_{'_'.join(sequence[:4])}",
        ablation_config={},
        budget_tokens=tokens,
        quality=quality,
        scalar_quality=quality.scalar_quality(),
        steps_used=len(executed),
        tokens_used=tokens,
        hypothesis_count=len(hyps),
        ignorance_count=len(ignorance_items),
        evidence_count=len(ev_ids),
        operator_sequence=executed,
    )


# ---------------------------------------------------------------
# B1 decomposition sequences (Phase 17.1)
# ---------------------------------------------------------------

B1_VARIANTS = {
    "B1_full":       ["retrieve", "generate_hypothesis", "retrieve", "generate_hypothesis", "reason"],
    "B1_no_1st_ret": ["generate_hypothesis", "retrieve", "generate_hypothesis", "reason"],
    "B1_no_2nd_ret": ["retrieve", "generate_hypothesis", "generate_hypothesis", "reason"],
    "B1_one_hyp":    ["retrieve", "generate_hypothesis", "retrieve", "reason"],
    "B1_no_reason":  ["retrieve", "generate_hypothesis", "retrieve", "generate_hypothesis"],
    "B1_reversed":   ["reason", "generate_hypothesis", "retrieve", "generate_hypothesis", "retrieve"],
    "B1_ret_only":   ["retrieve", "retrieve", "retrieve", "retrieve", "retrieve"],
    "B1_hyp_ret_reason": ["generate_hypothesis", "retrieve", "reason"],
    "B1_ret_hyp_ret_hyp_atk_reason": ["retrieve", "generate_hypothesis", "retrieve", "generate_hypothesis", "attack_hypothesis", "reason"],
    "B1_extended":   ["retrieve", "generate_hypothesis", "retrieve", "generate_hypothesis", "reason", "retrieve", "reason"],
}

# ---------------------------------------------------------------
# Phase 18: Cognitive sequence pairs for complementarity
# ---------------------------------------------------------------

SEQUENCE_PAIRS = {
    "hyp_then_ret": (["generate_hypothesis", "retrieve"], ["retrieve", "generate_hypothesis"]),
    "ret_then_reason": (["retrieve", "reason"], ["reason", "retrieve"]),
    "hyp_then_reason": (["generate_hypothesis", "reason"], ["reason", "generate_hypothesis"]),
    "atk_then_reason": (["attack_hypothesis", "reason"], ["reason", "attack_hypothesis"]),
    "ret_hyp_reason_vs_ret_ret_reason": (
        ["retrieve", "generate_hypothesis", "reason"],
        ["retrieve", "retrieve", "reason"],
    ),
    "hyp_ret_reason_vs_ret_hyp_reason": (
        ["generate_hypothesis", "retrieve", "reason"],
        ["retrieve", "generate_hypothesis", "reason"],
    ),
}

SINGLE_ACTIONS = ["retrieve", "generate_hypothesis", "attack_hypothesis", "reason"]

# ---------------------------------------------------------------
# Generate V3 worlds
# ---------------------------------------------------------------

def generate_v3_worlds(count_per_family: int = 20) -> dict[str, list[LatentWorld]]:
    """Generate fresh V3 worlds with new seeds, split into dev/validation/locked."""
    splits: dict[str, list[LatentWorld]] = {"dev": [], "validation": [], "locked_test": []}
    for family_name, gen_fn in SEMANTIC_FAMILY_GENERATORS.items():
        for i in range(count_per_family):
            if i < count_per_family // 2:
                split = "dev"
            elif i < int(count_per_family * 0.75):
                split = "validation"
            else:
                split = "locked_test"
            world = gen_fn(index=i, seed=V3_BASE_SEED + i)
            splits[split].append(world)
    return splits


# ---------------------------------------------------------------
# Phase 17.1: B1 decomposition
# ---------------------------------------------------------------

async def run_b1_decomposition(dev_worlds: list[LatentWorld]) -> dict[str, Any]:
    """Test which steps of B1 contribute to quality."""
    results: dict[str, list[float]] = defaultdict(list)
    detailed: list[dict] = []

    for world in dev_worlds:
        for name, seq in B1_VARIANTS.items():
            result = run_fixed_sequence(world, seq)
            results[name].append(result.scalar_quality)
            detailed.append({
                "world_id": world.world_id,
                "variant": name,
                "sequence": seq,
                "scalar_quality": result.scalar_quality,
                "hypothesis_count": result.hypothesis_count,
                "evidence_count": result.evidence_count,
                "tokens": result.tokens_used,
            })

    summary = {}
    for name, scores in sorted(results.items()):
        mean = statistics.mean(scores)
        std = statistics.stdev(scores) if len(scores) > 1 else 0
        summary[name] = {"mean": round(mean, 4), "std": round(std, 4), "n": len(scores)}

    return {"summary": summary, "detailed": detailed}


# ---------------------------------------------------------------
# Phase 17.2: Ecology across architectures
# ---------------------------------------------------------------

async def run_ecology_cross_architecture(dev_worlds: list[LatentWorld]) -> dict[str, Any]:
    """Test hypothesis ecology in B0/B1 contexts (not just Full REE)."""
    runner = SemanticBenchmarkRunner(
        default_budget=BudgetState(max_tokens=5000, max_steps=25),
    )
    results: dict[str, list[float]] = defaultdict(list)

    for world in dev_worlds:
        # B0 (no ecology)
        r = await runner.run(world, architecture="B0_direct")
        results["B0"].append(r.scalar_quality)

        # B1 (no ecology — fixed sequence uses sim directly, always has hypothesis generation)
        r = await runner.run(world, architecture="B1_reflection")
        results["B1"].append(r.scalar_quality)

        # B1 + extra hypothesis generation (simulating ecology effect)
        seq_ecology = ["retrieve", "generate_hypothesis", "retrieve", "generate_hypothesis",
                       "generate_hypothesis", "reason"]
        r = run_fixed_sequence(world, seq_ecology)
        results["B1_plus_ecology"].append(r.scalar_quality)

        # Full REE with ecology
        r = await runner.run(world, architecture="full_ree",
                             ablation={"hypothesis_ecology": True})
        results["full_ree_with_ecology"].append(r.scalar_quality)

        # Full REE without ecology
        r = await runner.run(world, architecture="full_ree",
                             ablation={"hypothesis_ecology": False})
        results["full_ree_no_ecology"].append(r.scalar_quality)

        # Fixed sequence without any hypothesis generation
        r = run_fixed_sequence(world, ["retrieve", "retrieve", "retrieve", "reason"])
        results["no_hypothesis_fixed"].append(r.scalar_quality)

    summary = {}
    for name, scores in sorted(results.items()):
        mean = statistics.mean(scores)
        std = statistics.stdev(scores) if len(scores) > 1 else 0
        summary[name] = {"mean": round(mean, 4), "std": round(std, 4), "n": len(scores)}

    return {"summary": summary}


# ---------------------------------------------------------------
# Phase 18.2-18.4: Sequence complementarity and order effects
# ---------------------------------------------------------------

def run_sequence_complementarity(dev_worlds: list[LatentWorld]) -> dict[str, Any]:
    """Measure whether sequence value differs from sum of primitive values."""
    outcomes: list[dict] = []

    for world in dev_worlds:
        # Single-action values
        single_values = {}
        for action in SINGLE_ACTIONS:
            r = run_fixed_sequence(world, [action])
            single_values[action] = r.scalar_quality

        # Null/stop value (no actions)
        null_quality = EpistemicWorldSimulator(world).evaluate({}, set(), set(), {}).scalar_quality()

        # Sequence pair comparisons
        for pair_name, (seq_a, seq_b) in SEQUENCE_PAIRS.items():
            r_a = run_fixed_sequence(world, seq_a)
            r_b = run_fixed_sequence(world, seq_b)

            sum_primitives_a = sum(single_values.get(a, 0) for a in seq_a) / max(1, len(seq_a))
            sum_primitives_b = sum(single_values.get(a, 0) for a in seq_b) / max(1, len(seq_b))

            outcomes.append({
                "world_id": world.world_id,
                "pair_name": pair_name,
                "seq_a": seq_a,
                "seq_b": seq_b,
                "quality_a": r_a.scalar_quality,
                "quality_b": r_b.scalar_quality,
                "quality_diff": r_a.scalar_quality - r_b.scalar_quality,
                "avg_primitive_a": round(sum_primitives_a, 4),
                "avg_primitive_b": round(sum_primitives_b, 4),
                "complementarity_a": round(r_a.scalar_quality - sum_primitives_a, 4),
                "complementarity_b": round(r_b.scalar_quality - sum_primitives_b, 4),
                "order_effect": round(r_a.scalar_quality - r_b.scalar_quality, 4),
                "null_quality": null_quality,
            })

    return {"outcomes": outcomes}


# ---------------------------------------------------------------
# Phase 18.5: Attack operator state-dependence
# ---------------------------------------------------------------

def run_attack_state_dependence(dev_worlds: list[LatentWorld]) -> dict[str, Any]:
    """Test when attack is beneficial vs harmful."""
    outcomes: list[dict] = []

    conditions = {
        "attack_early_no_hyps": ["attack_hypothesis"],
        "attack_after_1hyp": ["retrieve", "generate_hypothesis", "attack_hypothesis"],
        "attack_after_2hyps": ["retrieve", "generate_hypothesis", "retrieve",
                               "generate_hypothesis", "attack_hypothesis"],
        "attack_then_reason": ["retrieve", "generate_hypothesis", "attack_hypothesis", "reason"],
        "no_attack_reason_instead": ["retrieve", "generate_hypothesis", "reason"],
        "attack_late_rich_state": ["retrieve", "generate_hypothesis", "retrieve",
                                    "generate_hypothesis", "reason", "attack_hypothesis"],
    }

    for world in dev_worlds:
        for cond_name, seq in conditions.items():
            r = run_fixed_sequence(world, seq)
            outcomes.append({
                "world_id": world.world_id,
                "condition": cond_name,
                "sequence": seq,
                "quality": r.scalar_quality,
                "hypothesis_count": r.hypothesis_count,
                "ignorance_count": r.ignorance_count,
                "evidence_count": r.evidence_count,
                "tokens": r.tokens_used,
            })

    return {"outcomes": outcomes}


# ---------------------------------------------------------------
# Main campaign runner
# ---------------------------------------------------------------

async def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("PHASES 17-18: ISOLATE WHAT WORKS + TEMPORAL COMPLEMENTARITY")
    print("=" * 60)

    # Generate V3 worlds
    splits = generate_v3_worlds(count_per_family=20)
    dev = splits["dev"]
    print(f"\nV3 worlds: dev={len(dev)}, val={len(splits['validation'])}, locked={len(splits['locked_test'])}")

    # ---- PHASE 17.1: B1 DECOMPOSITION ----
    print("\n" + "=" * 60)
    print("PHASE 17.1 — B1 SEQUENCE DECOMPOSITION")
    print("=" * 60)

    b1_results = await run_b1_decomposition(dev)
    (RESULTS_DIR / "b1_decomposition.json").write_text(json.dumps(b1_results["summary"], indent=2))
    with open(RESULTS_DIR / "b1_decomposition_detailed.jsonl", "w") as f:
        for r in b1_results["detailed"]:
            f.write(json.dumps(r) + "\n")

    print(f"\n{'Variant':40s} {'Quality':>10s} {'Std':>8s} {'N':>4s}")
    print("-" * 65)
    for name, stats in sorted(b1_results["summary"].items(), key=lambda x: -x[1]["mean"]):
        print(f"  {name:40s} {stats['mean']:9.4f} {stats['std']:8.4f} {stats['n']:4d}")

    # ---- PHASE 17.2: ECOLOGY CROSS-ARCHITECTURE ----
    print("\n" + "=" * 60)
    print("PHASE 17.2 - HYPOTHESIS ECOLOGY ACROSS ARCHITECTURES")
    print("=" * 60)

    ecology_results = await run_ecology_cross_architecture(dev)
    (RESULTS_DIR / "ecology_cross_architecture.json").write_text(
        json.dumps(ecology_results["summary"], indent=2))

    for name, stats in sorted(ecology_results["summary"].items(), key=lambda x: -x[1]["mean"]):
        print(f"  {name:35s}: quality={stats['mean']:.4f} +/- {stats['std']:.4f}")

    # ---- PHASE 18.2-18.4: SEQUENCE COMPLEMENTARITY ----
    print("\n" + "=" * 60)
    print("PHASE 18.2-18.4 - SEQUENCE COMPLEMENTARITY AND ORDER EFFECTS")
    print("=" * 60)

    comp_results = run_sequence_complementarity(dev)
    with open(RESULTS_DIR / "sequence_complementarity.jsonl", "w") as f:
        for r in comp_results["outcomes"]:
            f.write(json.dumps(r) + "\n")

    by_pair = defaultdict(list)
    for o in comp_results["outcomes"]:
        by_pair[o["pair_name"]].append(o)

    print(f"\n{'Pair':40s} {'Q(A->B)':>10s} {'Q(B->A)':>10s} {'Order Eff':>10s} {'Compl A':>10s}")
    print("-" * 85)
    for pair_name, outcomes in sorted(by_pair.items()):
        mean_qa = statistics.mean([o["quality_a"] for o in outcomes])
        mean_qb = statistics.mean([o["quality_b"] for o in outcomes])
        mean_order = statistics.mean([o["order_effect"] for o in outcomes])
        mean_comp_a = statistics.mean([o["complementarity_a"] for o in outcomes])
        print(f"  {pair_name:40s} {mean_qa:9.4f} {mean_qb:9.4f} {mean_order:+10.4f} {mean_comp_a:+10.4f}")

    # ---- PHASE 18.5: ATTACK STATE-DEPENDENCE ----
    print("\n" + "=" * 60)
    print("PHASE 18.5 - ATTACK OPERATOR STATE-DEPENDENCE")
    print("=" * 60)

    attack_results = run_attack_state_dependence(dev)
    with open(RESULTS_DIR / "attack_state_dependence.jsonl", "w") as f:
        for r in attack_results["outcomes"]:
            f.write(json.dumps(r) + "\n")

    by_cond = defaultdict(list)
    for o in attack_results["outcomes"]:
        by_cond[o["condition"]].append(o)

    print(f"\n{'Condition':40s} {'Quality':>10s} {'Std':>8s} {'Hyps':>6s} {'Ign':>6s}")
    print("-" * 75)
    for cond, outcomes in sorted(by_cond.items(), key=lambda x: -statistics.mean([o["quality"] for o in x[1]])):
        mean_q = statistics.mean([o["quality"] for o in outcomes])
        std_q = statistics.stdev([o["quality"] for o in outcomes]) if len(outcomes) > 1 else 0
        mean_h = statistics.mean([o["hypothesis_count"] for o in outcomes])
        mean_i = statistics.mean([o["ignorance_count"] for o in outcomes])
        print(f"  {cond:40s} {mean_q:9.4f} {std_q:8.4f} {mean_h:5.1f} {mean_i:5.1f}")

    # ---- SUMMARY ----
    print("\n" + "=" * 60)
    print("PHASE 17-18 SUMMARY")
    print("=" * 60)

    # Identify cognitive motifs
    print("\n--- COGNITIVE MOTIF CANDIDATES ---")
    for pair_name, outcomes in sorted(by_pair.items()):
        mean_order = statistics.mean([o["order_effect"] for o in outcomes])
        if abs(mean_order) > 0.05:
            direction = "A>B" if mean_order > 0 else "B>A"
            seq_a = outcomes[0]["seq_a"]
            seq_b = outcomes[0]["seq_b"]
            print(f"  {pair_name}: order_effect={mean_order:+.4f} ({direction})")
            print(f"    A: {seq_a}")
            print(f"    B: {seq_b}")

    print("\n" + "=" * 60)
    print("PHASES 17-18 COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
