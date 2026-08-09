"""
World Model — hypothesis ecology, assumption graph, research graph, belief tracking.

Responsibilities:
- Manage competing hypotheses with typed tracking
- Maintain assumption dependency graphs
- Track predictions and falsifiers
- Detect and record contradictions
- Maintain the partial-order research graph
- Track belief trajectories over time
"""

from asar.world_model.hypothesis_graph import HypothesisGraph
from asar.world_model.research_graph import ResearchGraph
from asar.world_model.belief_tracker import BeliefTracker

__all__ = ["HypothesisGraph", "ResearchGraph", "BeliefTracker"]
