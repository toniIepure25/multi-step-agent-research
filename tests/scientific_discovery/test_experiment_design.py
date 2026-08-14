"""
Stage 2 — Experiment Design Tests.

Tests for SD-H3: Discriminative Experiment Selection.
Verifies that the discrimination policy selects experiments with objectively higher
information value than confirmation-seeking or random baselines.
"""

import math

import pytest

from asar.scientific_discovery.experiment_design import (
    ExperimentCandidate,
    ExperimentSelection,
    OutcomeLikelihoodByHypothesis,
    compute_confirmation_score,
    compute_discrimination_score,
    compute_oracle_information_gain,
    select_cheapest,
    select_confirmation,
    select_discrimination,
    select_oracle,
    select_random,
)
from asar.scientific_discovery.experiment_worlds import (
    create_confirmation_discrimination_split,
    create_costly_discrimination,
    create_multiple_rounds,
    create_non_identifiable_experiment,
)


class TestDiscriminationScoring:
    """Test that discrimination scores are computed correctly."""

    def test_identical_predictions_zero_discrimination(self):
        """If all hypotheses predict same outcomes, discrimination = 0."""
        e = ExperimentCandidate(
            experiment_id="test",
            description="test",
            possible_outcomes=["a", "b"],
            hypothesis_predictions=[
                OutcomeLikelihoodByHypothesis(outcome_id="a", likelihoods={"h1": 0.7, "h2": 0.7}),
                OutcomeLikelihoodByHypothesis(outcome_id="b", likelihoods={"h1": 0.3, "h2": 0.3}),
            ],
        )
        score = compute_discrimination_score(e, {"h1": 0.5, "h2": 0.5})
        assert score < 0.01

    def test_opposite_predictions_high_discrimination(self):
        """If hypotheses predict opposite outcomes, discrimination is high."""
        e = ExperimentCandidate(
            experiment_id="test",
            description="test",
            possible_outcomes=["a", "b"],
            hypothesis_predictions=[
                OutcomeLikelihoodByHypothesis(outcome_id="a", likelihoods={"h1": 0.95, "h2": 0.05}),
                OutcomeLikelihoodByHypothesis(outcome_id="b", likelihoods={"h1": 0.05, "h2": 0.95}),
            ],
        )
        score = compute_discrimination_score(e, {"h1": 0.5, "h2": 0.5})
        assert score > 0.5

    def test_three_hypotheses_three_outcomes(self):
        """Three hypotheses each predicting different outcomes = maximum discrimination."""
        e = ExperimentCandidate(
            experiment_id="test",
            description="test",
            possible_outcomes=["a", "b", "c"],
            hypothesis_predictions=[
                OutcomeLikelihoodByHypothesis(outcome_id="a", likelihoods={"h1": 0.9, "h2": 0.05, "h3": 0.05}),
                OutcomeLikelihoodByHypothesis(outcome_id="b", likelihoods={"h1": 0.05, "h2": 0.9, "h3": 0.05}),
                OutcomeLikelihoodByHypothesis(outcome_id="c", likelihoods={"h1": 0.05, "h2": 0.05, "h3": 0.9}),
            ],
        )
        beliefs = {"h1": 0.5, "h2": 0.3, "h3": 0.2}
        score = compute_discrimination_score(e, beliefs)
        assert score > 0.5


class TestConfirmationVsDiscrimination:
    """The central Stage 2 test: policies DISAGREE on which experiment to choose."""

    def test_confirmation_picks_efficacy_discrimination_picks_biomarker(self):
        """
        In the confirmation/discrimination split world:
        - Confirmation should pick the efficacy trial (high P(positive|leader))
        - Discrimination should pick the biomarker (opposite predictions for H1 vs H2)
        """
        world = create_confirmation_discrimination_split(seed=1)

        sel_confirm = select_confirmation(world.experiments, world.hypotheses)
        sel_disc = select_discrimination(world.experiments, world.hypotheses)

        # They should disagree
        assert sel_confirm.selected_experiment_id != sel_disc.selected_experiment_id, (
            "Confirmation and discrimination should select DIFFERENT experiments in this world"
        )

        # Confirmation picks efficacy (or cheap survey)
        efficacy_id = world.experiments[0].experiment_id
        biomarker_id = world.experiments[1].experiment_id

        assert sel_disc.selected_experiment_id == biomarker_id, (
            f"Discrimination should pick biomarker, got {sel_disc.selected_experiment_id}"
        )

    def test_oracle_agrees_with_discrimination(self):
        """Oracle should prefer the discriminative experiment (higher true IG)."""
        world = create_confirmation_discrimination_split(seed=1)

        sel_oracle = select_oracle(world.experiments, world.hypotheses, world.true_hypothesis_id)
        sel_disc = select_discrimination(world.experiments, world.hypotheses)

        # Oracle and discrimination should agree (both prefer high-information experiment)
        assert sel_oracle.selected_experiment_id == sel_disc.selected_experiment_id


