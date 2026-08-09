"""
Tests for the Ignorance Ledger.
"""

from __future__ import annotations

import pytest

from asar.ignorance.ledger import IgnoranceLedger
from schemas.ree.ignorance import IgnoranceItem, IgnoranceStatus, IgnoranceType


def _make_item(
    iid: str = "ignorance_001",
    ignorance_type: IgnoranceType = IgnoranceType.MISSING_EVIDENCE,
    relevance: float = 0.5,
    impact: float = 0.5,
    resolvability: float = 0.5,
    cost: float = 0.5,
) -> IgnoranceItem:
    return IgnoranceItem(
        ignorance_id=iid,
        ignorance_type=ignorance_type,
        description=f"Unknown: {iid}",
        probability_decision_relevant=relevance,
        impact_if_resolved=impact,
        resolvability=resolvability,
        estimated_cost=cost,
    )


class TestIgnoranceLedger:
    def test_add_and_retrieve(self) -> None:
        ledger = IgnoranceLedger()
        item = _make_item()
        ledger.add(item)
        assert ledger.get("ignorance_001") is not None

    def test_open_items(self) -> None:
        ledger = IgnoranceLedger()
        ledger.add(_make_item("i1"))
        ledger.add(_make_item("i2"))
        assert len(ledger.open_items()) == 2

    def test_resolve(self) -> None:
        ledger = IgnoranceLedger()
        ledger.add(_make_item("i1"))
        resolved = ledger.resolve("i1", "Found the answer")
        assert resolved.status == IgnoranceStatus.RESOLVED
        assert resolved.resolution == "Found the answer"
        assert len(ledger.open_items()) == 0

    def test_accept(self) -> None:
        ledger = IgnoranceLedger()
        ledger.add(_make_item("i1"))
        accepted = ledger.accept("i1")
        assert accepted.status == IgnoranceStatus.ACCEPTED
        assert len(ledger.open_items()) == 0

    def test_prioritized_order(self) -> None:
        ledger = IgnoranceLedger()
        ledger.add(_make_item("low", relevance=0.1, impact=0.1, resolvability=0.1, cost=1.0))
        ledger.add(_make_item("high", relevance=0.9, impact=0.9, resolvability=0.9, cost=0.1))
        ledger.add(_make_item("mid", relevance=0.5, impact=0.5, resolvability=0.5, cost=0.5))

        prioritized = ledger.prioritized()
        assert prioritized[0].ignorance_id == "high"
        assert prioritized[-1].ignorance_id == "low"

    def test_prioritized_top_k(self) -> None:
        ledger = IgnoranceLedger()
        for i in range(5):
            ledger.add(_make_item(f"i{i}", relevance=i * 0.2))
        assert len(ledger.prioritized(top_k=2)) == 2

    def test_by_type(self) -> None:
        ledger = IgnoranceLedger()
        ledger.add(_make_item("i1", ignorance_type=IgnoranceType.MISSING_EVIDENCE))
        ledger.add(_make_item("i2", ignorance_type=IgnoranceType.CONFOUND))
        ledger.add(_make_item("i3", ignorance_type=IgnoranceType.MISSING_EVIDENCE))
        assert len(ledger.by_type(IgnoranceType.MISSING_EVIDENCE)) == 2

    def test_decision_relevant_items(self) -> None:
        ledger = IgnoranceLedger()
        ledger.add(_make_item("i1", relevance=0.8))
        ledger.add(_make_item("i2", relevance=0.2))
        relevant = ledger.decision_relevant_items(threshold=0.5)
        assert len(relevant) == 1
        assert relevant[0].ignorance_id == "i1"

    def test_total_unresolved_impact(self) -> None:
        ledger = IgnoranceLedger()
        ledger.add(_make_item("i1", impact=0.3))
        ledger.add(_make_item("i2", impact=0.7))
        assert ledger.total_unresolved_impact() == pytest.approx(1.0)

    def test_priority_score_formula(self) -> None:
        item = _make_item("i1", relevance=0.8, impact=0.6, resolvability=0.5, cost=0.2)
        expected = 0.8 * 0.6 * 0.5 / 0.2
        assert item.priority_score == pytest.approx(expected)

    def test_to_artifacts(self) -> None:
        ledger = IgnoranceLedger()
        ledger.add(_make_item("i1"))
        artifacts = ledger.to_artifacts()
        assert "i1" in artifacts

    def test_resolve_nonexistent_returns_none(self) -> None:
        ledger = IgnoranceLedger()
        assert ledger.resolve("nonexistent", "whatever") is None
