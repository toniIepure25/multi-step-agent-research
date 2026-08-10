"""
V4 Heterogeneous Epistemic Regimes.

Each regime creates worlds where a genuinely different cognitive strategy
is optimal. The agent never sees the regime label.

Regimes A-H create structurally distinct information landscapes that
reward different cognitive motifs.
"""

from __future__ import annotations

import hashlib

from asar.evaluation.simulator import (
    CausalEdge,
    EvidenceSource,
    HiddenVariable,
    Hypothesis,
    LatentEvidence,
    LatentWorld,
)


def _sub_seed(family: str, index: int, seed: int) -> int:
    h = hashlib.sha256(f"{family}_{index}_{seed}".encode()).hexdigest()
    return int(h[:8], 16)


def generate_regime_a_exploration_deficit(
    *, index: int = 0, seed: int = 100,
) -> LatentWorld:
    """
    Regime A — Exploration Deficit.
    
    World starts with only 1 obvious hypothesis. The true hypothesis
    is non-obvious and requires active hypothesis generation to discover.
    Evidence is abundant but useless without the right hypothesis.
    
    Optimal: generate_hypothesis -> retrieve -> reason
    Suboptimal: retrieve-heavy (evidence without hypothesis = useless)
    """
    sub = _sub_seed("regime_a", index, seed)

    h_obvious = Hypothesis("H_obvious", "Obvious but wrong initial framing",
                           is_true=False, initial_plausibility=0.75)
    h_hidden = Hypothesis("H_hidden", "Non-obvious correct hypothesis",
                          is_true=True, initial_plausibility=0.15)
    h_distractor = Hypothesis("H_distractor", "Alternative wrong hypothesis",
                              is_true=False, initial_plausibility=0.10)

    sources = [
        EvidenceSource(f"src_{i}", reliability=0.7 + 0.05 * (sub % 4))
        for i in range(6)
    ]

    evidence = [
        LatentEvidence("E_general_1", sources[0],
                       "General observation consistent with H_obvious",
                       supports_hypotheses=("H_obvious",),
                       information_value=0.15),
        LatentEvidence("E_general_2", sources[1],
                       "Another general observation",
                       supports_hypotheses=("H_obvious",),
                       information_value=0.1),
        LatentEvidence("E_anomaly", sources[2],
                       "Anomalous observation that only H_hidden explains",
                       supports_hypotheses=("H_hidden",),
                       contradicts_hypotheses=("H_obvious",),
                       information_value=0.85),
        LatentEvidence("E_decisive", sources[3],
                       "Decisive evidence for H_hidden",
                       supports_hypotheses=("H_hidden",),
                       contradicts_hypotheses=("H_obvious", "H_distractor"),
                       information_value=0.95),
        LatentEvidence("E_noise_1", sources[4],
                       "Irrelevant background data",
                       information_value=0.05),
        LatentEvidence("E_noise_2", sources[5],
                       "More irrelevant data",
                       information_value=0.05),
    ]

    return LatentWorld(
        world_id=f"regime_a_{seed}_{index}",
        hypotheses={"H_obvious": h_obvious, "H_hidden": h_hidden,
                    "H_distractor": h_distractor},
        evidence_pool=evidence,
        source_registry={s.source_id: s for s in sources},
        true_hypothesis_id="H_hidden",
        correct_conclusion="H_hidden is correct",
    )


