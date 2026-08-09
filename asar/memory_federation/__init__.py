"""
Federated Memory — seven functional stores with consolidation and lifecycle.

Memory is NOT equal to vector retrieval. This module provides:
- Working memory (active workspace)
- Episodic memory (what happened in previous episodes)
- Semantic/belief memory (current knowledge and relations)
- Procedural memory (which strategies have worked)
- Self-model memory (capability/reliability history)
- Prospective memory (things to revisit later)
- Ignorance memory (unresolved uncertainty)

Each store has provenance and temporal state.
RAG/vector retrieval is one optional backend, not the architecture.
"""

from asar.memory_federation.federation import FederatedMemory
from asar.memory_federation.consolidation import MemoryConsolidator

__all__ = ["FederatedMemory", "MemoryConsolidator"]
