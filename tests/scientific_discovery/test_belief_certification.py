"""
Belief-Updater Metamorphic Certification.

These are scientific invariants — more important than code coverage.
Each test verifies a property that ANY valid scientific belief updater must satisfy.
"""

import pytest

from asar.scientific_discovery.belief_updater import BeliefUpdater
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


def _make_hypothesis(hid: str = "h1", confidence: float = 0.5, **kwargs) -> StructuredHypothesis:
    return StructuredHypothesis(
        hypothesis_id=hid,
        claim=f"Hypothesis {hid}",
        confidence=confidence,
        status=HypothesisStatus.ACTIVE,
        maturity=HypothesisMaturity.H2_FALSIFIABLE,
        **kwargs,
    )


def _make_evidence(
    eid: str,
    direction: EvidenceDirection,
    reliability: float = 0.85,
    relevance: float = 0.8,
    hid: str = "h1",
) -> ScientificEvidence:
    return ScientificEvidence(
        evidence_id=eid,
        content=f"Evidence {eid}",
        direction=direction,
        reliability=reliability,
        relevance_to_hypotheses={hid: relevance},
        source_type=SourceType.LITERATURE,
    )


class TestDecisiveRefutation:
    """Strong valid refutation of H must NOT increase belief in H."""

    def test_strong_refutation_decreases_belief(self, updater):
        h = _make_hypothesis()
        e = _make_evidence("e1", EvidenceDirection.CONTRADICTING, reliability=0.95, relevance=0.95)
        result = updater.update_belief(h, e, 0.7)
        assert result.posterior < result.prior, "INVARIANT: Decisive refutation must decrease belief"

    def test_maximum_strength_refutation(self, updater):
        h = _make_hypothesis()
        e = _make_evidence("e2", EvidenceDirection.CONTRADICTING, reliability=1.0, relevance=1.0)
        result = updater.update_belief(h, e, 0.9)
        assert result.posterior < 0.9
        assert result.magnitude > 0.1, "Strong refutation should produce substantial belief drop"

    @pytest.mark.parametrize("initial_belief", [0.3, 0.5, 0.7, 0.9])
    def test_refutation_never_increases_at_any_prior(self, updater, initial_belief):
        h = _make_hypothesis()
        e = _make_evidence("e3", EvidenceDirection.CONTRADICTING, reliability=0.9, relevance=0.9)
        result = updater.update_belief(h, e, initial_belief)
        assert result.posterior <= initial_belief, (
            f"INVARIANT VIOLATED: Refutation increased belief from {initial_belief} to {result.posterior}"
        )


class TestStrongSupport:
    """Valid independent support should normally increase belief."""

    def test_support_increases_belief(self, updater):
        h = _make_hypothesis()
        e = _make_evidence("e1", EvidenceDirection.SUPPORTING, reliability=0.9, relevance=0.8)
        result = updater.update_belief(h, e, 0.5)
        assert result.posterior > result.prior

    @pytest.mark.parametrize("initial_belief", [0.2, 0.4, 0.6])
    def test_support_increases_at_various_priors(self, updater, initial_belief):
        h = _make_hypothesis()
        e = _make_evidence("e_s", EvidenceDirection.SUPPORTING, reliability=0.85, relevance=0.8)
        result = updater.update_belief(h, e, initial_belief)
        assert result.posterior > initial_belief


