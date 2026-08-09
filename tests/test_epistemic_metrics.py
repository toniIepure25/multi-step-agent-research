"""
Tests for epistemic metrics computation.
"""

from __future__ import annotations

import pytest

from asar.evaluation.epistemic_metrics import EpistemicMetrics


class TestEpistemicMetrics:
    def test_ignorance_foresight_all_anticipated(self) -> None:
        m = EpistemicMetrics()
        score = m.ignorance_foresight_score(
            anticipated_failure_causes=["source_bias", "missing_data"],
            actual_failure_causes=["source_bias", "missing_data"],
        )
        assert score == pytest.approx(1.0)

    def test_ignorance_foresight_none_anticipated(self) -> None:
        m = EpistemicMetrics()
        score = m.ignorance_foresight_score(
            anticipated_failure_causes=[],
            actual_failure_causes=["source_bias", "missing_data"],
        )
        assert score == pytest.approx(0.0)

    def test_ignorance_foresight_partial(self) -> None:
        m = EpistemicMetrics()
        score = m.ignorance_foresight_score(
            anticipated_failure_causes=["source_bias"],
            actual_failure_causes=["source_bias", "missing_data"],
        )
        assert score == pytest.approx(0.5)

    def test_ignorance_foresight_no_failures(self) -> None:
        m = EpistemicMetrics()
        assert m.ignorance_foresight_score(["a"], []) == 1.0

    def test_ignorance_foresight_severity_weighted(self) -> None:
        m = EpistemicMetrics()
        score = m.ignorance_foresight_score(
            anticipated_failure_causes=["critical"],
            actual_failure_causes=["critical", "minor"],
            severity_weights={"critical": 10.0, "minor": 1.0},
        )
        assert score > 0.8

    def test_disconfirmation_yield(self) -> None:
        m = EpistemicMetrics()
        yield_val = m.disconfirmation_yield(
            hypotheses_attacked=5,
            hypotheses_rejected=2,
            attack_compute_tokens=4000,
        )
        assert yield_val == pytest.approx(0.5)

    def test_belief_revision_quality_perfect(self) -> None:
        m = EpistemicMetrics()
        revisions = [
            (0.2, 0.8, True),
            (-0.3, 0.7, False),
        ]
        assert m.belief_revision_quality(revisions) == pytest.approx(1.0)

    def test_belief_revision_quality_poor(self) -> None:
        m = EpistemicMetrics()
        revisions = [
            (-0.2, 0.8, True),
            (0.3, 0.7, False),
        ]
        assert m.belief_revision_quality(revisions) == pytest.approx(0.0)

    def test_research_efficiency(self) -> None:
        m = EpistemicMetrics()
        eff = m.research_efficiency(quality_score=0.8, total_tokens=4000)
        assert eff == pytest.approx(0.2)

    def test_paradigm_revision_score_full(self) -> None:
        m = EpistemicMetrics()
        score = m.paradigm_revision_score(
            dominant_hypothesis_abandoned=True,
            new_hypothesis_adopted=True,
            evidence_justified=True,
        )
        assert score == pytest.approx(1.0)

    def test_compute_all(self) -> None:
        m = EpistemicMetrics()
        result = m.compute_all(
            brier_score=0.15,
            ece=0.08,
            anticipated_failures=["a"],
            actual_failures=["a", "b"],
            mpr=0.7,
            total_tokens=5000,
            total_steps=10,
        )
        assert result.brier_score == 0.15
        assert result.ignorance_foresight_score == pytest.approx(0.5)
        assert result.total_tokens == 5000
        d = result.to_dict()
        assert "brier_score" in d
