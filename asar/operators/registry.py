"""
Operator registry — discovery and management of cognitive operators.
"""

from __future__ import annotations

from asar.operators.base import CognitiveOperator


class OperatorRegistry:
    """Registry of available cognitive operators."""

    def __init__(self) -> None:
        self._operators: dict[str, CognitiveOperator] = {}

    def register(self, operator: CognitiveOperator) -> None:
        """Register an operator by its name."""
        self._operators[operator.name] = operator

    def get(self, name: str) -> CognitiveOperator | None:
        """Get an operator by name."""
        return self._operators.get(name)

    def all(self) -> list[CognitiveOperator]:
        """Return all registered operators."""
        return list(self._operators.values())

    def names(self) -> list[str]:
        """Return all registered operator names."""
        return list(self._operators.keys())

    def __len__(self) -> int:
        return len(self._operators)
