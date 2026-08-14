"""
ASAR Scientific Discovery Engine — Falsification-Driven AI Research Scientist.

This module implements the core scientific reasoning loop:

    Problem formulation
    → Competing hypothesis ecology
    → Prediction derivation
    → Falsification attack
    → Discriminative experiment selection
    → Evidence gathering / computational experiment
    → Quantitative belief update
    → Theory revision or abandonment
    → Ontology revision when framing fails
    → Stop when appropriately uncertain

Key components:
    - ScientificState: Persistent typed belief state (event-sourced)
    - StructuredHypothesis: Hypothesis with maturity, predictions, falsifiers
    - HypothesisEcology: Competing hypothesis management with diversity metrics
    - BeliefUpdater: Quantitative belief revision
    - FalsificationEngine: Generates falsifiers, evaluates disconfirmation
    - ScientificController: Orchestrates the scientific loop
"""

from asar.scientific_discovery.state import (
    Assumption,
    AssumptionCategory,
    BeliefSnapshot,
    BeliefState,
    ConclusionType,
    EvidenceDirection,
    Falsifier,
    HypothesisEcology,
    HypothesisMaturity,
    HypothesisStatus,
    IgnoranceItem,
    IgnoranceStatus,
    NoveltyClass,
    Prediction,
    ScientificBudget,
    ScientificEvidence,
    ScientificState,
    SourceType,
    StructuredHypothesis,
)
from asar.scientific_discovery.events import ScientificEvent, ScientificEventType
from asar.scientific_discovery.belief_updater import BeliefUpdater
from asar.scientific_discovery.falsification_engine import FalsificationEngine
from asar.scientific_discovery.controller import ScientificController

__all__ = [
    "Assumption",
    "AssumptionCategory",
    "BeliefSnapshot",
    "BeliefState",
    "BeliefUpdater",
    "ConclusionType",
    "EvidenceDirection",
    "Falsifier",
    "FalsificationEngine",
    "HypothesisEcology",
    "HypothesisMaturity",
    "HypothesisStatus",
    "IgnoranceItem",
    "IgnoranceStatus",
    "NoveltyClass",
    "Prediction",
    "ScientificBudget",
    "ScientificController",
    "ScientificEvent",
    "ScientificEventType",
    "ScientificEvidence",
    "ScientificState",
    "SourceType",
    "StructuredHypothesis",
]
