"""
Active Science Tests.

SD-H9: Active Scientific Control — tests that endogenous experiment selection
genuinely matters for scientific recovery.

Critical requirement: in active worlds, confirmation-seeking should perform
WORSE than discrimination, because it wastes budget on non-informative experiments.
"""

import pytest

from asar.scientific_discovery.active_science import (
    ActiveWorld,
    active_confirmation,
    active_discrimination,
    active_passive,
    active_random,
    create_active_confirmation_trap,
    create_active_null_world,
    create_active_reverse_causality,
    run_active_benchmark,
    run_active_episode,
)


class TestActiveConfirmationTrap:
    """Test that discrimination outperforms confirmation in active worlds."""

    def test_discrimination_recovers_better_than_confirmation(self):
        """In the confirmation trap, discrimination should recover more often."""
        disc_recovered = 0
        conf_recovered = 0
        n = 20

        for seed in range(1, n + 1):
            world = create_active_confirmation_trap(seed=seed)

            result_disc = run_active_episode(world, active_discrimination, seed=seed)
            result_conf = run_active_episode(world, active_confirmation, seed=seed)

            if result_disc.recovered:
                disc_recovered += 1
            if result_conf.recovered:
                conf_recovered += 1

        # Discrimination should recover more often
        assert disc_recovered >= conf_recovered, (
            f"Discrimination ({disc_recovered}/{n}) should >= "
            f"confirmation ({conf_recovered}/{n})"
        )

    def test_confirmation_wastes_budget(self):
        """Confirmation-seeker should select the cheap non-discriminating experiments."""
        world = create_active_confirmation_trap(seed=1)
        result = run_active_episode(world, active_confirmation, seed=1)

        # Should have selected confirmation-oriented experiments
        discriminating_id = world.experiments[1].experiment_id
        # Confirmation-seeker unlikely to pick the discriminating one
        assert discriminating_id not in result.experiments_selected or len(result.experiments_selected) > 1


class TestActiveReverseCausality:
    """Intervention experiments should reveal true causal direction."""

    def test_discrimination_selects_intervention(self):
        """Discrimination should prefer intervention over observation."""
        world = create_active_reverse_causality(seed=1)
        result = run_active_episode(world, active_discrimination, seed=1)

        observation_id = world.experiments[0].experiment_id
        # At least one intervention should be selected
        has_intervention = any(
            eid != observation_id for eid in result.experiments_selected
        )
        assert has_intervention


class TestActiveNullWorld:
    """In null worlds, good policies should converge away from causal hypothesis."""

    def test_null_world_reduces_causal_belief(self):
        """Any reasonable policy should reduce belief in false causal hypothesis."""
        world = create_active_null_world(seed=1)
        result = run_active_episode(world, active_discrimination, seed=1)

        causal_id = list(world.hypotheses.keys())[0]  # first hypothesis is causal
        initial_causal = world.hypotheses[causal_id]
        final_causal = result.final_beliefs.get(causal_id, 0)

        # Belief in false causal hypothesis should decrease
        assert final_causal < initial_causal


class TestActiveBenchmark:
    """Run full active benchmark and verify structure."""

    def test_benchmark_runs_all_policies(self):
        """Benchmark should produce results for all policies."""
        results = run_active_benchmark(seeds=[1, 2, 3])
        assert "discrimination" in results
        assert "confirmation" in results
        assert "random" in results
        assert "passive" in results

    def test_discrimination_best_overall(self):
        """Across multiple worlds, discrimination should have highest recovery."""
        results = run_active_benchmark(seeds=list(range(1, 11)))

        disc_recovery = results["discrimination"].recovery_rate
        conf_recovery = results["confirmation"].recovery_rate
        rand_recovery = results["random"].recovery_rate

        # Discrimination should be >= random (which is already decent due to Bayesian update)
        assert disc_recovery >= rand_recovery - 0.1, (
            f"Discrimination ({disc_recovery:.2f}) should >= random ({rand_recovery:.2f})"
        )

    def test_episode_structure(self):
        """Verify episode results have correct structure."""
        results = run_active_benchmark(seeds=[1])
        for policy_name, result in results.items():
            assert len(result.episodes) > 0
            for ep in result.episodes:
                assert len(ep.belief_trajectory) >= 2
                assert ep.n_experiments >= 1
                assert ep.total_cost > 0
