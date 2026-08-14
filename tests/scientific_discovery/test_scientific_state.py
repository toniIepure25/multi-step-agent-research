"""
Tests for ScientificState, StructuredHypothesis, HypothesisEcology, BeliefState.

These are foundational tests for the typed scientific belief state.
"""

import pytest

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


class TestStructuredHypothesis:
    def test_basic_creation(self):
        h = StructuredHypothesis(
            hypothesis_id="h1",
            claim="X causes Y",
            causal_mechanism="Via pathway Z",
        )
        assert h.hypothesis_id == "h1"
        assert h.confidence == 0.5
        assert h.status == HypothesisStatus.PROPOSED
        assert h.maturity == HypothesisMaturity.H0_SPECULATIVE

    def test_is_falsifiable(self):
        h = StructuredHypothesis(
            hypothesis_id="h1",
            claim="X causes Y",
            potential_falsifiers=["f1"],
        )
        assert h.is_falsifiable is True

        h2 = StructuredHypothesis(hypothesis_id="h2", claim="Maybe something")
        assert h2.is_falsifiable is False

    def test_is_discriminative(self):
        h = StructuredHypothesis(
            hypothesis_id="h1",
            claim="X causes Y",
            derived_predictions=["p1"],
            alternative_explanations=["h2"],
        )
        assert h.is_discriminative is True

    def test_ad_hoc_complexity(self):
        h = StructuredHypothesis(
            hypothesis_id="h1", claim="X", rescue_assumptions=3
        )
        assert h.ad_hoc_complexity == 3


class TestHypothesisEcology:
    def _make_ecology(self) -> HypothesisEcology:
        h1 = StructuredHypothesis(
            hypothesis_id="h1", claim="A", confidence=0.6,
            status=HypothesisStatus.ACTIVE,
        )
        h2 = StructuredHypothesis(
            hypothesis_id="h2", claim="B", confidence=0.3,
            status=HypothesisStatus.ACTIVE,
        )
        h3 = StructuredHypothesis(
            hypothesis_id="h3", claim="C", confidence=0.1,
            status=HypothesisStatus.ABANDONED,
        )
        return HypothesisEcology(hypotheses={"h1": h1, "h2": h2, "h3": h3})

    def test_active_hypotheses(self):
        eco = self._make_ecology()
        assert eco.count == 3
        assert eco.active_count == 2
        assert "h3" not in eco.active_hypotheses

    def test_belief_distribution(self):
        eco = self._make_ecology()
        dist = eco.belief_distribution()
        assert dist["h1"] == 0.6
        assert dist["h2"] == 0.3
        assert "h3" not in dist

    def test_entropy(self):
        eco = self._make_ecology()
        e = eco.entropy()
        assert e > 0  # Non-zero entropy with two hypotheses

    def test_top_hypothesis(self):
        eco = self._make_ecology()
        top = eco.top_hypothesis()
        assert top is not None
        assert top.hypothesis_id == "h1"

    def test_margin(self):
        eco = self._make_ecology()
        m = eco.margin()
        assert m == pytest.approx(0.3)


class TestBeliefState:
    def test_get_set_belief(self):
        bs = BeliefState(beliefs={"h1": 0.5})
        assert bs.get_belief("h1") == 0.5
        assert bs.get_belief("unknown") == 0.5  # Default

        bs2 = bs.set_belief("h1", 0.8)
        assert bs2.get_belief("h1") == 0.8
        assert bs.get_belief("h1") == 0.5  # Original unchanged

    def test_clamping(self):
        bs = BeliefState(beliefs={"h1": 0.5})
        bs2 = bs.set_belief("h1", 1.5)
        assert bs2.get_belief("h1") == 1.0

        bs3 = bs.set_belief("h1", -0.3)
        assert bs3.get_belief("h1") == 0.0

    def test_record_update(self):
        bs = BeliefState(beliefs={"h1": 0.5})
        bs2 = bs.record_update("h1", 0.5, 0.7, "e1", 1)
        assert len(bs2.history) == 1
        assert bs2.history[0].prior == 0.5
        assert bs2.history[0].posterior == 0.7
        assert bs2.history[0].update_magnitude == pytest.approx(0.2)


class TestScientificBudget:
    def test_exhaustion(self):
        b = ScientificBudget(max_steps=5, steps_used=5)
        assert b.is_exhausted is True

        b2 = ScientificBudget(max_steps=5, steps_used=3)
        assert b2.is_exhausted is False

    def test_fraction_remaining(self):
        b = ScientificBudget(max_steps=10, max_llm_calls=20, steps_used=5, llm_calls_used=10)
        assert b.fraction_remaining == 0.5


class TestIgnoranceItem:
    def test_priority(self):
        item = IgnoranceItem(
            unknown_id="u1",
            question="What is X?",
            decision_relevance=0.8,
            expected_impact=0.9,
            resolvability=0.7,
            estimated_cost=2.0,
        )
        expected = (0.8 * 0.9 * 0.7) / 2.0
        assert item.priority == pytest.approx(expected)


class TestScientificState:
    def test_creation_and_versioning(self):
        state = ScientificState(
            version=0,
            episode_id="ep1",
            research_question="Does X cause Y?",
        )
        assert state.version == 0
        assert state.ecology.count == 0
        assert state.conclusion is None

        state2 = state.with_version(1)
        assert state2.version == 1
        assert state.version == 0  # Immutable
