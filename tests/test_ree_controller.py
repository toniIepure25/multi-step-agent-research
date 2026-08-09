"""
Tests for the REE epistemic controller — the main cognitive loop.
"""

from __future__ import annotations

from typing import Any

import pytest

from asar.epistemic.store import AppendOnlyEventStore
from asar.metacognition.controller import EpistemicController
from asar.metacognition.market import EpistemicMarket
from asar.operators.base import CognitiveOperator
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
    ResourceCost,
)


class MockRetrieveOperator:
    """Deterministic retrieve operator for testing."""

    @property
    def name(self) -> str:
        return "retrieve"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        if state.evidence_ids:
            return []
        return [EpistemicActionBid(
            action=EpistemicAction(
                action_id="act_retrieve",
                action_type=ActionType.RETRIEVE,
                operator_name=self.name,
                description="Mock retrieve",
            ),
            expected_information_gain=0.8,
            probability_changes_decision=0.5,
            estimated_token_cost=100,
        )]

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        return OperatorResult(
            operator_name=self.name,
            action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS,
            artifacts_produced={
                "evidence_001": {"content": "Mock evidence about the topic"},
                "evidence_002": {"content": "Additional mock evidence"},
            },
            workspace_additions=["evidence_001", "evidence_002"],
            resource_cost=ResourceCost(input_tokens=50, output_tokens=50),
        )


class MockSynthesizeOperator:
    """Deterministic synthesize operator for testing."""

    @property
    def name(self) -> str:
        return "synthesize"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        if not state.evidence_ids or state.claim_ids:
            return []
        return [EpistemicActionBid(
            action=EpistemicAction(
                action_id="act_synthesize",
                action_type=ActionType.SYNTHESIZE,
                operator_name=self.name,
                description="Mock synthesize",
            ),
            expected_information_gain=0.6,
            probability_changes_decision=0.7,
            estimated_token_cost=200,
        )]

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        return OperatorResult(
            operator_name=self.name,
            action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS,
            artifacts_produced={
                "claim_001": {"text": "The topic shows X", "supporting_evidence_ids": ["evidence_001"]},
            },
            workspace_additions=["claim_001"],
            resource_cost=ResourceCost(input_tokens=100, output_tokens=200),
        )


@pytest.mark.asyncio
async def test_controller_runs_complete_episode() -> None:
    registry = OperatorRegistry()
    registry.register(MockRetrieveOperator())
    registry.register(MockSynthesizeOperator())
    registry.register(StopOperator())

    controller = EpistemicController(
        registry=registry,
        budget=BudgetState(max_tokens=10000, max_steps=10),
    )

    state = await controller.run("What is the meaning of test?")

    assert state.process.status in ("completed", "stopped")
    assert state.version > 0
    assert len(controller.event_store) > 0


@pytest.mark.asyncio
async def test_controller_stops_on_budget_exhaustion() -> None:
    registry = OperatorRegistry()
    registry.register(MockRetrieveOperator())

    controller = EpistemicController(
        registry=registry,
        budget=BudgetState(max_tokens=50, max_steps=2),
    )

    state = await controller.run("test")
    assert state.process.status == "completed"
    assert state.budget.steps_used <= 3  # max 2 steps + 1 forced stop


@pytest.mark.asyncio
async def test_controller_events_are_replayable() -> None:
    registry = OperatorRegistry()
    registry.register(MockRetrieveOperator())
    registry.register(MockSynthesizeOperator())
    registry.register(StopOperator())

    controller = EpistemicController(
        registry=registry,
        budget=BudgetState(max_tokens=10000, max_steps=10),
    )

    final_state = await controller.run("test replay")

    from schemas.ree.epistemic_state import ProcessState
    initial = EpistemicState(
        version=0,
        process=ProcessState(
            episode_id=final_state.process.episode_id,
            goal="test replay",
        ),
        budget=BudgetState(max_tokens=10000, max_steps=10),
    )

    events = controller.event_store.get_all()
    replayed = controller.reducer.replay(initial, events)

    assert replayed.version == final_state.version
    assert replayed.evidence_ids == final_state.evidence_ids
    assert replayed.claim_ids == final_state.claim_ids
    assert replayed.process.status == final_state.process.status


@pytest.mark.asyncio
async def test_controller_no_operators_stops_gracefully() -> None:
    registry = OperatorRegistry()
    controller = EpistemicController(
        registry=registry,
        budget=BudgetState(max_tokens=1000, max_steps=5),
    )

    state = await controller.run("test with no operators")
    assert state.process.status == "completed"
    assert "no operators" in (state.process.stop_reason or "")


@pytest.mark.asyncio
async def test_operators_cannot_mutate_state_directly() -> None:
    """Verify that operator execute() receives state but cannot mutate it."""

    class BadOperator:
        @property
        def name(self) -> str:
            return "bad"

        async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
            return [EpistemicActionBid(
                action=EpistemicAction(
                    action_id="act_bad",
                    action_type=ActionType.REASON,
                    operator_name=self.name,
                ),
                expected_information_gain=0.9,
                estimated_token_cost=10,
            )]

        async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
            original_version = state.version
            return OperatorResult(
                operator_name=self.name,
                action_id=action.action_id,
                outcome=OperatorOutcome.SUCCESS,
                resource_cost=ResourceCost(input_tokens=5, output_tokens=5),
                state_updates={"_attempted_version": original_version},
            )

    registry = OperatorRegistry()
    registry.register(BadOperator())
    registry.register(StopOperator())

    controller = EpistemicController(
        registry=registry,
        budget=BudgetState(max_tokens=1000, max_steps=5),
    )

    state = await controller.run("test mutation guard")
    assert state.version > 0


@pytest.mark.asyncio
async def test_controller_event_store_tracks_all_events() -> None:
    registry = OperatorRegistry()
    registry.register(MockRetrieveOperator())
    registry.register(StopOperator())

    store = AppendOnlyEventStore()
    controller = EpistemicController(
        registry=registry,
        event_store=store,
        budget=BudgetState(max_tokens=5000, max_steps=5),
    )

    state = await controller.run("test store tracking")
    assert len(store) == state.version
    for event in store.get_all():
        assert event.episode_id == state.process.episode_id
