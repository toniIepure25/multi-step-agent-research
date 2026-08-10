"""
Phase 12 — Counterfactual Cognitive Policy Study tests.

Tests state forking, CognitiveActionOutcomeDataset, realized gain computation,
regret analysis, bid calibration, feature importance, and the full fork pipeline.
"""

from __future__ import annotations

import pytest

from asar.common import generate_id
from asar.epistemic.reducer import StateReducer
from asar.evaluation.counterfactual_study import (
    CognitiveActionOutcomeDataset,
    CounterfactualForkRunner,
    compute_realized_gain,
    extract_state_features,
    fork_and_execute,
)
from asar.evaluation.scenarios.generators import generate_false_majority, generate_hypothesis_ecology
from asar.evaluation.benchmark_runner import ScenarioRetrieveOperator, ScenarioHypothesisOperator
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
    HypothesisView,
    IgnoranceView,
    MaterializedViews,
    ProcessState,
    ResourceCost,
    SelfModelSummary,
)
from schemas.ree.experiment import (
    CognitiveActionOutcome,
    CognitiveActionRegret,
    EpistemicStateFeatures,
    RealizedEpistemicGain,
)


def _make_state(**kwargs) -> EpistemicState:
    defaults = {
        "version": 0,
        "process": ProcessState(episode_id="ep_cf", goal="counterfactual test"),
        "budget": BudgetState(max_tokens=5000, max_steps=10),
    }
    defaults.update(kwargs)
    return EpistemicState(**defaults)


# ---------------------------------------------------------------
# Feature extraction tests
# ---------------------------------------------------------------

class TestFeatureExtraction:
    def test_extracts_from_empty_state(self):
        state = _make_state()
        features = extract_state_features(state)
        assert features.hypothesis_entropy == 0.0
        assert features.evidence_count == 0
        assert features.budget_fraction == 1.0

    def test_extracts_from_rich_state(self):
        views = MaterializedViews(
            hypotheses={
                "h1": HypothesisView(hypothesis_id="h1", posterior=0.7, status="proposed"),
                "h2": HypothesisView(hypothesis_id="h2", posterior=0.3, status="proposed"),
            },
            ignorance_items={
                "i1": IgnoranceView(ignorance_id="i1", priority=0.8, status="open"),
            },
            self_model=SelfModelSummary(overall_success_rate=0.75),
        ).compute_derived(
            workspace=_make_state().workspace,
            contradiction_count=1,
            evidence_count=3,
        )
        state = _make_state(
            views=views,
            evidence_ids=["e1", "e2", "e3"],
        )
        features = extract_state_features(state)
        assert features.hypothesis_entropy > 0
        assert features.evidence_count == 3
        assert features.highest_ignorance_priority == 0.8
        assert features.self_model_expected_success == 0.75

    def test_no_outcome_leakage(self):
        features = extract_state_features(_make_state())
        assert not hasattr(features, "ground_truth")
        assert not hasattr(features, "final_quality")


# ---------------------------------------------------------------
# Fork and execute tests
# ---------------------------------------------------------------

class TestForkAndExecute:
    @pytest.mark.asyncio
    async def test_fork_produces_new_state(self):
        scenario = generate_false_majority(seed=42)
        op = ScenarioRetrieveOperator(scenario.evidence_pool)
        state = _make_state()

        new_state, cost = await fork_and_execute(state, op)
        assert new_state.version > state.version
        assert len(new_state.evidence_ids) > 0
        assert cost.total_tokens > 0

    @pytest.mark.asyncio
    async def test_fork_does_not_mutate_original(self):
        scenario = generate_false_majority(seed=42)
        op = ScenarioRetrieveOperator(scenario.evidence_pool)
        state = _make_state()
        original_version = state.version
        original_evidence = list(state.evidence_ids)

        await fork_and_execute(state, op)
        assert state.version == original_version
        assert state.evidence_ids == original_evidence


# ---------------------------------------------------------------
# Realized gain tests
# ---------------------------------------------------------------

