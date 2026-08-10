"""
Semantic scenario generators for Campaign V2.

Each generator creates a LatentWorld with information structure where
different cognitive strategies produce measurably different outcomes.
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


def generate_hypothesis_ecology_world(
    *, index: int = 0, seed: int = 100, split: str = "dev",
) -> LatentWorld:
    """
    H1 looks strong initially, but H2 is actually correct.
    Early evidence supports H1. Later evidence (via attack/retrieve) reveals H2.
    An agent that preserves H2 and retrieves anomaly evidence will succeed.
    """
    sub = _sub_seed("hyp_ecology", index, seed)

    h1 = Hypothesis("H1", "Dominant initial hypothesis (actually false)",
                     is_true=False, initial_plausibility=0.7)
    h2 = Hypothesis("H2", "Minority hypothesis (actually true)",
                     is_true=True, initial_plausibility=0.3)
    h3 = Hypothesis("H3", "Distractor hypothesis",
                     is_true=False, initial_plausibility=0.2)

    src_a = EvidenceSource("src_A", reliability=0.8)
    src_b = EvidenceSource("src_B", reliability=0.85)
    src_c = EvidenceSource("src_C", reliability=0.9)
    src_d = EvidenceSource("src_D", reliability=0.75)

    evidence = [
        LatentEvidence("E1", src_a, "Observation consistent with H1",
                       supports_hypotheses=("H1",), information_value=0.3),
        LatentEvidence("E2", src_b, "Further data supporting H1",
                       supports_hypotheses=("H1",), information_value=0.3),
        LatentEvidence("E3", src_c, "Anomalous result inconsistent with H1, supports H2",
                       supports_hypotheses=("H2",), contradicts_hypotheses=("H1",),
                       information_value=0.8),
        LatentEvidence("E4", src_d, "Decisive evidence confirming H2",
                       supports_hypotheses=("H2",), contradicts_hypotheses=("H1",),
                       information_value=0.9),
    ]

    hidden = {
        "confound_1": HiddenVariable(
            "confound_1", "Confounding factor explaining early H1 evidence",
            impact_on_conclusion=0.7, discoverable_via="attack_hypothesis",
        ),
    }

    return LatentWorld(
        world_id=f"hyp_ecology_{seed}_{index}",
        hypotheses={"H1": h1, "H2": h2, "H3": h3},
        causal_graph=[
            CausalEdge("confound_1", "E1_pattern", 0.8, is_true=True),
        ],
        evidence_pool=evidence,
        hidden_variables=hidden,
        source_registry={s.source_id: s for s in [src_a, src_b, src_c, src_d]},
        true_hypothesis_id="H2",
        correct_conclusion="H2 is correct",
    )


def generate_false_majority_world(
    *, index: int = 0, seed: int = 100, split: str = "dev",
) -> LatentWorld:
    """
    Multiple dependent sources support wrong conclusion.
    One independent source has strong contradictory evidence.
    """
    sub = _sub_seed("false_majority", index, seed)
    n_majority = 3 + (sub % 3)

    h_wrong = Hypothesis("H_wrong", "Majority-supported but incorrect",
                         is_true=False, initial_plausibility=0.6)
    h_correct = Hypothesis("H_correct", "Minority-supported but correct",
                           is_true=True, initial_plausibility=0.4)

    origin = EvidenceSource("origin", reliability=0.6)
    independent = EvidenceSource("independent_src", reliability=0.9)

    evidence = []
    for i in range(n_majority):
        dep_src = EvidenceSource(
            f"derived_{i}", reliability=0.65,
            parent_source="origin",
        )
        evidence.append(LatentEvidence(
            f"E_majority_{i}", dep_src,
            f"Evidence {i} supporting wrong conclusion",
            supports_hypotheses=("H_wrong",),
            information_value=0.2,
        ))

    evidence.append(LatentEvidence(
        "E_independent", independent,
        "Strong independent evidence for correct conclusion",
        supports_hypotheses=("H_correct",),
        contradicts_hypotheses=("H_wrong",),
        information_value=0.85,
    ))

    return LatentWorld(
        world_id=f"false_majority_{seed}_{index}",
        hypotheses={"H_wrong": h_wrong, "H_correct": h_correct},
        evidence_pool=evidence,
        source_registry={
            "origin": origin, "independent_src": independent,
            **{f"derived_{i}": EvidenceSource(f"derived_{i}", 0.65, "origin")
               for i in range(n_majority)},
        },
        true_hypothesis_id="H_correct",
        correct_conclusion="H_correct",
    )


def generate_ignorance_discovery_world(
    *, index: int = 0, seed: int = 100, split: str = "dev",
) -> LatentWorld:
    """
    Scenario with hidden confounding variables.
    Agent should discover what's missing before concluding.
    """
    sub = _sub_seed("ignorance", index, seed)
    hidden_vars = ["confounding_factor", "selection_bias", "measurement_error"]
    hidden_name = hidden_vars[sub % len(hidden_vars)]

    h_naive = Hypothesis("H_naive", "X causes Y (naive causal claim)",
                         is_true=False, initial_plausibility=0.65)
    h_confounded = Hypothesis("H_confounded",
                              f"Relationship confounded by {hidden_name}",
                              is_true=True, initial_plausibility=0.3)

    src = EvidenceSource("study_src", reliability=0.8)
    hint_src = EvidenceSource("hint_src", reliability=0.6)

    evidence = [
        LatentEvidence("E_correlation", src,
                       "X correlates with Y (r=0.6, p<0.001)",
                       supports_hypotheses=("H_naive",),
                       information_value=0.4),
        LatentEvidence("E_hint", hint_src,
                       f"Some researchers have noted possible {hidden_name}",
                       supports_hypotheses=("H_confounded",),
                       information_value=0.6),
        LatentEvidence("E_control", EvidenceSource("control_src", reliability=0.85),
                       f"Controlled study accounting for {hidden_name} shows no X→Y effect",
                       supports_hypotheses=("H_confounded",),
                       contradicts_hypotheses=("H_naive",),
                       information_value=0.9),
    ]

    hidden = {
        hidden_name: HiddenVariable(
            hidden_name, f"Critical hidden variable: {hidden_name}",
            impact_on_conclusion=0.9, discoverable_via="attack_hypothesis",
        ),
    }

    return LatentWorld(
        world_id=f"ignorance_{seed}_{index}",
        hypotheses={"H_naive": h_naive, "H_confounded": h_confounded},
        evidence_pool=evidence,
        hidden_variables=hidden,
        source_registry={"study_src": src, "hint_src": hint_src,
                         "control_src": EvidenceSource("control_src", 0.85)},
        true_hypothesis_id="H_confounded",
        correct_conclusion=f"Confounded by {hidden_name}",
    )


def generate_stopping_quality_world(
    *, index: int = 0, seed: int = 100, split: str = "dev",
) -> LatentWorld:
    """
    Scenario where early stopping is correct: first evidence is decisive.
    Additional cognition adds noise without value.
    """
    sub = _sub_seed("stopping", index, seed)

    h_correct = Hypothesis("H_A", "Clear correct conclusion",
                           is_true=True, initial_plausibility=0.5)
    h_wrong = Hypothesis("H_B", "Plausible but wrong alternative",
                         is_true=False, initial_plausibility=0.5)

    evidence = [
        LatentEvidence("E_decisive", EvidenceSource("strong_src", reliability=0.95),
                       "Decisive evidence for H_A",
                       supports_hypotheses=("H_A",),
                       contradicts_hypotheses=("H_B",),
                       information_value=0.95),
        LatentEvidence("E_noise1", EvidenceSource("noise_1", reliability=0.4),
                       "Weak noisy evidence suggesting H_B",
                       supports_hypotheses=("H_B",),
                       information_value=0.1),
        LatentEvidence("E_noise2", EvidenceSource("noise_2", reliability=0.35),
                       "More noise",
                       supports_hypotheses=("H_B",),
                       information_value=0.05),
    ]

    return LatentWorld(
        world_id=f"stopping_{seed}_{index}",
        hypotheses={"H_A": h_correct, "H_B": h_wrong},
        evidence_pool=evidence,
        source_registry={"strong_src": EvidenceSource("strong_src", 0.95),
                         "noise_1": EvidenceSource("noise_1", 0.4),
                         "noise_2": EvidenceSource("noise_2", 0.35)},
        true_hypothesis_id="H_A",
        correct_conclusion="H_A",
    )


def generate_source_duplication_world(
    *, index: int = 0, seed: int = 100, split: str = "dev",
) -> LatentWorld:
    """
    Multiple apparent sources derive from one origin.
    One genuinely independent contradictory source exists.
    """
    sub = _sub_seed("duplication", index, seed)
    n_duplicates = 3 + (sub % 4)

    h_inflated = Hypothesis("H_X", "Conclusion X (inflated by duplication)",
                            is_true=False, initial_plausibility=0.5)
    h_correct = Hypothesis("H_Y", "Conclusion Y (independent evidence)",
                           is_true=True, initial_plausibility=0.5)

    origin = EvidenceSource("original_study", reliability=0.7)
    independent = EvidenceSource("independent_study", reliability=0.88)

    evidence = [
        LatentEvidence("E_original", origin,
                       "Original study supports X",
                       supports_hypotheses=("H_X",),
                       information_value=0.4),
    ]
    for i in range(n_duplicates):
        dep = EvidenceSource(f"derivative_{i}", reliability=0.65,
                             parent_source="original_study")
        evidence.append(LatentEvidence(
            f"E_dup_{i}", dep,
            f"Article {i} citing original, confirms X",
            supports_hypotheses=("H_X",),
            information_value=0.1,
        ))

    evidence.append(LatentEvidence(
        "E_independent_Y", independent,
        "Independent primary study supports Y",
        supports_hypotheses=("H_Y",),
        contradicts_hypotheses=("H_X",),
        information_value=0.8,
    ))

    return LatentWorld(
        world_id=f"duplication_{seed}_{index}",
        hypotheses={"H_X": h_inflated, "H_Y": h_correct},
        evidence_pool=evidence,
        source_registry={
            "original_study": origin, "independent_study": independent,
            **{f"derivative_{i}": EvidenceSource(f"derivative_{i}", 0.65, "original_study")
               for i in range(n_duplicates)},
        },
        true_hypothesis_id="H_Y",
        correct_conclusion="Y",
    )


SEMANTIC_FAMILY_GENERATORS = {
    "hypothesis_ecology": generate_hypothesis_ecology_world,
    "false_majority": generate_false_majority_world,
    "ignorance_discovery": generate_ignorance_discovery_world,
    "stopping_quality": generate_stopping_quality_world,
    "source_duplication": generate_source_duplication_world,
}


def generate_all_semantic_worlds(
    *,
    count_per_family: int = 10,
    base_seed: int = 100,
    dev_fraction: float = 0.5,
    validation_fraction: float = 0.25,
) -> list[tuple[LatentWorld, str]]:
    """Generate worlds with dev/validation/locked_test splits."""
    worlds: list[tuple[LatentWorld, str]] = []
    for family_name, gen_fn in SEMANTIC_FAMILY_GENERATORS.items():
        for i in range(count_per_family):
            if i < int(count_per_family * dev_fraction):
                split = "dev"
            elif i < int(count_per_family * (dev_fraction + validation_fraction)):
                split = "validation"
            else:
                split = "locked_test"

            world = gen_fn(index=i, seed=base_seed + i, split=split)
            worlds.append((world, split))
    return worlds
