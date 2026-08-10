"""
Benchmark runner — executes controlled scenarios against architectures.

Supports equal-budget comparison, ablation switches, and raw artifact persistence.
Uses mock providers for deterministic controlled experiments.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from asar.common import generate_id
from asar.epistemic.reducer import StateReducer
from asar.epistemic.store import AppendOnlyEventStore
from asar.evaluation.baselines import (
    BaselineResult,
    DirectModelBaseline,
    FixedDepthREEBaseline,
    REEAdaptiveBaseline,
    SimpleReflectionBaseline,
)
from asar.evaluation.scenario import (
    AblationConfig,
    ScenarioResult,
    ScenarioSpec,
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
    EpistemicEvent,
    OperatorOutcome,
    OperatorResult,
)
from schemas.ree.epistemic_state import (
    BudgetState,
    EpistemicState,
    ResourceCost,
    SelfModelSummary,
)
from schemas.ree.experiment import ExperimentManifest, MechanismConfig


# ---------------------------------------------------------------
# Mock operator that reads from scenario evidence pool
# ---------------------------------------------------------------

class ScenarioRetrieveOperator:
    """Deterministic retrieve operator that returns scenario evidence."""

    def __init__(self, evidence_pool: tuple[dict[str, Any], ...]) -> None:
        self._pool = evidence_pool
        self._retrieved = 0

    @property
    def name(self) -> str:
        return "retrieve"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        if state.budget.is_exhausted or state.process.status != "active":
            return []
        if self._retrieved >= len(self._pool):
            return []

        p_success = state.views.self_model.operator_success_rates.get(
            self.name, state.views.self_model.overall_success_rate
        )
        base_gain = 0.6 if self._retrieved < 3 else 0.3

        ignorance_boost = 0.0
        for iv in state.views.ignorance_items.values():
            if iv.status == "open":
                ignorance_boost = max(ignorance_boost, iv.priority * 0.3)

        return [EpistemicActionBid(
            action=EpistemicAction(
                action_id=generate_id("action"),
                action_type=ActionType.RETRIEVE,
                operator_name=self.name,
            ),
            expected_information_gain=min(1.0, (base_gain + ignorance_boost) * p_success),
            estimated_token_cost=100,
            failure_risk=max(0.0, 1.0 - p_success),
        )]

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        if self._retrieved >= len(self._pool):
            return OperatorResult(
                operator_name=self.name, action_id=action.action_id,
                outcome=OperatorOutcome.NO_OP,
                resource_cost=ResourceCost(input_tokens=10, output_tokens=10),
            )

        item = self._pool[self._retrieved]
        self._retrieved += 1
        eid = generate_id("evidence")

        artifacts: dict[str, Any] = {eid: {
            "content": item["claim"],
            "source_id": item.get("source_id", "unknown"),
            "confidence": item.get("confidence", 0.5),
            "source_type": item.get("source_type", "unknown"),
            "parent_source": item.get("parent_source"),
        }}

        return OperatorResult(
            operator_name=self.name, action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS,
            artifacts_produced=artifacts,
            workspace_additions=[eid],
            resource_cost=ResourceCost(input_tokens=50, output_tokens=50),
        )


class ScenarioHypothesisOperator:
    """Generates hypotheses based on scenario evidence."""

    @property
    def name(self) -> str:
        return "generate_hypothesis"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        if state.budget.is_exhausted or state.process.status != "active":
            return []
        if not state.evidence_ids:
            return []
        if len(state.views.hypotheses) >= 4:
            return []

        p_success = state.views.self_model.operator_success_rates.get(
            self.name, state.views.self_model.overall_success_rate
        )
        base_gain = 0.7 if len(state.views.hypotheses) < 2 else 0.3
        return [EpistemicActionBid(
            action=EpistemicAction(
                action_id=generate_id("action"),
                action_type=ActionType.GENERATE_HYPOTHESIS,
                operator_name=self.name,
            ),
            expected_information_gain=min(1.0, base_gain * p_success),
            estimated_token_cost=200,
        )]

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        claims = [state.artifacts.get(eid, {}).get("content", "")
                  for eid in state.evidence_ids if isinstance(state.artifacts.get(eid), dict)]

        h_idx = len(state.views.hypotheses)
        hid = generate_id("hypothesis")
        combined = " ".join(c[:50] for c in claims)
        artifacts = {hid: {
            "statement": f"Hypothesis {h_idx}: based on {combined[:100]}",
            "prior": 0.5,
            "posterior": 0.5,
            "status": "proposed",
            "generation_method": "abduction",
        }}

        return OperatorResult(
            operator_name=self.name, action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS,
            artifacts_produced=artifacts,
            workspace_additions=[hid],
            resource_cost=ResourceCost(input_tokens=100, output_tokens=100),
        )


# ---------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------

@dataclass
class BenchmarkRunResult:
    """Complete result of running a benchmark scenario."""
    scenario_id: str
    architecture: str
    manifest: ExperimentManifest
    result: ScenarioResult
    trajectory_steps: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)


class BenchmarkRunner:
    """Runs controlled benchmark scenarios against architectures."""

    def __init__(
        self,
        *,
        output_dir: Path | None = None,
        default_budget: BudgetState | None = None,
    ) -> None:
        self._output_dir = output_dir
        self._default_budget = default_budget or BudgetState(
            max_tokens=5000, max_steps=15,
        )

    async def run_scenario(
        self,
        scenario: ScenarioSpec,
        *,
        architecture: str = "full_ree",
        ablation: dict[str, bool] | None = None,
        budget: BudgetState | None = None,
        self_model: SelfModelSummary | None = None,
    ) -> BenchmarkRunResult:
        """Run a single scenario through a given architecture."""
        effective_budget = budget or self._default_budget
        manifest = self._create_manifest(
            scenario, architecture, ablation, effective_budget,
        )

        if architecture == "B0_direct":
            baseline_result = await DirectModelBaseline().run(
                scenario.question, budget=effective_budget,
            )
            return self._wrap_baseline(scenario, manifest, baseline_result)

        if architecture == "B1_reflection":
            baseline_result = await SimpleReflectionBaseline().run(
                scenario.question, budget=effective_budget,
            )
            return self._wrap_baseline(scenario, manifest, baseline_result)

        reg = self._build_registry(scenario, ablation or {})
        store = AppendOnlyEventStore()
        traj = TrajectoryDataset()

        ctrl = EpistemicController(
            registry=reg,
            event_store=store,
            budget=effective_budget,
            trajectory=traj,
            self_model_summary=self_model,
        )

        final_state = await ctrl.run(scenario.question, budget=effective_budget)

        scenario_result = ScenarioResult(
            scenario_id=scenario.scenario_id,
            architecture=architecture,
            experiment_id=manifest.experiment_id,
            tokens_used=final_state.budget.tokens_used,
            steps_used=final_state.process.step_count,
            hypotheses=[
                {"id": hid, "posterior": hv.posterior, "status": hv.status}
                for hid, hv in final_state.views.hypotheses.items()
            ],
            ignorance_items=[
                {"id": iid, "priority": iv.priority, "status": iv.status}
                for iid, iv in final_state.views.ignorance_items.items()
            ],
            raw_events=[e.model_dump() for e in store.get_all()],
            raw_state=final_state.model_dump(),
        )

        return BenchmarkRunResult(
            scenario_id=scenario.scenario_id,
            architecture=architecture,
            manifest=manifest,
            result=scenario_result,
            trajectory_steps=len(traj),
            events=scenario_result.raw_events,
        )

    def _build_registry(
        self,
        scenario: ScenarioSpec,
        ablation: dict[str, bool],
    ) -> OperatorRegistry:
        reg = OperatorRegistry()
        reg.register(ScenarioRetrieveOperator(scenario.evidence_pool))
        reg.register(ScenarioHypothesisOperator())
        reg.register(StopOperator())
        return reg

    def _create_manifest(
        self,
        scenario: ScenarioSpec,
        architecture: str,
        ablation: dict[str, bool] | None,
        budget: BudgetState,
    ) -> ExperimentManifest:
        mechanisms = {}
        if ablation:
            for name, enabled in ablation.items():
                mechanisms[name] = MechanismConfig(enabled=enabled)

        return ExperimentManifest(
            experiment_id=generate_id("experiment"),
            architecture=architecture,
            description=f"Benchmark: {scenario.family} / {scenario.scenario_id}",
            mechanisms=mechanisms,
            budget_max_tokens=budget.max_tokens,
            budget_max_steps=budget.max_steps,
            seed=scenario.seed,
            scenario_split=scenario.split,
        )

    def _wrap_baseline(
        self,
        scenario: ScenarioSpec,
        manifest: ExperimentManifest,
        result: BaselineResult,
    ) -> BenchmarkRunResult:
        return BenchmarkRunResult(
            scenario_id=scenario.scenario_id,
            architecture=result.baseline_name,
            manifest=manifest,
            result=ScenarioResult(
                scenario_id=scenario.scenario_id,
                architecture=result.baseline_name,
                experiment_id=manifest.experiment_id,
                tokens_used=result.tokens_used,
                steps_used=result.steps_used,
            ),
            events=result.events,
        )
