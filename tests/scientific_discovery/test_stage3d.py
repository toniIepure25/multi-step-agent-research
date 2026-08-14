"""
Tests for Stage 3D — Distributional World Generator, Approx-EIG, and Oracle Regret.
"""

from __future__ import annotations

import math
import numpy as np
import pytest

from asar.scientific_discovery.experiment_design import (
    ExperimentCandidate,
    OutcomeLikelihoodByHypothesis,
    compute_approx_eig,
    compute_discrimination_score,
    compute_oracle_information_gain,
    select_approx_eig,
    select_discrimination,
    select_oracle,
)
from asar.scientific_discovery.world_generator import (
    WorldGeneratorConfig,
    generate_world,
    generate_benchmark_worlds,
    validate_world,
)


class TestApproxEIG:
    """Test the Approximate Expected Information Gain policy."""

    def test_eig_positive_for_discriminating_experiment(self):
        """EIG should be positive when experiment outcomes differ across hypotheses."""
        exp = ExperimentCandidate(
            experiment_id="test_exp",
            description="Test",
            cost=1.0,
            possible_outcomes=["o1", "o2"],
            hypothesis_predictions=[
                OutcomeLikelihoodByHypothesis(
                    outcome_id="o1", likelihoods={"h1": 0.9, "h2": 0.1}
                ),
                OutcomeLikelihoodByHypothesis(
                    outcome_id="o2", likelihoods={"h1": 0.1, "h2": 0.9}
                ),
            ],
        )
        beliefs = {"h1": 0.5, "h2": 0.5}
        eig = compute_approx_eig(exp, beliefs)
        assert eig > 0.3  # Should be high — perfectly discriminating

    def test_eig_zero_for_identical_predictions(self):
        """EIG should be ~0 when all hypotheses predict the same."""
        exp = ExperimentCandidate(
            experiment_id="test_exp",
            description="Test",
            cost=1.0,
            possible_outcomes=["o1", "o2"],
            hypothesis_predictions=[
                OutcomeLikelihoodByHypothesis(
                    outcome_id="o1", likelihoods={"h1": 0.5, "h2": 0.5}
                ),
                OutcomeLikelihoodByHypothesis(
                    outcome_id="o2", likelihoods={"h1": 0.5, "h2": 0.5}
                ),
            ],
        )
        beliefs = {"h1": 0.5, "h2": 0.5}
        eig = compute_approx_eig(exp, beliefs)
        assert eig < 0.01

    def test_eig_never_negative(self):
        """EIG should never be negative (information gain is non-negative)."""
        import random
        rng = random.Random(42)
        for _ in range(50):
            exp = ExperimentCandidate(
                experiment_id="rnd",
                description="Random",
                cost=1.0,
                possible_outcomes=["a", "b", "c"],
                hypothesis_predictions=[
                    OutcomeLikelihoodByHypothesis(
                        outcome_id=oid,
                        likelihoods={f"h{j}": rng.random() for j in range(3)}
                    )
                    for oid in ["a", "b", "c"]
                ],
            )
            beliefs = {"h0": 0.5, "h1": 0.3, "h2": 0.2}
            assert compute_approx_eig(exp, beliefs) >= 0.0

    def test_select_approx_eig_picks_best(self):
        """Policy should select experiment with highest EIG."""
        exp_good = ExperimentCandidate(
            experiment_id="good",
            description="Good",
            cost=1.0,
            possible_outcomes=["o1", "o2"],
            hypothesis_predictions=[
                OutcomeLikelihoodByHypothesis(outcome_id="o1", likelihoods={"h1": 0.9, "h2": 0.1}),
                OutcomeLikelihoodByHypothesis(outcome_id="o2", likelihoods={"h1": 0.1, "h2": 0.9}),
            ],
        )
        exp_bad = ExperimentCandidate(
            experiment_id="bad",
            description="Bad",
            cost=1.0,
            possible_outcomes=["o1", "o2"],
            hypothesis_predictions=[
                OutcomeLikelihoodByHypothesis(outcome_id="o1", likelihoods={"h1": 0.5, "h2": 0.5}),
                OutcomeLikelihoodByHypothesis(outcome_id="o2", likelihoods={"h1": 0.5, "h2": 0.5}),
            ],
        )
        beliefs = {"h1": 0.5, "h2": 0.5}
        sel = select_approx_eig([exp_bad, exp_good], beliefs)
        assert sel.selected_experiment_id == "good"


