"""
Phase 21 — Adaptive Necessity Benchmark.

Tests whether the V4 heterogeneous regimes genuinely require adaptive
cognitive control, or whether one fixed sequence dominates all states.
"""

from __future__ import annotations

import itertools
import json
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from asar.evaluation.scenarios.v4_regimes import V4_REGIME_GENERATORS
from asar.evaluation.simulator import EpistemicWorldSimulator, LatentWorld

RESULTS_DIR = Path(__file__).parent / "results"
V4_BASE_SEED = 271828

OPERATIONS = ["retrieve", "generate_hypothesis", "attack_hypothesis", "reason"]


# ---------------------------------------------------------------
# Fixed-sequence runner
# ---------------------------------------------------------------

def run_fixed_sequence(
    world: LatentWorld,
    sequence: list[str],
    *,
    seed: int = 42,
    pre_evidence: list[str] | None = None,
    pre_hypotheses: list[str] | None = None,
) -> dict[str, Any]:
    """Execute a fixed sequence and return quality + metadata."""
    sim = EpistemicWorldSimulator(world, seed=seed)
    ev_ids: list[str] = list(pre_evidence or [])
    hyps: dict[str, float] = {}
    ignorance_items: list[dict] = []
    evidence_sources: dict[str, str | None] = {}
    tokens = 0

    # Pre-populate with any pre-existing state
    for eid in (pre_evidence or []):
        sim._retrieved.add(eid)
    for hid in (pre_hypotheses or []):
        sim._generated_hypotheses.add(hid)
        h = world.hypotheses.get(hid)
        if h:
            hyps[hid] = h.initial_plausibility

    for op_name in sequence:
        if op_name == "retrieve":
            ev = sim.retrieve("")
            if ev:
                ev_ids.append(ev["evidence_id"])
                evidence_sources[ev["source_id"]] = ev.get("parent_source")
            tokens += 500
        elif op_name == "generate_hypothesis":
            h = sim.generate_hypothesis(ev_ids)
            if h:
                hyps[h["hypothesis_id"]] = h["initial_plausibility"]
            tokens += 500
        elif op_name == "attack_hypothesis":
            targets = list(hyps.keys())
            if targets:
                result = sim.attack_hypothesis(targets[0])
                ignorance_items.extend(result.get("ignorance_items", []))
            tokens += 500
        elif op_name == "reason":
            if hyps and ev_ids:
                reasoning = sim.reason(list(hyps.keys()), ev_ids)
                for hid, score in reasoning["consistency_scores"].items():
                    if hid in hyps:
                        hyps[hid] = score
            tokens += 500

    identified_hidden = set()
    for item in ignorance_items:
        desc = item.get("description", "").lower()
        for hv_id in world.hidden_variables:
            if hv_id.lower() in desc:
                identified_hidden.add(hv_id)

    quality = sim.evaluate(hyps, identified_hidden, set(), evidence_sources)
    return {
        "scalar_quality": quality.scalar_quality(),
        "tokens": tokens,
        "hypothesis_count": len(hyps),
        "evidence_count": len(ev_ids),
        "ignorance_count": len(ignorance_items),
        "sequence": sequence,
    }


# ---------------------------------------------------------------
# V4 world generation
# ---------------------------------------------------------------

def generate_v4_worlds(count_per_regime: int = 15) -> dict[str, list[LatentWorld]]:
    """Generate fresh V4 worlds across all 8 regimes."""
    splits: dict[str, list[LatentWorld]] = {"dev": [], "validation": [], "locked_test": []}
    for regime_name, gen_fn in V4_REGIME_GENERATORS.items():
        for i in range(count_per_regime):
            if i < count_per_regime // 2:
                split = "dev"
            elif i < int(count_per_regime * 0.73):
                split = "validation"
            else:
                split = "locked_test"
            world = gen_fn(index=i, seed=V4_BASE_SEED + i)
            splits[split].append(world)
    return splits


# ---------------------------------------------------------------
# Sequence oracle (exhaustive bounded evaluation)
# ---------------------------------------------------------------

def generate_all_sequences(max_length: int = 3) -> list[list[str]]:
    """Generate all bounded-length cognitive sequences."""
    sequences = []
    for length in range(1, max_length + 1):
        for combo in itertools.product(OPERATIONS, repeat=length):
            sequences.append(list(combo))
    return sequences


