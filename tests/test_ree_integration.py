"""
Full REE integration test — validates end-to-end with all components.

This test uses mocked operators to run a complete REE research episode
and verifies that all components integrate correctly.
"""

from __future__ import annotations

import pytest

from asar.epistemic.store import AppendOnlyEventStore
from asar.epistemic.diff import compute_diff
from asar.metacognition.controller import EpistemicController
from asar.metacognition.stopping import StoppingPolicy, StoppingDecision
from asar.metacognition.trajectory import TrajectoryDataset, TrajectoryStep
from asar.operators.registry import OperatorRegistry
from asar.operators.stop import StopOperator, AbstainOperator
from asar.world_model.hypothesis_graph import HypothesisGraph
from asar.world_model.belief_tracker import BeliefTracker
from asar.ignorance.ledger import IgnoranceLedger
from asar.ontology.forge import OntologyForge
from asar.ontology.counterfactual import CounterfactualLab
from asar.ontology.experiment_designer import ExperimentDesigner
from asar.social.tribunal import DissonanceTribunal
from asar.social.trust import EvidenceIndependenceAnalyzer
from asar.social.stakeholder import StakeholderRegistry
from asar.self_model.tracker import EpisodeTracker
from asar.self_model.calibration import CalibrationAnalyzer
from asar.self_model.predictor import CapabilityPredictor
from asar.memory_federation.federation import FederatedMemory
from asar.memory_federation.consolidation import MemoryConsolidator
from asar.value_model.principles import ValueRegistry
from asar.value_model.equilibrium import ReflectiveEquilibrium
from asar.evaluation.epistemic_metrics import EpistemicMetrics
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
    ProcessState,
    ResourceCost,
)
from schemas.ree.ignorance import IgnoranceItem, IgnoranceType
from schemas.ree.memory import MemoryStore
from schemas.ree.self_model import EpisodeRecord
from schemas.ree.social import EvidenceProvenance, StakeholderModel, TribunalRole
from schemas.ree.world_model import Hypothesis, HypothesisStatus


class MockRetrieveOp:
    @property
    def name(self) -> str:
        return "retrieve"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        if state.evidence_ids:
            return []
        return [EpistemicActionBid(
            action=EpistemicAction(
                action_id="act_r", action_type=ActionType.RETRIEVE,
                operator_name="retrieve",
            ),
            expected_information_gain=0.8,
            estimated_token_cost=100,
        )]

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        return OperatorResult(
            operator_name="retrieve", action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS,
            artifacts_produced={
                "evidence_001": {"content": "GDP fell 4.3% in Q4 2008"},
                "evidence_002": {"content": "Lehman Brothers collapsed September 2008"},
            },
            workspace_additions=["evidence_001", "evidence_002"],
            resource_cost=ResourceCost(input_tokens=50, output_tokens=50),
        )


class MockSynthesizeOp:
    @property
    def name(self) -> str:
        return "synthesize"

    async def propose(self, state: EpistemicState) -> list[EpistemicActionBid]:
        if not state.evidence_ids or state.claim_ids:
            return []
        return [EpistemicActionBid(
            action=EpistemicAction(
                action_id="act_s", action_type=ActionType.SYNTHESIZE,
                operator_name="synthesize",
            ),
            expected_information_gain=0.6,
            probability_changes_decision=0.7,
            estimated_token_cost=200,
        )]

    async def execute(self, state: EpistemicState, action: EpistemicAction) -> OperatorResult:
        return OperatorResult(
            operator_name="synthesize", action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS,
            artifacts_produced={
                "claim_001": {
                    "text": "The 2008 financial crisis was triggered by the collapse of Lehman Brothers",
                    "supporting_evidence_ids": ["evidence_001", "evidence_002"],
                },
            },
            workspace_additions=["claim_001"],
            resource_cost=ResourceCost(input_tokens=100, output_tokens=200),
        )