def generate_regime_b_evidence_deficit(
    *, index: int = 0, seed: int = 100,
) -> LatentWorld:
    """
    Regime B — Evidence Deficit.
    
    Both correct and incorrect hypotheses are already visible/easy to generate.
    The distinguishing evidence is scarce and requires targeted retrieval.
    
    Optimal: retrieve -> retrieve -> reason (targeted evidence gathering)
    Suboptimal: generate_hypothesis (hypotheses already known)
    """
    sub = _sub_seed("regime_b", index, seed)

    h_correct = Hypothesis("H_correct", "Correct hypothesis, known but unconfirmed",
                           is_true=True, initial_plausibility=0.45)
    h_rival = Hypothesis("H_rival", "Strong rival, also plausible",
                         is_true=False, initial_plausibility=0.50)

    src_shallow = EvidenceSource("shallow_src", reliability=0.5)
    src_deep = EvidenceSource("deep_src", reliability=0.92)
    src_confirming = EvidenceSource("confirming_src", reliability=0.88)

    n_shallow = 2 + (sub % 3)
    evidence = []
    for i in range(n_shallow):
        evidence.append(LatentEvidence(
            f"E_shallow_{i}", src_shallow,
            f"Ambiguous evidence item {i}",
            supports_hypotheses=("H_correct", "H_rival"),
            information_value=0.1,
        ))

    evidence.extend([
        LatentEvidence("E_deep_1", src_deep,
                       "Deep evidence specifically supporting H_correct",
                       supports_hypotheses=("H_correct",),
                       contradicts_hypotheses=("H_rival",),
                       information_value=0.85),
        LatentEvidence("E_deep_2", src_confirming,
                       "Confirming evidence for H_correct",
                       supports_hypotheses=("H_correct",),
                       information_value=0.75),
    ])

    return LatentWorld(
        world_id=f"regime_b_{seed}_{index}",
        hypotheses={"H_correct": h_correct, "H_rival": h_rival},
        evidence_pool=evidence,
        source_registry={"shallow_src": src_shallow, "deep_src": src_deep,
                         "confirming_src": src_confirming},
        true_hypothesis_id="H_correct",
        correct_conclusion="H_correct",
    )


def generate_regime_c_discrimination_deficit(
    *, index: int = 0, seed: int = 100,
) -> LatentWorld:
    """
    Regime C — Discrimination Deficit.
    
    Multiple plausible hypotheses exist with sufficient general evidence.
    What's missing is falsification of the wrong hypothesis.
    Attack should become high-value here.
    
    Optimal: attack -> reason (falsify then integrate)
    Suboptimal: more retrieval or hypothesis generation (already saturated)
    """
    sub = _sub_seed("regime_c", index, seed)

    h_true = Hypothesis("H_true", "Actually correct hypothesis",
                        is_true=True, initial_plausibility=0.40)
    h_plausible = Hypothesis("H_plausible", "Plausible but wrong",
                             is_true=False, initial_plausibility=0.55)
    h_weak = Hypothesis("H_weak", "Weakly supported alternative",
                        is_true=False, initial_plausibility=0.20)

    sources = [EvidenceSource(f"src_{i}", reliability=0.75) for i in range(5)]

    evidence = [
        LatentEvidence("E_support_true", sources[0],
                       "Evidence supporting H_true",
                       supports_hypotheses=("H_true",),
                       information_value=0.5),
        LatentEvidence("E_support_plausible", sources[1],
                       "Evidence also supporting H_plausible",
                       supports_hypotheses=("H_plausible",),
                       information_value=0.4),
        LatentEvidence("E_general_1", sources[2],
                       "General data consistent with both",
                       supports_hypotheses=("H_true", "H_plausible"),
                       information_value=0.15),
        LatentEvidence("E_general_2", sources[3],
                       "More general data",
                       supports_hypotheses=("H_true", "H_plausible"),
                       information_value=0.1),
        LatentEvidence("E_falsifying", sources[4],
                       "Evidence that contradicts H_plausible specifically",
                       supports_hypotheses=("H_true",),
                       contradicts_hypotheses=("H_plausible",),
                       information_value=0.9),
    ]

    hidden = {
        "methodological_flaw": HiddenVariable(
            "methodological_flaw",
            "Methodological issue undermining H_plausible's support",
            impact_on_conclusion=0.8,
            discoverable_via="attack_hypothesis",
        ),
    }

    return LatentWorld(
        world_id=f"regime_c_{seed}_{index}",
        hypotheses={"H_true": h_true, "H_plausible": h_plausible,
                    "H_weak": h_weak},
        evidence_pool=evidence,
        hidden_variables=hidden,
        source_registry={s.source_id: s for s in sources},
        true_hypothesis_id="H_true",
        correct_conclusion="H_true after falsifying H_plausible",
    )


