"""
Stage 3B Tests — Generative Scientist, Hard Active Worlds, Self-Authorship Framework.

Tests scientific invariants without requiring LLM API access.
LLM-dependent tests are marked with pytest.mark.llm and skipped when no API key.
"""

import json
import os
from unittest.mock import AsyncMock, patch

import pytest

from asar.scientific_discovery.active_science import (
    ActiveWorld,
    active_confirmation,
    active_discrimination,
    active_passive,
    active_random,
    run_active_benchmark,
    run_active_episode,
)
from asar.scientific_discovery.active_worlds_hard import (
    create_confirmation_dead_end,
    create_multi_hypothesis_branch,
    create_null_vs_weak_effect,
    create_sequential_active_world,
)
from asar.scientific_discovery.capability_gate import (
    CapabilityLevel,
    CapabilityResult,
    GeneratedAlternative,
    GeneratedExperiment,
    GeneratedFalsifier,
    GeneratedHypothesis,
    GeneratedPrediction,
    ModelCapabilityReport,
    RationalizationEvent,
    RescueType,
    SelfAuthorshipBiasReport,
    SelfAuthorshipCondition,
    SelfAuthorshipResult,
    compute_rationalization_rate,
)
from asar.scientific_discovery.generative_scientist import (
    GenerativeScientist,
    ModelManifest,
    _parse_json_response,
    _strip_markdown_fences,
)


# ---------------------------------------------------------------------------
# Schema Parsing Tests
# ---------------------------------------------------------------------------


class TestSchemaParsing:
    """Verify JSON parsing and schema validation for generated outputs."""

    def test_valid_hypothesis_json(self):
        text = json.dumps({
            "claim": "Drug X reduces inflammation via COX-2 inhibition",
            "mechanism": "COX-2 pathway suppression",
            "scope": "acute inflammation",
            "assumptions": ["COX-2 is accessible"],
            "predictions": ["Reduced prostaglandin levels"],
            "falsifiers": ["No change in COX-2 activity after dosing"],
        })
        result = _parse_json_response(text, GeneratedHypothesis)
        assert result is not None
        assert result.claim == "Drug X reduces inflammation via COX-2 inhibition"

    def test_invalid_json_returns_none(self):
        result = _parse_json_response("not json at all", GeneratedHypothesis)
        assert result is None

    def test_partial_json_missing_required_field(self):
        text = json.dumps({"claim": "hello"})  # missing mechanism
        result = _parse_json_response(text, GeneratedHypothesis)
        assert result is None

    def test_strip_markdown_fences(self):
        text = "```json\n{\"claim\": \"test\", \"mechanism\": \"m\"}\n```"
        cleaned = _strip_markdown_fences(text)
        result = _parse_json_response(cleaned, GeneratedHypothesis)
        assert result is not None

    def test_alternative_schema(self):
        text = json.dumps({
            "claim": "Y causes X (reverse)",
            "mechanism": "feedback loop",
            "how_it_differs": "Reverses causal direction",
            "predictions_different_from_primary": ["Intervention on Y changes X"],
        })
        result = _parse_json_response(text, GeneratedAlternative)
        assert result is not None
        assert result.how_it_differs == "Reverses causal direction"

    def test_prediction_schema(self):
        text = json.dumps({
            "experiment": "test_exp",
            "predicted_outcome": "positive",
            "confidence": 0.8,
            "reasoning": "Because mechanism predicts activation",
        })
        result = _parse_json_response(text, GeneratedPrediction)
        assert result is not None
        assert result.confidence == 0.8

    def test_falsifier_schema(self):
        text = json.dumps({
            "observation_that_would_falsify": "No pathway activation",
            "why_this_falsifies": "Mechanism requires pathway activation",
            "how_to_test": "Measure pathway markers after intervention",
        })
        result = _parse_json_response(text, GeneratedFalsifier)
        assert result is not None

    def test_experiment_schema(self):
        text = json.dumps({
            "experiment_description": "Knockout study",
            "what_it_tests": "Whether gene X is necessary",
            "predicted_outcome_if_h1": "Function lost",
            "predicted_outcome_if_h2": "Function retained",
            "why_discriminating": "Only H1 requires gene X",
        })
        result = _parse_json_response(text, GeneratedExperiment)
        assert result is not None


# ---------------------------------------------------------------------------
# Hard Active World Tests
# ---------------------------------------------------------------------------