def compute_sequence_oracle(
    worlds: list[LatentWorld],
    max_length: int = 3,
) -> dict[str, Any]:
    """For each world, find the best sequence of each length."""
    all_seqs = generate_all_sequences(max_length)
    oracle_records = []
    best_per_world: dict[str, dict] = {}

    for world in worlds:
        world_results = []
        for seq in all_seqs:
            result = run_fixed_sequence(world, seq)
            world_results.append({
                "world_id": world.world_id,
                "sequence": seq,
                "quality": result["scalar_quality"],
                "tokens": result["tokens"],
                "length": len(seq),
            })

        best = max(world_results, key=lambda r: r["quality"])
        best_per_world[world.world_id] = best
        oracle_records.extend(world_results)

    return {"oracle_records": oracle_records, "best_per_world": best_per_world}


# ---------------------------------------------------------------
# Named candidate sequences for comparison
# ---------------------------------------------------------------

CANDIDATE_SEQUENCES = {
    "B1_extended": ["retrieve", "generate_hypothesis", "retrieve",
                    "generate_hypothesis", "reason", "retrieve", "reason"],
    "B1_full": ["retrieve", "generate_hypothesis", "retrieve",
                "generate_hypothesis", "reason"],
    "explore_first": ["generate_hypothesis", "retrieve", "reason"],
    "evidence_heavy": ["retrieve", "retrieve", "retrieve", "reason"],
    "attack_then_reason": ["retrieve", "generate_hypothesis",
                           "attack_hypothesis", "reason"],
    "discriminate": ["retrieve", "generate_hypothesis", "retrieve",
                     "generate_hypothesis", "attack_hypothesis", "reason"],
    "integrate_only": ["retrieve", "generate_hypothesis", "reason"],
    "full_explore": ["generate_hypothesis", "retrieve", "generate_hypothesis",
                     "retrieve", "reason"],
    "atk_late": ["retrieve", "generate_hypothesis", "retrieve",
                 "generate_hypothesis", "reason", "attack_hypothesis", "reason"],
}


# ---------------------------------------------------------------
# Phase 21.2-21.6: Adaptivity gap and sequence oracle diversity
# ---------------------------------------------------------------

def compute_adaptivity_gap(dev_worlds: list[LatentWorld]) -> dict[str, Any]:
    """
    Compute AdaptivityGap = Quality(state-conditioned oracle) - Quality(best global fixed).
    """
    # Best global fixed: evaluate all named candidates on all worlds
    global_results: dict[str, list[float]] = defaultdict(list)
    for world in dev_worlds:
        for name, seq in CANDIDATE_SEQUENCES.items():
            r = run_fixed_sequence(world, seq)
            global_results[name].append(r["scalar_quality"])

    global_means = {name: statistics.mean(scores)
                    for name, scores in global_results.items()}
    best_global_name = max(global_means, key=global_means.get)
    best_global_quality = global_means[best_global_name]

    # State-conditioned oracle: best candidate per world
    oracle_total = 0.0
    oracle_per_world: dict[str, dict] = {}
    for world in dev_worlds:
        best_q = -1.0
        best_seq = ""
        for name, seq in CANDIDATE_SEQUENCES.items():
            r = run_fixed_sequence(world, seq)
            if r["scalar_quality"] > best_q:
                best_q = r["scalar_quality"]
                best_seq = name
        oracle_total += best_q
        oracle_per_world[world.world_id] = {
            "best_sequence": best_seq,
            "quality": best_q,
        }

    oracle_quality = oracle_total / len(dev_worlds)
    adaptivity_gap = oracle_quality - best_global_quality

    # Sequence oracle diversity
    oracle_sequence_counts = Counter(
        v["best_sequence"] for v in oracle_per_world.values()
    )
    dominant_pct = max(oracle_sequence_counts.values()) / len(dev_worlds) * 100

    return {
        "best_global_name": best_global_name,
        "best_global_quality": round(best_global_quality, 4),
        "oracle_quality": round(oracle_quality, 4),
        "adaptivity_gap": round(adaptivity_gap, 4),
        "oracle_sequence_distribution": dict(oracle_sequence_counts),
        "dominant_sequence_pct": round(dominant_pct, 1),
        "global_means": {k: round(v, 4) for k, v in sorted(
            global_means.items(), key=lambda x: -x[1])},
        "oracle_per_world": oracle_per_world,
    }


# ---------------------------------------------------------------
# Phase 21.7: Cognitive non-commutativity
# ---------------------------------------------------------------

