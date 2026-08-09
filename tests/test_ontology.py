"""
Tests for ontology forge, counterfactual laboratory, and experiment designer.
"""

from __future__ import annotations

import pytest

from asar.ontology.forge import OntologyForge
from asar.ontology.counterfactual import CounterfactualLab
from asar.ontology.experiment_designer import ExperimentDesigner
from schemas.ree.ontology import (
    ConclusionInvariance,
    CounterfactualWorld,
    OntologyFrame,
    SensitivityResult,
)


class TestOntologyForge:
    def test_default_frame_exists(self) -> None:
        forge = OntologyForge()
        assert forge.get_frame("default") is not None

    def test_add_frame(self) -> None:
        forge = OntologyForge()
        forge.add_frame(OntologyFrame(
            frame_id="causal",
            name="Causal-Mechanistic",
            key_variables=["X", "Y"],
        ))
        assert forge.get_frame("causal") is not None
        assert len(forge.active_frames()) == 2

    def test_create_revision_tracks_lineage(self) -> None:
        forge = OntologyForge()
        revised = forge.create_revision(
            parent_frame_id="default",
            name="Statistical",
            description="Statistical reframing",
            key_variables=["correlation", "p-value"],
        )
        assert revised.parent_frame_id == "default"
        lineage = forge.lineage(revised.frame_id)
        assert lineage == [revised.frame_id, "default"]

    def test_deactivate_preserves_frame(self) -> None:
        forge = OntologyForge()
        forge.add_frame(OntologyFrame(frame_id="f1", name="Test"))
        forge.deactivate("f1")
        assert forge.get_frame("f1") is not None
        assert not forge.get_frame("f1").active
        assert "f1" not in [f.frame_id for f in forge.active_frames()]

    def test_classify_invariant_conclusion(self) -> None:
        forge = OntologyForge()
        result = forge.classify_conclusion_invariance({
            "frame_a": "conclusion X",
            "frame_b": "conclusion X",
        })
        assert result == ConclusionInvariance.INVARIANT

    def test_classify_ontology_dependent_conclusion(self) -> None:
        forge = OntologyForge()
        result = forge.classify_conclusion_invariance({
            "frame_a": "conclusion X",
            "frame_b": "conclusion Y",
            "frame_c": "conclusion X",
        })
        assert result == ConclusionInvariance.ONTOLOGY_DEPENDENT

    def test_classify_underdetermined_conclusion(self) -> None:
        forge = OntologyForge()
        result = forge.classify_conclusion_invariance({
            "frame_a": "conclusion X",
            "frame_b": "conclusion Y",
            "frame_c": "conclusion Z",
        })
        assert result == ConclusionInvariance.UNDERDETERMINED


class TestCounterfactualLab:
    def test_create_world(self) -> None:
        lab = CounterfactualLab()
        world = lab.create_world(
            perturbation_type="assumption_change",
            description="What if assumption A is false?",
        )
        assert world.world_id.startswith("world_")
        assert lab.get_world(world.world_id) is not None

    def test_record_conclusion(self) -> None:
        lab = CounterfactualLab()
        world = lab.create_world(perturbation_type="evidence_removal")
        updated = lab.record_conclusion(world.world_id, "Different answer", True)
        assert updated.conclusion == "Different answer"
        assert updated.conclusion_changed is True

    def test_robustness_score_all_stable(self) -> None:
        lab = CounterfactualLab()
        lab.record_sensitivity(SensitivityResult(
            target_id="a1", target_type="assumption",
            perturbation="flip", conclusion_changed=False,
            is_causally_decisive=False,
        ))
        lab.record_sensitivity(SensitivityResult(
            target_id="a2", target_type="assumption",
            perturbation="flip", conclusion_changed=False,
            is_causally_decisive=False,
        ))
        assert lab.robustness_score() == pytest.approx(1.0)

    def test_robustness_score_one_unstable(self) -> None:
        lab = CounterfactualLab()
        lab.record_sensitivity(SensitivityResult(
            target_id="a1", target_type="assumption",
            perturbation="flip", conclusion_changed=True,
            is_causally_decisive=False,
        ))
        lab.record_sensitivity(SensitivityResult(
            target_id="a2", target_type="assumption",
            perturbation="flip", conclusion_changed=False,
            is_causally_decisive=False,
        ))
        assert lab.robustness_score() == pytest.approx(0.5)

    def test_responsiveness_score(self) -> None:
        lab = CounterfactualLab()
        lab.record_sensitivity(SensitivityResult(
            target_id="a1", target_type="assumption",
            perturbation="critical flip", conclusion_changed=True,
            is_causally_decisive=True,
        ))
        lab.record_sensitivity(SensitivityResult(
            target_id="a2", target_type="assumption",
            perturbation="critical flip", conclusion_changed=False,
            is_causally_decisive=True,
        ))
        assert lab.responsiveness_score() == pytest.approx(0.5)

    def test_causally_decisive_assumptions(self) -> None:
        lab = CounterfactualLab()
        lab.record_sensitivity(SensitivityResult(
            target_id="a1", target_type="assumption",
            perturbation="flip", conclusion_changed=True,
            is_causally_decisive=True,
        ))
        lab.record_sensitivity(SensitivityResult(
            target_id="a2", target_type="assumption",
            perturbation="flip", conclusion_changed=False,
            is_causally_decisive=False,
        ))
        decisive = lab.causally_decisive_assumptions()
        assert len(decisive) == 1
        assert decisive[0].target_id == "a1"

    def test_empty_lab_scores(self) -> None:
        lab = CounterfactualLab()
        assert lab.robustness_score() == 1.0
        assert lab.responsiveness_score() == 1.0


class TestExperimentDesigner:
    def test_propose_experiment(self) -> None:
        designer = ExperimentDesigner()
        candidate = designer.propose_experiment(
            description="Check source reliability",
            target_hypotheses=["h1", "h2"],
            expected_information_gain=0.8,
            discrimination_power=0.7,
        )
        assert candidate.experiment_id.startswith("experiment_")
        assert candidate.priority_score > 0

    def test_ranked_candidates(self) -> None:
        designer = ExperimentDesigner()
        designer.propose_experiment("Low info", ["h1"], expected_information_gain=0.2, discrimination_power=0.2)
        designer.propose_experiment("High info", ["h1"], expected_information_gain=0.9, discrimination_power=0.9)
        ranked = designer.ranked_candidates()
        assert ranked[0].description == "High info"

    def test_best_candidate(self) -> None:
        designer = ExperimentDesigner()
        designer.propose_experiment("A", ["h1"], expected_information_gain=0.5)
        designer.propose_experiment("B", ["h1"], expected_information_gain=0.9, discrimination_power=0.8)
        best = designer.best_candidate()
        assert best.description == "B"

    def test_empty_designer(self) -> None:
        designer = ExperimentDesigner()
        assert designer.best_candidate() is None
        assert designer.ranked_candidates() == []

    def test_high_cost_lowers_priority(self) -> None:
        designer = ExperimentDesigner()
        cheap = designer.propose_experiment("Cheap", ["h1"], expected_information_gain=0.5, estimated_cost=0.1, risk=0.1)
        expensive = designer.propose_experiment("Expensive", ["h1"], expected_information_gain=0.5, estimated_cost=0.9, risk=0.1)
        assert cheap.priority_score > expensive.priority_score
