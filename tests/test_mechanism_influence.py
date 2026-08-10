"""
Mechanism influence tests — Phase 10A.8.

For every major mechanism: same initial state, same provider outputs,
same budget, mechanism ON vs OFF → expected difference in downstream
epistemic behavior. Mandatory before Phase 11.
"""

from __future__ import annotations

import asyncio

import pytest

from asar.common import generate_id
from asar.epistemic.reducer import StateReducer
from asar.epistemic.store import AppendOnlyEventStore
from asar.metacognition.controller import EpistemicController
from asar.metacognition.market import EpistemicMarket
from asar.metacognition.stopping import StoppingDecision, StoppingPolicy
from asar.metacognition.trajectory import TrajectoryDataset
from asar.operators.counterfactual import CounterfactualOperator
from asar.operators.registry import OperatorRegistry
from asar.operators.stop import AbstainOperator, StopOperator
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
    HypothesisView,
    IgnoranceView,
    MaterializedViews,
    ProcessState,
    ResourceCost,
    SelfModelSummary,
)

# ---------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------

def _base_state(*, self_model: SelfModelSummary | None = None, views_update: dict | None = None) -> EpistemicState:
    views = MaterializedViews()
    if self_model:
        views = views.model_copy(update={"self_model": self_model})
    if views_update:
        views = views.model_copy(update=views_update)
    return EpistemicState(
        version=0,
        process=ProcessState(episode_id="ep_test", goal="test goal"),
        budget=BudgetState(max_tokens=10_000, max_steps=20),
        views=views,
    )


class _FixedRetrieveOp:
    """Deterministic retrieve operator returning fixed evidence."""

    @property
    def name(self) -> str:
        return "retrieve"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        if state.evidence_ids:
            return []
        p_success = state.views.self_model.operator_success_rates.get(
            self.name, state.views.self_model.overall_success_rate
        )
        return [EpistemicActionBid(
            action=EpistemicAction(
                action_id="a_r", action_type=ActionType.RETRIEVE, operator_name=self.name,
            ),
            expected_information_gain=0.6 * p_success,
            estimated_token_cost=50,
            failure_risk=max(0.0, 1.0 - p_success),
        )]

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        return OperatorResult(
            operator_name=self.name, action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS,
            artifacts_produced={
                "evidence_001": {"content": "Test evidence A"},
                "evidence_002": {"content": "Test evidence B"},
            },
            workspace_additions=["evidence_001", "evidence_002"],
            resource_cost=ResourceCost(input_tokens=25, output_tokens=25),
        )


class _IgnoranceDrivenRetrieveOp:
    """Retrieve operator whose bid explicitly depends on ignorance priority."""

    @property
    def name(self) -> str:
        return "retrieve"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        base = 0.3
        for iv in state.views.ignorance_items.values():
            if iv.status == "open":
                base = max(base, 0.3 + iv.priority * 0.5)
        return [EpistemicActionBid(
            action=EpistemicAction(
                action_id="a_r_ign", action_type=ActionType.RETRIEVE, operator_name=self.name,
            ),
            expected_information_gain=min(1.0, base),
            estimated_token_cost=50,
        )]

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        return OperatorResult(
            operator_name=self.name, action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS,
            artifacts_produced={"evidence_ign": {"content": "Ignorance-targeted retrieval"}},
            workspace_additions=["evidence_ign"],
            resource_cost=ResourceCost(input_tokens=10, output_tokens=10),
        )


# ---------------------------------------------------------------
# TEST 1: Self-model changes operator ranking
# ---------------------------------------------------------------

