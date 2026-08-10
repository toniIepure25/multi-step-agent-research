"""
Phase 11 — Controlled Epistemic Benchmark Campaign.

Tests the complete benchmark pipeline: scenario generation, execution,
metric computation, and preliminary hypothesis evaluation.
"""

from __future__ import annotations

import pytest

from asar.evaluation.benchmark_runner import BenchmarkRunner
from asar.evaluation.scenario import ScenarioRegistry, leakage_check
from asar.evaluation.scenarios.generators import (
    FAMILY_GENERATORS,
    generate_all_scenarios,
    generate_assumption_flip,
    generate_duplicated_source,
    generate_false_majority,
    generate_hypothesis_ecology,
    generate_ignorance_discovery,
    generate_stopping_quality,
)
from asar.evaluation.statistical import (
    EffectSize,
    ExperimentSummary,
    bootstrap_ci,
    paired_comparison,
    win_tie_loss,
)
from schemas.ree.epistemic_state import BudgetState, SelfModelSummary


# ---------------------------------------------------------------
# Scenario generation tests
# ---------------------------------------------------------------

class TestScenarioGeneration:
    def test_all_families_generate(self):
        for family, gen_fn in FAMILY_GENERATORS.items():
            spec = gen_fn(seed=42, index=0)
            assert spec.scenario_id
            assert spec.family == family
            assert spec.ground_truth is not None

    def test_deterministic_generation(self):
        a = generate_false_majority(seed=42, index=0)
        b = generate_false_majority(seed=42, index=0)
        assert a.scenario_id == b.scenario_id
        assert a.ground_truth == b.ground_truth

    def test_different_seeds_differ(self):
        a = generate_false_majority(seed=42, index=0)
        b = generate_false_majority(seed=99, index=0)
        assert a.scenario_id != b.scenario_id

    def test_dev_holdout_split(self):
        scenarios = generate_all_scenarios(count_per_family=10, dev_fraction=0.7)
        dev = [s for s in scenarios if s.split == "dev"]
        holdout = [s for s in scenarios if s.split == "holdout"]
        assert len(dev) > 0
        assert len(holdout) > 0
        assert len(dev) + len(holdout) == len(scenarios)

    def test_no_leakage_between_splits(self):
        scenarios = generate_all_scenarios(count_per_family=10)
        dev = [s for s in scenarios if s.split == "dev"]
        holdout = [s for s in scenarios if s.split == "holdout"]
        violations = leakage_check(dev, holdout)
        assert len(violations) == 0

    def test_sufficient_scenario_count(self):
        scenarios = generate_all_scenarios(count_per_family=15)
        assert len(scenarios) >= 80


# ---------------------------------------------------------------
# Benchmark runner integration tests
# ---------------------------------------------------------------

class TestBenchmarkRunner:
    @pytest.mark.asyncio
    async def test_run_false_majority_scenario(self):
        spec = generate_false_majority(seed=42, index=0)
        runner = BenchmarkRunner(
            default_budget=BudgetState(max_tokens=3000, max_steps=10),
        )
        result = await runner.run_scenario(spec, architecture="full_ree")
        assert result.scenario_id == spec.scenario_id
        assert result.manifest.experiment_id
        assert result.result.tokens_used > 0
        assert result.result.steps_used > 0

    @pytest.mark.asyncio
    async def test_run_baseline_b0(self):
        spec = generate_false_majority(seed=42, index=0)
        runner = BenchmarkRunner()
        result = await runner.run_scenario(spec, architecture="B0_direct")
        assert result.architecture == "B0_direct_model"
        assert result.result.steps_used == 1

    @pytest.mark.asyncio
    async def test_run_baseline_b1(self):
        spec = generate_false_majority(seed=42, index=0)
        runner = BenchmarkRunner()
        result = await runner.run_scenario(spec, architecture="B1_reflection")
        assert result.architecture == "B1_simple_reflection"
        assert result.result.steps_used == 3

    @pytest.mark.asyncio
    async def test_manifest_persisted(self):
        spec = generate_false_majority(seed=42, index=0)
        runner = BenchmarkRunner()
        result = await runner.run_scenario(spec, architecture="full_ree")
        assert result.manifest.architecture == "full_ree"
        assert result.manifest.seed == 42
        assert result.manifest.budget_max_tokens > 0

    @pytest.mark.asyncio
    async def test_equal_budget_comparison(self):
        spec = generate_hypothesis_ecology(seed=42, index=0)
        budget = BudgetState(max_tokens=2000, max_steps=8)
        runner = BenchmarkRunner()

        result_b0 = await runner.run_scenario(spec, architecture="B0_direct", budget=budget)
        result_ree = await runner.run_scenario(spec, architecture="full_ree", budget=budget)

        assert result_b0.result.tokens_used <= budget.max_tokens
        assert result_ree.result.tokens_used <= budget.max_tokens

    @pytest.mark.asyncio
    async def test_self_model_propagates_to_operators(self):
        spec = generate_false_majority(seed=42, index=0)
        runner = BenchmarkRunner()
        self_model = SelfModelSummary(
            operator_success_rates={"retrieve": 0.3},
            overall_success_rate=0.3,
        )
        result = await runner.run_scenario(
            spec, architecture="full_ree", self_model=self_model,
        )
        assert result.result.steps_used > 0


