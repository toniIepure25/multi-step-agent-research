"""
Stage 2 — Discriminative Experiment Design.

SD-H3: A policy that selects experiments for discriminative power achieves lower
oracle regret and faster uncertainty reduction than confirmation-seeking or random.

Key distinction: ASAR optimizes PREDICTED DISCRIMINATIVE VALUE,
not PROBABILITY EXPERIMENT SUPPORTS CURRENT BEST HYPOTHESIS.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Core typed objects
# ---------------------------------------------------------------------------


class PossibleOutcome(BaseModel):
    """A possible result of an experiment."""

    outcome_id: str
    description: str
    probability_given_true: float = 0.5  # P(outcome | world truth)


class OutcomeLikelihoodByHypothesis(BaseModel):
    """How likely each hypothesis predicts a specific outcome."""

    outcome_id: str
    likelihoods: dict[str, float] = Field(default_factory=dict)
    # hypothesis_id → P(outcome | hypothesis)


class ExperimentCandidate(BaseModel):
    """A candidate experiment the system can choose to run."""

    experiment_id: str
    description: str
    cost: float = 1.0
    possible_outcomes: list[str] = Field(default_factory=list)
    hypothesis_predictions: list[OutcomeLikelihoodByHypothesis] = Field(default_factory=list)
    feasibility: float = 1.0

    @property
    def n_outcomes(self) -> int:
        return len(self.possible_outcomes)


class ExperimentSelection(BaseModel):
    """Record of which experiment was selected and why."""

    selected_experiment_id: str
    discrimination_score: float
    policy_rationale: str
    alternatives_considered: list[str] = Field(default_factory=list)


class ExperimentObservation(BaseModel):
    """The actual observed outcome of a conducted experiment."""

    experiment_id: str
    observed_outcome_id: str
    reliability: float = 1.0


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------


def compute_discrimination_score(
    experiment: ExperimentCandidate,
    beliefs: dict[str, float],
) -> float:
    """
    Compute how well an experiment discriminates between live hypotheses.

    Uses Jensen-Shannon divergence between hypothesis prediction distributions.
    Higher score = experiment outcomes differ more across hypotheses.
    """
    if not experiment.hypothesis_predictions:
        return 0.0

    hypothesis_ids = list(beliefs.keys())
    if len(hypothesis_ids) < 2:
        return 0.0

    # Build prediction matrix: for each outcome, what does each hypothesis predict?
    # Then compute average pairwise divergence
    total_divergence = 0.0
    n_pairs = 0

    for i, h1 in enumerate(hypothesis_ids):
        for h2 in hypothesis_ids[i + 1:]:
            # Get prediction vectors for h1 and h2
            p1 = _get_prediction_vector(experiment, h1)
            p2 = _get_prediction_vector(experiment, h2)

            if p1 and p2:
                div = _jensen_shannon_divergence(p1, p2)
                # Weight by combined belief (focus discrimination on plausible hypotheses)
                weight = beliefs.get(h1, 0) * beliefs.get(h2, 0)
                total_divergence += div * weight
                n_pairs += 1

    if n_pairs == 0:
        return 0.0

    # Normalize to [0, 1]
    max_possible = math.log(2)  # max JSD
    total_weight = sum(
        beliefs.get(h1, 0) * beliefs.get(h2, 0)
        for i, h1 in enumerate(hypothesis_ids)
        for h2 in hypothesis_ids[i + 1:]
    )

    if total_weight < 1e-10:
        return 0.0

    return min(1.0, total_divergence / (total_weight * max_possible + 1e-10))


def compute_confirmation_score(
    experiment: ExperimentCandidate,
    beliefs: dict[str, float],
) -> float:
    """
    Compute how likely an experiment confirms the current leading hypothesis.

    A confirmation-seeking policy maximizes this.
    """
    if not beliefs or not experiment.hypothesis_predictions:
        return 0.0

    leader = max(beliefs.items(), key=lambda x: x[1])[0]
    preds = _get_prediction_vector(experiment, leader)

    if not preds:
        return 0.0

    # Confirmation score = expected probability of most-likely outcome under leader
    return max(preds.values()) if preds else 0.0


def compute_oracle_information_gain(
    experiment: ExperimentCandidate,
    beliefs: dict[str, float],
    true_hypothesis_id: str,
) -> float:
    """
    EVALUATOR-ONLY: Compute true expected information gain using latent truth.

    This is the oracle upper bound — never available to agent policies.
    """
    if not experiment.hypothesis_predictions:
        return 0.0

    # Get the true hypothesis's prediction
    true_preds = _get_prediction_vector(experiment, true_hypothesis_id)
    if not true_preds:
        return 0.0

    # Current entropy
    current_entropy = _entropy(list(beliefs.values()))

    # Expected posterior entropy (using true distribution of outcomes)
    expected_posterior_entropy = 0.0
    for outcome_id, p_outcome in true_preds.items():
        if p_outcome < 1e-10:
            continue

        # Compute posterior beliefs given this outcome
        posterior = {}
        for hid, prior in beliefs.items():
            h_preds = _get_prediction_vector(experiment, hid)
            likelihood = h_preds.get(outcome_id, 0.01) if h_preds else 0.01
            posterior[hid] = prior * likelihood

        # Normalize
        total = sum(posterior.values())
        if total > 0:
            posterior = {k: v / total for k, v in posterior.items()}

        expected_posterior_entropy += p_outcome * _entropy(list(posterior.values()))

    return max(0.0, current_entropy - expected_posterior_entropy)


# ---------------------------------------------------------------------------
# Experiment Design Policies
# ---------------------------------------------------------------------------


def select_random(
    experiments: list[ExperimentCandidate],
    beliefs: dict[str, float],
    seed: int = 42,
) -> ExperimentSelection:
    """E0: Random experiment selection."""
    import random as rng
    rng.seed(seed)
    chosen = rng.choice(experiments)
    return ExperimentSelection(
        selected_experiment_id=chosen.experiment_id,
        discrimination_score=compute_discrimination_score(chosen, beliefs),
        policy_rationale="Random selection",
        alternatives_considered=[e.experiment_id for e in experiments if e != chosen],
    )


def select_cheapest(
    experiments: list[ExperimentCandidate],
    beliefs: dict[str, float],
) -> ExperimentSelection:
    """E1: Select cheapest experiment."""
    chosen = min(experiments, key=lambda e: e.cost)
    return ExperimentSelection(
        selected_experiment_id=chosen.experiment_id,
        discrimination_score=compute_discrimination_score(chosen, beliefs),
        policy_rationale="Cheapest experiment",
        alternatives_considered=[e.experiment_id for e in experiments if e != chosen],
    )


def select_confirmation(
    experiments: list[ExperimentCandidate],
    beliefs: dict[str, float],
) -> ExperimentSelection:
    """E2: Select experiment most likely to confirm current leader."""
    scored = [(e, compute_confirmation_score(e, beliefs)) for e in experiments]
    scored.sort(key=lambda x: -x[1])
    chosen = scored[0][0]
    return ExperimentSelection(
        selected_experiment_id=chosen.experiment_id,
        discrimination_score=compute_discrimination_score(chosen, beliefs),
        policy_rationale=f"Maximizes confirmation of leader (score={scored[0][1]:.3f})",
        alternatives_considered=[e.experiment_id for e in experiments if e != chosen],
    )


def select_discrimination(
    experiments: list[ExperimentCandidate],
    beliefs: dict[str, float],
) -> ExperimentSelection:
    """E3: ASAR — select experiment with highest discriminative power."""
    scored = [(e, compute_discrimination_score(e, beliefs)) for e in experiments]
    scored.sort(key=lambda x: -x[1])
    chosen = scored[0][0]
    return ExperimentSelection(
        selected_experiment_id=chosen.experiment_id,
        discrimination_score=scored[0][1],
        policy_rationale=f"Maximizes discrimination (JSD={scored[0][1]:.3f})",
        alternatives_considered=[e.experiment_id for e in experiments if e != chosen],
    )


def select_oracle(
    experiments: list[ExperimentCandidate],
    beliefs: dict[str, float],
    true_hypothesis_id: str,
) -> ExperimentSelection:
    """E5: Oracle — uses ground truth for upper bound. NEVER available to agents."""
    scored = [
        (e, compute_oracle_information_gain(e, beliefs, true_hypothesis_id))
        for e in experiments
    ]
    scored.sort(key=lambda x: -x[1])
    chosen = scored[0][0]
    return ExperimentSelection(
        selected_experiment_id=chosen.experiment_id,
        discrimination_score=compute_discrimination_score(chosen, beliefs),
        policy_rationale=f"Oracle: max true IG={scored[0][1]:.3f}",
        alternatives_considered=[e.experiment_id for e in experiments if e != chosen],
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _get_prediction_vector(
    experiment: ExperimentCandidate,
    hypothesis_id: str,
) -> dict[str, float]:
    """Get outcome probability distribution predicted by a hypothesis."""
    result: dict[str, float] = {}
    for pred in experiment.hypothesis_predictions:
        likelihood = pred.likelihoods.get(hypothesis_id, 0.0)
        result[pred.outcome_id] = likelihood
    return result


def _jensen_shannon_divergence(p: dict[str, float], q: dict[str, float]) -> float:
    """Compute JSD between two discrete distributions."""
    all_keys = set(p.keys()) | set(q.keys())
    eps = 1e-10

    # Normalize
    p_total = sum(p.values()) + eps
    q_total = sum(q.values()) + eps

    jsd = 0.0
    for key in all_keys:
        pk = p.get(key, 0) / p_total
        qk = q.get(key, 0) / q_total
        mk = (pk + qk) / 2

        if pk > eps:
            jsd += 0.5 * pk * math.log(pk / mk)
        if qk > eps:
            jsd += 0.5 * qk * math.log(qk / mk)

    return max(0.0, jsd)


def _entropy(probs: list[float]) -> float:
    """Compute Shannon entropy of a probability distribution."""
    total = sum(probs) + 1e-10
    h = 0.0
    for p in probs:
        if p > 1e-10:
            pp = p / total
            h -= pp * math.log(pp)
    return h
