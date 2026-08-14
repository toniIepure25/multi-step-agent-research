"""
Tests for BeliefUpdater — quantitative belief revision.

Includes metamorphic tests (benchmark validity invariants):
1. Decisive falsifier must NOT increase belief in target
2. Duplicate evidence must NOT double confidence
3. Irrelevant evidence must minimally affect belief
4. Evidence reversal must move posterior appropriately
"""

import pytest

from asar.scientific_discovery.belief_updater import BeliefUpdater, BeliefUpdateResult
from asar.scientific_discovery.state import (
    BeliefState,
    EvidenceDirection,
    HypothesisEcology,
    HypothesisMaturity,
    HypothesisStatus,
    ScientificEvidence,
    SourceType,
    StructuredHypothesis,
)


@pytest.fixture
def updater() -> BeliefUpdater:
    return BeliefUpdater()


@pytest.fixture
def hypothesis() -> StructuredHypothesis:
    return StructuredHypothesis(
        hypothesis_id="h1",
        claim="X causes Y",
        confidence=0.6,
        maturity=HypothesisMaturity.H2_FALSIFIABLE,
        status=HypothesisStatus.ACTIVE,
    )


class TestBasicUpdates:
    def test_supporting_evidence_increases_belief(self, updater, hypothesis):
        evidence = ScientificEvidence(
            evidence_id="e1",
            content="Supports H1",
            direction=EvidenceDirection.SUPPORTING,
            reliability=0.9,
            relevance_to_hypotheses={"h1": 0.8},
        )
        result = updater.update_belief(hypothesis, evidence, 0.5)
        assert result.posterior > result.prior

    def test_contradicting_evidence_decreases_belief(self, updater, hypothesis):
        evidence = ScientificEvidence(
            evidence_id="e2",
            content="Contradicts H1",
            direction=EvidenceDirection.CONTRADICTING,
            reliability=0.9,
            relevance_to_hypotheses={"h1": 0.8},
        )
        result = updater.update_belief(hypothesis, evidence, 0.6)
        assert result.posterior < result.prior

    def test_neutral_evidence_no_change(self, updater, hypothesis):
        evidence = ScientificEvidence(
            evidence_id="e3",
            content="Irrelevant observation",
            direction=EvidenceDirection.NEUTRAL,
            reliability=0.9,
            relevance_to_hypotheses={"h1": 0.5},
        )
        result = updater.update_belief(hypothesis, evidence, 0.5)
        assert result.posterior == result.prior

    def test_belief_stays_bounded(self, updater, hypothesis):
        strong_support = ScientificEvidence(
            evidence_id="e4",
            content="Very strong support",
            direction=EvidenceDirection.SUPPORTING,
            reliability=1.0,
            relevance_to_hypotheses={"h1": 1.0},
        )
        result = updater.update_belief(hypothesis, strong_support, 0.95)
        assert result.posterior <= 1.0

        strong_contra = ScientificEvidence(
            evidence_id="e5",
            content="Very strong contradiction",
            direction=EvidenceDirection.CONTRADICTING,
            reliability=1.0,
            relevance_to_hypotheses={"h1": 1.0},
        )
        result2 = updater.update_belief(hypothesis, strong_contra, 0.05)
        assert result2.posterior >= 0.0


