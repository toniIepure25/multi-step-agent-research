"""
Phase 13 — Live Validation + Full Ablation + Scientific Findings tests.

Tests ablation campaign, Pareto frontier, prompt-only controls,
hypothesis verdict aggregation, and cross-architecture analysis.
"""

from __future__ import annotations

import pytest

from asar.evaluation.ablation_runner import (
    AblationCampaignResult,
    AblationCampaignRunner,
    AblationResult,
    HypothesisVerdict,
    ParetoPoint,
    PromptOnlyControl,
    aggregate_verdicts,
    build_pareto_data,
    compute_pareto_frontier,
)
from asar.evaluation.benchmark_runner import BenchmarkRunner, BenchmarkRunResult
from asar.evaluation.scenario import AblationConfig, ScenarioResult
from asar.evaluation.scenarios.generators import (
    generate_all_scenarios,
    generate_false_majority,
    generate_hypothesis_ecology,
)
from asar.evaluation.statistical import paired_comparison
from schemas.ree.epistemic_state import BudgetState
from schemas.ree.experiment import ExperimentManifest


# ---------------------------------------------------------------
# Pareto frontier tests
# ---------------------------------------------------------------

class TestParetoFrontier:
    def test_pareto_identifies_optimal_points(self):
        points = [
            ParetoPoint("A", quality=0.9, compute=100),
            ParetoPoint("B", quality=0.7, compute=50),
            ParetoPoint("C", quality=0.5, compute=30),
            ParetoPoint("D", quality=0.6, compute=80),
        ]
        pareto = compute_pareto_frontier(points)
        pareto_archs = {p.architecture for p in pareto}
        assert "C" in pareto_archs
        assert "A" in pareto_archs
        assert "D" not in pareto_archs

    def test_single_point_is_pareto(self):
        points = [ParetoPoint("A", quality=0.8, compute=100)]
        pareto = compute_pareto_frontier(points)
        assert len(pareto) == 1

    def test_build_pareto_data(self):
        results_by_arch = {
            "B0": [_mock_run("B0", tokens=100, hypotheses=0)],
            "REE": [_mock_run("REE", tokens=500, hypotheses=3)],
        }
        data = build_pareto_data(results_by_arch)
        assert len(data) == 2
        pareto_count = sum(1 for p in data if p.is_pareto_optimal)
        assert pareto_count >= 1


# ---------------------------------------------------------------
# Ablation campaign tests
# ---------------------------------------------------------------

class TestAblationCampaign:
    @pytest.mark.asyncio
    async def test_leave_one_out_campaign(self):
        scenarios = [generate_false_majority(seed=42 + i, index=i) for i in range(3)]
        runner = AblationCampaignRunner(
            budget=BudgetState(max_tokens=2000, max_steps=8),
        )
        campaign = await runner.run_leave_one_out(scenarios)

        assert "full_ree" in campaign.conditions
        assert len(campaign.conditions) == 1 + len(AblationConfig.FULL_REE_MECHANISMS)

        for name, result in campaign.conditions.items():
            assert len(result.results) == 3

    @pytest.mark.asyncio
    async def test_additive_campaign(self):
        scenarios = [generate_hypothesis_ecology(seed=42 + i, index=i) for i in range(2)]
        runner = AblationCampaignRunner(
            budget=BudgetState(max_tokens=2000, max_steps=8),
        )
        campaign = await runner.run_additive(scenarios)

        assert "ree_core" in campaign.conditions
        assert len(campaign.conditions) > 1

    @pytest.mark.asyncio
    async def test_campaign_comparisons(self):
        scenarios = [generate_false_majority(seed=42 + i, index=i) for i in range(3)]
        runner = AblationCampaignRunner(
            budget=BudgetState(max_tokens=2000, max_steps=8),
        )
        campaign = await runner.run_leave_one_out(scenarios)

        comparisons = campaign.comparisons(
            baseline="full_ree",
            metric_fn=lambda r: r.result.steps_used,
        )
        assert len(comparisons) > 0
        for comp in comparisons:
            assert "condition" in comp
            assert "effect_size" in comp
            assert "n" in comp


# ---------------------------------------------------------------
# Prompt-only controls tests
# ---------------------------------------------------------------

