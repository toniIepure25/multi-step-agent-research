"""
Ignorance — persistent tracking of known unknowns.

The system must explicitly represent: missing evidence, untested assumptions,
unresolved contradictions, confounders, model limitations, ontology gaps,
and uncertainty whose resolution could change the final decision.
"""

from asar.ignorance.ledger import IgnoranceLedger

__all__ = ["IgnoranceLedger"]