def compute_order_effects(dev_worlds: list[LatentWorld]) -> list[dict]:
    """Measure order effects for all compatible operation pairs."""
    pairs = list(itertools.combinations(OPERATIONS, 2))
    results = []

    for op_a, op_b in pairs:
        ab_scores = []
        ba_scores = []
        for world in dev_worlds:
            r_ab = run_fixed_sequence(world, [op_a, op_b])
            r_ba = run_fixed_sequence(world, [op_b, op_a])
            ab_scores.append(r_ab["scalar_quality"])
            ba_scores.append(r_ba["scalar_quality"])

        mean_ab = statistics.mean(ab_scores)
        mean_ba = statistics.mean(ba_scores)
        order_effect = mean_ab - mean_ba

        # State-dependent reversal: how often does the better order flip?
        reversals = sum(1 for a, b in zip(ab_scores, ba_scores) if a < b)
        reversal_pct = reversals / len(ab_scores) * 100

        category = "near_commutative"
        if abs(order_effect) > 0.15:
            category = "strong_order_effect"
        elif abs(order_effect) > 0.05:
            category = "weak_order_effect"
        if reversal_pct > 30:
            category = "state_dependent_reversal"

        results.append({
            "op_a": op_a,
            "op_b": op_b,
            "mean_ab": round(mean_ab, 4),
            "mean_ba": round(mean_ba, 4),
            "order_effect": round(order_effect, 4),
            "reversal_pct": round(reversal_pct, 1),
            "category": category,
        })

    return results


# ---------------------------------------------------------------
# Phase 21.8: Temporal complementarity matrix
# ---------------------------------------------------------------

def compute_complementarity_matrix(dev_worlds: list[LatentWorld]) -> dict[str, Any]:
    """
    For operation pairs, compute synergy/redundancy/interference.
    
    Complementarity(A,B|E) = Value(A->B|E) - 0.5*(Value(A|E) + Value(B|E))
    """
    single_values: dict[str, list[float]] = defaultdict(list)
    for world in dev_worlds:
        for op in OPERATIONS:
            r = run_fixed_sequence(world, [op])
            single_values[op].append(r["scalar_quality"])

    matrix = {}
    for op_a in OPERATIONS:
        for op_b in OPERATIONS:
            pair_key = f"{op_a}->{op_b}"
            pair_scores = []
            for i, world in enumerate(dev_worlds):
                r = run_fixed_sequence(world, [op_a, op_b])
                expected_independent = 0.5 * (single_values[op_a][i] + single_values[op_b][i])
                complementarity = r["scalar_quality"] - expected_independent
                pair_scores.append({
                    "world_id": world.world_id,
                    "pair_quality": r["scalar_quality"],
                    "expected_independent": round(expected_independent, 4),
                    "complementarity": round(complementarity, 4),
                })

            mean_comp = statistics.mean([s["complementarity"] for s in pair_scores])
            mean_qual = statistics.mean([s["pair_quality"] for s in pair_scores])

            if mean_comp > 0.05:
                relation = "synergy"
            elif mean_comp < -0.05:
                relation = "interference"
            else:
                relation = "redundancy"

            # Check state dependence
            comp_values = [s["complementarity"] for s in pair_scores]
            comp_std = statistics.stdev(comp_values) if len(comp_values) > 1 else 0
            state_dependent = comp_std > abs(mean_comp) * 0.5 if mean_comp != 0 else comp_std > 0.05

            matrix[pair_key] = {
                "mean_complementarity": round(mean_comp, 4),
                "mean_quality": round(mean_qual, 4),
                "relation": relation,
                "state_dependent": state_dependent,
                "std": round(comp_std, 4),
            }

    return {"matrix": matrix, "single_means": {
        op: round(statistics.mean(scores), 4)
        for op, scores in single_values.items()
    }}


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------

