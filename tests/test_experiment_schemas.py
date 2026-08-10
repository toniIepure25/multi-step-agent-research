"""
Tests for experiment infrastructure schemas — Phase 10B.
"""

import pytest

from schemas.ree.experiment import (
    CognitiveActionOutcome,
    CognitiveActionRegret,
    EpistemicStateFeatures,
    ExperimentManifest,
    MechanismConfig,
    RealizedEpistemicGain,
)


class TestExperimentManifest:
    def test_manifest_creation(self):
        m = ExperimentManifest(
            experiment_id="exp_001",
            architecture="full_ree",
            mechanisms={
                "tribunal": MechanismConfig(enabled=True),
                "ontology_forge": MechanismConfig(enabled=False),
            },
            budget_max_tokens=10_000,
            seed=42,
        )
        assert m.experiment_id == "exp_001"
        assert m.mechanisms["tribunal"].enabled is True
        assert m.mechanisms["ontology_forge"].enabled is False
        assert m.budget_max_tokens == 10_000

    def test_manifest_records_all_config(self):
        m = ExperimentManifest(
            experiment_id="exp_002",
            architecture="ree_no_self_model",
            scheduler_type="heuristic",
            scheduler_weights={"information_gain": 0.4, "cost": 0.3},
            provider="openai",
            model="gpt-4",
            stopping_policy={"min_evidence": 3, "budget_exhaustion_threshold": 0.05},
            memory_regime="federated",
            scenario_split="holdout",
        )
        assert m.scheduler_weights["information_gain"] == 0.4
        assert m.provider == "openai"
        assert m.scenario_split == "holdout"


class TestRealizedEpistemicGain:
    def test_default_scalarization(self):
        gain = RealizedEpistemicGain(
            task_quality_delta=0.5,
            calibration_delta=0.2,
            compute_cost=1.0,
        )
        scalar = gain.scalarize()
        assert scalar > 0

    def test_custom_scalarization(self):
        gain = RealizedEpistemicGain(task_quality_delta=1.0, compute_cost=0.0)
        w1 = {"task_quality_delta": 1.0, "compute_cost": 0.0}
        w2 = {"task_quality_delta": 0.5, "compute_cost": 0.0}
        assert gain.scalarize(w1) > gain.scalarize(w2)

    def test_vector_representation(self):
        gain = RealizedEpistemicGain(task_quality_delta=0.3, calibration_delta=0.1)
        v = gain.to_vector()
        assert len(v) == 8
        assert v[0] == 0.3
        assert v[1] == 0.1


class TestCognitiveActionOutcome:
    def test_outcome_creation(self):
        outcome = CognitiveActionOutcome(
            outcome_id="cao_001",
            episode_id="ep_001",
            step=3,
            state_features=EpistemicStateFeatures(
                hypothesis_entropy=1.5,
                top_hypothesis_margin=0.2,
                budget_fraction=0.7,
            ),
            action_type="retrieve",
            operator_name="retrieve",
            bid_score=0.65,
            realized_gain=RealizedEpistemicGain(task_quality_delta=0.3),
            resource_cost_tokens=500,
        )
        assert outcome.state_features.hypothesis_entropy == 1.5
        assert outcome.scalarized_gain > 0

    def test_state_features_no_outcome_leakage(self):
        feats = EpistemicStateFeatures(
            hypothesis_entropy=1.0,
            step_count=5,
            budget_fraction=0.6,
        )
        assert not hasattr(feats, "final_quality")
        assert not hasattr(feats, "ground_truth")


class TestCognitiveActionRegret:
    def test_regret_computation(self):
        outcomes = {
            "retrieve": RealizedEpistemicGain(task_quality_delta=0.3, compute_cost=0.1),
            "reason": RealizedEpistemicGain(task_quality_delta=0.5, compute_cost=0.2),
            "stop": RealizedEpistemicGain(task_quality_delta=0.0, compute_cost=0.0),
        }
        regret = CognitiveActionRegret.compute(
            fork_state_version=5,
            episode_id="ep_001",
            selected_action="retrieve",
            outcomes=outcomes,
        )
        assert regret.best_action == "reason"
        assert regret.regret >= 0
        assert regret.selected_action == "retrieve"
        assert regret.best_scalar >= regret.selected_scalar

    def test_zero_regret_when_best_selected(self):
        outcomes = {
            "retrieve": RealizedEpistemicGain(task_quality_delta=0.9),
            "reason": RealizedEpistemicGain(task_quality_delta=0.1),
        }
        regret = CognitiveActionRegret.compute(
            fork_state_version=3,
            episode_id="ep_002",
            selected_action="retrieve",
            outcomes=outcomes,
        )
        assert regret.regret == 0.0

    def test_custom_weights_change_regret(self):
        outcomes = {
            "retrieve": RealizedEpistemicGain(task_quality_delta=0.5, compute_cost=2.0),
            "reason": RealizedEpistemicGain(task_quality_delta=0.6, compute_cost=5.0),
        }
        w_quality = {"task_quality_delta": 1.0, "compute_cost": 0.0}
        w_cost = {"task_quality_delta": 1.0, "compute_cost": -1.0}

        r_quality = CognitiveActionRegret.compute(
            fork_state_version=1, episode_id="ep_003",
            selected_action="retrieve", outcomes=outcomes, weights=w_quality,
        )
        r_cost = CognitiveActionRegret.compute(
            fork_state_version=1, episode_id="ep_003",
            selected_action="retrieve", outcomes=outcomes, weights=w_cost,
        )
        assert r_quality.best_action == "reason"
        assert r_cost.best_action == "retrieve"
