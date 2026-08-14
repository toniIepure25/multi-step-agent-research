"""
Baseline Scientific Policies for FalsificationBench.

B0 — PASSIVE UPDATE: No active falsification. Consumes evidence, updates beliefs.
B1 — CONFIRMATION SEEKER: Processes evidence but gives extra weight to supporting evidence.
B2 — RANDOM CHALLENGE: Randomly challenges hypotheses (controls for extra actions).
B3 — FALSIFICATION-FIRST: Current ASAR Stage 1 policy (ScientificController with enable_falsification=True).
B4 — ORACLE: Uses latent world knowledge for upper bound (never exposed to agents).

All baselines receive the same evidence rounds and budget.
Policies differ only in how they process evidence and whether they generate falsification proposals.
"""

from __future__ import annotations

from dataclasses import dataclass

from asar.scientific_discovery.belief_updater import BeliefUpdater
from asar.scientific_discovery.controller import EvidenceRound, ScientificController, ScientificEpisodeResult
from asar.scientific_discovery.controlled_worlds import ControlledWorld, WorldGroundTruth
from asar.scientific_discovery.state import (
    BeliefState,
    ConclusionType,
    EvidenceDirection,
    HypothesisStatus,
    ScientificState,
)


@dataclass
class PolicyResult:
    """Result of a policy run for comparison."""

    policy_name: str
    result: ScientificEpisodeResult
    world_id: str
    seed: int


def run_b0_passive(world: ControlledWorld, seed: int = 42) -> PolicyResult:
    """
    B0 — PASSIVE UPDATE.
    
    No falsification. Just consumes evidence and updates beliefs normally.
    This is the minimal scientific behavior: observe and update.
    """
    controller = ScientificController(enable_falsification=False)
    result = controller.run_episode(world.initial_state, world.evidence_rounds)
    return PolicyResult(
        policy_name="B0_passive",
        result=result,
        world_id=world.world_id,
        seed=seed,
    )


def run_b1_confirmation(world: ControlledWorld, seed: int = 42) -> PolicyResult:
    """
    B1 — CONFIRMATION SEEKER.

    Processes evidence but uses a belief updater that gives extra weight to
    supporting evidence relative to contradicting evidence. This simulates
    confirmation bias — a scientifically weak but common policy.
    """
    # Confirmation bias: support multiplier high, falsification multiplier low
    biased_updater = BeliefUpdater(
        base_update_strength=0.3,
        falsification_multiplier=0.5,  # Discounts contradictions
        reliability_weight=0.8,
        independence_weight=0.7,
        max_single_update=0.4,
        abandonment_threshold=0.05,  # Very reluctant to abandon
    )
    controller = ScientificController(
        belief_updater=biased_updater,
        enable_falsification=False,
    )
    result = controller.run_episode(world.initial_state, world.evidence_rounds)
    return PolicyResult(
        policy_name="B1_confirmation",
        result=result,
        world_id=world.world_id,
        seed=seed,
    )


def run_b2_random_challenge(world: ControlledWorld, seed: int = 42) -> PolicyResult:
    """
    B2 — RANDOM CHALLENGE.

    Uses the falsification engine but with standard (non-amplified) update weights.
    This controls for the additional computational actions of falsification
    without the scientific targeting.
    """
    # Standard updater (no falsification amplification)
    standard_updater = BeliefUpdater(
        base_update_strength=0.3,
        falsification_multiplier=1.0,  # No amplification for contradictions
        reliability_weight=0.8,
        independence_weight=0.7,
        max_single_update=0.4,
        abandonment_threshold=0.1,
    )
    controller = ScientificController(
        belief_updater=standard_updater,
        enable_falsification=True,  # Generates proposals but doesn't amplify
    )
    result = controller.run_episode(world.initial_state, world.evidence_rounds)
    return PolicyResult(
        policy_name="B2_random_challenge",
        result=result,
        world_id=world.world_id,
        seed=seed,
    )


def run_b3_zero(world: ControlledWorld, seed: int = 42) -> PolicyResult:
    """
    B3-ZERO — FALSIFICATION POLICY WITHOUT BOOST.

    Same falsification-first action policy (identifies target, proposes falsifier)
    but the recognition boost is disabled. This isolates:
    - B3-ZERO vs B0: Does the POLICY of seeking falsifiers add value?
    - B3 vs B3-ZERO: Does the update amplification add value beyond the policy?
    """
    controller = ScientificController(
        enable_falsification=True,
        enable_boost=False,
    )
    result = controller.run_episode(world.initial_state, world.evidence_rounds)
    return PolicyResult(
        policy_name="B3_zero",
        result=result,
        world_id=world.world_id,
        seed=seed,
    )


def run_b3_falsification_first(world: ControlledWorld, seed: int = 42) -> PolicyResult:
    """
    B3 — FALSIFICATION-FIRST (ASAR Stage 1 policy).

    Full falsification engine with amplified response to contradicting evidence.
    This is the policy under test.
    """
    controller = ScientificController(enable_falsification=True)
    result = controller.run_episode(world.initial_state, world.evidence_rounds)
    return PolicyResult(
        policy_name="B3_falsification_first",
        result=result,
        world_id=world.world_id,
        seed=seed,
    )


def run_b4_oracle(world: ControlledWorld, seed: int = 42) -> PolicyResult:
    """
    B4 — ORACLE.

    Uses world ground truth to set beliefs perfectly.
    This provides the upper bound on what's achievable.
    Never used as a fair comparison — only as ceiling.
    """
    gt = world.ground_truth
    state = world.initial_state

    # Oracle: immediately set correct hypothesis high, others low
    new_beliefs: dict[str, float] = {}
    for hid in state.ecology.hypotheses:
        if hid == gt.correct_hypothesis_id:
            new_beliefs[hid] = 0.95
        else:
            new_beliefs[hid] = 0.05

    # Build minimal result with oracle knowledge
    oracle_state = state.model_copy(update={
        "beliefs": BeliefState(beliefs=new_beliefs),
        "conclusion": ConclusionType.SUPPORTED if gt.correct_hypothesis_id else ConclusionType.UNDERDETERMINED,
    })

    # Still run through controller to get proper event structure
    # but with oracle-informed initial beliefs
    oracle_initial = state.model_copy(update={
        "beliefs": BeliefState(beliefs=new_beliefs),
    })
    controller = ScientificController(enable_falsification=True)
    result = controller.run_episode(oracle_initial, world.evidence_rounds)

    return PolicyResult(
        policy_name="B4_oracle",
        result=result,
        world_id=world.world_id,
        seed=seed,
    )


def run_all_policies(world: ControlledWorld, seed: int = 42) -> list[PolicyResult]:
    """Run all baseline policies on a single world."""
    return [
        run_b0_passive(world, seed),
        run_b1_confirmation(world, seed),
        run_b2_random_challenge(world, seed),
        run_b3_zero(world, seed),
        run_b3_falsification_first(world, seed),
        run_b4_oracle(world, seed),
    ]
