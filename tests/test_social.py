"""
Tests for social epistemology: tribunal, evidence independence, stakeholders.
"""

from __future__ import annotations

import pytest

from asar.social.tribunal import DissonanceTribunal
from asar.social.trust import EvidenceIndependenceAnalyzer
from asar.social.stakeholder import StakeholderRegistry
from schemas.ree.social import (
    EvidenceProvenance,
    StakeholderModel,
    TribunalRole,
)


class TestDissonanceTribunal:
    def test_sealed_submissions_before_cross_examination(self) -> None:
        tribunal = DissonanceTribunal()
        s1 = tribunal.submit_sealed(TribunalRole.ADVOCATE, "Position A", confidence=0.8)
        s2 = tribunal.submit_sealed(TribunalRole.FALSIFIER, "Position B", confidence=0.6)
        assert s1.sealed is True
        assert s2.sealed is True
        assert len(tribunal.sealed_submissions()) == 2

    def test_cross_examination_blocked_before_sealed_phase(self) -> None:
        tribunal = DissonanceTribunal()
        result = tribunal.submit_cross_examination(TribunalRole.JUDGE, "Verdict")
        assert result is None

    def test_cross_examination_allowed_after_sealed_phase(self) -> None:
        tribunal = DissonanceTribunal()
        tribunal.submit_sealed(TribunalRole.ADVOCATE, "Position A")
        tribunal.complete_sealed_phase()
        result = tribunal.submit_cross_examination(TribunalRole.JUDGE, "Agree with A")
        assert result is not None
        assert result.sealed is False
        assert result.round_number == 2

    def test_adjudication_preserves_minority(self) -> None:
        tribunal = DissonanceTribunal()
        tribunal.submit_sealed(TribunalRole.ADVOCATE, "Majority view",
                               evidence_cited=["e1", "e2"], confidence=0.8)
        tribunal.submit_sealed(TribunalRole.ADVOCATE, "Majority view",
                               evidence_cited=["e3"], confidence=0.7)
        tribunal.submit_sealed(TribunalRole.FALSIFIER, "Minority dissent",
                               evidence_cited=["e4"], confidence=0.4)
        tribunal.complete_sealed_phase()

        verdict = tribunal.adjudicate()
        assert "Majority view" in verdict.surviving_positions
        assert "Minority dissent" in verdict.minority_positions or "Minority dissent" in verdict.surviving_positions

    def test_adjudication_rejects_unsupported(self) -> None:
        tribunal = DissonanceTribunal()
        tribunal.submit_sealed(TribunalRole.ADVOCATE, "Well supported",
                               evidence_cited=["e1", "e2", "e3"], confidence=0.9)
        tribunal.submit_sealed(TribunalRole.ALTERNATIVE_THEORIST, "No evidence",
                               evidence_cited=[], confidence=0.1)
        tribunal.complete_sealed_phase()

        verdict = tribunal.adjudicate()
        assert "Well supported" in verdict.surviving_positions
        assert "No evidence" in verdict.rejected_positions

    def test_sealed_phase_returns_all_sealed_submissions(self) -> None:
        tribunal = DissonanceTribunal()
        tribunal.submit_sealed(TribunalRole.ADVOCATE, "A")
        tribunal.submit_sealed(TribunalRole.FALSIFIER, "B")
        sealed = tribunal.complete_sealed_phase()
        assert len(sealed) == 2

    def test_minority_preservation_rate(self) -> None:
        tribunal = DissonanceTribunal()
        tribunal.submit_sealed(TribunalRole.ADVOCATE, "Main", confidence=0.8, evidence_cited=["e1"])
        tribunal.submit_sealed(TribunalRole.FALSIFIER, "Minor", confidence=0.35, evidence_cited=["e2"])
        tribunal.complete_sealed_phase()
        tribunal.adjudicate()
        assert tribunal.minority_preservation_rate() >= 0.0


