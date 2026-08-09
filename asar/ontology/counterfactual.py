"""
Counterfactual Laboratory — perturbation engine for testing robustness
and responsiveness of conclusions.

Robustness: conclusion should remain stable under irrelevant perturbations.
Responsiveness: conclusion should change under causally decisive perturbations.
A system that never changes its mind is not robust; it is rigid.
"""

from __future__ import annotations

from asar.common import generate_id
from schemas.ree.ontology import CounterfactualWorld, SensitivityResult


class CounterfactualLab:
    """Manages counterfactual worlds and sensitivity analysis."""

    def __init__(self) -> None:
        self._worlds: dict[str, CounterfactualWorld] = {}
        self._sensitivity_results: list[SensitivityResult] = []

    def create_world(
        self,
        *,
        perturbation_type: str,
        description: str = "",
        base_world_id: str | None = None,
        frame_id: str = "default",
        perturbation_details: dict | None = None,
        modified_assumptions: dict | None = None,
        modified_evidence_ids: list[str] | None = None,
    ) -> CounterfactualWorld:
        """Create a counterfactual world with specified perturbations."""
        world = CounterfactualWorld(
            world_id=generate_id("world"),
            base_world_id=base_world_id,
            frame_id=frame_id,
            description=description,
            perturbation_type=perturbation_type,
            perturbation_details=perturbation_details or {},
            modified_assumptions=modified_assumptions or {},
            modified_evidence_ids=modified_evidence_ids or [],
        )
        self._worlds[world.world_id] = world
        return world

    def get_world(self, world_id: str) -> CounterfactualWorld | None:
        return self._worlds.get(world_id)

    def all_worlds(self) -> list[CounterfactualWorld]:
        return list(self._worlds.values())

    def record_conclusion(
        self,
        world_id: str,
        conclusion: str,
        conclusion_changed: bool,
    ) -> CounterfactualWorld | None:
        """Record the conclusion reached in a counterfactual world."""
        world = self._worlds.get(world_id)
        if world is None:
            return None
        updated = world.model_copy(update={
            "conclusion": conclusion,
            "conclusion_changed": conclusion_changed,
        })
        self._worlds[world_id] = updated
        return updated

    def record_sensitivity(self, result: SensitivityResult) -> None:
        self._sensitivity_results.append(result)

    def sensitivity_results(self) -> list[SensitivityResult]:
        return list(self._sensitivity_results)

    def robustness_score(self) -> float:
        """Fraction of irrelevant perturbations where conclusion remained stable."""
        irrelevant = [r for r in self._sensitivity_results if not r.is_causally_decisive]
        if not irrelevant:
            return 1.0
        stable = sum(1 for r in irrelevant if not r.conclusion_changed)
        return stable / len(irrelevant)

    def responsiveness_score(self) -> float:
        """Fraction of causally decisive perturbations where conclusion changed."""
        decisive = [r for r in self._sensitivity_results if r.is_causally_decisive]
        if not decisive:
            return 1.0
        changed = sum(1 for r in decisive if r.conclusion_changed)
        return changed / len(decisive)

    def causally_decisive_assumptions(self) -> list[SensitivityResult]:
        """Return assumptions whose modification changed conclusions."""
        return [r for r in self._sensitivity_results if r.conclusion_changed and r.is_causally_decisive]
