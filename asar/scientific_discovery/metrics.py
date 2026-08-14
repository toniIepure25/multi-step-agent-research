"""
Scientific Self-Correction Metrics for FalsificationBench.

These metrics evaluate the PROCESS quality of scientific reasoning,
not just the final answer.
"""

from __future__ import annotations

from dataclasses import dataclass

from asar.scientific_discovery.controller import ScientificEpisodeResult
from asar.scientific_discovery.controlled_worlds import ControlledWorld, WorldGroundTruth
from asar.scientific_discovery.state import ConclusionType


@dataclass
class BenchmarkMetrics:
    """Complete metric vector for a single episode evaluation."""

    # Primary metrics
    refutation_sensitivity: float
    irrelevant_perturbation_robustness: float
    recovery_accuracy: float
    abandonment_latency: int
    theory_stickiness: float

    # Derived
    conclusion_correct: bool
    world_type: str
    world_id: str


def compute_refutation_sensitivity(
    belief_trajectory: list[dict[str, float]],
    target_hypothesis_id: str,
    decisive_round: int,
) -> float:
    """
    RS = P_before(H) - P_after_decisive_refutation(H)

    Higher is better when refutation is valid.
    Measures responsiveness to falsification.
    """
    if decisive_round < 0 or decisive_round >= len(belief_trajectory) - 1:
        return 0.0

    before = belief_trajectory[decisive_round].get(target_hypothesis_id, 0.5)
    after = belief_trajectory[decisive_round + 1].get(target_hypothesis_id, 0.5)

    return max(0.0, before - after)


def compute_irrelevant_perturbation_robustness(
    belief_before: dict[str, float],
    belief_after: dict[str, float],
) -> float:
    """
    IPR = 1 - max|P_before(H) - P_after_irrelevant(H)| over all H

    Higher is better. Measures stability under noise.
    """
    if not belief_before or not belief_after:
        return 1.0

    max_change = 0.0
    for hid in belief_before:
        if hid in belief_after:
            change = abs(belief_before[hid] - belief_after[hid])
            max_change = max(max_change, change)

    return 1.0 - max_change


def compute_recovery_accuracy(
    final_beliefs: dict[str, float],
    correct_hypothesis_id: str | None,
) -> float:
    """
    Does the system's final ranking match ground truth?

    Returns 1.0 if correct hypothesis is top-ranked, 0.0 otherwise.
    For null worlds (no correct hypothesis), returns 1.0 if all beliefs are low.
    """
    if correct_hypothesis_id is None:
        # Null/non-identifiable world — correct if no hypothesis dominates
        if not final_beliefs:
            return 1.0
        max_belief = max(final_beliefs.values())
        return 1.0 if max_belief < 0.6 else 0.0

    if correct_hypothesis_id not in final_beliefs:
        return 0.0

    correct_belief = final_beliefs[correct_hypothesis_id]
    top_belief = max(final_beliefs.values())

    return 1.0 if correct_belief >= top_belief else 0.0


def compute_abandonment_latency(
    belief_trajectory: list[dict[str, float]],
    target_hypothesis_id: str,
    decisive_round: int,
    abandonment_threshold: float = 0.1,
) -> int:
    """
    Number of evidence rounds after decisive falsifier before abandoning.

    Lower is better (0 = ideal immediate abandonment).
    Returns -1 if never abandoned.
    """
    if decisive_round is None or decisive_round < 0:
        return -1

    for i in range(decisive_round + 1, len(belief_trajectory)):
        belief = belief_trajectory[i].get(target_hypothesis_id, 0.5)
        if belief <= abandonment_threshold:
            return i - decisive_round - 1

    return -1  # Never abandoned


def compute_theory_stickiness(
    final_beliefs: dict[str, float],
    refuted_hypothesis_id: str,
    ground_truth_belief: float = 0.0,
) -> float:
    """
    Excess probability retained on refuted hypothesis.

    TS = P_final(H_refuted) - P_ground_truth(H_refuted)

    Lower is better (0 = no stickiness).
    """
    actual = final_beliefs.get(refuted_hypothesis_id, 0.0)
    return max(0.0, actual - ground_truth_belief)


def evaluate_episode(
    result: ScientificEpisodeResult,
    world: ControlledWorld,
) -> BenchmarkMetrics:
    """Compute all metrics for a completed episode against ground truth."""
    gt = world.ground_truth
    trajectory = result.belief_trajectory
    final_beliefs = trajectory[-1] if trajectory else {}

    # Determine which hypothesis was wrong (for worlds with a correct answer)
    wrong_hypothesis_id = None
    if gt.correct_hypothesis_id:
        for hid in final_beliefs:
            if hid != gt.correct_hypothesis_id:
                wrong_hypothesis_id = hid
                break

    # Refutation sensitivity
    rs = 0.0
    if gt.decisive_round is not None and wrong_hypothesis_id:
        rs = compute_refutation_sensitivity(
            trajectory, wrong_hypothesis_id, gt.decisive_round
        )

    # IPR (compare first two rounds if non-decisive)
    ipr = 1.0
    if len(trajectory) >= 2 and (gt.decisive_round is None or gt.decisive_round > 0):
        ipr = compute_irrelevant_perturbation_robustness(trajectory[0], trajectory[1])

    # Recovery accuracy
    ra = compute_recovery_accuracy(final_beliefs, gt.correct_hypothesis_id)

    # Abandonment latency
    al = -1
    if wrong_hypothesis_id and gt.decisive_round is not None:
        al = compute_abandonment_latency(
            trajectory, wrong_hypothesis_id, gt.decisive_round
        )

    # Theory stickiness
    ts = 0.0
    if wrong_hypothesis_id:
        ts = compute_theory_stickiness(final_beliefs, wrong_hypothesis_id)

    # Conclusion correctness
    conclusion_correct = _check_conclusion_correct(result.conclusion, gt)

    return BenchmarkMetrics(
        refutation_sensitivity=rs,
        irrelevant_perturbation_robustness=ipr,
        recovery_accuracy=ra,
        abandonment_latency=al,
        theory_stickiness=ts,
        conclusion_correct=conclusion_correct,
        world_type=gt.world_type,
        world_id=world.world_id,
    )


def _check_conclusion_correct(
    actual: ConclusionType,
    ground_truth: WorldGroundTruth,
) -> bool:
    """Check if the system's conclusion matches expected."""
    expected = ground_truth.expected_conclusion

    if expected == "supported":
        return actual == ConclusionType.SUPPORTED
    elif expected == "refuted":
        return actual == ConclusionType.REFUTED
    elif expected == "not_identifiable":
        return actual in (ConclusionType.NOT_IDENTIFIABLE, ConclusionType.ABSTAIN, ConclusionType.NEEDS_EXPERIMENT)
    elif expected == "underdetermined":
        return actual == ConclusionType.UNDERDETERMINED
    else:
        return False
