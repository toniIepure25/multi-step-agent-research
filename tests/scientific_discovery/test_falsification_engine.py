"""
Tests for FalsificationEngine — the core scientific self-correction mechanism.
"""

import pytest

from asar.scientific_discovery.falsification_engine import (
    DiscriminationAnalysis,
    FalsificationEngine,
    FalsificationProposal,
)
from asar.scientific_discovery.state import (
    Assumption,
    AssumptionCategory,
    EvidenceDirection,
    Falsifier,
    HypothesisEcology,
    HypothesisMaturity,
    HypothesisStatus,
    Prediction,
    ScientificEvidence,
    ScientificState,
    StructuredHypothesis,
)


@pytest.fixture
def engine() -> FalsificationEngine:
    return FalsificationEngine()


@pytest.fixture
def state_with_falsifiers() -> ScientificState:
    """State with a hypothesis that has registered falsifiers and assumptions."""
    h1 = StructuredHypothesis(
        hypothesis_id="h1",
        claim="Drug X works via COX-2",
        causal_mechanism="COX-2 inhibition",
        potential_falsifiers=["f1", "f2"],
        assumptions=["a1"],
        alternative_explanations=["h2"],
        expected_observations_if_false=["No COX-2 binding"],
        confidence=0.7,
        maturity=HypothesisMaturity.H2_FALSIFIABLE,
        status=HypothesisStatus.ACTIVE,
    )
    h2 = StructuredHypothesis(
        hypothesis_id="h2",
        claim="Drug X works via NF-kB",
        causal_mechanism="NF-kB modulation",
        derived_predictions=["p2"],
        expected_observations_if_true=["Reduced NF-kB"],
        confidence=0.4,
        maturity=HypothesisMaturity.H2_FALSIFIABLE,
        status=HypothesisStatus.ACTIVE,
    )

    f1 = Falsifier(
        falsifier_id="f1",
        hypothesis_id="h1",
        statement="No COX-2 binding detected",
        attack_vector="Binding mechanism",
        observation_feasibility=0.9,
        impact_if_observed=0.85,
    )
    f2 = Falsifier(
        falsifier_id="f2",
        hypothesis_id="h1",
        statement="COX-2 knockout shows same effect",
        attack_vector="Necessity of COX-2",
        observation_feasibility=0.5,
        impact_if_observed=0.7,
    )

    a1 = Assumption(
        assumption_id="a1",
        text="Drug reaches COX-2 at therapeutic dose",
        criticality=0.8,
        dependent_hypothesis_ids=["h1"],
        tested=False,
        category=AssumptionCategory.AUXILIARY,
    )

    p2 = Prediction(
        prediction_id="p2",
        hypothesis_id="h2",
        statement="NF-kB translocation reduced",
        discriminating_power=0.8,
    )

    ecology = HypothesisEcology(hypotheses={"h1": h1, "h2": h2})

    return ScientificState(
        episode_id="test_ep",
        research_question="How does Drug X work?",
        ecology=ecology,
        assumptions={"a1": a1},
        falsifiers={"f1": f1, "f2": f2},
        predictions={"p2": p2},
    )


class TestFalsificationProposal:
    def test_finds_strongest_falsifier(self, engine, state_with_falsifiers):
        proposal = engine.propose_falsification(state_with_falsifiers, "h1")
        assert proposal.strongest_falsifier is not None
        # f1 has higher score (0.9 × 0.85 = 0.765) than f2 (0.5 × 0.7 = 0.35)
        assert proposal.strongest_falsifier.falsifier_id == "f1"

    def test_identifies_critical_assumptions(self, engine, state_with_falsifiers):
        proposal = engine.propose_falsification(state_with_falsifiers, "h1")
        assert "a1" in proposal.critical_assumptions_attacked

    def test_derives_predictions(self, engine, state_with_falsifiers):
        proposal = engine.propose_falsification(state_with_falsifiers, "h1")
        assert len(proposal.predicted_observations) > 0

    def test_computes_information_gain(self, engine, state_with_falsifiers):
        proposal = engine.propose_falsification(state_with_falsifiers, "h1")
        assert proposal.expected_information_gain > 0.0

    def test_proposes_search(self, engine, state_with_falsifiers):
        proposal = engine.propose_falsification(state_with_falsifiers, "h1")
        assert len(proposal.proposed_evidence_search) > 0

    def test_handles_missing_hypothesis(self, engine, state_with_falsifiers):
        proposal = engine.propose_falsification(state_with_falsifiers, "nonexistent")
        assert proposal.strongest_falsifier is None
        assert "not found" in proposal.failure_modes[0].lower() or "not found" in proposal.rationale.lower()

    def test_skips_observed_falsifiers(self, engine):
        """Already-observed falsifiers should not be selected."""
        h = StructuredHypothesis(
            hypothesis_id="h1", claim="X", potential_falsifiers=["f_obs"],
            status=HypothesisStatus.ACTIVE,
        )
        f_obs = Falsifier(
            falsifier_id="f_obs", hypothesis_id="h1",
            statement="Already seen", observation_feasibility=0.9,
            impact_if_observed=0.9, observed=True,
        )
        state = ScientificState(
            episode_id="test",
            ecology=HypothesisEcology(hypotheses={"h1": h}),
            falsifiers={"f_obs": f_obs},
        )
        proposal = engine.propose_falsification(state, "h1")
        assert proposal.strongest_falsifier is None


