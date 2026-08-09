"""
Value principle registry — manages task-level epistemic values and conflicts.
"""

from __future__ import annotations

from asar.common import generate_id
from schemas.ree.value_model import NormConflict, ValuePrinciple


class ValueRegistry:
    """Manages task-level value principles and their conflicts."""

    def __init__(self) -> None:
        self._principles: dict[str, ValuePrinciple] = {}
        self._conflicts: list[NormConflict] = []
        self._init_defaults()

    def _init_defaults(self) -> None:
        defaults = [
            ("accuracy", "Accuracy", "Correctness of factual claims", 0.9, False),
            ("completeness", "Completeness", "Coverage of relevant aspects", 0.7, True),
            ("novelty", "Novelty", "Discovering non-obvious insights", 0.4, True),
            ("cost_efficiency", "Cost Efficiency", "Minimizing compute cost", 0.5, True),
            ("falsifiability", "Falsifiability", "Preferring falsifiable claims", 0.6, True),
            ("interpretability", "Interpretability", "Clear reasoning chains", 0.6, True),
            ("robustness", "Robustness", "Stability under perturbation", 0.7, True),
            ("evidence_quality", "Evidence Quality", "Preferring high-quality sources", 0.8, False),
        ]
        for pid, name, desc, weight, revisable in defaults:
            self._principles[pid] = ValuePrinciple(
                principle_id=pid, name=name, description=desc,
                weight=weight, revisable=revisable,
            )

    def get(self, principle_id: str) -> ValuePrinciple | None:
        return self._principles.get(principle_id)

    def all_principles(self) -> list[ValuePrinciple]:
        return list(self._principles.values())

    def add_principle(self, principle: ValuePrinciple) -> None:
        self._principles[principle.principle_id] = principle

    def update_weight(self, principle_id: str, new_weight: float, reason: str = "") -> ValuePrinciple | None:
        """Update a principle's weight (only if revisable)."""
        p = self._principles.get(principle_id)
        if p is None or not p.revisable:
            return None
        updated = p.model_copy(update={
            "weight": max(0.0, min(1.0, new_weight)),
            "revision_history": [*p.revision_history, reason] if reason else p.revision_history,
        })
        self._principles[principle_id] = updated
        return updated

    def hard_constraints(self) -> list[ValuePrinciple]:
        return [p for p in self._principles.values() if not p.revisable]

    def revisable_principles(self) -> list[ValuePrinciple]:
        return [p for p in self._principles.values() if p.revisable]

    def register_conflict(
        self,
        principle_a_id: str,
        principle_b_id: str,
        context: str = "",
        affected_stakeholders: list[str] | None = None,
    ) -> NormConflict:
        """Register a conflict between two principles."""
        conflict = NormConflict(
            conflict_id=generate_id("conflict"),
            principle_a_id=principle_a_id,
            principle_b_id=principle_b_id,
            context=context,
            affected_stakeholders=affected_stakeholders or [],
        )
        self._conflicts.append(conflict)
        return conflict

    def resolve_conflict(
        self,
        conflict_id: str,
        resolution: str,
        residual: str | None = None,
    ) -> NormConflict | None:
        """Record a resolution for a conflict."""
        for i, c in enumerate(self._conflicts):
            if c.conflict_id == conflict_id:
                updated = c.model_copy(update={
                    "proposed_resolution": resolution,
                    "resolution_accepted": True,
                    "residual_disagreement": residual,
                })
                self._conflicts[i] = updated
                return updated
        return None

    def unresolved_conflicts(self) -> list[NormConflict]:
        return [c for c in self._conflicts if not c.resolution_accepted]

    def all_conflicts(self) -> list[NormConflict]:
        return list(self._conflicts)
