"""
Tests for the epistemic market (heuristic scheduler).
"""

from __future__ import annotations

import pytest

from asar.metacognition.market import EpistemicMarket, MarketWeights
from schemas.ree.epistemic_event import (
    ActionType,
    EpistemicAction,
    EpistemicActionBid,
)
from schemas.ree.epistemic_state import (
    BudgetState,
    EpistemicState,
    ProcessState,
)


def _make_state(tokens_used: int = 0, max_tokens: int = 10000) -> EpistemicState:
    return EpistemicState(
        version=0,
        process=ProcessState(episode_id="ep_001", goal="test"),
        budget=BudgetState(max_tokens=max_tokens, tokens_used=tokens_used),
    )


def _make_bid(
    operator: str = "test_op",
    action_type: ActionType = ActionType.RETRIEVE,
    info_gain: float = 0.5,
    decision_change: float = 0.3,
    token_cost: int = 500,
    failure_risk: float = 0.1,
) -> EpistemicActionBid:
    return EpistemicActionBid(
        action=EpistemicAction(
            action_id="action_001",
            action_type=action_type,
            operator_name=operator,
        ),
        expected_information_gain=info_gain,
        probability_changes_decision=decision_change,
        estimated_token_cost=token_cost,
        failure_risk=failure_risk,
    )


class TestEpistemicMarket:
    def test_select_returns_highest_score(self) -> None:
        market = EpistemicMarket()
        state = _make_state()
        bids = [
            _make_bid(operator="low", info_gain=0.1, decision_change=0.1),
            _make_bid(operator="high", info_gain=0.9, decision_change=0.8),
        ]
        decision = market.select(bids, state)
        assert decision is not None
        assert decision.selected_bid.action.operator_name == "high"

    def test_select_empty_bids_returns_none(self) -> None:
        market = EpistemicMarket()
        state = _make_state()
        assert market.select([], state) is None

    def test_high_token_cost_penalized(self) -> None:
        market = EpistemicMarket()
        state = _make_state(max_tokens=1000)
        cheap = _make_bid(operator="cheap", info_gain=0.5, token_cost=100)
        expensive = _make_bid(operator="expensive", info_gain=0.5, token_cost=900)

        cheap_score = market.evaluate_bid(cheap, state)
        expensive_score = market.evaluate_bid(expensive, state)
        assert cheap_score > expensive_score

    def test_low_budget_increases_cost_penalty(self) -> None:
        market = EpistemicMarket()
        bid = _make_bid(info_gain=0.5, token_cost=200)

        state_rich = _make_state(tokens_used=0, max_tokens=10000)
        state_poor = _make_state(tokens_used=9500, max_tokens=10000)

        score_rich = market.evaluate_bid(bid, state_rich)
        score_poor = market.evaluate_bid(bid, state_poor)
        assert score_rich > score_poor

    def test_competing_bids_tracked(self) -> None:
        market = EpistemicMarket()
        state = _make_state()
        bids = [
            _make_bid(operator="a", info_gain=0.3),
            _make_bid(operator="b", info_gain=0.8),
            _make_bid(operator="c", info_gain=0.5),
        ]
        decision = market.select(bids, state)
        assert len(decision.competing_bids) == 2

    def test_selection_score_is_deterministic(self) -> None:
        market = EpistemicMarket()
        state = _make_state()
        bids = [_make_bid(info_gain=0.7), _make_bid(info_gain=0.3)]

        d1 = market.select(bids, state)
        d2 = market.select(bids, state)
        assert d1.selection_score == d2.selection_score
