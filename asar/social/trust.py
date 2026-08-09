"""
Evidence independence analysis — provenance clustering and independence scoring.

Do not treat 10 citations as 10 independent pieces of evidence if they
derive from one original source.
"""

from __future__ import annotations

from schemas.ree.social import EvidenceProvenance


class EvidenceIndependenceAnalyzer:
    """Analyzes evidence provenance to determine independence."""

    def __init__(self) -> None:
        self._provenance: dict[str, EvidenceProvenance] = {}

    def register_provenance(self, provenance: EvidenceProvenance) -> None:
        self._provenance[provenance.evidence_id] = provenance

    def get_provenance(self, evidence_id: str) -> EvidenceProvenance | None:
        return self._provenance.get(evidence_id)

    def compute_independence_groups(self) -> dict[str, list[str]]:
        """Group evidence by common original source."""
        groups: dict[str, list[str]] = {}
        for prov in self._provenance.values():
            root = prov.original_source_id or prov.evidence_id
            if root not in groups:
                groups[root] = []
            groups[root].append(prov.evidence_id)
        return groups

    def effective_evidence_count(self, evidence_ids: list[str]) -> int:
        """Count independent evidence roots among the given evidence IDs.

        Evidence sharing a common ancestor counts as one independent source.
        """
        groups = self.compute_independence_groups()
        relevant_roots: set[str] = set()
        for eid in evidence_ids:
            prov = self._provenance.get(eid)
            if prov:
                root = prov.original_source_id or eid
                relevant_roots.add(root)
            else:
                relevant_roots.add(eid)
        return len(relevant_roots)

    def evidence_independence_score(self, evidence_ids: list[str]) -> float:
        """Ratio of independent roots to total evidence count.

        1.0 = all evidence is independent. Low = significant duplication.
        """
        if not evidence_ids:
            return 1.0
        effective = self.effective_evidence_count(evidence_ids)
        return effective / len(evidence_ids)

    def is_derivative(self, evidence_id: str) -> bool:
        prov = self._provenance.get(evidence_id)
        if prov is None:
            return False
        return prov.is_derivative

    def duplicated_sources(self) -> list[str]:
        """Return original source IDs that have multiple derivatives."""
        groups = self.compute_independence_groups()
        return [root for root, members in groups.items() if len(members) > 1]
