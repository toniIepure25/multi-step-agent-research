"""
Tests for the value model: principles, conflicts, and reflective equilibrium.
"""

from __future__ import annotations

import pytest

from asar.value_model.principles import ValueRegistry
from asar.value_model.equilibrium import ReflectiveEquilibrium
from schemas.ree.value_model import ValuePrinciple


class TestValueRegistry:
    def test_default_principles_loaded(self) -> None:
        reg = ValueRegistry()
        assert reg.get("accuracy") is not None
        assert reg.get("completeness") is not None

    def test_hard_constraints_not_revisable(self) -> None:
        reg = ValueRegistry()
        hard = reg.hard_constraints()
        assert len(hard) >= 1
        for h in hard:
            assert not h.revisable

    def test_update_weight_on_revisable(self) -> None:
        reg = ValueRegistry()
        updated = reg.update_weight("completeness", 0.9, "task requires thoroughness")
        assert updated is not None
        assert updated.weight == pytest.approx(0.9)
        assert "task requires thoroughness" in updated.revision_history

    def test_update_weight_blocked_on_hard_constraint(self) -> None:
        reg = ValueRegistry()
        result = reg.update_weight("accuracy", 0.1, "trying to reduce accuracy")
        assert result is None

    def test_register_conflict(self) -> None:
        reg = ValueRegistry()
        conflict = reg.register_conflict("completeness", "cost_efficiency", "More complete = more costly")
        assert conflict.conflict_id.startswith("conflict_")
        assert len(reg.unresolved_conflicts()) == 1

    def test_resolve_conflict(self) -> None:
        reg = ValueRegistry()
        conflict = reg.register_conflict("novelty", "robustness")
        resolved = reg.resolve_conflict(conflict.conflict_id, "Prioritize robustness for this task")
        assert resolved is not None
        assert resolved.resolution_accepted
        assert len(reg.unresolved_conflicts()) == 0

    def test_add_custom_principle(self) -> None:
        reg = ValueRegistry()
        reg.add_principle(ValuePrinciple(
            principle_id="privacy", name="Privacy",
            description="Protect user data", weight=0.9, revisable=False,
        ))
        assert reg.get("privacy") is not None


class TestReflectiveEquilibrium:
    def test_propose_revision_accepted(self) -> None:
        reg = ValueRegistry()
        eq = ReflectiveEquilibrium(reg)
        assert eq.propose_revision("completeness", 0.8, "need more coverage")
        assert reg.get("completeness").weight == pytest.approx(0.8)

    def test_propose_revision_blocked_for_hard_constraint(self) -> None:
        reg = ValueRegistry()
        eq = ReflectiveEquilibrium(reg)
        assert not eq.propose_revision("accuracy", 0.1, "nope")

    def test_balance_weights(self) -> None:
        reg = ValueRegistry()
        eq = ReflectiveEquilibrium(reg)
        adjustments = eq.balance_weights()
        assert len(adjustments) > 0
        by_category: dict[str, float] = {}
        for pid, w in adjustments.items():
            p = reg.get(pid)
            by_category.setdefault(p.category, 0.0)
            by_category[p.category] += w
        for total in by_category.values():
            assert total == pytest.approx(1.0)

    def test_detect_tensions(self) -> None:
        reg = ValueRegistry()
        reg.update_weight("completeness", 0.9, "high")
        reg.update_weight("robustness", 0.9, "high")
        eq = ReflectiveEquilibrium(reg)
        tensions = eq.detect_tensions()
        assert len(tensions) >= 1
