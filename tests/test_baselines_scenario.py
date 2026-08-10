"""
Tests for baselines, scenario runner, and ablation config — Phase 10B.
"""

import asyncio

import pytest

from asar.evaluation.baselines import (
    DirectModelBaseline,
    FixedDepthREEBaseline,
    REEAdaptiveBaseline,
    SimpleReflectionBaseline,
)
from asar.evaluation.scenario import (
    AblationConfig,
    ResultStore,
    ScenarioRegistry,
    ScenarioSpec,
    leakage_check,
)
from asar.operators.registry import OperatorRegistry
from asar.operators.stop import StopOperator
from schemas.ree.epistemic_event import (
    ActionType,
    EpistemicAction,
    EpistemicActionBid,
    OperatorOutcome,
    OperatorResult,
)
from schemas.ree.epistemic_state import BudgetState, EpistemicState, ResourceCost


# ---------------------------------------------------------------
# Mock operator for baselines
# ---------------------------------------------------------------

class _MockRetrieveOp:
    @property
    def name(self): return "retrieve"
    async def propose(self, state):
        if state.evidence_ids: return []
        return [EpistemicActionBid(
            action=EpistemicAction(action_id="a_r", action_type=ActionType.RETRIEVE, operator_name="retrieve"),
            expected_information_gain=0.6, estimated_token_cost=50,
        )]
    async def execute(self, state, action):
        return OperatorResult(
            operator_name="retrieve", action_id=action.action_id,
            outcome=OperatorOutcome.SUCCESS,
            artifacts_produced={"evidence_001": {"content": "test"}},
            workspace_additions=["evidence_001"],
            resource_cost=ResourceCost(input_tokens=25, output_tokens=25),
        )


# ---------------------------------------------------------------
# Baseline tests
# ---------------------------------------------------------------

class TestDirectModelBaseline:
    @pytest.mark.asyncio
    async def test_single_step(self):
        b = DirectModelBaseline()
        result = await b.run("Test question", budget=BudgetState(max_tokens=1000))
        assert result.baseline_name == "B0_direct_model"
        assert result.steps_used == 1
        assert result.tokens_used > 0
        assert result.tokens_used <= 1000

    @pytest.mark.asyncio
    async def test_respects_budget(self):
        b = DirectModelBaseline()
        result = await b.run("Q", budget=BudgetState(max_tokens=100))
        assert result.tokens_used <= 100


class TestSimpleReflectionBaseline:
    @pytest.mark.asyncio
    async def test_three_steps(self):
        b = SimpleReflectionBaseline()
        result = await b.run("Test question", budget=BudgetState(max_tokens=3000))
        assert result.baseline_name == "B1_simple_reflection"
        assert result.steps_used == 3
        assert result.tokens_used > 0

    @pytest.mark.asyncio
    async def test_produces_claims(self):
        b = SimpleReflectionBaseline()
        result = await b.run("Q", budget=BudgetState(max_tokens=3000))
        assert len(result.claims) == 3


class TestFixedDepthREEBaseline:
    @pytest.mark.asyncio
    async def test_runs_fixed_sequence(self):
        reg = OperatorRegistry()
        reg.register(_MockRetrieveOp())
        reg.register(StopOperator())
        b = FixedDepthREEBaseline(operators=reg)
        result = await b.run("Test", budget=BudgetState(max_tokens=5000, max_steps=20))
        assert result.baseline_name == "B3_fixed_depth_ree"
        assert result.steps_used > 0
        assert result.final_state is not None


class TestREEAdaptiveBaseline:
    @pytest.mark.asyncio
    async def test_adaptive_run(self):
        reg = OperatorRegistry()
        reg.register(_MockRetrieveOp())
        reg.register(StopOperator())
        b = REEAdaptiveBaseline(registry=reg)
        result = await b.run("Test", budget=BudgetState(max_tokens=5000, max_steps=10))
        assert result.baseline_name == "B4_ree_adaptive"
        assert result.final_state is not None


# ---------------------------------------------------------------
# Scenario registry tests
# ---------------------------------------------------------------

