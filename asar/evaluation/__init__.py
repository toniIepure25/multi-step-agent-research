"""
Evaluation — experiment logging (legacy v0) and REE epistemic metrics.

Responsibilities:
- Legacy: Log experiment runs, compute v0 metrics (groundedness, utilisation)
- REE: Compute epistemic metrics (Brier score, ECE, ignorance foresight, etc.)
- Define controlled benchmark scenarios
- Provide metamorphic cognitive tests
- Support ablation experiments
"""

from asar.evaluation.experiment_logger import ExperimentLogger
from asar.evaluation.epistemic_metrics import EpistemicMetrics

__all__ = ["ExperimentLogger", "EpistemicMetrics"]
