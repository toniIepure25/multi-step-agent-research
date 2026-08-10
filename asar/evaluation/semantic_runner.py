"""
Semantic Benchmark Runner — Campaign V2.

Uses EpistemicWorldSimulator for semantically meaningful experiments.
Supports true causal ablation where mechanism flags change runtime behavior.
Produces EpistemicQualityVector evaluations against latent world ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from asar.common import generate_id
from asar.epistemic.reducer import StateReducer
from asar.epistemic.store import AppendOnlyEventStore
from asar.evaluation.simulator import (
    EpistemicQualityVector,
    EpistemicWorldSimulator,
    LatentWorld,
)
from asar.metacognition.controller import EpistemicController
from asar.metacognition.market import DiversityAwareMarket, EpistemicMarket, RoundRobinMarket
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
    MaterializedViews,
    ProcessState,
    ResourceCost,
    SelfModelSummary,
)
from schemas.ree.experiment import ExperimentManifest, MechanismConfig


# ---------------------------------------------------------------
# Semantic operators that consult the EpistemicWorldSimulator
# ---------------------------------------------------------------

class SimRetrieveOperator:
    """Retrieves evidence from the simulated world."""

    PER_STEP_TOKENS = 500

    def __init__(self, sim: EpistemicWorldSimulator) -> None:
        self._sim = sim

    @property
    def name(self) -> str:
        return "retrieve"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        if state.budget.is_exhausted or state.process.status != "active":
            return []

        p_success = state.views.self_model.operator_success_rates.get(
            self.name, state.views.self_model.overall_success_rate
        )
        base_gain = 0.5
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
            estimated_token_cost=self.PER_STEP_TOKENS,
            failure_risk=max(0.0, 1.0 - p_success),
        )]

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        result = self._sim.retrieve(state.process.goal)
        if result is None:
            return OperatorResult(
                operator_name=self.name, action_id=action.action_id,
                outcome=OperatorOutcome.NO_OP,
                resource_cost=ResourceCost(input_tokens=50, output_tokens=50),
            )

        eid = f"evidence_{result['evidence_id']}"
        artifacts = {eid: {
            "content": result["content"],
            "source_id": result["source_id"],
            "confidence": result["confidence"],
            "parent_source": result["parent_source"],
            "supports": result["supports"],
            "contradicts": result["contradicts"],
            "information_value": result["information_value"],
            "world_evidence_id": result["evidence_id"],
        }}

        half = self.PER_STEP_TOKENS // 2
        return OperatorResult(
            operator_name=self.name, action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS,
            artifacts_produced=artifacts,
            workspace_additions=[eid],
            resource_cost=ResourceCost(input_tokens=half, output_tokens=half),
        )


class SimHypothesisOperator:
    """Generates hypotheses from the simulated world."""

    PER_STEP_TOKENS = 500

    def __init__(self, sim: EpistemicWorldSimulator) -> None:
        self._sim = sim

    @property
    def name(self) -> str:
        return "generate_hypothesis"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        if state.budget.is_exhausted or state.process.status != "active":
            return []
        if not state.evidence_ids:
            return []
        if len(state.views.hypotheses) >= 5:
            return []

        p_success = state.views.self_model.operator_success_rates.get(
            self.name, state.views.self_model.overall_success_rate
        )
        base_gain = 0.6 if len(state.views.hypotheses) < 2 else 0.3
        if state.views.hypothesis_entropy < 0.5 and len(state.views.hypotheses) > 0:
            base_gain += 0.15

        return [EpistemicActionBid(
            action=EpistemicAction(
                action_id=generate_id("action"),
                action_type=ActionType.GENERATE_HYPOTHESIS,
                operator_name=self.name,
            ),
            expected_information_gain=min(1.0, base_gain * p_success),
            estimated_token_cost=self.PER_STEP_TOKENS,
        )]

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        world_evidence_ids = []
        for eid in state.evidence_ids:
            art = state.artifacts.get(eid)
            if isinstance(art, dict):
                world_evidence_ids.append(art.get("world_evidence_id", eid))

        result = self._sim.generate_hypothesis(world_evidence_ids)
        if result is None:
            return OperatorResult(
                operator_name=self.name, action_id=action.action_id,
                outcome=OperatorOutcome.NO_OP,
                resource_cost=ResourceCost(input_tokens=50, output_tokens=50),
            )

        hid = f"hypothesis_{result['hypothesis_id']}"
        artifacts = {hid: {
            "statement": result["statement"],
            "prior": result["initial_plausibility"],
            "posterior": result["initial_plausibility"],
            "status": "proposed",
            "generation_method": result["generation_method"],
            "world_hypothesis_id": result["hypothesis_id"],
        }}

        half = self.PER_STEP_TOKENS // 2
        return OperatorResult(
            operator_name=self.name, action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS,
            artifacts_produced=artifacts,
            workspace_additions=[hid],
            resource_cost=ResourceCost(input_tokens=half, output_tokens=half),
        )


class SimAttackOperator:
    """Attacks hypotheses in the simulated world. Can discover hidden variables."""

    PER_STEP_TOKENS = 500

    def __init__(self, sim: EpistemicWorldSimulator) -> None:
        self._sim = sim
        self._attacks_without_result = 0

    @property
    def name(self) -> str:
        return "attack_hypothesis"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        if state.budget.is_exhausted or state.process.status != "active":
            return []
        if not state.views.hypotheses:
            return []

        p_success = state.views.self_model.operator_success_rates.get(
            self.name, state.views.self_model.overall_success_rate
        )
        ignorance_boost = 0.0
        for iv in state.views.ignorance_items.values():
            if iv.status == "open":
                ignorance_boost = max(ignorance_boost, iv.priority * 0.2)

        base_gain = 0.35 + ignorance_boost
        decay = max(0.1, 1.0 - self._attacks_without_result * 0.3)
        base_gain *= decay

        falsification_value = 0.4 * decay

        return [EpistemicActionBid(
            action=EpistemicAction(
                action_id=generate_id("action"),
                action_type=ActionType.ATTACK_HYPOTHESIS,
                operator_name=self.name,
            ),
            expected_information_gain=min(1.0, base_gain * p_success),
            expected_falsification_value=falsification_value,
            estimated_token_cost=self.PER_STEP_TOKENS,
        )]

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        target_hid = next(iter(state.views.hypotheses.keys()), None)
        if target_hid is None:
            return OperatorResult(
                operator_name=self.name, action_id=action.action_id,
                outcome=OperatorOutcome.NO_OP,
                resource_cost=ResourceCost(input_tokens=50, output_tokens=50),
            )

        art = state.artifacts.get(target_hid)
        world_hid = art.get("world_hypothesis_id", target_hid) if isinstance(art, dict) else target_hid
        result = self._sim.attack_hypothesis(world_hid)
        artifacts: dict[str, Any] = {}
        for ign in result.get("ignorance_items", []):
            iid = generate_id("ignorance")
            artifacts[iid] = {
                "type": "ignorance_item",
                "ignorance_id": iid,
                "ignorance_type": ign.get("ignorance_type", "untested_assumption"),
                "description": ign["description"],
                "priority": ign["priority"],
                "status": "open",
                "related_hypothesis_ids": [target_hid],
            }

        if result.get("found_something", False):
            self._attacks_without_result = 0
        else:
            self._attacks_without_result += 1

        half = self.PER_STEP_TOKENS // 2
        outcome = OperatorOutcome.SUCCESS if artifacts else OperatorOutcome.NO_OP
        return OperatorResult(
            operator_name=self.name, action_id=action.action_id,
            outcome=outcome,
            artifacts_produced=artifacts,
            resource_cost=ResourceCost(input_tokens=half, output_tokens=half),
        )


class SimReasonOperator:
    """Reasons about hypotheses and evidence using the simulator."""

    PER_STEP_TOKENS = 500

    def __init__(self, sim: EpistemicWorldSimulator) -> None:
        self._sim = sim

    @property
    def name(self) -> str:
        return "reason"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        if state.budget.is_exhausted or state.process.status != "active":
            return []
        if not state.evidence_ids or not state.views.hypotheses:
            return []

        p_success = state.views.self_model.operator_success_rates.get(
            self.name, state.views.self_model.overall_success_rate
        )
        base_gain = 0.3
        if state.views.contradiction_density > 0:
            base_gain += 0.2

        return [EpistemicActionBid(
            action=EpistemicAction(
                action_id=generate_id("action"),
                action_type=ActionType.REASON,
                operator_name=self.name,
            ),
            expected_information_gain=min(1.0, base_gain * p_success),
            estimated_token_cost=self.PER_STEP_TOKENS,
        )]

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        world_hids = []
        hid_map: dict[str, str] = {}
        for hid in state.views.hypotheses:
            art = state.artifacts.get(hid)
            world_hid = art.get("world_hypothesis_id", hid) if isinstance(art, dict) else hid
            world_hids.append(world_hid)
            hid_map[world_hid] = hid

        world_eids = []
        for eid in state.evidence_ids:
            art = state.artifacts.get(eid)
            world_eid = art.get("world_evidence_id", eid) if isinstance(art, dict) else eid
            world_eids.append(world_eid)

        result = self._sim.reason(world_hids, world_eids)

        aid = generate_id("analysis")
        artifacts: dict[str, Any] = {aid: {
            "type": "analysis",
            "consistency_scores": result["consistency_scores"],
            "evidence_analyzed": result["evidence_analyzed"],
            "contradictions_found": result["contradictions_found"],
        }}

        for world_hid, score in result["consistency_scores"].items():
            prefixed_hid = hid_map.get(world_hid, world_hid)
            if prefixed_hid in state.views.hypotheses:
                artifacts[prefixed_hid] = {
                    "statement": state.views.hypotheses[prefixed_hid].statement,
                    "prior": state.views.hypotheses[prefixed_hid].prior,
                    "posterior": score,
                    "status": state.views.hypotheses[prefixed_hid].status,
                    "world_hypothesis_id": world_hid,
                }

        half = self.PER_STEP_TOKENS // 2
        return OperatorResult(
            operator_name=self.name, action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS,
            artifacts_produced=artifacts,
            workspace_additions=[aid],
            resource_cost=ResourceCost(input_tokens=half, output_tokens=half),
        )


# ---------------------------------------------------------------
# Semantic Benchmark Runner
# ---------------------------------------------------------------

@dataclass
class SemanticRunResult:
    """Result of running a semantic scenario."""
    world_id: str
    architecture: str
    ablation_config: dict[str, bool]
    budget_tokens: int
    quality: EpistemicQualityVector
    scalar_quality: float
    steps_used: int
    tokens_used: int
    hypothesis_count: int
    ignorance_count: int
    evidence_count: int
    operator_sequence: list[str] = field(default_factory=list)
    oracle_values: dict[str, float] = field(default_factory=dict)
    manifest_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = {
            "world_id": self.world_id,
            "architecture": self.architecture,
            "ablation_config": self.ablation_config,
            "budget_tokens": self.budget_tokens,
            "scalar_quality": self.scalar_quality,
            "steps_used": self.steps_used,
            "tokens_used": self.tokens_used,
            "hypothesis_count": self.hypothesis_count,
            "ignorance_count": self.ignorance_count,
            "evidence_count": self.evidence_count,
            "operator_sequence": self.operator_sequence,
            "manifest_id": self.manifest_id,
        }
        d.update({f"q_{k}": v for k, v in self.quality.to_dict().items()})
        return d


class SemanticBenchmarkRunner:
    """
    Runs semantic scenarios with true causal ablation.

    Ablation flags control:
    - hypothesis_ecology: whether SimHypothesisOperator is registered
    - ignorance_ledger: whether SimAttackOperator is registered
    - self_model: whether operators see empirical reliability or neutral prior
    - stopping_policy: whether StoppingPolicy is active or trivial
    - epistemic_market: whether bid-based selection or round-robin is used
    """

    def __init__(self, *, default_budget: BudgetState | None = None) -> None:
        self._default_budget = default_budget or BudgetState(max_tokens=5000, max_steps=25)

    async def run(
        self,
        world: LatentWorld,
        *,
        architecture: str = "full_ree",
        ablation: dict[str, bool] | None = None,
        budget: BudgetState | None = None,
        self_model: SelfModelSummary | None = None,
    ) -> SemanticRunResult:
        effective_budget = budget or self._default_budget
        abl = ablation or {}

        sim = EpistemicWorldSimulator(world)

        if architecture == "B0_direct":
            return self._run_direct(world, sim, effective_budget, abl)

        if architecture == "B1_reflection":
            return self._run_reflection(world, sim, effective_budget, abl)

        if architecture in ("full_ree", "B4_diversity_ree"):
            pass  # proceed to REE controller
        elif architecture.startswith("B"):
            pass  # unknown baseline, run as REE

        reg = self._build_registry(sim, abl)
        store = AppendOnlyEventStore()
        traj = TrajectoryDataset()

        sm = self._resolve_self_model(self_model, abl)

        stopping = StoppingPolicy() if abl.get("stopping_policy", True) else None

        if not abl.get("epistemic_market", True):
            market = RoundRobinMarket()
        elif architecture == "B4_diversity_ree":
            market = DiversityAwareMarket()
        else:
            market = EpistemicMarket()

        ctrl = EpistemicController(
            registry=reg,
            event_store=store,
            budget=effective_budget,
            trajectory=traj,
            self_model_summary=sm,
            stopping_policy=stopping,
            market=market,
        )

        final_state = await ctrl.run(world.world_id, budget=effective_budget)

        quality = self._evaluate(sim, final_state)

        op_seq = []
        for event in store.get_all():
            op_seq.append(event.action.operator_name)

        return SemanticRunResult(
            world_id=world.world_id,
            architecture=architecture,
            ablation_config=abl,
            budget_tokens=effective_budget.max_tokens,
            quality=quality,
            scalar_quality=quality.scalar_quality(),
            steps_used=final_state.process.step_count,
            tokens_used=final_state.budget.tokens_used,
            hypothesis_count=len(final_state.views.hypotheses),
            ignorance_count=len(final_state.views.ignorance_items),
            evidence_count=len(final_state.evidence_ids),
            operator_sequence=op_seq,
            manifest_id=generate_id("manifest"),
        )

    def _build_registry(
        self,
        sim: EpistemicWorldSimulator,
        ablation: dict[str, bool],
    ) -> OperatorRegistry:
        reg = OperatorRegistry()
        reg.register(SimRetrieveOperator(sim))

        if ablation.get("hypothesis_ecology", True):
            reg.register(SimHypothesisOperator(sim))

        if ablation.get("ignorance_ledger", True):
            reg.register(SimAttackOperator(sim))

        reg.register(SimReasonOperator(sim))
        reg.register(StopOperator())
        return reg

    def _resolve_self_model(
        self,
        provided: SelfModelSummary | None,
        ablation: dict[str, bool],
    ) -> SelfModelSummary | None:
        if not ablation.get("self_model", True):
            return SelfModelSummary(
                overall_success_rate=1.0,
                operator_success_rates={},
            )
        return provided

    def _evaluate(
        self,
        sim: EpistemicWorldSimulator,
        state: EpistemicState,
    ) -> EpistemicQualityVector:
        final_hypotheses: dict[str, float] = {}
        for hid, hv in state.views.hypotheses.items():
            art = state.artifacts.get(hid)
            world_hid = art.get("world_hypothesis_id", hid) if isinstance(art, dict) else hid
            final_hypotheses[world_hid] = hv.posterior

        identified_hidden = set()
        for iid, iv in state.views.ignorance_items.items():
            desc = iv.description.lower() if hasattr(iv, 'description') else ""
            for hv_id in sim.world.hidden_variables:
                if hv_id.lower() in desc:
                    identified_hidden.add(hv_id)

        evidence_sources: dict[str, str | None] = {}
        for eid in state.evidence_ids:
            art = state.artifacts.get(eid)
            if isinstance(art, dict):
                evidence_sources[art.get("source_id", eid)] = art.get("parent_source")

        identified_assumptions = set()

        return sim.evaluate(
            final_hypotheses, identified_hidden,
            identified_assumptions, evidence_sources,
        )

    def _run_direct(
        self,
        world: LatentWorld,
        sim: EpistemicWorldSimulator,
        budget: BudgetState,
        ablation: dict[str, bool],
    ) -> SemanticRunResult:
        """B0: Single retrieve, pick best hypothesis from evidence."""
        ev = sim.retrieve("")
        hyp = sim.generate_hypothesis([ev["evidence_id"]] if ev else [])

        final_hyps: dict[str, float] = {}
        if hyp:
            final_hyps[hyp["hypothesis_id"]] = hyp["initial_plausibility"]

        quality = sim.evaluate(final_hyps, set(), set(), {})

        return SemanticRunResult(
            world_id=world.world_id,
            architecture="B0_direct",
            ablation_config=ablation,
            budget_tokens=budget.max_tokens,
            quality=quality,
            scalar_quality=quality.scalar_quality(),
            steps_used=2,
            tokens_used=1000,
            hypothesis_count=len(final_hyps),
            ignorance_count=0,
            evidence_count=1 if ev else 0,
            operator_sequence=["retrieve", "generate_hypothesis"],
        )

    def _run_reflection(
        self,
        world: LatentWorld,
        sim: EpistemicWorldSimulator,
        budget: BudgetState,
        ablation: dict[str, bool],
    ) -> SemanticRunResult:
        """B1: Retrieve, generate hypothesis, reason, generate another."""
        ev1 = sim.retrieve("")
        ev_ids = [ev1["evidence_id"]] if ev1 else []

        hyp1 = sim.generate_hypothesis(ev_ids)
        ev2 = sim.retrieve("")
        if ev2:
            ev_ids.append(ev2["evidence_id"])

        hyp2 = sim.generate_hypothesis(ev_ids)

        final_hyps: dict[str, float] = {}
        if hyp1:
            final_hyps[hyp1["hypothesis_id"]] = hyp1["initial_plausibility"]
        if hyp2:
            final_hyps[hyp2["hypothesis_id"]] = hyp2["initial_plausibility"]

        if final_hyps:
            reasoning = sim.reason(list(final_hyps.keys()), ev_ids)
            for hid, score in reasoning["consistency_scores"].items():
                if hid in final_hyps:
                    final_hyps[hid] = score

        evidence_sources: dict[str, str | None] = {}
        for eid in ev_ids:
            for e in world.evidence_pool:
                if e.evidence_id == eid:
                    evidence_sources[e.source.source_id] = e.source.parent_source

        quality = sim.evaluate(final_hyps, set(), set(), evidence_sources)

        return SemanticRunResult(
            world_id=world.world_id,
            architecture="B1_reflection",
            ablation_config=ablation,
            budget_tokens=budget.max_tokens,
            quality=quality,
            scalar_quality=quality.scalar_quality(),
            steps_used=4,
            tokens_used=2000,
            hypothesis_count=len(final_hyps),
            ignorance_count=0,
            evidence_count=len(ev_ids),
            operator_sequence=["retrieve", "generate_hypothesis", "retrieve", "generate_hypothesis", "reason"],
        )
