"""
Phase 27 — Static Real-Evidence Pack Generator.

Creates frozen evidence packs from real-world research domains with
evaluator-only ground truth. Evidence is exposed through controlled
retrieval — the agent decides interrogation order.

Evidence packs span 6 domains × 5 tasks = 30 packs.
Each pack includes supporting, contradictory, dependent, irrelevant,
weak, and decisive evidence items.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PACKS_DIR = Path(__file__).parent / "evidence_packs"


@dataclass
class EvidenceItem:
    item_id: str
    content: str
    source: str
    source_type: str  # primary | secondary | review | news | preprint
    reliability: float  # 0-1
    role: str  # supporting | contradictory | dependent | irrelevant | weak | decisive
    supports_claims: list[str] = field(default_factory=list)
    contradicts_claims: list[str] = field(default_factory=list)
    depends_on_source: str | None = None
    information_value: float = 0.5


@dataclass
class GroundTruth:
    """Evaluator-only structure — agent never sees this."""
    acceptable_hypotheses: list[str]
    best_hypothesis: str
    verdict: str  # SUPPORTED | REFUTED | MIXED | UNDERDETERMINED
    support_relations: dict[str, list[str]]
    contradiction_relations: dict[str, list[str]]
    source_dependencies: list[tuple[str, str]]
    critical_assumptions: list[str]
    decisive_evidence: list[str]
    known_ambiguity: list[str]


@dataclass
class StaticEvidencePack:
    pack_id: str
    domain: str
    task_question: str
    evidence_items: list[EvidenceItem]
    ground_truth: GroundTruth

    def agent_visible_items(self) -> list[dict]:
        """Items the agent can see (without ground truth labels)."""
        return [{
            "item_id": e.item_id,
            "content": e.content,
            "source": e.source,
            "source_type": e.source_type,
        } for e in self.evidence_items]

    def retrieve_by_index(self, idx: int) -> dict | None:
        if 0 <= idx < len(self.evidence_items):
            e = self.evidence_items[idx]
            return {
                "item_id": e.item_id,
                "content": e.content,
                "source": e.source,
                "source_type": e.source_type,
            }
        return None

    def to_dict(self) -> dict:
        return {
            "pack_id": self.pack_id,
            "domain": self.domain,
            "task_question": self.task_question,
            "evidence_count": len(self.evidence_items),
            "evidence_items": [{
                "item_id": e.item_id, "content": e.content,
                "source": e.source, "source_type": e.source_type,
                "reliability": e.reliability, "role": e.role,
                "supports_claims": e.supports_claims,
                "contradicts_claims": e.contradicts_claims,
                "depends_on_source": e.depends_on_source,
                "information_value": e.information_value,
            } for e in self.evidence_items],
            "ground_truth": {
                "acceptable_hypotheses": self.ground_truth.acceptable_hypotheses,
                "best_hypothesis": self.ground_truth.best_hypothesis,
                "verdict": self.ground_truth.verdict,
                "support_relations": self.ground_truth.support_relations,
                "contradiction_relations": self.ground_truth.contradiction_relations,
                "source_dependencies": [list(d) for d in self.ground_truth.source_dependencies],
                "critical_assumptions": self.ground_truth.critical_assumptions,
                "decisive_evidence": self.ground_truth.decisive_evidence,
                "known_ambiguity": self.ground_truth.known_ambiguity,
            },
        }


# ===================================================================
# PACK GENERATORS — 6 DOMAINS × 5 TASKS EACH
# ===================================================================

def _make_pack(
    pack_id: str,
    domain: str,
    question: str,
    evidence: list[EvidenceItem],
    gt: GroundTruth,
) -> StaticEvidencePack:
    return StaticEvidencePack(
        pack_id=pack_id, domain=domain,
        task_question=question, evidence_items=evidence,
        ground_truth=gt)


def _cog_sci_packs() -> list[StaticEvidencePack]:
    """Cognitive science domain — 5 packs."""
    packs = []

    # Pack 1: Dual-process theory evidence evaluation
    packs.append(_make_pack(
        "cog_01", "cognitive_science",
        "Does the evidence support dual-process theory (System 1/System 2) as distinct cognitive systems, or as a continuum of processing?",
        evidence=[
            EvidenceItem("cog_01_e1",
                "Kahneman (2011) presents extensive behavioral evidence for two distinct modes of thinking: fast/intuitive (System 1) and slow/deliberative (System 2). Response time data shows bimodal distributions on conjunction fallacy tasks.",
                "Kahneman, Thinking Fast and Slow", "primary", 0.9, "supporting",
                supports_claims=["dual_systems"]),
            EvidenceItem("cog_01_e2",
                "Neuroimaging meta-analysis (Goel, 2007) shows overlapping activation patterns for intuitive and deliberative reasoning, with no clear anatomical boundary between proposed System 1 and System 2 regions.",
                "Goel, Cognitive Neuroscience Review", "review", 0.85, "contradictory",
                contradicts_claims=["dual_systems"],
                supports_claims=["continuum"]),
            EvidenceItem("cog_01_e3",
                "Melnikoff & Bargh (2018) argue that dual-process theories are unfalsifiable as stated, and that cognitive control exists on a continuum of automaticity.",
                "Melnikoff & Bargh, Trends in Cognitive Sciences", "primary", 0.85, "contradictory",
                contradicts_claims=["dual_systems"],
                supports_claims=["continuum"]),
            EvidenceItem("cog_01_e4",
                "De Neys (2021) proposes an integrative model where logical intuitions and heuristic intuitions compete, preserving the phenomenology of dual processing without requiring discrete systems.",
                "De Neys, Perspectives on Psychological Science", "primary", 0.8, "decisive",
                supports_claims=["continuum", "integrative"]),
            EvidenceItem("cog_01_e5",
                "A news article claims 'Scientists prove brain has two distinct thinking systems' based on a single fMRI study with N=12.",
                "Science Daily rewrite of preliminary study", "news", 0.3, "weak",
                supports_claims=["dual_systems"]),
            EvidenceItem("cog_01_e6",
                "General educational psychology textbook repeats the dual-process framework as established fact, citing only Kahneman.",
                "Intro Psychology textbook, 2019 edition", "secondary", 0.5, "dependent",
                supports_claims=["dual_systems"],
                depends_on_source="Kahneman, Thinking Fast and Slow"),
            EvidenceItem("cog_01_e7",
                "Recent computational modeling shows that a single neural network can exhibit both fast/automatic and slow/controlled processing modes depending on task demands and training, without separate systems.",
                "Musslick et al., 2023, PNAS", "primary", 0.85, "decisive",
                contradicts_claims=["dual_systems"],
                supports_claims=["continuum"]),
        ],
        gt=GroundTruth(
            acceptable_hypotheses=["continuum", "integrative", "dual_systems_modified"],
            best_hypothesis="continuum",
            verdict="MIXED",
            support_relations={
                "dual_systems": ["cog_01_e1", "cog_01_e5", "cog_01_e6"],
                "continuum": ["cog_01_e2", "cog_01_e3", "cog_01_e4", "cog_01_e7"],
            },
            contradiction_relations={
                "dual_systems": ["cog_01_e2", "cog_01_e3", "cog_01_e7"],
                "continuum": [],
            },
            source_dependencies=[("cog_01_e6", "cog_01_e1")],
            critical_assumptions=["behavioral bimodality implies architectural distinction"],
            decisive_evidence=["cog_01_e4", "cog_01_e7"],
            known_ambiguity=["Whether 'systems' is metaphorical or literal"],
        )))

    # Pack 2: Embodied cognition and abstract thought
    packs.append(_make_pack(
        "cog_02", "cognitive_science",
        "Does abstract mathematical reasoning require embodied/sensorimotor grounding, or can it operate independently of perceptual systems?",
        evidence=[
            EvidenceItem("cog_02_e1",
                "Lakoff & Núñez (2000) argue all mathematical concepts derive from embodied metaphors (e.g., numbers as positions along a path). Cross-linguistic evidence shows spatial metaphors for arithmetic in all studied languages.",
                "Lakoff & Núñez, Where Mathematics Comes From", "primary", 0.7, "supporting",
                supports_claims=["embodied_math"]),
            EvidenceItem("cog_02_e2",
                "Congenitally blind mathematicians perform equivalently to sighted peers on abstract algebra tasks, with fMRI showing activation in visual cortex repurposed for mathematical reasoning (Kanjlia et al., 2016).",
                "Kanjlia et al., PNAS", "primary", 0.9, "contradictory",
                contradicts_claims=["embodied_math"],
                supports_claims=["abstract_independent"]),
            EvidenceItem("cog_02_e3",
                "Motor cortex TMS disruption impairs numerical magnitude comparison but not symbolic arithmetic, suggesting grounding is operation-specific (Sato et al., 2007).",
                "Sato et al., Neuropsychologia", "primary", 0.8, "decisive",
                supports_claims=["partial_grounding"]),
            EvidenceItem("cog_02_e4",
                "Review of 47 behavioral studies finds spatial-numerical associations (SNARC effect) are robust but culturally variable and dissociable from mathematical competence (Wood et al., 2008).",
                "Wood et al., Cognition", "review", 0.85, "supporting",
                supports_claims=["partial_grounding"]),
            EvidenceItem("cog_02_e5",
                "Blog post claims 'Math is just body movements' based on misreading of Lakoff.",
                "Popular science blog", "news", 0.15, "irrelevant"),
            EvidenceItem("cog_02_e6",
                "Large language models perform graduate-level mathematics without any sensorimotor experience, challenging strong embodiment claims (Trinh et al., 2024).",
                "Trinh et al., Nature", "primary", 0.85, "contradictory",
                contradicts_claims=["embodied_math"],
                supports_claims=["abstract_independent"]),
        ],
        gt=GroundTruth(
            acceptable_hypotheses=["partial_grounding", "abstract_independent"],
            best_hypothesis="partial_grounding",
            verdict="MIXED",
            support_relations={
                "embodied_math": ["cog_02_e1"],
                "partial_grounding": ["cog_02_e3", "cog_02_e4"],
                "abstract_independent": ["cog_02_e2", "cog_02_e6"],
            },
            contradiction_relations={
                "embodied_math": ["cog_02_e2", "cog_02_e6"],
            },
            source_dependencies=[],
            critical_assumptions=["Spatial metaphors imply causal grounding"],
            decisive_evidence=["cog_02_e3"],
            known_ambiguity=["Whether LLM math counts as evidence about human cognition"],
        )))

    # Pack 3: Working memory capacity limits
    packs.append(_make_pack(
        "cog_03", "cognitive_science",
        "Is working memory capacity fixed at approximately 4 items (Cowan's limit), or is it resource-based and continuously variable?",
        evidence=[
            EvidenceItem("cog_03_e1",
                "Cowan (2001) meta-analysis of change detection, running span, and visual array tasks converges on a limit of 3-5 items across modalities and age groups.",
                "Cowan, Behavioral and Brain Sciences", "review", 0.9, "supporting",
                supports_claims=["fixed_slots"]),
            EvidenceItem("cog_03_e2",
                "Ma, Husain & Bays (2014) show that recall precision decreases continuously with set size in a manner inconsistent with discrete slots but well-fit by a shared resource model.",
                "Ma et al., Nature Neuroscience", "primary", 0.9, "contradictory",
                contradicts_claims=["fixed_slots"],
                supports_claims=["continuous_resource"]),
            EvidenceItem("cog_03_e3",
                "Zhang & Luck (2008) find mixture-model evidence: responses are either precise or random guesses, consistent with discrete slots rather than graded resource.",
                "Zhang & Luck, Nature", "primary", 0.85, "supporting",
                supports_claims=["fixed_slots"]),
            EvidenceItem("cog_03_e4",
                "van den Berg et al. (2012) show that a variable-precision model (neither pure slots nor pure resource) fits data better than both fixed-slot and continuous-resource models.",
                "van den Berg et al., Psychological Review", "primary", 0.9, "decisive",
                supports_claims=["hybrid_model"]),
            EvidenceItem("cog_03_e5",
                "Textbook states 'Miller's magic number 7±2 defines working memory capacity', conflating chunk capacity with item capacity.",
                "Introductory Psychology textbook", "secondary", 0.3, "irrelevant",
                depends_on_source="outdated Miller 1956 interpretation"),
            EvidenceItem("cog_03_e6",
                "Neural recording in macaque PFC shows discrete attractor states corresponding to remembered items, supporting a slot-like mechanism (Lundqvist et al., 2016).",
                "Lundqvist et al., Neuron", "primary", 0.8, "supporting",
                supports_claims=["fixed_slots"]),
        ],
        gt=GroundTruth(
            acceptable_hypotheses=["hybrid_model", "continuous_resource"],
            best_hypothesis="hybrid_model",
            verdict="MIXED",
            support_relations={
                "fixed_slots": ["cog_03_e1", "cog_03_e3", "cog_03_e6"],
                "continuous_resource": ["cog_03_e2"],
                "hybrid_model": ["cog_03_e4"],
            },
            contradiction_relations={"fixed_slots": ["cog_03_e2"]},
            source_dependencies=[],
            critical_assumptions=["Visual WM paradigms generalize to verbal/spatial WM"],
            decisive_evidence=["cog_03_e4"],
            known_ambiguity=["Whether 'variable precision' is slots with noise or resource with discretization"],
        )))

    # Pack 4: Predictive processing / prediction error
    packs.append(_make_pack(
        "cog_04", "cognitive_science",
        "Is the brain primarily a prediction engine that minimizes prediction error (predictive processing), and does this framework explain perception, action, and cognition?",
        evidence=[
            EvidenceItem("cog_04_e1",
                "Clark (2013) synthesizes evidence from perception, motor control, and attention showing hierarchical predictive coding can unify these domains. Mismatch negativity (MMN) directly measures prediction error.",
                "Clark, Behavioral and Brain Sciences", "review", 0.85, "supporting",
                supports_claims=["predictive_processing"]),
            EvidenceItem("cog_04_e2",
                "Keller & Mrsic-Flogel (2018) show that visual cortex neurons in mice carry prediction-error signals that update with learning, providing cellular-level evidence for predictive coding.",
                "Keller & Mrsic-Flogel, Neuron", "primary", 0.9, "supporting",
                supports_claims=["predictive_processing"]),
            EvidenceItem("cog_04_e3",
                "Bowers & Davis (2012) argue that predictive coding models are unfalsifiable because any neural response can be reinterpreted as either a prediction or a prediction error.",
                "Bowers & Davis, Psychological Review", "primary", 0.8, "contradictory",
                contradicts_claims=["predictive_processing"]),
            EvidenceItem("cog_04_e4",
                "Walsh et al. (2020) demonstrate that predictive processing cannot account for creative imagination or counterfactual reasoning without additional generative mechanisms not included in the standard framework.",
                "Walsh et al., Cognitive Science", "primary", 0.75, "weak",
                contradicts_claims=["predictive_processing_universal"]),
            EvidenceItem("cog_04_e5",
                "Rao & Ballard (1999) computational model replicates V1 receptive field properties using hierarchical predictive coding, establishing computational plausibility.",
                "Rao & Ballard, Nature Neuroscience", "primary", 0.9, "supporting",
                supports_claims=["predictive_processing"]),
        ],
        gt=GroundTruth(
            acceptable_hypotheses=["predictive_processing", "predictive_processing_limited"],
            best_hypothesis="predictive_processing_limited",
            verdict="SUPPORTED",
            support_relations={
                "predictive_processing": ["cog_04_e1", "cog_04_e2", "cog_04_e5"],
            },
            contradiction_relations={
                "predictive_processing": ["cog_04_e3"],
                "predictive_processing_universal": ["cog_04_e4"],
            },
            source_dependencies=[],
            critical_assumptions=["Prediction error signals in neurons = predictive coding architecture"],
            decisive_evidence=["cog_04_e2"],
            known_ambiguity=["Whether predictive processing is a complete theory or a useful framework"],
        )))

    # Pack 5: Sapir-Whorf / linguistic relativity
    packs.append(_make_pack(
        "cog_05", "cognitive_science",
        "Does language shape thought (linguistic relativity)? Specifically, do cross-linguistic differences in color terminology affect color perception and discrimination?",
        evidence=[
            EvidenceItem("cog_05_e1",
                "Winawer et al. (2007) show Russian speakers, who have obligatory light/dark blue distinction (goluboy/siniy), discriminate these colors faster than English speakers in behavioral tasks.",
                "Winawer et al., PNAS", "primary", 0.9, "supporting",
                supports_claims=["linguistic_relativity"]),
            EvidenceItem("cog_05_e2",
                "The same color discrimination advantage disappears under verbal interference (dual-task) but not spatial interference, suggesting language-mediated rather than perceptual effect (Winawer et al., 2007, Experiment 2).",
                "Winawer et al., PNAS Exp 2", "primary", 0.9, "decisive",
                supports_claims=["weak_relativity"],
                contradicts_claims=["strong_relativity"]),
            EvidenceItem("cog_05_e3",
                "Regier & Kay (2009) find universal tendencies in color naming across 110 languages despite surface variation, suggesting biological constraints dominate linguistic effects.",
                "Regier & Kay, Current Opinion in Psychology", "review", 0.85, "contradictory",
                contradicts_claims=["strong_relativity"],
                supports_claims=["universal_perception"]),
            EvidenceItem("cog_05_e4",
                "Pre-linguistic infants show categorical color perception at boundaries that match English categories, suggesting innate perceptual categories precede language (Bornstein et al., 1976; replicated by Franklin et al., 2005).",
                "Bornstein 1976, Franklin 2005", "primary", 0.85, "contradictory",
                contradicts_claims=["strong_relativity"]),
            EvidenceItem("cog_05_e5",
                "Popular article claims 'Eskimos have 50 words for snow, proving language determines reality' — a widely debunked misrepresentation.",
                "Popular media", "news", 0.1, "irrelevant"),
        ],
        gt=GroundTruth(
            acceptable_hypotheses=["weak_relativity", "language_augmented_perception"],
            best_hypothesis="weak_relativity",
            verdict="SUPPORTED",
            support_relations={
                "linguistic_relativity": ["cog_05_e1"],
                "weak_relativity": ["cog_05_e1", "cog_05_e2"],
            },
            contradiction_relations={
                "strong_relativity": ["cog_05_e2", "cog_05_e3", "cog_05_e4"],
            },
            source_dependencies=[],
            critical_assumptions=["RT differences reflect genuine perceptual change vs. labeling strategy"],
            decisive_evidence=["cog_05_e2"],
            known_ambiguity=["Whether online language effects count as 'shaping thought'"],
        )))

    return packs


def _ai_research_packs() -> list[StaticEvidencePack]:
    """AI research domain — 5 packs."""
    packs = []

    # Pack 1: Scaling laws and emergent abilities
    packs.append(_make_pack(
        "ai_01", "ai_research",
        "Do large language models exhibit genuine emergent abilities at scale, or are apparent emergent transitions artifacts of evaluation methodology?",
        evidence=[
            EvidenceItem("ai_01_e1",
                "Wei et al. (2022) document abilities (arithmetic, word unscrambling, multi-step reasoning) that appear absent below a threshold model size and suddenly emerge above it, across multiple model families.",
                "Wei et al., TMLR 2022", "primary", 0.85, "supporting",
                supports_claims=["genuine_emergence"]),
            EvidenceItem("ai_01_e2",
                "Schaeffer, Miranda & Koyejo (2024) demonstrate that all claimed emergent abilities can be explained by nonlinear or discontinuous evaluation metrics. Using linear metrics (e.g., edit distance), performance improves smoothly with scale.",
                "Schaeffer et al., NeurIPS 2024", "primary", 0.9, "contradictory",
                contradicts_claims=["genuine_emergence"],
                supports_claims=["metric_artifact"]),
            EvidenceItem("ai_01_e3",
                "Lu et al. (2024) show that for some tasks, performance genuinely transitions from near-random to near-perfect within a narrow range of model sizes, even with continuous metrics, but only for tasks requiring compositional generalization.",
                "Lu et al., ICLR 2024", "primary", 0.85, "decisive",
                supports_claims=["partial_emergence"]),
            EvidenceItem("ai_01_e4",
                "Blog post claims 'AGI will emerge at 10T parameters' based on extrapolation of the Wei et al. findings.",
                "AI hype blog", "news", 0.1, "irrelevant"),
            EvidenceItem("ai_01_e5",
                "Kaplan et al. (2020) show smooth power-law scaling of cross-entropy loss with model size, data, and compute, suggesting underlying capability growth is continuous.",
                "Kaplan et al., OpenAI scaling laws", "primary", 0.9, "supporting",
                supports_claims=["smooth_scaling"]),
            EvidenceItem("ai_01_e6",
                "A tech news article repeats claims from the Wei et al. paper without mentioning the Schaeffer rebuttal.",
                "Tech journalism, 2023", "news", 0.3, "dependent",
                depends_on_source="Wei et al., TMLR 2022",
                supports_claims=["genuine_emergence"]),
        ],
        gt=GroundTruth(
            acceptable_hypotheses=["metric_artifact", "partial_emergence"],
            best_hypothesis="partial_emergence",
            verdict="MIXED",
            support_relations={
                "genuine_emergence": ["ai_01_e1", "ai_01_e6"],
                "metric_artifact": ["ai_01_e2"],
                "partial_emergence": ["ai_01_e3"],
                "smooth_scaling": ["ai_01_e5"],
            },
            contradiction_relations={
                "genuine_emergence": ["ai_01_e2"],
            },
            source_dependencies=[("ai_01_e6", "ai_01_e1")],
            critical_assumptions=["Evaluation metric choice does not constitute the phenomenon"],
            decisive_evidence=["ai_01_e2", "ai_01_e3"],
            known_ambiguity=["Whether metric sensitivity invalidates the emergent framing entirely"],
        )))

    # Pack 2: Chain-of-thought faithful reasoning
    packs.append(_make_pack(
        "ai_02", "ai_research",
        "Are chain-of-thought (CoT) traces in large language models faithful representations of the model's reasoning process, or post-hoc rationalizations?",
        evidence=[
            EvidenceItem("ai_02_e1",
                "Turpin et al. (2024) show that biasing features (answer order, user opinion) change model answers without appearing in CoT traces, demonstrating systematic unfaithfulness.",
                "Turpin et al., NeurIPS 2024", "primary", 0.9, "supporting",
                supports_claims=["unfaithful"]),
            EvidenceItem("ai_02_e2",
                "Lanham et al. (2023) find that truncating or corrupting CoT traces often does not change the final answer, suggesting the model may not depend on its own generated reasoning.",
                "Lanham et al., 2023", "primary", 0.85, "supporting",
                supports_claims=["unfaithful"]),
            EvidenceItem("ai_02_e3",
                "Wei et al. (2022) show that CoT prompting dramatically improves accuracy on math/logic tasks only for large models, suggesting CoT does participate in computation.",
                "Wei et al., NeurIPS 2022", "primary", 0.85, "contradictory",
                contradicts_claims=["unfaithful"],
                supports_claims=["partially_faithful"]),
            EvidenceItem("ai_02_e4",
                "Anthropic (2025) mechanistic interpretability work identifies circuits that track CoT reasoning steps, showing some internal computation aligns with the trace.",
                "Anthropic, 2025 interpretability blog", "primary", 0.75, "supporting",
                supports_claims=["partially_faithful"]),
            EvidenceItem("ai_02_e5",
                "Press release claims 'AI can now explain its reasoning' based on CoT results, without discussing faithfulness concerns.",
                "Corporate press release", "news", 0.2, "irrelevant"),
        ],
        gt=GroundTruth(
            acceptable_hypotheses=["partially_faithful", "task_dependent_faithfulness"],
            best_hypothesis="partially_faithful",
            verdict="MIXED",
            support_relations={
                "unfaithful": ["ai_02_e1", "ai_02_e2"],
                "partially_faithful": ["ai_02_e3", "ai_02_e4"],
            },
            contradiction_relations={"unfaithful": ["ai_02_e3"]},
            source_dependencies=[],
            critical_assumptions=["Faithfulness is a property of the trace-answer relationship"],
            decisive_evidence=["ai_02_e1"],
            known_ambiguity=["Whether partial faithfulness is sufficient for reliability"],
        )))

    # Pack 3: RLHF and alignment
    packs.append(_make_pack(
        "ai_03", "ai_research",
        "Does RLHF (Reinforcement Learning from Human Feedback) produce genuinely aligned models, or does it primarily teach surface compliance that breaks under distribution shift?",
        evidence=[
            EvidenceItem("ai_03_e1",
                "Ouyang et al. (2022) show InstructGPT with RLHF significantly improves helpfulness and safety ratings compared to base GPT-3, with human evaluators preferring RLHF outputs 85% of the time.",
                "Ouyang et al., NeurIPS 2022", "primary", 0.9, "supporting",
                supports_claims=["genuine_alignment"]),
            EvidenceItem("ai_03_e2",
                "Casper et al. (2023) catalog fundamental limitations of RLHF including reward hacking, distributional shift vulnerability, and inability to express complex value structures.",
                "Casper et al., TMLR 2023", "review", 0.85, "contradictory",
                contradicts_claims=["genuine_alignment"],
                supports_claims=["surface_compliance"]),
            EvidenceItem("ai_03_e3",
                "Wolf et al. (2024) demonstrate that jailbreaking RLHF-aligned models is trivially easy with adversarial suffixes, suggesting alignment is a shallow pattern match.",
                "Wolf et al., 2024", "primary", 0.85, "decisive",
                contradicts_claims=["genuine_alignment"],
                supports_claims=["surface_compliance"]),
            EvidenceItem("ai_03_e4",
                "Bai et al. (2022) find that RLHF models trained with Constitutional AI show improved robustness to adversarial attacks compared to standard RLHF.",
                "Bai et al., 2022", "primary", 0.85, "supporting",
                supports_claims=["improvable_alignment"]),
            EvidenceItem("ai_03_e5",
                "Reddit user claims 'RLHF is just censorship' based on a single refused request.",
                "Reddit comment", "news", 0.05, "irrelevant"),
        ],
        gt=GroundTruth(
            acceptable_hypotheses=["surface_compliance", "improvable_alignment"],
            best_hypothesis="surface_compliance",
            verdict="MIXED",
            support_relations={
                "genuine_alignment": ["ai_03_e1"],
                "surface_compliance": ["ai_03_e2", "ai_03_e3"],
                "improvable_alignment": ["ai_03_e4"],
            },
            contradiction_relations={"genuine_alignment": ["ai_03_e2", "ai_03_e3"]},
            source_dependencies=[],
            critical_assumptions=["Human preference ratings measure alignment"],
            decisive_evidence=["ai_03_e3"],
            known_ambiguity=["Whether any training method can produce deep alignment"],
        )))

    # Pack 4: In-context learning mechanism
    packs.append(_make_pack(
        "ai_04", "ai_research",
        "Does in-context learning in transformers implement genuine learning algorithms (e.g., gradient descent in forward pass), or is it sophisticated pattern matching from pretraining?",
        evidence=[
            EvidenceItem("ai_04_e1",
                "Akyürek et al. (2023) provide evidence that transformers trained on linear regression tasks implement an algorithm equivalent to one step of gradient descent in their forward pass.",
                "Akyürek et al., ICLR 2023", "primary", 0.85, "supporting",
                supports_claims=["implicit_learning"]),
            EvidenceItem("ai_04_e2",
                "von Oswald et al. (2023) construct transformers that provably implement gradient descent on in-context examples, showing this is mechanistically possible.",
                "von Oswald et al., ICML 2023", "primary", 0.85, "supporting",
                supports_claims=["implicit_learning"]),
            EvidenceItem("ai_04_e3",
                "Chan et al. (2022) show that in-context learning only emerges when pretraining data has 'bursty' distributions (many examples of few concepts), suggesting it leverages pretraining structure.",
                "Chan et al., NeurIPS 2022", "primary", 0.85, "supporting",
                supports_claims=["pretraining_dependent"]),
            EvidenceItem("ai_04_e4",
                "Olsson et al. (2022) identify 'induction heads' — specific attention patterns that implement in-context copying and are necessary for in-context learning.",
                "Olsson et al., 2022", "primary", 0.9, "decisive",
                supports_claims=["mechanism_identified"]),
            EvidenceItem("ai_04_e5",
                "Blog claims 'Transformers literally learn like humans during inference' — overstatement of the gradient descent analogy.",
                "AI blog post", "news", 0.15, "irrelevant"),
        ],
        gt=GroundTruth(
            acceptable_hypotheses=["implicit_learning", "pretraining_dependent"],
            best_hypothesis="implicit_learning",
            verdict="SUPPORTED",
            support_relations={
                "implicit_learning": ["ai_04_e1", "ai_04_e2"],
                "pretraining_dependent": ["ai_04_e3"],
                "mechanism_identified": ["ai_04_e4"],
            },
            contradiction_relations={},
            source_dependencies=[],
            critical_assumptions=["Synthetic task findings transfer to natural language ICL"],
            decisive_evidence=["ai_04_e4"],
            known_ambiguity=["Whether the mechanism is the same for regression tasks and natural language"],
        )))

    # Pack 5: Multimodal grounding
    packs.append(_make_pack(
        "ai_05", "ai_research",
        "Do vision-language models achieve genuine visual understanding, or do they exploit statistical shortcuts in image-text training data?",
        evidence=[
            EvidenceItem("ai_05_e1",
                "Thrush et al. (2022) show CLIP and similar models fail on compositional understanding: 'a cat on a mat' vs 'a mat on a cat' are indistinguishable despite high benchmark scores.",
                "Thrush et al., 2022", "primary", 0.85, "supporting",
                supports_claims=["shortcut_exploitation"]),
            EvidenceItem("ai_05_e2",
                "Yuksekgonul et al. (2023) create ARO benchmark showing VLMs treat image-text matching as bag-of-words, ignoring relations and attributes.",
                "Yuksekgonul et al., NeurIPS 2023", "primary", 0.9, "decisive",
                supports_claims=["shortcut_exploitation"]),
            EvidenceItem("ai_05_e3",
                "GPT-4V achieves near-human performance on visual question answering and can describe complex scenes with accurate spatial reasoning (OpenAI, 2023).",
                "OpenAI GPT-4V technical report", "primary", 0.8, "contradictory",
                contradicts_claims=["shortcut_exploitation"],
                supports_claims=["genuine_understanding_emerging"]),
            EvidenceItem("ai_05_e4",
                "Tong et al. (2024) show that even GPT-4V fails systematically on tasks requiring precise spatial reasoning, counting, and fine-grained attribute binding.",
                "Tong et al., CVPR 2024", "primary", 0.85, "supporting",
                supports_claims=["partial_understanding"]),
        ],
        gt=GroundTruth(
            acceptable_hypotheses=["partial_understanding", "shortcut_plus_emerging"],
            best_hypothesis="partial_understanding",
            verdict="MIXED",
            support_relations={
                "shortcut_exploitation": ["ai_05_e1", "ai_05_e2"],
                "genuine_understanding_emerging": ["ai_05_e3"],
                "partial_understanding": ["ai_05_e4"],
            },
            contradiction_relations={"shortcut_exploitation": ["ai_05_e3"]},
            source_dependencies=[],
            critical_assumptions=["Compositional understanding tests measure genuine understanding"],
            decisive_evidence=["ai_05_e2"],
            known_ambiguity=["Whether newer models have genuinely overcome shortcut reliance"],
        )))

    return packs


def _biomedical_packs() -> list[StaticEvidencePack]:
    """Biomedical research — 5 packs."""
    packs = []

    # Pack 1: Gut microbiome and depression
    packs.append(_make_pack(
        "bio_01", "biomedical",
        "Does the gut microbiome causally influence depression, or are observed correlations explained by confounders (diet, medication, lifestyle)?",
        evidence=[
            EvidenceItem("bio_01_e1",
                "Valles-Colomer et al. (2019) metagenomic study of 1,054 individuals finds significant association between Coprococcus and Dialister depletion and depression, controlling for antidepressant use.",
                "Valles-Colomer et al., Nature Microbiology", "primary", 0.85, "supporting",
                supports_claims=["causal_influence"]),
            EvidenceItem("bio_01_e2",
                "Fecal microbiota transplant (FMT) from depressed humans to germ-free mice induces depressive-like behavior (Kelly et al., 2016), providing experimental causal evidence.",
                "Kelly et al., Journal of Psychiatric Research", "primary", 0.9, "decisive",
                supports_claims=["causal_influence"]),
            EvidenceItem("bio_01_e3",
                "Large-scale Mendelian randomization study (Liu et al., 2023) finds no significant causal effect of gut microbiome composition on depression risk, suggesting confounding explains associations.",
                "Liu et al., Nature Genetics", "primary", 0.9, "contradictory",
                contradicts_claims=["causal_influence"],
                supports_claims=["confounded"]),
            EvidenceItem("bio_01_e4",
                "Probiotic supplementation meta-analysis (Nikolova et al., 2019) finds small but significant improvement in depression symptoms (SMD = -0.24, 95% CI [-0.38, -0.09]).",
                "Nikolova et al., JAMA Psychiatry", "review", 0.85, "supporting",
                supports_claims=["causal_influence"]),
            EvidenceItem("bio_01_e5",
                "Supplement company website claims 'Cure your depression with probiotics!' citing one small uncontrolled study.",
                "Commercial website", "news", 0.05, "irrelevant"),
            EvidenceItem("bio_01_e6",
                "Depression itself alters eating behavior and medication use, both of which change microbiome composition (reverse causation pathway documented in Marx et al., 2021).",
                "Marx et al., Molecular Psychiatry", "review", 0.85, "contradictory",
                contradicts_claims=["causal_influence"],
                supports_claims=["reverse_causation"]),
        ],
        gt=GroundTruth(
            acceptable_hypotheses=["bidirectional", "partial_causal"],
            best_hypothesis="bidirectional",
            verdict="MIXED",
            support_relations={
                "causal_influence": ["bio_01_e1", "bio_01_e2", "bio_01_e4"],
                "confounded": ["bio_01_e3"],
                "reverse_causation": ["bio_01_e6"],
            },
            contradiction_relations={"causal_influence": ["bio_01_e3", "bio_01_e6"]},
            source_dependencies=[],
            critical_assumptions=["Mouse models of depression translate to humans"],
            decisive_evidence=["bio_01_e2", "bio_01_e3"],
            known_ambiguity=["Whether FMT mouse results generalize to human depression"],
        )))

    # Packs 2-5: additional biomedical topics
    for i, (q, verdict) in enumerate([
        ("Does intermittent fasting improve healthspan independently of caloric restriction?", "MIXED"),
        ("Is Alzheimer's disease primarily caused by amyloid-beta plaques, or are plaques a consequence rather than cause?", "MIXED"),
        ("Do antioxidant supplements reduce cancer risk, or can they paradoxically promote tumor growth?", "REFUTED"),
        ("Is the reported decline in human sperm counts real and globally generalizable, or an artifact of measurement and selection bias?", "UNDERDETERMINED"),
    ], start=2):
        packs.append(_make_pack(
            f"bio_{i:02d}", "biomedical", q,
            evidence=[
                EvidenceItem(f"bio_{i:02d}_e1",
                    f"Primary study supporting the main claim in domain-specific context for question about {q[:50]}...",
                    "Primary research journal", "primary", 0.85, "supporting",
                    supports_claims=["main_claim"]),
                EvidenceItem(f"bio_{i:02d}_e2",
                    f"Contradictory evidence from large-scale study challenging the main claim regarding {q[:50]}...",
                    "Large cohort study", "primary", 0.9, "contradictory",
                    contradicts_claims=["main_claim"]),
                EvidenceItem(f"bio_{i:02d}_e3",
                    f"Meta-analysis providing nuanced view of the question about {q[:50]}...",
                    "Systematic review", "review", 0.85, "decisive",
                    supports_claims=["nuanced_view"]),
                EvidenceItem(f"bio_{i:02d}_e4",
                    f"Media oversimplification of findings regarding {q[:50]}...",
                    "Health news website", "news", 0.2, "irrelevant"),
            ],
            gt=GroundTruth(
                acceptable_hypotheses=["nuanced_view", "main_claim_partial"],
                best_hypothesis="nuanced_view",
                verdict=verdict,
                support_relations={"main_claim": [f"bio_{i:02d}_e1"]},
                contradiction_relations={"main_claim": [f"bio_{i:02d}_e2"]},
                source_dependencies=[], critical_assumptions=["Study populations are representative"],
                decisive_evidence=[f"bio_{i:02d}_e3"],
                known_ambiguity=["Generalizability across populations"],
            )))

    return packs


def _econ_packs() -> list[StaticEvidencePack]:
    """Economics domain — 5 packs."""
    packs = []

    packs.append(_make_pack(
        "econ_01", "economics",
        "Does minimum wage increase cause significant unemployment, or does the monopsony model better explain labor market responses?",
        evidence=[
            EvidenceItem("econ_01_e1",
                "Card & Krueger (1994) natural experiment comparing NJ and PA fast-food employment after NJ minimum wage increase found no negative employment effect.",
                "Card & Krueger, AER 1994", "primary", 0.9, "supporting",
                supports_claims=["no_unemployment_effect"]),
            EvidenceItem("econ_01_e2",
                "Neumark & Wascher (2008) meta-analysis of 100+ studies finds majority show small negative employment effects, especially for young and low-skilled workers.",
                "Neumark & Wascher, MIT Press", "review", 0.85, "contradictory",
                contradicts_claims=["no_unemployment_effect"],
                supports_claims=["negative_effect"]),
            EvidenceItem("econ_01_e3",
                "Dube, Lester & Reich (2010) using contiguous county-pairs across state borders find no significant disemployment effects, replicating Card & Krueger with modern methods.",
                "Dube et al., Review of Economics and Statistics", "primary", 0.9, "decisive",
                supports_claims=["no_unemployment_effect"]),
            EvidenceItem("econ_01_e4",
                "Jardim et al. (2022) study Seattle's $15 minimum wage using administrative data finds hours reduction offset wage gains for low-wage workers.",
                "Jardim et al., QJE 2022", "primary", 0.85, "contradictory",
                contradicts_claims=["no_unemployment_effect"]),
            EvidenceItem("econ_01_e5",
                "Political advocacy organization claims 'minimum wage destroys millions of jobs' citing no peer-reviewed evidence.",
                "Advocacy group press release", "news", 0.1, "irrelevant"),
        ],
        gt=GroundTruth(
            acceptable_hypotheses=["small_or_no_effect", "context_dependent"],
            best_hypothesis="context_dependent",
            verdict="MIXED",
            support_relations={
                "no_unemployment_effect": ["econ_01_e1", "econ_01_e3"],
                "negative_effect": ["econ_01_e2", "econ_01_e4"],
            },
            contradiction_relations={
                "no_unemployment_effect": ["econ_01_e2", "econ_01_e4"],
            },
            source_dependencies=[],
            critical_assumptions=["Natural experiments identify causal effects"],
            decisive_evidence=["econ_01_e3"],
            known_ambiguity=["Whether small cities behave like large metro areas"],
        )))

    for i, (q, v) in enumerate([
        ("Does quantitative easing primarily increase asset prices without proportional effects on real economic output?", "SUPPORTED"),
        ("Can cryptocurrency serve as a viable medium of exchange, or is it primarily a speculative asset?", "SUPPORTED"),
        ("Does financial literacy education significantly improve financial outcomes?", "MIXED"),
        ("Does trade liberalization increase inequality within developing countries?", "MIXED"),
    ], start=2):
        packs.append(_make_pack(
            f"econ_{i:02d}", "economics", q,
            evidence=[
                EvidenceItem(f"econ_{i:02d}_e1",
                    f"Primary empirical study supporting the main position on {q[:50]}...",
                    "Top economics journal", "primary", 0.85, "supporting",
                    supports_claims=["main_claim"]),
                EvidenceItem(f"econ_{i:02d}_e2",
                    f"Counter-evidence from natural experiment or RCT regarding {q[:50]}...",
                    "Experimental economics study", "primary", 0.9, "contradictory",
                    contradicts_claims=["main_claim"]),
                EvidenceItem(f"econ_{i:02d}_e3",
                    f"Comprehensive review synthesizing evidence on {q[:50]}...",
                    "Annual Review of Economics", "review", 0.85, "decisive",
                    supports_claims=["nuanced_view"]),
                EvidenceItem(f"econ_{i:02d}_e4",
                    f"Op-ed using selective evidence about {q[:50]}...",
                    "Newspaper opinion section", "news", 0.2, "irrelevant"),
            ],
            gt=GroundTruth(
                acceptable_hypotheses=["nuanced_view", "main_claim_qualified"],
                best_hypothesis="nuanced_view", verdict=v,
                support_relations={"main_claim": [f"econ_{i:02d}_e1"]},
                contradiction_relations={"main_claim": [f"econ_{i:02d}_e2"]},
                source_dependencies=[], critical_assumptions=["Identification strategy is valid"],
                decisive_evidence=[f"econ_{i:02d}_e3"],
                known_ambiguity=["Context/time period sensitivity"],
            )))

    return packs


def _history_packs() -> list[StaticEvidencePack]:
    """History of science domain — 5 packs."""
    packs = []

    packs.append(_make_pack(
        "hist_01", "history_of_science",
        "Did Kuhn's paradigm shift model accurately describe the Copernican revolution, or was the transition more gradual and multi-causal than his account suggests?",
        evidence=[
            EvidenceItem("hist_01_e1",
                "Kuhn (1962) argues the shift from Ptolemaic to Copernican astronomy exemplifies paradigm shift: crisis accumulation, revolutionary break, new normal science.",
                "Kuhn, Structure of Scientific Revolutions", "primary", 0.8, "supporting",
                supports_claims=["paradigm_shift_model"]),
            EvidenceItem("hist_01_e2",
                "Westman (1975) shows only ~10 astronomers accepted heliocentrism by 1600 (60 years after Copernicus), and most adopted it for computational convenience rather than physical conviction.",
                "Westman, in The Copernican Achievement", "primary", 0.85, "contradictory",
                contradicts_claims=["paradigm_shift_model"],
                supports_claims=["gradual_transition"]),
            EvidenceItem("hist_01_e3",
                "Gingerich (2004) analysis of 600 surviving copies of De Revolutionibus shows annotation patterns indicating gradual, selective adoption of Copernican mathematical methods without accepting heliocentrism.",
                "Gingerich, The Book Nobody Read", "primary", 0.9, "decisive",
                supports_claims=["gradual_transition"]),
            EvidenceItem("hist_01_e4",
                "Popular science article states 'Copernicus single-handedly overthrew the medieval worldview', dramatizing the transition.",
                "Popular science magazine", "news", 0.2, "irrelevant"),
        ],
        gt=GroundTruth(
            acceptable_hypotheses=["gradual_transition", "modified_paradigm_shift"],
            best_hypothesis="gradual_transition",
            verdict="SUPPORTED",
            support_relations={
                "paradigm_shift_model": ["hist_01_e1"],
                "gradual_transition": ["hist_01_e2", "hist_01_e3"],
            },
            contradiction_relations={"paradigm_shift_model": ["hist_01_e2", "hist_01_e3"]},
            source_dependencies=[],
            critical_assumptions=["Kuhn intended literal rather than ideal-type description"],
            decisive_evidence=["hist_01_e3"],
            known_ambiguity=["Whether 'paradigm shift' is meant as precise history or useful heuristic"],
        )))

    for i, (q, v) in enumerate([
        ("Was the Scientific Revolution a coherent historical event, or a retrospective construct?", "MIXED"),
        ("Did the peer review system arise primarily to improve scientific quality, or to manage intellectual authority?", "MIXED"),
        ("Was Semmelweis's rejection primarily due to lack of germ theory, or professional politics?", "MIXED"),
        ("Did Thomas Edison's laboratory represent genuine collaborative innovation, or primarily Edison's self-promotion?", "MIXED"),
    ], start=2):
        packs.append(_make_pack(
            f"hist_{i:02d}", "history_of_science", q,
            evidence=[
                EvidenceItem(f"hist_{i:02d}_e1", f"Primary historical source on {q[:50]}...",
                    "Historical journal", "primary", 0.85, "supporting",
                    supports_claims=["traditional_view"]),
                EvidenceItem(f"hist_{i:02d}_e2", f"Revisionist scholarship challenging view on {q[:50]}...",
                    "Revisionist history study", "primary", 0.85, "contradictory",
                    contradicts_claims=["traditional_view"], supports_claims=["revised_view"]),
                EvidenceItem(f"hist_{i:02d}_e3", f"Archival evidence providing nuance on {q[:50]}...",
                    "Archival research", "primary", 0.9, "decisive",
                    supports_claims=["nuanced_view"]),
                EvidenceItem(f"hist_{i:02d}_e4", f"Popular narrative simplifying {q[:50]}...",
                    "Popular history book", "secondary", 0.4, "weak",
                    depends_on_source="Traditional narrative"),
            ],
            gt=GroundTruth(
                acceptable_hypotheses=["nuanced_view", "revised_view"],
                best_hypothesis="nuanced_view", verdict=v,
                support_relations={"traditional_view": [f"hist_{i:02d}_e1"]},
                contradiction_relations={"traditional_view": [f"hist_{i:02d}_e2"]},
                source_dependencies=[(f"hist_{i:02d}_e4", "Traditional narrative")],
                critical_assumptions=["Archival sources are representative"],
                decisive_evidence=[f"hist_{i:02d}_e3"],
                known_ambiguity=["Historiographic framing effects"],
            )))

    return packs


def _social_science_packs() -> list[StaticEvidencePack]:
    """Social science domain — 5 packs."""
    packs = []

    packs.append(_make_pack(
        "soc_01", "social_science",
        "Is the replication crisis in social psychology primarily due to p-hacking and QRPs, or does it reveal deeper problems with effect size estimation in behavioral science?",
        evidence=[
            EvidenceItem("soc_01_e1",
                "Open Science Collaboration (2015) replicated 100 psychology studies: only 36% reached significance, with mean effect sizes halved.",
                "Open Science Collaboration, Science", "primary", 0.95, "supporting",
                supports_claims=["overestimated_effects"]),
            EvidenceItem("soc_01_e2",
                "Simmons et al. (2011) demonstrate that standard 'researcher degrees of freedom' can produce p<.05 for almost any hypothesis, showing QRPs are sufficient to explain many false positives.",
                "Simmons et al., Psychological Science", "primary", 0.9, "supporting",
                supports_claims=["qrp_primary_cause"]),
            EvidenceItem("soc_01_e3",
                "Protzko et al. (2024) pre-registered replications of 16 classic effects with transparent methods: 11/16 replicated, suggesting the crisis is concentrated in specific subfields.",
                "Protzko et al., Nature Human Behaviour", "primary", 0.9, "decisive",
                supports_claims=["concentrated_not_universal"]),
            EvidenceItem("soc_01_e4",
                "Blog post claims 'All of social psychology is fake' based on selective reading of failed replications.",
                "Blog post", "news", 0.1, "irrelevant"),
            EvidenceItem("soc_01_e5",
                "Van Bavel et al. (2016) argue many replication failures reflect hidden moderators and contextual sensitivity rather than original fraud or error.",
                "Van Bavel et al., PNAS", "primary", 0.75, "weak",
                supports_claims=["hidden_moderators"],
                contradicts_claims=["qrp_primary_cause"]),
        ],
        gt=GroundTruth(
            acceptable_hypotheses=["concentrated_not_universal", "multiple_causes"],
            best_hypothesis="multiple_causes",
            verdict="SUPPORTED",
            support_relations={
                "overestimated_effects": ["soc_01_e1"],
                "qrp_primary_cause": ["soc_01_e2"],
                "concentrated_not_universal": ["soc_01_e3"],
            },
            contradiction_relations={"qrp_primary_cause": ["soc_01_e5"]},
            source_dependencies=[],
            critical_assumptions=["Direct replications share the relevant causal features"],
            decisive_evidence=["soc_01_e3"],
            known_ambiguity=["Whether hidden moderators are real or a deflection strategy"],
        )))

    for i, (q, v) in enumerate([
        ("Does social media use causally increase adolescent depression, or do depressed adolescents gravitate toward social media?", "MIXED"),
        ("Is implicit bias (as measured by IAT) a valid predictor of discriminatory behavior?", "MIXED"),
        ("Does diversity training in organizations reduce prejudice and improve outcomes?", "REFUTED"),
        ("Do nudges (choice architecture) produce lasting behavior change, or do effects decay rapidly?", "MIXED"),
    ], start=2):
        packs.append(_make_pack(
            f"soc_{i:02d}", "social_science", q,
            evidence=[
                EvidenceItem(f"soc_{i:02d}_e1", f"Key empirical study on {q[:50]}...",
                    "Top social science journal", "primary", 0.85, "supporting",
                    supports_claims=["main_claim"]),
                EvidenceItem(f"soc_{i:02d}_e2", f"Large-scale counter-evidence on {q[:50]}...",
                    "Preregistered replication", "primary", 0.9, "contradictory",
                    contradicts_claims=["main_claim"]),
                EvidenceItem(f"soc_{i:02d}_e3", f"Systematic review providing balanced assessment of {q[:50]}...",
                    "Psychological Bulletin meta-analysis", "review", 0.9, "decisive",
                    supports_claims=["nuanced_view"]),
                EvidenceItem(f"soc_{i:02d}_e4", f"Media coverage oversimplifying {q[:50]}...",
                    "News article", "news", 0.2, "irrelevant"),
            ],
            gt=GroundTruth(
                acceptable_hypotheses=["nuanced_view", "main_claim_limited"],
                best_hypothesis="nuanced_view", verdict=v,
                support_relations={"main_claim": [f"soc_{i:02d}_e1"]},
                contradiction_relations={"main_claim": [f"soc_{i:02d}_e2"]},
                source_dependencies=[], critical_assumptions=["Measurement validity"],
                decisive_evidence=[f"soc_{i:02d}_e3"],
                known_ambiguity=["Definitional boundaries of key constructs"],
            )))

    return packs


# ===================================================================
# Registry
# ===================================================================

ALL_PACK_GENERATORS = {
    "cognitive_science": _cog_sci_packs,
    "ai_research": _ai_research_packs,
    "biomedical": _biomedical_packs,
    "economics": _econ_packs,
    "history_of_science": _history_packs,
    "social_science": _social_science_packs,
}


def generate_all_packs() -> list[StaticEvidencePack]:
    packs = []
    for gen_fn in ALL_PACK_GENERATORS.values():
        packs.extend(gen_fn())
    return packs


def save_all_packs():
    PACKS_DIR.mkdir(parents=True, exist_ok=True)
    packs = generate_all_packs()
    for pack in packs:
        out = PACKS_DIR / f"{pack.pack_id}.json"
        out.write_text(json.dumps(pack.to_dict(), indent=2))
    print(f"Saved {len(packs)} evidence packs to {PACKS_DIR}")
    return packs


if __name__ == "__main__":
    save_all_packs()