def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("PHASE 21 — ADAPTIVE NECESSITY BENCHMARK")
    print("=" * 70)

    # Generate V4 worlds
    splits = generate_v4_worlds(count_per_regime=15)
    dev = splits["dev"]
    val = splits["validation"]
    locked = splits["locked_test"]
    print(f"\nV4 worlds: dev={len(dev)}, val={len(val)}, locked={len(locked)}")
    print(f"Regimes: {list(V4_REGIME_GENERATORS.keys())}")

    # ---- 21.2-21.6: ADAPTIVITY GAP ----
    print("\n" + "=" * 70)
    print("21.2-21.6: ADAPTIVITY GAP AND SEQUENCE ORACLE")
    print("=" * 70)

    gap_results = compute_adaptivity_gap(dev)
    (RESULTS_DIR / "adaptivity_gap.json").write_text(json.dumps(gap_results, indent=2, default=str))

    print(f"\n  Best global fixed: {gap_results['best_global_name']} "
          f"(quality={gap_results['best_global_quality']})")
    print(f"  State-conditioned oracle: quality={gap_results['oracle_quality']}")
    print(f"  ADAPTIVITY GAP = {gap_results['adaptivity_gap']}")
    print(f"  Dominant sequence: {gap_results['dominant_sequence_pct']}% of worlds")

    print(f"\n  Global sequence ranking:")
    for name, quality in gap_results["global_means"].items():
        print(f"    {name:30s} {quality:.4f}")

    print(f"\n  Oracle sequence distribution:")
    for seq, count in sorted(gap_results["oracle_sequence_distribution"].items(),
                              key=lambda x: -x[1]):
        print(f"    {seq:30s} {count:3d} worlds ({count/len(dev)*100:.1f}%)")

    # ---- ADAPTIVE NECESSITY GATE ----
    print("\n" + "-" * 50)
    print("ADAPTIVE NECESSITY GATE EVALUATION")
    print("-" * 50)

    gate_criteria = {
        "multiple_optimal_sequences": len(gap_results["oracle_sequence_distribution"]) >= 3,
        "no_single_dominant_>90%": gap_results["dominant_sequence_pct"] < 90.0,
        "adaptivity_gap_>0.05": gap_results["adaptivity_gap"] > 0.05,
        "adaptivity_gap_>0.10": gap_results["adaptivity_gap"] > 0.10,
    }

    for criterion, passed in gate_criteria.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {criterion}")

    gate_passed = all([
        gate_criteria["multiple_optimal_sequences"],
        gate_criteria["no_single_dominant_>90%"],
        gate_criteria["adaptivity_gap_>0.05"],
    ])
    print(f"\n  ADAPTIVE NECESSITY: {'ESTABLISHED' if gate_passed else 'NOT ESTABLISHED'}")

    # ---- 21.7: ORDER EFFECTS ----
    print("\n" + "=" * 70)
    print("21.7: COGNITIVE NON-COMMUTATIVITY")
    print("=" * 70)

    order_effects = compute_order_effects(dev)
    (RESULTS_DIR / "order_effects.json").write_text(json.dumps(order_effects, indent=2))

    print(f"\n  {'Pair':50s} {'Q(A->B)':>10s} {'Q(B->A)':>10s} {'Effect':>10s} {'Category':>25s}")
    print("  " + "-" * 110)
    for r in sorted(order_effects, key=lambda x: -abs(x["order_effect"])):
        pair = f"{r['op_a']} -> {r['op_b']}"
        print(f"  {pair:50s} {r['mean_ab']:9.4f} {r['mean_ba']:9.4f} "
              f"{r['order_effect']:+10.4f} {r['category']:>25s}")

    # ---- 21.8: COMPLEMENTARITY MATRIX ----
    print("\n" + "=" * 70)
    print("21.8: TEMPORAL COMPLEMENTARITY MATRIX")
    print("=" * 70)

    comp_results = compute_complementarity_matrix(dev)
    (RESULTS_DIR / "complementarity_matrix.json").write_text(
        json.dumps(comp_results, indent=2))

    print(f"\n  Single operation values:")
    for op, val_score in comp_results["single_means"].items():
        print(f"    {op:30s} {val_score:.4f}")

    print(f"\n  {'Pair':45s} {'Quality':>8s} {'Compl':>10s} {'Relation':>12s} {'State-dep':>10s}")
    print("  " + "-" * 90)
    for pair_key, data in sorted(comp_results["matrix"].items(),
                                  key=lambda x: -abs(x[1]["mean_complementarity"])):
        print(f"  {pair_key:45s} {data['mean_quality']:7.4f} "
              f"{data['mean_complementarity']:+10.4f} {data['relation']:>12s} "
              f"{'YES' if data['state_dependent'] else 'no':>10s}")

    # ---- PER-REGIME ANALYSIS ----
    print("\n" + "=" * 70)
    print("PER-REGIME OPTIMAL SEQUENCES")
    print("=" * 70)

    regime_oracle: dict[str, Counter] = defaultdict(Counter)
    for world_id, oracle_data in gap_results["oracle_per_world"].items():
        regime = "_".join(world_id.split("_")[:3])
        regime_oracle[regime][oracle_data["best_sequence"]] += 1

    for regime, counts in sorted(regime_oracle.items()):
        print(f"\n  {regime}:")
        for seq_name, count in counts.most_common():
            print(f"    {seq_name:30s} {count}")

    # ---- SAVE SEQUENCE ORACLE DATA ----
    oracle_data = compute_sequence_oracle(dev, max_length=3)
    with open(RESULTS_DIR / "sequence_oracle.jsonl", "w") as f:
        for rec in oracle_data["oracle_records"]:
            f.write(json.dumps(rec) + "\n")

    print("\n" + "=" * 70)
    print(f"PHASE 21 COMPLETE — Adaptive Necessity: "
          f"{'ESTABLISHED' if gate_passed else 'NOT ESTABLISHED'}")
    print("=" * 70)

    return gate_passed


if __name__ == "__main__":
    main()
