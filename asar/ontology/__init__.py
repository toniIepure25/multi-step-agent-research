"""
Ontology — conceptual framing, counterfactual laboratory, and active experiment design.

Responsibilities:
- Manage multiple candidate ontological frames
- Support ontology revision and lineage tracking
- Counterfactual perturbation engine (robustness and responsiveness)
- Assumption sensitivity analysis
- Active experiment design with information gain estimation
"""

from asar.ontology.forge import OntologyForge
from asar.ontology.counterfactual import CounterfactualLab
from asar.ontology.experiment_designer import ExperimentDesigner

__all__ = ["OntologyForge", "CounterfactualLab", "ExperimentDesigner"]
