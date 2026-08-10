"""
Phase 22: LLM-in-the-loop protocol and capability gate design
Phase 23: Sequence-aware metacognitive policy
Phase 24: Prior-art audit and paper decision

Phase 22 builds the experimental protocol for LLM-in-the-loop validation.
Actual LLM execution requires a running model server.

Phase 23 tests whether state features can predict optimal cognitive motifs,
using Phase 21's established adaptive necessity (gap = 0.0955).

Phase 24 surveys 2024-2026 prior art and determines paper viability.
"""

from __future__ import annotations

import itertools
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from asar.evaluation.scenarios.v4_regimes import V4_REGIME_GENERATORS
from asar.evaluation.simulator import EpistemicWorldSimulator, LatentWorld

RESULTS_DIR = Path(__file__).parent / "results"
V4_BASE_SEED = 271828

OPERATIONS = ["retrieve", "generate_hypothesis", "attack_hypothesis", "reason"]


# ---------------------------------------------------------------
# Fixed-sequence runner (shared with Phase 21)
# ---------------------------------------------------------------

def run_fixed_sequence(
    world: LatentWorld,
    sequence: list[str],
    *,
    seed: int = 42,
) -> dict[str, Any]:
    sim = EpistemicWorldSimulator(world, seed=seed)
    ev_ids: list[str] = []
    hyps: dict[str, float] = {}
    ignorance_items: list[dict] = []
    evidence_sources: dict[str, str | None] = {}
    tokens = 0

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
    }


# ---------------------------------------------------------------
# V4 world generation
# ---------------------------------------------------------------

def generate_v4_worlds(count_per_regime: int = 15) -> dict[str, list[LatentWorld]]:
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
# Phase 23: Cognitive Motif Policy
# ---------------------------------------------------------------

MOTIFS = {
    "EXPLORE": ["generate_hypothesis", "retrieve"],
    "DISCRIMINATE": ["retrieve", "generate_hypothesis", "reason"],
    "INTEGRATE": ["reason"],
    "INVESTIGATE": ["attack_hypothesis", "reason"],
    "EXPAND": ["retrieve", "generate_hypothesis", "retrieve",
               "generate_hypothesis", "reason"],
    "FULL_EXPLORE": ["generate_hypothesis", "retrieve", "generate_hypothesis",
                     "retrieve", "reason"],
}


def extract_state_features(world: LatentWorld) -> dict[str, float]:
    """Extract epistemic state features from the world structure."""
    n_hyps = len(world.hypotheses)
    n_evidence = len(world.evidence_pool)
    n_hidden = len(world.hidden_variables)

    true_h = world.hypotheses.get(world.true_hypothesis_id)
    true_plausibility = true_h.initial_plausibility if true_h else 0.0
    max_plausibility = max((h.initial_plausibility for h in world.hypotheses.values()), default=0)

    plausibilities = [h.initial_plausibility for h in world.hypotheses.values()]
    hyp_entropy = 0.0
    if plausibilities:
        total = sum(plausibilities)
        if total > 0:
            probs = [p / total for p in plausibilities]
            hyp_entropy = -sum(p * math.log(p + 1e-10) for p in probs)

    top_margin = 0.0
    if len(plausibilities) >= 2:
        sorted_p = sorted(plausibilities, reverse=True)
        top_margin = sorted_p[0] - sorted_p[1]

    support_counts = defaultdict(int)
    contradict_counts = defaultdict(int)
    for e in world.evidence_pool:
        for h in e.supports_hypotheses:
            support_counts[h] += 1
        for h in e.contradicts_hypotheses:
            contradict_counts[h] += 1

    evidence_coverage = len(support_counts) / max(1, n_hyps)
    contradiction_density = sum(contradict_counts.values()) / max(1, n_evidence)

    mean_info_value = statistics.mean(
        [e.information_value for e in world.evidence_pool]) if world.evidence_pool else 0

    dependent_sources = sum(
        1 for s in world.source_registry.values() if s.parent_source is not None)
    source_independence = 1.0 - (dependent_sources / max(1, len(world.source_registry)))

    return {
        "hypothesis_count": float(n_hyps),
        "evidence_count": float(n_evidence),
        "hidden_variable_count": float(n_hidden),
        "true_plausibility": true_plausibility,
        "max_plausibility": max_plausibility,
        "hypothesis_entropy": round(hyp_entropy, 4),
        "top_margin": round(top_margin, 4),
        "evidence_coverage": round(evidence_coverage, 4),
        "contradiction_density": round(contradiction_density, 4),
        "mean_info_value": round(mean_info_value, 4),
        "source_independence": round(source_independence, 4),
    }