class TestScenarioRegistry:
    def test_register_and_retrieve(self):
        reg = ScenarioRegistry()
        spec = ScenarioSpec(
            scenario_id="sc_001", family="false_majority",
            question="What caused X?", ground_truth="Y",
            split="dev", seed=42,
        )
        reg.register(spec)
        assert reg.get("sc_001") is not None
        assert reg.get("sc_001").family == "false_majority"

    def test_split_filtering(self):
        reg = ScenarioRegistry()
        for i in range(5):
            reg.register(ScenarioSpec(
                scenario_id=f"dev_{i}", family="test",
                question=f"Q{i}", split="dev",
            ))
        for i in range(3):
            reg.register(ScenarioSpec(
                scenario_id=f"hold_{i}", family="test",
                question=f"HQ{i}", split="holdout",
            ))
        assert len(reg.dev_scenarios()) == 5
        assert len(reg.holdout_scenarios()) == 3

    def test_family_filtering(self):
        reg = ScenarioRegistry()
        reg.register(ScenarioSpec(scenario_id="a", family="A", question="Q"))
        reg.register(ScenarioSpec(scenario_id="b", family="B", question="Q"))
        assert len(reg.by_family("A")) == 1
        assert len(reg.by_family("B")) == 1

    def test_deterministic_generation(self):
        reg = ScenarioRegistry()
        def template(family, index, seed, split):
            return ScenarioSpec(
                scenario_id=f"{family}_{seed}",
                family=family, question=f"Q_{seed}",
                seed=seed, split=split,
            )
        generated = reg.generate_deterministic(
            family="test", template_fn=template, count=5, base_seed=100,
        )
        assert len(generated) == 5
        assert generated[0].seed == 100
        assert generated[4].seed == 104


# ---------------------------------------------------------------
# Leakage check tests
# ---------------------------------------------------------------

class TestLeakageCheck:
    def test_no_leakage(self):
        dev = [ScenarioSpec(scenario_id="d1", family="f", question="What is A?")]
        holdout = [ScenarioSpec(scenario_id="h1", family="f", question="What is B?")]
        assert leakage_check(dev, holdout) == []

    def test_detects_leakage(self):
        dev = [ScenarioSpec(scenario_id="d1", family="f", question="What is A?")]
        holdout = [ScenarioSpec(scenario_id="h1", family="f", question="What is A?")]
        violations = leakage_check(dev, holdout)
        assert "h1" in violations


# ---------------------------------------------------------------
# Ablation config tests
# ---------------------------------------------------------------

class TestAblationConfig:
    def test_full_ree_all_enabled(self):
        cfg = AblationConfig.full_ree()
        assert all(v for v in cfg.values())

    def test_leave_one_out(self):
        cfg = AblationConfig.leave_one_out("sealed_tribunal")
        assert cfg["sealed_tribunal"] is False
        assert cfg["hypothesis_ecology"] is True

    def test_additive(self):
        cfg = AblationConfig.additive("ontology_forge")
        assert cfg["ontology_forge"] is True
        core = {"hypothesis_ecology", "ignorance_ledger", "epistemic_market", "stopping_policy"}
        for m in core:
            assert cfg[m] is True
        for m in AblationConfig.FULL_REE_MECHANISMS:
            if m not in core and m != "ontology_forge":
                assert cfg[m] is False

    def test_all_leave_one_out_coverage(self):
        configs = AblationConfig.all_leave_one_out_configs()
        assert len(configs) == len(AblationConfig.FULL_REE_MECHANISMS)
        for name, cfg in configs.items():
            disabled = [m for m, v in cfg.items() if not v]
            assert len(disabled) == 1


# ---------------------------------------------------------------
# Result store tests
# ---------------------------------------------------------------

class TestResultStore:
    def test_save_and_load(self, tmp_path):
        from asar.evaluation.scenario import ScenarioResult
        store = ResultStore(tmp_path / "results.jsonl")
        r = ScenarioResult(
            scenario_id="sc_001", architecture="full_ree",
            experiment_id="exp_001", tokens_used=500,
        )
        store.save(r)
        loaded = store.load_all()
        assert len(loaded) == 1
        assert loaded[0]["scenario_id"] == "sc_001"
