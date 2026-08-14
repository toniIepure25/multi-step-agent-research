"""
Extended Controlled Worlds — Reverse Causality, Null World, Measurement Artifact.

Each world is designed around a SCIENTIFIC FAILURE MODE, not around ASAR's policy.
"""

from __future__ import annotations

from asar.scientific_discovery.controller import EvidenceRound
from asar.scientific_discovery.controlled_worlds import ControlledWorld, WorldGroundTruth
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


def create_reverse_causality_world(*, seed: int = 42) -> ControlledWorld:
    """
    REVERSE CAUSALITY — Observed X↔Y but causal direction is opposite to leading hypothesis.

    Setup: Correlation between exercise and mood.
    Tempting hypothesis: Exercise → Better Mood (X causes Y)
    Truth: Better Mood → Exercise (Y causes X) — people exercise MORE when already feeling good.

    Evidence:
        Round 0: Cross-sectional correlation (ambiguous direction)
        Round 1: Temporal precedence data showing mood predicts next-day exercise
        Round 2: Intervention study — forced exercise does NOT improve mood

    Correct behavior: Reduce belief in X→Y, increase belief in Y→X.
    """
    h1_id = f"rc_h1_{seed}"
    h2_id = f"rc_h2_{seed}"
    h3_id = f"rc_h3_{seed}"
    f1_id = f"rc_f1_{seed}"

    h1 = StructuredHypothesis(
        hypothesis_id=h1_id,
        claim="Regular exercise directly causes improved mood via endorphin release",
        causal_mechanism="Exercise → endorphin release → mood elevation",
        expected_observations_if_true=[
            "Forced exercise improves mood",
            "Exercise precedes mood improvement temporally",
        ],
        expected_observations_if_false=[
            "Forced exercise has no mood effect",
            "Mood improvement precedes exercise temporally",
        ],
        potential_falsifiers=[f1_id],
        alternative_explanations=[h2_id, h3_id],
        confidence=0.6,
        maturity=HypothesisMaturity.H2_FALSIFIABLE,
        status=HypothesisStatus.ACTIVE,
    )

    h2 = StructuredHypothesis(
        hypothesis_id=h2_id,
        claim="Good mood causes increased exercise — people exercise when they feel good",
        causal_mechanism="Positive affect → increased motivation → exercise behavior",
        expected_observations_if_true=[
            "Mood predicts next-day exercise",
            "Forced exercise doesn't improve mood",
        ],
        expected_observations_if_false=[
            "Exercise predicts next-day mood",
            "Forced exercise improves mood",
        ],
        alternative_explanations=[h1_id, h3_id],
        confidence=0.4,
        maturity=HypothesisMaturity.H2_FALSIFIABLE,
        status=HypothesisStatus.ACTIVE,
    )

    h3 = StructuredHypothesis(
        hypothesis_id=h3_id,
        claim="Both exercise and mood are driven by a third factor (e.g., sleep quality)",
        causal_mechanism="Good sleep → both better mood AND more energy for exercise",
        alternative_explanations=[h1_id, h2_id],
        confidence=0.3,
        maturity=HypothesisMaturity.H1_MECHANISTIC,
        status=HypothesisStatus.ACTIVE,
    )

    falsifier = Falsifier(
        falsifier_id=f1_id,
        hypothesis_id=h1_id,
        statement="Randomized exercise intervention shows no mood improvement",
        attack_vector="Causal direction from exercise to mood",
        observation_feasibility=0.8,
        impact_if_observed=0.8,
    )

    rounds = [
        EvidenceRound(
            round_number=0,
            evidence=[ScientificEvidence(
                evidence_id=f"rc_e0_{seed}",
                content="Cross-sectional survey (N=5000): r=0.42 between weekly exercise hours and mood scores",
                source="Health Psychology journal",
                source_type=SourceType.LITERATURE,
                reliability=0.7,
                relevance_to_hypotheses={h1_id: 0.6, h2_id: 0.5, h3_id: 0.4},
                direction=EvidenceDirection.SUPPORTING,
                direction_per_hypothesis={
                    h1_id: EvidenceDirection.SUPPORTING,
                    h2_id: EvidenceDirection.SUPPORTING,
                    h3_id: EvidenceDirection.SUPPORTING,
                },
            )],
            decisive=False,
        ),
        EvidenceRound(
            round_number=1,
            evidence=[ScientificEvidence(
                evidence_id=f"rc_e1_{seed}",
                content="Daily diary study (N=200, 30 days): Morning mood significantly predicts afternoon exercise (β=0.31, p<.001) but afternoon exercise does NOT predict next-morning mood (β=0.02, p=.71)",
                source="Journal of Behavioral Medicine",
                source_type=SourceType.OBSERVATION,
                reliability=0.85,
                relevance_to_hypotheses={h1_id: 0.9, h2_id: 0.9, h3_id: 0.3},
                direction=EvidenceDirection.CONTRADICTING,
                direction_per_hypothesis={
                    h1_id: EvidenceDirection.CONTRADICTING,
                    h2_id: EvidenceDirection.SUPPORTING,
                    h3_id: EvidenceDirection.NEUTRAL,
                },
            )],
            decisive=True,
            description="Temporal precedence contradicts X→Y, supports Y→X",
        ),
        EvidenceRound(
            round_number=2,
            evidence=[ScientificEvidence(
                evidence_id=f"rc_e2_{seed}",
                content="RCT (N=300): 12-week structured exercise program shows no significant mood improvement vs. active control (d=0.08, p=0.44). Compliance verified by accelerometry.",
                source="The Lancet Psychiatry",
                source_type=SourceType.COMPUTATION,
                reliability=0.92,
                relevance_to_hypotheses={h1_id: 0.95, h2_id: 0.5, h3_id: 0.2},
                direction=EvidenceDirection.CONTRADICTING,
                direction_per_hypothesis={
                    h1_id: EvidenceDirection.CONTRADICTING,
                    h2_id: EvidenceDirection.SUPPORTING,
                    h3_id: EvidenceDirection.NEUTRAL,
                },
            )],
            decisive=True,
            description="Intervention failure confirms reverse causality",
        ),
    ]

    ecology = HypothesisEcology(hypotheses={h1_id: h1, h2_id: h2, h3_id: h3})

    state = ScientificState(
        version=0,
        episode_id=f"rc_episode_{seed}",
        research_question="What is the causal relationship between exercise and mood?",
        ecology=ecology,
        falsifiers={f1_id: falsifier},
        beliefs=BeliefState(beliefs={h1_id: 0.6, h2_id: 0.4, h3_id: 0.3}),
        budget=ScientificBudget(max_steps=10),
    )

    ground_truth = WorldGroundTruth(
        correct_hypothesis_id=h2_id,
        world_type="reverse_causality",
        expected_conclusion="supported",
        decisive_round=1,
        expected_belief_trajectory={
            h1_id: ["increase_slight", "decrease_major", "decrease_major"],
            h2_id: ["stable", "increase", "increase"],
        },
    )

    return ControlledWorld(
        world_id=f"rc_world_{seed}",
        name=f"Reverse Causality (Exercise/Mood, seed={seed})",
        world_type="reverse_causality",
        description="Correlation suggests exercise→mood but temporal/intervention data reveals mood→exercise",
        initial_state=state,
        evidence_rounds=rounds,
        ground_truth=ground_truth,
    )