class TestMetamorphicInvariants:
    """
    Metamorphic tests — these validate the BENCHMARK, not just the system.
    If these fail, the belief updater violates scientific reasoning invariants.
    """

    def test_decisive_falsifier_never_increases_belief(self, updater, hypothesis):
        """Adding valid decisive refutation must NOT increase belief in target."""
        falsifier_evidence = ScientificEvidence(
            evidence_id="f1",
            content="Decisive refutation of H1",
            direction=EvidenceDirection.CONTRADICTING,
            reliability=0.95,
            relevance_to_hypotheses={"h1": 0.99},
        )
        result = updater.update_belief(hypothesis, falsifier_evidence, 0.7)
        assert result.posterior <= result.prior, (
            f"INVARIANT VIOLATED: Falsifier increased belief from {result.prior} to {result.posterior}"
        )

    def test_duplicate_evidence_not_double_effect(self, updater, hypothesis):
        """Duplicating same source must NOT double confidence."""
        evidence = ScientificEvidence(
            evidence_id="e_dup",
            content="Supports H1",
            direction=EvidenceDirection.SUPPORTING,
            reliability=0.8,
            relevance_to_hypotheses={"h1": 0.7},
        )

        # First application
        result1 = updater.update_belief(hypothesis, evidence, 0.5)

        # Second application with low independence (same source)
        result2 = updater.update_belief(hypothesis, evidence, result1.posterior, independence_score=0.1)

        # Single fresh application
        fresh_result = updater.update_belief(hypothesis, evidence, 0.5, independence_score=1.0)

        # The cumulative effect of duplicate should be less than 2× single
        total_dup_effect = result2.posterior - 0.5
        single_effect = fresh_result.posterior - 0.5
        assert total_dup_effect < 2 * single_effect, (
            f"INVARIANT VIOLATED: Duplicate evidence doubled effect "
            f"({total_dup_effect:.4f} vs 2×{single_effect:.4f})"
        )

    def test_irrelevant_evidence_minimal_effect(self, updater, hypothesis):
        """Adding irrelevant evidence must minimally affect belief."""
        irrelevant = ScientificEvidence(
            evidence_id="irr",
            content="Completely unrelated observation about weather",
            direction=EvidenceDirection.NEUTRAL,
            reliability=0.9,
            relevance_to_hypotheses={"h1": 0.0},
        )
        result = updater.update_belief(hypothesis, irrelevant, 0.6)
        change = abs(result.posterior - result.prior)
        assert change < 0.01, (
            f"INVARIANT VIOLATED: Irrelevant evidence changed belief by {change}"
        )

    def test_evidence_direction_reversal(self, updater, hypothesis):
        """Replacing support with contradiction must move posterior appropriately."""
        support = ScientificEvidence(
            evidence_id="sup",
            content="Supports H1",
            direction=EvidenceDirection.SUPPORTING,
            reliability=0.8,
            relevance_to_hypotheses={"h1": 0.8},
        )
        contra = ScientificEvidence(
            evidence_id="con",
            content="Contradicts H1",
            direction=EvidenceDirection.CONTRADICTING,
            reliability=0.8,
            relevance_to_hypotheses={"h1": 0.8},
        )

        result_support = updater.update_belief(hypothesis, support, 0.5)
        result_contra = updater.update_belief(hypothesis, contra, 0.5)

        # Contradiction should move in opposite direction from support
        assert result_support.posterior > 0.5
        assert result_contra.posterior < 0.5


class TestAbandonmentThreshold:
    def test_should_abandon_below_threshold(self, updater, hypothesis):
        assert updater.should_abandon(hypothesis, 0.05) is True
        assert updater.should_abandon(hypothesis, 0.15) is False

    def test_rescue_assumption_penalty(self):
        updater = BeliefUpdater(rescue_penalty_per_assumption=0.05)
        hyp_with_rescue = StructuredHypothesis(
            hypothesis_id="h_rescue",
            claim="Theory with ad hoc fixes",
            confidence=0.5,
            rescue_assumptions=3,
            status=HypothesisStatus.ACTIVE,
        )
        hyp_without = StructuredHypothesis(
            hypothesis_id="h_clean",
            claim="Clean theory",
            confidence=0.5,
            rescue_assumptions=0,
            status=HypothesisStatus.ACTIVE,
        )

        evidence = ScientificEvidence(
            evidence_id="e_same",
            content="Neutral-ish evidence",
            direction=EvidenceDirection.SUPPORTING,
            reliability=0.7,
            relevance_to_hypotheses={"h_rescue": 0.5, "h_clean": 0.5},
        )

        result_rescue = updater.update_belief(hyp_with_rescue, evidence, 0.5)
        result_clean = updater.update_belief(hyp_without, evidence, 0.5)

        # Hypothesis with rescue assumptions should gain less
        assert result_rescue.posterior < result_clean.posterior


class TestEcologyUpdate:
    def test_updates_all_active(self, updater):
        h1 = StructuredHypothesis(
            hypothesis_id="h1", claim="A", confidence=0.5,
            status=HypothesisStatus.ACTIVE,
        )
        h2 = StructuredHypothesis(
            hypothesis_id="h2", claim="B", confidence=0.5,
            status=HypothesisStatus.ACTIVE,
        )
        h3 = StructuredHypothesis(
            hypothesis_id="h3", claim="C", confidence=0.5,
            status=HypothesisStatus.ABANDONED,
        )
        ecology = HypothesisEcology(hypotheses={"h1": h1, "h2": h2, "h3": h3})
        beliefs = BeliefState(beliefs={"h1": 0.5, "h2": 0.5, "h3": 0.5})

        evidence = ScientificEvidence(
            evidence_id="e1",
            content="Supports H1",
            direction=EvidenceDirection.SUPPORTING,
            reliability=0.8,
            relevance_to_hypotheses={"h1": 0.9, "h2": 0.2},
        )

        results = updater.update_ecology(ecology, evidence, beliefs)
        # Should update h1 and h2 (active), not h3 (abandoned)
        assert len(results) == 2
        h1_result = next(r for r in results if r.hypothesis_id == "h1")
        h2_result = next(r for r in results if r.hypothesis_id == "h2")
        assert h1_result.posterior > h2_result.posterior
