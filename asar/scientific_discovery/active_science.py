"""
Stage 3 — Active Science: Endogenous Evidence Acquisition.

In Stage 1, evidence was predetermined — the agent could not choose what to observe.
In Active Science, the agent selects experiments and the environment produces
observations conditional on the selection. This is where policy selection
genuinely matters.

SD-H9: A policy combining falsification-oriented hypothesis challenge with
discriminative experiment selection improves scientific recovery under
endogenous evidence acquisition.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable

from asar.scientific_discovery.experiment_design import (
    ExperimentCandidate,
    ExperimentSelection,
    OutcomeLikelihoodByHypothesis,
    compute_discrimination_score,
    compute_confirmation_score,
    compute_oracle_information_gain,
    select_cheapest,
    select_confirmation,
    select_discrimination,
    select_oracle,
    select_random,
)
from asar.scientific_discovery.state import EvidenceDirection, ScientificEvidence


# ---------------------------------------------------------------------------
# Active World Definition
# ---------------------------------------------------------------------------


@dataclass
class ActiveWorld:
    """A world where the agent's experiment choice determines the observation."""

    world_id: str
    world_type: str
    description: str
    hypotheses: dict[str, float]  # hypothesis_id → initial belief
    true_hypothesis_id: str
    experiments: list[ExperimentCandidate]
    experiment_budget: int = 3  # max number of experiments
    cost_budget: float = 10.0

    def sample_outcome(self, experiment_id: str, rng: random.Random) -> str:
        """Sample an outcome from the true generative distribution."""
        exp = next((e for e in self.experiments if e.experiment_id == experiment_id), None)
        if exp is None:
            raise ValueError(f"Unknown experiment: {experiment_id}")

        # Get true likelihoods for each outcome
        outcome_probs: dict[str, float] = {}
        for pred in exp.hypothesis_predictions:
            prob = pred.likelihoods.get(self.true_hypothesis_id, 0.5)
            outcome_probs[pred.outcome_id] = prob

        # Normalize and sample
        total = sum(outcome_probs.values())
        if total < 1e-10:
            return list(outcome_probs.keys())[0]

        r = rng.random() * total
        cumulative = 0.0
        for outcome_id, prob in outcome_probs.items():
            cumulative += prob
            if r <= cumulative:
                return outcome_id
        return list(outcome_probs.keys())[-1]


@dataclass
class ActiveEpisodeResult:
    """Result of running an active science episode."""

    world_id: str
    world_type: str
    policy_name: str
    experiments_selected: list[str]
    outcomes_observed: list[str]
    belief_trajectory: list[dict[str, float]]
    final_beliefs: dict[str, float]
    total_cost: float
    recovered: bool  # final leader == true hypothesis
    true_hypothesis_id: str
    n_experiments: int


# ---------------------------------------------------------------------------
# Active Science Runner
# ---------------------------------------------------------------------------


def run_active_episode(
    world: ActiveWorld,
    policy_fn: Callable[[list[ExperimentCandidate], dict[str, float]], ExperimentSelection],
    seed: int = 42,
) -> ActiveEpisodeResult:
    """
    Run an active science episode where the agent selects experiments
    and the environment produces observations.
    """
    rng = random.Random(seed)
    beliefs = dict(world.hypotheses)
    trajectory = [dict(beliefs)]
    experiments_selected: list[str] = []
    outcomes_observed: list[str] = []
    total_cost = 0.0

    available_experiments = list(world.experiments)

    for _ in range(world.experiment_budget):
        if total_cost >= world.cost_budget:
            break
        if not available_experiments:
            break

        # Filter by remaining budget
        affordable = [e for e in available_experiments if e.cost + total_cost <= world.cost_budget]
        if not affordable:
            break

        # Policy selects experiment
        selection = policy_fn(affordable, beliefs)
        selected_exp = next(
            (e for e in affordable if e.experiment_id == selection.selected_experiment_id),
            affordable[0],
        )

        # Environment samples outcome
        outcome = world.sample_outcome(selected_exp.experiment_id, rng)
        experiments_selected.append(selected_exp.experiment_id)
        outcomes_observed.append(outcome)
        total_cost += selected_exp.cost

        # Bayesian belief update
        beliefs = _bayesian_update(beliefs, selected_exp, outcome)
        trajectory.append(dict(beliefs))

    # Determine recovery
    leader = max(beliefs.items(), key=lambda x: x[1])[0]
    recovered = (leader == world.true_hypothesis_id)

    return ActiveEpisodeResult(
        world_id=world.world_id,
        world_type=world.world_type,
        policy_name="",  # set by caller
        experiments_selected=experiments_selected,
        outcomes_observed=outcomes_observed,
        belief_trajectory=trajectory,
        final_beliefs=beliefs,
        total_cost=total_cost,
        recovered=recovered,
        true_hypothesis_id=world.true_hypothesis_id,
        n_experiments=len(experiments_selected),
    )


