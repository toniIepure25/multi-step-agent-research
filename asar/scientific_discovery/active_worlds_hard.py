"""
Hard Active Worlds — designed so confirmation and discrimination genuinely diverge.

These worlds satisfy Phase 26 requirements:
- Confirmation dead-end: repeated confirmation provides zero information gain
- Rare discriminator: most experiments are uninformative; one rare test is decisive
- Costly decisive test: cheap evidence accumulates slowly; expensive test resolves
- Multi-hypothesis branch: different experiments partition hypothesis space differently
- Null vs weak effect: confirmation reinforces false positive; discrimination reveals null

In each: B0 recovery < 0.8, confirmation < discrimination (by construction).
"""

from __future__ import annotations

import random

from asar.scientific_discovery.active_science import ActiveWorld
from asar.scientific_discovery.experiment_design import (
    ExperimentCandidate,
    OutcomeLikelihoodByHypothesis,
)


def create_confirmation_dead_end(*, seed: int = 1) -> ActiveWorld:
    """
    Confirmation experiments yield outcomes predicted equally by H1 and H2.
    Only a costly specific intervention separates them.
    Confirmation-seeking wastes all budget on dead-end experiments.
    """
    h1, h2, h3 = f"cde_h1_{seed}", f"cde_h2_{seed}", f"cde_h3_{seed}"

    # Dead-end: both H1 and H2 predict the same outcome strongly
    e_dead1 = ExperimentCandidate(
        experiment_id=f"cde_edead1_{seed}",
        description="Symptom observation (H1≈H2 predict same)",
        cost=1.0,
        possible_outcomes=["present", "absent"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="present", likelihoods={h1: 0.80, h2: 0.78, h3: 0.20}),
            OutcomeLikelihoodByHypothesis(outcome_id="absent", likelihoods={h1: 0.20, h2: 0.22, h3: 0.80}),
        ],
    )

    e_dead2 = ExperimentCandidate(
        experiment_id=f"cde_edead2_{seed}",
        description="Magnitude test (again H1≈H2)",
        cost=1.0,
        possible_outcomes=["high", "low"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="high", likelihoods={h1: 0.75, h2: 0.72, h3: 0.30}),
            OutcomeLikelihoodByHypothesis(outcome_id="low", likelihoods={h1: 0.25, h2: 0.28, h3: 0.70}),
        ],
    )

    # The ONLY discriminating experiment
    e_decisive = ExperimentCandidate(
        experiment_id=f"cde_edecisive_{seed}",
        description="Mechanistic intervention (H1 vs H2 opposite predictions)",
        cost=2.5,
        possible_outcomes=["response_a", "response_b", "no_response"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="response_a", likelihoods={h1: 0.85, h2: 0.05, h3: 0.10}),
            OutcomeLikelihoodByHypothesis(outcome_id="response_b", likelihoods={h1: 0.05, h2: 0.85, h3: 0.10}),
            OutcomeLikelihoodByHypothesis(outcome_id="no_response", likelihoods={h1: 0.10, h2: 0.10, h3: 0.80}),
        ],
    )

    return ActiveWorld(
        world_id=f"conf_dead_end_{seed}",
        world_type="confirmation_dead_end",
        description="Cheap experiments confirm leader but provide zero discrimination between H1/H2",
        hypotheses={h1: 0.50, h2: 0.35, h3: 0.15},
        true_hypothesis_id=h2,
        experiments=[e_dead1, e_dead2, e_decisive],
        experiment_budget=3,
        cost_budget=4.0,
    )