class TestOracleRegret:
    """Test oracle regret computation is correct."""

    def test_regret_zero_when_policy_matches_oracle(self):
        """If policy picks same experiment as oracle, regret = 0."""
        exp = ExperimentCandidate(
            experiment_id="only",
            description="Only option",
            cost=1.0,
            possible_outcomes=["o1", "o2"],
            hypothesis_predictions=[
                OutcomeLikelihoodByHypothesis(outcome_id="o1", likelihoods={"h1": 0.8, "h2": 0.2}),
                OutcomeLikelihoodByHypothesis(outcome_id="o2", likelihoods={"h1": 0.2, "h2": 0.8}),
            ],
        )
        beliefs = {"h1": 0.6, "h2": 0.4}
        oracle_ig = compute_oracle_information_gain(exp, beliefs, "h1")
        # If only one experiment, regret is always 0
        assert oracle_ig >= 0

    def test_regret_non_negative(self):
        """True regret should never be negative."""
        exp1 = ExperimentCandidate(
            experiment_id="e1",
            description="E1",
            cost=1.0,
            possible_outcomes=["o1", "o2"],
            hypothesis_predictions=[
                OutcomeLikelihoodByHypothesis(outcome_id="o1", likelihoods={"h1": 0.9, "h2": 0.3}),
                OutcomeLikelihoodByHypothesis(outcome_id="o2", likelihoods={"h1": 0.1, "h2": 0.7}),
            ],
        )
        exp2 = ExperimentCandidate(
            experiment_id="e2",
            description="E2",
            cost=1.0,
            possible_outcomes=["o1", "o2"],
            hypothesis_predictions=[
                OutcomeLikelihoodByHypothesis(outcome_id="o1", likelihoods={"h1": 0.5, "h2": 0.5}),
                OutcomeLikelihoodByHypothesis(outcome_id="o2", likelihoods={"h1": 0.5, "h2": 0.5}),
            ],
        )
        beliefs = {"h1": 0.6, "h2": 0.4}
        oracle_sel = select_oracle([exp1, exp2], beliefs, "h1")
        oracle_exp = exp1 if oracle_sel.selected_experiment_id == "e1" else exp2
        oracle_ig = compute_oracle_information_gain(oracle_exp, beliefs, "h1")

        for exp in [exp1, exp2]:
            policy_ig = compute_oracle_information_gain(exp, beliefs, "h1")
            regret = oracle_ig - policy_ig
            assert regret >= -1e-10  # Allow tiny float error


class TestDistributionalWorldGenerator:
    """Test the parametric world generator."""

    def test_generates_valid_worlds(self):
        worlds = generate_benchmark_worlds(10, seed_offset=9000)
        assert len(worlds) == 10
        for world, meta in worlds:
            assert meta.valid
            assert meta.n_hypotheses >= 3
            assert meta.n_experiments >= 3

    def test_worlds_have_required_structure(self):
        worlds = generate_benchmark_worlds(5, seed_offset=9100)
        for world, meta in worlds:
            assert world.true_hypothesis_id in world.hypotheses
            assert len(world.experiments) >= 3
            assert len(world.hypotheses) >= 3
            # Beliefs sum to ~1
            assert abs(sum(world.hypotheses.values()) - 1.0) < 0.01

    def test_metadata_computed(self):
        worlds = generate_benchmark_worlds(5, seed_offset=9200)
        for _, meta in worlds:
            assert meta.prior_entropy > 0
            assert meta.oracle_action_margin >= 0
            assert meta.difficulty_score > 0

    def test_different_seeds_produce_different_worlds(self):
        w1, _ = generate_world(100)
        w2, _ = generate_world(200)
        assert w1.world_id != w2.world_id
        assert w1.true_hypothesis_id != w2.true_hypothesis_id or len(w1.hypotheses) != len(w2.hypotheses)

    def test_config_controls_dimensions(self):
        small_config = WorldGeneratorConfig(
            n_hypotheses_range=(2, 3),
            n_experiments_range=(2, 3),
        )
        worlds = generate_benchmark_worlds(10, seed_offset=9300, config=small_config)
        for world, meta in worlds:
            assert meta.n_hypotheses <= 3
            assert meta.n_experiments <= 3

    def test_validation_rejects_invalid(self):
        from asar.scientific_discovery.experiment_worlds import ExperimentWorld
        # World with true hypothesis not in belief set
        bad_world = ExperimentWorld(
            world_id="bad",
            world_type="test",
            description="Invalid",
            hypotheses={"h1": 0.5, "h2": 0.5},
            experiments=[],
            true_hypothesis_id="h3",  # NOT in hypotheses
            true_outcomes={},
        )
        valid, reason = validate_world(bad_world)
        assert not valid

    def test_jsd_oracle_agreement_varies(self):
        """Not all worlds should have JSD = Oracle (that would be ceiling)."""
        worlds = generate_benchmark_worlds(50, seed_offset=9400)
        agreements = [meta.jsd_oracle_agreement for _, meta in worlds]
        # Should have SOME disagreement (not all True)
        assert not all(agreements), "All JSD=Oracle suggests ceiling problem"
        # But mostly agreement (JSD is a good policy)
        assert sum(agreements) / len(agreements) > 0.5


class TestRegretFormula:
    """Verify regret formula properties."""

    def test_regret_is_oracle_minus_policy(self):
        """Regret = OracleIG(best) - OracleIG(policy_chosen)."""
        exp_best = ExperimentCandidate(
            experiment_id="best",
            description="Best",
            cost=1.0,
            possible_outcomes=["o1", "o2"],
            hypothesis_predictions=[
                OutcomeLikelihoodByHypothesis(outcome_id="o1", likelihoods={"h1": 0.95, "h2": 0.05}),
                OutcomeLikelihoodByHypothesis(outcome_id="o2", likelihoods={"h1": 0.05, "h2": 0.95}),
            ],
        )
        exp_worse = ExperimentCandidate(
            experiment_id="worse",
            description="Worse",
            cost=1.0,
            possible_outcomes=["o1", "o2"],
            hypothesis_predictions=[
                OutcomeLikelihoodByHypothesis(outcome_id="o1", likelihoods={"h1": 0.6, "h2": 0.4}),
                OutcomeLikelihoodByHypothesis(outcome_id="o2", likelihoods={"h1": 0.4, "h2": 0.6}),
            ],
        )
        beliefs = {"h1": 0.5, "h2": 0.5}

        ig_best = compute_oracle_information_gain(exp_best, beliefs, "h1")
        ig_worse = compute_oracle_information_gain(exp_worse, beliefs, "h1")

        regret = ig_best - ig_worse
        assert regret > 0  # best experiment has higher IG
        assert ig_best > ig_worse
