"""
Controlled Scientific Worlds — benchmark scenarios with known ground truth.

Each world provides:
- A research question
- An initial hypothesis ecology (with the correct and wrong hypotheses)
- A sequence of evidence rounds (some misleading, some decisive)
- Ground truth for evaluation

These worlds are designed around SCIENTIFIC FAILURE MODES, not around ASAR's policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from asar.common.ids import generate_id
from asar.scientific_discovery.controller import EvidenceRound
from asar.scientific_discovery.state import (
    Assumption,
    AssumptionCategory,
    BeliefState,
    EvidenceDirection,
    Falsifier,
    HypothesisEcology,
    HypothesisMaturity,
    HypothesisStatus,
    Prediction,
    ScientificBudget,
    ScientificEvidence,
    ScientificState,
    SourceType,
    StructuredHypothesis,
)


@dataclass
class WorldGroundTruth:
    """Ground truth for evaluation of a controlled world."""

    correct_hypothesis_id: Optional[str]
    world_type: str
    expected_conclusion: str
    decisive_round: Optional[int]
    expected_belief_trajectory: dict[str, list[str]]


@dataclass
class ControlledWorld:
    """A complete controlled scientific world for benchmarking."""

    world_id: str
    name: str
    world_type: str
    description: str
    initial_state: ScientificState
    evidence_rounds: list[EvidenceRound]
    ground_truth: WorldGroundTruth


def create_confirmation_trap_world(
    *,
    seed: int = 42,
    difficulty: str = "medium",
) -> ControlledWorld:
    """
    CONFIRMATION TRAP — Early evidence favors wrong hypothesis.

    Setup: H1 (wrong) appears well-supported initially.
           H2 (correct) has weaker initial support.
    Evidence sequence:
        Round 0: Strong support for H1
        Round 1: Weak contradiction of H1
        Round 2: DECISIVE falsification of H1
        Round 3: Strong support for H2

    Correct behavior: Abandon H1 after Round 2, converge on H2 after Round 3.
    Failure mode: Theory stickiness — retaining H1 despite falsification.
    """
    h1_id = f"ct_h1_{seed}"
    h2_id = f"ct_h2_{seed}"
    h3_id = f"ct_h3_{seed}"
    f1_id = f"ct_f1_{seed}"
    p1_id = f"ct_p1_{seed}"
    p2_id = f"ct_p2_{seed}"
    a1_id = f"ct_a1_{seed}"

    # Build hypotheses
    h1 = StructuredHypothesis(
        hypothesis_id=h1_id,
        claim="Drug X reduces inflammation via COX-2 inhibition",
        causal_mechanism="Selective COX-2 inhibition reduces prostaglandin synthesis",
        scope="Acute inflammation in human cell lines",
        assumptions=[a1_id],
        derived_predictions=[p1_id],
        expected_observations_if_true=["Reduced PGE2 levels", "COX-2 activity decreases"],
        expected_observations_if_false=["PGE2 levels unchanged", "COX-2 unaffected"],
        potential_falsifiers=[f1_id],
        alternative_explanations=[h2_id, h3_id],
        confidence=0.5,
        maturity=HypothesisMaturity.H2_FALSIFIABLE,
        status=HypothesisStatus.ACTIVE,
    )

    h2 = StructuredHypothesis(
        hypothesis_id=h2_id,
        claim="Drug X reduces inflammation via NF-kB pathway modulation",
        causal_mechanism="Direct inhibition of NF-kB nuclear translocation",
        scope="Acute inflammation in human cell lines",
        assumptions=[],
        derived_predictions=[p2_id],
        expected_observations_if_true=["Reduced nuclear NF-kB", "Decreased IL-6"],
        expected_observations_if_false=["NF-kB unchanged", "IL-6 unchanged"],
        potential_falsifiers=[],
        alternative_explanations=[h1_id, h3_id],
        confidence=0.5,
        maturity=HypothesisMaturity.H2_FALSIFIABLE,
        status=HypothesisStatus.ACTIVE,
    )

    h3 = StructuredHypothesis(
        hypothesis_id=h3_id,
        claim="Drug X has no genuine anti-inflammatory effect (placebo/artifact)",
        causal_mechanism="Observed effect is measurement artifact or placebo",
        scope="Null hypothesis",
        confidence=0.3,
        alternative_explanations=[h1_id, h2_id],
        maturity=HypothesisMaturity.H1_MECHANISTIC,
        status=HypothesisStatus.ACTIVE,
    )

    # Build supporting objects
    assumption = Assumption(
        assumption_id=a1_id,
        text="Drug X reaches sufficient concentration to inhibit COX-2",
        criticality=0.8,
        dependent_hypothesis_ids=[h1_id],
        category=AssumptionCategory.AUXILIARY,
    )

    falsifier = Falsifier(
        falsifier_id=f1_id,
        hypothesis_id=h1_id,
        statement="Drug X shows no binding affinity to COX-2 in cell-free assay",
        attack_vector="COX-2 binding assumption",
        observation_feasibility=0.9,
        impact_if_observed=0.85,
    )

    pred1 = Prediction(
        prediction_id=p1_id,
        hypothesis_id=h1_id,
        statement="COX-2 activity reduced by >50% at therapeutic dose",
        discriminating_power=0.7,
        expected_if_true="COX-2 activity < 50% of control",
        expected_if_false="COX-2 activity unchanged",
    )

    pred2 = Prediction(
        prediction_id=p2_id,
        hypothesis_id=h2_id,
        statement="NF-kB nuclear translocation reduced by >40%",
        discriminating_power=0.8,
        expected_if_true="NF-kB in nucleus < 60% of control",
        expected_if_false="NF-kB translocation unchanged",
    )

    # Build evidence rounds
    rounds = _build_confirmation_trap_evidence(h1_id, h2_id, h3_id, seed, difficulty)

    # Assemble state
    ecology = HypothesisEcology(hypotheses={h1_id: h1, h2_id: h2, h3_id: h3})

    state = ScientificState(
        version=0,
        episode_id=f"ct_episode_{seed}",
        research_question="What is the mechanism by which Drug X reduces inflammation?",
        ecology=ecology,
        assumptions={a1_id: assumption},
        predictions={p1_id: pred1, p2_id: pred2},
        falsifiers={f1_id: falsifier},
        beliefs=_initial_beliefs({h1_id: 0.5, h2_id: 0.5, h3_id: 0.3}),
        budget=ScientificBudget(max_steps=20),
    )

    ground_truth = WorldGroundTruth(
        correct_hypothesis_id=h2_id,
        world_type="confirmation_trap",
        expected_conclusion="supported",
        decisive_round=2,
        expected_belief_trajectory={
            h1_id: ["increase", "decrease_slight", "decrease_major", "low"],
            h2_id: ["stable", "stable", "increase_slight", "increase_major"],
        },
    )

    return ControlledWorld(
        world_id=f"ct_world_{seed}",
        name=f"Confirmation Trap (Drug X mechanism, seed={seed})",
        world_type="confirmation_trap",
        description="Early evidence favors wrong COX-2 hypothesis; later decisive evidence reveals NF-kB mechanism",
        initial_state=state,
        evidence_rounds=rounds,
        ground_truth=ground_truth,
    )


def create_non_identifiable_world(
    *,
    seed: int = 42,
) -> ControlledWorld:
    """
    NON-IDENTIFIABLE WORLD — Evidence cannot distinguish hypotheses.

    Setup: H1 and H2 make identical predictions given available evidence.
    Correct behavior: ABSTAIN / declare non-identifiable / request experiment.
    Failure mode: Forcing a conclusion when evidence is insufficient.
    """
    h1_id = f"ni_h1_{seed}"
    h2_id = f"ni_h2_{seed}"

    h1 = StructuredHypothesis(
        hypothesis_id=h1_id,
        claim="Protein A activates pathway through direct binding",
        causal_mechanism="Direct physical interaction with receptor",
        expected_observations_if_true=["Pathway activation", "Dose-response curve"],
        expected_observations_if_false=["No activation"],
        confidence=0.5,
        maturity=HypothesisMaturity.H2_FALSIFIABLE,
        status=HypothesisStatus.ACTIVE,
        alternative_explanations=[h2_id],
    )

    h2 = StructuredHypothesis(
        hypothesis_id=h2_id,
        claim="Protein A activates pathway through indirect signaling cascade",
        causal_mechanism="Activation of intermediate kinase that then activates receptor",
        expected_observations_if_true=["Pathway activation", "Dose-response curve"],
        expected_observations_if_false=["No activation"],
        confidence=0.5,
        maturity=HypothesisMaturity.H2_FALSIFIABLE,
        status=HypothesisStatus.ACTIVE,
        alternative_explanations=[h1_id],
    )

    # Evidence is ambiguous — supports both equally
    rounds = [
        EvidenceRound(
            round_number=0,
            evidence=[ScientificEvidence(
                evidence_id=f"ni_e0_{seed}",
                content="Pathway activation observed at 10nM concentration",
                source="Lab assay",
                source_type=SourceType.OBSERVATION,
                reliability=0.9,
                relevance_to_hypotheses={h1_id: 0.7, h2_id: 0.7},
                direction=EvidenceDirection.SUPPORTING,
            )],
            decisive=False,
        ),
        EvidenceRound(
            round_number=1,
            evidence=[ScientificEvidence(
                evidence_id=f"ni_e1_{seed}",
                content="Dose-response curve consistent with single-site binding model",
                source="Pharmacology study",
                source_type=SourceType.LITERATURE,
                reliability=0.8,
                relevance_to_hypotheses={h1_id: 0.6, h2_id: 0.5},
                direction=EvidenceDirection.AMBIGUOUS,
            )],
            decisive=False,
        ),
        EvidenceRound(
            round_number=2,
            evidence=[ScientificEvidence(
                evidence_id=f"ni_e2_{seed}",
                content="Both direct binding and cascade models predict observed kinetics equally well",
                source="Computational modeling",
                source_type=SourceType.COMPUTATION,
                reliability=0.85,
                relevance_to_hypotheses={h1_id: 0.5, h2_id: 0.5},
                direction=EvidenceDirection.NEUTRAL,
            )],
            decisive=False,
        ),
    ]

    ecology = HypothesisEcology(hypotheses={h1_id: h1, h2_id: h2})

    state = ScientificState(
        version=0,
        episode_id=f"ni_episode_{seed}",
        research_question="How does Protein A activate the downstream pathway?",
        ecology=ecology,
        beliefs=_initial_beliefs({h1_id: 0.5, h2_id: 0.5}),
        budget=ScientificBudget(max_steps=10),
    )

    ground_truth = WorldGroundTruth(
        correct_hypothesis_id=None,
        world_type="non_identifiable",
        expected_conclusion="not_identifiable",
        decisive_round=None,
        expected_belief_trajectory={
            h1_id: ["stable", "stable", "stable"],
            h2_id: ["stable", "stable", "stable"],
        },
    )

    return ControlledWorld(
        world_id=f"ni_world_{seed}",
        name=f"Non-Identifiable (Protein A mechanism, seed={seed})",
        world_type="non_identifiable",
        description="Two hypotheses make identical predictions; correct behavior is to abstain",
        initial_state=state,
        evidence_rounds=rounds,
        ground_truth=ground_truth,
    )


def create_confounded_causality_world(
    *,
    seed: int = 42,
) -> ControlledWorld:
    """
    CONFOUNDED CAUSALITY — Hidden variable explains observed correlation.

    Setup: Correlation between X and Y suggests X→Y.
    Truth: Confounder Z causes both X and Y.
    Evidence: Progressive revelation of Z.
    Correct behavior: Detect confounding, reduce causal claim belief.
    """
    h1_id = f"cc_h1_{seed}"
    h2_id = f"cc_h2_{seed}"
    f1_id = f"cc_f1_{seed}"

    h1 = StructuredHypothesis(
        hypothesis_id=h1_id,
        claim="Social media use directly causes increased anxiety in teenagers",
        causal_mechanism="Dopamine dysregulation from intermittent reinforcement",
        expected_observations_if_true=["Correlation persists after controlling for confounders"],
        expected_observations_if_false=["Correlation disappears with proper controls"],
        potential_falsifiers=[f1_id],
        confidence=0.6,
        maturity=HypothesisMaturity.H2_FALSIFIABLE,
        status=HypothesisStatus.ACTIVE,
        alternative_explanations=[h2_id],
    )

    h2 = StructuredHypothesis(
        hypothesis_id=h2_id,
        claim="Pre-existing anxiety drives both social media use and measured anxiety",
        causal_mechanism="Anxious individuals seek social validation online AND report higher anxiety",
        expected_observations_if_true=["Correlation disappears when controlling for baseline anxiety"],
        expected_observations_if_false=["Effect persists after baseline control"],
        confidence=0.4,
        maturity=HypothesisMaturity.H2_FALSIFIABLE,
        status=HypothesisStatus.ACTIVE,
        alternative_explanations=[h1_id],
    )

    falsifier = Falsifier(
        falsifier_id=f1_id,
        hypothesis_id=h1_id,
        statement="Randomized reduction in social media use shows no anxiety improvement",
        attack_vector="Causal direction",
        observation_feasibility=0.7,
        impact_if_observed=0.8,
    )

    rounds = [
        EvidenceRound(
            round_number=0,
            evidence=[ScientificEvidence(
                evidence_id=f"cc_e0_{seed}",
                content="Large cross-sectional study: r=0.35 between daily screen time and anxiety scores",
                source="Journal of Adolescent Health",
                source_type=SourceType.LITERATURE,
                reliability=0.8,
                relevance_to_hypotheses={h1_id: 0.8, h2_id: 0.4},
                direction=EvidenceDirection.SUPPORTING,
            )],
            decisive=False,
        ),
        EvidenceRound(
            round_number=1,
            evidence=[ScientificEvidence(
                evidence_id=f"cc_e1_{seed}",
                content="Longitudinal study: baseline anxiety predicts BOTH social media use increase AND later anxiety; social media coefficient non-significant after baseline control",
                source="Developmental Psychology",
                source_type=SourceType.LITERATURE,
                reliability=0.85,
                relevance_to_hypotheses={h1_id: 0.9, h2_id: 0.9},
                direction=EvidenceDirection.CONTRADICTING,
            )],
            decisive=True,
            description="Decisive evidence revealing confound",
        ),
        EvidenceRound(
            round_number=2,
            evidence=[ScientificEvidence(
                evidence_id=f"cc_e2_{seed}",
                content="RCT: 4-week social media reduction shows no significant anxiety improvement vs control (d=0.05, p=0.72)",
                source="Nature Human Behaviour",
                source_type=SourceType.COMPUTATION,
                reliability=0.9,
                relevance_to_hypotheses={h1_id: 0.95, h2_id: 0.3},
                direction=EvidenceDirection.CONTRADICTING,
            )],
            decisive=True,
            description="Experimental confirmation of confound",
        ),
    ]

    ecology = HypothesisEcology(hypotheses={h1_id: h1, h2_id: h2})

    state = ScientificState(
        version=0,
        episode_id=f"cc_episode_{seed}",
        research_question="Does social media use cause increased anxiety in teenagers?",
        ecology=ecology,
        falsifiers={f1_id: falsifier},
        beliefs=_initial_beliefs({h1_id: 0.6, h2_id: 0.4}),
        budget=ScientificBudget(max_steps=10),
    )

    ground_truth = WorldGroundTruth(
        correct_hypothesis_id=h2_id,
        world_type="confounded_causality",
        expected_conclusion="supported",
        decisive_round=1,
        expected_belief_trajectory={
            h1_id: ["increase", "decrease_major", "decrease_major"],
            h2_id: ["stable", "increase_major", "increase"],
        },
    )

    return ControlledWorld(
        world_id=f"cc_world_{seed}",
        name=f"Confounded Causality (Social media/anxiety, seed={seed})",
        world_type="confounded_causality",
        description="Initial correlation suggests direct causation; longitudinal + RCT data reveals confound",
        initial_state=state,
        evidence_rounds=rounds,
        ground_truth=ground_truth,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _initial_beliefs(beliefs: dict[str, float]) -> BeliefState:
    return BeliefState(beliefs=beliefs)


def _build_confirmation_trap_evidence(
    h1_id: str,
    h2_id: str,
    h3_id: str,
    seed: int,
    difficulty: str,
) -> list[EvidenceRound]:
    """Build evidence rounds for confirmation trap."""
    reliability_mod = {"easy": 0.95, "medium": 0.85, "hard": 0.7}.get(difficulty, 0.85)

    return [
        # Round 0: Strong support for H1 (misleading)
        EvidenceRound(
            round_number=0,
            evidence=[ScientificEvidence(
                evidence_id=f"ct_e0_{seed}",
                content="In vitro assay shows Drug X reduces PGE2 production by 60% — consistent with COX-2 inhibition",
                source="Initial screening study",
                source_type=SourceType.OBSERVATION,
                reliability=reliability_mod,
                relevance_to_hypotheses={h1_id: 0.9, h2_id: 0.2, h3_id: 0.1},
                direction=EvidenceDirection.SUPPORTING,
            )],
            decisive=False,
            description="Misleading initial evidence favoring H1",
        ),
        # Round 1: Weak contradiction
        EvidenceRound(
            round_number=1,
            evidence=[ScientificEvidence(
                evidence_id=f"ct_e1_{seed}",
                content="Structural analysis suggests Drug X has low predicted binding affinity to COX-2 active site (docking score: -4.2 kcal/mol, threshold for activity typically < -7)",
                source="Computational chemistry",
                source_type=SourceType.COMPUTATION,
                reliability=0.6,
                relevance_to_hypotheses={h1_id: 0.7, h2_id: 0.1, h3_id: 0.2},
                direction=EvidenceDirection.CONTRADICTING,
            )],
            decisive=False,
            description="Weak contradictory evidence against H1",
        ),
        # Round 2: DECISIVE falsification of H1
        EvidenceRound(
            round_number=2,
            evidence=[ScientificEvidence(
                evidence_id=f"ct_e2_{seed}",
                content="Cell-free COX-2 binding assay: Drug X shows NO detectable binding at concentrations up to 100μM (Ki > 100μM). COX-2 mechanism is ruled out.",
                source="Biochemical assay — gold standard",
                source_type=SourceType.OBSERVATION,
                reliability=0.95,
                relevance_to_hypotheses={h1_id: 0.99, h2_id: 0.1, h3_id: 0.3},
                direction=EvidenceDirection.CONTRADICTING,
            )],
            decisive=True,
            description="DECISIVE: Drug X does not bind COX-2 at all",
        ),
        # Round 3: Strong support for H2
        EvidenceRound(
            round_number=3,
            evidence=[ScientificEvidence(
                evidence_id=f"ct_e3_{seed}",
                content="NF-kB reporter assay: Drug X reduces NF-kB nuclear translocation by 75% at 10μM. Confirmed in 3 cell lines. Mechanism: direct IKK inhibition.",
                source="Molecular biology study",
                source_type=SourceType.OBSERVATION,
                reliability=0.9,
                relevance_to_hypotheses={h1_id: 0.1, h2_id: 0.95, h3_id: 0.05},
                direction=EvidenceDirection.SUPPORTING,
            )],
            decisive=False,
            description="Strong evidence supporting correct hypothesis H2",
        ),
    ]