class TestIrrelevantEvidence:
    """Irrelevant evidence should produce approximately zero update."""

    def test_zero_relevance_no_effect(self, updater):
        h = _make_hypothesis()
        e = ScientificEvidence(
            evidence_id="irr1",
            content="Completely irrelevant",
            direction=EvidenceDirection.SUPPORTING,
            reliability=0.9,
            relevance_to_hypotheses={"h1": 0.0},
        )
        result = updater.update_belief(h, e, 0.5)
        assert abs(result.posterior - 0.5) < 0.01

    def test_neutral_direction_no_effect(self, updater):
        h = _make_hypothesis()
        e = _make_evidence("n1", EvidenceDirection.NEUTRAL, relevance=0.8)
        result = updater.update_belief(h, e, 0.6)
        assert result.posterior == result.prior

    def test_very_low_relevance_minimal_effect(self, updater):
        h = _make_hypothesis()
        e = _make_evidence("low_r", EvidenceDirection.SUPPORTING, relevance=0.01, reliability=0.9)
        result = updater.update_belief(h, e, 0.5)
        assert abs(result.posterior - 0.5) < 0.02


class TestDuplicateEvidence:
    """Duplicating the exact same evidence/source must not double-count."""

    def test_low_independence_reduces_update(self, updater):
        h = _make_hypothesis()
        e = _make_evidence("dup", EvidenceDirection.SUPPORTING, reliability=0.8, relevance=0.7)

        # Full independence
        r_full = updater.update_belief(h, e, 0.5, independence_score=1.0)
        # Near-zero independence (same source repeated)
        r_dup = updater.update_belief(h, e, 0.5, independence_score=0.05)

        assert r_dup.magnitude < r_full.magnitude, (
            "Duplicate evidence (low independence) must have smaller effect than independent"
        )

    def test_sequential_duplicates_bounded(self, updater):
        """Applying same evidence 5 times should not 5× the effect."""
        h = _make_hypothesis()
        e = _make_evidence("rep", EvidenceDirection.SUPPORTING, reliability=0.8, relevance=0.7)

        belief = 0.5
        for _ in range(5):
            result = updater.update_belief(h, e, belief, independence_score=0.1)
            belief = result.posterior

        # 5 duplicate applications should be much less than 5× independent
        single_result = updater.update_belief(h, e, 0.5, independence_score=1.0)
        five_independent_effect = single_result.magnitude * 5

        actual_effect = belief - 0.5
        assert actual_effect < five_independent_effect * 0.7, (
            f"5 duplicate sources produced {actual_effect:.4f} vs 5×independent {five_independent_effect:.4f}"
        )


class TestDependentEvidence:
    """Evidence from same underlying study should count less than independent evidence."""

    def test_dependent_less_than_independent(self, updater):
        h = _make_hypothesis()
        e = _make_evidence("dep", EvidenceDirection.SUPPORTING, reliability=0.8, relevance=0.7)

        r_ind = updater.update_belief(h, e, 0.5, independence_score=1.0)
        r_dep = updater.update_belief(h, e, 0.5, independence_score=0.3)

        assert r_dep.magnitude < r_ind.magnitude


class TestEvidenceReversal:
    """Replacing support with contradiction should reverse update direction."""

    def test_opposite_directions_opposite_effects(self, updater):
        h = _make_hypothesis()

        e_sup = _make_evidence("sup", EvidenceDirection.SUPPORTING, reliability=0.8, relevance=0.7)
        e_con = _make_evidence("con", EvidenceDirection.CONTRADICTING, reliability=0.8, relevance=0.7)

        r_sup = updater.update_belief(h, e_sup, 0.5)
        r_con = updater.update_belief(h, e_con, 0.5)

        assert r_sup.posterior > 0.5
        assert r_con.posterior < 0.5

    def test_reversal_magnitude_appropriate(self, updater):
        """Contradiction should produce at least as large a magnitude as support (falsification multiplier)."""
        h = _make_hypothesis()

        e_sup = _make_evidence("s", EvidenceDirection.SUPPORTING, reliability=0.85, relevance=0.8)
        e_con = _make_evidence("c", EvidenceDirection.CONTRADICTING, reliability=0.85, relevance=0.8)

        r_sup = updater.update_belief(h, e_sup, 0.5)
        r_con = updater.update_belief(h, e_con, 0.5)

        # With falsification_multiplier > 1, contradiction should be larger
        assert r_con.magnitude >= r_sup.magnitude