class TestSelfModelInfluence:
    """Self-model with low P(success) for retrieve should reduce its bid value."""

    @pytest.mark.asyncio
    async def test_self_model_reduces_bid_for_unreliable_operator(self):
        high_reliability = SelfModelSummary(
            operator_success_rates={"retrieve": 0.95},
            overall_success_rate=0.8,
        )
        low_reliability = SelfModelSummary(
            operator_success_rates={"retrieve": 0.2},
            overall_success_rate=0.8,
        )

        state_high = _base_state(self_model=high_reliability)
        state_low = _base_state(self_model=low_reliability)

        op = _FixedRetrieveOp()
        bids_high = await op.propose(state_high)
        bids_low = await op.propose(state_low)

        assert len(bids_high) == 1
        assert len(bids_low) == 1
        assert bids_high[0].expected_information_gain > bids_low[0].expected_information_gain, (
            "Self-model with low reliability should produce lower bid"
        )

    @pytest.mark.asyncio
    async def test_self_model_increases_failure_risk(self):
        high = SelfModelSummary(operator_success_rates={"retrieve": 0.9})
        low = SelfModelSummary(operator_success_rates={"retrieve": 0.3})

        bids_h = await _FixedRetrieveOp().propose(_base_state(self_model=high))
        bids_l = await _FixedRetrieveOp().propose(_base_state(self_model=low))

        assert bids_l[0].failure_risk > bids_h[0].failure_risk


# ---------------------------------------------------------------
# TEST 2: Ignorance triggers/boosts retrieval bid
# ---------------------------------------------------------------

class TestIgnoranceInfluence:
    """High-priority ignorance items should increase retrieval bids."""

    @pytest.mark.asyncio
    async def test_ignorance_boosts_retrieve_bid(self):
        no_ignorance = _base_state()
        with_ignorance = _base_state(views_update={
            "ignorance_items": {
                "ign_001": IgnoranceView(
                    ignorance_id="ign_001",
                    ignorance_type="missing_evidence",
                    description="Critical missing data",
                    priority=0.9,
                    status="open",
                ),
            },
        })

        op = _IgnoranceDrivenRetrieveOp()
        bids_clean = await op.propose(no_ignorance)
        bids_ign = await op.propose(with_ignorance)

        assert bids_ign[0].expected_information_gain > bids_clean[0].expected_information_gain, (
            "High-priority ignorance should boost retrieval bid"
        )

    @pytest.mark.asyncio
    async def test_resolved_ignorance_does_not_boost(self):
        with_resolved = _base_state(views_update={
            "ignorance_items": {
                "ign_002": IgnoranceView(
                    ignorance_id="ign_002",
                    ignorance_type="missing_evidence",
                    description="Already resolved",
                    priority=0.9,
                    status="resolved",
                ),
            },
        })
        clean = _base_state()

        op = _IgnoranceDrivenRetrieveOp()
        bids_r = await op.propose(with_resolved)
        bids_c = await op.propose(clean)

        assert bids_r[0].expected_information_gain == bids_c[0].expected_information_gain


# ---------------------------------------------------------------
# TEST 3: Stopping policy reads materialized ignorance views
# ---------------------------------------------------------------

class TestStoppingPolicyViewIntegration:
    """StoppingPolicy should stop when ignorance impact is low (views), continue otherwise."""

    def test_stop_when_ignorance_impact_low(self):
        state = _base_state()
        state = state.model_copy(update={
            "evidence_ids": ["e1"],
            "claim_ids": ["c1"],
            "operator_history": ["retrieve", "synthesize"],
            "process": state.process.model_copy(update={"step_count": 5}),
        })
        policy = StoppingPolicy(ignorance_impact_threshold=0.3)
        result = policy.evaluate(state)
        assert result.decision == StoppingDecision.STOP

    def test_continue_when_high_ignorance(self):
        views = MaterializedViews(ignorance_items={
            "ign_hi": IgnoranceView(
                ignorance_id="ign_hi", ignorance_type="unknown",
                description="Critical unknown", priority=0.8,
                status="open", impact_if_resolved=0.9,
            ),
        })
        state = _base_state(views_update={"ignorance_items": views.ignorance_items})
        state = state.model_copy(update={
            "evidence_ids": ["e1"],
            "claim_ids": ["c1"],
            "ignorance_ids": ["ign_hi"],
            "operator_history": ["retrieve", "synthesize"],
            "process": state.process.model_copy(update={"step_count": 5}),
        })
        policy = StoppingPolicy(ignorance_impact_threshold=0.3)
        result = policy.evaluate(state)
        assert result.decision == StoppingDecision.CONTINUE


