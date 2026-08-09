"""
Dissonance Tribunal — epistemic institution with sealed first round.

NOT ordinary multi-agent debate. Critical rule: participants must initially
reason independently without seeing other conclusions. Only after independent
commitments are persisted may cross-examination begin.
"""

from __future__ import annotations

from asar.common import generate_id
from schemas.ree.social import TribunalRole, TribunalSubmission, TribunalVerdict


class DissonanceTribunal:
    """Manages a sealed-first-round deliberation process."""

    def __init__(self) -> None:
        self._submissions: list[TribunalSubmission] = []
        self._verdicts: list[TribunalVerdict] = []
        self._sealed_phase_complete = False

    def submit_sealed(
        self,
        role: TribunalRole,
        position: str,
        hypothesis_id: str = "",
        evidence_cited: list[str] | None = None,
        confidence: float = 0.5,
    ) -> TribunalSubmission:
        """Submit an independent assessment during the sealed round."""
        sub = TribunalSubmission(
            submission_id=generate_id("submission"),
            role=role,
            hypothesis_id=hypothesis_id,
            position=position,
            evidence_cited=evidence_cited or [],
            confidence=confidence,
            sealed=True,
            round_number=1,
        )
        self._submissions.append(sub)
        return sub

    def complete_sealed_phase(self) -> list[TribunalSubmission]:
        """Mark sealed phase as complete. Returns all sealed submissions."""
        self._sealed_phase_complete = True
        return [s for s in self._submissions if s.sealed and s.round_number == 1]

    @property
    def is_sealed_phase_complete(self) -> bool:
        return self._sealed_phase_complete

    def submit_cross_examination(
        self,
        role: TribunalRole,
        position: str,
        hypothesis_id: str = "",
        evidence_cited: list[str] | None = None,
        confidence: float = 0.5,
    ) -> TribunalSubmission | None:
        """Submit a cross-examination response (only after sealed phase)."""
        if not self._sealed_phase_complete:
            return None

        sub = TribunalSubmission(
            submission_id=generate_id("submission"),
            role=role,
            hypothesis_id=hypothesis_id,
            position=position,
            evidence_cited=evidence_cited or [],
            confidence=confidence,
            sealed=False,
            round_number=2,
        )
        self._submissions.append(sub)
        return sub

    def adjudicate(self, hypothesis_id: str = "") -> TribunalVerdict:
        """Produce a verdict based on evidence weight, not majority vote.

        Preserves minority positions that remain evidentially plausible.
        """
        relevant = [s for s in self._submissions if not hypothesis_id or s.hypothesis_id == hypothesis_id]

        position_evidence: dict[str, list[str]] = {}
        position_confidence: dict[str, list[float]] = {}
        for s in relevant:
            if s.position not in position_evidence:
                position_evidence[s.position] = []
                position_confidence[s.position] = []
            position_evidence[s.position].extend(s.evidence_cited)
            position_confidence[s.position].append(s.confidence)

        surviving: list[str] = []
        rejected: list[str] = []
        minority: list[str] = []

        for position, confidences in position_confidence.items():
            avg_conf = sum(confidences) / len(confidences)
            evidence_count = len(set(position_evidence.get(position, [])))

            if avg_conf >= 0.5 or evidence_count >= 2:
                surviving.append(position)
            elif avg_conf >= 0.3 or evidence_count >= 1:
                minority.append(position)
            else:
                rejected.append(position)

        overall_conf = 0.5
        if surviving:
            all_confs = []
            for pos in surviving:
                all_confs.extend(position_confidence[pos])
            overall_conf = sum(all_confs) / len(all_confs) if all_confs else 0.5

        verdict = TribunalVerdict(
            verdict_id=generate_id("verdict"),
            hypothesis_id=hypothesis_id,
            surviving_positions=surviving,
            rejected_positions=rejected,
            minority_positions=minority,
            consensus_confidence=overall_conf,
        )
        self._verdicts.append(verdict)
        return verdict

    def all_submissions(self) -> list[TribunalSubmission]:
        return list(self._submissions)

    def sealed_submissions(self) -> list[TribunalSubmission]:
        return [s for s in self._submissions if s.sealed]

    def minority_preservation_rate(self) -> float:
        """MPR: fraction of verdicts where minority positions survived."""
        if not self._verdicts:
            return 0.0
        with_minority = sum(1 for v in self._verdicts if v.minority_positions)
        return with_minority / len(self._verdicts)