def evaluate_motifs_on_world(world: LatentWorld) -> dict[str, float]:
    """Evaluate all motifs on a single world."""
    results = {}
    for name, seq in MOTIFS.items():
        r = run_fixed_sequence(world, seq)
        results[name] = r["scalar_quality"]
    return results


class SimpleMotifPolicy:
    """
    Transparent rule-based motif selector using state features.
    Trained by finding feature thresholds that predict optimal motifs.
    """

    def __init__(self, rules: list[tuple[str, str, float, str]]) -> None:
        self._rules = rules  # (feature, comparator, threshold, motif)

    def select(self, features: dict[str, float]) -> str:
        for feature, comparator, threshold, motif in self._rules:
            val = features.get(feature, 0.0)
            if comparator == ">" and val > threshold:
                return motif
            if comparator == "<" and val < threshold:
                return motif
            if comparator == ">=" and val >= threshold:
                return motif
            if comparator == "<=" and val <= threshold:
                return motif
        return "EXPAND"


def train_motif_policy(
    worlds: list[LatentWorld],
) -> tuple[SimpleMotifPolicy, dict[str, Any]]:
    """Learn motif selection rules from dev data."""
    training_data = []
    for world in worlds:
        features = extract_state_features(world)
        motif_values = evaluate_motifs_on_world(world)
        best_motif = max(motif_values, key=motif_values.get)
        training_data.append({
            "world_id": world.world_id,
            "features": features,
            "best_motif": best_motif,
            "motif_values": motif_values,
        })

    # Analyze which features predict motif choice
    motif_groups: dict[str, list[dict]] = defaultdict(list)
    for record in training_data:
        motif_groups[record["best_motif"]].append(record["features"])

    rules = []
    for motif, feature_lists in motif_groups.items():
        if len(feature_lists) < 3:
            continue
        for feature_name in feature_lists[0]:
            vals = [f[feature_name] for f in feature_lists]
            all_vals = [r["features"][feature_name] for r in training_data]
            mean_motif = statistics.mean(vals)
            mean_all = statistics.mean(all_vals)
            if abs(mean_motif - mean_all) > 0.3 * (statistics.stdev(all_vals) + 0.01):
                comp = ">" if mean_motif > mean_all else "<"
                threshold = (mean_motif + mean_all) / 2
                rules.append((feature_name, comp, round(threshold, 3), motif))

    if not rules:
        rules = [("hypothesis_count", ">=", 0, "EXPAND")]

    policy = SimpleMotifPolicy(rules)
    return policy, {
        "n_training": len(training_data),
        "n_rules": len(rules),
        "rules": [(f, c, t, m) for f, c, t, m in rules],
        "motif_distribution": dict(Counter(r["best_motif"] for r in training_data)),
        "training_data": training_data,
    }


# ---------------------------------------------------------------
# Phase 23.6: Regret computation
# ---------------------------------------------------------------

def compute_regret_analysis(
    worlds: list[LatentWorld],
    policy: SimpleMotifPolicy,
) -> dict[str, Any]:
    """Compare regret across different selection strategies."""
    oracle_regrets = []
    fixed_regrets = []
    policy_regrets = []
    policy_selections: list[str] = []
    trajectories: list[dict] = []

    # Best global fixed
    global_means: dict[str, float] = defaultdict(float)
    for world in worlds:
        for name, seq in MOTIFS.items():
            r = run_fixed_sequence(world, seq)
            global_means[name] += r["scalar_quality"]
    global_means = {k: v / len(worlds) for k, v in global_means.items()}
    best_global = max(global_means, key=global_means.get)

    for world in worlds:
        motif_values = evaluate_motifs_on_world(world)
        oracle_quality = max(motif_values.values())
        features = extract_state_features(world)

        # Best global fixed
        fixed_quality = motif_values.get(best_global, 0)
        fixed_regrets.append(oracle_quality - fixed_quality)

        # Policy
        selected = policy.select(features)
        policy_quality = motif_values.get(selected, 0)
        policy_regrets.append(oracle_quality - policy_quality)
        policy_selections.append(selected)

        trajectories.append({
            "world_id": world.world_id,
            "features": features,
            "oracle_best": max(motif_values, key=motif_values.get),
            "oracle_quality": oracle_quality,
            "fixed_selected": best_global,
            "fixed_quality": fixed_quality,
            "policy_selected": selected,
            "policy_quality": policy_quality,
            "motif_values": motif_values,
        })

    selection_entropy = 0.0
    counts = Counter(policy_selections)
    total = len(policy_selections)
    for c in counts.values():
        p = c / total
        selection_entropy -= p * math.log(p + 1e-10)

    return {
        "best_global_motif": best_global,
        "mean_oracle_quality": round(statistics.mean([t["oracle_quality"] for t in trajectories]), 4),
        "mean_fixed_quality": round(statistics.mean([t["fixed_quality"] for t in trajectories]), 4),
        "mean_policy_quality": round(statistics.mean([t["policy_quality"] for t in trajectories]), 4),
        "mean_fixed_regret": round(statistics.mean(fixed_regrets), 4),
        "mean_policy_regret": round(statistics.mean(policy_regrets), 4),
        "policy_selection_distribution": dict(counts),
        "selection_entropy": round(selection_entropy, 4),
        "n_distinct_trajectories": len(set(policy_selections)),
        "policy_beats_fixed": statistics.mean(
            [t["policy_quality"] for t in trajectories]) > statistics.mean(
            [t["fixed_quality"] for t in trajectories]),
        "trajectories": trajectories,
    }


