"""
Reflective equilibrium — constrained revision of task-level values.

Hard constraints cannot be self-revised. Revisable principles may be
adjusted through a recorded, evidence-based process.
"""

from __future__ import annotations

from asar.value_model.principles import ValueRegistry


class ReflectiveEquilibrium:
    """Performs constrained reflective equilibrium on value principles."""

    def __init__(self, registry: ValueRegistry) -> None:
        self._registry = registry

    def propose_revision(
        self,
        principle_id: str,
        new_weight: float,
        reason: str,
    ) -> bool:
        """Propose a weight revision. Returns True if accepted."""
        principle = self._registry.get(principle_id)
        if principle is None:
            return False
        if not principle.revisable:
            return False

        result = self._registry.update_weight(principle_id, new_weight, reason)
        return result is not None

    def balance_weights(self) -> dict[str, float]:
        """Normalize revisable weights so they sum to 1.0 within their category."""
        revisable = self._registry.revisable_principles()
        if not revisable:
            return {}

        by_category: dict[str, list[str]] = {}
        for p in revisable:
            by_category.setdefault(p.category, []).append(p.principle_id)

        adjustments: dict[str, float] = {}
        for category, pids in by_category.items():
            total = sum(self._registry.get(pid).weight for pid in pids)
            if total > 0:
                for pid in pids:
                    normalized = self._registry.get(pid).weight / total
                    adjustments[pid] = normalized

        return adjustments

    def detect_tensions(self) -> list[tuple[str, str, str]]:
        """Detect potential value tensions based on weight proximity.

        Returns list of (principle_a_id, principle_b_id, description).
        Principles with similar high weights may compete for priority.
        """
        principles = self._registry.all_principles()
        tensions: list[tuple[str, str, str]] = []

        for i, a in enumerate(principles):
            for b in principles[i + 1:]:
                if a.weight >= 0.7 and b.weight >= 0.7 and a.category == b.category:
                    tensions.append((
                        a.principle_id,
                        b.principle_id,
                        f"Both {a.name} and {b.name} have high weights in {a.category}",
                    ))

        return tensions
