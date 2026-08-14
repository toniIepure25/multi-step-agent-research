"""
Hardened Stage 2 — Experiment Design Worlds.

These worlds break the ceiling observed in basic Stage 2:
- E3 no longer equals oracle (non-zero regret expected)
- Noisy outcomes, imperfect predictions, cost tradeoffs
- Sequential design, multi-hypothesis compression
- Deceptive confirmation patterns

SD-H3B: Robust Discriminative Experiment Selection under uncertainty.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from asar.scientific_discovery.experiment_design import (
    ExperimentCandidate,
    OutcomeLikelihoodByHypothesis,
    compute_discrimination_score,
    compute_oracle_information_gain,
)
from asar.scientific_discovery.experiment_worlds import ExperimentWorld


# ---------------------------------------------------------------------------
# World 1: NOISY OUTCOMES — Agent predictions are miscalibrated
# ---------------------------------------------------------------------------


def create_noisy_predictions_world(*, seed: int = 1, noise: float = 0.15) -> ExperimentWorld:
    """
    Agent-visible predictions are noisy versions of true likelihoods.

    The agent's JSD computation uses imperfect estimates.
    Oracle uses true generative probabilities.
    This breaks the E3=oracle ceiling.
    """
    rng = random.Random(seed)
    h1, h2, h3 = f"np_h1_{seed}", f"np_h2_{seed}", f"np_h3_{seed}"

    # True generative probabilities (oracle-only)
    true_probs = {
        "exp_a": {"outcome_x": {h1: 0.85, h2: 0.15, h3: 0.50},
                  "outcome_y": {h1: 0.15, h2: 0.85, h3: 0.50}},
        "exp_b": {"outcome_p": {h1: 0.60, h2: 0.55, h3: 0.10},
                  "outcome_q": {h1: 0.40, h2: 0.45, h3: 0.90}},
        "exp_c": {"outcome_m": {h1: 0.70, h2: 0.30, h3: 0.70},
                  "outcome_n": {h1: 0.30, h2: 0.70, h3: 0.30}},
    }

    def _add_noise(prob: float) -> float:
        noisy = prob + rng.gauss(0, noise)
        return max(0.01, min(0.99, noisy))

    experiments = []
    for exp_id, outcomes in true_probs.items():
        preds = []
        for outcome_id, hyp_probs in outcomes.items():
            # Agent sees noisy version
            noisy_likelihoods = {h: _add_noise(p) for h, p in hyp_probs.items()}
            preds.append(OutcomeLikelihoodByHypothesis(
                outcome_id=outcome_id,
                likelihoods=noisy_likelihoods,
            ))
        experiments.append(ExperimentCandidate(
            experiment_id=f"np_{exp_id}_{seed}",
            description=f"Experiment {exp_id} with noisy agent predictions",
            cost=1.0,
            possible_outcomes=list(outcomes.keys()),
            hypothesis_predictions=preds,
        ))

    # Store true predictions for oracle computation
    # (oracle uses _true_predictions attribute)
    oracle_experiments = []
    for exp_id, outcomes in true_probs.items():
        preds = []
        for outcome_id, hyp_probs in outcomes.items():
            preds.append(OutcomeLikelihoodByHypothesis(
                outcome_id=outcome_id,
                likelihoods=hyp_probs,
            ))
        oracle_experiments.append(ExperimentCandidate(
            experiment_id=f"np_{exp_id}_{seed}",
            description=f"Experiment {exp_id} (oracle view)",
            cost=1.0,
            possible_outcomes=list(outcomes.keys()),
            hypothesis_predictions=preds,
        ))

    world = ExperimentWorld(
        world_id=f"noisy_pred_{seed}",
        world_type="noisy_predictions",
        description="Agent predictions are miscalibrated; oracle uses true probabilities",
        hypotheses={h1: 0.45, h2: 0.35, h3: 0.20},
        experiments=experiments,
        true_hypothesis_id=h2,
        true_outcomes={
            f"np_exp_a_{seed}": "outcome_y",
            f"np_exp_b_{seed}": "outcome_q",
            f"np_exp_c_{seed}": "outcome_n",
        },
    )
    # Attach oracle experiments for fair oracle regret computation
    world._oracle_experiments = oracle_experiments  # type: ignore[attr-defined]
    return world


# ---------------------------------------------------------------------------
# World 2: COST-INFORMATION TRADEOFF
# ---------------------------------------------------------------------------


def create_cost_information_tradeoff(*, seed: int = 1) -> ExperimentWorld:
    """
    Most discriminating experiment costs 5×.
    A moderately discriminating experiment costs 1×.
    Cost-adjusted value may favor the cheaper option.
    """
    h1, h2, h3 = f"ci_h1_{seed}", f"ci_h2_{seed}", f"ci_h3_{seed}"

    # Cheap but moderately discriminating
    e_moderate = ExperimentCandidate(
        experiment_id=f"ci_emod_{seed}",
        description="Moderate discrimination, low cost",
        cost=1.0,
        possible_outcomes=["pos", "neg"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="pos", likelihoods={h1: 0.75, h2: 0.35, h3: 0.50}),
            OutcomeLikelihoodByHypothesis(outcome_id="neg", likelihoods={h1: 0.25, h2: 0.65, h3: 0.50}),
        ],
    )

    # Highly discriminating but expensive — max outcome prob for leader is moderate
    e_expensive = ExperimentCandidate(
        experiment_id=f"ci_eexp_{seed}",
        description="High discrimination, high cost",
        cost=5.0,
        possible_outcomes=["type_a", "type_b", "type_c"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="type_a", likelihoods={h1: 0.60, h2: 0.05, h3: 0.10}),
            OutcomeLikelihoodByHypothesis(outcome_id="type_b", likelihoods={h1: 0.10, h2: 0.85, h3: 0.05}),
            OutcomeLikelihoodByHypothesis(outcome_id="type_c", likelihoods={h1: 0.30, h2: 0.10, h3: 0.85}),
        ],
    )

    # Cheap but useless (deceptive confirmation)
    e_cheap_confirm = ExperimentCandidate(
        experiment_id=f"ci_echeap_{seed}",
        description="Cheap confirmation — supports leader but doesn't discriminate",
        cost=0.5,
        possible_outcomes=["good", "bad"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="good", likelihoods={h1: 0.80, h2: 0.75, h3: 0.30}),
            OutcomeLikelihoodByHypothesis(outcome_id="bad", likelihoods={h1: 0.20, h2: 0.25, h3: 0.70}),
        ],
    )

    return ExperimentWorld(
        world_id=f"cost_info_{seed}",
        world_type="cost_information_tradeoff",
        description="Best discrimination costs 5×; moderate costs 1×; cheap confirms without discriminating",
        hypotheses={h1: 0.50, h2: 0.30, h3: 0.20},
        experiments=[e_moderate, e_expensive, e_cheap_confirm],
        true_hypothesis_id=h2,
        true_outcomes={
            f"ci_emod_{seed}": "neg",
            f"ci_eexp_{seed}": "type_b",
            f"ci_echeap_{seed}": "good",
        },
    )


# ---------------------------------------------------------------------------
# World 3: MULTI-HYPOTHESIS COMPRESSION (5 hypotheses)
# ---------------------------------------------------------------------------


def create_multi_hypothesis_world(*, seed: int = 1) -> ExperimentWorld:
    """
    5 competing hypotheses where some differ only under rare outcomes.
    Requires careful experiment selection to separate clusters.
    """
    hs = [f"mh_h{i}_{seed}" for i in range(1, 6)]

    # Experiment 1: Separates cluster {h1,h2} from {h3,h4,h5}
    e_cluster = ExperimentCandidate(
        experiment_id=f"mh_ecluster_{seed}",
        description="Separates two major hypothesis clusters",
        cost=1.5,
        possible_outcomes=["cluster_a", "cluster_b"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="cluster_a",
                likelihoods={hs[0]: 0.80, hs[1]: 0.75, hs[2]: 0.20, hs[3]: 0.15, hs[4]: 0.25}),
            OutcomeLikelihoodByHypothesis(outcome_id="cluster_b",
                likelihoods={hs[0]: 0.20, hs[1]: 0.25, hs[2]: 0.80, hs[3]: 0.85, hs[4]: 0.75}),
        ],
    )

    # Experiment 2: Separates h1 from h2 (within-cluster)
    e_within_ab = ExperimentCandidate(
        experiment_id=f"mh_ewithin_ab_{seed}",
        description="Distinguishes h1 from h2 within cluster A",
        cost=2.0,
        possible_outcomes=["specific_1", "specific_2"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="specific_1",
                likelihoods={hs[0]: 0.90, hs[1]: 0.10, hs[2]: 0.50, hs[3]: 0.50, hs[4]: 0.50}),
            OutcomeLikelihoodByHypothesis(outcome_id="specific_2",
                likelihoods={hs[0]: 0.10, hs[1]: 0.90, hs[2]: 0.50, hs[3]: 0.50, hs[4]: 0.50}),
        ],
    )

    # Experiment 3: Separates h3/h4 from h5 (within cluster B)
    e_within_b = ExperimentCandidate(
        experiment_id=f"mh_ewithin_b_{seed}",
        description="Distinguishes h3/h4 from h5 within cluster B",
        cost=1.0,
        possible_outcomes=["sub_x", "sub_y"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="sub_x",
                likelihoods={hs[0]: 0.50, hs[1]: 0.50, hs[2]: 0.75, hs[3]: 0.80, hs[4]: 0.15}),
            OutcomeLikelihoodByHypothesis(outcome_id="sub_y",
                likelihoods={hs[0]: 0.50, hs[1]: 0.50, hs[2]: 0.25, hs[3]: 0.20, hs[4]: 0.85}),
        ],
    )

    beliefs = {hs[0]: 0.30, hs[1]: 0.25, hs[2]: 0.20, hs[3]: 0.15, hs[4]: 0.10}

    return ExperimentWorld(
        world_id=f"multi_hyp_{seed}",
        world_type="multi_hypothesis",
        description="5 hypotheses in 2 clusters; different experiments separate at different levels",
        hypotheses=beliefs,
        experiments=[e_cluster, e_within_ab, e_within_b],
        true_hypothesis_id=hs[3],  # h4 is true (within cluster B)
        true_outcomes={
            f"mh_ecluster_{seed}": "cluster_b",
            f"mh_ewithin_ab_{seed}": "specific_2",
            f"mh_ewithin_b_{seed}": "sub_x",
        },
    )


# ---------------------------------------------------------------------------
# World 4: SEQUENTIAL DESIGN (greedy ≠ optimal)
# ---------------------------------------------------------------------------


@dataclass
class SequentialExperimentWorld:
    """
    A world where the optimal SEQUENCE of experiments differs from the
    greedy one-step-optimal experiment.

    The greedy JSD policy picks the single best discriminator.
    But the oracle sequential policy picks a cheaper first experiment
    that enables a much more informative second experiment.
    """

    world_id: str
    world_type: str = "sequential_design"
    description: str = ""
    hypotheses: dict[str, float] = field(default_factory=dict)
    experiments_round1: list[ExperimentCandidate] = field(default_factory=list)
    experiments_round2: dict[str, list[ExperimentCandidate]] = field(default_factory=dict)
    true_hypothesis_id: str = ""
    true_outcomes: dict[str, str] = field(default_factory=dict)
    budget: float = 3.0


def create_sequential_world(*, seed: int = 1) -> SequentialExperimentWorld:
    """
    Round 1 has two experiments:
    - e_greedy: best single-step discrimination (cost=2.5)
    - e_enable: weaker discrimination (cost=1.0) but enables powerful round 2

    If budget = 3.0:
    - Greedy path: e_greedy (2.5) + nothing affordable
    - Optimal path: e_enable (1.0) + e_powerful (2.0) = much more total info
    """
    h1, h2, h3 = f"sq_h1_{seed}", f"sq_h2_{seed}", f"sq_h3_{seed}"

    e_greedy = ExperimentCandidate(
        experiment_id=f"sq_egreedy_{seed}",
        description="Best single-step discrimination but expensive",
        cost=2.5,
        possible_outcomes=["g_a", "g_b"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="g_a", likelihoods={h1: 0.80, h2: 0.20, h3: 0.50}),
            OutcomeLikelihoodByHypothesis(outcome_id="g_b", likelihoods={h1: 0.20, h2: 0.80, h3: 0.50}),
        ],
    )

    e_enable = ExperimentCandidate(
        experiment_id=f"sq_eenable_{seed}",
        description="Moderate discrimination, enables powerful follow-up",
        cost=1.0,
        possible_outcomes=["en_x", "en_y"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="en_x", likelihoods={h1: 0.60, h2: 0.40, h3: 0.70}),
            OutcomeLikelihoodByHypothesis(outcome_id="en_y", likelihoods={h1: 0.40, h2: 0.60, h3: 0.30}),
        ],
    )

    # After e_enable, a powerful follow-up becomes available
    e_powerful = ExperimentCandidate(
        experiment_id=f"sq_epow_{seed}",
        description="Powerful discriminator available only after e_enable",
        cost=2.0,
        possible_outcomes=["pow_1", "pow_2", "pow_3"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="pow_1", likelihoods={h1: 0.85, h2: 0.05, h3: 0.10}),
            OutcomeLikelihoodByHypothesis(outcome_id="pow_2", likelihoods={h1: 0.05, h2: 0.85, h3: 0.10}),
            OutcomeLikelihoodByHypothesis(outcome_id="pow_3", likelihoods={h1: 0.10, h2: 0.10, h3: 0.80}),
        ],
    )

    return SequentialExperimentWorld(
        world_id=f"sequential_{seed}",
        description="Greedy picks expensive e_greedy; optimal picks cheap e_enable then e_powerful",
        hypotheses={h1: 0.40, h2: 0.35, h3: 0.25},
        experiments_round1=[e_greedy, e_enable],
        experiments_round2={f"sq_eenable_{seed}": [e_powerful]},
        true_hypothesis_id=h2,
        true_outcomes={
            f"sq_egreedy_{seed}": "g_b",
            f"sq_eenable_{seed}": "en_y",
            f"sq_epow_{seed}": "pow_2",
        },
        budget=3.0,
    )


# ---------------------------------------------------------------------------
# World 5: DECEPTIVE CONFIRMATION
# ---------------------------------------------------------------------------


def create_deceptive_confirmation_world(*, seed: int = 1) -> ExperimentWorld:
    """
    Cheap experiments confirm leader but reveal nothing.
    The only informative experiment is moderately costly and unlikely
    to produce 'positive' results for the current leader.

    Tests whether agent avoids the confirmation trap in experiment design.
    """
    h1, h2 = f"dc_h1_{seed}", f"dc_h2_{seed}"

    e_deceptive1 = ExperimentCandidate(
        experiment_id=f"dc_edec1_{seed}",
        description="Cheap: high P(positive|leader) but H1≈H2 predictions",
        cost=0.5,
        possible_outcomes=["positive", "negative"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="positive", likelihoods={h1: 0.80, h2: 0.75}),
            OutcomeLikelihoodByHypothesis(outcome_id="negative", likelihoods={h1: 0.20, h2: 0.25}),
        ],
    )

    e_deceptive2 = ExperimentCandidate(
        experiment_id=f"dc_edec2_{seed}",
        description="Cheap: slightly favors leader in expected direction",
        cost=0.5,
        possible_outcomes=["success", "failure"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="success", likelihoods={h1: 0.70, h2: 0.65}),
            OutcomeLikelihoodByHypothesis(outcome_id="failure", likelihoods={h1: 0.30, h2: 0.35}),
        ],
    )

    # Informative: predictions diverge but max for leader is only moderate
    e_informative = ExperimentCandidate(
        experiment_id=f"dc_einf_{seed}",
        description="Costly but predictions diverge substantially",
        cost=2.0,
        possible_outcomes=["marker_present", "marker_absent"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="marker_present", likelihoods={h1: 0.75, h2: 0.10}),
            OutcomeLikelihoodByHypothesis(outcome_id="marker_absent", likelihoods={h1: 0.25, h2: 0.90}),
        ],
    )

    return ExperimentWorld(
        world_id=f"deceptive_conf_{seed}",
        world_type="deceptive_confirmation",
        description="Cheap experiments confirm leader with no discrimination; only costly one separates",
        hypotheses={h1: 0.60, h2: 0.40},
        experiments=[e_deceptive1, e_deceptive2, e_informative],
        true_hypothesis_id=h2,
        true_outcomes={
            f"dc_edec1_{seed}": "positive",
            f"dc_edec2_{seed}": "success",
            f"dc_einf_{seed}": "marker_absent",
        },
    )


# ---------------------------------------------------------------------------
# World 6: PARTIAL IDENTIFIABILITY
# ---------------------------------------------------------------------------


def create_partial_identifiability_world(*, seed: int = 1) -> ExperimentWorld:
    """
    Budget allows one experiment. No single experiment fully identifies truth.
    Best strategy: pick experiment maximizing partial information.
    Correct final state may be UNCERTAIN rather than DECIDED.
    """
    h1, h2, h3 = f"pi_h1_{seed}", f"pi_h2_{seed}", f"pi_h3_{seed}"

    # All experiments partially discriminate but none is decisive
    e1 = ExperimentCandidate(
        experiment_id=f"pi_e1_{seed}",
        description="Separates h1 from h2/h3 somewhat",
        cost=1.0,
        possible_outcomes=["r1", "r2"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="r1", likelihoods={h1: 0.70, h2: 0.40, h3: 0.45}),
            OutcomeLikelihoodByHypothesis(outcome_id="r2", likelihoods={h1: 0.30, h2: 0.60, h3: 0.55}),
        ],
    )

    e2 = ExperimentCandidate(
        experiment_id=f"pi_e2_{seed}",
        description="Separates h2 from h1/h3 somewhat",
        cost=1.0,
        possible_outcomes=["s1", "s2"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="s1", likelihoods={h1: 0.45, h2: 0.75, h3: 0.40}),
            OutcomeLikelihoodByHypothesis(outcome_id="s2", likelihoods={h1: 0.55, h2: 0.25, h3: 0.60}),
        ],
    )

    e3 = ExperimentCandidate(
        experiment_id=f"pi_e3_{seed}",
        description="Separates h3 from h1/h2 somewhat",
        cost=1.0,
        possible_outcomes=["t1", "t2"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="t1", likelihoods={h1: 0.50, h2: 0.45, h3: 0.80}),
            OutcomeLikelihoodByHypothesis(outcome_id="t2", likelihoods={h1: 0.50, h2: 0.55, h3: 0.20}),
        ],
    )

    return ExperimentWorld(
        world_id=f"partial_ident_{seed}",
        world_type="partial_identifiability",
        description="No single experiment decisively identifies truth; partial info is best achievable",
        hypotheses={h1: 0.35, h2: 0.35, h3: 0.30},
        experiments=[e1, e2, e3],
        true_hypothesis_id=h2,
        true_outcomes={
            f"pi_e1_{seed}": "r2",
            f"pi_e2_{seed}": "s1",
            f"pi_e3_{seed}": "t2",
        },
    )
