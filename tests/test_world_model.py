"""
Tests for the world model: hypothesis graph, research graph, belief tracker.
"""

from __future__ import annotations

import pytest

from asar.world_model.hypothesis_graph import HypothesisGraph
from asar.world_model.research_graph import ResearchGraph
from asar.world_model.belief_tracker import BeliefTracker
from schemas.ree.world_model import (
    Assumption,
    Contradiction,
    Falsifier,
    Hypothesis,
    HypothesisStatus,
    Prediction,
    ResearchEdge,
    ResearchEdgeType,
    ResearchNode,
    ResearchNodeType,
)


class TestHypothesisGraph:
    def _make_hyp(self, hid: str = "hypothesis_001", statement: str = "Test hypothesis") -> Hypothesis:
        return Hypothesis(hypothesis_id=hid, statement=statement)

    def test_add_and_retrieve(self) -> None:
        g = HypothesisGraph()
        h = self._make_hyp()
        g.add_hypothesis(h)
        assert g.get_hypothesis("hypothesis_001") is not None
        assert g.get_hypothesis("hypothesis_001").statement == "Test hypothesis"

    def test_active_hypotheses(self) -> None:
        g = HypothesisGraph()
        g.add_hypothesis(self._make_hyp("h1"))
        g.add_hypothesis(Hypothesis(hypothesis_id="h2", statement="rejected", status=HypothesisStatus.REJECTED))
        assert len(g.active_hypotheses()) == 1

    def test_update_posterior_transitions_status(self) -> None:
        g = HypothesisGraph()
        g.add_hypothesis(self._make_hyp("h1"))

        updated = g.update_posterior("h1", 0.8)
        assert updated.status == HypothesisStatus.ACTIVE

        updated = g.update_posterior("h1", 0.2)
        assert updated.status == HypothesisStatus.WEAKENED

        updated = g.update_posterior("h1", 0.05)
        assert updated.status == HypothesisStatus.REJECTED

    def test_posterior_bounds(self) -> None:
        g = HypothesisGraph()
        g.add_hypothesis(self._make_hyp("h1"))
        updated = g.update_posterior("h1", 1.5)
        assert updated.posterior <= 1.0
        updated = g.update_posterior("h1", -0.5)
        assert updated.posterior >= 0.0

    def test_evidence_tracking(self) -> None:
        g = HypothesisGraph()
        g.add_hypothesis(self._make_hyp("h1"))
        g.add_supporting_evidence("h1", "evidence_001")
        g.add_attacking_evidence("h1", "evidence_002")

        h = g.get_hypothesis("h1")
        assert "evidence_001" in h.supporting_evidence_ids
        assert "evidence_002" in h.attacking_evidence_ids

    def test_assumption_tracking(self) -> None:
        g = HypothesisGraph()
        g.add_hypothesis(self._make_hyp("h1"))
        g.add_assumption(Assumption(
            assumption_id="a1",
            text="Market is efficient",
            criticality=0.9,
            dependent_hypothesis_ids=["h1"],
        ))
        assumptions = g.get_assumptions_for("h1")
        assert len(assumptions) == 1
        critical = g.critical_assumptions(threshold=0.8)
        assert len(critical) == 1

    def test_prediction_links_to_hypothesis(self) -> None:
        g = HypothesisGraph()
        g.add_hypothesis(self._make_hyp("h1"))
        g.add_prediction(Prediction(
            prediction_id="p1",
            hypothesis_id="h1",
            statement="Price will drop",
            discriminating_power=0.8,
        ))
        h = g.get_hypothesis("h1")
        assert "p1" in h.prediction_ids

    def test_falsifier_links_to_hypothesis(self) -> None:
        g = HypothesisGraph()
        g.add_hypothesis(self._make_hyp("h1"))
        g.add_falsifier(Falsifier(
            falsifier_id="f1",
            hypothesis_id="h1",
            statement="If unemployment stays low",
            impact_if_observed=0.9,
        ))
        h = g.get_hypothesis("h1")
        assert "f1" in h.falsifier_ids
        falsifiers = g.get_falsifiers_for("h1")
        assert len(falsifiers) == 1

    def test_contradiction_detection(self) -> None:
        g = HypothesisGraph()
        c = g.detect_contradiction("h1", "h2", "Mutually exclusive explanations", severity=0.8)
        assert c.contradiction_id.startswith("contradiction_")
        assert len(g.unresolved_contradictions()) == 1

    def test_diversity_score(self) -> None:
        g = HypothesisGraph()
        g.add_hypothesis(Hypothesis(hypothesis_id="h1", statement="A", ontology_frame="causal"))
        g.add_hypothesis(Hypothesis(hypothesis_id="h2", statement="B", ontology_frame="statistical"))
        g.add_hypothesis(Hypothesis(hypothesis_id="h3", statement="C", ontology_frame="causal"))
        score = g.hypothesis_diversity_score()
        assert 0.0 < score < 1.0

    def test_to_artifacts(self) -> None:
        g = HypothesisGraph()
        g.add_hypothesis(self._make_hyp("h1"))
        g.add_assumption(Assumption(assumption_id="a1", text="test", dependent_hypothesis_ids=["h1"]))
        artifacts = g.to_artifacts()
        assert "h1" in artifacts
        assert "a1" in artifacts