class TestOrderRobustness:
    """Equivalent independent evidence in different order should not diverge wildly."""

    def test_two_evidence_order_independence(self, updater):
        h = _make_hypothesis()
        e_a = _make_evidence("ea", EvidenceDirection.SUPPORTING, reliability=0.7, relevance=0.6)
        e_b = _make_evidence("eb", EvidenceDirection.SUPPORTING, reliability=0.8, relevance=0.7)

        # Order A→B
        r1 = updater.update_belief(h, e_a, 0.5)
        r2 = updater.update_belief(h, e_b, r1.posterior)
        final_ab = r2.posterior

        # Order B→A
        r3 = updater.update_belief(h, e_b, 0.5)
        r4 = updater.update_belief(h, e_a, r3.posterior)
        final_ba = r4.posterior

        # Should be reasonably close (exact commutativity not required for additive updates)
        assert abs(final_ab - final_ba) < 0.1, (
            f"Order sensitivity too high: A→B={final_ab:.4f} vs B→A={final_ba:.4f}"
        )


class TestExtremeConfidenceProtection:
    """Belief must remain bounded and numerically stable."""

    def test_belief_never_exceeds_one(self, updater):
        h = _make_hypothesis()
        e = _make_evidence("strong", EvidenceDirection.SUPPORTING, reliability=1.0, relevance=1.0)

        belief = 0.99
        for _ in range(10):
            result = updater.update_belief(h, e, belief)
            belief = result.posterior
            assert belief <= 1.0

    def test_belief_never_below_zero(self, updater):
        h = _make_hypothesis()
        e = _make_evidence("harsh", EvidenceDirection.CONTRADICTING, reliability=1.0, relevance=1.0)

        belief = 0.01
        for _ in range(10):
            result = updater.update_belief(h, e, belief)
            belief = result.posterior
            assert belief >= 0.0

    def test_no_nan_or_inf(self, updater):
        """Edge cases must not produce NaN or infinity."""
        import math
        h = _make_hypothesis()
        e = _make_evidence("edge", EvidenceDirection.SUPPORTING, reliability=0.0, relevance=0.0)
        result = updater.update_belief(h, e, 0.0)
        assert not math.isnan(result.posterior)
        assert not math.isinf(result.posterior)


class TestNonIdentifiability:
    """Evidence that cannot distinguish H1/H2 must not create artificial separation."""

    def test_equal_relevance_no_separation(self, updater):
        """Evidence equally relevant to both hypotheses should not separate them."""
        h1 = _make_hypothesis("h1", confidence=0.5)
        h2 = _make_hypothesis("h2", confidence=0.5)

        e = ScientificEvidence(
            evidence_id="ambig",
            content="Supports both equally",
            direction=EvidenceDirection.SUPPORTING,
            reliability=0.8,
            relevance_to_hypotheses={"h1": 0.7, "h2": 0.7},
        )

        r1 = updater.update_belief(h1, e, 0.5)
        r2 = updater.update_belief(h2, e, 0.5)

        separation = abs(r1.posterior - r2.posterior)
        assert separation < 0.01, (
            f"Non-discriminating evidence created separation: {separation:.4f}"
        )

    def test_neutral_evidence_preserves_equality(self, updater):
        """Neutral evidence should not create a winner between equal hypotheses."""
        h1 = _make_hypothesis("h1")
        h2 = _make_hypothesis("h2")

        e = ScientificEvidence(
            evidence_id="neutral",
            content="Irrelevant",
            direction=EvidenceDirection.NEUTRAL,
            reliability=0.9,
            relevance_to_hypotheses={"h1": 0.5, "h2": 0.5},
        )

        r1 = updater.update_belief(h1, e, 0.5)
        r2 = updater.update_belief(h2, e, 0.5)

        assert r1.posterior == r2.posterior == 0.5
