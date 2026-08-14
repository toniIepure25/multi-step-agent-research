"""
Stage 2 — Experiment Design Worlds.

Each world provides:
- Competing hypotheses with initial beliefs
- Candidate experiments with per-hypothesis outcome predictions
- A ground truth (which hypothesis is correct)
- The oracle-optimal experiment (for regret computation)

Key design principle: worlds where CONFIRMATION and DISCRIMINATION policies DISAGREE.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from asar.scientific_discovery.experiment_design import (
    ExperimentCandidate,
    ExperimentObservation,
    OutcomeLikelihoodByHypothesis,
    compute_discrimination_score,
    compute_oracle_information_gain,
)


@dataclass
class ExperimentWorld:
    """A controlled world for Stage 2 experiment design evaluation."""

    world_id: str
    world_type: str
    description: str
    hypotheses: dict[str, float]  # hypothesis_id → initial belief
    experiments: list[ExperimentCandidate]
    true_hypothesis_id: str
    true_outcomes: dict[str, str]  # experiment_id → true outcome_id


def create_confirmation_discrimination_split(*, seed: int = 1) -> ExperimentWorld:
    """
    World where confirmation-seeking and discrimination policies disagree.

    H1 (leader, 0.60): Drug X works via mechanism A
    H2 (0.30): Drug X works via mechanism B
    H3 (0.10): Drug X is placebo effect

    E_confirm: "Test drug efficacy" — both H1 and H2 predict positive result.
        Confirms leader but doesn't discriminate H1 from H2.
    E_discriminate: "Test mechanism biomarker" — H1 and H2 predict OPPOSITE biomarker levels.
        Less likely to "support" leader specifically but separates hypotheses.

    Truth: H2 is correct.
    """
    h1, h2, h3 = f"cd_h1_{seed}", f"cd_h2_{seed}", f"cd_h3_{seed}"

    e_confirm = ExperimentCandidate(
        experiment_id=f"cd_econf_{seed}",
        description="Standard efficacy trial — does the drug reduce symptoms?",
        cost=1.0,
        possible_outcomes=["positive", "negative"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(
                outcome_id="positive",
                likelihoods={h1: 0.85, h2: 0.80, h3: 0.25},
            ),
            OutcomeLikelihoodByHypothesis(
                outcome_id="negative",
                likelihoods={h1: 0.15, h2: 0.20, h3: 0.75},
            ),
        ],
    )

    e_discriminate = ExperimentCandidate(
        experiment_id=f"cd_edisc_{seed}",
        description="Biomarker assay — which molecular pathway is activated?",
        cost=1.0,
        possible_outcomes=["pathway_a", "pathway_b", "neither"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(
                outcome_id="pathway_a",
                likelihoods={h1: 0.80, h2: 0.10, h3: 0.05},
            ),
            OutcomeLikelihoodByHypothesis(
                outcome_id="pathway_b",
                likelihoods={h1: 0.10, h2: 0.80, h3: 0.05},
            ),
            OutcomeLikelihoodByHypothesis(
                outcome_id="neither",
                likelihoods={h1: 0.10, h2: 0.10, h3: 0.90},
            ),
        ],
    )

    e_cheap = ExperimentCandidate(
        experiment_id=f"cd_echeap_{seed}",
        description="Patient survey — reports subjective improvement",
        cost=0.3,
        possible_outcomes=["improved", "no_change"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(
                outcome_id="improved",
                likelihoods={h1: 0.70, h2: 0.65, h3: 0.40},
            ),
            OutcomeLikelihoodByHypothesis(
                outcome_id="no_change",
                likelihoods={h1: 0.30, h2: 0.35, h3: 0.60},
            ),
        ],
    )

    return ExperimentWorld(
        world_id=f"cd_world_{seed}",
        world_type="confirmation_discrimination_split",
        description="Efficacy trial confirms leader but doesn't discriminate; biomarker separates mechanisms",
        hypotheses={h1: 0.60, h2: 0.30, h3: 0.10},
        experiments=[e_confirm, e_discriminate, e_cheap],
        true_hypothesis_id=h2,
        true_outcomes={
            e_confirm.experiment_id: "positive",
            e_discriminate.experiment_id: "pathway_b",
            e_cheap.experiment_id: "improved",
        },
    )


def create_costly_discrimination(*, seed: int = 1) -> ExperimentWorld:
    """
    World where the discriminative experiment costs more.

    Tests cost-adjusted value. The discriminative experiment is clearly better
    per-information-unit but costs 3× more.
    """
    h1, h2 = f"cost_h1_{seed}", f"cost_h2_{seed}"

    e_cheap_ambig = ExperimentCandidate(
        experiment_id=f"cost_echeap_{seed}",
        description="Quick observational study (low cost, low discrimination)",
        cost=1.0,
        possible_outcomes=["obs_a", "obs_b"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(
                outcome_id="obs_a",
                likelihoods={h1: 0.60, h2: 0.50},
            ),
            OutcomeLikelihoodByHypothesis(
                outcome_id="obs_b",
                likelihoods={h1: 0.40, h2: 0.50},
            ),
        ],
    )

    e_expensive_clear = ExperimentCandidate(
        experiment_id=f"cost_eexp_{seed}",
        description="Randomized controlled trial (high cost, high discrimination)",
        cost=3.0,
        possible_outcomes=["effect", "null"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(
                outcome_id="effect",
                likelihoods={h1: 0.90, h2: 0.10},
            ),
            OutcomeLikelihoodByHypothesis(
                outcome_id="null",
                likelihoods={h1: 0.10, h2: 0.90},
            ),
        ],
    )

    return ExperimentWorld(
        world_id=f"cost_world_{seed}",
        world_type="costly_discrimination",
        description="Cheap experiment is ambiguous; expensive one decisively separates",
        hypotheses={h1: 0.55, h2: 0.45},
        experiments=[e_cheap_ambig, e_expensive_clear],
        true_hypothesis_id=h2,
        true_outcomes={
            e_cheap_ambig.experiment_id: "obs_b",
            e_expensive_clear.experiment_id: "null",
        },
    )


def create_non_identifiable_experiment(*, seed: int = 1) -> ExperimentWorld:
    """
    World where NO available experiment can distinguish H1 from H2.

    Correct behavior: ABSTAIN or report non-identifiability.
    """
    h1, h2 = f"ni_h1_{seed}", f"ni_h2_{seed}"

    e1 = ExperimentCandidate(
        experiment_id=f"ni_e1_{seed}",
        description="Experiment 1 — both hypotheses predict same outcomes",
        cost=1.0,
        possible_outcomes=["result_x", "result_y"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(
                outcome_id="result_x",
                likelihoods={h1: 0.70, h2: 0.70},
            ),
            OutcomeLikelihoodByHypothesis(
                outcome_id="result_y",
                likelihoods={h1: 0.30, h2: 0.30},
            ),
        ],
    )

    e2 = ExperimentCandidate(
        experiment_id=f"ni_e2_{seed}",
        description="Experiment 2 — also non-discriminating",
        cost=2.0,
        possible_outcomes=["result_a", "result_b"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(
                outcome_id="result_a",
                likelihoods={h1: 0.50, h2: 0.50},
            ),
            OutcomeLikelihoodByHypothesis(
                outcome_id="result_b",
                likelihoods={h1: 0.50, h2: 0.50},
            ),
        ],
    )

    return ExperimentWorld(
        world_id=f"ni_world_{seed}",
        world_type="non_identifiable_experiment",
        description="No experiment distinguishes hypotheses",
        hypotheses={h1: 0.50, h2: 0.50},
        experiments=[e1, e2],
        true_hypothesis_id=h1,
        true_outcomes={
            e1.experiment_id: "result_x",
            e2.experiment_id: "result_a",
        },
    )


def create_multiple_rounds(*, seed: int = 1) -> ExperimentWorld:
    """
    World with 4 experiments of varying discrimination.

    Tests whether policy consistently picks highest-discrimination option.
    """
    h1, h2, h3 = f"mr_h1_{seed}", f"mr_h2_{seed}", f"mr_h3_{seed}"

    e_useless = ExperimentCandidate(
        experiment_id=f"mr_euseless_{seed}",
        description="Measures unrelated variable",
        cost=0.5,
        possible_outcomes=["high", "low"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="high", likelihoods={h1: 0.50, h2: 0.50, h3: 0.50}),
            OutcomeLikelihoodByHypothesis(outcome_id="low", likelihoods={h1: 0.50, h2: 0.50, h3: 0.50}),
        ],
    )

    e_weak = ExperimentCandidate(
        experiment_id=f"mr_eweak_{seed}",
        description="Slightly discriminating observation",
        cost=1.0,
        possible_outcomes=["positive", "negative"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="positive", likelihoods={h1: 0.65, h2: 0.45, h3: 0.35}),
            OutcomeLikelihoodByHypothesis(outcome_id="negative", likelihoods={h1: 0.35, h2: 0.55, h3: 0.65}),
        ],
    )

    e_strong = ExperimentCandidate(
        experiment_id=f"mr_estrong_{seed}",
        description="Highly discriminating intervention",
        cost=2.0,
        possible_outcomes=["outcome_a", "outcome_b", "outcome_c"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="outcome_a", likelihoods={h1: 0.80, h2: 0.10, h3: 0.10}),
            OutcomeLikelihoodByHypothesis(outcome_id="outcome_b", likelihoods={h1: 0.10, h2: 0.80, h3: 0.10}),
            OutcomeLikelihoodByHypothesis(outcome_id="outcome_c", likelihoods={h1: 0.10, h2: 0.10, h3: 0.80}),
        ],
    )

    e_confirming = ExperimentCandidate(
        experiment_id=f"mr_econfirm_{seed}",
        description="Likely confirms H1 but doesn't separate from H2",
        cost=1.0,
        possible_outcomes=["confirms", "denies"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="confirms", likelihoods={h1: 0.85, h2: 0.75, h3: 0.20}),
            OutcomeLikelihoodByHypothesis(outcome_id="denies", likelihoods={h1: 0.15, h2: 0.25, h3: 0.80}),
        ],
    )

    return ExperimentWorld(
        world_id=f"mr_world_{seed}",
        world_type="multiple_rounds",
        description="Four experiments of varying discrimination; strong one separates all three hypotheses",
        hypotheses={h1: 0.50, h2: 0.30, h3: 0.20},
        experiments=[e_useless, e_weak, e_strong, e_confirming],
        true_hypothesis_id=h2,
        true_outcomes={
            e_useless.experiment_id: "high",
            e_weak.experiment_id: "negative",
            e_strong.experiment_id: "outcome_b",
            e_confirming.experiment_id: "confirms",
        },
    )
