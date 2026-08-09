"""
Metacognition — controls which cognitive operation to execute next.

The metacognitive controller is the main REE loop:
state -> propose bids -> select best action -> execute -> reduce -> repeat

The epistemic market evaluates bids to select the most epistemically
valuable action given the current state and remaining budget.
"""

from asar.metacognition.controller import EpistemicController
from asar.metacognition.market import EpistemicMarket
from asar.metacognition.stopping import StoppingPolicy
from asar.metacognition.trajectory import TrajectoryDataset

__all__ = ["EpistemicController", "EpistemicMarket", "StoppingPolicy", "TrajectoryDataset"]
