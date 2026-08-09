"""
Ontology Forge — manages multiple candidate ontological frames and their lineage.

The system must be capable of changing its conceptual framing, maintaining
multiple candidate ontologies, and tracking whether conclusions are invariant
across frames, ontology-dependent, or underdetermined.
"""

from __future__ import annotations

from asar.common import generate_id
from schemas.ree.ontology import ConclusionInvariance, OntologyFrame


class OntologyForge:
    """Manages the ecology of ontological frames."""

    def __init__(self) -> None:
        self._frames: dict[str, OntologyFrame] = {}
        default = OntologyFrame(
            frame_id="default",
            name="Default",
            description="Initial unstructured conceptual frame",
        )
        self._frames["default"] = default

    def add_frame(self, frame: OntologyFrame) -> None:
        self._frames[frame.frame_id] = frame

    def get_frame(self, frame_id: str) -> OntologyFrame | None:
        return self._frames.get(frame_id)

    def active_frames(self) -> list[OntologyFrame]:
        return [f for f in self._frames.values() if f.active]

    def all_frames(self) -> list[OntologyFrame]:
        return list(self._frames.values())

    def create_revision(
        self,
        parent_frame_id: str,
        name: str,
        description: str = "",
        key_variables: list[str] | None = None,
        key_relations: list[str] | None = None,
        assumptions: list[str] | None = None,
    ) -> OntologyFrame:
        """Create a revised frame derived from an existing one."""
        parent = self._frames.get(parent_frame_id)
        new_frame = OntologyFrame(
            frame_id=generate_id("frame"),
            name=name,
            description=description,
            key_variables=key_variables or (parent.key_variables if parent else []),
            key_relations=key_relations or (parent.key_relations if parent else []),
            assumptions=assumptions or (parent.assumptions if parent else []),
            parent_frame_id=parent_frame_id,
        )
        self._frames[new_frame.frame_id] = new_frame
        return new_frame

    def deactivate(self, frame_id: str) -> None:
        """Deactivate a frame (does not delete — preserves lineage)."""
        frame = self._frames.get(frame_id)
        if frame:
            self._frames[frame_id] = frame.model_copy(update={"active": False})

    def lineage(self, frame_id: str) -> list[str]:
        """Return the chain of parent frame IDs."""
        chain: list[str] = []
        current = frame_id
        while current:
            chain.append(current)
            frame = self._frames.get(current)
            if frame and frame.parent_frame_id:
                current = frame.parent_frame_id
            else:
                break
        return chain

    def classify_conclusion_invariance(
        self,
        conclusions_by_frame: dict[str, str],
    ) -> ConclusionInvariance:
        """Classify whether a conclusion is invariant across frames."""
        unique_conclusions = set(conclusions_by_frame.values())
        if len(unique_conclusions) == 1:
            return ConclusionInvariance.INVARIANT
        elif len(unique_conclusions) < len(conclusions_by_frame):
            return ConclusionInvariance.ONTOLOGY_DEPENDENT
        else:
            return ConclusionInvariance.UNDERDETERMINED