def generate_regime_d_integration_deficit(
    *, index: int = 0, seed: int = 100,
) -> LatentWorld:
    """
    Regime D — Integration Deficit.
    
    Abundant evidence and correct hypotheses exist. Additional exploration
    is wasteful. What's needed is reasoning to integrate.
    
    Optimal: reason (consolidate immediately)
    Suboptimal: more retrieval or hypothesis generation (redundant)
    """
    sub = _sub_seed("regime_d", index, seed)

    h_correct = Hypothesis("H_correct", "Correct well-supported hypothesis",
                           is_true=True, initial_plausibility=0.60)
    h_wrong = Hypothesis("H_wrong", "Weakly supported wrong hypothesis",
                         is_true=False, initial_plausibility=0.30)

    sources = [EvidenceSource(f"src_{i}", reliability=0.85) for i in range(6)]

    evidence = [
        LatentEvidence(f"E_strong_{i}", sources[i],
                       f"Strong evidence {i} supporting H_correct",
                       supports_hypotheses=("H_correct",),
                       contradicts_hypotheses=("H_wrong",),
                       information_value=0.7)
        for i in range(4)
    ]
    evidence.extend([
        LatentEvidence("E_weak_1", sources[4],
                       "Weak evidence for H_wrong",
                       supports_hypotheses=("H_wrong",),
                       information_value=0.1),
        LatentEvidence("E_noise", sources[5],
                       "Background noise",
                       information_value=0.02),
    ])

    return LatentWorld(
        world_id=f"regime_d_{seed}_{index}",
        hypotheses={"H_correct": h_correct, "H_wrong": h_wrong},
        evidence_pool=evidence,
        source_registry={s.source_id: s for s in sources},
        true_hypothesis_id="H_correct",
        correct_conclusion="H_correct",
    )


def generate_regime_e_misleading_evidence(
    *, index: int = 0, seed: int = 100,
) -> LatentWorld:
    """
    Regime E — Misleading Evidence.
    
    Large volume of evidence supports the wrong hypothesis.
    One piece of decisive falsifying evidence exists.
    
    Optimal: attack -> retrieve -> reason (find the falsifier)
    Suboptimal: naive evidence aggregation (gets misled)
    """
    sub = _sub_seed("regime_e", index, seed)
    n_misleading = 4 + (sub % 3)

    h_wrong = Hypothesis("H_popular", "Popular but wrong hypothesis",
                         is_true=False, initial_plausibility=0.70)
    h_correct = Hypothesis("H_minority", "Unpopular but correct",
                           is_true=True, initial_plausibility=0.25)

    misleading_src = EvidenceSource("misleading_src", reliability=0.60)
    decisive_src = EvidenceSource("decisive_src", reliability=0.95)

    evidence = []
    for i in range(n_misleading):
        evidence.append(LatentEvidence(
            f"E_misleading_{i}", misleading_src,
            f"Misleading evidence {i} for H_popular",
            supports_hypotheses=("H_popular",),
            information_value=0.15,
        ))

    evidence.append(LatentEvidence(
        "E_decisive_falsifier", decisive_src,
        "Decisive evidence falsifying H_popular and supporting H_minority",
        supports_hypotheses=("H_minority",),
        contradicts_hypotheses=("H_popular",),
        information_value=0.95,
    ))

    hidden = {
        "systematic_bias": HiddenVariable(
            "systematic_bias",
            "Systematic bias in misleading evidence sources",
            impact_on_conclusion=0.9,
            discoverable_via="attack_hypothesis",
        ),
    }

    return LatentWorld(
        world_id=f"regime_e_{seed}_{index}",
        hypotheses={"H_popular": h_wrong, "H_minority": h_correct},
        evidence_pool=evidence,
        hidden_variables=hidden,
        source_registry={"misleading_src": misleading_src,
                         "decisive_src": decisive_src},
        true_hypothesis_id="H_minority",
        correct_conclusion="H_minority after discovering bias",
    )