class TestDiscriminationAnalysis:
    def test_distinct_predictions_give_high_discriminability(self, engine):
        h1 = StructuredHypothesis(
            hypothesis_id="h1", claim="A",
            derived_predictions=["p1", "p2"],
            status=HypothesisStatus.ACTIVE,
        )
        h2 = StructuredHypothesis(
            hypothesis_id="h2", claim="B",
            derived_predictions=["p3", "p4"],
            status=HypothesisStatus.ACTIVE,
        )
        state = ScientificState(
            episode_id="test",
            ecology=HypothesisEcology(hypotheses={"h1": h1, "h2": h2}),
        )
        analysis = engine.analyze_discrimination(state, "h1", "h2")
        assert analysis.discriminability == 1.0  # No shared predictions

    def test_identical_predictions_give_low_discriminability(self, engine):
        h1 = StructuredHypothesis(
            hypothesis_id="h1", claim="A",
            derived_predictions=["p_shared"],
            status=HypothesisStatus.ACTIVE,
        )
        h2 = StructuredHypothesis(
            hypothesis_id="h2", claim="B",
            derived_predictions=["p_shared"],
            status=HypothesisStatus.ACTIVE,
        )
        state = ScientificState(
            episode_id="test",
            ecology=HypothesisEcology(hypotheses={"h1": h1, "h2": h2}),
        )
        analysis = engine.analyze_discrimination(state, "h1", "h2")
        assert analysis.discriminability == 0.0

    def test_pairwise_matrix(self, engine, state_with_falsifiers):
        matrix = engine.pairwise_discrimination_matrix(state_with_falsifiers)
        assert ("h1", "h2") in matrix or ("h2", "h1") in matrix


class TestEvidenceAsFalsifier:
    def test_contradicting_relevant_evidence_scores_high(self, engine, state_with_falsifiers):
        evidence = ScientificEvidence(
            evidence_id="e1",
            content="No COX-2 binding detected",
            direction=EvidenceDirection.CONTRADICTING,
            reliability=0.95,
            relevance_to_hypotheses={"h1": 0.99},
        )
        score = engine.evaluate_evidence_as_falsifier(state_with_falsifiers, evidence, "h1")
        assert score > 0.8

    def test_supporting_evidence_scores_zero(self, engine, state_with_falsifiers):
        evidence = ScientificEvidence(
            evidence_id="e2",
            content="COX-2 activity reduced",
            direction=EvidenceDirection.SUPPORTING,
            reliability=0.9,
            relevance_to_hypotheses={"h1": 0.9},
        )
        score = engine.evaluate_evidence_as_falsifier(state_with_falsifiers, evidence, "h1")
        assert score == 0.0

    def test_irrelevant_evidence_scores_low(self, engine, state_with_falsifiers):
        evidence = ScientificEvidence(
            evidence_id="e3",
            content="Unrelated finding",
            direction=EvidenceDirection.CONTRADICTING,
            reliability=0.9,
            relevance_to_hypotheses={"h1": 0.0},
        )
        score = engine.evaluate_evidence_as_falsifier(state_with_falsifiers, evidence, "h1")
        assert score == 0.0