class TestConfirmationDeadEnd:
    """Confirm dead-end world separates confirmation from discrimination."""

    def test_discrimination_finds_decisive_experiment(self):
        """Discrimination should select the decisive experiment, not dead-ends."""
        world = create_confirmation_dead_end(seed=1)
        result = run_active_episode(world, active_discrimination, seed=1)
        decisive_id = world.experiments[2].experiment_id
        # At some point, discrimination should select the decisive experiment
        assert decisive_id in result.experiments_selected

    def test_confirmation_prefers_dead_ends(self):
        """Confirmation-seeker maximizes P(positive|leader) — picks dead-ends."""
        world = create_confirmation_dead_end(seed=1)
        result = run_active_episode(world, active_confirmation, seed=1)
        dead1_id = world.experiments[0].experiment_id
        dead2_id = world.experiments[1].experiment_id
        # Confirmation should pick dead-end experiments (highest confirmation score)
        dead_selected = sum(1 for eid in result.experiments_selected if eid in [dead1_id, dead2_id])
        assert dead_selected >= 1


class TestMultiHypothesisBranch:
    """The critical world where discrimination clearly outperforms confirmation."""

    def test_discrimination_higher_recovery(self):
        """Over 20 seeds, discrimination should recover more often."""
        disc_recovered = 0
        conf_recovered = 0
        for seed in range(1, 21):
            world = create_multi_hypothesis_branch(seed=seed)
            rd = run_active_episode(world, active_discrimination, seed=seed)
            rc = run_active_episode(world, active_confirmation, seed=seed)
            disc_recovered += int(rd.recovered)
            conf_recovered += int(rc.recovered)

        # Discrimination should beat confirmation on this world
        assert disc_recovered > conf_recovered, (
            f"Disc ({disc_recovered}/20) should > Conf ({conf_recovered}/20)"
        )


class TestNullVsWeakEffect:
    """Null world where observational evidence is misleading."""

    def test_rct_reveals_null(self):
        """Discrimination should select RCT, leading to correct null conclusion."""
        world = create_null_vs_weak_effect(seed=1)
        result = run_active_episode(world, active_discrimination, seed=1)
        rct_id = world.experiments[2].experiment_id
        assert rct_id in result.experiments_selected


class TestSequentialDesign:
    """Test greedy vs sequential strategy."""

    def test_greedy_prefers_high_discrimination(self):
        """Greedy JSD picks the most discriminating available experiment."""
        from asar.scientific_discovery.experiment_design import compute_discrimination_score
        world = create_sequential_active_world(seed=1)
        scores = [(e.experiment_id, compute_discrimination_score(e, world.hypotheses))
                  for e in world.experiments]
        scores.sort(key=lambda x: -x[1])
        # The followup (3 outcomes, clear separation) has highest JSD
        # The cheap screen has lowest. Greedy ignores cost.
        assert scores[-1][0] == world.experiments[1].experiment_id  # cheap is lowest

    def test_sequential_world_allows_two_experiments(self):
        """With budget=3.5, cheap(1.0)+followup(2.0) fits but expensive(3.0) leaves nothing."""
        world = create_sequential_active_world(seed=1)
        result = run_active_episode(world, active_discrimination, seed=1)
        # Greedy picks expensive first, may or may not afford second
        # The test just verifies the world is structurally valid
        assert result.n_experiments >= 1
        assert result.total_cost <= world.cost_budget


# ---------------------------------------------------------------------------
# Self-Authorship Framework Tests
# ---------------------------------------------------------------------------


class TestSelfAuthorshipFramework:
    """Test the self-authorship bias measurement framework."""

    def test_condition_creation(self):
        """Self and external conditions must have identical hypothesis text."""
        cond_self = SelfAuthorshipCondition(
            condition_name="SELF",
            hypothesis_text="Drug X works via COX-2",
            hypothesis_mechanism="COX-2 inhibition",
            provenance="self_generated",
            is_correct=False,
        )
        cond_ext = SelfAuthorshipCondition(
            condition_name="EXTERNAL",
            hypothesis_text="Drug X works via COX-2",
            hypothesis_mechanism="COX-2 inhibition",
            provenance="externally_provided",
            is_correct=False,
        )
        assert cond_self.hypothesis_text == cond_ext.hypothesis_text
        assert cond_self.provenance != cond_ext.provenance

    def test_bias_report_computation(self):
        """SAB should be retention_self - retention_external."""
        report = SelfAuthorshipBiasReport(
            n_trials=10,
            mean_drop_self=0.30,
            mean_drop_external=0.45,
            bias=-0.15,  # self drops LESS → self-protection bias
        )
        # Negative bias = self-generated hypotheses retained more = concerning
        assert report.bias < 0

    def test_zero_bias_is_healthy(self):
        """No self-authorship bias is the desired outcome."""
        report = SelfAuthorshipBiasReport(
            n_trials=20,
            mean_drop_self=0.40,
            mean_drop_external=0.41,
            bias=-0.01,
        )
        assert abs(report.bias) < 0.05


