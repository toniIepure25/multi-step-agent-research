"""
Self Model — empirical capability tracking, calibration, and self-assessment.

The Self Model MUST NOT simply consist of LLM-generated introspective prose.
It must learn from historical outcomes.

Responsibilities:
- Track episode outcomes (predicted success vs actual success)
- Build empirical capability estimates P(success | task, strategy, model, tool, state)
- Compute calibration metrics (Brier score, ECE)
- Support abstention/delegation decisions based on capability estimates
"""

from asar.self_model.tracker import EpisodeTracker
from asar.self_model.calibration import CalibrationAnalyzer
from asar.self_model.predictor import CapabilityPredictor

__all__ = ["EpisodeTracker", "CalibrationAnalyzer", "CapabilityPredictor"]