def _bayesian_update(
    beliefs: dict[str, float],
    experiment: ExperimentCandidate,
    observed_outcome: str,
) -> dict[str, float]:
    """Perform exact Bayesian update given observed outcome."""
    posterior = {}
    for hid, prior in beliefs.items():
        # Find likelihood P(outcome | hypothesis)
        likelihood = 0.5  # default
        for pred in experiment.hypothesis_predictions:
            if pred.outcome_id == observed_outcome:
                likelihood = pred.likelihoods.get(hid, 0.5)
                break
        posterior[hid] = prior * likelihood

    # Normalize
    total = sum(posterior.values())
    if total < 1e-10:
        return beliefs
    return {k: v / total for k, v in posterior.items()}


# ---------------------------------------------------------------------------
# Active Science Policies (wrappers)
# ---------------------------------------------------------------------------


def active_passive(experiments: list[ExperimentCandidate], beliefs: dict[str, float]) -> ExperimentSelection:
    """Passive: just picks the first available experiment (arbitrary)."""
    return ExperimentSelection(
        selected_experiment_id=experiments[0].experiment_id,
        discrimination_score=0.0,
        policy_rationale="Passive (first available)",
    )


def active_random(experiments: list[ExperimentCandidate], beliefs: dict[str, float]) -> ExperimentSelection:
    """Random experiment selection."""
    return select_random(experiments, beliefs, seed=hash(str(beliefs)) % 10000)


def active_confirmation(experiments: list[ExperimentCandidate], beliefs: dict[str, float]) -> ExperimentSelection:
    """Confirmation-seeking: maximize P(positive result for leader)."""
    return select_confirmation(experiments, beliefs)


def active_discrimination(experiments: list[ExperimentCandidate], beliefs: dict[str, float]) -> ExperimentSelection:
    """ASAR discrimination: maximize JSD between hypothesis predictions."""
    return select_discrimination(experiments, beliefs)


# ---------------------------------------------------------------------------
# Active World Generators
# ---------------------------------------------------------------------------


