"""
Tests for the empirical self model: tracker, calibration, and capability predictor.
"""

from __future__ import annotations

import pytest

from asar.self_model.tracker import EpisodeTracker
from asar.self_model.calibration import CalibrationAnalyzer
from asar.self_model.predictor import CapabilityPredictor
from schemas.ree.self_model import CalibrationPoint, EpisodeRecord


def _make_episode(
    episode_id: str = "ep_001",
    domain: str = "science",
    confidence: float = 0.7,
    success: float = 0.8,
    task_sig: str = "causal_reasoning",
    strategy: str = "retrieve_then_reason",
    tokens: int = 1000,
    failure_type: str | None = None,
) -> EpisodeRecord:
    return EpisodeRecord(
        episode_id=episode_id,
        task_signature=task_sig,
        domain=domain,
        confidence_predicted=confidence,
        success_actual=success,
        strategy_sequence=[strategy],
        total_tokens=tokens,
        failure_type=failure_type,
    )


class TestEpisodeTracker:
    def test_record_and_retrieve(self) -> None:
        tracker = EpisodeTracker()
        tracker.record(_make_episode())
        assert len(tracker) == 1

    def test_by_domain(self) -> None:
        tracker = EpisodeTracker()
        tracker.record(_make_episode("e1", domain="science"))
        tracker.record(_make_episode("e2", domain="history"))
        tracker.record(_make_episode("e3", domain="science"))
        assert len(tracker.by_domain("science")) == 2

    def test_calibration_points(self) -> None:
        tracker = EpisodeTracker()
        tracker.record(_make_episode("e1", confidence=0.9, success=1.0))
        tracker.record(_make_episode("e2", confidence=0.3, success=0.0))
        points = tracker.calibration_points()
        assert len(points) == 2
        assert points[0].predicted == 0.9

    def test_success_rate(self) -> None:
        tracker = EpisodeTracker()
        tracker.record(_make_episode("e1", success=0.8))
        tracker.record(_make_episode("e2", success=0.3))
        tracker.record(_make_episode("e3", success=0.9))
        assert tracker.success_rate(threshold=0.5) == pytest.approx(2.0 / 3)

    def test_failure_type_distribution(self) -> None:
        tracker = EpisodeTracker()
        tracker.record(_make_episode("e1", failure_type="retrieval_failed"))
        tracker.record(_make_episode("e2", failure_type="retrieval_failed"))
        tracker.record(_make_episode("e3", failure_type="hallucination"))
        dist = tracker.failure_type_distribution()
        assert dist["retrieval_failed"] == 2
        assert dist["hallucination"] == 1


class TestCalibrationAnalyzer:
    def test_brier_score_perfect(self) -> None:
        analyzer = CalibrationAnalyzer()
        points = [
            CalibrationPoint(predicted=1.0, actual=1.0),
            CalibrationPoint(predicted=0.0, actual=0.0),
        ]
        assert analyzer.brier_score(points) == pytest.approx(0.0)

    def test_brier_score_worst(self) -> None:
        analyzer = CalibrationAnalyzer()
        points = [
            CalibrationPoint(predicted=1.0, actual=0.0),
            CalibrationPoint(predicted=0.0, actual=1.0),
        ]
        assert analyzer.brier_score(points) == pytest.approx(1.0)

    def test_brier_score_empty(self) -> None:
        analyzer = CalibrationAnalyzer()
        assert analyzer.brier_score([]) == 0.0

    def test_ece_well_calibrated(self) -> None:
        analyzer = CalibrationAnalyzer()
        points = [CalibrationPoint(predicted=i / 10.0, actual=i / 10.0) for i in range(11)]
        ece = analyzer.expected_calibration_error(points, n_bins=5)
        assert ece < 0.15

    def test_ece_poorly_calibrated(self) -> None:
        analyzer = CalibrationAnalyzer()
        points = [CalibrationPoint(predicted=0.9, actual=0.1)] * 10
        ece = analyzer.expected_calibration_error(points, n_bins=5)
        assert ece > 0.5

    def test_calibration_curve_bins(self) -> None:
        analyzer = CalibrationAnalyzer()
        points = [
            CalibrationPoint(predicted=0.1, actual=0.0),
            CalibrationPoint(predicted=0.2, actual=0.1),
            CalibrationPoint(predicted=0.8, actual=0.9),
            CalibrationPoint(predicted=0.9, actual=1.0),
        ]
        bins = analyzer.calibration_curve(points, n_bins=5)
        assert len(bins) >= 2

    def test_self_model_calibration_error(self) -> None:
        analyzer = CalibrationAnalyzer()
        predicted = [0.8, 0.6, 0.9]
        realized = [0.7, 0.5, 0.8]
        smce = analyzer.self_model_calibration_error(predicted, realized)
        assert smce == pytest.approx(0.1)


class TestCapabilityPredictor:
    def test_estimate_with_data(self) -> None:
        predictor = CapabilityPredictor()
        records = [
            _make_episode(f"e{i}", success=0.8, task_sig="causal")
            for i in range(10)
        ]
        est = predictor.estimate(records, task_signature="causal")
        assert est.estimated_success_rate > 0.7
        assert est.sample_count == 10

    def test_estimate_no_data_returns_prior(self) -> None:
        predictor = CapabilityPredictor(prior_success=0.5)
        est = predictor.estimate([], task_signature="unknown")
        assert est.estimated_success_rate == pytest.approx(0.5)
        assert est.sample_count == 0

    def test_should_abstain(self) -> None:
        predictor = CapabilityPredictor()
        records = [_make_episode(f"e{i}", success=0.1) for i in range(20)]
        est = predictor.estimate(records)
        assert predictor.should_abstain(est, threshold=0.3)

    def test_should_not_abstain(self) -> None:
        predictor = CapabilityPredictor()
        records = [_make_episode(f"e{i}", success=0.9) for i in range(20)]
        est = predictor.estimate(records)
        assert not predictor.should_abstain(est, threshold=0.3)

    def test_relative_advantage(self) -> None:
        predictor = CapabilityPredictor()
        records = [
            _make_episode(f"a{i}", success=0.9, strategy="strategy_a")
            for i in range(10)
        ] + [
            _make_episode(f"b{i}", success=0.4, strategy="strategy_b")
            for i in range(10)
        ]
        advantage = predictor.relative_advantage(records, "strategy_a", "strategy_b")
        assert advantage > 0.3

    def test_confidence_interval_narrows_with_data(self) -> None:
        predictor = CapabilityPredictor()
        few = [_make_episode(f"e{i}", success=0.5) for i in range(3)]
        many = [_make_episode(f"e{i}", success=0.5) for i in range(100)]
        est_few = predictor.estimate(few)
        est_many = predictor.estimate(many)
        width_few = est_few.confidence_interval_upper - est_few.confidence_interval_lower
        width_many = est_many.confidence_interval_upper - est_many.confidence_interval_lower
        assert width_many < width_few