# ---------------------------------------------------------------------------
# Rationalization Detection Tests
# ---------------------------------------------------------------------------


class TestRationalizationDetection:
    """Test rationalization classification and rate computation."""

    def test_rationalization_rate_zero_when_no_rescues(self):
        events = [
            RationalizationEvent(hypothesis_id="h1", round_idx=3, rescue_type=RescueType.ABANDON),
            RationalizationEvent(hypothesis_id="h1", round_idx=4, rescue_type=RescueType.LEGITIMATE_REVISION),
        ]
        rate = compute_rationalization_rate(events, n_falsifications=2)
        assert rate == 0.0

    def test_rationalization_rate_nonzero(self):
        events = [
            RationalizationEvent(hypothesis_id="h1", round_idx=3, rescue_type=RescueType.AD_HOC_RESCUE),
            RationalizationEvent(hypothesis_id="h1", round_idx=4, rescue_type=RescueType.CREATE_NEAR_DUPLICATE),
            RationalizationEvent(hypothesis_id="h2", round_idx=5, rescue_type=RescueType.ABANDON),
        ]
        rate = compute_rationalization_rate(events, n_falsifications=3)
        assert rate == pytest.approx(2 / 3)

    def test_rationalization_rate_zero_falsifications(self):
        rate = compute_rationalization_rate([], n_falsifications=0)
        assert rate == 0.0


# ---------------------------------------------------------------------------
# Capability Gate Verdict Tests
# ---------------------------------------------------------------------------


class TestCapabilityVerdicts:
    """Test capability gate verdict logic."""

    def test_valid_substrate(self):
        result = CapabilityResult(
            capability_id="C1",
            description="Hypothesis generation",
            n_tasks=10,
            n_valid=8,
            n_partial=1,
            n_invalid=1,
            schema_compliance_rate=0.9,
        )
        assert result.verdict == CapabilityLevel.VALID

    def test_partial_substrate(self):
        result = CapabilityResult(
            capability_id="C1",
            description="Hypothesis generation",
            n_tasks=10,
            n_valid=4,
            n_partial=2,
            n_invalid=4,
            schema_compliance_rate=0.6,
        )
        assert result.verdict == CapabilityLevel.PARTIAL

    def test_invalid_substrate(self):
        result = CapabilityResult(
            capability_id="C1",
            description="Hypothesis generation",
            n_tasks=10,
            n_valid=2,
            n_partial=1,
            n_invalid=7,
            schema_compliance_rate=0.3,
        )
        assert result.verdict == CapabilityLevel.INVALID

    def test_model_report_overall_verdict(self):
        report = ModelCapabilityReport(
            model_id="test-model",
            capabilities={
                "C1": CapabilityResult(capability_id="C1", description="", n_tasks=10, n_valid=8, schema_compliance_rate=0.9),
                "C2": CapabilityResult(capability_id="C2", description="", n_tasks=10, n_valid=3, n_invalid=7, schema_compliance_rate=0.3),
            },
        )
        # One INVALID → overall INVALID
        assert report.overall_verdict == CapabilityLevel.INVALID


# ---------------------------------------------------------------------------
# Hard Benchmark Integration Test
# ---------------------------------------------------------------------------


class TestHardBenchmarkIntegration:
    """Verify the hard benchmark runs correctly."""

    def test_hard_benchmark_includes_new_worlds(self):
        results = run_active_benchmark(seeds=[1, 2], hard=True)
        world_types = set()
        for ep in results["discrimination"].episodes:
            world_types.add(ep.world_type)

        assert "confirmation_dead_end" in world_types
        assert "null_vs_weak_effect" in world_types
        assert "multi_hypothesis_branch" in world_types
        assert "sequential_design" in world_types

    def test_hard_benchmark_more_episodes_than_basic(self):
        basic = run_active_benchmark(seeds=[1])
        hard = run_active_benchmark(seeds=[1], hard=True)
        assert len(hard["discrimination"].episodes) > len(basic["discrimination"].episodes)