def create_active_confirmation_trap(*, seed: int = 1) -> ActiveWorld:
    """
    Active version of the confirmation trap.
    Cheap experiments confirm leader; expensive one discriminates.
    Agent must choose to invest in discrimination over easy confirmation.
    """
    h1, h2, h3 = f"act_h1_{seed}", f"act_h2_{seed}", f"act_h3_{seed}"

    # Cheap confirmation: both H1 and H2 predict positive
    e_confirm = ExperimentCandidate(
        experiment_id=f"act_econf_{seed}",
        description="Symptom survey (H1≈H2 predictions)",
        cost=1.0,
        possible_outcomes=["improved", "no_change"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="improved", likelihoods={h1: 0.75, h2: 0.70, h3: 0.30}),
            OutcomeLikelihoodByHypothesis(outcome_id="no_change", likelihoods={h1: 0.25, h2: 0.30, h3: 0.70}),
        ],
    )

    # Discriminating experiment: H1 and H2 make opposite predictions
    e_discriminate = ExperimentCandidate(
        experiment_id=f"act_edisc_{seed}",
        description="Mechanistic biomarker (H1 vs H2 opposite)",
        cost=2.0,
        possible_outcomes=["pathway_a", "pathway_b", "none"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="pathway_a", likelihoods={h1: 0.80, h2: 0.10, h3: 0.10}),
            OutcomeLikelihoodByHypothesis(outcome_id="pathway_b", likelihoods={h1: 0.10, h2: 0.80, h3: 0.10}),
            OutcomeLikelihoodByHypothesis(outcome_id="none", likelihoods={h1: 0.10, h2: 0.10, h3: 0.80}),
        ],
    )

    # Another cheap non-discriminating experiment
    e_cheap2 = ExperimentCandidate(
        experiment_id=f"act_echeap2_{seed}",
        description="Follow-up questionnaire (non-discriminating)",
        cost=0.5,
        possible_outcomes=["satisfied", "neutral"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="satisfied", likelihoods={h1: 0.65, h2: 0.60, h3: 0.35}),
            OutcomeLikelihoodByHypothesis(outcome_id="neutral", likelihoods={h1: 0.35, h2: 0.40, h3: 0.65}),
        ],
    )

    return ActiveWorld(
        world_id=f"active_trap_{seed}",
        world_type="active_confirmation_trap",
        description="Confirmation-seekers waste budget; discrimination identifies truth",
        hypotheses={h1: 0.55, h2: 0.30, h3: 0.15},
        true_hypothesis_id=h2,
        experiments=[e_confirm, e_discriminate, e_cheap2],
        experiment_budget=3,
        cost_budget=4.0,
    )


def create_active_reverse_causality(*, seed: int = 1) -> ActiveWorld:
    """Active version where intervention experiments reveal causal direction."""
    h_xy, h_yx, h_conf = f"arc_hxy_{seed}", f"arc_hyx_{seed}", f"arc_hconf_{seed}"

    e_observe = ExperimentCandidate(
        experiment_id=f"arc_eobs_{seed}",
        description="Observational correlation study (ambiguous)",
        cost=1.0,
        possible_outcomes=["correlated", "uncorrelated"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="correlated", likelihoods={h_xy: 0.85, h_yx: 0.85, h_conf: 0.70}),
            OutcomeLikelihoodByHypothesis(outcome_id="uncorrelated", likelihoods={h_xy: 0.15, h_yx: 0.15, h_conf: 0.30}),
        ],
    )

    e_intervene_x = ExperimentCandidate(
        experiment_id=f"arc_eintx_{seed}",
        description="Intervene on X, observe Y (discriminates X→Y from Y→X)",
        cost=3.0,
        possible_outcomes=["y_changes", "y_stable"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="y_changes", likelihoods={h_xy: 0.90, h_yx: 0.10, h_conf: 0.20}),
            OutcomeLikelihoodByHypothesis(outcome_id="y_stable", likelihoods={h_xy: 0.10, h_yx: 0.90, h_conf: 0.80}),
        ],
    )

    e_intervene_y = ExperimentCandidate(
        experiment_id=f"arc_einty_{seed}",
        description="Intervene on Y, observe X (discriminates Y→X from X→Y)",
        cost=3.0,
        possible_outcomes=["x_changes", "x_stable"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="x_changes", likelihoods={h_xy: 0.10, h_yx: 0.90, h_conf: 0.20}),
            OutcomeLikelihoodByHypothesis(outcome_id="x_stable", likelihoods={h_xy: 0.90, h_yx: 0.10, h_conf: 0.80}),
        ],
    )

    return ActiveWorld(
        world_id=f"active_reverse_{seed}",
        world_type="active_reverse_causality",
        description="Observation is ambiguous; only intervention experiments reveal causality",
        hypotheses={h_xy: 0.50, h_yx: 0.30, h_conf: 0.20},
        true_hypothesis_id=h_yx,
        experiments=[e_observe, e_intervene_x, e_intervene_y],
        experiment_budget=2,
        cost_budget=5.0,
    )