@pytest.mark.asyncio
async def test_full_ree_integration() -> None:
    """Run a complete REE episode and validate all component interactions."""

    registry = OperatorRegistry()
    registry.register(MockRetrieveOp())
    registry.register(MockSynthesizeOp())
    registry.register(StopOperator())
    registry.register(AbstainOperator())

    store = AppendOnlyEventStore()
    controller = EpistemicController(
        registry=registry,
        event_store=store,
        budget=BudgetState(max_tokens=10000, max_steps=10),
    )

    final_state = await controller.run("What caused the 2008 financial crisis?")

    assert final_state.process.status in ("completed", "stopped")
    assert final_state.version > 0
    assert len(store) > 0
    assert "evidence_001" in final_state.evidence_ids

    initial = EpistemicState(
        version=0,
        process=ProcessState(
            episode_id=final_state.process.episode_id,
            goal="What caused the 2008 financial crisis?",
        ),
        budget=BudgetState(max_tokens=10000, max_steps=10),
    )
    replayed = controller.reducer.replay(initial, store.get_all())
    assert replayed.version == final_state.version
    assert replayed.evidence_ids == final_state.evidence_ids

    diff = compute_diff(initial, final_state)
    assert len(diff.new_evidence_ids) >= 2
    assert diff.budget_tokens_consumed > 0

    hyp_graph = HypothesisGraph()
    hyp_graph.add_hypothesis(Hypothesis(
        hypothesis_id="h1",
        statement="Financial crisis was caused by banking deregulation",
        ontology_frame="institutional",
    ))
    hyp_graph.add_hypothesis(Hypothesis(
        hypothesis_id="h2",
        statement="Financial crisis was caused by excessive leverage",
        ontology_frame="financial",
    ))
    assert hyp_graph.hypothesis_diversity_score() > 0

    tracker = BeliefTracker()
    tracker.record("h1", 1, 0.5, HypothesisStatus.PROPOSED)
    tracker.record("h1", 3, 0.7, HypothesisStatus.ACTIVE)
    assert tracker.latest("h1").posterior == 0.7

    ledger = IgnoranceLedger()
    ledger.add(IgnoranceItem(
        ignorance_id="ig1",
        ignorance_type=IgnoranceType.MISSING_EVIDENCE,
        description="Missing data on derivatives market",
        probability_decision_relevant=0.8,
        impact_if_resolved=0.7,
        resolvability=0.5,
    ))
    assert ledger.prioritized()[0].ignorance_id == "ig1"

    forge = OntologyForge()
    forge.create_revision("default", "Financial", key_variables=["leverage", "risk"])

    lab = CounterfactualLab()
    world = lab.create_world(perturbation_type="evidence_removal", description="Remove Lehman evidence")

    designer = ExperimentDesigner()
    designer.propose_experiment("Check derivatives data", ["h1"], expected_information_gain=0.7)

    tribunal = DissonanceTribunal()
    tribunal.submit_sealed(TribunalRole.ADVOCATE, "Banking deregulation was the cause",
                           hypothesis_id="h1", confidence=0.7)
    tribunal.submit_sealed(TribunalRole.FALSIFIER, "But what about monetary policy?",
                           hypothesis_id="h1", confidence=0.4, evidence_cited=["e_mp"])
    tribunal.complete_sealed_phase()
    verdict = tribunal.adjudicate("h1")
    assert len(verdict.surviving_positions) > 0

    independence = EvidenceIndependenceAnalyzer()
    independence.register_provenance(EvidenceProvenance(
        evidence_id="evidence_001", original_source_id="fed_reserve",
    ))
    independence.register_provenance(EvidenceProvenance(
        evidence_id="evidence_002", original_source_id="nber",
    ))
    assert independence.evidence_independence_score(["evidence_001", "evidence_002"]) == 1.0

    ep_tracker = EpisodeTracker()
    ep_tracker.record(EpisodeRecord(
        episode_id=final_state.process.episode_id,
        domain="economics",
        confidence_predicted=0.7,
        success_actual=0.8,
        total_tokens=final_state.budget.tokens_used,
    ))

    predictor = CapabilityPredictor()
    est = predictor.estimate(ep_tracker.all_records(), task_signature="")
    assert est.sample_count == 1

    calibrator = CalibrationAnalyzer()
    points = ep_tracker.calibration_points()
    brier = calibrator.brier_score(points)
    assert 0.0 <= brier <= 1.0

    memory = FederatedMemory()
    memory.store(MemoryStore.EPISODIC, {"episode": final_state.process.episode_id, "result": "success"})
    memory.store(MemoryStore.SEMANTIC, "Financial crises often involve banking failures", tags=["economics"])
    memory.store(MemoryStore.PROCEDURAL, {"strategy": "retrieve_then_synthesize", "success_rate": 0.8})

    values = ValueRegistry()
    eq = ReflectiveEquilibrium(values)
    eq.propose_revision("completeness", 0.8, "economic topics need thorough coverage")
    assert values.get("completeness").weight == pytest.approx(0.8)

    stopping = StoppingPolicy()
    reason = stopping.evaluate(final_state)
    assert reason.decision in (StoppingDecision.STOP, StoppingDecision.CONTINUE, StoppingDecision.RETURN_PARTIAL)

    metrics = EpistemicMetrics()
    result = metrics.compute_all(
        brier_score=brier,
        anticipated_failures=["missing_data"],
        actual_failures=["missing_data", "limited_sources"],
        mpr=tribunal.minority_preservation_rate(),
        eis=independence.evidence_independence_score(["evidence_001", "evidence_002"]),
        hypothesis_diversity=hyp_graph.hypothesis_diversity_score(),
        total_tokens=final_state.budget.tokens_used,
        total_steps=final_state.process.step_count,
    )
    assert result.brier_score is not None
    assert result.total_tokens > 0