def create_null_world(*, seed: int = 42) -> ControlledWorld:
    """
    NULL WORLD — No meaningful causal relationship exists.

    Setup: Observed weak correlation between phone radiation and headaches.
    Truth: No causal relationship (coincidence + reporting bias).

    Correct behavior: Do NOT force a causal hypothesis to survive.
    Expected terminal state: UNDERDETERMINED or correctly reject all causal hypotheses.
    """
    h1_id = f"nw_h1_{seed}"
    h2_id = f"nw_h2_{seed}"
    h3_id = f"nw_h3_{seed}"

    h1 = StructuredHypothesis(
        hypothesis_id=h1_id,
        claim="Cell phone radiation causes headaches via thermal effects on neurons",
        causal_mechanism="RF radiation → localized heating → neural inflammation",
        confidence=0.4,
        maturity=HypothesisMaturity.H2_FALSIFIABLE,
        status=HypothesisStatus.ACTIVE,
        alternative_explanations=[h2_id, h3_id],
    )

    h2 = StructuredHypothesis(
        hypothesis_id=h2_id,
        claim="Cell phone radiation causes headaches via non-thermal electromagnetic sensitivity",
        causal_mechanism="EM fields → altered ion channel function → headache",
        confidence=0.3,
        maturity=HypothesisMaturity.H1_MECHANISTIC,
        status=HypothesisStatus.ACTIVE,
        alternative_explanations=[h1_id, h3_id],
    )

    h3 = StructuredHypothesis(
        hypothesis_id=h3_id,
        claim="No causal relationship — correlation is due to reporting bias and nocebo effect",
        causal_mechanism="Belief about radiation + attention to symptoms → reported headaches",
        confidence=0.4,
        maturity=HypothesisMaturity.H2_FALSIFIABLE,
        status=HypothesisStatus.ACTIVE,
        alternative_explanations=[h1_id, h2_id],
    )

    rounds = [
        EvidenceRound(
            round_number=0,
            evidence=[ScientificEvidence(
                evidence_id=f"nw_e0_{seed}",
                content="Observational study: self-reported cell phone users report 20% more headaches (OR=1.2, 95% CI [1.05, 1.38])",
                source="Epidemiology study",
                source_type=SourceType.LITERATURE,
                reliability=0.6,
                relevance_to_hypotheses={h1_id: 0.5, h2_id: 0.5, h3_id: 0.3},
                direction=EvidenceDirection.AMBIGUOUS,
                direction_per_hypothesis={
                    h1_id: EvidenceDirection.SUPPORTING,
                    h2_id: EvidenceDirection.SUPPORTING,
                    h3_id: EvidenceDirection.AMBIGUOUS,
                },
            )],
            decisive=False,
        ),
        EvidenceRound(
            round_number=1,
            evidence=[ScientificEvidence(
                evidence_id=f"nw_e1_{seed}",
                content="Double-blind sham-controlled exposure study (N=150): No significant difference in headache rates between real RF exposure and sham (p=0.68). Participants could not detect exposure above chance.",
                source="Bioelectromagnetics",
                source_type=SourceType.OBSERVATION,
                reliability=0.9,
                relevance_to_hypotheses={h1_id: 0.9, h2_id: 0.85, h3_id: 0.8},
                direction=EvidenceDirection.CONTRADICTING,
                direction_per_hypothesis={
                    h1_id: EvidenceDirection.CONTRADICTING,
                    h2_id: EvidenceDirection.CONTRADICTING,
                    h3_id: EvidenceDirection.SUPPORTING,
                },
            )],
            decisive=True,
            description="Double-blind shows no real effect — supports null",
        ),
        EvidenceRound(
            round_number=2,
            evidence=[ScientificEvidence(
                evidence_id=f"nw_e2_{seed}",
                content="Meta-analysis of 12 provocation studies: pooled effect d=0.01 (95% CI [-0.05, 0.07]). No evidence of any exposure-headache relationship. Nocebo identified as explanation for observational findings.",
                source="Cochrane Review",
                source_type=SourceType.META_ANALYSIS,
                reliability=0.95,
                relevance_to_hypotheses={h1_id: 0.95, h2_id: 0.9, h3_id: 0.85},
                direction=EvidenceDirection.CONTRADICTING,
                direction_per_hypothesis={
                    h1_id: EvidenceDirection.CONTRADICTING,
                    h2_id: EvidenceDirection.CONTRADICTING,
                    h3_id: EvidenceDirection.SUPPORTING,
                },
            )],
            decisive=True,
            description="Meta-analysis confirms null — nocebo explains observations",
        ),
    ]

    ecology = HypothesisEcology(hypotheses={h1_id: h1, h2_id: h2, h3_id: h3})

    state = ScientificState(
        version=0,
        episode_id=f"nw_episode_{seed}",
        research_question="Does cell phone radiation cause headaches?",
        ecology=ecology,
        beliefs=BeliefState(beliefs={h1_id: 0.4, h2_id: 0.3, h3_id: 0.4}),
        budget=ScientificBudget(max_steps=10),
    )

    ground_truth = WorldGroundTruth(
        correct_hypothesis_id=h3_id,
        world_type="null_world",
        expected_conclusion="supported",
        decisive_round=1,
        expected_belief_trajectory={
            h1_id: ["stable", "decrease_major", "decrease_major"],
            h2_id: ["stable", "decrease_major", "decrease_major"],
            h3_id: ["stable", "increase", "increase"],
        },
    )

    return ControlledWorld(
        world_id=f"nw_world_{seed}",
        name=f"Null World (Phone radiation/headaches, seed={seed})",
        world_type="null_world",
        description="Weak observational correlation; double-blind + meta-analysis shows no real effect",
        initial_state=state,
        evidence_rounds=rounds,
        ground_truth=ground_truth,
    )