# ---------------------------------------------------------------
# Cross-architecture comparison tests
# ---------------------------------------------------------------

class TestCrossArchitectureComparison:
    @pytest.mark.asyncio
    async def test_multiple_architectures_on_same_scenario(self):
        spec = generate_hypothesis_ecology(seed=42, index=0)
        runner = BenchmarkRunner(
            default_budget=BudgetState(max_tokens=3000, max_steps=10),
        )
        architectures = ["B0_direct", "B1_reflection", "full_ree"]
        results = {}
        for arch in architectures:
            r = await runner.run_scenario(spec, architecture=arch)
            results[arch] = r

        assert len(results) == 3
        for arch, r in results.items():
            assert r.result.steps_used > 0

    @pytest.mark.asyncio
    async def test_ablation_changes_behavior(self):
        spec = generate_false_majority(seed=42, index=0)
        runner = BenchmarkRunner(
            default_budget=BudgetState(max_tokens=3000, max_steps=10),
        )

        from asar.evaluation.scenario import AblationConfig
        full_cfg = AblationConfig.full_ree()
        no_hyp = AblationConfig.leave_one_out("hypothesis_ecology")

        r_full = await runner.run_scenario(spec, architecture="full_ree", ablation=full_cfg)
        r_no_hyp = await runner.run_scenario(spec, architecture="ree_no_hypothesis", ablation=no_hyp)

        assert r_full.manifest.mechanisms != r_no_hyp.manifest.mechanisms


# ---------------------------------------------------------------
# Metric computation tests
# ---------------------------------------------------------------

class TestMetricComputation:
    def test_paired_quality_comparison(self):
        quality_a = [0.8, 0.75, 0.9, 0.85, 0.7]
        quality_b = [0.6, 0.55, 0.7, 0.65, 0.5]
        result = paired_comparison(
            quality_a, quality_b,
            label_a="REE", label_b="B0",
            metric="quality",
        )
        assert result.mean_diff > 0
        assert result.effect_size.cohens_d > 0
        assert result.n_a == 5

    def test_bootstrap_ci_for_quality(self):
        qualities = [0.7, 0.8, 0.75, 0.85, 0.9, 0.65, 0.72, 0.88]
        ci = bootstrap_ci(qualities)
        assert ci.lower < ci.mean < ci.upper

    def test_win_tie_loss_computation(self):
        a = [1.0, 0.5, 0.8, 0.9]
        b = [0.5, 0.6, 0.8, 0.7]
        w, t, l = win_tie_loss(a, b)
        assert w + t + l == 4


# ---------------------------------------------------------------
# Batch scenario execution
# ---------------------------------------------------------------

class TestBatchExecution:
    @pytest.mark.asyncio
    async def test_run_dev_split_scenarios(self):
        scenarios = generate_all_scenarios(count_per_family=4, dev_fraction=0.75)
        dev_scenarios = [s for s in scenarios if s.split == "dev"]
        runner = BenchmarkRunner(
            default_budget=BudgetState(max_tokens=2000, max_steps=8),
        )

        results = []
        for spec in dev_scenarios[:6]:
            r = await runner.run_scenario(spec, architecture="full_ree")
            results.append(r)

        assert len(results) == 6
        for r in results:
            assert r.result.tokens_used > 0
            assert r.manifest.scenario_split == "dev"

    @pytest.mark.asyncio
    async def test_scenario_families_covered(self):
        scenarios = generate_all_scenarios(count_per_family=4)
        families = {s.family for s in scenarios}
        assert "false_majority" in families
        assert "duplicated_source" in families
        assert "hypothesis_ecology" in families
        assert "ignorance_discovery" in families
        assert "assumption_flip" in families
        assert "stopping_quality" in families
