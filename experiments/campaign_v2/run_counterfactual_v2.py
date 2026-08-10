"""
Phase 15 — Counterfactual Cognitive Action Study on Semantic Simulator.

For each sampled epistemic state E_t, fork into all feasible cognitive actions:
  retrieve, generate_hypothesis, attack_hypothesis, reason, stop

Execute each fork under identical continuation budget.
Compute RealizedEpistemicGain for each (E, a) pair.
Compare against oracle action values from the simulator.

Target: 1000+ distinct source states, several thousand (state, action) outcomes.
"""

from __future__ import annotations

import asyncio
import json
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from asar.common import generate_id
from asar.epistemic.reducer import StateReducer
from asar.epistemic.store import AppendOnlyEventStore
from asar.evaluation.scenarios.semantic_generators import SEMANTIC_FAMILY_GENERATORS
from asar.evaluation.semantic_runner import (
    SemanticBenchmarkRunner,
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
from asar.metacognition.trajectory import TrajectoryDataset
from asar.operators.registry import OperatorRegistry
from asar.operators.stop import StopOperator
from schemas.ree.epistemic_state import BudgetState, SelfModelSummary

RESULTS_DIR = Path(__file__).parent / "results"
CAMPAIGN_V2_BASE_SEED = 7777


@dataclass
class CounterfactualOutcome:
    """Result of forcing one cognitive action from a state."""
    source_state_id: str
    source_episode: str
    world_id: str
    family: str
    step: int
    forced_action: str
    estimated_bid: float
    oracle_value: float
    realized_quality: float
    quality_delta: float
    tokens_used: int
    hypothesis_count: int
    evidence_count: int
    ignorance_count: int
    hypothesis_entropy: float
    top_margin: float
    budget_fraction: float
    contradiction_density: float
    ignorance_priority: float
    workspace_saturation: float


async def fork_and_evaluate(
    world: LatentWorld,
    fork_state: "EpistemicState",
    action_type: str,
    continuation_budget: int,
    family: str,
) -> CounterfactualOutcome | None:
    """Fork from an epistemic state. Force ONE action, then continue with heuristic."""
    from schemas.ree.epistemic_state import EpistemicState as ES

    sim = EpistemicWorldSimulator(world, seed=hash(f"{fork_state.process.episode_id}_{action_type}") % 10000)

    for eid in fork_state.evidence_ids:
        art = fork_state.artifacts.get(eid)
        if isinstance(art, dict) and "world_evidence_id" in art:
            sim._retrieved.add(art["world_evidence_id"])

    for hid in fork_state.hypothesis_ids:
        art = fork_state.artifacts.get(hid)
        if isinstance(art, dict) and "world_hypothesis_id" in art:
            sim._generated_hypotheses.add(art["world_hypothesis_id"])

    operators = {
        "retrieve": SimRetrieveOperator(sim),
        "generate_hypothesis": SimHypothesisOperator(sim),
        "attack_hypothesis": SimAttackOperator(sim),
        "reason": SimReasonOperator(sim),
    }

    if action_type == "stop":
        quality = SemanticBenchmarkRunner()._evaluate(sim, fork_state)
        return CounterfactualOutcome(
            source_state_id=f"{fork_state.process.episode_id}_v{fork_state.version}",
            source_episode=fork_state.process.episode_id,
            world_id=world.world_id,
            family=family,
            step=fork_state.process.step_count,
            forced_action="stop",
            estimated_bid=0.0,
            oracle_value=sim.oracle_action_value("stop",
                set(fork_state.evidence_ids), set(fork_state.hypothesis_ids)),
            realized_quality=quality.scalar_quality(),
            quality_delta=0.0,
            tokens_used=0,
            hypothesis_count=len(fork_state.views.hypotheses),
            evidence_count=len(fork_state.evidence_ids),
            ignorance_count=len(fork_state.views.ignorance_items),
            hypothesis_entropy=fork_state.views.hypothesis_entropy,
            top_margin=fork_state.views.top_hypothesis_margin,
            budget_fraction=fork_state.budget.budget_fraction_remaining,
            contradiction_density=fork_state.views.contradiction_density,
            ignorance_priority=fork_state.views.highest_ignorance_priority,
            workspace_saturation=fork_state.views.workspace_saturation,
        )

    op = operators.get(action_type)
    if op is None:
        return None

    from schemas.ree.epistemic_event import EpistemicAction, ActionType, EpistemicEvent, EpistemicActionBid

    bids = await op.propose(fork_state)
    if not bids:
        return None

    bid = bids[0]
    result = await op.execute(fork_state, bid.action)

    reducer = StateReducer()
    event = EpistemicEvent(
        event_id=generate_id("event"),
        episode_id=fork_state.process.episode_id,
        version_before=fork_state.version,
        version_after=fork_state.version + 1,
        action=bid.action,
        result=result,
        resource_cost=result.resource_cost,
        rationale=f"Forced: {action_type}",
    )
    post_state = reducer.apply(fork_state, event)

    reg = OperatorRegistry()
    reg.register(SimRetrieveOperator(sim))
    reg.register(SimHypothesisOperator(sim))
    reg.register(SimAttackOperator(sim))
    reg.register(SimReasonOperator(sim))
    reg.register(StopOperator())

    cont_budget = BudgetState(max_tokens=continuation_budget, max_steps=10)
    post_state_with_budget = post_state.model_copy(update={
        "budget": cont_budget,
        "process": post_state.process.model_copy(update={"status": "active"}),
    })

    store = AppendOnlyEventStore()
    ctrl = EpistemicController(
        registry=reg,
        event_store=store,
        budget=cont_budget,
        stopping_policy=StoppingPolicy(),
    )

    final_state = post_state_with_budget
    while final_state.process.status == "active" and not final_state.budget.is_exhausted:
        final_state = await ctrl._step(final_state)

    if final_state.process.status == "active" and final_state.budget.is_exhausted:
        stop_event = ctrl._make_stop_event(final_state, "budget exhausted")
        store.append(stop_event)
        final_state = ctrl.reducer.apply(final_state, stop_event)

    quality = SemanticBenchmarkRunner()._evaluate(sim, final_state)
    oracle_val = sim.oracle_action_value(
        action_type,
        set(fork_state.evidence_ids), set(fork_state.hypothesis_ids),
    )

    return CounterfactualOutcome(
        source_state_id=f"{fork_state.process.episode_id}_v{fork_state.version}",
        source_episode=fork_state.process.episode_id,
        world_id=world.world_id,
        family=family,
        step=fork_state.process.step_count,
        forced_action=action_type,
        estimated_bid=bid.expected_information_gain,
        oracle_value=oracle_val,
        realized_quality=quality.scalar_quality(),
        quality_delta=0.0,
        tokens_used=final_state.budget.tokens_used,
        hypothesis_count=len(final_state.views.hypotheses),
        evidence_count=len(final_state.evidence_ids),
        ignorance_count=len(final_state.views.ignorance_items),
        hypothesis_entropy=fork_state.views.hypothesis_entropy,
        top_margin=fork_state.views.top_hypothesis_margin,
        budget_fraction=fork_state.budget.budget_fraction_remaining,
        contradiction_density=fork_state.views.contradiction_density,
        ignorance_priority=fork_state.views.highest_ignorance_priority,
        workspace_saturation=fork_state.views.workspace_saturation,
    )


async def collect_states_and_fork(
    family_name: str,
    world: LatentWorld,
    n_states: int = 5,
) -> list[CounterfactualOutcome]:
    """Run one episode, reconstruct states via replay, fork from each."""
    sim = EpistemicWorldSimulator(world, seed=42)
    reg = OperatorRegistry()
    reg.register(SimRetrieveOperator(sim))
    reg.register(SimHypothesisOperator(sim))
    reg.register(SimAttackOperator(sim))
    reg.register(SimReasonOperator(sim))
    reg.register(StopOperator())

    store = AppendOnlyEventStore()
    budget = BudgetState(max_tokens=5000, max_steps=25)

    ctrl = EpistemicController(
        registry=reg,
        event_store=store,
        budget=budget,
    )

    final_state = await ctrl.run(world.world_id, budget=budget)

    events = store.get_all()
    reducer = StateReducer()

    from schemas.ree.epistemic_state import EpistemicState, ProcessState
    state = EpistemicState(
        version=0,
        process=ProcessState(episode_id=final_state.process.episode_id, goal=world.world_id),
        budget=budget,
    )

    states: list[EpistemicState] = [state]
    for event in events:
        state = reducer.apply(state, event)
        states.append(state)

    sample_indices = list(range(min(n_states, len(states) - 1)))

    outcomes = []
    actions = ["retrieve", "generate_hypothesis", "attack_hypothesis", "reason", "stop"]
    for idx in sample_indices:
        fork_state = states[idx]
        if fork_state.process.status != "active":
            continue
        for action in actions:
            try:
                outcome = await fork_and_evaluate(
                    world, fork_state, action,
                    continuation_budget=3000,
                    family=family_name,
                )
                if outcome:
                    outcomes.append(outcome)
            except Exception:
                continue

    return outcomes


async def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("PHASE 15 - COUNTERFACTUAL COGNITIVE ACTION STUDY V2")
    print("=" * 60)

    all_outcomes: list[CounterfactualOutcome] = []
    n_states_per_world = 5
    n_worlds_per_family = 20

    for family_name, gen_fn in SEMANTIC_FAMILY_GENERATORS.items():
        print(f"\n--- Family: {family_name} ---")
        family_outcomes = []

        for idx in range(n_worlds_per_family):
            world = gen_fn(index=idx, seed=CAMPAIGN_V2_BASE_SEED + idx)
            outcomes = await collect_states_and_fork(
                family_name, world, n_states=n_states_per_world,
            )
            family_outcomes.extend(outcomes)

        all_outcomes.extend(family_outcomes)
        print(f"  States forked: {len(family_outcomes)}")

        by_action = defaultdict(list)
        for o in family_outcomes:
            by_action[o.forced_action].append(o.realized_quality)
        for action in sorted(by_action.keys()):
            quals = by_action[action]
            mean_q = statistics.mean(quals) if quals else 0
            print(f"    {action:25s}: mean_quality={mean_q:.4f} (n={len(quals)})")

    print(f"\n{'=' * 60}")
    print(f"TOTAL OUTCOMES: {len(all_outcomes)}")
    print(f"DISTINCT SOURCE STATES: {len(set(o.source_state_id for o in all_outcomes))}")
    print(f"{'=' * 60}")

    # Compute per-state best action and regret
    by_state = defaultdict(list)
    for o in all_outcomes:
        by_state[o.source_state_id].append(o)

    regrets = []
    best_action_counter = Counter()
    for state_id, outcomes in by_state.items():
        best = max(outcomes, key=lambda o: o.realized_quality)
        best_action_counter[best.forced_action] += 1
        for o in outcomes:
            regret = best.realized_quality - o.realized_quality
            regrets.append({
                "state_id": state_id,
                "family": o.family,
                "forced_action": o.forced_action,
                "realized_quality": o.realized_quality,
                "best_quality": best.realized_quality,
                "regret": regret,
                "oracle_value": o.oracle_value,
                "estimated_bid": o.estimated_bid,
            })

    print("\n--- BEST ACTION DISTRIBUTION ---")
    for action, count in best_action_counter.most_common():
        print(f"  {action:25s}: {count} ({count/len(by_state)*100:.1f}%)")

    print("\n--- MEAN REGRET BY ACTION ---")
    by_action_regret = defaultdict(list)
    for r in regrets:
        by_action_regret[r["forced_action"]].append(r["regret"])
    for action in sorted(by_action_regret.keys()):
        regs = by_action_regret[action]
        print(f"  {action:25s}: mean_regret={statistics.mean(regs):.4f} (n={len(regs)})")

    # Bid-value correlation
    print("\n--- BID vs REALIZED VALUE ---")
    bids = [r["estimated_bid"] for r in regrets]
    vals = [r["realized_quality"] for r in regrets]
    if len(set(bids)) > 1 and len(set(vals)) > 1:
        n = len(bids)
        mean_b = sum(bids) / n
        mean_v = sum(vals) / n
        cov = sum((b - mean_b) * (v - mean_v) for b, v in zip(bids, vals)) / n
        std_b = (sum((b - mean_b) ** 2 for b in bids) / n) ** 0.5
        std_v = (sum((v - mean_v) ** 2 for v in vals) / n) ** 0.5
        corr = cov / (std_b * std_v) if std_b > 0 and std_v > 0 else 0
        print(f"  Bid-value correlation: r = {corr:.4f}")
    else:
        print("  Insufficient variance for correlation")

    # Oracle vs realized correlation
    print("\n--- ORACLE vs REALIZED VALUE ---")
    oracle_vals = [r["oracle_value"] for r in regrets]
    if len(set(oracle_vals)) > 1 and len(set(vals)) > 1:
        n = len(oracle_vals)
        mean_o = sum(oracle_vals) / n
        mean_v = sum(vals) / n
        cov = sum((o - mean_o) * (v - mean_v) for o, v in zip(oracle_vals, vals)) / n
        std_o = (sum((o - mean_o) ** 2 for o in oracle_vals) / n) ** 0.5
        std_v = (sum((v - mean_v) ** 2 for v in vals) / n) ** 0.5
        corr = cov / (std_o * std_v) if std_o > 0 and std_v > 0 else 0
        print(f"  Oracle-realized correlation: r = {corr:.4f}")
    else:
        print("  Insufficient variance for correlation")

    # Save all data
    records = []
    for o in all_outcomes:
        records.append({
            "source_state_id": o.source_state_id,
            "source_episode": o.source_episode,
            "world_id": o.world_id,
            "family": o.family,
            "step": o.step,
            "forced_action": o.forced_action,
            "estimated_bid": o.estimated_bid,
            "oracle_value": o.oracle_value,
            "realized_quality": o.realized_quality,
            "tokens_used": o.tokens_used,
            "hypothesis_count": o.hypothesis_count,
            "evidence_count": o.evidence_count,
            "ignorance_count": o.ignorance_count,
            "hypothesis_entropy": o.hypothesis_entropy,
            "top_margin": o.top_margin,
            "budget_fraction": o.budget_fraction,
            "contradiction_density": o.contradiction_density,
            "ignorance_priority": o.ignorance_priority,
            "workspace_saturation": o.workspace_saturation,
        })

    out_path = RESULTS_DIR / "counterfactual_v2.jsonl"
    with open(out_path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    regret_path = RESULTS_DIR / "regret_analysis_v2.json"
    Path(regret_path).write_text(json.dumps(regrets, indent=2))

    print(f"\nCounterfactual data: {out_path}")
    print(f"Regret analysis: {regret_path}")


if __name__ == "__main__":
    asyncio.run(main())
