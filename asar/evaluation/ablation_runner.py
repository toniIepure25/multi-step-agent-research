"""
Ablation campaign runner — Phase 13.

Runs leave-one-out and additive ablation studies, prompt-only controls,
quality-compute Pareto frontier analysis, and scientific findings aggregation.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from asar.evaluation.benchmark_runner import BenchmarkRunner, BenchmarkRunResult
from asar.evaluation.scenario import AblationConfig, ScenarioSpec
from asar.evaluation.statistical import (
    ExperimentSummary,
    bootstrap_ci,
    paired_comparison,
    win_tie_loss,
)
from schemas.ree.epistemic_state import BudgetState


# ---------------------------------------------------------------
# Ablation campaign
# ---------------------------------------------------------------

@dataclass
class AblationResult:
    """Result of a single ablation condition across multiple scenarios."""
    condition_name: str
    mechanism_config: dict[str, bool]
    results: list[BenchmarkRunResult] = field(default_factory=list)

    @property
    def mean_tokens(self) -> float:
        tokens = [r.result.tokens_used for r in self.results]
        return sum(tokens) / len(tokens) if tokens else 0.0

    @property
    def mean_steps(self) -> float:
        steps = [r.result.steps_used for r in self.results]
        return sum(steps) / len(steps) if steps else 0.0

    @property
    def hypothesis_counts(self) -> list[int]:
        return [len(r.result.hypotheses) for r in self.results]


@dataclass
class AblationCampaignResult:
    """Complete ablation campaign across all conditions."""
    conditions: dict[str, AblationResult] = field(default_factory=dict)

    def comparisons(
        self,
        baseline: str = "full_ree",
        metric_fn: Any = None,
    ) -> list[dict[str, Any]]:
        """Generate pairwise comparisons against baseline."""
        if baseline not in self.conditions:
            return []
        base = self.conditions[baseline]
        if metric_fn is None:
            metric_fn = lambda r: r.result.steps_used

        comparisons = []
        for name, ablation in self.conditions.items():
            if name == baseline:
                continue
            n = min(len(base.results), len(ablation.results))
            if n == 0:
                continue
            vals_base = [metric_fn(r) for r in base.results[:n]]
            vals_abl = [metric_fn(r) for r in ablation.results[:n]]

            comp = paired_comparison(
                vals_base, vals_abl,
                label_a=baseline, label_b=name,
                metric="custom",
            )
            comparisons.append({
                "condition": name,
                "mean_diff": comp.mean_diff,
                "effect_size": comp.effect_size.cohens_d,
                "interpretation": comp.effect_size.interpretation,
                "ci_lower": comp.ci.lower,
                "ci_upper": comp.ci.upper,
                "n": n,
            })
        return comparisons


class AblationCampaignRunner:
    """Runs the complete ablation campaign."""

    def __init__(
        self,
        *,
        runner: BenchmarkRunner | None = None,
        budget: BudgetState | None = None,
    ) -> None:
        self._runner = runner or BenchmarkRunner()
        self._budget = budget or BudgetState(max_tokens=3000, max_steps=10)

    async def run_leave_one_out(
        self,
        scenarios: list[ScenarioSpec],
    ) -> AblationCampaignResult:
        """Stage A: leave-one-out ablation."""
        campaign = AblationCampaignResult()

        full_config = AblationConfig.full_ree()
        campaign.conditions["full_ree"] = await self._run_condition(
            "full_ree", full_config, scenarios,
        )

        for mechanism in AblationConfig.FULL_REE_MECHANISMS:
            config = AblationConfig.leave_one_out(mechanism)
            name = f"ree_no_{mechanism}"
            campaign.conditions[name] = await self._run_condition(
                name, config, scenarios,
            )

        return campaign

    async def run_additive(
        self,
        scenarios: list[ScenarioSpec],
    ) -> AblationCampaignResult:
        """Stage B: additive ablation."""
        campaign = AblationCampaignResult()

        core_config = AblationConfig.ree_core_only()
        campaign.conditions["ree_core"] = await self._run_condition(
            "ree_core", core_config, scenarios,
        )

        for name, config in AblationConfig.all_additive_configs().items():
            campaign.conditions[name] = await self._run_condition(
                name, config, scenarios,
            )

        return campaign

    async def _run_condition(
        self,
        name: str,
        config: dict[str, bool],
        scenarios: list[ScenarioSpec],
    ) -> AblationResult:
        result = AblationResult(condition_name=name, mechanism_config=config)
        for spec in scenarios:
            r = await self._runner.run_scenario(
                spec, architecture=name, ablation=config, budget=self._budget,
            )
            result.results.append(r)
        return result


# ---------------------------------------------------------------
# Quality-Compute Pareto Frontier
# ---------------------------------------------------------------

@dataclass(frozen=True)
class ParetoPoint:
    """A point on the quality-compute frontier."""
    architecture: str
    quality: float
    compute: float
    is_pareto_optimal: bool = False


def compute_pareto_frontier(
    points: list[ParetoPoint],
) -> list[ParetoPoint]:
    """Identify Pareto-optimal points (maximize quality, minimize compute)."""
    sorted_pts = sorted(points, key=lambda p: p.compute)
    pareto: list[ParetoPoint] = []
    max_quality = float("-inf")

    for pt in sorted_pts:
        if pt.quality >= max_quality:
            pareto.append(ParetoPoint(
                architecture=pt.architecture,
                quality=pt.quality,
                compute=pt.compute,
                is_pareto_optimal=True,
            ))
            max_quality = pt.quality

    return pareto


def build_pareto_data(
    results_by_arch: dict[str, list[BenchmarkRunResult]],
    *,
    quality_fn: Any = None,
    compute_fn: Any = None,
) -> list[ParetoPoint]:
    """Build Pareto frontier data from multi-architecture results."""
    if quality_fn is None:
        quality_fn = lambda r: len(r.result.hypotheses) + len(r.result.ignorance_items)
    if compute_fn is None:
        compute_fn = lambda r: r.result.tokens_used

    points = []
    for arch, results in results_by_arch.items():
        if not results:
            continue
        mean_q = sum(quality_fn(r) for r in results) / len(results)
        mean_c = sum(compute_fn(r) for r in results) / len(results)
        points.append(ParetoPoint(
            architecture=arch,
            quality=mean_q,
            compute=mean_c,
        ))

    pareto = compute_pareto_frontier(points)
    pareto_archs = {p.architecture for p in pareto}

    return [
        ParetoPoint(
            architecture=p.architecture,
            quality=p.quality,
            compute=p.compute,
            is_pareto_optimal=p.architecture in pareto_archs,
        )
        for p in points
    ]


# ---------------------------------------------------------------
# Prompt-only control
# ---------------------------------------------------------------

@dataclass
class PromptOnlyControl:
    """Simulates a mechanism via prompting only (no architectural support)."""
    mechanism: str
    prompt_suffix: str
    description: str

    @classmethod
    def ignorance_prompt(cls) -> "PromptOnlyControl":
        return cls(
            mechanism="ignorance_ledger",
            prompt_suffix="Before answering, list what you don't know that might affect the answer.",
            description="Prompt-only ignorance tracking",
        )

    @classmethod
    def hypothesis_prompt(cls) -> "PromptOnlyControl":
        return cls(
            mechanism="hypothesis_ecology",
            prompt_suffix="Consider at least 3 alternative explanations before committing to one.",
            description="Prompt-only hypothesis diversity",
        )

    @classmethod
    def ontology_prompt(cls) -> "PromptOnlyControl":
        return cls(
            mechanism="ontology_forge",
            prompt_suffix="Consider whether your conceptual framing might be wrong. Try an alternative framing.",
            description="Prompt-only ontology revision",
        )


# ---------------------------------------------------------------
# Hypothesis verdict aggregation
# ---------------------------------------------------------------

@dataclass
class HypothesisVerdict:
    """Verdict for a pre-registered hypothesis."""
    hypothesis_id: str
    claim: str
    status: str
    evidence_summary: str
    effect_size: float | None = None
    ci_lower: float | None = None
    ci_upper: float | None = None
    n_scenarios: int = 0
    methodological_notes: str = ""


VERDICT_OPTIONS = ("SUPPORTED", "PARTIALLY_SUPPORTED", "NOT_SUPPORTED", "INCONCLUSIVE")


def aggregate_verdicts(
    hypothesis_results: dict[str, dict[str, Any]],
) -> list[HypothesisVerdict]:
    """Aggregate experimental evidence into hypothesis verdicts."""
    verdicts = []
    for h_id, data in hypothesis_results.items():
        effect = data.get("effect_size", 0.0)
        n = data.get("n_scenarios", 0)
        ci_l = data.get("ci_lower", None)
        ci_u = data.get("ci_upper", None)

        if n < 5:
            status = "INCONCLUSIVE"
        elif effect is not None and abs(effect) > 0.5 and ci_l is not None and ci_l > 0:
            status = "SUPPORTED"
        elif effect is not None and abs(effect) > 0.2:
            status = "PARTIALLY_SUPPORTED"
        elif effect is not None and abs(effect) < 0.1:
            status = "NOT_SUPPORTED"
        else:
            status = "INCONCLUSIVE"

        verdicts.append(HypothesisVerdict(
            hypothesis_id=h_id,
            claim=data.get("claim", ""),
            status=status,
            evidence_summary=data.get("evidence_summary", ""),
            effect_size=effect,
            ci_lower=ci_l,
            ci_upper=ci_u,
            n_scenarios=n,
            methodological_notes=data.get("notes", ""),
        ))
    return verdicts