class TestRealizedGain:
    def test_gain_from_evidence_addition(self):
        state_before = _make_state()
        state_after = _make_state(evidence_ids=["e1", "e2"])
        cost = ResourceCost(input_tokens=100, output_tokens=100)

        gain = compute_realized_gain(state_before, state_after, cost)
        assert gain.task_quality_delta > 0
        assert gain.compute_cost > 0

    def test_gain_is_vector_not_scalar(self):
        gain = RealizedEpistemicGain(
            task_quality_delta=0.3,
            hypothesis_discrimination_delta=0.2,
            compute_cost=0.5,
        )
        v = gain.to_vector()
        assert len(v) == 8

    def test_scalarization_sensitivity(self):
        gain = RealizedEpistemicGain(
            task_quality_delta=0.5,
            compute_cost=2.0,
        )
        w_ignore_cost = {"task_quality_delta": 1.0, "compute_cost": 0.0}
        w_penalize_cost = {"task_quality_delta": 1.0, "compute_cost": -1.0}

        s1 = gain.scalarize(w_ignore_cost)
        s2 = gain.scalarize(w_penalize_cost)
        assert s1 > s2


# ---------------------------------------------------------------
# CognitiveActionOutcomeDataset tests
# ---------------------------------------------------------------

class TestCognitiveActionOutcomeDataset:
    def test_add_and_retrieve(self):
        ds = CognitiveActionOutcomeDataset()
        outcome = CognitiveActionOutcome(
            outcome_id="cao_1", episode_id="ep_1", step=0,
            state_features=EpistemicStateFeatures(),
            action_type="retrieve", operator_name="retrieve",
            realized_gain=RealizedEpistemicGain(task_quality_delta=0.3),
        )
        ds.add(outcome)
        assert len(ds) == 1
        assert ds.all()[0].action_type == "retrieve"

    def test_by_action_filter(self):
        ds = CognitiveActionOutcomeDataset()
        for action in ["retrieve", "reason", "retrieve", "stop"]:
            ds.add(CognitiveActionOutcome(
                outcome_id=generate_id("cao"), episode_id="ep_1", step=0,
                state_features=EpistemicStateFeatures(),
                action_type=action, operator_name=action,
            ))
        assert len(ds.by_action("retrieve")) == 2
        assert len(ds.by_action("stop")) == 1

    def test_mean_gain_by_action(self):
        ds = CognitiveActionOutcomeDataset()
        ds.add(CognitiveActionOutcome(
            outcome_id="c1", episode_id="ep_1", step=0,
            state_features=EpistemicStateFeatures(),
            action_type="retrieve", operator_name="retrieve",
            realized_gain=RealizedEpistemicGain(task_quality_delta=0.5),
        ))
        ds.add(CognitiveActionOutcome(
            outcome_id="c2", episode_id="ep_1", step=1,
            state_features=EpistemicStateFeatures(),
            action_type="reason", operator_name="reason",
            realized_gain=RealizedEpistemicGain(task_quality_delta=0.3),
        ))
        means = ds.mean_gain_by_action({"task_quality_delta": 1.0})
        assert means["retrieve"] > means["reason"]

    def test_bid_vs_realized_correlation(self):
        ds = CognitiveActionOutcomeDataset()
        for i in range(10):
            ds.add(CognitiveActionOutcome(
                outcome_id=f"c{i}", episode_id="ep_1", step=i,
                state_features=EpistemicStateFeatures(),
                action_type="retrieve", operator_name="retrieve",
                bid_score=i * 0.1,
                realized_gain=RealizedEpistemicGain(task_quality_delta=i * 0.1),
            ))
        rho = ds.bid_vs_realized_correlation()
        assert rho > 0.5

    def test_feature_importance_proxy(self):
        ds = CognitiveActionOutcomeDataset()
        for i in range(20):
            ds.add(CognitiveActionOutcome(
                outcome_id=f"c{i}", episode_id="ep_1", step=i,
                state_features=EpistemicStateFeatures(
                    hypothesis_entropy=i * 0.1,
                    budget_fraction=1.0 - i * 0.04,
                ),
                action_type="retrieve", operator_name="retrieve",
                realized_gain=RealizedEpistemicGain(
                    task_quality_delta=i * 0.05,
                ),
            ))
        importance = ds.feature_importance_proxy()
        assert len(importance) > 0

    def test_persistence(self, tmp_path):
        path = tmp_path / "outcomes.jsonl"
        ds = CognitiveActionOutcomeDataset(path=path)
        ds.add(CognitiveActionOutcome(
            outcome_id="c1", episode_id="ep_1", step=0,
            state_features=EpistemicStateFeatures(),
            action_type="retrieve", operator_name="retrieve",
        ))
        assert path.exists()
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 1


# ---------------------------------------------------------------
# Regret computation tests
# ---------------------------------------------------------------

