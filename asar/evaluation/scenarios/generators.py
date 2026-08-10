"""
Deterministic scenario generators for each benchmark family.

All scenarios are generated from seeds for reproducibility.
Each generator creates ScenarioSpec instances with ground truth.
"""

from __future__ import annotations

import hashlib
from typing import Any

from asar.evaluation.scenario import ScenarioSpec


def _hash_seed(family: str, index: int, seed: int) -> int:
    """Deterministic sub-seed from family+index+seed."""
    h = hashlib.sha256(f"{family}_{index}_{seed}".encode()).hexdigest()
    return int(h[:8], 16)


# ---------------------------------------------------------------
# Family A: False Majority / Social Cascade
# ---------------------------------------------------------------

def generate_false_majority(
    *, family: str = "false_majority", index: int = 0,
    seed: int = 42, split: str = "dev",
) -> ScenarioSpec:
    """Scenario where majority sources support wrong conclusion."""
    sub = _hash_seed(family, index, seed)
    correct = "B" if sub % 2 == 0 else "A"
    wrong = "A" if correct == "B" else "B"

    n_majority = 3 + (sub % 3)
    evidence_pool = []
    for i in range(n_majority):
        evidence_pool.append({
            "source_id": f"majority_{i}",
            "claim": f"Evidence supports {wrong}",
            "confidence": 0.85,
            "source_type": "article",
            "parent_source": "common_origin_report" if i > 0 else None,
        })
    evidence_pool.append({
        "source_id": "minority_0",
        "claim": f"Strong independent evidence supports {correct}",
        "confidence": 0.92,
        "source_type": "primary_study",
        "parent_source": None,
    })

    return ScenarioSpec(
        scenario_id=f"{family}_{seed}_{index}",
        family=family,
        question=f"Based on the evidence, is the answer {wrong} or {correct}? [seed={seed}]",
        ground_truth=correct,
        ground_truth_metadata={
            "correct_answer": correct,
            "wrong_majority": wrong,
            "n_majority": n_majority,
            "independent_sources": 1,
        },
        domain="epistemology",
        difficulty="medium",
        tags=("social_cascade", "minority_preservation"),
        seed=seed,
        split=split,
        evidence_pool=tuple(evidence_pool),
        hidden_variables={"common_ancestry": True},
    )


# ---------------------------------------------------------------
# Family B: Duplicated Source Illusion
# ---------------------------------------------------------------

def generate_duplicated_source(
    *, family: str = "duplicated_source", index: int = 0,
    seed: int = 42, split: str = "dev",
) -> ScenarioSpec:
    """Scenario where apparent evidence volume is inflated by citation chains."""
    sub = _hash_seed(family, index, seed)
    n_duplicates = 3 + (sub % 4)

    evidence_pool = [
        {"source_id": "original_A", "claim": "Supports conclusion X",
         "confidence": 0.8, "source_type": "study", "parent_source": None},
    ]
    for i in range(n_duplicates):
        parent = "original_A" if i < 2 else evidence_pool[-(1 + (sub % 2))]["source_id"]
        evidence_pool.append({
            "source_id": f"derivative_{i}",
            "claim": "Confirms conclusion X",
            "confidence": 0.75 + (i % 3) * 0.05,
            "source_type": "article",
            "parent_source": parent,
        })
    evidence_pool.append({
        "source_id": "independent_contra",
        "claim": "Strong evidence for conclusion Y (contradicts X)",
        "confidence": 0.88,
        "source_type": "primary_study",
        "parent_source": None,
    })

    return ScenarioSpec(
        scenario_id=f"{family}_{seed}_{index}",
        family=family,
        question=f"Is conclusion X or Y correct? [seed={seed}]",
        ground_truth="Y",
        ground_truth_metadata={
            "correct": "Y",
            "n_apparent_sources_X": 1 + n_duplicates,
            "n_independent_sources_X": 1,
            "n_independent_sources_Y": 1,
        },
        domain="epistemology",
        difficulty="medium",
        tags=("source_duplication", "evidence_independence"),
        seed=seed,
        split=split,
        evidence_pool=tuple(evidence_pool),
        hidden_variables={"true_independent_count_X": 1},
    )


