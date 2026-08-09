"""
Legacy orchestration — preserves the frozen v0 SequentialOrchestrator.

This module exists for backward compatibility. The SequentialOrchestrator
remains unchanged and is the active orchestrator when runtime mode is "legacy".
"""

from asar.orchestration.sequential_orchestrator import SequentialOrchestrator

__all__ = ["SequentialOrchestrator"]