def generate_regime_f_hidden_alternative(
    *, index: int = 0, seed: int = 100,
) -> LatentWorld:
    """
    Regime F — Hidden Alternative.
    
    Visible evidence makes H1 look sufficient, but an unconsidered H2
    explains anomalies better. Requires renewed hypothesis generation.
    
    Optimal: generate_hypothesis -> retrieve -> generate_hypothesis -> reason
    Suboptimal: committing to H1 too early
    """
    sub = _sub_seed("regime_f", index, seed)

    h_obvious = Hypothesis("H_sufficient", "Looks sufficient but incomplete",
                           is_true=False, initial_plausibility=0.65)
    h_better = Hypothesis("H_better", "Better explanation found later",
                          is_true=True, initial_plausibility=0.10)
    h_auxiliary = Hypothesis("H_auxiliary", "Auxiliary partial explanation",
                             is_true=False, initial_plausibility=0.20)

    sources = [EvidenceSource(f"src_{i}", reliability=0.80) for i in range(5)]

    evidence = [
        LatentEvidence("E_surface_1", sources[0],
                       "Surface-level evidence supporting H_sufficient",
                       supports_hypotheses=("H_sufficient",),
                       information_value=0.3),
        LatentEvidence("E_surface_2", sources[1],
                       "More surface evidence",
                       supports_hypotheses=("H_sufficient",),
                       information_value=0.25),
        LatentEvidence("E_anomaly_1", sources[2],
                       "Anomaly that H_sufficient cannot explain",
                       supports_hypotheses=("H_better",),
                       contradicts_hypotheses=("H_sufficient",),
                       information_value=0.7),
        LatentEvidence("E_anomaly_2", sources[3],
                       "Second anomaly pointing to H_better",
                       supports_hypotheses=("H_better",),
                       information_value=0.8),
        LatentEvidence("E_confirming", sources[4],
                       "Evidence confirming H_better's prediction",
                       supports_hypotheses=("H_better",),
                       contradicts_hypotheses=("H_sufficient",),
                       information_value=0.9),
    ]

    return LatentWorld(
        world_id=f"regime_f_{seed}_{index}",
        hypotheses={"H_sufficient": h_obvious, "H_better": h_better,
                    "H_auxiliary": h_auxiliary},
        evidence_pool=evidence,
        source_registry={s.source_id: s for s in sources},
        true_hypothesis_id="H_better",
        correct_conclusion="H_better",
    )


def generate_regime_g_source_dependency(
    *, index: int = 0, seed: int = 100,
) -> LatentWorld:
    """
    Regime G — Source Dependency.
    
    Many apparently independent evidence items share one origin.
    Evidence independence/provenance reasoning matters.
    
    Optimal: reason with provenance awareness
    Suboptimal: treating all evidence as independent
    """
    sub = _sub_seed("regime_g", index, seed)
    n_dependent = 4 + (sub % 3)

    h_inflated = Hypothesis("H_inflated", "Conclusion with inflated support",
                            is_true=False, initial_plausibility=0.60)
    h_actual = Hypothesis("H_actual", "True conclusion with genuine support",
                          is_true=True, initial_plausibility=0.35)

    origin = EvidenceSource("hidden_origin", reliability=0.55)
    independent = EvidenceSource("independent_primary", reliability=0.90)

    evidence = []
    for i in range(n_dependent):
        dep = EvidenceSource(f"apparent_independent_{i}", reliability=0.70,
                             parent_source="hidden_origin")
        evidence.append(LatentEvidence(
            f"E_dep_{i}", dep,
            f"Apparently independent evidence {i} for H_inflated",
            supports_hypotheses=("H_inflated",),
            information_value=0.1,
        ))

    evidence.extend([
        LatentEvidence("E_genuine", independent,
                       "Genuinely independent evidence for H_actual",
                       supports_hypotheses=("H_actual",),
                       contradicts_hypotheses=("H_inflated",),
                       information_value=0.85),
        LatentEvidence("E_confirming", EvidenceSource("confirming_src", reliability=0.88),
                       "Confirming independent evidence for H_actual",
                       supports_hypotheses=("H_actual",),
                       information_value=0.75),
    ])

    return LatentWorld(
        world_id=f"regime_g_{seed}_{index}",
        hypotheses={"H_inflated": h_inflated, "H_actual": h_actual},
        evidence_pool=evidence,
        source_registry={
            "hidden_origin": origin, "independent_primary": independent,
            "confirming_src": EvidenceSource("confirming_src", 0.88),
            **{f"apparent_independent_{i}":
               EvidenceSource(f"apparent_independent_{i}", 0.70, "hidden_origin")
               for i in range(n_dependent)},
        },
        true_hypothesis_id="H_actual",
        correct_conclusion="H_actual",
    )