def create_measurement_artifact_world(*, seed: int = 42) -> ControlledWorld:
    """
    MEASUREMENT ARTIFACT — Apparent phenomenon is caused by measurement bias.

    Setup: Gene expression study shows apparent upregulation in disease tissue.
    Truth: The "upregulation" is a batch effect from sample processing, not biology.

    Correct behavior: Detect artifact, reduce signal belief.
    """
    h1_id = f"ma_h1_{seed}"
    h2_id = f"ma_h2_{seed}"
    h3_id = f"ma_h3_{seed}"

    h1 = StructuredHypothesis(
        hypothesis_id=h1_id,
        claim="Gene X is genuinely upregulated in tumor tissue, driving proliferation",
        causal_mechanism="Oncogenic signaling → Gene X transcription → cell proliferation",
        confidence=0.55,
        maturity=HypothesisMaturity.H2_FALSIFIABLE,
        status=HypothesisStatus.ACTIVE,
        alternative_explanations=[h2_id, h3_id],
    )

    h2 = StructuredHypothesis(
        hypothesis_id=h2_id,
        claim="Apparent Gene X upregulation is a batch effect from RNA degradation in tumor samples",
        causal_mechanism="Tumor samples processed later → RNA degradation → GC-bias → apparent upregulation of GC-rich genes including Gene X",
        confidence=0.3,
        maturity=HypothesisMaturity.H2_FALSIFIABLE,
        status=HypothesisStatus.ACTIVE,
        alternative_explanations=[h1_id, h3_id],
    )

    h3 = StructuredHypothesis(
        hypothesis_id=h3_id,
        claim="Gene X is upregulated but is a passenger, not a driver",
        causal_mechanism="Nearby oncogene drives region; Gene X co-amplified but non-functional",
        confidence=0.25,
        maturity=HypothesisMaturity.H1_MECHANISTIC,
        status=HypothesisStatus.ACTIVE,
        alternative_explanations=[h1_id, h2_id],
    )

    rounds = [
        EvidenceRound(
            round_number=0,
            evidence=[ScientificEvidence(
                evidence_id=f"ma_e0_{seed}",
                content="Microarray study: Gene X shows 4.2-fold upregulation in 50 tumor vs 50 normal samples (FDR < 0.001)",
                source="Cancer Research",
                source_type=SourceType.LITERATURE,
                reliability=0.7,
                relevance_to_hypotheses={h1_id: 0.8, h2_id: 0.3, h3_id: 0.5},
                direction=EvidenceDirection.SUPPORTING,
                direction_per_hypothesis={
                    h1_id: EvidenceDirection.SUPPORTING,
                    h2_id: EvidenceDirection.AMBIGUOUS,
                    h3_id: EvidenceDirection.SUPPORTING,
                },
            )],
            decisive=False,
        ),
        EvidenceRound(
            round_number=1,
            evidence=[ScientificEvidence(
                evidence_id=f"ma_e1_{seed}",
                content="Batch analysis: All tumor samples processed in weeks 3-4, all normals in weeks 1-2. Gene X is in top 5% GC-content genes. RIN scores: tumor mean=6.2, normal mean=8.8. After batch correction, Gene X fold-change drops to 1.1 (non-significant).",
                source="Bioinformatics re-analysis",
                source_type=SourceType.COMPUTATION,
                reliability=0.88,
                relevance_to_hypotheses={h1_id: 0.9, h2_id: 0.95, h3_id: 0.5},
                direction=EvidenceDirection.CONTRADICTING,
                direction_per_hypothesis={
                    h1_id: EvidenceDirection.CONTRADICTING,
                    h2_id: EvidenceDirection.SUPPORTING,
                    h3_id: EvidenceDirection.CONTRADICTING,
                },
            )],
            decisive=True,
            description="Batch effect revealed — supports artifact hypothesis",
        ),
        EvidenceRound(
            round_number=2,
            evidence=[ScientificEvidence(
                evidence_id=f"ma_e2_{seed}",
                content="Independent RNA-seq with matched processing (same day extraction): Gene X shows no differential expression (log2FC=0.05, padj=0.91). Three other GC-rich genes from original study also lose significance.",
                source="Independent validation study",
                source_type=SourceType.OBSERVATION,
                reliability=0.92,
                relevance_to_hypotheses={h1_id: 0.95, h2_id: 0.9, h3_id: 0.7},
                direction=EvidenceDirection.CONTRADICTING,
                direction_per_hypothesis={
                    h1_id: EvidenceDirection.CONTRADICTING,
                    h2_id: EvidenceDirection.SUPPORTING,
                    h3_id: EvidenceDirection.CONTRADICTING,
                },
            )],
            decisive=True,
            description="Independent replication confirms artifact",
        ),
    ]

    ecology = HypothesisEcology(hypotheses={h1_id: h1, h2_id: h2, h3_id: h3})

    state = ScientificState(
        version=0,
        episode_id=f"ma_episode_{seed}",
        research_question="Is Gene X a genuine oncogenic driver in this tumor type?",
        ecology=ecology,
        beliefs=BeliefState(beliefs={h1_id: 0.55, h2_id: 0.3, h3_id: 0.25}),
        budget=ScientificBudget(max_steps=10),
    )

    ground_truth = WorldGroundTruth(
        correct_hypothesis_id=h2_id,
        world_type="measurement_artifact",
        expected_conclusion="supported",
        decisive_round=1,
        expected_belief_trajectory={
            h1_id: ["increase", "decrease_major", "decrease_major"],
            h2_id: ["stable", "increase_major", "increase"],
        },
    )

    return ControlledWorld(
        world_id=f"ma_world_{seed}",
        name=f"Measurement Artifact (Gene expression batch effect, seed={seed})",
        world_type="measurement_artifact",
        description="Initial microarray shows upregulation; batch analysis reveals RNA degradation artifact",
        initial_state=state,
        evidence_rounds=rounds,
        ground_truth=ground_truth,
    )
