"""
Epistemic Controller — the main REE loop.

Implements: state -> propose bids -> select -> execute -> reduce -> repeat

This is the REE equivalent of the legacy SequentialOrchestrator.
"""

from __future__ import annotations

from asar.common import generate_id
from asar.epistemic.reducer import StateReducer
from asar.epistemic.store import AppendOnlyEventStore
from asar.metacognition.market import EpistemicMarket
from asar.operators.base import CognitiveOperator
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
    ProcessState,
    ResourceCost,
)


class EpistemicController:
    """
    The main REE cognitive loop.

    Repeatedly: gather bids from all operators, select the best action
    via the epistemic market, execute it, record the event, and
    apply the result through the reducer.
    """

    def __init__(
        self,
        *,
        registry: OperatorRegistry,
        market: EpistemicMarket | None = None,
        reducer: StateReducer | None = None,
        event_store: AppendOnlyEventStore | None = None,
        budget: BudgetState | None = None,
    ) -> None:
        self._registry = registry
        self._market = market if market is not None else EpistemicMarket()
        self._reducer = reducer if reducer is not None else StateReducer()
        self._store = event_store if event_store is not None else AppendOnlyEventStore()
        self._default_budget = budget if budget is not None else BudgetState()

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

        state = EpistemicState(
            version=0,
            process=ProcessState(episode_id=episode_id, goal=goal),
            budget=effective_budget,
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
        return self._reducer.apply(state, event)

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