def create_active_null_world(*, seed: int = 1) -> ActiveWorld:
    """Active world where no causal hypothesis is correct."""
    h_causal, h_artifact, h_null = f"an_hcaus_{seed}", f"an_hart_{seed}", f"an_hnull_{seed}"

    e_replicate = ExperimentCandidate(
        experiment_id=f"an_erep_{seed}",
        description="Replication study with larger sample",
        cost=2.0,
        possible_outcomes=["effect_found", "null_result"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="effect_found", likelihoods={h_causal: 0.85, h_artifact: 0.40, h_null: 0.15}),
            OutcomeLikelihoodByHypothesis(outcome_id="null_result", likelihoods={h_causal: 0.15, h_artifact: 0.60, h_null: 0.85}),
        ],
    )

    e_control = ExperimentCandidate(
        experiment_id=f"an_ectrl_{seed}",
        description="Placebo-controlled trial",
        cost=3.0,
        possible_outcomes=["treatment_better", "no_difference"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="treatment_better", likelihoods={h_causal: 0.80, h_artifact: 0.20, h_null: 0.10}),
            OutcomeLikelihoodByHypothesis(outcome_id="no_difference", likelihoods={h_causal: 0.20, h_artifact: 0.80, h_null: 0.90}),
        ],
    )

    e_mechanism = ExperimentCandidate(
        experiment_id=f"an_emech_{seed}",
        description="Mechanism assay (tests proposed pathway)",
        cost=1.5,
        possible_outcomes=["pathway_active", "pathway_inactive"],
        hypothesis_predictions=[
            OutcomeLikelihoodByHypothesis(outcome_id="pathway_active", likelihoods={h_causal: 0.75, h_artifact: 0.30, h_null: 0.25}),
            OutcomeLikelihoodByHypothesis(outcome_id="pathway_inactive", likelihoods={h_causal: 0.25, h_artifact: 0.70, h_null: 0.75}),
        ],
    )

    return ActiveWorld(
        world_id=f"active_null_{seed}",
        world_type="active_null",
        description="No real causal effect; good policy converges on null/artifact",
        hypotheses={h_causal: 0.50, h_artifact: 0.25, h_null: 0.25},
        true_hypothesis_id=h_null,
        experiments=[e_replicate, e_control, e_mechanism],
        experiment_budget=2,
        cost_budget=5.0,
    )


# ---------------------------------------------------------------------------
# Active Science Benchmark Runner
# ---------------------------------------------------------------------------


@dataclass
class ActiveBenchmarkResult:
    """Aggregate results from active science benchmark."""

    policy_name: str
    episodes: list[ActiveEpisodeResult] = field(default_factory=list)

    @property
    def recovery_rate(self) -> float:
        if not self.episodes:
            return 0.0
        return sum(1 for e in self.episodes if e.recovered) / len(self.episodes)

    @property
    def mean_cost(self) -> float:
        if not self.episodes:
            return 0.0
        return sum(e.total_cost for e in self.episodes) / len(self.episodes)

    @property
    def mean_experiments(self) -> float:
        if not self.episodes:
            return 0.0
        return sum(e.n_experiments for e in self.episodes) / len(self.episodes)


def run_active_benchmark(seeds: list[int], hard: bool = False) -> dict[str, ActiveBenchmarkResult]:
    """Run active science benchmark across all policies and worlds."""
    world_factories = [
        create_active_confirmation_trap,
        create_active_reverse_causality,
        create_active_null_world,
    ]

    if hard:
        from asar.scientific_discovery.active_worlds_hard import (
            create_confirmation_dead_end,
            create_multi_hypothesis_branch,
            create_null_vs_weak_effect,
            create_sequential_active_world,
        )
        world_factories.extend([
            create_confirmation_dead_end,
            create_null_vs_weak_effect,
            create_multi_hypothesis_branch,
            create_sequential_active_world,
        ])

    policies = {
        "passive": active_passive,
        "random": active_random,
        "confirmation": active_confirmation,
        "discrimination": active_discrimination,
    }

    results = {name: ActiveBenchmarkResult(policy_name=name) for name in policies}

    for seed in seeds:
        for factory in world_factories:
            world = factory(seed=seed)
            for name, policy_fn in policies.items():
                episode = run_active_episode(world, policy_fn, seed=seed)
                episode.policy_name = name
                results[name].episodes.append(episode)

    return results
