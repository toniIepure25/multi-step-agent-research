"""
Capability predictor — builds empirical capability estimates from episode history.

Level 1: Empirical frequency baseline (mean success rate by task signature).
Level 2: Simple smoothed estimator with Laplace correction.
"""

from __future__ import annotations

from schemas.ree.self_model import CapabilityEstimate, EpisodeRecord


class CapabilityPredictor:
    """Estimates P(success | task, strategy, model) from historical data."""

    def __init__(self, *, prior_success: float = 0.5, prior_weight: int = 2) -> None:
        self._prior_success = prior_success
        self._prior_weight = prior_weight

    def estimate(
        self,
        records: list[EpisodeRecord],
        task_signature: str = "",
        strategy: str = "",
        model_provider: str = "",
    ) -> CapabilityEstimate:
        """Compute a smoothed capability estimate from matching records."""
        filtered = records
        if task_signature:
            filtered = [r for r in filtered if r.task_signature == task_signature]
        if strategy:
            filtered = [r for r in filtered if strategy in r.strategy_sequence]
        if model_provider:
            filtered = [r for r in filtered if r.model_provider == model_provider]

        n = len(filtered)
        if n == 0:
            return CapabilityEstimate(
                task_signature=task_signature or "unknown",
                strategy=strategy,
                model_provider=model_provider,
                estimated_success_rate=self._prior_success,
                sample_count=0,
            )

        successes = sum(r.success_actual for r in filtered)
        smoothed_rate = (successes + self._prior_weight * self._prior_success) / (n + self._prior_weight)

        std_err = (smoothed_rate * (1 - smoothed_rate) / max(1, n)) ** 0.5
        ci_lower = max(0.0, smoothed_rate - 1.96 * std_err)
        ci_upper = min(1.0, smoothed_rate + 1.96 * std_err)

        return CapabilityEstimate(
            task_signature=task_signature or "all",
            strategy=strategy,
            model_provider=model_provider,
            estimated_success_rate=smoothed_rate,
            sample_count=n,
            confidence_interval_lower=ci_lower,
            confidence_interval_upper=ci_upper,
        )

    def should_abstain(
        self,
        estimate: CapabilityEstimate,
        threshold: float = 0.3,
    ) -> bool:
        """Recommend abstention if estimated success rate is below threshold."""
        return estimate.estimated_success_rate < threshold

    def relative_advantage(
        self,
        records: list[EpisodeRecord],
        strategy_a: str,
        strategy_b: str,
        task_signature: str = "",
    ) -> float:
        """Compute the estimated advantage of strategy_a over strategy_b."""
        est_a = self.estimate(records, task_signature=task_signature, strategy=strategy_a)
        est_b = self.estimate(records, task_signature=task_signature, strategy=strategy_b)
        return est_a.estimated_success_rate - est_b.estimated_success_rate