# ---------------------------------------------------------------
# TEST 4: High ignorance suppresses stop bid
# ---------------------------------------------------------------

class TestStopOperatorIgnoranceSuppression:
    """Stop operator value should decrease when ignorance is high."""

    @pytest.mark.asyncio
    async def test_stop_bid_lower_with_high_ignorance(self):
        from asar.operators.stop import StopOperator

        base = _base_state()
        base = base.model_copy(update={
            "claim_ids": ["c1"],
            "operator_history": ["retrieve", "synthesize"],
            "process": base.process.model_copy(update={"step_count": 5}),
        })
        base_views = base.views.compute_derived(base.workspace, 0, 1)
        base = base.model_copy(update={"views": base_views})

        with_ign_views = MaterializedViews(ignorance_items={
            "ign_x": IgnoranceView(
                ignorance_id="ign_x", ignorance_type="unknown",
                description="Big unknown", priority=0.9, status="open",
                impact_if_resolved=0.8,
            ),
        }).compute_derived(base.workspace, 0, 1)
        with_ign = base.model_copy(update={"views": with_ign_views})

        op = StopOperator()
        bids_clean = await op.propose(base)
        bids_ign = await op.propose(with_ign)

        assert len(bids_clean) > 0 and len(bids_ign) > 0
        assert bids_ign[0].expected_information_gain < bids_clean[0].expected_information_gain, (
            "Stop bid value should be lower when ignorance is high"
        )


# ---------------------------------------------------------------
# TEST 5: Reducer projects hypotheses into views
# ---------------------------------------------------------------

class TestReducerHypothesisProjection:
    """Reducer must project hypothesis artifacts into HypothesisView."""

    def test_hypothesis_projected_to_views(self):
        state = _base_state()
        from schemas.ree.epistemic_event import EpistemicEvent
        event = EpistemicEvent(
            event_id="ev1", episode_id="ep_test",
            version_before=0, version_after=1,
            action=EpistemicAction(action_id="a1", action_type=ActionType.GENERATE_HYPOTHESIS, operator_name="gen"),
            result=OperatorResult(
                operator_name="gen", action_id="a1",
                outcome=OperatorOutcome.SUCCESS,
                artifacts_produced={
                    "hypothesis_h1": {
                        "statement": "Test hypothesis",
                        "prior": 0.6, "posterior": 0.6,
                        "status": "proposed", "ontology_frame": "causal",
                    },
                },
                workspace_additions=["hypothesis_h1"],
            ),
            resource_cost=ResourceCost(),
        )
        reducer = StateReducer()
        new_state = reducer.apply(state, event)

        assert "hypothesis_h1" in new_state.views.hypotheses
        hv = new_state.views.hypotheses["hypothesis_h1"]
        assert hv.statement == "Test hypothesis"
        assert hv.posterior == 0.6
        assert hv.ontology_frame == "causal"

    def test_replay_reconstructs_identical_views(self):
        """Replay must produce identical materialized views."""
        state = _base_state()
        from schemas.ree.epistemic_event import EpistemicEvent
        events = [
            EpistemicEvent(
                event_id=f"ev{i}", episode_id="ep_test",
                version_before=i, version_after=i + 1,
                action=EpistemicAction(action_id=f"a{i}", action_type=ActionType.RETRIEVE, operator_name="ret"),
                result=OperatorResult(
                    operator_name="ret", action_id=f"a{i}",
                    outcome=OperatorOutcome.SUCCESS,
                    artifacts_produced={
                        f"hypothesis_h{i}": {
                            "statement": f"H{i}",
                            "prior": 0.3 + i * 0.1,
                            "posterior": 0.3 + i * 0.1,
                            "status": "proposed",
                        },
                        f"ignorance_ig{i}": {
                            "ignorance_type": "unknown",
                            "description": f"Unknown {i}",
                            "impact_if_resolved": 0.7,
                            "resolvability": 0.5,
                            "probability_decision_relevant": 0.6,
                        },
                    },
                    workspace_additions=[f"hypothesis_h{i}"],
                ),
                resource_cost=ResourceCost(input_tokens=50, output_tokens=50),
            )
            for i in range(3)
        ]

        reducer = StateReducer()
        final = state
        for e in events:
            final = reducer.apply(final, e)

        replayed = reducer.replay(state, events)
        assert replayed.views.hypotheses == final.views.hypotheses
        assert replayed.views.ignorance_items == final.views.ignorance_items
        assert replayed.views.belief_trajectory == final.views.belief_trajectory
        assert replayed.views.hypothesis_entropy == final.views.hypothesis_entropy


