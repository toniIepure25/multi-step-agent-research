"""
Epistemic Controller — the main REE loop.

Implements: state -> propose bids -> select -> execute -> reduce -> repeat

Integrates:
  - StoppingPolicy for first-class stop/continue/abstain decisions
  - TrajectoryDataset for step-level data collection
  - MaterializedViews for rich state propagation
"""

from __future__ import annotations

from asar.common import generate_id
from asar.epistemic.reducer import StateReducer
from asar.epistemic.store import AppendOnlyEventStore
from asar.metacognition.market import EpistemicMarket
from asar.metacognition.stopping import StoppingDecision, StoppingPolicy
from asar.metacognition.trajectory import TrajectoryDataset, TrajectoryStep
from asar.operators.registry import OperatorRegistry
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


class EpistemicController:
    """
    The main REE cognitive loop.

    Repeatedly: gather bids from all operators, select the best action
    via the epistemic market, execute it, record the event,
    apply the result through the reducer, evaluate stopping policy,
    and record trajectory data.
    """

    def __init__(
        self,
        *,
        registry: OperatorRegistry,
        market: EpistemicMarket | None = None,
        reducer: StateReducer | None = None,
        event_store: AppendOnlyEventStore | None = None,
        budget: BudgetState | None = None,
        stopping_policy: StoppingPolicy | None = None,
        trajectory: TrajectoryDataset | None = None,
        self_model_summary: SelfModelSummary | None = None,
    ) -> None:
        self._registry = registry
        self._market = market if market is not None else EpistemicMarket()
        self._reducer = reducer if reducer is not None else StateReducer()
        self._store = event_store if event_store is not None else AppendOnlyEventStore()
        self._default_budget = budget if budget is not None else BudgetState()
        self._stopping = stopping_policy if stopping_policy is not None else StoppingPolicy()
        self._trajectory = trajectory
        self._self_model_summary = self_model_summary

    async def run(
        self,
        goal: str,
        *,
        budget: BudgetState | None = None,
        max_steps: int | None = None,
    ) -> EpistemicState:
        """Run a complete REE research episode."""
        episode_id = generate_id("episode")
        effective_budget = budget or self._default_budget
        if max_steps is not None:
            effective_budget = effective_budget.model_copy(update={"max_steps": max_steps})

        initial_views = MaterializedViews()
        if self._self_model_summary is not None:
            initial_views = initial_views.model_copy(update={"self_model": self._self_model_summary})

        state = EpistemicState(
            version=0,
            process=ProcessState(episode_id=episode_id, goal=goal),
            budget=effective_budget,
            views=initial_views,
        )

        while state.process.status == "active" and not state.budget.is_exhausted:
            state = await self._step(state)

        if state.process.status == "active" and state.budget.is_exhausted:
            stop_event = self._make_stop_event(state, "budget exhausted")
            self._store.append(stop_event)
            state = self._reducer.apply(state, stop_event)

        return state

    async def _step(self, state: EpistemicState) -> EpistemicState:
        """Execute one step of the epistemic loop."""
        all_bids: list[EpistemicActionBid] = []
        for operator in self._registry.all():
            try:
                bids = await operator.propose(state)
                all_bids.extend(bids)
            except Exception:
                continue

        if not all_bids:
            stop_event = self._make_stop_event(state, "no operators proposed actions")
            self._store.append(stop_event)
            return self._reducer.apply(state, stop_event)

        decision = self._market.select(all_bids, state)
        if decision is None:
            stop_event = self._make_stop_event(state, "market could not select action")
            self._store.append(stop_event)
            return self._reducer.apply(state, stop_event)

        selected_action = decision.selected_bid.action
        operator = self._registry.get(selected_action.operator_name)
        if operator is None:
            stop_event = self._make_stop_event(state, f"operator {selected_action.operator_name} not found")
            self._store.append(stop_event)
            return self._reducer.apply(state, stop_event)

        try:
            result = await operator.execute(state, selected_action)
        except Exception as exc:
            result = OperatorResult(
                operator_name=selected_action.operator_name,
                action_id=selected_action.action_id,
                outcome=OperatorOutcome.FAILURE,
                error_message=str(exc),
                resource_cost=ResourceCost(latency_ms=100),
            )

        event = EpistemicEvent(
            event_id=generate_id("event"),
            episode_id=state.process.episode_id,
            version_before=state.version,
            version_after=state.version + 1,
            action=selected_action,
            decision=decision,
            result=result,
            resource_cost=result.resource_cost,
            rationale=decision.selection_rationale,
        )
        self._store.append(event)
        new_state = self._reducer.apply(state, event)

        self._record_trajectory(state, new_state, selected_action, decision, result)

        if new_state.process.status == "active":
            stop_reason = self._stopping.evaluate(new_state)
            if stop_reason.decision != StoppingDecision.CONTINUE:
                status_map = {
                    StoppingDecision.STOP: "completed",
                    StoppingDecision.ABSTAIN: "abstained",
                    StoppingDecision.RETURN_PARTIAL: "completed",
                }
                stop_event = self._make_stop_event(
                    new_state,
                    f"stopping_policy: {stop_reason.reason}",
                )
                self._store.append(stop_event)
                new_state = self._reducer.apply(new_state, stop_event)

        return new_state

    def _record_trajectory(
        self,
        state_before: EpistemicState,
        state_after: EpistemicState,
        action: EpistemicAction,
        decision: "EpistemicDecision",
        result: OperatorResult,
    ) -> None:
        """Record a trajectory step with rich state features."""
        if self._trajectory is None:
            return

        step = TrajectoryStep(
            episode_id=state_before.process.episode_id,
            step=state_before.process.step_count,
            state_version=state_before.version,
            action_type=action.action_type.value,
            operator_name=action.operator_name,
            bid_score=decision.selection_score,
            outcome=result.outcome.value,
            evidence_count_before=len(state_before.evidence_ids),
            hypothesis_count_before=len(state_before.hypothesis_ids),
            claim_count_before=len(state_before.claim_ids),
            budget_fraction_before=state_before.budget.budget_fraction_remaining,
            tokens_consumed=result.resource_cost.total_tokens,
            hypothesis_entropy=state_before.views.hypothesis_entropy,
            top_hypothesis_margin=state_before.views.top_hypothesis_margin,
            contradiction_density=state_before.views.contradiction_density,
            highest_ignorance_priority=state_before.views.highest_ignorance_priority,
            mean_ignorance_priority=state_before.views.mean_ignorance_priority,
            workspace_saturation=state_before.views.workspace_saturation,
            ignorance_count_before=len(state_before.ignorance_ids),
            assumption_count_before=len(state_before.assumption_ids),
            self_model_expected_success=state_before.views.self_model.operator_success_rates.get(
                action.operator_name, state_before.views.self_model.overall_success_rate
            ),
            event_id=state_after.version,
        )
        self._trajectory.record(step)

    def _make_stop_event(self, state: EpistemicState, reason: str) -> EpistemicEvent:
        """Create a synthetic stop event."""
        action = EpistemicAction(
            action_id=generate_id("action"),
            action_type=ActionType.STOP,
            operator_name="stop",
            parameters={"reason": reason},
            description=f"Stop: {reason}",
        )
        result = OperatorResult(
            operator_name="stop",
            action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS,
            resource_cost=ResourceCost(),
            notes=reason,
        )
        return EpistemicEvent(
            event_id=generate_id("event"),
            episode_id=state.process.episode_id,
            version_before=state.version,
            version_after=state.version + 1,
            action=action,
            result=result,
            resource_cost=ResourceCost(),
            rationale=reason,
        )

    @property
    def event_store(self) -> AppendOnlyEventStore:
        return self._store

    @property
    def reducer(self) -> StateReducer:
        return self._reducer
