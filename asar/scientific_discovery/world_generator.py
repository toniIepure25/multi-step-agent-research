"""
Stage 3D — Distributional World Generator.

Generates heterogeneous scientific decision problems from parameterized
distributions rather than hand-authored templates. This creates hundreds
of diverse worlds for robust benchmarking.

Frozen hyperparameters define the generator. Agent never sees latent structure.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any

from asar.scientific_discovery.experiment_design import (
    ExperimentCandidate,
    OutcomeLikelihoodByHypothesis,
    compute_discrimination_score,
    compute_approx_eig,
    compute_oracle_information_gain,
)
from asar.scientific_discovery.experiment_worlds import ExperimentWorld


@dataclass
class WorldGeneratorConfig:
    """Frozen hyperparameters for the distributional world generator."""

    n_hypotheses_range: tuple[int, int] = (3, 8)
    n_experiments_range: tuple[int, int] = (3, 10)
    n_outcomes_range: tuple[int, int] = (2, 4)
    prior_concentration: float = 1.0  # Dirichlet concentration (lower = more skewed)
    prediction_noise: float = 0.1  # How noisy predictions are
    cost_range: tuple[float, float] = (0.5, 3.0)
    overlap_range: tuple[float, float] = (0.1, 0.8)  # Prediction overlap between hypotheses


@dataclass
class GeneratedWorldMetadata:
    """Evaluator-side metadata about a generated world (not visible to agent)."""

    world_id: str
    seed: int
    n_hypotheses: int
    n_experiments: int
    prior_entropy: float
    min_pairwise_divergence: float
    max_pairwise_divergence: float
    oracle_action_margin: float  # Value(best) - Value(second_best)
    jsd_oracle_agreement: bool  # Does JSD rank == oracle rank for top experiment?
    difficulty_score: float  # Composite difficulty
    valid: bool = True
    rejection_reason: str = ""


def generate_world(
    seed: int,
    config: WorldGeneratorConfig | None = None,
) -> tuple[ExperimentWorld, GeneratedWorldMetadata]:
    """
    Generate a single random scientific decision problem.

    Returns (world, metadata). Metadata includes evaluator-only diagnostics.
    """
    if config is None:
        config = WorldGeneratorConfig()

    rng = random.Random(seed)

    # Sample world dimensions
    n_hyp = rng.randint(*config.n_hypotheses_range)
    n_exp = rng.randint(*config.n_experiments_range)

    # Generate hypotheses with Dirichlet-like prior
    raw_priors = [rng.gammavariate(config.prior_concentration, 1.0) for _ in range(n_hyp)]
    total = sum(raw_priors)
    hypothesis_ids = [f"h_{seed}_{i}" for i in range(n_hyp)]
    beliefs = {hid: p / total for hid, p in zip(hypothesis_ids, raw_priors)}

    # Choose true hypothesis (weighted by prior — realistic that true hypothesis has moderate support)
    true_idx = rng.choices(range(n_hyp), weights=raw_priors, k=1)[0]
    true_hypothesis_id = hypothesis_ids[true_idx]

    # Generate experiments
    experiments = []
    true_outcomes = {}

    for e_idx in range(n_exp):
        n_outcomes = rng.randint(*config.n_outcomes_range)
        outcome_ids = [f"o_{seed}_{e_idx}_{j}" for j in range(n_outcomes)]
        cost = rng.uniform(*config.cost_range)

        # Generate prediction distributions for each hypothesis
        predictions = []
        for o_idx, oid in enumerate(outcome_ids):
            likelihoods = {}
            for h_idx, hid in enumerate(hypothesis_ids):
                # Base prediction with controlled overlap
                overlap = rng.uniform(*config.overlap_range)
                if h_idx == 0:
                    # First hypothesis gets a "base" prediction
                    base_p = rng.random()
                    likelihoods[hid] = max(0.01, min(0.99, base_p + rng.gauss(0, config.prediction_noise)))
                else:
                    # Other hypotheses: mix of overlap with first and independent signal
                    base_p = likelihoods[hypothesis_ids[0]]
                    independent = rng.random()
                    mixed = overlap * base_p + (1 - overlap) * independent
                    likelihoods[hid] = max(0.01, min(0.99, mixed + rng.gauss(0, config.prediction_noise)))

            predictions.append(OutcomeLikelihoodByHypothesis(
                outcome_id=oid, likelihoods=likelihoods
            ))

        # Normalize likelihoods per hypothesis (ensure they sum to ~1 across outcomes)
        for hid in hypothesis_ids:
            total_h = sum(p.likelihoods.get(hid, 0.01) for p in predictions)
            if total_h > 0:
                for p in predictions:
                    if hid in p.likelihoods:
                        p.likelihoods[hid] /= total_h

        # Determine true outcome (sample from true hypothesis's distribution)
        true_probs = [p.likelihoods.get(true_hypothesis_id, 1.0 / n_outcomes) for p in predictions]
        total_tp = sum(true_probs)
        true_probs_norm = [tp / total_tp for tp in true_probs]
        true_outcome_idx = rng.choices(range(n_outcomes), weights=true_probs_norm, k=1)[0]

        exp_id = f"e_{seed}_{e_idx}"
        experiments.append(ExperimentCandidate(
            experiment_id=exp_id,
            description=f"Experiment {e_idx} in world {seed}",
            cost=cost,
            possible_outcomes=outcome_ids,
            hypothesis_predictions=predictions,
        ))
        true_outcomes[exp_id] = outcome_ids[true_outcome_idx]

    # Build world
    world = ExperimentWorld(
        world_id=f"gen_world_{seed}",
        world_type="distributional",
        description=f"Generated world (seed={seed}, H={n_hyp}, E={n_exp})",
        hypotheses=beliefs,
        experiments=experiments,
        true_hypothesis_id=true_hypothesis_id,
        true_outcomes=true_outcomes,
    )

    # Compute metadata
    prior_entropy = -sum(p * math.log(p + 1e-10) for p in beliefs.values())

    # Pairwise divergence between hypothesis predictions
    from asar.scientific_discovery.experiment_design import _get_prediction_vector, _jensen_shannon_divergence
    all_divs = []
    for exp in experiments:
        for i, h1 in enumerate(hypothesis_ids):
            for h2 in hypothesis_ids[i + 1:]:
                p1 = _get_prediction_vector(exp, h1)
                p2 = _get_prediction_vector(exp, h2)
                if p1 and p2:
                    all_divs.append(_jensen_shannon_divergence(p1, p2))

    min_div = min(all_divs) if all_divs else 0.0
    max_div = max(all_divs) if all_divs else 0.0

    # Oracle action margin
    oracle_values = [
        compute_oracle_information_gain(exp, beliefs, true_hypothesis_id)
        for exp in experiments
    ]
    oracle_values_sorted = sorted(oracle_values, reverse=True)
    oracle_margin = (oracle_values_sorted[0] - oracle_values_sorted[1]) if len(oracle_values_sorted) >= 2 else 0.0

    # JSD-Oracle agreement
    jsd_values = [compute_discrimination_score(exp, beliefs) for exp in experiments]
    oracle_best_idx = oracle_values.index(max(oracle_values))
    jsd_best_idx = jsd_values.index(max(jsd_values))
    jsd_oracle_agree = (oracle_best_idx == jsd_best_idx)

    # Difficulty: higher when margin is low, overlap is high, and divergence is low
    difficulty = (1.0 - oracle_margin) * (1.0 - max_div + min_div) * (1.0 + prior_entropy / math.log(n_hyp + 1))

    metadata = GeneratedWorldMetadata(
        world_id=world.world_id,
        seed=seed,
        n_hypotheses=n_hyp,
        n_experiments=n_exp,
        prior_entropy=prior_entropy,
        min_pairwise_divergence=min_div,
        max_pairwise_divergence=max_div,
        oracle_action_margin=oracle_margin,
        jsd_oracle_agreement=jsd_oracle_agree,
        difficulty_score=difficulty,
    )

    return world, metadata


def validate_world(world: ExperimentWorld) -> tuple[bool, str]:
    """Check if a generated world is mathematically valid."""
    # Check probabilities sum reasonably
    for exp in world.experiments:
        for hid in world.hypotheses:
            preds = [p.likelihoods.get(hid, 0) for p in exp.hypothesis_predictions]
            total = sum(preds)
            if total < 0.5 or total > 2.0:
                return False, f"Prediction sum {total:.2f} for {hid} in {exp.experiment_id}"

    # Check no degenerate duplicates
    h_ids = list(world.hypotheses.keys())
    if len(set(h_ids)) != len(h_ids):
        return False, "Duplicate hypothesis IDs"

    # Check at least one valid observation exists
    if not world.experiments:
        return False, "No experiments"

    # Check true hypothesis exists
    if world.true_hypothesis_id not in world.hypotheses:
        return False, "True hypothesis not in belief set"

    return True, ""


def generate_benchmark_worlds(
    n_worlds: int,
    seed_offset: int = 1000,
    config: WorldGeneratorConfig | None = None,
) -> list[tuple[ExperimentWorld, GeneratedWorldMetadata]]:
    """Generate N valid worlds from the distributional generator."""
    results = []
    seed = seed_offset
    attempts = 0
    max_attempts = n_worlds * 3

    while len(results) < n_worlds and attempts < max_attempts:
        world, meta = generate_world(seed, config)
        valid, reason = validate_world(world)
        if valid:
            results.append((world, meta))
        else:
            meta.valid = False
            meta.rejection_reason = reason
        seed += 1
        attempts += 1

    return results