class TestPromptOnlyControls:
    def test_ignorance_prompt_control(self):
        ctrl = PromptOnlyControl.ignorance_prompt()
        assert ctrl.mechanism == "ignorance_ledger"
        assert len(ctrl.prompt_suffix) > 0

    def test_hypothesis_prompt_control(self):
        ctrl = PromptOnlyControl.hypothesis_prompt()
        assert ctrl.mechanism == "hypothesis_ecology"

    def test_ontology_prompt_control(self):
        ctrl = PromptOnlyControl.ontology_prompt()
        assert ctrl.mechanism == "ontology_forge"

    def test_three_prompt_controls_available(self):
        controls = [
            PromptOnlyControl.ignorance_prompt(),
            PromptOnlyControl.hypothesis_prompt(),
            PromptOnlyControl.ontology_prompt(),
        ]
        assert len(controls) == 3
        mechanisms = {c.mechanism for c in controls}
        assert len(mechanisms) == 3


# ---------------------------------------------------------------
# Hypothesis verdict tests
# ---------------------------------------------------------------

class TestHypothesisVerdicts:
    def test_supported_verdict(self):
        results = {
            "H-REE-04": {
                "claim": "Hypothesis ecology prevents premature convergence",
                "effect_size": 0.8,
                "ci_lower": 0.3,
                "ci_upper": 1.3,
                "n_scenarios": 20,
                "evidence_summary": "Large effect observed",
            },
        }
        verdicts = aggregate_verdicts(results)
        assert len(verdicts) == 1
        assert verdicts[0].status == "SUPPORTED"

    def test_not_supported_verdict(self):
        results = {
            "H-REE-07": {
                "claim": "Counterfactual robustness",
                "effect_size": 0.05,
                "ci_lower": -0.1,
                "ci_upper": 0.2,
                "n_scenarios": 15,
            },
        }
        verdicts = aggregate_verdicts(results)
        assert verdicts[0].status == "NOT_SUPPORTED"

    def test_inconclusive_with_small_n(self):
        results = {
            "H-REE-09": {
                "claim": "Synergy test",
                "effect_size": 0.6,
                "ci_lower": -0.5,
                "ci_upper": 1.7,
                "n_scenarios": 3,
            },
        }
        verdicts = aggregate_verdicts(results)
        assert verdicts[0].status == "INCONCLUSIVE"

    def test_all_hypotheses_get_verdicts(self):
        results = {
            f"H-REE-{i:02d}": {
                "claim": f"Hypothesis {i}",
                "effect_size": 0.5 * (i % 3),
                "n_scenarios": 10 + i,
                "ci_lower": 0.1 if i % 2 == 0 else -0.1,
                "ci_upper": 0.9,
            }
            for i in range(1, 11)
        }
        verdicts = aggregate_verdicts(results)
        assert len(verdicts) == 10
        statuses = {v.status for v in verdicts}
        assert len(statuses) > 1


# ---------------------------------------------------------------
# Cross-architecture statistical analysis
# ---------------------------------------------------------------

class TestCrossArchitectureAnalysis:
    def test_paired_step_comparison(self):
        ree_steps = [5, 6, 4, 7, 5]
        b0_steps = [1, 1, 1, 1, 1]
        result = paired_comparison(
            ree_steps, b0_steps,
            label_a="REE", label_b="B0",
            metric="steps",
        )
        assert result.mean_diff > 0

    def test_quality_compute_data(self):
        results = {
            "B0": [_mock_run("B0", tokens=100, hypotheses=0) for _ in range(5)],
            "B1": [_mock_run("B1", tokens=300, hypotheses=0) for _ in range(5)],
            "REE": [_mock_run("REE", tokens=500, hypotheses=3) for _ in range(5)],
        }
        data = build_pareto_data(results)
        assert len(data) == 3


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------

def _mock_run(
    arch: str,
    tokens: int = 100,
    hypotheses: int = 0,
) -> BenchmarkRunResult:
    return BenchmarkRunResult(
        scenario_id="sc_mock",
        architecture=arch,
        manifest=ExperimentManifest(
            experiment_id="exp_mock",
            architecture=arch,
        ),
        result=ScenarioResult(
            scenario_id="sc_mock",
            architecture=arch,
            experiment_id="exp_mock",
            tokens_used=tokens,
            steps_used=tokens // 100,
            hypotheses=[{"id": f"h{i}"} for i in range(hypotheses)],
        ),
    )
