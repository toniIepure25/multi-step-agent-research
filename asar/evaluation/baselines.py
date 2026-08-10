"""
Baseline implementations — Phase 10B.6.

B0: Direct model (single call)
B1: Simple reflection (answer + critique + revision)
B2: Legacy ASAR v1-minimal (sequential orchestrator)
B3: Fixed-depth REE (predetermined operator sequence)
B4: REE heuristic metacognitive scheduler (full adaptive)

All baselines share a common CognitiveBudget for fair comparison.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from asar.common import generate_id
from asar.epistemic.reducer import StateReducer
from asar.epistemic.store import AppendOnlyEventStore
from asar.metacognition.controller import EpistemicController
from asar.metacognition.market import EpistemicMarket
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
    ProcessState,
    ResourceCost,
    SelfModelSummary,
)


@dataclass
class BaselineResult:
    """Result of running a baseline on a task."""
    baseline_name: str
    answer: str = ""
    claims: list[dict[str, Any]] = field(default_factory=list)
    tokens_used: int = 0
    steps_used: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)
    final_state: EpistemicState | None = None


# ---------------------------------------------------------------
# B0 — Direct Model (single LLM call)
# ---------------------------------------------------------------

class DirectModelBaseline:
    """B0: Single model call with no additional architecture."""

    name = "B0_direct_model"

    async def run(self, goal: str, *, budget: BudgetState) -> BaselineResult:
        episode_id = generate_id("episode")
        state = EpistemicState(
            version=0,
            process=ProcessState(episode_id=episode_id, goal=goal),
            budget=budget,
        )

        action = EpistemicAction(
            action_id=generate_id("action"),
            action_type=ActionType.SYNTHESIZE,
            operator_name="direct",
            description="Direct single-call answer",
        )
        result = OperatorResult(
            operator_name="direct",
            action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS,
            artifacts_produced={
                "claim_direct": {
                    "type": "claim",
                    "text": f"[Direct answer placeholder for: {goal}]",
                    "epistemic_status": "moderate_confidence",
                },
            },
            resource_cost=ResourceCost(
                input_tokens=min(500, budget.max_tokens // 2),
                output_tokens=min(500, budget.max_tokens // 2),
            ),
        )

        reducer = StateReducer()
        event = EpistemicEvent(
            event_id=generate_id("event"),
            episode_id=episode_id,
            version_before=0, version_after=1,
            action=action, result=result,
            resource_cost=result.resource_cost,
        )
        final = reducer.apply(state, event)

        return BaselineResult(
            baseline_name=self.name,
            answer=f"[Direct answer for: {goal}]",
            claims=[{"text": result.artifacts_produced["claim_direct"]["text"]}],
            tokens_used=result.resource_cost.total_tokens,
            steps_used=1,
            events=[event.model_dump()],
            final_state=final,
        )


# ---------------------------------------------------------------
# B1 — Simple Reflection (answer + critique + revision)
# ---------------------------------------------------------------

class SimpleReflectionBaseline:
    """B1: Answer → critique → revise. Fixed 3-step process."""

    name = "B1_simple_reflection"

    async def run(self, goal: str, *, budget: BudgetState) -> BaselineResult:
        episode_id = generate_id("episode")
        state = EpistemicState(
            version=0,
            process=ProcessState(episode_id=episode_id, goal=goal),
            budget=budget,
        )
        reducer = StateReducer()
        per_step_tokens = budget.max_tokens // 3

        steps = [
            ("synthesize", "initial_answer", f"[Initial answer for: {goal}]"),
            ("reason", "critique", "[Critique of initial answer]"),
            ("synthesize", "revised_answer", f"[Revised answer for: {goal}]"),
        ]
        events = []
        total_tokens = 0

        for i, (op_name, artifact_prefix, text) in enumerate(steps):
            action_type = ActionType.SYNTHESIZE if op_name == "synthesize" else ActionType.REASON
            action = EpistemicAction(
                action_id=generate_id("action"),
                action_type=action_type,
                operator_name=op_name,
            )
            cost = ResourceCost(
                input_tokens=min(per_step_tokens // 2, budget.max_tokens - total_tokens),
                output_tokens=min(per_step_tokens // 2, budget.max_tokens - total_tokens),
            )
            result = OperatorResult(
                operator_name=op_name,
                action_id=action.action_id,
                outcome=OperatorOutcome.SUCCESS,
                artifacts_produced={
                    f"claim_{artifact_prefix}": {
                        "type": "claim",
                        "text": text,
                        "epistemic_status": "moderate_confidence",
                    },
                },
                resource_cost=cost,
            )
            event = EpistemicEvent(
                event_id=generate_id("event"),
                episode_id=episode_id,
                version_before=state.version,
                version_after=state.version + 1,
                action=action, result=result,
                resource_cost=cost,
            )
            events.append(event)
            state = reducer.apply(state, event)
            total_tokens += cost.total_tokens

        return BaselineResult(
            baseline_name=self.name,
            answer=f"[Revised answer for: {goal}]",
            claims=[{"text": s[2]} for s in steps],
            tokens_used=total_tokens,
            steps_used=3,
            events=[e.model_dump() for e in events],
            final_state=state,
        )


# ---------------------------------------------------------------
# B3 — Fixed-Depth REE
# ---------------------------------------------------------------

class FixedDepthREEBaseline:
    """B3: Uses REE representations but follows predetermined operator sequence.

    Sequence: retrieve → reason → generate_hypothesis → synthesize → stop
    No adaptive scheduling.
    """

    name = "B3_fixed_depth_ree"

    def __init__(self, operators: OperatorRegistry | None = None) -> None:
        self._registry = operators

    async def run(
        self,
        goal: str,
        *,
        budget: BudgetState,
        registry: OperatorRegistry | None = None,
    ) -> BaselineResult:
        reg = registry or self._registry
        if reg is None:
            raise ValueError("OperatorRegistry required for B3 baseline")

        episode_id = generate_id("episode")
        state = EpistemicState(
            version=0,
            process=ProcessState(episode_id=episode_id, goal=goal),
            budget=budget,
        )
        reducer = StateReducer()
        store = AppendOnlyEventStore()

        sequence = ["retrieve", "reason", "generate_hypothesis", "synthesize"]

        for op_name in sequence:
            if state.budget.is_exhausted:
                break
            operator = reg.get(op_name)
            if operator is None:
                continue

            bids = await operator.propose(state)
            if not bids:
                continue

            action = bids[0].action
            try:
                result = await operator.execute(state, action)
            except Exception:
                continue

            event = EpistemicEvent(
                event_id=generate_id("event"),
                episode_id=episode_id,
                version_before=state.version,
                version_after=state.version + 1,
                action=action, result=result,
                resource_cost=result.resource_cost,
            )
            store.append(event)
            state = reducer.apply(state, event)

        stop_action = EpistemicAction(
            action_id=generate_id("action"),
            action_type=ActionType.STOP,
            operator_name="stop",
        )
        stop_result = OperatorResult(
            operator_name="stop",
            action_id=stop_action.action_id,
            outcome=OperatorOutcome.SUCCESS,
            notes="Fixed sequence complete",
        )
        stop_event = EpistemicEvent(
            event_id=generate_id("event"),
            episode_id=episode_id,
            version_before=state.version,
            version_after=state.version + 1,
            action=stop_action, result=stop_result,
            resource_cost=ResourceCost(),
        )
        store.append(stop_event)
        state = reducer.apply(state, stop_event)

        return BaselineResult(
            baseline_name=self.name,
            tokens_used=state.budget.tokens_used,
            steps_used=state.process.step_count,
            events=[e.model_dump() for e in store.get_all()],
            final_state=state,
        )


# ---------------------------------------------------------------
# B4 — REE Heuristic Metacognitive Scheduler (full adaptive)
# ---------------------------------------------------------------

class REEAdaptiveBaseline:
    """B4: Full adaptive REE with heuristic metacognitive scheduler.

    Wraps EpistemicController with default market weights.
    """

    name = "B4_ree_adaptive"

    def __init__(
        self,
        registry: OperatorRegistry | None = None,
        *,
        self_model_summary: SelfModelSummary | None = None,
    ) -> None:
        self._registry = registry
        self._self_model = self_model_summary

    async def run(
        self,
        goal: str,
        *,
        budget: BudgetState,
        registry: OperatorRegistry | None = None,
        trajectory: TrajectoryDataset | None = None,
    ) -> BaselineResult:
        reg = registry or self._registry
        if reg is None:
            raise ValueError("OperatorRegistry required for B4 baseline")

        store = AppendOnlyEventStore()
        ctrl = EpistemicController(
            registry=reg,
            event_store=store,
            budget=budget,
            trajectory=trajectory,
            self_model_summary=self._self_model,
        )

        state = await ctrl.run(goal, budget=budget)

        return BaselineResult(
            baseline_name=self.name,
            tokens_used=state.budget.tokens_used,
            steps_used=state.process.step_count,
            events=[e.model_dump() for e in store.get_all()],
            final_state=state,
        )