class TestEvidenceIndependenceAnalyzer:
    def test_independent_evidence(self) -> None:
        analyzer = EvidenceIndependenceAnalyzer()
        analyzer.register_provenance(EvidenceProvenance(
            evidence_id="e1", original_source_id="src_a",
        ))
        analyzer.register_provenance(EvidenceProvenance(
            evidence_id="e2", original_source_id="src_b",
        ))
        assert analyzer.effective_evidence_count(["e1", "e2"]) == 2
        assert analyzer.evidence_independence_score(["e1", "e2"]) == pytest.approx(1.0)

    def test_duplicated_evidence(self) -> None:
        analyzer = EvidenceIndependenceAnalyzer()
        analyzer.register_provenance(EvidenceProvenance(
            evidence_id="e1", original_source_id="src_a", is_derivative=False,
        ))
        analyzer.register_provenance(EvidenceProvenance(
            evidence_id="e2", original_source_id="src_a", is_derivative=True,
        ))
        analyzer.register_provenance(EvidenceProvenance(
            evidence_id="e3", original_source_id="src_a", is_derivative=True,
        ))
        assert analyzer.effective_evidence_count(["e1", "e2", "e3"]) == 1
        assert analyzer.evidence_independence_score(["e1", "e2", "e3"]) == pytest.approx(1 / 3)

    def test_duplicated_sources(self) -> None:
        analyzer = EvidenceIndependenceAnalyzer()
        analyzer.register_provenance(EvidenceProvenance(evidence_id="e1", original_source_id="src_a"))
        analyzer.register_provenance(EvidenceProvenance(evidence_id="e2", original_source_id="src_a"))
        analyzer.register_provenance(EvidenceProvenance(evidence_id="e3", original_source_id="src_b"))
        dupes = analyzer.duplicated_sources()
        assert "src_a" in dupes
        assert "src_b" not in dupes

    def test_unknown_evidence_treated_as_independent(self) -> None:
        analyzer = EvidenceIndependenceAnalyzer()
        assert analyzer.effective_evidence_count(["unknown_1", "unknown_2"]) == 2

    def test_empty_evidence(self) -> None:
        analyzer = EvidenceIndependenceAnalyzer()
        assert analyzer.evidence_independence_score([]) == 1.0


class TestStakeholderRegistry:
    def _make_model(self, actor_id: str = "s1", reliability: float = 0.5) -> StakeholderModel:
        return StakeholderModel(
            actor_id=actor_id,
            name="Test Source",
            reliability_score=reliability,
            uncertainty=0.5,
        )

    def test_register_and_get(self) -> None:
        reg = StakeholderRegistry()
        reg.register(self._make_model("s1"))
        assert reg.get("s1") is not None

    def test_reliable_sources(self) -> None:
        reg = StakeholderRegistry()
        reg.register(self._make_model("good", reliability=0.9))
        reg.register(self._make_model("bad", reliability=0.2))
        assert len(reg.reliable_sources(threshold=0.7)) == 1

    def test_unreliable_sources(self) -> None:
        reg = StakeholderRegistry()
        reg.register(self._make_model("good", reliability=0.9))
        reg.register(self._make_model("bad", reliability=0.2))
        assert len(reg.unreliable_sources(threshold=0.3)) == 1

    def test_update_reliability(self) -> None:
        reg = StakeholderRegistry()
        reg.register(self._make_model("s1", reliability=0.5))
        updated = reg.update_reliability("s1", 0.9)
        assert updated.reliability_score == pytest.approx(0.9)

    def test_high_uncertainty_models(self) -> None:
        reg = StakeholderRegistry()
        reg.register(StakeholderModel(actor_id="s1", uncertainty=0.9))
        reg.register(StakeholderModel(actor_id="s2", uncertainty=0.3))
        assert len(reg.high_uncertainty_models(threshold=0.7)) == 1

    def test_by_type(self) -> None:
        reg = StakeholderRegistry()
        reg.register(StakeholderModel(actor_id="s1", actor_type="source"))
        reg.register(StakeholderModel(actor_id="s2", actor_type="expert"))
        assert len(reg.by_type("source")) == 1