def create_null_vs_weak_effect(*, seed: int = 1) -> ActiveWorld:
    """
    Confirmation evidence supports a spurious weak effect.
    Discriminative controlled experiment reveals null.
    Confirmation-seekers reinforce the false positive.
    """
    h_real, h_artifact, h_null = f"nw_hreal_{seed}", f"nw_hart_{seed}", f"nw_hnull_{seed}"

    # Cheap observational: appears to support h_real (the wrong one)
    e_observational = ExperimentCandidate(
        experiment_id=f"nw_eobs_{seed}",
        description="Observational study (selection bias likely)",
        cost=0.5,
        possible_outcomes=["effect_seen", "no_effect"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="effect_seen", likelihoods={h_real: 0.80, h_artifact: 0.65, h_null: 0.35}),
            OutcomeLikelihoodByHypothesis(outcome_id="no_effect", likelihoods={h_real: 0.20, h_artifact: 0.35, h_null: 0.65}),
        ],
    )

    # Confirmation: another observational study
    e_confirm = ExperimentCandidate(
        experiment_id=f"nw_econfirm_{seed}",
        description="Correlated measurement (confirms leader)",
        cost=0.5,
        possible_outcomes=["positive", "negative"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="positive", likelihoods={h_real: 0.75, h_artifact: 0.60, h_null: 0.30}),
            OutcomeLikelihoodByHypothesis(outcome_id="negative", likelihoods={h_real: 0.25, h_artifact: 0.40, h_null: 0.70}),
        ],
    )

    # Discriminating: randomized controlled test
    e_rct = ExperimentCandidate(
        experiment_id=f"nw_erct_{seed}",
        description="Randomized controlled trial (removes confounding)",
        cost=3.0,
        possible_outcomes=["treatment_works", "no_difference"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="treatment_works", likelihoods={h_real: 0.85, h_artifact: 0.15, h_null: 0.10}),
            OutcomeLikelihoodByHypothesis(outcome_id="no_difference", likelihoods={h_real: 0.15, h_artifact: 0.85, h_null: 0.90}),
        ],
    )

    return ActiveWorld(
        world_id=f"null_weak_{seed}",
        world_type="null_vs_weak_effect",
        description="Observational evidence supports false positive; only RCT reveals null",
        hypotheses={h_real: 0.45, h_artifact: 0.30, h_null: 0.25},
        true_hypothesis_id=h_null,
        experiments=[e_observational, e_confirm, e_rct],
        experiment_budget=3,
        cost_budget=4.0,
    )


def create_multi_hypothesis_branch(*, seed: int = 1) -> ActiveWorld:
    """
    4 hypotheses. Different experiments separate different pairs.
    Optimal strategy requires choosing the most globally informative experiment.
    """
    hs = [f"mhb_h{i}_{seed}" for i in range(1, 5)]

    # Separates {h1,h2} from {h3,h4}
    e_cluster = ExperimentCandidate(
        experiment_id=f"mhb_ecluster_{seed}",
        description="Separates mechanism family A from B",
        cost=1.5,
        possible_outcomes=["family_a", "family_b"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="family_a", likelihoods={hs[0]: 0.85, hs[1]: 0.80, hs[2]: 0.15, hs[3]: 0.10}),
            OutcomeLikelihoodByHypothesis(outcome_id="family_b", likelihoods={hs[0]: 0.15, hs[1]: 0.20, hs[2]: 0.85, hs[3]: 0.90}),
        ],
    )

    # Separates h1 from h2 (within family A)
    e_within_a = ExperimentCandidate(
        experiment_id=f"mhb_ea_{seed}",
        description="Distinguishes h1 from h2",
        cost=2.0,
        possible_outcomes=["marker_1", "marker_2"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="marker_1", likelihoods={hs[0]: 0.90, hs[1]: 0.10, hs[2]: 0.50, hs[3]: 0.50}),
            OutcomeLikelihoodByHypothesis(outcome_id="marker_2", likelihoods={hs[0]: 0.10, hs[1]: 0.90, hs[2]: 0.50, hs[3]: 0.50}),
        ],
    )

    # Separates h3 from h4 (within family B)
    e_within_b = ExperimentCandidate(
        experiment_id=f"mhb_eb_{seed}",
        description="Distinguishes h3 from h4",
        cost=2.0,
        possible_outcomes=["variant_x", "variant_y"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="variant_x", likelihoods={hs[0]: 0.50, hs[1]: 0.50, hs[2]: 0.85, hs[3]: 0.15}),
            OutcomeLikelihoodByHypothesis(outcome_id="variant_y", likelihoods={hs[0]: 0.50, hs[1]: 0.50, hs[2]: 0.15, hs[3]: 0.85}),
        ],
    )

    return ActiveWorld(
        world_id=f"multi_branch_{seed}",
        world_type="multi_hypothesis_branch",
        description="4 hypotheses in 2 clusters; must choose which split to resolve first",
        hypotheses={hs[0]: 0.30, hs[1]: 0.25, hs[2]: 0.25, hs[3]: 0.20},
        true_hypothesis_id=hs[2],
        experiments=[e_cluster, e_within_a, e_within_b],
        experiment_budget=2,
        cost_budget=4.0,
    )


