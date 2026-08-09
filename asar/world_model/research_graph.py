"""
Partial-order research graph — represents the research process as
a typed directed graph with nodes and edges.
"""

from __future__ import annotations

from schemas.ree.world_model import (
    ResearchEdge,
    ResearchEdgeType,
    ResearchNode,
    ResearchNodeType,
)


class ResearchGraph:
    """A partial-order graph of the research process."""

    def __init__(self) -> None:
        self._nodes: dict[str, ResearchNode] = {}
        self._edges: list[ResearchEdge] = []

    def add_node(self, node: ResearchNode) -> None:
        self._nodes[node.node_id] = node

    def get_node(self, node_id: str) -> ResearchNode | None:
        return self._nodes.get(node_id)

    def all_nodes(self) -> list[ResearchNode]:
        return list(self._nodes.values())

    def nodes_by_type(self, node_type: ResearchNodeType) -> list[ResearchNode]:
        return [n for n in self._nodes.values() if n.node_type == node_type]

    def add_edge(self, edge: ResearchEdge) -> None:
        self._edges.append(edge)

    def all_edges(self) -> list[ResearchEdge]:
        return list(self._edges)

    def edges_from(self, node_id: str) -> list[ResearchEdge]:
        return [e for e in self._edges if e.source_id == node_id]

    def edges_to(self, node_id: str) -> list[ResearchEdge]:
        return [e for e in self._edges if e.target_id == node_id]

    def supporters(self, node_id: str) -> list[str]:
        """Return IDs of nodes that support this node."""
        return [
            e.source_id for e in self._edges
            if e.target_id == node_id and e.edge_type == ResearchEdgeType.SUPPORTS
        ]

    def attackers(self, node_id: str) -> list[str]:
        """Return IDs of nodes that attack this node."""
        return [
            e.source_id for e in self._edges
            if e.target_id == node_id and e.edge_type == ResearchEdgeType.ATTACKS
        ]

    def dependencies(self, node_id: str) -> list[str]:
        """Return IDs of nodes this node depends on."""
        return [
            e.target_id for e in self._edges
            if e.source_id == node_id and e.edge_type == ResearchEdgeType.DEPENDS_ON
        ]

    def alternatives(self, node_id: str) -> list[str]:
        """Return IDs of nodes that are alternatives to this node."""
        return [
            e.target_id for e in self._edges
            if e.source_id == node_id and e.edge_type == ResearchEdgeType.ALTERNATIVE_TO
        ] + [
            e.source_id for e in self._edges
            if e.target_id == node_id and e.edge_type == ResearchEdgeType.ALTERNATIVE_TO
        ]

    def frontier_nodes(self) -> list[ResearchNode]:
        """Return nodes with no outgoing SUPPORTS, EXPLAINS, or TESTS edges.

        These are the current frontier of unexplored research questions.
        """
        productive_types = {
            ResearchEdgeType.SUPPORTS,
            ResearchEdgeType.EXPLAINS,
            ResearchEdgeType.TESTS,
        }
        productive_sources = {
            e.source_id for e in self._edges
            if e.edge_type in productive_types
        }
        return [n for n in self._nodes.values() if n.node_id not in productive_sources]

    def to_artifacts(self) -> dict[str, object]:
        """Export graph state for artifact storage."""
        return {
            "_research_graph_nodes": [n.model_dump() for n in self._nodes.values()],
            "_research_graph_edges": [e.model_dump() for e in self._edges],
        }
