"""
Falsification Engine — the core scientific self-correction mechanism.

For every leading hypothesis, this engine:
1. Identifies the strongest potential falsifier
2. Determines which assumptions are attacked
3. Derives predicted observations if the falsifier is real
4. Proposes evidence searches to find disconfirmation
5. Estimates expected information gain from falsification attempts

The critical distinction:
    CONSISTENT EVIDENCE ≠ DISCRIMINATIVE EVIDENCE

This engine focuses on discrimination and disconfirmation, NOT confirmation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from asar.scientific_discovery.state import (
    Assumption,
    EvidenceDirection,
    Falsifier,
    HypothesisEcology,
    Prediction,
    ScientificEvidence,
    ScientificState,
    StructuredHypothesis,
)


@dataclass
class FalsificationProposal:
    """Output of the falsification engine for a target hypothesis."""

    target_hypothesis_id: str
    strongest_falsifier: Falsifier | None
    critical_assumptions_attacked: list[str]
    predicted_observations: list[str]
    proposed_evidence_search: str
    expected_information_gain: float
    failure_modes: list[str]
    rationale: str


@dataclass
class DiscriminationAnalysis:
    """Analysis of how well evidence/experiments discriminate between hypotheses."""

    hypothesis_pair: tuple[str, str]
    discriminability: float  # [0, 1] — how differently they predict the same observation
    distinguishing_predictions: list[str]
    shared_predictions: list[str]
    best_discriminative_test: str


class FalsificationEngine:
    """
    Implements the FALSIFY_HYPOTHESIS operator.

    This is NOT a confirmation engine. It actively seeks the STRONGEST
    way a hypothesis could fail.
    """

    def __init__(
        self,
        *,
        min_falsifier_impact: float = 0.3,
        min_discriminability: float = 0.2,
    ) -> None:
        self._min_impact = min_falsifier_impact
        self._min_discriminability = min_discriminability

    def propose_falsification(
        self,
        state: ScientificState,
        target_hypothesis_id: str,
    ) -> FalsificationProposal:
        """
        Generate the strongest falsification proposal for a hypothesis.

        This examines:
        1. Existing falsifiers — which are most impactful and feasible?
        2. Assumptions — which are most critical and least tested?
        3. Competing hypotheses — what would competing theories predict differently?
        """
        hypothesis = state.ecology.hypotheses.get(target_hypothesis_id)
        if hypothesis is None:
            return FalsificationProposal(
                target_hypothesis_id=target_hypothesis_id,
                strongest_falsifier=None,
                critical_assumptions_attacked=[],
                predicted_observations=[],
                proposed_evidence_search="",
                expected_information_gain=0.0,
                failure_modes=["Hypothesis not found"],
                rationale="Target hypothesis does not exist in ecology",
            )

        # Find strongest existing falsifier
        strongest = self._find_strongest_falsifier(state, hypothesis)

        # Identify critical untested assumptions
        critical_assumptions = self._find_critical_assumptions(state, hypothesis)

        # Derive predictions from falsification
        predicted_obs = self._derive_falsification_predictions(state, hypothesis, strongest)

        # Compute expected information gain
        eig = self._estimate_information_gain(state, hypothesis, strongest)

        # Propose search strategy
        search_proposal = self._propose_search(hypothesis, strongest, critical_assumptions)

        # Identify failure modes of the falsification attempt
        failure_modes = self._identify_failure_modes(hypothesis, strongest)

        return FalsificationProposal(
            target_hypothesis_id=target_hypothesis_id,
            strongest_falsifier=strongest,
            critical_assumptions_attacked=[a.assumption_id for a in critical_assumptions],
            predicted_observations=predicted_obs,
            proposed_evidence_search=search_proposal,
            expected_information_gain=eig,
            failure_modes=failure_modes,
            rationale=self._build_rationale(hypothesis, strongest, critical_assumptions),
        )

    def analyze_discrimination(
        self,
        state: ScientificState,
        hypothesis_a_id: str,
        hypothesis_b_id: str,
    ) -> DiscriminationAnalysis:
        """Analyze how well two hypotheses can be distinguished."""
        hyp_a = state.ecology.hypotheses.get(hypothesis_a_id)
        hyp_b = state.ecology.hypotheses.get(hypothesis_b_id)

        if hyp_a is None or hyp_b is None:
            return DiscriminationAnalysis(
                hypothesis_pair=(hypothesis_a_id, hypothesis_b_id),
                discriminability=0.0,
                distinguishing_predictions=[],
                shared_predictions=[],
                best_discriminative_test="",
            )

        # Find predictions unique to each
        preds_a = set(hyp_a.derived_predictions)
        preds_b = set(hyp_b.derived_predictions)
        shared = preds_a & preds_b
        unique_a = preds_a - shared
        unique_b = preds_b - shared
        distinguishing = list(unique_a | unique_b)

        # Compute discriminability based on prediction overlap
        total_preds = len(preds_a | preds_b)
        if total_preds == 0:
            discriminability = 0.0
        else:
            discriminability = len(distinguishing) / total_preds

        # Find best discriminative test from predictions
        best_test = ""
        best_power = 0.0
        for pred_id in distinguishing:
            pred = state.predictions.get(pred_id)
            if pred and pred.discriminating_power > best_power:
                best_power = pred.discriminating_power
                best_test = pred.statement

        return DiscriminationAnalysis(
            hypothesis_pair=(hypothesis_a_id, hypothesis_b_id),
            discriminability=discriminability,
            distinguishing_predictions=distinguishing,
            shared_predictions=list(shared),
            best_discriminative_test=best_test,
        )

    def pairwise_discrimination_matrix(
        self,
        state: ScientificState,
    ) -> dict[tuple[str, str], float]:
        """Compute pairwise discriminability for all active hypothesis pairs."""
        active_ids = list(state.ecology.active_hypotheses.keys())
        matrix: dict[tuple[str, str], float] = {}

        for i, hid_a in enumerate(active_ids):
            for hid_b in active_ids[i + 1:]:
                analysis = self.analyze_discrimination(state, hid_a, hid_b)
                matrix[(hid_a, hid_b)] = analysis.discriminability
                matrix[(hid_b, hid_a)] = analysis.discriminability

        return matrix

    def evaluate_evidence_as_falsifier(
        self,
        state: ScientificState,
        evidence: ScientificEvidence,
        hypothesis_id: str,
    ) -> float:
        """
        Score how strongly a piece of evidence falsifies a hypothesis.

        Returns a falsification score [0, 1]:
        - 0 = evidence does not falsify
        - 1 = evidence is a decisive falsifier
        """
        if evidence.direction != EvidenceDirection.CONTRADICTING:
            return 0.0

        relevance = evidence.relevance_to_hypotheses.get(hypothesis_id, 0.0)
        score = relevance * evidence.reliability

        # Check if evidence matches any registered falsifier
        hypothesis = state.ecology.hypotheses.get(hypothesis_id)
        if hypothesis:
            for fid in hypothesis.potential_falsifiers:
                falsifier = state.falsifiers.get(fid)
                if falsifier and not falsifier.observed:
                    score = max(score, falsifier.impact_if_observed * evidence.reliability)

        return min(1.0, score)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_strongest_falsifier(
        self,
        state: ScientificState,
        hypothesis: StructuredHypothesis,
    ) -> Falsifier | None:
        """Find the most impactful and feasible unobserved falsifier."""
        best: Falsifier | None = None
        best_score = 0.0

        for fid in hypothesis.potential_falsifiers:
            falsifier = state.falsifiers.get(fid)
            if falsifier is None or falsifier.observed:
                continue
            # Score = impact × feasibility
            score = falsifier.impact_if_observed * falsifier.observation_feasibility
            if score > best_score and score >= self._min_impact:
                best_score = score
                best = falsifier

        return best

    def _find_critical_assumptions(
        self,
        state: ScientificState,
        hypothesis: StructuredHypothesis,
    ) -> list[Assumption]:
        """Find high-criticality untested assumptions."""
        critical = []
        for aid in hypothesis.assumptions:
            assumption = state.assumptions.get(aid)
            if assumption and not assumption.tested and assumption.criticality > 0.5:
                critical.append(assumption)
        critical.sort(key=lambda a: a.criticality, reverse=True)
        return critical[:3]

    def _derive_falsification_predictions(
        self,
        state: ScientificState,
        hypothesis: StructuredHypothesis,
        falsifier: Falsifier | None,
    ) -> list[str]:
        """What observations would we expect if the hypothesis is wrong?"""
        predictions = list(hypothesis.expected_observations_if_false)

        if falsifier:
            predictions.append(
                f"If '{falsifier.statement}' is observed, "
                f"belief should drop by ~{falsifier.impact_if_observed:.0%}"
            )

        # Add predictions from competing hypotheses
        for alt_id in hypothesis.alternative_explanations:
            alt = state.ecology.hypotheses.get(alt_id)
            if alt:
                for obs in alt.expected_observations_if_true[:2]:
                    predictions.append(f"Alternative ({alt.claim[:50]}...): expects {obs}")

        return predictions[:5]

    def _estimate_information_gain(
        self,
        state: ScientificState,
        hypothesis: StructuredHypothesis,
        falsifier: Falsifier | None,
    ) -> float:
        """Estimate expected information gain from pursuing this falsification."""
        if falsifier is None:
            return 0.1  # Low EIG without a concrete falsifier

        # EIG ≈ P(falsifier observed) × information_if_observed
        # + P(falsifier not observed) × information_if_not_observed
        current_belief = hypothesis.confidence

        # Information from observing falsifier (large belief change)
        info_if_observed = falsifier.impact_if_observed * current_belief

        # Information from NOT observing falsifier (modest confidence increase)
        info_if_not = (1 - falsifier.impact_if_observed) * (1 - current_belief) * 0.3

        # Weight by feasibility (proxy for probability of observation)
        eig = (
            falsifier.observation_feasibility * info_if_observed
            + (1 - falsifier.observation_feasibility) * info_if_not
        )

        return min(1.0, eig)

    def _propose_search(
        self,
        hypothesis: StructuredHypothesis,
        falsifier: Falsifier | None,
        critical_assumptions: list[Assumption],
    ) -> str:
        """Propose a search strategy for disconfirmation."""
        parts = []

        if falsifier:
            parts.append(f"Search for evidence of: {falsifier.statement}")
            if falsifier.attack_vector:
                parts.append(f"Attack vector: {falsifier.attack_vector}")

        for assumption in critical_assumptions[:2]:
            parts.append(f"Test assumption: {assumption.text}")

        if not parts:
            parts.append(
                f"Search for observations inconsistent with: {hypothesis.claim}"
            )

        return " | ".join(parts)

    def _identify_failure_modes(
        self,
        hypothesis: StructuredHypothesis,
        falsifier: Falsifier | None,
    ) -> list[str]:
        """What could go wrong with this falsification attempt?"""
        modes = []

        if falsifier is None:
            modes.append("No concrete falsifier identified — falsification is underspecified")
        elif falsifier.observation_feasibility < 0.3:
            modes.append("Falsifier has low observation feasibility — may be practically untestable")

        if hypothesis.rescue_assumptions > 2:
            modes.append(
                "Hypothesis already has rescue assumptions — "
                "may resist falsification through further ad-hoc additions"
            )

        if not hypothesis.alternative_explanations:
            modes.append("No alternatives registered — falsification without fallback is less useful")

        return modes

    def _build_rationale(
        self,
        hypothesis: StructuredHypothesis,
        falsifier: Falsifier | None,
        critical_assumptions: list[Assumption],
    ) -> str:
        """Build human-readable rationale for the falsification proposal."""
        parts = [f"Target: {hypothesis.claim[:80]}"]

        if falsifier:
            parts.append(f"Strongest falsifier: {falsifier.statement[:80]}")
            parts.append(
                f"Expected impact: {falsifier.impact_if_observed:.0%} belief reduction"
            )
        else:
            parts.append("No registered falsifier — hypothesis may lack falsifiability")

        if critical_assumptions:
            parts.append(
                f"Critical untested assumptions: {len(critical_assumptions)} "
                f"(highest criticality: {critical_assumptions[0].criticality:.2f})"
            )

        return " | ".join(parts)