# ---------------------------------------------------------------
# TEST 6: Trajectory records rich state features
# ---------------------------------------------------------------

class TestTrajectoryRichFeatures:
    """TrajectoryDataset must record MaterializedViews-derived features."""

    @pytest.mark.asyncio
    async def test_trajectory_captures_view_features(self):
        reg = OperatorRegistry()
        reg.register(_FixedRetrieveOp())
        reg.register(StopOperator())
        store = AppendOnlyEventStore()
        traj = TrajectoryDataset()

        ctrl = EpistemicController(
            registry=reg, event_store=store, trajectory=traj,
            budget=BudgetState(max_tokens=5000, max_steps=10),
        )
        await ctrl.run("trajectory feature test")

        assert len(traj) > 0
        step = traj.all_steps()[0]
        assert hasattr(step, "hypothesis_entropy")
        assert hasattr(step, "highest_ignorance_priority")
        assert hasattr(step, "workspace_saturation")
        assert hasattr(step, "self_model_expected_success")


# ---------------------------------------------------------------
# TEST 7: Counterfactual operator reads views
# ---------------------------------------------------------------

class TestCounterfactualViewDependency:
    """CounterfactualOperator should not propose when no hypotheses in views."""

    @pytest.mark.asyncio
    async def test_no_proposal_without_hypothesis_views(self):
        state = _base_state()
        state = state.model_copy(update={"assumption_ids": ["a1"]})
        op = CounterfactualOperator()
        bids = await op.propose(state)
        assert len(bids) == 0

    @pytest.mark.asyncio
    async def test_proposes_with_hypothesis_views(self):
        state = _base_state(views_update={
            "hypotheses": {
                "hypothesis_h1": HypothesisView(hypothesis_id="hypothesis_h1", statement="H1"),
            },
        })
        state = state.model_copy(update={
            "hypothesis_ids": ["hypothesis_h1"],
            "assumption_ids": ["a1"],
        })
        op = CounterfactualOperator()
        bids = await op.propose(state)
        assert len(bids) > 0


# ---------------------------------------------------------------
# TEST 8: Controller integrates StoppingPolicy (not inline check only)
# ---------------------------------------------------------------

class TestControllerStoppingPolicyIntegration:
    """StoppingPolicy must be called by controller and can halt early."""

    @pytest.mark.asyncio
    async def test_aggressive_stopping_policy_halts_early(self):
        aggressive_policy = StoppingPolicy(
            min_evidence=0, min_steps_before_stop=0,
            budget_exhaustion_threshold=1.0,
        )
        reg = OperatorRegistry()
        reg.register(_FixedRetrieveOp())
        reg.register(StopOperator())

        ctrl = EpistemicController(
            registry=reg,
            stopping_policy=aggressive_policy,
            budget=BudgetState(max_tokens=50000, max_steps=100),
        )
        final = await ctrl.run("test aggressive stop")
        assert final.process.step_count <= 3