class TestRegretComputation:
    def test_regret_from_forked_outcomes(self):
        outcomes = {
            "retrieve": RealizedEpistemicGain(task_quality_delta=0.3, compute_cost=0.1),
            "reason": RealizedEpistemicGain(task_quality_delta=0.5, compute_cost=0.2),
            "stop": RealizedEpistemicGain(task_quality_delta=0.0, compute_cost=0.0),
        }
        regret = CognitiveActionRegret.compute(
            fork_state_version=3,
            episode_id="ep_1",
            selected_action="retrieve",
            outcomes=outcomes,
        )
        assert regret.regret >= 0
        assert regret.best_action == "reason"

    def test_two_scalarizations_produce_different_regret(self):
        outcomes = {
            "retrieve": RealizedEpistemicGain(task_quality_delta=0.5, compute_cost=2.0),
            "reason": RealizedEpistemicGain(task_quality_delta=0.6, compute_cost=5.0),
        }
        r1 = CognitiveActionRegret.compute(
            fork_state_version=1, episode_id="ep_1",
            selected_action="retrieve", outcomes=outcomes,
            weights={"task_quality_delta": 1.0, "compute_cost": 0.0},
        )
        r2 = CognitiveActionRegret.compute(
            fork_state_version=1, episode_id="ep_1",
            selected_action="retrieve", outcomes=outcomes,
            weights={"task_quality_delta": 1.0, "compute_cost": -1.0},
        )
        assert r1.regret > 0
        assert r2.regret == 0.0


# ---------------------------------------------------------------
# Full counterfactual fork pipeline
# ---------------------------------------------------------------

class TestCounterfactualForkRunner:
    @pytest.mark.asyncio
    async def test_fork_runner_collects_outcomes(self):
        dataset = CognitiveActionOutcomeDataset()
        runner = CounterfactualForkRunner(dataset=dataset)

        scenario = generate_hypothesis_ecology(seed=42)
        operators = [
            ScenarioRetrieveOperator(scenario.evidence_pool),
            ScenarioHypothesisOperator(),
        ]

        state = _make_state(evidence_ids=["e1"])
        state = state.model_copy(update={
            "artifacts": {"e1": {"content": "test evidence"}},
        })

        outcomes = await runner.run_fork(state, operators)
        assert len(dataset) > 0
        for o in outcomes:
            assert o.state_features.state_version == state.version

    @pytest.mark.asyncio
    async def test_fork_runner_computes_regret(self):
        dataset = CognitiveActionOutcomeDataset()
        runner = CounterfactualForkRunner(dataset=dataset)

        scenario = generate_false_majority(seed=42)
        operators = [
            ScenarioRetrieveOperator(scenario.evidence_pool),
            StopOperator(),
        ]

        state = _make_state()
        outcomes = await runner.run_fork(
            state, operators, selected_action="retrieve",
        )

        if outcomes:
            regret = runner.compute_regret(outcomes, "retrieve")
            assert regret is not None
            assert regret.regret >= 0

    @pytest.mark.asyncio
    async def test_batch_fork_collection(self):
        """Collect many outcomes across multiple scenarios for dataset building."""
        dataset = CognitiveActionOutcomeDataset()
        runner = CounterfactualForkRunner(dataset=dataset)

        for seed in range(42, 52):
            scenario = generate_false_majority(seed=seed)
            operators = [
                ScenarioRetrieveOperator(scenario.evidence_pool),
                ScenarioHypothesisOperator(),
            ]
            state = _make_state(
                process=ProcessState(episode_id=f"ep_{seed}", goal="test"),
                evidence_ids=["e_base"],
                artifacts={"e_base": {"content": "base evidence"}},
            )
            await runner.run_fork(state, operators)

        assert len(dataset) >= 10
        assert len(dataset.episode_ids()) >= 5

    @pytest.mark.asyncio
    async def test_action_confusion_matrix(self):
        dataset = CognitiveActionOutcomeDataset()
        for i in range(20):
            dataset.add(CognitiveActionOutcome(
                outcome_id=f"c{i}", episode_id="ep_1", step=i,
                state_features=EpistemicStateFeatures(),
                action_type="retrieve" if i < 10 else "reason",
                operator_name="retrieve" if i < 10 else "reason",
                realized_gain=RealizedEpistemicGain(
                    task_quality_delta=0.5 if i < 10 else 0.1,
                ),
            ))
        matrix = dataset.action_confusion_matrix()
        assert "high_gain" in matrix
        assert "low_gain" in matrix