class TestResearchGraph:
    def test_add_nodes_and_edges(self) -> None:
        rg = ResearchGraph()
        rg.add_node(ResearchNode(node_id="q1", node_type=ResearchNodeType.QUESTION, label="Main question"))
        rg.add_node(ResearchNode(node_id="h1", node_type=ResearchNodeType.HYPOTHESIS, label="Hypothesis 1"))
        rg.add_edge(ResearchEdge(source_id="h1", target_id="q1", edge_type=ResearchEdgeType.EXPLAINS))
        assert len(rg.all_nodes()) == 2
        assert len(rg.all_edges()) == 1

    def test_supporters_and_attackers(self) -> None:
        rg = ResearchGraph()
        rg.add_node(ResearchNode(node_id="h1", node_type=ResearchNodeType.HYPOTHESIS))
        rg.add_node(ResearchNode(node_id="e1", node_type=ResearchNodeType.EVIDENCE))
        rg.add_node(ResearchNode(node_id="e2", node_type=ResearchNodeType.EVIDENCE))
        rg.add_edge(ResearchEdge(source_id="e1", target_id="h1", edge_type=ResearchEdgeType.SUPPORTS))
        rg.add_edge(ResearchEdge(source_id="e2", target_id="h1", edge_type=ResearchEdgeType.ATTACKS))

        assert rg.supporters("h1") == ["e1"]
        assert rg.attackers("h1") == ["e2"]

    def test_dependencies(self) -> None:
        rg = ResearchGraph()
        rg.add_node(ResearchNode(node_id="h1", node_type=ResearchNodeType.HYPOTHESIS))
        rg.add_node(ResearchNode(node_id="a1", node_type=ResearchNodeType.ASSUMPTION))
        rg.add_edge(ResearchEdge(source_id="h1", target_id="a1", edge_type=ResearchEdgeType.DEPENDS_ON))
        assert rg.dependencies("h1") == ["a1"]

    def test_alternatives(self) -> None:
        rg = ResearchGraph()
        rg.add_node(ResearchNode(node_id="h1", node_type=ResearchNodeType.HYPOTHESIS))
        rg.add_node(ResearchNode(node_id="h2", node_type=ResearchNodeType.HYPOTHESIS))
        rg.add_edge(ResearchEdge(source_id="h1", target_id="h2", edge_type=ResearchEdgeType.ALTERNATIVE_TO))
        assert "h2" in rg.alternatives("h1")
        assert "h1" in rg.alternatives("h2")

    def test_frontier_nodes(self) -> None:
        rg = ResearchGraph()
        rg.add_node(ResearchNode(node_id="q1", node_type=ResearchNodeType.QUESTION))
        rg.add_node(ResearchNode(node_id="e1", node_type=ResearchNodeType.EVIDENCE))
        rg.add_edge(ResearchEdge(source_id="e1", target_id="q1", edge_type=ResearchEdgeType.SUPPORTS))
        frontier = rg.frontier_nodes()
        assert any(n.node_id == "q1" for n in frontier)

    def test_nodes_by_type(self) -> None:
        rg = ResearchGraph()
        rg.add_node(ResearchNode(node_id="h1", node_type=ResearchNodeType.HYPOTHESIS))
        rg.add_node(ResearchNode(node_id="h2", node_type=ResearchNodeType.HYPOTHESIS))
        rg.add_node(ResearchNode(node_id="e1", node_type=ResearchNodeType.EVIDENCE))
        assert len(rg.nodes_by_type(ResearchNodeType.HYPOTHESIS)) == 2


class TestBeliefTracker:
    def test_record_and_trajectory(self) -> None:
        tracker = BeliefTracker()
        tracker.record("h1", version=1, posterior=0.5, status=HypothesisStatus.PROPOSED)
        tracker.record("h1", version=3, posterior=0.7, status=HypothesisStatus.ACTIVE)
        tracker.record("h1", version=5, posterior=0.3, status=HypothesisStatus.WEAKENED)

        traj = tracker.trajectory("h1")
        assert len(traj) == 3
        assert traj[0].version == 1
        assert traj[-1].version == 5

    def test_latest(self) -> None:
        tracker = BeliefTracker()
        tracker.record("h1", version=1, posterior=0.5, status=HypothesisStatus.PROPOSED)
        tracker.record("h1", version=5, posterior=0.8, status=HypothesisStatus.ACTIVE)
        assert tracker.latest("h1").posterior == 0.8

    def test_belief_delta(self) -> None:
        tracker = BeliefTracker()
        tracker.record("h1", version=1, posterior=0.5, status=HypothesisStatus.PROPOSED)
        tracker.record("h1", version=5, posterior=0.8, status=HypothesisStatus.ACTIVE)
        assert tracker.belief_delta("h1") == pytest.approx(0.3)

    def test_revision_count(self) -> None:
        tracker = BeliefTracker()
        tracker.record("h1", version=1, posterior=0.5, status=HypothesisStatus.PROPOSED)
        tracker.record("h1", version=2, posterior=0.7, status=HypothesisStatus.ACTIVE)
        tracker.record("h1", version=3, posterior=0.4, status=HypothesisStatus.WEAKENED)
        assert tracker.revision_count("h1") == 2

    def test_monotonic_change(self) -> None:
        tracker = BeliefTracker()
        tracker.record("h1", version=1, posterior=0.3, status=HypothesisStatus.PROPOSED)
        tracker.record("h1", version=2, posterior=0.5, status=HypothesisStatus.ACTIVE)
        tracker.record("h1", version=3, posterior=0.8, status=HypothesisStatus.ACTIVE)
        assert tracker.monotonic_change("h1") is True

        tracker.record("h1", version=4, posterior=0.4, status=HypothesisStatus.WEAKENED)
        assert tracker.monotonic_change("h1") is False