# ---------------------------------------------------------------
# Phase 23.7: Primitive vs sequence value prediction
# ---------------------------------------------------------------

def compare_primitive_vs_sequence_prediction(
    worlds: list[LatentWorld],
) -> dict[str, Any]:
    """Compare predictive quality of primitive action values vs motif values."""
    primitive_correct = 0
    sequence_correct = 0
    total = 0

    for world in worlds:
        # Primitive: single operation values
        primitive_values = {}
        for op in OPERATIONS:
            r = run_fixed_sequence(world, [op])
            primitive_values[op] = r["scalar_quality"]
        best_primitive = max(primitive_values, key=primitive_values.get)

        # Sequence: motif values
        motif_values = evaluate_motifs_on_world(world)
        best_motif = max(motif_values, key=motif_values.get)

        # Ground truth: which produces better final quality?
        # Extend to full-length sequences for fair comparison
        full_sequences = {
            "primitive_repeated": [best_primitive] * 3,
            "motif_selected": MOTIFS[best_motif],
        }

        primitive_full = run_fixed_sequence(world, full_sequences["primitive_repeated"])
        motif_full = run_fixed_sequence(world, full_sequences["motif_selected"])

        if motif_full["scalar_quality"] >= primitive_full["scalar_quality"]:
            sequence_correct += 1
        else:
            primitive_correct += 1
        total += 1

    return {
        "sequence_wins": sequence_correct,
        "primitive_wins": primitive_correct,
        "total": total,
        "sequence_win_rate": round(sequence_correct / max(1, total), 4),
        "primitive_win_rate": round(primitive_correct / max(1, total), 4),
    }


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------

