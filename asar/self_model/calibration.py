"""
Calibration analyzer — computes Brier score, ECE, and calibration curves.

Compares predicted confidence against realized outcomes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from schemas.ree.self_model import CalibrationPoint


@dataclass(frozen=True)
class CalibrationBin:
    """A bin in a calibration curve."""

    bin_lower: float
    bin_upper: float
    mean_predicted: float
    mean_actual: float
    count: int


class CalibrationAnalyzer:
    """Computes calibration metrics from (predicted, actual) pairs."""

    def brier_score(self, points: list[CalibrationPoint]) -> float:
        """Compute Brier score: mean squared error between predicted and actual.

        Lower is better. Range [0, 1].
        """
        if not points:
            return 0.0
        return sum((p.predicted - p.actual) ** 2 for p in points) / len(points)

    def expected_calibration_error(
        self,
        points: list[CalibrationPoint],
        n_bins: int = 10,
    ) -> float:
        """Compute Expected Calibration Error (ECE).

        Weighted average of |mean_predicted - mean_actual| across bins.
        """
        if not points:
            return 0.0

        bins = self.calibration_curve(points, n_bins=n_bins)
        total = len(points)
        ece = sum(
            b.count * abs(b.mean_predicted - b.mean_actual)
            for b in bins
        ) / total
        return ece

    def calibration_curve(
        self,
        points: list[CalibrationPoint],
        n_bins: int = 10,
    ) -> list[CalibrationBin]:
        """Compute a binned calibration curve."""
        if not points:
            return []

        bin_width = 1.0 / n_bins
        bins: list[CalibrationBin] = []

        for i in range(n_bins):
            lower = i * bin_width
            upper = (i + 1) * bin_width
            in_bin = [p for p in points if lower <= p.predicted < upper or (i == n_bins - 1 and p.predicted == 1.0)]

            if in_bin:
                mean_pred = sum(p.predicted for p in in_bin) / len(in_bin)
                mean_actual = sum(p.actual for p in in_bin) / len(in_bin)
                bins.append(CalibrationBin(
                    bin_lower=lower,
                    bin_upper=upper,
                    mean_predicted=mean_pred,
                    mean_actual=mean_actual,
                    count=len(in_bin),
                ))

        return bins

    def self_model_calibration_error(
        self,
        predicted_competence: list[float],
        realized_competence: list[float],
    ) -> float:
        """Compare predicted competence against realized competence.

        Returns mean absolute error between predicted and realized competence.
        """
        if not predicted_competence or len(predicted_competence) != len(realized_competence):
            return 0.0
        return sum(
            abs(p - r) for p, r in zip(predicted_competence, realized_competence)
        ) / len(predicted_competence)