# ---------------------------------------------------------------------------
# Sequential Experiment Design (Phase 27-28)
# ---------------------------------------------------------------------------


def create_sequential_active_world(*, seed: int = 1) -> ActiveWorld:
    """
    A world where the greedy one-step JSD experiment differs from the
    optimal two-step strategy.

    Greedy picks e_strong_local (best single-step discrimination, cost=3.0).
    Optimal picks e_cheap_first (moderate info, cost=1.0) then e_conditional (cost=2.0)
    because e_conditional's value depends on e_cheap_first's result.

    Budget = 3.5 means:
    - Greedy path: e_strong_local (3.0) + nothing
    - Optimal path: e_cheap_first (1.0) + e_conditional (2.0) = more total info
    """
    h1, h2, h3 = f"seq_h1_{seed}", f"seq_h2_{seed}", f"seq_h3_{seed}"

    # Greedy best (most JSD in one shot, but expensive)
    e_strong = ExperimentCandidate(
        experiment_id=f"seq_estrong_{seed}",
        description="Comprehensive test (high discrimination, high cost)",
        cost=3.0,
        possible_outcomes=["result_a", "result_b"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="result_a", likelihoods={h1: 0.80, h2: 0.20, h3: 0.50}),
            OutcomeLikelihoodByHypothesis(outcome_id="result_b", likelihoods={h1: 0.20, h2: 0.80, h3: 0.50}),
        ],
    )

    # Cheap first step (moderate JSD)
    e_cheap = ExperimentCandidate(
        experiment_id=f"seq_echeap_{seed}",
        description="Quick screen (moderate info, enables follow-up)",
        cost=1.0,
        possible_outcomes=["screen_pos", "screen_neg"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="screen_pos", likelihoods={h1: 0.70, h2: 0.40, h3: 0.60}),
            OutcomeLikelihoodByHypothesis(outcome_id="screen_neg", likelihoods={h1: 0.30, h2: 0.60, h3: 0.40}),
        ],
    )

    # Powerful follow-up (available always, but most useful after e_cheap)
    e_followup = ExperimentCandidate(
        experiment_id=f"seq_efollowup_{seed}",
        description="Targeted confirmation of screen result",
        cost=2.0,
        possible_outcomes=["confirm_1", "confirm_2", "confirm_3"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="confirm_1", likelihoods={h1: 0.80, h2: 0.10, h3: 0.10}),
            OutcomeLikelihoodByHypothesis(outcome_id="confirm_2", likelihoods={h1: 0.10, h2: 0.80, h3: 0.10}),
            OutcomeLikelihoodByHypothesis(outcome_id="confirm_3", likelihoods={h1: 0.10, h2: 0.10, h3: 0.80}),
        ],
    )

    return ActiveWorld(
        world_id=f"sequential_{seed}",
        world_type="sequential_design",
        description="Greedy picks expensive one-shot; optimal picks cheap+followup for more total info",
        hypotheses={h1: 0.40, h2: 0.35, h3: 0.25},
        true_hypothesis_id=h2,
        experiments=[e_strong, e_cheap, e_followup],
        experiment_budget=3,
        cost_budget=3.5,
    )