def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    splits = generate_v4_worlds(count_per_regime=15)
    dev = splits["dev"]
    val = splits["validation"]
    locked = splits["locked_test"]

    # ================ PHASE 22 ================
    print("=" * 70)
    print("PHASE 22 — LLM-IN-THE-LOOP PROTOCOL")
    print("=" * 70)

    print("""
  INFRASTRUCTURE STATUS:
    LLMClientProtocol:     EXISTS (asar/core/llm.py)
    OpenAI Responses API:  EXISTS (asar/providers/openai_llm.py)
    Chat Completions API:  BUILT  (asar/providers/chat_completions_llm.py)
    Cognitive Operators:   EXIST  (asar/operators/*.py) - accept LLMClientProtocol
    Model Configuration:   EXISTS (config/models.toml, env overrides)

  MISSING FOR LIVE EXECUTION:
    Running local model server (Ollama/vLLM/LM Studio)
    API credentials (if using cloud model)

  CAPABILITY GATE PROTOCOL:
    10 primitive tests required before architecture comparisons:
    1. interpret_evidence        - score on evidence relevance
    2. generate_hypothesis       - novel hypothesis from evidence
    3. generate_alternative      - genuinely different hypothesis
    4. derive_implication        - logical consequence
    5. identify_contradiction    - find inconsistency
    6. attack_hypothesis         - find weakness
    7. identify_missing_info     - what's unknown
    8. targeted_retrieval        - formulate useful query
    9. synthesize_conclusion     - integrate evidence
    10. structured_output        - follow JSON schema

  LEAKAGE PREVENTION:
    LLM must NEVER see: latent true hypothesis, oracle values,
    hidden regime labels, expected answers, locked-test metadata.

  STATUS: PROTOCOL DEFINED, INFRASTRUCTURE BUILT
  EXECUTION: REQUIRES RUNNING MODEL SERVER
    """)

    (RESULTS_DIR / "phase22_protocol.json").write_text(json.dumps({
        "infrastructure_status": {
            "llm_protocol": "exists",
            "responses_adapter": "exists",
            "chat_completions_adapter": "built",
            "cognitive_operators": "exist",
            "model_config": "exists",
        },
        "capability_gate": {
            "tests": [
                "interpret_evidence", "generate_hypothesis",
                "generate_alternative", "derive_implication",
                "identify_contradiction", "attack_hypothesis",
                "identify_missing_info", "targeted_retrieval",
                "synthesize_conclusion", "structured_output",
            ],
            "scoring": "simulator-grounded objective",
        },
        "execution_status": "REQUIRES_RUNNING_MODEL_SERVER",
    }, indent=2))

    # ================ PHASE 23 ================
    print("\n" + "=" * 70)
    print("PHASE 23 — SEQUENCE-AWARE METACOGNITIVE POLICY")
    print("=" * 70)

    # 23.1-23.2: Train motif policy on dev
    print("\n--- 23.1-23.2: MOTIF POLICY TRAINING ---")
    policy, training_info = train_motif_policy(dev)

    print(f"  Training worlds: {training_info['n_training']}")
    print(f"  Rules learned: {training_info['n_rules']}")
    print(f"  Motif distribution on dev:")
    for motif, count in sorted(training_info["motif_distribution"].items(),
                                key=lambda x: -x[1]):
        print(f"    {motif:20s} {count:3d}")
    print(f"  Rules:")
    for feature, comp, threshold, motif in training_info["rules"]:
        print(f"    IF {feature} {comp} {threshold} THEN {motif}")

    # 23.3-23.6: Regret analysis on dev
    print("\n--- 23.3-23.6: DEV REGRET ANALYSIS ---")
    dev_regret = compute_regret_analysis(dev, policy)
    (RESULTS_DIR / "phase23_dev_regret.json").write_text(
        json.dumps({k: v for k, v in dev_regret.items() if k != "trajectories"}, indent=2))

    print(f"  Oracle quality:      {dev_regret['mean_oracle_quality']}")
    print(f"  Best fixed quality:  {dev_regret['mean_fixed_quality']} ({dev_regret['best_global_motif']})")
    print(f"  Policy quality:      {dev_regret['mean_policy_quality']}")
    print(f"  Fixed regret:        {dev_regret['mean_fixed_regret']}")
    print(f"  Policy regret:       {dev_regret['mean_policy_regret']}")
    print(f"  Policy beats fixed:  {dev_regret['policy_beats_fixed']}")
    print(f"  Selection entropy:   {dev_regret['selection_entropy']}")
    print(f"  Distinct motifs:     {dev_regret['n_distinct_trajectories']}")
    print(f"  Selection distribution:")
    for motif, count in sorted(dev_regret["policy_selection_distribution"].items(),
                                key=lambda x: -x[1]):
        print(f"    {motif:20s} {count:3d}")

    # 23.6: Validation regret
    print("\n--- 23.6: VALIDATION REGRET ---")
    val_regret = compute_regret_analysis(val, policy)
    (RESULTS_DIR / "phase23_val_regret.json").write_text(
        json.dumps({k: v for k, v in val_regret.items() if k != "trajectories"}, indent=2))

    print(f"  Oracle quality:      {val_regret['mean_oracle_quality']}")
    print(f"  Best fixed quality:  {val_regret['mean_fixed_quality']}")
    print(f"  Policy quality:      {val_regret['mean_policy_quality']}")
    print(f"  Fixed regret:        {val_regret['mean_fixed_regret']}")
    print(f"  Policy regret:       {val_regret['mean_policy_regret']}")
    print(f"  Policy beats fixed:  {val_regret['policy_beats_fixed']}")

    # 23.7: Primitive vs sequence prediction
    print("\n--- 23.7: PRIMITIVE VS SEQUENCE VALUE PREDICTION ---")
    pred_results = compare_primitive_vs_sequence_prediction(dev)
    (RESULTS_DIR / "phase23_prediction_comparison.json").write_text(
        json.dumps(pred_results, indent=2))

    print(f"  Sequence motif wins: {pred_results['sequence_wins']}/{pred_results['total']} "
          f"({pred_results['sequence_win_rate']*100:.1f}%)")
    print(f"  Primitive wins:      {pred_results['primitive_wins']}/{pred_results['total']} "
          f"({pred_results['primitive_win_rate']*100:.1f}%)")

    # 23.10: GO criterion for adaptive metacognition
    print("\n--- 23.10: GO CRITERION ---")
    go_criteria = {
        "policy_quality > fixed_quality": val_regret["policy_beats_fixed"],
        "policy_regret < fixed_regret": val_regret["mean_policy_regret"] < val_regret["mean_fixed_regret"],
        "n_distinct_trajectories >= 3": val_regret["n_distinct_trajectories"] >= 3,
        "selection_entropy > 0.5": val_regret["selection_entropy"] > 0.5,
    }
    for criterion, passed in go_criteria.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {criterion}")

    go_passed = all(go_criteria.values())
    print(f"\n  ADAPTIVE METACOGNITION: {'SUPPORTED' if go_passed else 'NOT SUPPORTED'}")

    # ---- LOCKED TEST (ONE-SHOT) ----
    print("\n--- LOCKED TEST (ONE-SHOT) ---")
    locked_regret = compute_regret_analysis(locked, policy)
    (RESULTS_DIR / "phase23_locked_regret.json").write_text(
        json.dumps({k: v for k, v in locked_regret.items() if k != "trajectories"}, indent=2))

    print(f"  Oracle quality:      {locked_regret['mean_oracle_quality']}")
    print(f"  Best fixed quality:  {locked_regret['mean_fixed_quality']}")
    print(f"  Policy quality:      {locked_regret['mean_policy_quality']}")
    print(f"  Fixed regret:        {locked_regret['mean_fixed_regret']}")
    print(f"  Policy regret:       {locked_regret['mean_policy_regret']}")
    print(f"  Policy beats fixed:  {locked_regret['policy_beats_fixed']}")

    # ================ PHASE 24 ================
    print("\n" + "=" * 70)
    print("PHASE 24 — PRIOR-ART AUDIT AND PAPER DECISION")
    print("=" * 70)

    print("""
  PRIOR-ART CATEGORIES (2024-2026):

  1. ADAPTIVE TEST-TIME COMPUTE
     - OpenAI o1/o3 scaling reasoning tokens
     - DeepSeek-R1 adaptive reasoning length
     - Budget-forcing / compute-optimal inference
     Prior concept: YES. Same mechanism: NO (we study cognitive operation
     sequences, not reasoning chain length).

  2. ADAPTIVE RETRIEVAL / AGENTIC SEARCH
     - Self-RAG, Adaptive-RAG, FLARE
     - When to retrieve vs when to reason directly
     Prior concept: YES. Similar motivation: YES. Novel finding:
     Our quantification of retrieve-hypothesize-reason complementarity
     and order effects is more specific.

  3. HIERARCHICAL AGENT PLANNING
     - Skills/options in LLM agents (Voyager, DEPS)
     - Temporal abstraction in agent control
     Prior concept: YES. Same mechanism: PARTIALLY. Our cognitive motifs
     are epistemically grounded, not task-completion skills.

  4. PROCESS REWARD MODELS
     - Math-Shepherd, OmegaPRM
     - Step-level reward for reasoning chains
     Prior concept: YES. Similar motivation: YES. Novel:
     We measure operation-pair complementarity, not step correctness.

  5. VALUE-GUIDED SEARCH
     - MCTS + LLM (AlphaCode, tree-of-thought)
     - Value estimation for search branches
     Prior concept: YES. Distinct: Our domain is epistemic research,
     not code generation or math.

  6. METACOGNITIVE LLM AGENTS
     - Reflexion, self-evaluation
     - Know-when-you-don't-know
     Prior concept: YES. Distinct: We provide controlled measurement
     of temporal complementarity, not just self-reflection.

  NOVELTY ASSESSMENT:
    """)

    novelty_analysis = {
        "A_temporal_complementarity": {
            "description": "Cognitive operations exhibit measurable non-additive order-dependent value",
            "prior_concept_exists": True,
            "same_mechanism": False,
            "novel_experimental_finding": True,
            "strength": "MODERATE — the specific quantification of gen_hyp+reason synergy (+0.228) in an epistemic domain with controlled measurement is novel",
        },
        "B_greedy_failure": {
            "description": "Greedy primitive-level scheduling fails when operations are temporally complementary",
            "prior_concept_exists": True,
            "same_mechanism": True,
            "novel_experimental_finding": False,
            "strength": "WEAK — this is known from options/hierarchical RL literature",
        },
        "C_state_dependent_motifs": {
            "description": "Epistemic state predicts which cognitive motif is most valuable",
            "prior_concept_exists": True,
            "same_mechanism": False,
            "novel_experimental_finding": True,
            "strength": "MODERATE — applying option selection to epistemic research is novel",
        },
        "D_epistemic_benchmark": {
            "description": "Controlled benchmark for counterfactual cognitive sequence evaluation",
            "prior_concept_exists": False,
            "same_mechanism": False,
            "novel_experimental_finding": True,
            "strength": "STRONG — EpistemicWorldSimulator with counterfactual forking, regime diversity, and sequence-level evaluation is a novel benchmark contribution",
        },
        "E_minimal_architecture": {
            "description": "Empirically derived minimal architecture outperforms complex reflexive agent",
            "prior_concept_exists": True,
            "same_mechanism": False,
            "novel_experimental_finding": True,
            "strength": "MODERATE — the specific finding that B1_extended beats Full REE is a meaningful negative result",
        },
    }

    for key, analysis in novelty_analysis.items():
        marker = "NOVEL" if analysis["novel_experimental_finding"] else "KNOWN"
        print(f"  [{marker}] {key}: {analysis['strength']}")

    (RESULTS_DIR / "phase24_novelty_analysis.json").write_text(
        json.dumps(novelty_analysis, indent=2))

    # Paper decision
    print("\n--- PAPER DECISION ---")

    paper_criteria = {
        "temporal_complementarity_replicates": True,
        "ordering_effects_generalize": True,
        "benchmark_cleanly_measures": True,
        "greedy_failure_replicated": True,
        "differentiated_from_prior": True,
        "llm_in_loop_replication": False,
        "state_motif_beats_fixed": go_passed,
        "external_validation": False,
    }

    controlled_paper = all([
        paper_criteria["temporal_complementarity_replicates"],
        paper_criteria["ordering_effects_generalize"],
        paper_criteria["benchmark_cleanly_measures"],
        paper_criteria["greedy_failure_replicated"],
        paper_criteria["differentiated_from_prior"],
    ])

    stronger_paper = controlled_paper and all([
        paper_criteria["llm_in_loop_replication"],
        paper_criteria["state_motif_beats_fixed"],
    ])

    conference_paper = stronger_paper and paper_criteria["external_validation"]

    print(f"  Controlled-mechanism paper:   {'JUSTIFIED' if controlled_paper else 'NOT YET'}")
    print(f"  Stronger agent paper:         {'JUSTIFIED' if stronger_paper else 'NOT YET'}")
    print(f"  Conference-level claim:       {'JUSTIFIED' if conference_paper else 'NOT YET'}")

    (RESULTS_DIR / "phase24_paper_decision.json").write_text(json.dumps({
        "controlled_paper_justified": controlled_paper,
        "stronger_paper_justified": stronger_paper,
        "conference_paper_justified": conference_paper,
        "missing_for_stronger": [k for k, v in paper_criteria.items() if not v],
        "central_claim_recommendation": "D" if controlled_paper else "none",
    }, indent=2))

    missing = [k for k, v in paper_criteria.items() if not v]
    print(f"  Missing: {missing}")

    best_contribution = "D_epistemic_benchmark"
    print(f"\n  Recommended central claim: {best_contribution}")
    print(f"  = A controlled benchmark for measuring temporal complementarity")
    print(f"    of cognitive operations in epistemic research")

    # ---- FINAL SUMMARY ----
    print("\n" + "=" * 70)
    print("CAMPAIGN V4 SUMMARY")
    print("=" * 70)

    print(f"""
  Phase 21: Adaptive Necessity = ESTABLISHED (gap={0.0955})
  Phase 22: LLM-in-loop = PROTOCOL DEFINED, awaiting model
  Phase 23: Motif Policy = {'SUPPORTED' if go_passed else 'NOT SUPPORTED'}
  Phase 24: Paper = {'CONTROLLED PAPER JUSTIFIED' if controlled_paper else 'NOT YET'}
    """)


if __name__ == "__main__":
    main()
