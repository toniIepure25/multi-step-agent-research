"""
Tests for statistical analysis utilities — Phase 10B.9.
"""

from asar.evaluation.statistical import (
    EffectSize,
    ExperimentSummary,
    bootstrap_ci,
    benjamini_hochberg,
    holm_correction,
    paired_comparison,
    win_tie_loss,
)


class TestHolmCorrection:
    def test_no_rejections(self):
        p_values = [0.5, 0.6, 0.7]
        rejected = holm_correction(p_values, alpha=0.05)
        assert not any(rejected)

    def test_all_rejected(self):
        p_values = [0.001, 0.002, 0.003]
        rejected = holm_correction(p_values, alpha=0.05)
        assert all(rejected)

    def test_partial_rejection(self):
        p_values = [0.01, 0.02, 0.5]
        rejected = holm_correction(p_values, alpha=0.05)
        assert rejected[0] is True
        assert rejected[1] is True
        assert rejected[2] is False

    def test_single_hypothesis(self):
        rejected = holm_correction([0.03], alpha=0.05)
        assert rejected == [True]

    def test_ordering_matters(self):
        rejected = holm_correction([0.04, 0.01], alpha=0.05)
        assert rejected[1] is True


class TestBenjaminiHochberg:
    def test_no_rejections(self):
        p_values = [0.5, 0.6, 0.7]
        rejected = benjamini_hochberg(p_values, alpha=0.05)
        assert not any(rejected)

    def test_all_rejected(self):
        p_values = [0.001, 0.002, 0.003]
        rejected = benjamini_hochberg(p_values, alpha=0.05)
        assert all(rejected)

    def test_fdr_more_permissive_than_holm(self):
        p_values = [0.01, 0.02, 0.04, 0.06, 0.10]
        holm_r = holm_correction(p_values, alpha=0.10)
        bh_r = benjamini_hochberg(p_values, alpha=0.10)
        assert sum(bh_r) >= sum(holm_r)


class TestBootstrapCI:
    def test_contains_mean(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        ci = bootstrap_ci(values, confidence=0.95)
        assert ci.lower <= ci.mean <= ci.upper

    def test_empty_values(self):
        ci = bootstrap_ci([])
        assert ci.mean == 0.0

    def test_constant_values(self):
        ci = bootstrap_ci([5.0] * 10)
        assert ci.lower == 5.0
        assert ci.upper == 5.0


class TestEffectSize:
    def test_zero_effect(self):
        es = EffectSize.from_paired([0.0, 0.0, 0.0])
        assert es.interpretation == "negligible"

    def test_large_effect(self):
        es = EffectSize.from_paired([10.0, 10.0, 10.0, 10.0])
        assert es.interpretation == "large"


class TestPairedComparison:
    def test_basic_comparison(self):
        a = [0.8, 0.9, 0.7, 0.85]
        b = [0.5, 0.6, 0.4, 0.55]
        result = paired_comparison(a, b, label_a="REE", label_b="legacy")
        assert result.mean_diff > 0
        assert result.effect_size.cohens_d > 0
        assert result.n_a == 4

    def test_empty_comparison(self):
        result = paired_comparison([], [])
        assert result.n_a == 0


class TestWinTieLoss:
    def test_all_wins(self):
        w, t, l = win_tie_loss([1.0, 2.0, 3.0], [0.5, 1.0, 1.5])
        assert w == 3 and t == 0 and l == 0

    def test_ties(self):
        w, t, l = win_tie_loss([1.0, 1.0], [1.0, 1.0])
        assert t == 2

    def test_mixed(self):
        w, t, l = win_tie_loss([1.0, 0.5, 1.0], [0.5, 1.0, 1.0])
        assert w == 1 and l == 1 and t == 1


class TestExperimentSummary:
    def test_from_values(self):
        s = ExperimentSummary.from_values("REE", "quality", [0.7, 0.8, 0.9])
        assert s.n == 3
        assert 0.7 <= s.mean <= 0.9
        assert s.std > 0

    def test_empty_values(self):
        s = ExperimentSummary.from_values("REE", "quality", [])
        assert s.n == 0
