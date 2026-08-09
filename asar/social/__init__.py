"""
Social — dissonance tribunal, stakeholder models, evidence independence.

Responsibilities:
- Sealed-first-round deliberation protocol
- Transient epistemic roles (Advocate, Falsifier, Judge, etc.)
- Evidence-based adjudication (not majority vote)
- Evidence provenance clustering and independence scoring
- Stakeholder models with probabilistic beliefs/goals/incentives
"""

from asar.social.tribunal import DissonanceTribunal
from asar.social.trust import EvidenceIndependenceAnalyzer
from asar.social.stakeholder import StakeholderRegistry

__all__ = ["DissonanceTribunal", "EvidenceIndependenceAnalyzer", "StakeholderRegistry"]
