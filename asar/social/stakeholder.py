"""
Stakeholder registry — manages probabilistic models of epistemic actors.

Every inferred mental state must have uncertainty, evidence, and alternatives.
Never convert speculative inferred motivations into facts.
"""

from __future__ import annotations

from schemas.ree.social import StakeholderModel


class StakeholderRegistry:
    """Registry of stakeholder / source epistemic models."""

    def __init__(self) -> None:
        self._models: dict[str, StakeholderModel] = {}

    def register(self, model: StakeholderModel) -> None:
        self._models[model.actor_id] = model

    def get(self, actor_id: str) -> StakeholderModel | None:
        return self._models.get(actor_id)

    def all_models(self) -> list[StakeholderModel]:
        return list(self._models.values())

    def by_type(self, actor_type: str) -> list[StakeholderModel]:
        return [m for m in self._models.values() if m.actor_type == actor_type]

    def reliable_sources(self, threshold: float = 0.7) -> list[StakeholderModel]:
        return [m for m in self._models.values() if m.reliability_score >= threshold]

    def unreliable_sources(self, threshold: float = 0.3) -> list[StakeholderModel]:
        return [m for m in self._models.values() if m.reliability_score <= threshold]

    def update_reliability(self, actor_id: str, new_score: float) -> StakeholderModel | None:
        model = self._models.get(actor_id)
        if model is None:
            return None
        updated = model.model_copy(update={
            "reliability_score": max(0.0, min(1.0, new_score)),
        })
        self._models[actor_id] = updated
        return updated

    def high_uncertainty_models(self, threshold: float = 0.7) -> list[StakeholderModel]:
        """Return models with high uncertainty about the actor's beliefs/goals."""
        return [m for m in self._models.values() if m.uncertainty >= threshold]