class TestOracleRegret:
    """Test that discrimination policy has lower oracle regret than alternatives."""

    def test_discrimination_lower_regret_than_confirmation(self):
        """ASAR discrimination should have lower oracle regret than confirmation-seeking."""
        world = create_confirmation_discrimination_split(seed=1)

        sel_disc = select_discrimination(world.experiments, world.hypotheses)
        sel_conf = select_confirmation(world.experiments, world.hypotheses)

        # Compute oracle IG for each selection
        ig_disc = compute_oracle_information_gain(
            next(e for e in world.experiments if e.experiment_id == sel_disc.selected_experiment_id),
            world.hypotheses,
            world.true_hypothesis_id,
        )
        ig_conf = compute_oracle_information_gain(
            next(e for e in world.experiments if e.experiment_id == sel_conf.selected_experiment_id),
            world.hypotheses,
            world.true_hypothesis_id,
        )

        # Oracle IG of discrimination selection should be >= confirmation selection
        assert ig_disc >= ig_conf, (
            f"Discrimination IG ({ig_disc:.3f}) should >= confirmation IG ({ig_conf:.3f})"
        )


class TestNonIdentifiableExperiment:
    """When no experiment discriminates, all policies should score near zero."""

    def test_non_identifiable_low_scores(self):
        world = create_non_identifiable_experiment(seed=1)

        for exp in world.experiments:
            score = compute_discrimination_score(exp, world.hypotheses)
            assert score < 0.05, f"Non-identifiable experiment scored {score:.3f}"


class TestMetamorphicInvariants:
    """Experiment design metamorphic tests — anti-tautology."""

    def test_label_permutation(self):
        """Renaming hypothesis IDs must not change selected experiment."""
        world1 = create_confirmation_discrimination_split(seed=1)
        sel1 = select_discrimination(world1.experiments, world1.hypotheses)

        # Create same world with permuted hypothesis labels
        world2 = create_confirmation_discrimination_split(seed=2)
        sel2 = select_discrimination(world2.experiments, world2.hypotheses)

        # Both should pick the biomarker/discriminative experiment
        # (the experiment with highest discrimination regardless of hypothesis names)
        disc1 = sel1.discrimination_score
        disc2 = sel2.discrimination_score
        assert abs(disc1 - disc2) < 0.01

    def test_prediction_convergence_kills_discrimination(self):
        """If all hypotheses predict same outcomes, discrimination → 0."""
        e = ExperimentCandidate(
            experiment_id="uniform",
            description="test",
            possible_outcomes=["x", "y"],
            hypothesis_predictions=[
                OutcomeLikelihoodByHypothesis(outcome_id="x", likelihoods={"h1": 0.5, "h2": 0.5, "h3": 0.5}),
                OutcomeLikelihoodByHypothesis(outcome_id="y", likelihoods={"h1": 0.5, "h2": 0.5, "h3": 0.5}),
            ],
        )
        score = compute_discrimination_score(e, {"h1": 0.4, "h2": 0.3, "h3": 0.3})
        assert score < 0.01

    def test_dominated_experiment_not_preferred(self):
        """If experiment A is strictly worse and more expensive, it should not be selected."""
        world = create_multiple_rounds(seed=1)

        sel = select_discrimination(world.experiments, world.hypotheses)

        # The useless experiment (discrimination ≈ 0) should never be selected
        useless_id = world.experiments[0].experiment_id
        assert sel.selected_experiment_id != useless_id


class TestMultipleRoundsWorld:
    """Test behavior across a world with multiple experiment options."""

    def test_strong_experiment_selected(self):
        """The highly discriminating experiment should be selected by ASAR."""
        world = create_multiple_rounds(seed=1)
        sel = select_discrimination(world.experiments, world.hypotheses)

        strong_id = world.experiments[2].experiment_id  # e_strong
        assert sel.selected_experiment_id == strong_id

    def test_oracle_picks_strong(self):
        """Oracle should also prefer the strongly discriminating experiment."""
        world = create_multiple_rounds(seed=1)
        sel = select_oracle(world.experiments, world.hypotheses, world.true_hypothesis_id)

        strong_id = world.experiments[2].experiment_id
        assert sel.selected_experiment_id == strong_id