def generate_regime_h_low_resolvability(
    *, index: int = 0, seed: int = 100,
) -> LatentWorld:
    """
    Regime H — High Ignorance / Low Resolvability.
    
    Unknowns exist but further investigation has low expected value.
    The correct strategy is partial conclusion with appropriate uncertainty.
    
    Optimal: reason -> stop (conclude with partial info)
    Suboptimal: excessive exploration (wastes compute without value)
    """
    sub = _sub_seed("regime_h", index, seed)

    h_likely = Hypothesis("H_likely", "Most likely conclusion given limited info",
                          is_true=True, initial_plausibility=0.55)
    h_alternative = Hypothesis("H_alternative", "Possible but less likely",
                               is_true=False, initial_plausibility=0.40)

    weak_src = EvidenceSource("weak_source", reliability=0.50)

    evidence = [
        LatentEvidence("E_partial_1", weak_src,
                       "Weak partial evidence for H_likely",
                       supports_hypotheses=("H_likely",),
                       information_value=0.25),
        LatentEvidence("E_partial_2", EvidenceSource("weak_2", reliability=0.45),
                       "Another weak observation",
                       supports_hypotheses=("H_likely",),
                       information_value=0.15),
        LatentEvidence("E_noise_1", EvidenceSource("noise_src", reliability=0.30),
                       "Noisy irrelevant data",
                       information_value=0.02),
        LatentEvidence("E_noise_2", EvidenceSource("noise_src_2", reliability=0.25),
                       "More noise",
                       information_value=0.01),
    ]

    hidden = {
        "unresolvable_uncertainty": HiddenVariable(
            "unresolvable_uncertainty",
            "Fundamental uncertainty that cannot be resolved with available evidence",
            impact_on_conclusion=0.3,
            discoverable_via="attack_hypothesis",
        ),
    }

    return LatentWorld(
        world_id=f"regime_h_{seed}_{index}",
        hypotheses={"H_likely": h_likely, "H_alternative": h_alternative},
        evidence_pool=evidence,
        hidden_variables=hidden,
        source_registry={
            "weak_source": weak_src,
            "weak_2": EvidenceSource("weak_2", 0.45),
            "noise_src": EvidenceSource("noise_src", 0.30),
            "noise_src_2": EvidenceSource("noise_src_2", 0.25),
        },
        true_hypothesis_id="H_likely",
        correct_conclusion="H_likely with acknowledged uncertainty",
    )


V4_REGIME_GENERATORS = {
    "regime_a_exploration_deficit": generate_regime_a_exploration_deficit,
    "regime_b_evidence_deficit": generate_regime_b_evidence_deficit,
    "regime_c_discrimination_deficit": generate_regime_c_discrimination_deficit,
    "regime_d_integration_deficit": generate_regime_d_integration_deficit,
    "regime_e_misleading_evidence": generate_regime_e_misleading_evidence,
    "regime_f_hidden_alternative": generate_regime_f_hidden_alternative,
    "regime_g_source_dependency": generate_regime_g_source_dependency,
    "regime_h_low_resolvability": generate_regime_h_low_resolvability,
}
