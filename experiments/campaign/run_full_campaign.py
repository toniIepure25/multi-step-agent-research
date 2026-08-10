"""
ASAR-REE Full Scientific Campaign Runner.

Executes all holdout scenarios across all architecture conditions,
collects CognitiveActionOutcome data, runs ablation comparisons,
and produces machine-readable result artifacts.

This is the actual experiment execution, not infrastructure.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# -- Infrastructure imports --
from asar.common import generate_id
from asar.epistemic.reducer import StateReducer
from asar.epistemic.store import AppendOnlyEventStore
from asar.evaluation.baselines import (
    DirectModelBaseline,
    FixedDepthREEBaseline,
    REEAdaptiveBaseline,
    SimpleReflectionBaseline,
)
from asar.evaluation.benchmark_runner import (
    BenchmarkRunner,
    BenchmarkRunResult,
    ScenarioHypothesisOperator,
    ScenarioRetrieveOperator,
)
from asar.evaluation.counterfactual_study import (
    CognitiveActionOutcomeDataset,
    CounterfactualForkRunner,
    compute_realized_gain,
    extract_state_features,
    fork_and_execute,
)
from asar.evaluation.scenario import AblationConfig, ScenarioSpec
from asar.evaluation.scenarios.generators import generate_all_scenarios
from asar.evaluation.statistical import (
    ExperimentSummary,
    bootstrap_ci,
    paired_comparison,
    win_tie_loss,
)
from asar.metacognition.controller import EpistemicController
from asar.metacognition.stopping import StoppingPolicy
from asar.metacognition.trajectory import TrajectoryDataset
from asar.operators.registry import OperatorRegistry
from asar.operators.stop import StopOperator
from schemas.ree.epistemic_event import (
    ActionType,
    EpistemicAction,
    EpistemicActionBid,
    OperatorOutcome,
    OperatorResult,
)
from schemas.ree.epistemic_state import (
    BudgetState,
    EpistemicState,
    ProcessState,
    ResourceCost,
    SelfModelSummary,
)
from schemas.ree.experiment import (
    CognitiveActionOutcome,
    CognitiveActionRegret,
    EpistemicStateFeatures,
    ExperimentManifest,
    MechanismConfig,
    RealizedEpistemicGain,
)


OUTPUT_DIR = Path("experiments/campaign/results")


# ---------------------------------------------------------------
# Campaign result types
# ---------------------------------------------------------------

@dataclass
class RunRecord:
    scenario_id: str
    family: str
    seed: int
    split: str
    architecture: str
    budget_tokens: int
    steps_used: int
    tokens_used: int
    hypothesis_count: int
    evidence_count: int
    claim_count: int
    ignorance_count: int
    hypothesis_entropy: float
    highest_ignorance_priority: float
    workspace_saturation: float
    operator_sequence: list[str]
    final_status: str
    manifest_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "family": self.family,
            "seed": self.seed,
            "split": self.split,
            "architecture": self.architecture,
            "budget_tokens": self.budget_tokens,
            "steps_used": self.steps_used,
            "tokens_used": self.tokens_used,
            "hypothesis_count": self.hypothesis_count,
            "evidence_count": self.evidence_count,
            "claim_count": self.claim_count,
            "ignorance_count": self.ignorance_count,
            "hypothesis_entropy": self.hypothesis_entropy,
            "highest_ignorance_priority": self.highest_ignorance_priority,
            "workspace_saturation": self.workspace_saturation,
            "operator_sequence": self.operator_sequence,
            "final_status": self.final_status,
            "manifest_id": self.manifest_id,
        }


def extract_record(
    scenario: ScenarioSpec,
    architecture: str,
    budget_tokens: int,
    result: BenchmarkRunResult,
) -> RunRecord:
    state = result.result.raw_state
    views = state.get("views", {}) if isinstance(state, dict) else {}

    return RunRecord(
        scenario_id=scenario.scenario_id,
        family=scenario.family,
        seed=scenario.seed,
        split=scenario.split,
        architecture=architecture,
        budget_tokens=budget_tokens,
        steps_used=result.result.steps_used,
        tokens_used=result.result.tokens_used,
        hypothesis_count=len(result.result.hypotheses),
        evidence_count=len(state.get("evidence_ids", [])) if isinstance(state, dict) else 0,
        claim_count=len(state.get("claim_ids", [])) if isinstance(state, dict) else 0,
        ignorance_count=len(result.result.ignorance_items),
        hypothesis_entropy=views.get("hypothesis_entropy", 0.0),
        highest_ignorance_priority=views.get("highest_ignorance_priority", 0.0),
        workspace_saturation=views.get("workspace_saturation", 0.0),
        operator_sequence=state.get("operator_history", []) if isinstance(state, dict) else [],
        final_status=state.get("process", {}).get("status", "unknown") if isinstance(state, dict) else "unknown",
        manifest_id=result.manifest.experiment_id,
    )


# ---------------------------------------------------------------
# Campaign execution
# ---------------------------------------------------------------

async def run_holdout_campaign(
    scenarios: list[ScenarioSpec],
    budgets: list[int],
    architectures: list[str],
) -> list[RunRecord]:
    """Execute all holdout scenarios × architectures × budgets."""
    records: list[RunRecord] = []

    for budget_tokens in budgets:
        budget = BudgetState(max_tokens=budget_tokens, max_steps=budget_tokens // 200)

        for arch in architectures:
            runner = BenchmarkRunner(default_budget=budget)

            for scenario in scenarios:
                try:
                    result = await runner.run_scenario(
                        scenario,
                        architecture=arch,
                        budget=budget,
                    )
                    record = extract_record(scenario, arch, budget_tokens, result)
                    records.append(record)
                except Exception as exc:
                    print(f"  FAILED: {scenario.scenario_id} / {arch} / {budget_tokens}: {exc}")

    return records


async def run_counterfactual_fork_campaign(
    scenarios: list[ScenarioSpec],
    budget: BudgetState,
) -> CognitiveActionOutcomeDataset:
    """Collect CognitiveActionOutcome data via state forking."""
    dataset = CognitiveActionOutcomeDataset()
    fork_runner = CounterfactualForkRunner(dataset=dataset)

    for scenario in scenarios:
        retrieve_op = ScenarioRetrieveOperator(scenario.evidence_pool)
        hypothesis_op = ScenarioHypothesisOperator()
        stop_op = StopOperator()

        reg = OperatorRegistry()
        reg.register(retrieve_op)
        reg.register(hypothesis_op)
        reg.register(stop_op)
        store = AppendOnlyEventStore()
        traj = TrajectoryDataset()

        ctrl = EpistemicController(
            registry=reg, event_store=store, budget=budget, trajectory=traj,
        )
        final_state = await ctrl.run(scenario.question, budget=budget)

        events = store.get_all()
        reducer = StateReducer()

        initial_state = EpistemicState(
            version=0,
            process=ProcessState(episode_id=final_state.process.episode_id, goal=scenario.question),
            budget=budget,
        )
        state = initial_state
        for i, event in enumerate(events):
            if i > 0 and i < len(events) - 1:
                fork_ops = [
                    ScenarioRetrieveOperator(scenario.evidence_pool),
                    ScenarioHypothesisOperator(),
                    StopOperator(),
                ]
                await fork_runner.run_fork(
                    state, fork_ops,
                    selected_action=event.action.action_type.value,
                    selected_bid_score=event.decision.selection_score if event.decision else 0.0,
                )
            state = reducer.apply(state, event)

    return dataset


async def run_ablation_campaign(
    scenarios: list[ScenarioSpec],
    budget: BudgetState,
) -> dict[str, list[RunRecord]]:
    """Run leave-one-out and core-only ablation comparisons."""
    results: dict[str, list[RunRecord]] = {}

    configs = {
        "full_ree": AblationConfig.full_ree(),
        "ree_core": AblationConfig.ree_core_only(),
        "baseline_none": AblationConfig.baseline_none(),
    }
    for mech in ["hypothesis_ecology", "ignorance_ledger", "self_model",
                  "evidence_independence", "epistemic_market", "stopping_policy"]:
        configs[f"ree_no_{mech}"] = AblationConfig.leave_one_out(mech)

    runner = BenchmarkRunner(default_budget=budget)

    for config_name, config in configs.items():
        records = []
        for scenario in scenarios:
            try:
                result = await runner.run_scenario(
                    scenario, architecture=config_name, ablation=config, budget=budget,
                )
                record = extract_record(scenario, config_name, budget.max_tokens, result)
                records.append(record)
            except Exception as exc:
                print(f"  ABLATION FAILED: {scenario.scenario_id}/{config_name}: {exc}")
        results[config_name] = records

    return results


# ---------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------

def analyze_by_family(records: list[RunRecord]) -> dict[str, dict[str, Any]]:
    """Break down results by scenario family and architecture."""
    families: dict[str, dict[str, list[RunRecord]]] = {}
    for r in records:
        families.setdefault(r.family, {}).setdefault(r.architecture, []).append(r)

    analysis: dict[str, dict[str, Any]] = {}
    for family, archs in families.items():
        family_analysis: dict[str, Any] = {}
        for arch, recs in archs.items():
            steps = [r.steps_used for r in recs]
            tokens = [r.tokens_used for r in recs]
            hyp_counts = [r.hypothesis_count for r in recs]
            ign_counts = [r.ignorance_count for r in recs]
            evidence_counts = [r.evidence_count for r in recs]

            family_analysis[arch] = {
                "n": len(recs),
                "mean_steps": sum(steps) / len(steps) if steps else 0,
                "mean_tokens": sum(tokens) / len(tokens) if tokens else 0,
                "mean_hypotheses": sum(hyp_counts) / len(hyp_counts) if hyp_counts else 0,
                "mean_ignorance": sum(ign_counts) / len(ign_counts) if ign_counts else 0,
                "mean_evidence": sum(evidence_counts) / len(evidence_counts) if evidence_counts else 0,
                "steps_ci": bootstrap_ci(steps).lower if steps else 0,
                "steps_ci_upper": bootstrap_ci(steps).upper if steps else 0,
            }
        analysis[family] = family_analysis
    return analysis


def compute_pareto_data(records: list[RunRecord]) -> list[dict[str, Any]]:
    """Build quality-compute data for Pareto frontier analysis."""
    grouped: dict[tuple[str, int], list[RunRecord]] = {}
    for r in records:
        key = (r.architecture, r.budget_tokens)
        grouped.setdefault(key, []).append(r)

    points = []
    for (arch, budget), recs in grouped.items():
        quality = sum(r.hypothesis_count + r.evidence_count + r.claim_count for r in recs) / len(recs)
        compute = sum(r.tokens_used for r in recs) / len(recs)
        points.append({
            "architecture": arch,
            "budget": budget,
            "mean_quality": quality,
            "mean_compute": compute,
            "n": len(recs),
            "mean_steps": sum(r.steps_used for r in recs) / len(recs),
            "mean_hypotheses": sum(r.hypothesis_count for r in recs) / len(recs),
        })
    return points


def pairwise_architecture_comparison(
    records: list[RunRecord],
    arch_a: str,
    arch_b: str,
) -> dict[str, Any]:
    """Paired comparison between two architectures on matched scenarios."""
    a_by_scenario: dict[str, RunRecord] = {}
    b_by_scenario: dict[str, RunRecord] = {}
    for r in records:
        key = f"{r.scenario_id}_{r.budget_tokens}"
        if r.architecture == arch_a:
            a_by_scenario[key] = r
        elif r.architecture == arch_b:
            b_by_scenario[key] = r

    common = set(a_by_scenario.keys()) & set(b_by_scenario.keys())
    if not common:
        return {"n": 0, "note": "no matched scenarios"}

    steps_a = [a_by_scenario[k].steps_used for k in sorted(common)]
    steps_b = [b_by_scenario[k].steps_used for k in sorted(common)]
    tokens_a = [a_by_scenario[k].tokens_used for k in sorted(common)]
    tokens_b = [b_by_scenario[k].tokens_used for k in sorted(common)]
    hyp_a = [a_by_scenario[k].hypothesis_count for k in sorted(common)]
    hyp_b = [b_by_scenario[k].hypothesis_count for k in sorted(common)]
    ign_a = [a_by_scenario[k].ignorance_count for k in sorted(common)]
    ign_b = [b_by_scenario[k].ignorance_count for k in sorted(common)]

    steps_comp = paired_comparison(steps_a, steps_b, label_a=arch_a, label_b=arch_b, metric="steps")
    tokens_comp = paired_comparison(tokens_a, tokens_b, label_a=arch_a, label_b=arch_b, metric="tokens")
    hyp_comp = paired_comparison(hyp_a, hyp_b, label_a=arch_a, label_b=arch_b, metric="hypotheses")

    w, t, l = win_tie_loss(
        [a.hypothesis_count + a.evidence_count for a in [a_by_scenario[k] for k in sorted(common)]],
        [b.hypothesis_count + b.evidence_count for b in [b_by_scenario[k] for k in sorted(common)]],
    )

    return {
        "n": len(common),
        "steps": {
            "mean_a": steps_comp.mean_a, "mean_b": steps_comp.mean_b,
            "diff": steps_comp.mean_diff,
            "effect_size": steps_comp.effect_size.cohens_d,
            "interpretation": steps_comp.effect_size.interpretation,
            "ci_lower": steps_comp.ci.lower, "ci_upper": steps_comp.ci.upper,
        },
        "tokens": {
            "mean_a": tokens_comp.mean_a, "mean_b": tokens_comp.mean_b,
            "diff": tokens_comp.mean_diff,
            "effect_size": tokens_comp.effect_size.cohens_d,
        },
        "hypotheses": {
            "mean_a": hyp_comp.mean_a, "mean_b": hyp_comp.mean_b,
            "diff": hyp_comp.mean_diff,
            "effect_size": hyp_comp.effect_size.cohens_d,
        },
        "quality_wtl": {"wins": w, "ties": t, "losses": l},
    }


# ---------------------------------------------------------------
# Main campaign
# ---------------------------------------------------------------

async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("ASAR-REE SCIENTIFIC CAMPAIGN")
    print("=" * 70)

    # Generate scenarios
    all_scenarios = generate_all_scenarios(count_per_family=15, dev_fraction=0.7)
    holdout = [s for s in all_scenarios if s.split == "holdout"]
    dev = [s for s in all_scenarios if s.split == "dev"]

    print(f"\nScenarios: {len(all_scenarios)} total, {len(holdout)} holdout, {len(dev)} dev")

    # ---------------------------------------------------------------
    # CAMPAIGN 1: Holdout benchmark — all architectures × budgets
    # ---------------------------------------------------------------
    print("\n" + "=" * 70)
    print("CAMPAIGN 1: HOLDOUT BENCHMARKS")
    print("=" * 70)

    budgets = [2000, 5000, 10000, 20000]
    architectures = ["B0_direct", "B1_reflection", "full_ree"]

    all_records: list[RunRecord] = []
    for budget_tokens in budgets:
        budget = BudgetState(max_tokens=budget_tokens, max_steps=max(5, budget_tokens // 200))
        runner = BenchmarkRunner(default_budget=budget)

        for arch in architectures:
            arch_records = []
            for scenario in holdout:
                try:
                    result = await runner.run_scenario(scenario, architecture=arch, budget=budget)
                    record = extract_record(scenario, arch, budget_tokens, result)
                    arch_records.append(record)
                except Exception as exc:
                    print(f"  FAILED: {scenario.scenario_id}/{arch}/{budget_tokens}: {exc}")
            all_records.extend(arch_records)
            print(f"  {arch} @ {budget_tokens}tok: {len(arch_records)} runs, "
                  f"avg steps={sum(r.steps_used for r in arch_records)/max(1,len(arch_records)):.1f}, "
                  f"avg tokens={sum(r.tokens_used for r in arch_records)/max(1,len(arch_records)):.0f}")

    # Save raw records
    with (OUTPUT_DIR / "holdout_records.jsonl").open("w") as f:
        for r in all_records:
            f.write(json.dumps(r.to_dict()) + "\n")

    print(f"\nTotal holdout records: {len(all_records)}")

    # ---------------------------------------------------------------
    # CAMPAIGN 2: Ablation campaign on dev scenarios
    # ---------------------------------------------------------------
    print("\n" + "=" * 70)
    print("CAMPAIGN 2: ABLATION CAMPAIGN (dev scenarios)")
    print("=" * 70)

    ablation_budget = BudgetState(max_tokens=5000, max_steps=25)
    ablation_records: dict[str, list[RunRecord]] = await run_ablation_campaign(
        dev[:18], ablation_budget,
    )

    ablation_flat: list[RunRecord] = []
    for config_name, recs in ablation_records.items():
        ablation_flat.extend(recs)
        print(f"  {config_name}: {len(recs)} runs, "
              f"avg steps={sum(r.steps_used for r in recs)/max(1,len(recs)):.1f}")

    with (OUTPUT_DIR / "ablation_records.jsonl").open("w") as f:
        for r in ablation_flat:
            f.write(json.dumps(r.to_dict()) + "\n")

    # ---------------------------------------------------------------
    # CAMPAIGN 3: Counterfactual fork study
    # ---------------------------------------------------------------
    print("\n" + "=" * 70)
    print("CAMPAIGN 3: COUNTERFACTUAL FORK STUDY")
    print("=" * 70)

    cf_budget = BudgetState(max_tokens=5000, max_steps=25)
    cf_dataset = await run_counterfactual_fork_campaign(dev, cf_budget)

    print(f"  Total CognitiveActionOutcome records: {len(cf_dataset)}")
    print(f"  Distinct episodes: {len(cf_dataset.episode_ids())}")
    print(f"  Actions by type: {cf_dataset.mean_gain_by_action()}")

    # Save outcomes
    with (OUTPUT_DIR / "counterfactual_outcomes.jsonl").open("w") as f:
        for o in cf_dataset.all():
            f.write(o.model_dump_json() + "\n")

    # ---------------------------------------------------------------
    # ANALYSIS
    # ---------------------------------------------------------------
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)

    # Family breakdown
    family_analysis = analyze_by_family(all_records)
    with (OUTPUT_DIR / "family_analysis.json").open("w") as f:
        json.dump(family_analysis, f, indent=2, default=str)

    for family, archs in family_analysis.items():
        print(f"\n  {family}:")
        for arch, stats in archs.items():
            print(f"    {arch}: steps={stats['mean_steps']:.1f}, "
                  f"tokens={stats['mean_tokens']:.0f}, "
                  f"hyps={stats['mean_hypotheses']:.1f}, "
                  f"ign={stats['mean_ignorance']:.1f}")

    # Pairwise comparisons
    print("\n--- Pairwise Comparisons (holdout) ---")
    comparisons = {}
    pairs = [
        ("full_ree", "B0_direct"),
        ("full_ree", "B1_reflection"),
    ]
    for arch_a, arch_b in pairs:
        comp = pairwise_architecture_comparison(all_records, arch_a, arch_b)
        comparisons[f"{arch_a}_vs_{arch_b}"] = comp
        if comp["n"] > 0:
            print(f"\n  {arch_a} vs {arch_b} (n={comp['n']}):")
            print(f"    Steps: {comp['steps']['mean_a']:.1f} vs {comp['steps']['mean_b']:.1f} "
                  f"(d={comp['steps']['effect_size']:.2f}, {comp['steps']['interpretation']})")
            print(f"    Tokens: {comp['tokens']['mean_a']:.0f} vs {comp['tokens']['mean_b']:.0f}")
            print(f"    Hypotheses: {comp['hypotheses']['mean_a']:.1f} vs {comp['hypotheses']['mean_b']:.1f}")
            print(f"    Quality W/T/L: {comp['quality_wtl']}")

    with (OUTPUT_DIR / "pairwise_comparisons.json").open("w") as f:
        json.dump(comparisons, f, indent=2, default=str)

    # Pareto data
    pareto_data = compute_pareto_data(all_records)
    with (OUTPUT_DIR / "pareto_data.json").open("w") as f:
        json.dump(pareto_data, f, indent=2, default=str)

    print("\n--- Quality-Compute Pareto Data ---")
    for pt in sorted(pareto_data, key=lambda p: (p["architecture"], p["budget"])):
        print(f"  {pt['architecture']} @ {pt['budget']}tok: "
              f"quality={pt['mean_quality']:.1f}, compute={pt['mean_compute']:.0f}")

    # Ablation analysis
    print("\n--- Ablation Analysis ---")
    if "full_ree" in ablation_records and ablation_records["full_ree"]:
        full_steps = [r.steps_used for r in ablation_records["full_ree"]]
        full_hyps = [r.hypothesis_count for r in ablation_records["full_ree"]]
        for config_name, recs in ablation_records.items():
            if config_name == "full_ree" or not recs:
                continue
            n = min(len(full_steps), len(recs))
            abl_steps = [r.steps_used for r in recs[:n]]
            comp = paired_comparison(
                full_steps[:n], abl_steps,
                label_a="full_ree", label_b=config_name, metric="steps",
            )
            print(f"  full_ree vs {config_name}: "
                  f"steps diff={comp.mean_diff:.1f} (d={comp.effect_size.cohens_d:.2f})")

    # Counterfactual analysis
    print("\n--- Counterfactual Cognition Analysis ---")
    if len(cf_dataset) > 0:
        bid_corr = cf_dataset.bid_vs_realized_correlation()
        print(f"  Bid vs Realized correlation: {bid_corr:.3f}")

        importance = cf_dataset.feature_importance_proxy()
        print(f"  Top predictive features:")
        for feat, imp in list(importance.items())[:8]:
            print(f"    {feat}: {imp:.3f}")

        confusion = cf_dataset.action_confusion_matrix()
        print(f"  High-gain actions: {confusion.get('high_gain', {})}")
        print(f"  Low-gain actions: {confusion.get('low_gain', {})}")

        mean_gains = cf_dataset.mean_gain_by_action()
        print(f"  Mean scalarized gain by action: {mean_gains}")

    # Save counterfactual analysis
    cf_analysis = {
        "n_outcomes": len(cf_dataset),
        "n_episodes": len(cf_dataset.episode_ids()),
        "bid_vs_realized_correlation": cf_dataset.bid_vs_realized_correlation() if len(cf_dataset) > 0 else None,
        "feature_importance": cf_dataset.feature_importance_proxy() if len(cf_dataset) > 0 else {},
        "mean_gain_by_action": cf_dataset.mean_gain_by_action() if len(cf_dataset) > 0 else {},
        "confusion_matrix": cf_dataset.action_confusion_matrix() if len(cf_dataset) > 0 else {},
    }
    with (OUTPUT_DIR / "counterfactual_analysis.json").open("w") as f:
        json.dump(cf_analysis, f, indent=2, default=str)

    print("\n" + "=" * 70)
    print("CAMPAIGN COMPLETE")
    print(f"Total holdout records: {len(all_records)}")
    print(f"Total ablation records: {len(ablation_flat)}")
    print(f"Total counterfactual outcomes: {len(cf_dataset)}")
    print(f"Results written to: {OUTPUT_DIR}")
    print("=" * 70)

    return {
        "holdout_records": all_records,
        "ablation_records": ablation_records,
        "cf_dataset": cf_dataset,
        "family_analysis": family_analysis,
        "comparisons": comparisons,
        "pareto_data": pareto_data,
        "cf_analysis": cf_analysis,
    }


if __name__ == "__main__":
    asyncio.run(main())
