"""
Scenario runner — executes controlled benchmark scenarios.

Supports:
  - Deterministic scenario generation from seeds
  - Development / held-out test split with leakage prevention
  - Equal-budget comparisons across architectures
  - Ablation configuration via ExperimentManifest
  - Raw artifact persistence
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScenarioSpec:
    """A single benchmark scenario specification."""

    scenario_id: str
    family: str
    question: str
    ground_truth: str | None = None
    ground_truth_metadata: dict[str, Any] = field(default_factory=dict)
    domain: str = "general"
    difficulty: str = "medium"
    tags: tuple[str, ...] = ()
    seed: int = 0
    split: str = "dev"

    evidence_pool: tuple[dict[str, Any], ...] = ()
    hidden_variables: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "family": self.family,
            "question": self.question,
            "ground_truth": self.ground_truth,
            "ground_truth_metadata": self.ground_truth_metadata,
            "domain": self.domain,
            "difficulty": self.difficulty,
            "tags": list(self.tags),
            "seed": self.seed,
            "split": self.split,
        }


@dataclass
class ScenarioResult:
    """Result of running one scenario through one architecture."""

    scenario_id: str
    architecture: str
    experiment_id: str

    answer: str = ""
    claims: list[dict[str, Any]] = field(default_factory=list)
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    ignorance_items: list[dict[str, Any]] = field(default_factory=list)

    tokens_used: int = 0
    steps_used: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0

    quality_score: float | None = None
    ground_truth_match: bool | None = None

    raw_events: list[dict[str, Any]] = field(default_factory=list)
    raw_state: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "architecture": self.architecture,
            "experiment_id": self.experiment_id,
            "answer": self.answer,
            "claims_count": len(self.claims),
            "hypotheses_count": len(self.hypotheses),
            "ignorance_count": len(self.ignorance_items),
            "tokens_used": self.tokens_used,
            "steps_used": self.steps_used,
            "cost_usd": self.cost_usd,
            "latency_ms": self.latency_ms,
            "quality_score": self.quality_score,
            "ground_truth_match": self.ground_truth_match,
        }


class ScenarioRegistry:
    """Manages scenario specifications with dev/holdout split."""

    def __init__(self) -> None:
        self._scenarios: dict[str, ScenarioSpec] = {}

    def register(self, spec: ScenarioSpec) -> None:
        self._scenarios[spec.scenario_id] = spec

    def get(self, scenario_id: str) -> ScenarioSpec | None:
        return self._scenarios.get(scenario_id)

    def all(self) -> list[ScenarioSpec]:
        return list(self._scenarios.values())

    def by_family(self, family: str) -> list[ScenarioSpec]:
        return [s for s in self._scenarios.values() if s.family == family]

    def by_split(self, split: str) -> list[ScenarioSpec]:
        return [s for s in self._scenarios.values() if s.split == split]

    def dev_scenarios(self) -> list[ScenarioSpec]:
        return self.by_split("dev")

    def holdout_scenarios(self) -> list[ScenarioSpec]:
        return self.by_split("holdout")

    def families(self) -> list[str]:
        return sorted({s.family for s in self._scenarios.values()})

    def generate_deterministic(
        self,
        *,
        family: str,
        template_fn: Any,
        count: int = 10,
        base_seed: int = 42,
        split: str = "dev",
    ) -> list[ScenarioSpec]:
        """Generate deterministic scenarios from a template function."""
        generated = []
        for i in range(count):
            seed = base_seed + i
            spec = template_fn(family=family, index=i, seed=seed, split=split)
            self.register(spec)
            generated.append(spec)
        return generated


class AblationConfig:
    """Configures which REE mechanisms are enabled/disabled for an experiment."""

    FULL_REE_MECHANISMS: list[str] = [
        "hypothesis_ecology",
        "ignorance_ledger",
        "self_model",
        "counterfactual_lab",
        "ontology_forge",
        "sealed_tribunal",
        "evidence_independence",
        "federated_memory",
        "epistemic_market",
        "stopping_policy",
        "trajectory_collection",
        "value_model",
    ]

    @classmethod
    def full_ree(cls) -> dict[str, bool]:
        return {m: True for m in cls.FULL_REE_MECHANISMS}

    @classmethod
    def ree_core_only(cls) -> dict[str, bool]:
        core = {"hypothesis_ecology", "ignorance_ledger", "epistemic_market", "stopping_policy"}
        return {m: m in core for m in cls.FULL_REE_MECHANISMS}

    @classmethod
    def leave_one_out(cls, mechanism: str) -> dict[str, bool]:
        config = cls.full_ree()
        config[mechanism] = False
        return config

    @classmethod
    def additive(cls, mechanism: str) -> dict[str, bool]:
        config = cls.ree_core_only()
        config[mechanism] = True
        return config

    @classmethod
    def baseline_none(cls) -> dict[str, bool]:
        return {m: False for m in cls.FULL_REE_MECHANISMS}

    @classmethod
    def all_leave_one_out_configs(cls) -> dict[str, dict[str, bool]]:
        return {f"ree_no_{m}": cls.leave_one_out(m) for m in cls.FULL_REE_MECHANISMS}

    @classmethod
    def all_additive_configs(cls) -> dict[str, dict[str, bool]]:
        return {f"ree_core_plus_{m}": cls.additive(m)
                for m in cls.FULL_REE_MECHANISMS
                if m not in {"hypothesis_ecology", "ignorance_ledger", "epistemic_market", "stopping_policy"}}


class ResultStore:
    """Persists scenario results as JSONL for reproducibility."""

    def __init__(self, path: Path) -> None:
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, result: ScenarioResult) -> None:
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result.to_dict()) + "\n")

    def load_all(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        results = []
        with self._path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    results.append(json.loads(line))
        return results

    def by_scenario(self, scenario_id: str) -> list[dict[str, Any]]:
        return [r for r in self.load_all() if r["scenario_id"] == scenario_id]

    def by_architecture(self, architecture: str) -> list[dict[str, Any]]:
        return [r for r in self.load_all() if r["architecture"] == architecture]


def leakage_check(
    dev_scenarios: list[ScenarioSpec],
    holdout_scenarios: list[ScenarioSpec],
) -> list[str]:
    """Check for question leakage between dev and holdout splits."""
    dev_hashes = set()
    for s in dev_scenarios:
        h = hashlib.sha256(s.question.strip().lower().encode()).hexdigest()
        dev_hashes.add(h)

    violations = []
    for s in holdout_scenarios:
        h = hashlib.sha256(s.question.strip().lower().encode()).hexdigest()
        if h in dev_hashes:
            violations.append(s.scenario_id)

    return violations
