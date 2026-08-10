"""
Statistical analysis utilities — Phase 10B.9.

Implements:
  - Holm correction for confirmatory hypothesis families
  - Benjamini-Hochberg FDR for exploratory ablation discovery
  - Effect size computation (Cohen's d, rank-biserial)
  - Bootstrap confidence intervals
  - Paired analysis
  - Multiple comparison policy
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EffectSize:
    """Standardized effect size with interpretation."""
    cohens_d: float
    interpretation: str

    @classmethod
    def from_paired(cls, diffs: list[float]) -> "EffectSize":
        if not diffs:
            return cls(cohens_d=0.0, interpretation="no data")
        mean_diff = sum(diffs) / len(diffs)
        if len(diffs) < 2:
            return cls(cohens_d=0.0, interpretation="insufficient data")
        var = sum((d - mean_diff) ** 2 for d in diffs) / (len(diffs) - 1)
        sd = math.sqrt(var) if var > 0 else 1e-10
        d = mean_diff / sd
        interpretation = _interpret_d(d)
        return cls(cohens_d=d, interpretation=interpretation)


def _interpret_d(d: float) -> str:
    ad = abs(d)
    if ad < 0.2:
        return "negligible"
    elif ad < 0.5:
        return "small"
    elif ad < 0.8:
        return "medium"
    else:
        return "large"


@dataclass(frozen=True)
class BootstrapCI:
    """Bootstrap confidence interval."""
    lower: float
    upper: float
    mean: float
    confidence_level: float


def bootstrap_ci(
    values: list[float],
    *,
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    seed: int = 42,
) -> BootstrapCI:
    """Compute bootstrap confidence interval for the mean."""
    import random
    rng = random.Random(seed)
    n = len(values)
    if n == 0:
        return BootstrapCI(lower=0.0, upper=0.0, mean=0.0, confidence_level=confidence)

    means = []
    for _ in range(n_bootstrap):
        sample = [rng.choice(values) for _ in range(n)]
        means.append(sum(sample) / n)

    means.sort()
    alpha = (1.0 - confidence) / 2.0
    lower_idx = max(0, int(math.floor(alpha * n_bootstrap)))
    upper_idx = min(n_bootstrap - 1, int(math.ceil((1.0 - alpha) * n_bootstrap)) - 1)

    return BootstrapCI(
        lower=means[lower_idx],
        upper=means[upper_idx],
        mean=sum(values) / n,
        confidence_level=confidence,
    )


@dataclass(frozen=True)
class ComparisonResult:
    """Result of comparing two conditions."""
    condition_a: str
    condition_b: str
    metric: str
    mean_a: float
    mean_b: float
    mean_diff: float
    effect_size: EffectSize
    ci: BootstrapCI
    n_a: int
    n_b: int
    p_value: float | None = None
    significant_after_correction: bool | None = None


# ---------------------------------------------------------------
# Multiple comparison corrections
# ---------------------------------------------------------------

def holm_correction(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    """Holm step-down correction for confirmatory hypothesis families.

    Returns list of booleans: True if hypothesis is rejected.
    """
    m = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    rejected = [False] * m

    for rank, (orig_idx, p) in enumerate(indexed):
        adjusted_alpha = alpha / (m - rank)
        if p <= adjusted_alpha:
            rejected[orig_idx] = True
        else:
            break

    return rejected


def benjamini_hochberg(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    """Benjamini-Hochberg FDR correction for exploratory discovery.

    Returns list of booleans: True if hypothesis is rejected.
    """
    m = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    rejected = [False] * m

    last_rejected = -1
    for rank, (orig_idx, p) in enumerate(indexed):
        threshold = alpha * (rank + 1) / m
        if p <= threshold:
            last_rejected = rank

    for rank in range(last_rejected + 1):
        orig_idx = indexed[rank][0]
        rejected[orig_idx] = True

    return rejected


# ---------------------------------------------------------------
# Paired analysis
# ---------------------------------------------------------------

def paired_comparison(
    values_a: list[float],
    values_b: list[float],
    *,
    label_a: str = "A",
    label_b: str = "B",
    metric: str = "quality",
) -> ComparisonResult:
    """Compute paired comparison with effect size and bootstrap CI."""
    n = min(len(values_a), len(values_b))
    if n == 0:
        return ComparisonResult(
            condition_a=label_a, condition_b=label_b, metric=metric,
            mean_a=0.0, mean_b=0.0, mean_diff=0.0,
            effect_size=EffectSize(0.0, "no data"),
            ci=BootstrapCI(0.0, 0.0, 0.0, 0.95),
            n_a=0, n_b=0,
        )

    diffs = [values_a[i] - values_b[i] for i in range(n)]
    mean_a = sum(values_a[:n]) / n
    mean_b = sum(values_b[:n]) / n
    mean_diff = sum(diffs) / n

    effect = EffectSize.from_paired(diffs)
    ci = bootstrap_ci(diffs)

    return ComparisonResult(
        condition_a=label_a, condition_b=label_b, metric=metric,
        mean_a=mean_a, mean_b=mean_b, mean_diff=mean_diff,
        effect_size=effect, ci=ci,
        n_a=n, n_b=n,
    )


# ---------------------------------------------------------------
# Win/tie/loss
# ---------------------------------------------------------------

def win_tie_loss(
    values_a: list[float],
    values_b: list[float],
    *,
    tolerance: float = 0.001,
) -> tuple[int, int, int]:
    """Compute win/tie/loss counts for paired comparisons."""
    n = min(len(values_a), len(values_b))
    wins = ties = losses = 0
    for i in range(n):
        diff = values_a[i] - values_b[i]
        if diff > tolerance:
            wins += 1
        elif diff < -tolerance:
            losses += 1
        else:
            ties += 1
    return wins, ties, losses


# ---------------------------------------------------------------
# Summary report
# ---------------------------------------------------------------

@dataclass
class ExperimentSummary:
    """Summary statistics for an experiment condition."""
    condition: str
    metric: str
    n: int
    mean: float
    median: float
    std: float
    ci_lower: float
    ci_upper: float

    @classmethod
    def from_values(
        cls,
        condition: str,
        metric: str,
        values: list[float],
    ) -> "ExperimentSummary":
        n = len(values)
        if n == 0:
            return cls(condition=condition, metric=metric, n=0,
                       mean=0, median=0, std=0, ci_lower=0, ci_upper=0)
        sorted_v = sorted(values)
        mean = sum(values) / n
        median = sorted_v[n // 2] if n % 2 == 1 else (sorted_v[n//2 - 1] + sorted_v[n//2]) / 2
        var = sum((v - mean) ** 2 for v in values) / max(1, n - 1)
        std = math.sqrt(var)
        ci = bootstrap_ci(values)
        return cls(
            condition=condition, metric=metric, n=n,
            mean=mean, median=median, std=std,
            ci_lower=ci.lower, ci_upper=ci.upper,
        )
