"""
Metamorphic cognitive tests for REE.

These test invariance, resistance, and responsiveness properties
that any well-functioning epistemic system should satisfy.
"""

from __future__ import annotations

import pytest

from asar.epistemic.workspace import SalienceScorer, SalienceSignals, WorkspaceManager
from asar.metacognition.market import EpistemicMarket
from asar.social.trust import EvidenceIndependenceAnalyzer
from asar.ontology.counterfactual import CounterfactualLab
from schemas.ree.epistemic_event import (
    ActionType,
    EpistemicAction,
    EpistemicActionBid,
)
from schemas.ree.epistemic_state import (
    BudgetState,
    EpistemicState,
    ProcessState,
    WorkspaceSlot,
    WorkspaceState,
)
from schemas.ree.ontology import SensitivityResult
from schemas.ree.social import EvidenceProvenance


class TestDuplicateCitationResistance:
    """Duplicate evidence from the same source must not inflate importance."""

    def test_independence_score_decreases_with_duplication(self) -> None:
        analyzer = EvidenceIndependenceAnalyzer()
        analyzer.register_provenance(EvidenceProvenance(
            evidence_id="e1", original_source_id="src_a",
        ))
        score_single = analyzer.evidence_independence_score(["e1"])

        for i in range(2, 6):
            analyzer.register_provenance(EvidenceProvenance(
                evidence_id=f"e{i}", original_source_id="src_a", is_derivative=True,
            ))

        ids = [f"e{i}" for i in range(1, 6)]
        score_many = analyzer.evidence_independence_score(ids)
        assert score_many < score_single

    def test_workspace_redundancy_penalty(self) -> None:
        scorer = SalienceScorer()
        base = SalienceSignals(relevance=0.8, novelty=0.5)
        duplicate = SalienceSignals(relevance=0.8, novelty=0.5, redundancy_penalty=0.8)
        assert scorer.score(base) > scorer.score(duplicate)


class TestIrrelevantSourceResistance:
    """Irrelevant material should not enter or dominate the workspace."""

    def test_irrelevant_cannot_evict_relevant(self) -> None:
        mgr = WorkspaceManager()
        ws = WorkspaceState(
            capacity=2,
            slots=[
                WorkspaceSlot(artifact_id="relevant_1", artifact_type="evidence",
                             salience=0.7, added_at_version=1),
                WorkspaceSlot(artifact_id="relevant_2", artifact_type="evidence",
                             salience=0.6, added_at_version=1),
            ],
        )
        ws2 = mgr.add_artifact(
            ws, "irrelevant", "noise",
            SalienceSignals(relevance=0.0, novelty=0.0),
            version=2,
        )
        ids = {s.artifact_id for s in ws2.slots}
        assert "irrelevant" not in ids


class TestContradictionEscalation:
    """Contradictions should receive elevated workspace salience."""

    def test_contradiction_signal_increases_score(self) -> None:
        scorer = SalienceScorer()
        normal = SalienceSignals(relevance=0.5)
        contradictory = SalienceSignals(relevance=0.5, contradiction=0.9)
        assert scorer.score(contradictory) > scorer.score(normal)


class TestBudgetSensitiveScheduling:
    """The market should become more cost-sensitive as budget decreases."""

    def test_same_bid_scores_lower_with_less_budget(self) -> None:
        market = EpistemicMarket()
        bid = EpistemicActionBid(
            action=EpistemicAction(
                action_id="a1", action_type=ActionType.RETRIEVE,
                operator_name="test",
            ),
            expected_information_gain=0.5,
            estimated_token_cost=500,
        )
        state_rich = EpistemicState(
            version=0,
            process=ProcessState(episode_id="ep", goal="test"),
            budget=BudgetState(max_tokens=10000, tokens_used=0),
        )
        state_poor = EpistemicState(
            version=0,
            process=ProcessState(episode_id="ep", goal="test"),
            budget=BudgetState(max_tokens=10000, tokens_used=9000),
        )
        score_rich = market.evaluate_bid(bid, state_rich)
        score_poor = market.evaluate_bid(bid, state_poor)
        assert score_rich > score_poor


class TestAssumptionFlipResponsiveness:
    """Conclusions should change when causally decisive assumptions are flipped."""

    def test_decisive_perturbation_registers_as_responsive(self) -> None:
        lab = CounterfactualLab()
        lab.record_sensitivity(SensitivityResult(
            target_id="a1", target_type="assumption",
            perturbation="flip critical assumption",
            conclusion_changed=True,
            is_causally_decisive=True,
        ))
        assert lab.responsiveness_score() == 1.0

    def test_irrelevant_perturbation_registers_as_robust(self) -> None:
        lab = CounterfactualLab()
        lab.record_sensitivity(SensitivityResult(
            target_id="a2", target_type="assumption",
            perturbation="flip irrelevant detail",
            conclusion_changed=False,
            is_causally_decisive=False,
        ))
        assert lab.robustness_score() == 1.0


class TestEventReplayEquivalence:
    """Replaying events from an initial state must produce equivalent state."""

    @pytest.mark.asyncio
    async def test_full_controller_replay(self) -> None:
        from asar.epistemic.store import AppendOnlyEventStore
        from asar.metacognition.controller import EpistemicController
        from asar.operators.registry import OperatorRegistry
        from asar.operators.stop import StopOperator

        class SimpleRetrieve:
            @property
            def name(self) -> str:
                return "retrieve"

            async def propose(self, state):
                if state.evidence_ids:
                    return []
                from schemas.ree.epistemic_event import EpistemicActionBid
                return [EpistemicActionBid(
                    action=EpistemicAction(
                        action_id="a_r", action_type=ActionType.RETRIEVE,
                        operator_name="retrieve",
                    ),
                    expected_information_gain=0.8,
                    estimated_token_cost=50,
                )]

            async def execute(self, state, action):
                from schemas.ree.epistemic_event import OperatorOutcome, OperatorResult
                from schemas.ree.epistemic_state import ResourceCost
                return OperatorResult(
                    operator_name="retrieve", action_id=action.action_id,
                    outcome=OperatorOutcome.SUCCESS,
                    artifacts_produced={"evidence_001": {"content": "test"}},
                    resource_cost=ResourceCost(input_tokens=25, output_tokens=25),
                )

        registry = OperatorRegistry()
        registry.register(SimpleRetrieve())
        registry.register(StopOperator())

        controller = EpistemicController(
            registry=registry,
            budget=BudgetState(max_tokens=5000, max_steps=10),
        )

        final = await controller.run("replay test")
        events = controller.event_store.get_all()

        from asar.epistemic.reducer import StateReducer
        initial = EpistemicState(
            version=0,
            process=ProcessState(episode_id=final.process.episode_id, goal="replay test"),
            budget=BudgetState(max_tokens=5000, max_steps=10),
        )
        replayed = StateReducer().replay(initial, events)

        assert replayed.version == final.version
        assert replayed.evidence_ids == final.evidence_ids
        assert replayed.process.status == final.process.status