# ---------------------------------------------------------------
# Family D: Assumption Flips
# ---------------------------------------------------------------

def generate_assumption_flip(
    *, family: str = "assumption_flip", index: int = 0,
    seed: int = 42, split: str = "dev",
) -> ScenarioSpec:
    """Scenario where changing one assumption changes the correct conclusion."""
    sub = _hash_seed(family, index, seed)

    decisive_assumption = "linear_relationship" if sub % 2 == 0 else "independence"
    irrelevant_assumption = "sample_size_adequate" if sub % 2 == 0 else "measurement_precision"

    return ScenarioSpec(
        scenario_id=f"{family}_{seed}_{index}",
        family=family,
        question=f"Given the data and assumptions, what is the conclusion? [seed={seed}]",
        ground_truth="conclusion_changes_with_decisive_flip",
        ground_truth_metadata={
            "decisive_assumption": decisive_assumption,
            "irrelevant_assumption": irrelevant_assumption,
            "conclusion_under_original": "A",
            "conclusion_under_decisive_flip": "B",
            "conclusion_under_irrelevant_flip": "A",
        },
        domain="methodology",
        difficulty="hard",
        tags=("assumption_sensitivity", "counterfactual_robustness"),
        seed=seed,
        split=split,
        evidence_pool=(
            {"source_id": "data", "claim": "Data supports A under original assumptions",
             "confidence": 0.85, "source_type": "study", "parent_source": None},
            {"source_id": "assumption_note", "claim": f"Assumes {decisive_assumption}",
             "confidence": 1.0, "source_type": "methodology", "parent_source": None},
        ),
        hidden_variables={
            "decisive_assumption": decisive_assumption,
            "irrelevant_assumption": irrelevant_assumption,
        },
    )


# ---------------------------------------------------------------
# Family E: Hypothesis Ecology
# ---------------------------------------------------------------

def generate_hypothesis_ecology(
    *, family: str = "hypothesis_ecology", index: int = 0,
    seed: int = 42, split: str = "dev",
) -> ScenarioSpec:
    """Scenario where initial evidence favors H1 but later evidence favors H2."""
    sub = _hash_seed(family, index, seed)

    return ScenarioSpec(
        scenario_id=f"{family}_{seed}_{index}",
        family=family,
        question=f"What is the best explanation for the observed pattern? [seed={seed}]",
        ground_truth="H2",
        ground_truth_metadata={
            "initially_favored": "H1",
            "correct": "H2",
            "anomaly_at_step": 3,
        },
        domain="science",
        difficulty="hard",
        tags=("premature_convergence", "hypothesis_preservation", "belief_revision"),
        seed=seed,
        split=split,
        evidence_pool=(
            {"source_id": "early_1", "claim": "Observation consistent with H1",
             "confidence": 0.8, "source_type": "observation", "parent_source": None,
             "phase": "early"},
            {"source_id": "early_2", "claim": "Another observation favoring H1",
             "confidence": 0.75, "source_type": "observation", "parent_source": None,
             "phase": "early"},
            {"source_id": "anomaly", "claim": "Anomalous result inconsistent with H1, consistent with H2",
             "confidence": 0.9, "source_type": "experiment", "parent_source": None,
             "phase": "late"},
            {"source_id": "late_1", "claim": "Decisive evidence for H2",
             "confidence": 0.92, "source_type": "experiment", "parent_source": None,
             "phase": "late"},
        ),
        hidden_variables={"correct_hypothesis": "H2"},
    )


# ---------------------------------------------------------------
# Family I: Ignorance Discovery
# ---------------------------------------------------------------

