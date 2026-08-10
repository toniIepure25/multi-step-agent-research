"""
EpistemicWorldSimulator — deterministic but semantically meaningful environment.

Contains a hidden structured world state. Research agents interact through
cognitive operations whose results depend on the latent world + current
epistemic state + selected action.

The agent never sees the latent world directly.
Oracle quantities are evaluation-only.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Hypothesis:
    """A hypothesis in the latent world."""
    hypothesis_id: str
    statement: str
    is_true: bool
    initial_plausibility: float
    domain: str = "general"


@dataclass(frozen=True)
class CausalEdge:
    """A causal relationship in the latent world."""
    cause: str
    effect: str
    strength: float
    is_true: bool = True


@dataclass(frozen=True)
class EvidenceSource:
    """A source of evidence with known reliability."""
    source_id: str
    reliability: float
    parent_source: str | None = None
    domain_expertise: str = "general"


@dataclass(frozen=True)
class LatentEvidence:
    """Evidence available in the world, accessible via retrieve."""
    evidence_id: str
    source: EvidenceSource
    content: str
    supports_hypotheses: tuple[str, ...] = ()
    contradicts_hypotheses: tuple[str, ...] = ()
    information_value: float = 0.5
    is_accessible: bool = True


@dataclass(frozen=True)
class HiddenVariable:
    """A variable the agent should ideally discover."""
    variable_id: str
    description: str
    impact_on_conclusion: float
    discoverable_via: str = "attack_hypothesis"


@dataclass
class LatentWorld:
    """The complete hidden world state for a scenario."""

    world_id: str
    hypotheses: dict[str, Hypothesis] = field(default_factory=dict)
    causal_graph: list[CausalEdge] = field(default_factory=list)
    evidence_pool: list[LatentEvidence] = field(default_factory=list)
    hidden_variables: dict[str, HiddenVariable] = field(default_factory=dict)
    source_registry: dict[str, EvidenceSource] = field(default_factory=dict)
    true_hypothesis_id: str = ""
    correct_conclusion: str = ""
    auxiliary_assumptions: dict[str, bool] = field(default_factory=dict)

    def true_hypothesis(self) -> Hypothesis | None:
        return self.hypotheses.get(self.true_hypothesis_id)


@dataclass
class EpistemicQualityVector:
    """Multi-dimensional quality evaluation against latent world."""

    correct_final_hypothesis: float = 0.0
    posterior_mass_on_true: float = 0.0
    hypothesis_ranking_quality: float = 0.0
    causal_edge_precision: float = 0.0
    causal_edge_recall: float = 0.0
    hidden_variable_discovery: float = 0.0
    critical_assumption_identification: float = 0.0
    evidence_provenance_quality: float = 0.0
    calibration: float = 0.0
    appropriate_abstention: float = 0.0

    def scalar_quality(self, weights: dict[str, float] | None = None) -> float:
        """Aggregate into a single scalar. Default equal weights."""
        w = weights or {}
        components = {
            "correct_final_hypothesis": 0.25,
            "posterior_mass_on_true": 0.15,
            "hypothesis_ranking_quality": 0.15,
            "hidden_variable_discovery": 0.15,
            "critical_assumption_identification": 0.10,
            "calibration": 0.10,
            "evidence_provenance_quality": 0.05,
            "appropriate_abstention": 0.05,
        }
        total = 0.0
        for name, default_w in components.items():
            val = getattr(self, name, 0.0)
            total += val * w.get(name, default_w)
        return total

    def to_dict(self) -> dict[str, float]:
        return {
            "correct_final_hypothesis": self.correct_final_hypothesis,
            "posterior_mass_on_true": self.posterior_mass_on_true,
            "hypothesis_ranking_quality": self.hypothesis_ranking_quality,
            "causal_edge_precision": self.causal_edge_precision,
            "causal_edge_recall": self.causal_edge_recall,
            "hidden_variable_discovery": self.hidden_variable_discovery,
            "critical_assumption_identification": self.critical_assumption_identification,
            "evidence_provenance_quality": self.evidence_provenance_quality,
            "calibration": self.calibration,
            "appropriate_abstention": self.appropriate_abstention,
        }


class EpistemicWorldSimulator:
    """
    Provides cognitive operation results that depend on the latent world.

    Each operation consults the hidden world state to produce semantically
    meaningful results. The agent never sees the latent world directly.
    """

    def __init__(self, world: LatentWorld, *, seed: int = 42) -> None:
        self._world = world
        self._seed = seed
        self._retrieved: set[str] = set()
        self._attacked_hypotheses: set[str] = set()
        self._discovered_hidden: set[str] = set()
        self._generated_hypotheses: set[str] = set()

    @property
    def world(self) -> LatentWorld:
        return self._world

    def _deterministic_choice(self, options: list[Any], context: str) -> Any:
        """Deterministic selection based on seed + context."""
        h = hashlib.sha256(f"{self._seed}_{context}".encode()).hexdigest()
        idx = int(h[:8], 16) % len(options) if options else 0
        return options[idx] if options else None

    def retrieve(self, query_context: str = "") -> dict[str, Any] | None:
        """Retrieve evidence from the world. Result depends on what's available."""
        available = [
            e for e in self._world.evidence_pool
            if e.evidence_id not in self._retrieved and e.is_accessible
        ]
        if not available:
            return None

        ctx = f"retrieve_{len(self._retrieved)}_{query_context}"
        selected = self._deterministic_choice(available, ctx)
        if selected is None:
            return None

        self._retrieved.add(selected.evidence_id)

        noise = 1.0 if selected.source.reliability >= 0.8 else 0.7
        return {
            "evidence_id": selected.evidence_id,
            "content": selected.content,
            "source_id": selected.source.source_id,
            "source_reliability": selected.source.reliability,
            "parent_source": selected.source.parent_source,
            "confidence": min(1.0, selected.source.reliability * noise),
            "supports": list(selected.supports_hypotheses),
            "contradicts": list(selected.contradicts_hypotheses),
            "information_value": selected.information_value,
        }

    def generate_hypothesis(
        self,
        visible_evidence_ids: list[str],
    ) -> dict[str, Any] | None:
        """Generate a hypothesis consistent with visible evidence."""
        candidates = [
            h for hid, h in self._world.hypotheses.items()
            if hid not in self._generated_hypotheses
        ]
        if not candidates:
            return None

        evidence_hints = []
        for eid in visible_evidence_ids:
            for e in self._world.evidence_pool:
                if e.evidence_id == eid:
                    evidence_hints.extend(e.supports_hypotheses)
                    break

        prioritized = sorted(
            candidates,
            key=lambda h: (
                1.0 if h.hypothesis_id in evidence_hints else 0.0,
                h.initial_plausibility,
            ),
            reverse=True,
        )

        ctx = f"gen_hyp_{len(self._generated_hypotheses)}"
        selected = self._deterministic_choice(prioritized[:3], ctx)
        if selected is None:
            return None

        self._generated_hypotheses.add(selected.hypothesis_id)

        return {
            "hypothesis_id": selected.hypothesis_id,
            "statement": selected.statement,
            "initial_plausibility": selected.initial_plausibility,
            "generation_method": "abduction",
        }

    def attack_hypothesis(
        self,
        hypothesis_id: str,
    ) -> dict[str, Any]:
        """Attempt to find weaknesses in a hypothesis. May discover hidden variables."""
        hyp = self._world.hypotheses.get(hypothesis_id)
        if hyp is None:
            return {"outcome": "no_target", "ignorance_items": []}

        weaknesses = []
        ignorance_items = []

        if not hyp.is_true:
            contradicting = [
                e for e in self._world.evidence_pool
                if hypothesis_id in e.contradicts_hypotheses
                and e.evidence_id not in self._retrieved
            ]
            if contradicting:
                weaknesses.append(f"Contradictory evidence exists from {len(contradicting)} sources")

        for hv_id, hv in self._world.hidden_variables.items():
            if hv_id not in self._discovered_hidden:
                ctx = f"attack_{hypothesis_id}_{hv_id}"
                h = hashlib.sha256(f"{self._seed}_{ctx}".encode()).hexdigest()
                discover_prob = 0.3 + (0.4 if hv.discoverable_via == "attack_hypothesis" else 0.0)
                if int(h[:4], 16) / 0xFFFF < discover_prob:
                    self._discovered_hidden.add(hv_id)
                    ignorance_items.append({
                        "variable_id": hv_id,
                        "description": hv.description,
                        "priority": hv.impact_on_conclusion,
                        "ignorance_type": "untested_assumption",
                    })

        self._attacked_hypotheses.add(hypothesis_id)

        return {
            "hypothesis_id": hypothesis_id,
            "weaknesses": weaknesses,
            "ignorance_items": ignorance_items,
            "is_actually_true": hyp.is_true,
        }

    def reason(
        self,
        hypothesis_ids: list[str],
        evidence_ids: list[str],
    ) -> dict[str, Any]:
        """Derive implications from hypotheses and evidence."""
        visible_evidence = []
        for eid in evidence_ids:
            for e in self._world.evidence_pool:
                if e.evidence_id == eid:
                    visible_evidence.append(e)
                    break

        consistency_scores: dict[str, float] = {}
        for hid in hypothesis_ids:
            support_count = sum(
                1 for e in visible_evidence if hid in e.supports_hypotheses
            )
            contradict_count = sum(
                1 for e in visible_evidence if hid in e.contradicts_hypotheses
            )
            total = support_count + contradict_count
            if total > 0:
                consistency_scores[hid] = support_count / total
            else:
                hyp = self._world.hypotheses.get(hid)
                consistency_scores[hid] = hyp.initial_plausibility if hyp else 0.5

        return {
            "consistency_scores": consistency_scores,
            "evidence_analyzed": len(visible_evidence),
            "contradictions_found": sum(
                1 for e in visible_evidence
                if any(hid in e.contradicts_hypotheses for hid in hypothesis_ids)
            ),
        }

    def counterfactual(
        self,
        assumption_name: str,
        flip_to: bool,
    ) -> dict[str, Any]:
        """What happens if we flip an auxiliary assumption?"""
        if assumption_name not in self._world.auxiliary_assumptions:
            return {"valid": False, "reason": "assumption not found"}

        original = self._world.auxiliary_assumptions[assumption_name]
        changes_conclusion = False

        for edge in self._world.causal_graph:
            if edge.cause == assumption_name and edge.is_true != flip_to:
                if edge.strength > 0.5:
                    changes_conclusion = True

        return {
            "assumption": assumption_name,
            "original_value": original,
            "flipped_to": flip_to,
            "changes_conclusion": changes_conclusion,
            "is_decisive": changes_conclusion,
        }

    def evaluate(
        self,
        final_hypotheses: dict[str, float],
        identified_hidden_vars: set[str],
        identified_assumptions: set[str],
        evidence_sources_used: dict[str, str | None],
    ) -> EpistemicQualityVector:
        """Evaluate the agent's epistemic state against ground truth."""
        true_hid = self._world.true_hypothesis_id

        correct_final = 0.0
        posterior_on_true = 0.0
        ranking_quality = 0.0

        if final_hypotheses:
            best_hid = max(final_hypotheses, key=final_hypotheses.get)
            correct_final = 1.0 if best_hid == true_hid else 0.0
            posterior_on_true = final_hypotheses.get(true_hid, 0.0)

            sorted_hyps = sorted(final_hypotheses.items(), key=lambda x: -x[1])
            for rank, (hid, _) in enumerate(sorted_hyps):
                if hid == true_hid:
                    ranking_quality = 1.0 / (1 + rank)
                    break

        hv_discovery = 0.0
        if self._world.hidden_variables:
            hv_discovery = len(
                identified_hidden_vars & set(self._world.hidden_variables.keys())
            ) / len(self._world.hidden_variables)

        assumption_id = 0.0
        if self._world.auxiliary_assumptions:
            decisive = {
                k for k, v in self._world.auxiliary_assumptions.items()
                if any(
                    e.cause == k and e.strength > 0.5
                    for e in self._world.causal_graph
                )
            }
            if decisive:
                assumption_id = len(
                    identified_assumptions & decisive
                ) / len(decisive)

        provenance_quality = 0.0
        if evidence_sources_used:
            independent_sources = set()
            for src_id, parent in evidence_sources_used.items():
                if parent is None:
                    independent_sources.add(src_id)
                else:
                    root = parent
                    independent_sources.add(root)
            total_sources = len(evidence_sources_used)
            if total_sources > 0:
                provenance_quality = len(independent_sources) / total_sources

        calibration = 0.0
        if final_hypotheses:
            probs = list(final_hypotheses.values())
            max_conf = max(probs) if probs else 0.5
            if correct_final > 0.5:
                calibration = min(1.0, max_conf)
            else:
                calibration = max(0.0, 1.0 - max_conf)

        return EpistemicQualityVector(
            correct_final_hypothesis=correct_final,
            posterior_mass_on_true=posterior_on_true,
            hypothesis_ranking_quality=ranking_quality,
            hidden_variable_discovery=hv_discovery,
            critical_assumption_identification=assumption_id,
            evidence_provenance_quality=provenance_quality,
            calibration=calibration,
        )

    def oracle_action_value(
        self,
        action_type: str,
        current_evidence_ids: set[str],
        current_hypothesis_ids: set[str],
    ) -> float:
        """Oracle: true information value of an action (evaluation only)."""
        if action_type == "retrieve":
            available = [
                e for e in self._world.evidence_pool
                if e.evidence_id not in current_evidence_ids and e.is_accessible
            ]
            if not available:
                return 0.0
            return max(e.information_value for e in available)

        if action_type == "generate_hypothesis":
            undiscovered = [
                h for hid, h in self._world.hypotheses.items()
                if hid not in current_hypothesis_ids
            ]
            if not undiscovered:
                return 0.0
            true_undiscovered = [h for h in undiscovered if h.is_true]
            if true_undiscovered:
                return 0.9
            return 0.3

        if action_type == "attack_hypothesis":
            false_in_current = [
                hid for hid in current_hypothesis_ids
                if hid in self._world.hypotheses
                and not self._world.hypotheses[hid].is_true
            ]
            if false_in_current:
                return 0.7
            undiscovered_hv = [
                hv for hv_id, hv in self._world.hidden_variables.items()
                if hv_id not in self._discovered_hidden
            ]
            if undiscovered_hv:
                return 0.5
            return 0.1

        if action_type == "reason":
            if len(current_evidence_ids) >= 2 and len(current_hypothesis_ids) >= 2:
                return 0.5
            return 0.2

        if action_type == "stop":
            true_hid = self._world.true_hypothesis_id
            if true_hid in current_hypothesis_ids:
                return 0.6
            return 0.1

        return 0.0
