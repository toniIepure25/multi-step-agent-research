"""
Cognitive Operators — swappable cognitive actions for the REE architecture.

Every operator exposes propose() and execute() methods. Operators never
mutate state directly — they return typed OperatorResults that the
state reducer applies.
"""

from asar.operators.base import CognitiveOperator
from asar.operators.registry import OperatorRegistry

__all__ = ["CognitiveOperator", "OperatorRegistry"]