def generate_ignorance_discovery(
    *, family: str = "ignorance_discovery", index: int = 0,
    seed: int = 42, split: str = "dev",
) -> ScenarioSpec:
    """Scenario with a hidden critical variable the system should identify."""
    sub = _hash_seed(family, index, seed)
    hidden_vars = ["confounding_factor", "selection_bias", "measurement_error",
                   "temporal_ordering", "missing_population"]
    hidden = hidden_vars[sub % len(hidden_vars)]

    return ScenarioSpec(
        scenario_id=f"{family}_{seed}_{index}",
        family=family,
        question=f"What is the relationship between X and Y? [seed={seed}]",
        ground_truth=f"The relationship is confounded by {hidden}",
        ground_truth_metadata={
            "hidden_variable": hidden,
            "apparent_conclusion": "X causes Y",
            "actual_conclusion": f"Relationship confounded by {hidden}",
        },
        domain="methodology",
        difficulty="hard",
        tags=("ignorance_foresight", "hidden_variable"),
        seed=seed,
        split=split,
        evidence_pool=(
            {"source_id": "correlational", "claim": "X correlates with Y (r=0.6)",
             "confidence": 0.85, "source_type": "study", "parent_source": None},
            {"source_id": "mechanism_hint", "claim": f"Some studies suggest {hidden} may be relevant",
             "confidence": 0.5, "source_type": "review", "parent_source": None},
        ),
        hidden_variables={"critical_hidden_variable": hidden},
    )


# ---------------------------------------------------------------
# Family J: Stopping Quality
# ---------------------------------------------------------------

def generate_stopping_quality(
    *, family: str = "stopping_quality", index: int = 0,
    seed: int = 42, split: str = "dev",
) -> ScenarioSpec:
    """Scenario where additional cognition is useful, useless, or harmful."""
    sub = _hash_seed(family, index, seed)
    conditions = ["useful", "useless", "harmful", "redundant"]
    condition = conditions[sub % len(conditions)]

    return ScenarioSpec(
        scenario_id=f"{family}_{seed}_{index}",
        family=family,
        question=f"What is the answer? Additional investigation is {condition}. [seed={seed}]",
        ground_truth=f"correct_answer_under_{condition}",
        ground_truth_metadata={
            "additional_cognition": condition,
            "optimal_stop_step": 2 if condition in ("useless", "redundant") else 5,
        },
        domain="general",
        difficulty="medium",
        tags=("stopping_quality", f"cognition_{condition}"),
        seed=seed,
        split=split,
        evidence_pool=(
            {"source_id": "base_evidence", "claim": "Base evidence for answer",
             "confidence": 0.8, "source_type": "study", "parent_source": None},
        ),
        hidden_variables={"cognition_utility": condition},
    )


# ---------------------------------------------------------------
# Master generator
# ---------------------------------------------------------------

FAMILY_GENERATORS = {
    "false_majority": generate_false_majority,
    "duplicated_source": generate_duplicated_source,
    "assumption_flip": generate_assumption_flip,
    "hypothesis_ecology": generate_hypothesis_ecology,
    "ignorance_discovery": generate_ignorance_discovery,
    "stopping_quality": generate_stopping_quality,
}


def generate_all_scenarios(
    *,
    count_per_family: int = 10,
    base_seed: int = 42,
    dev_fraction: float = 0.7,
) -> list[ScenarioSpec]:
    """Generate the complete scenario suite with dev/holdout split."""
    all_scenarios: list[ScenarioSpec] = []
    for family_name, gen_fn in FAMILY_GENERATORS.items():
        for i in range(count_per_family):
            split = "dev" if i < int(count_per_family * dev_fraction) else "holdout"
            spec = gen_fn(
                family=family_name,
                index=i,
                seed=base_seed + i,
                split=split,
            )
            all_scenarios.append(spec)
    return all_scenarios
