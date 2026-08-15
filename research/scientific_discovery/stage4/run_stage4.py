#!/usr/bin/env python3
"""
STAGE 4A — REPRESENTATIONAL REGIME REVISION EXPERIMENT

Tests SD-H11 (Detection), SD-H12 (Generation), SD-H13 (Validation),
SD-H14 (Active Discrimination).

World families:
  A: Hidden variable (latent confound)
  B: Interaction (non-additive)
  C: Nonlinear/threshold
  D: Temporal memory
  E: Measurement model
  F: Latent mixture

Controls:
  NEGATIVE: R0 is sufficient (no revision needed)
  DECOY: R1 overfits, R0 better on held-out

Usage:
  .venv/bin/python research/scientific_discovery/stage4/run_stage4.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import hashlib
from pathlib import Path
from dataclasses import dataclass, field

import numpy as np
from scipy import stats

STAGE4 = Path(__file__).parent
sys.path.insert(0, str(STAGE4.parent.parent.parent))
from asar.scientific_discovery.remote_provider import RemoteLLMProvider
from asar.scientific_discovery.generative_scientist import _strip_markdown_fences

MODEL = "gemma3:27b-it-qat"
TEMPERATURE = 0
CHECKPOINT = STAGE4 / "STAGE4_CHECKPOINT.json"


def safe_json_parse(text: str) -> dict | None:
    if not text:
        return None
    cleaned = _strip_markdown_fences(text)
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except (json.JSONDecodeError, TypeError):
                pass
    return None


# ============================================================
# WORLD DEFINITIONS
# ============================================================

@dataclass
class RegimeWorld:
    """A controlled world for regime revision testing."""
    id: str
    family: str  # A-F or NEGATIVE or DECOY
    r0_description: str  # The initial (insufficient) regime
    observations: str  # What the agent observes
    anomalous_evidence: str  # Evidence that R0 cannot explain
    held_out_evidence: str  # For validation (not shown until validation phase)
    true_regime_description: str  # What R* looks like
    true_missing_structure: str  # Exact structure R0 lacks
    expressible_in_r0: bool  # Can truth be expressed in R0?
    correct_revision_markers: list  # Keywords indicating correct revision
    r0_hypotheses: list  # Hypotheses available in R0 (all insufficient)


# Family A: Hidden Variable
WORLDS_A = [
    RegimeWorld(
        id="A01", family="A",
        r0_description="Variables: X (fertilizer amount), Y (crop yield). Allowed relations: X→Y, Y→X, X⊥Y.",
        observations="Farms using more fertilizer have higher yields.\nCorrelation r=0.7.\nFertilizer increases soil nitrogen.\nNitrogen is needed for plant growth.",
        anomalous_evidence="RCT: Randomized fertilizer amounts show ZERO effect on yield.\nFarms that choose more fertilizer are systematically different.\nSoil quality predicts both fertilizer choice AND yield independently.\nControlling for soil quality eliminates the X-Y correlation entirely.",
        held_out_evidence="New region with uniform soil: fertilizer-yield correlation drops to r=0.02.\nSoil quality measurement added: partial correlation X→Y|Soil = 0.01.",
        true_regime_description="Variables: X (fertilizer), Y (yield), Z (soil quality, LATENT). Relations: Z→X, Z→Y. X has no direct effect on Y.",
        true_missing_structure="LATENT_COMMON_CAUSE: soil quality Z confounds X-Y relationship",
        expressible_in_r0=False,
        correct_revision_markers=["latent", "confound", "common cause", "soil", "hidden variable", "third variable", "spurious"],
        r0_hypotheses=["X causes Y (fertilizer improves yield)", "Y causes X (high-yield farms invest in fertilizer)", "X and Y are independent"],
    ),
    RegimeWorld(
        id="A02", family="A",
        r0_description="Variables: X (ice cream sales), Y (drowning deaths). Allowed relations: X→Y, Y→X, X⊥Y.",
        observations="Months with more ice cream sales have more drownings.\nCorrelation is highly significant (p<0.001).\nThe pattern repeats every year.\nBoth variables spike June-August.",
        anomalous_evidence="Banning ice cream sales in one city: drowning rate UNCHANGED.\nForcing free ice cream in winter: drowning rate UNCHANGED.\nNo plausible mechanism connects ice cream to swimming ability.\nBoth variables are perfectly predicted by a third factor: temperature/season.",
        held_out_evidence="New dataset: controlling for daily temperature, partial correlation = -0.01.\nSeasonal decomposition shows identical phase for both series.",
        true_regime_description="Variables: X (ice cream), Y (drownings), Z (temperature/season, LATENT). Relations: Z→X, Z→Y.",
        true_missing_structure="LATENT_COMMON_CAUSE: temperature drives both variables independently",
        expressible_in_r0=False,
        correct_revision_markers=["temperature", "season", "confound", "common cause", "latent", "third variable", "heat"],
        r0_hypotheses=["Ice cream causes drowning", "Drowning causes ice cream sales", "Independent (but highly correlated)"],
    ),
    RegimeWorld(
        id="A03", family="A",
        r0_description="Variables: X (shoe size), Y (reading ability). Allowed: X→Y, Y→X, X⊥Y.",
        observations="Children with larger shoe sizes read better.\nCorrelation is strong and replicable.\nThe relationship is monotonic.\nSample includes ages 4-16.",
        anomalous_evidence="Within any single age group: correlation drops to zero.\nShoe size does not predict reading within same-age peers.\nA 10-year-old with size 6 reads identically to a 10-year-old with size 4.\nAge alone predicts both shoe size and reading ability perfectly.",
        held_out_evidence="Age-controlled dataset: shoe-reading correlation = 0.00.\nGrowth-stunted children (small feet, normal age): read at age-appropriate level.",
        true_regime_description="Variables: X (shoe size), Y (reading), Z (age/development, LATENT). Relations: Z→X, Z→Y.",
        true_missing_structure="LATENT_COMMON_CAUSE: developmental age drives both shoe growth and cognitive development",
        expressible_in_r0=False,
        correct_revision_markers=["age", "development", "confound", "common cause", "latent", "maturation", "growth"],
        r0_hypotheses=["Shoe size causes reading ability", "Reading causes foot growth", "Independent"],
    ),
]

# Family B: Interaction
WORLDS_B = [
    RegimeWorld(
        id="B01", family="B",
        r0_description="Variables: Drug (D), Gene (G), Recovery (R). Allowed model: R = a*D + b*G + noise. Additive effects only.",
        observations="Drug D helps recovery on average.\nGene G variant is associated with slower recovery.\nBoth main effects are significant in regression.\nR² = 0.35.",
        anomalous_evidence="Patients with Gene+ who take Drug: DRAMATICALLY better than predicted by additive model.\nPatients with Gene- who take Drug: ZERO benefit (Drug effect disappears).\nResidual pattern shows clear cross-shaped structure.\nAdditive model systematically under-predicts Gene+Drug+ group by 40%.",
        held_out_evidence="Validation cohort: interaction D×G explains additional 25% variance.\nGene+ without drug: poor. Gene+ with drug: excellent. Predicted by interaction model only.",
        true_regime_description="R = a*D + b*G + c*D*G + noise. The interaction term D×G is essential.",
        true_missing_structure="INTERACTION: D×G interaction term required; drug only works for Gene+ carriers",
        expressible_in_r0=False,
        correct_revision_markers=["interaction", "moderat", "D×G", "gene-drug", "conditional", "multiply", "pharmacogenomic"],
        r0_hypotheses=["D main effect + G main effect (additive)", "Only D matters", "Only G matters"],
    ),
    RegimeWorld(
        id="B02", family="B",
        r0_description="Variables: Exercise (E), Diet (D), Weight loss (W). Model: W = a*E + b*D + noise. Additive only.",
        observations="Exercise alone produces moderate weight loss.\nDiet alone produces moderate weight loss.\nBoth effects are significant independently.",
        anomalous_evidence="Combined exercise+diet produces weight loss FAR exceeding sum of individual effects.\nExercise increases metabolic rate, which amplifies diet restriction effect.\nThe interaction is 3x larger than either main effect alone.\nNo additive combination of E and D can produce the observed combined effect.",
        held_out_evidence="Factorial RCT: E alone: -2kg, D alone: -3kg, E+D: -12kg (not -5kg as additive predicts).\nMetabolic measurements confirm synergy mechanism.",
        true_regime_description="W = a*E + b*D + c*E*D + noise. Synergistic interaction dominates.",
        true_missing_structure="INTERACTION: Exercise×Diet synergy (metabolic amplification)",
        expressible_in_r0=False,
        correct_revision_markers=["interaction", "synerg", "multiply", "amplif", "non-additive", "E×D", "combined"],
        r0_hypotheses=["E + D additive", "Only E", "Only D"],
    ),
]

# Family C: Nonlinear/Threshold
WORLDS_C = [
    RegimeWorld(
        id="C01", family="C",
        r0_description="Variables: Dose (D), Response (R). Model: R = a + b*D (linear). Smooth continuous.",
        observations="Low doses produce no response.\nHigh doses produce strong response.\nOverall positive correlation.\nLinear fit: R² = 0.6.",
        anomalous_evidence="Below D=50: response is exactly ZERO regardless of dose variation.\nAbove D=50: response jumps sharply and then increases.\nThe transition is abrupt, not gradual.\nResidual plot shows massive systematic error near D=50.",
        held_out_evidence="Fine-grained dosing around D=50: step function confirmed.\nD=49.9: R=0. D=50.1: R=15. No intermediate values exist.",
        true_regime_description="R = 0 if D < threshold; R = a*(D - threshold) if D >= threshold. Threshold ≈ 50.",
        true_missing_structure="THRESHOLD: piecewise function with activation threshold at D≈50",
        expressible_in_r0=False,
        correct_revision_markers=["threshold", "step", "piecewise", "activation", "switch", "nonlinear", "discontinu"],
        r0_hypotheses=["Linear relationship R = a + b*D", "No relationship", "Quadratic"],
    ),
    RegimeWorld(
        id="C02", family="C",
        r0_description="Variables: Stress (S), Performance (P). Model: P = a + b*S (linear).",
        observations="Some stress improves performance.\nToo much stress decreases performance.\nOverall linear fit is poor (R²=0.15).\nScatter plot shows curved pattern.",
        anomalous_evidence="Low stress: low performance. Medium stress: high performance. High stress: low performance.\nThe relationship is perfectly described by an inverted U.\nNo linear model can capture the rise-then-fall pattern.\nQuadratic fit R²=0.85 vs linear R²=0.15.",
        held_out_evidence="Controlled stress manipulation: confirms inverted-U (Yerkes-Dodson).\nPeak performance at moderate stress, decline at both extremes.",
        true_regime_description="P = a + b*S - c*S². Inverted-U (quadratic with negative leading term).",
        true_missing_structure="NONLINEAR: quadratic/inverted-U relationship (Yerkes-Dodson law)",
        expressible_in_r0=False,
        correct_revision_markers=["inverted", "quadratic", "curvilinear", "u-shaped", "nonlinear", "yerkes", "optimal"],
        r0_hypotheses=["Linear positive", "Linear negative", "No relationship"],
    ),
]

# Family D: Temporal Memory
WORLDS_D = [
    RegimeWorld(
        id="D01", family="D",
        r0_description="Variables: Stimulus (S_t), Response (R_t). Model: R_t = f(S_t). Memoryless — response depends only on current stimulus.",
        observations="Stimulus predicts response reasonably.\nSame stimulus sometimes gives different responses.\nVariability seems random.\nR² for concurrent model = 0.4.",
        anomalous_evidence="Previous trial's stimulus PERFECTLY predicts the unexplained variance.\nR_t depends on S_t AND S_{t-1}.\nWhen S_{t-1} was high, R_t is elevated regardless of current S_t.\nAdding lagged predictor: R² jumps from 0.4 to 0.9.",
        held_out_evidence="Controlled sequence: alternating high/low confirms lag-1 dependency.\nModel with S_t + S_{t-1}: validation R² = 0.88.",
        true_regime_description="R_t = a*S_t + b*S_{t-1} + noise. Response depends on current AND previous stimulus.",
        true_missing_structure="TEMPORAL_MEMORY: lag-1 dependency; response carries forward from previous state",
        expressible_in_r0=False,
        correct_revision_markers=["lag", "previous", "memory", "temporal", "history", "prior", "carry", "sequence"],
        r0_hypotheses=["R depends only on current S", "R is random", "R depends on S intensity"],
    ),
]

# Family E: Measurement Model
WORLDS_E = [
    RegimeWorld(
        id="E01", family="E",
        r0_description="Variables: True_ability (A), Test_score (T). Model: T = A (observation equals latent state). No measurement error.",
        observations="Test scores vary between individuals.\nRetest shows different scores.\nScores seem inconsistent.\nSome people score high once and low next time.",
        anomalous_evidence="Test-retest correlation: only 0.6 (should be 1.0 if T=A).\nPractice effects: second test systematically higher.\nTired subjects score lower regardless of ability.\nMultiple tests averaged correlate much higher (0.95) — consistent with measurement noise, not ability change.",
        held_out_evidence="Factor analysis: single latent factor + measurement error fits perfectly.\nReliability improves with more items exactly as predicted by classical test theory.",
        true_regime_description="T = A + error. Observation contains measurement noise independent of true state.",
        true_missing_structure="MEASUREMENT_LAYER: observation ≠ latent state; systematic measurement error exists",
        expressible_in_r0=False,
        correct_revision_markers=["measurement", "error", "noise", "reliability", "latent", "true score", "observation"],
        r0_hypotheses=["Score equals ability", "Ability changes randomly", "Test is invalid"],
    ),
]

# Family F: Latent Mixture
WORLDS_F = [
    RegimeWorld(
        id="F01", family="F",
        r0_description="Variables: Treatment (T), Outcome (O). Model: O = a + b*T + noise. Single homogeneous population.",
        observations="Treatment produces small average benefit.\nHigh variability in outcomes.\nSome patients dramatically improve, others don't change.\nBimodal outcome distribution.",
        anomalous_evidence="Outcome distribution is clearly BIMODAL, not unimodal.\n~40% of patients show zero response; ~60% show strong response.\nSingle-population model cannot produce bimodality.\nA latent subgroup (responders vs non-responders) perfectly explains the pattern.",
        held_out_evidence="Genetic marker identifies responders: responders show effect d=1.2, non-responders d=0.0.\nMixture model validation: BIC strongly favors 2-class over 1-class.",
        true_regime_description="Two latent classes: Responders (60%) with O = a + b_high*T and Non-responders (40%) with O = a (no treatment effect).",
        true_missing_structure="LATENT_MIXTURE: population contains distinct subgroups with different treatment responses",
        expressible_in_r0=False,
        correct_revision_markers=["mixture", "subgroup", "responder", "class", "heterogen", "bimodal", "latent class"],
        r0_hypotheses=["Treatment helps everyone equally", "Treatment doesn't work", "Treatment helps on average"],
    ),
]

# NEGATIVE CONTROL: R0 IS SUFFICIENT
NEGATIVE_WORLDS = [
    RegimeWorld(
        id="NEG01", family="NEGATIVE",
        r0_description="Variables: Hours_studied (H), Exam_score (S). Allowed: S = a + b*H + noise.",
        observations="More study hours correlate with higher scores.\nLinear fit is good (R²=0.7).\nRelationship seems straightforward.\nSome noise but consistent pattern.",
        anomalous_evidence="One outlier student scored high with few hours (gifted?).\nAnother scored low despite many hours (test anxiety?).\nResiduals look normal except 2 points.\nThese outliers are within 2.5 SD — not extreme.",
        held_out_evidence="New class: linear model validates perfectly (R²=0.68).\nNo systematic residual structure. Outliers are just noise.",
        true_regime_description="S = a + b*H + noise. Linear model IS correct. Outliers are just noise.",
        true_missing_structure="NONE — R0 is sufficient",
        expressible_in_r0=True,
        correct_revision_markers=["sufficient", "no revision", "linear works", "noise", "adequate"],
        r0_hypotheses=["Linear: S = a + b*H"],
    ),
    RegimeWorld(
        id="NEG02", family="NEGATIVE",
        r0_description="Variables: Temperature (T), Ice_melt (M). Allowed: M = a + b*T + noise.",
        observations="Higher temperatures cause more ice melt.\nRelationship is linear above 0°C.\nR² = 0.92.\nPhysically sensible.",
        anomalous_evidence="One week of anomalously low melt despite high temperature.\nLikely due to unusual cloud cover or measurement error.\nSubsequent days return to normal relationship.\nSingle data point, not systematic.",
        held_out_evidence="Next season: linear model predicts within 5% accuracy.\nAnomaly was confirmed as instrument malfunction.",
        true_regime_description="M = a + b*T + noise. Linear model is correct. Anomaly was measurement error.",
        true_missing_structure="NONE — R0 is sufficient",
        expressible_in_r0=True,
        correct_revision_markers=["sufficient", "no revision", "linear correct", "measurement error", "adequate", "noise"],
        r0_hypotheses=["Linear: M = a + b*T"],
    ),
    RegimeWorld(
        id="NEG03", family="NEGATIVE",
        r0_description="Variables: Dose (D), Blood_pressure_reduction (R). Allowed: R = a + b*D + noise.",
        observations="Drug reduces blood pressure linearly with dose.\nR² = 0.8.\nSide effects also increase linearly.\nStandard pharmacokinetics.",
        anomalous_evidence="At very high doses (10x therapeutic), response saturates.\nBut these doses are clinically irrelevant.\nWithin therapeutic range: perfectly linear.\nNo patient receives >3x standard dose.",
        held_out_evidence="Clinical trial within normal range: linear model validates R²=0.79.\nSaturation exists but is outside relevant parameter space.",
        true_regime_description="Within therapeutic range: R = a + b*D. Linear is correct for the relevant domain.",
        true_missing_structure="NONE — R0 is sufficient within relevant domain",
        expressible_in_r0=True,
        correct_revision_markers=["sufficient", "no revision", "linear adequate", "within range", "therapeutic"],
        r0_hypotheses=["Linear dose-response within therapeutic range"],
    ),
]

# DECOY: R1 overfits, R0 better on held-out
DECOY_WORLDS = [
    RegimeWorld(
        id="DEC01", family="DECOY",
        r0_description="Variables: X, Y. Model: Y = a + b*X + noise.",
        observations="Strong linear relationship (R²=0.75).\nSmall sample (N=20).\nTwo outliers deviate from line.\nPattern generally consistent.",
        anomalous_evidence="An expanded model with X² term fits training data better (R²=0.82).\nA model with latent variable also fits better.\nBut both improvements are driven by fitting the 2 outliers.\nWith N=20, overfitting risk is high for added parameters.",
        held_out_evidence="Large validation (N=500): linear model R²=0.74, quadratic R²=0.73 (WORSE).\nAdded complexity does not generalize. Linear is correct.",
        true_regime_description="Y = a + b*X + noise. Apparent anomalies are just sampling noise at N=20.",
        true_missing_structure="NONE — simpler R0 is correct; apparent anomaly is overfitting",
        expressible_in_r0=True,
        correct_revision_markers=["overfit", "simpler", "no revision", "noise", "sample size", "sufficient", "parsimony"],
        r0_hypotheses=["Linear Y = a + b*X (correct)"],
    ),
    RegimeWorld(
        id="DEC02", family="DECOY",
        r0_description="Variables: Treatment, Outcome. Model: Outcome = a + b*Treatment + noise. Homogeneous.",
        observations="Treatment shows moderate effect (d=0.5).\nSome variation in response.\nSubgroup analysis suggests differential response.\nBut subgroups defined post-hoc.",
        anomalous_evidence="Post-hoc subgroup: patients with marker M+ show d=0.9, M- show d=0.2.\nThis COULD indicate latent mixture.\nBut marker was chosen after seeing data (data dredging).\n20 markers were tested; M was the most different by chance.",
        held_out_evidence="Preregistered replication with marker M: NO differential response.\nOriginal 'mixture' was a multiple comparisons artifact. Uniform effect.",
        true_regime_description="Homogeneous treatment effect d=0.5. No real subgroups. Post-hoc finding was spurious.",
        true_missing_structure="NONE — apparent heterogeneity is multiple comparisons artifact",
        expressible_in_r0=True,
        correct_revision_markers=["no subgroup", "homogeneous", "spurious", "multiple comparison", "overfit", "sufficient"],
        r0_hypotheses=["Uniform treatment effect (correct)"],
    ),
]


ALL_WORLDS = WORLDS_A + WORLDS_B + WORLDS_C + WORLDS_D + WORLDS_E + WORLDS_F + NEGATIVE_WORLDS + DECOY_WORLDS


# ============================================================
# PROMPTS
# ============================================================

DETECT_PROMPT = (
    "You are a scientist working within this representational framework:\n\n"
    "CURRENT REGIME:\n{regime}\n\n"
    "AVAILABLE HYPOTHESES IN THIS REGIME:\n{hypotheses}\n\n"
    "You have observed:\n{observations}\n\n"
    "And this ANOMALOUS evidence that no current hypothesis fully explains:\n{anomalous}\n\n"
    "Question: Is the current representational regime SUFFICIENT to explain all evidence, "
    "or is there a STRUCTURAL inadequacy that requires changing the representational framework itself?\n\n"
    "Reply ONLY JSON:\n"
    '{{"verdict": "SUFFICIENT" or "SUSPECT" or "INADEQUATE", '
    '"reasoning": "<why>", '
    '"shared_failure": "<what all hypotheses fail to explain>", '
    '"missing_structure": "<what kind of structure the regime lacks, if any>"}}'
)

GENERATE_PROMPT = (
    "The current representational regime has been found INADEQUATE:\n\n"
    "CURRENT REGIME:\n{regime}\n\n"
    "ANOMALOUS EVIDENCE:\n{anomalous}\n\n"
    "IDENTIFIED INADEQUACY:\n{inadequacy}\n\n"
    "Propose a REVISED representational regime that can accommodate the anomalous evidence. "
    "Your revision must specify:\n"
    "- What new structure is added (variables, relations, functional forms)\n"
    "- Why the old regime cannot express this\n"
    "- What new predictions the revised regime makes\n"
    "- What observation could FALSIFY your proposed revision\n\n"
    "Reply ONLY JSON:\n"
    '{{"new_structure": "<what you add>", '
    '"revision_type": "<ADD_VARIABLE/ADD_INTERACTION/ADD_NONLINEARITY/ADD_TEMPORAL/ADD_MEASUREMENT/ADD_MIXTURE/OTHER>", '
    '"why_old_fails": "<why R0 is insufficient>", '
    '"new_predictions": ["<prediction 1>", "<prediction 2>"], '
    '"falsifier": "<what would disprove this revision>", '
    '"complexity_added": "<brief description of added complexity>", '
    '"confidence": <0-100>}}'
)

VALIDATE_PROMPT = (
    "You proposed this representational revision:\n\n"
    "ORIGINAL REGIME:\n{regime}\n\n"
    "PROPOSED REVISION:\n{revision}\n\n"
    "NEW HELD-OUT EVIDENCE (not seen before):\n{held_out}\n\n"
    "Does the new evidence SUPPORT or REJECT your proposed revision?\n"
    "Compare: Does the revised regime predict this evidence better than the original?\n\n"
    "Reply ONLY JSON:\n"
    '{{"decision": "ACCEPT" or "REJECT" or "ROLLBACK", '
    '"held_out_fit_original": "<how well original explains held-out>", '
    '"held_out_fit_revised": "<how well revision explains held-out>", '
    '"reasoning": "<evidence-based justification>", '
    '"confidence": <0-100>}}'
)

BASELINE_REFLECT_PROMPT = (
    "You are investigating a phenomenon.\n\n"
    "CURRENT FRAMEWORK:\n{regime}\n\n"
    "OBSERVATIONS:\n{observations}\n\n"
    "ANOMALOUS EVIDENCE:\n{anomalous}\n\n"
    "Reflect carefully on what might explain the anomaly. Consider whether your "
    "current conceptual framework needs revision. Think broadly about what "
    "structure or mechanism might be missing.\n\n"
    "Reply ONLY JSON:\n"
    '{{"needs_revision": true/false, '
    '"proposed_change": "<what to change if needed>", '
    '"reasoning": "<detailed reasoning>", '
    '"confidence": <0-100>}}'
)


# ============================================================
# EXECUTION ENGINE
# ============================================================

def load_checkpoint() -> dict:
    if CHECKPOINT.exists():
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {"results": {}, "resources": {"calls": 0, "input_tokens": 0, "output_tokens": 0, "latency_ms": 0}}


def save_checkpoint(state: dict):
    tmp = str(CHECKPOINT) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2, default=str)
    os.replace(tmp, CHECKPOINT)


def record_call(state, result):
    state["resources"]["calls"] += 1
    state["resources"]["input_tokens"] += result.prompt_tokens
    state["resources"]["output_tokens"] += result.completion_tokens
    state["resources"]["latency_ms"] += result.latency_ms


def check_revision(text: str, world: RegimeWorld) -> bool:
    """Check if revision contains correct missing structure markers."""
    if not text:
        return False
    lower = text.lower()
    return any(m.lower() in lower for m in world.correct_revision_markers)


def run_asar_condition(provider, world: RegimeWorld, state: dict) -> dict:
    """Full ASAR regime revision pipeline: Detect → Generate → Validate."""
    key = f"{world.id}_ASAR"
    if key in state["results"]:
        return state["results"][key]

    result = {"world_id": world.id, "family": world.family, "condition": "ASAR"}

    # Step 1: DETECT
    hyp_text = "\n".join(f"  - {h}" for h in world.r0_hypotheses)
    r_det = provider.complete(MODEL, [{"role": "user", "content":
        DETECT_PROMPT.format(
            regime=world.r0_description, hypotheses=hyp_text,
            observations=world.observations, anomalous=world.anomalous_evidence
        )}], temperature=TEMPERATURE)
    record_call(state, r_det)
    det = safe_json_parse(r_det.output_text) or {}

    verdict = (det.get("verdict") or "").upper()
    result["detection_verdict"] = verdict
    result["detection_reasoning"] = det.get("reasoning", "")
    result["missing_structure_claim"] = det.get("missing_structure", "")

    # Correct detection?
    if world.expressible_in_r0:
        result["detection_correct"] = verdict == "SUFFICIENT"
        result["false_revision"] = verdict in ("SUSPECT", "INADEQUATE")
    else:
        result["detection_correct"] = verdict in ("SUSPECT", "INADEQUATE")
        result["false_revision"] = False

    # Step 2: GENERATE (only if detected inadequacy)
    if verdict in ("SUSPECT", "INADEQUATE"):
        r_gen = provider.complete(MODEL, [{"role": "user", "content":
            GENERATE_PROMPT.format(
                regime=world.r0_description,
                anomalous=world.anomalous_evidence,
                inadequacy=det.get("missing_structure", det.get("shared_failure", ""))
            )}], temperature=TEMPERATURE)
        record_call(state, r_gen)
        gen = safe_json_parse(r_gen.output_text) or {}

        result["revision_proposed"] = True
        result["revision_type"] = gen.get("revision_type", "")
        result["new_structure"] = gen.get("new_structure", "")
        result["new_predictions"] = gen.get("new_predictions", [])
        result["falsifier"] = gen.get("falsifier", "")
        result["generation_correct"] = check_revision(
            gen.get("new_structure", "") + " " + gen.get("revision_type", ""),
            world
        )

        # Step 3: VALIDATE
        revision_text = (
            f"Type: {gen.get('revision_type', '')}\n"
            f"New structure: {gen.get('new_structure', '')}\n"
            f"Why old fails: {gen.get('why_old_fails', '')}"
        )
        r_val = provider.complete(MODEL, [{"role": "user", "content":
            VALIDATE_PROMPT.format(
                regime=world.r0_description,
                revision=revision_text,
                held_out=world.held_out_evidence
            )}], temperature=TEMPERATURE)
        record_call(state, r_val)
        val = safe_json_parse(r_val.output_text) or {}

        decision = (val.get("decision") or "").upper()
        result["validation_decision"] = decision
        result["validation_correct"] = (
            (decision == "ACCEPT" and not world.expressible_in_r0 and result["generation_correct"])
            or (decision in ("REJECT", "ROLLBACK") and world.expressible_in_r0)
        )
    else:
        result["revision_proposed"] = False
        result["generation_correct"] = world.expressible_in_r0  # Not proposing revision IS correct for sufficient worlds
        result["validation_decision"] = "N/A"
        result["validation_correct"] = world.expressible_in_r0

    # End-to-end success
    if world.expressible_in_r0:
        # Negative control: success = did NOT revise
        result["end_to_end"] = not result.get("revision_proposed", False) or result.get("validation_decision") in ("REJECT", "ROLLBACK")
    else:
        # True regime failure: success = detected + generated correct + validated
        result["end_to_end"] = (
            result.get("detection_correct", False)
            and result.get("generation_correct", False)
            and result.get("validation_decision") == "ACCEPT"
        )

    state["results"][key] = result
    save_checkpoint(state)
    return result


def run_baseline_reflect(provider, world: RegimeWorld, state: dict) -> dict:
    """B2: Unconstrained reflection baseline."""
    key = f"{world.id}_B2"
    if key in state["results"]:
        return state["results"][key]

    result = {"world_id": world.id, "family": world.family, "condition": "B2"}

    hyp_text = "\n".join(f"  - {h}" for h in world.r0_hypotheses)
    r = provider.complete(MODEL, [{"role": "user", "content":
        BASELINE_REFLECT_PROMPT.format(
            regime=world.r0_description,
            observations=world.observations,
            anomalous=world.anomalous_evidence
        )}], temperature=TEMPERATURE)
    record_call(state, r)
    p = safe_json_parse(r.output_text) or {}

    needs_rev = p.get("needs_revision", False)
    proposed = p.get("proposed_change", "")

    result["needs_revision"] = needs_rev
    result["proposed_change"] = proposed

    if world.expressible_in_r0:
        result["detection_correct"] = not needs_rev
        result["false_revision"] = needs_rev
        result["generation_correct"] = not needs_rev
        result["end_to_end"] = not needs_rev
    else:
        result["detection_correct"] = needs_rev
        result["false_revision"] = False
        result["generation_correct"] = check_revision(proposed, world) if needs_rev else False
        result["end_to_end"] = needs_rev and check_revision(proposed, world)

    state["results"][key] = result
    save_checkpoint(state)
    return result


def run_all(provider, state):
    """Run all conditions on all worlds."""
    print("=" * 70)
    print("STAGE 4A — REPRESENTATIONAL REGIME REVISION")
    print("=" * 70)

    for cond_name, runner in [("ASAR", run_asar_condition), ("B2", run_baseline_reflect)]:
        print(f"\n--- {cond_name} ---")
        for i, world in enumerate(ALL_WORLDS):
            key = f"{world.id}_{cond_name}"
            if key in state["results"]:
                r = state["results"][key]
                print(f"  [{i+1}/{len(ALL_WORLDS)}] {world.id} ({world.family}) SKIP "
                      f"(det={r.get('detection_correct')} gen={r.get('generation_correct')} e2e={r.get('end_to_end')})")
                continue
            print(f"  [{i+1}/{len(ALL_WORLDS)}] {world.id} ({world.family})...", end=" ", flush=True)
            r = runner(provider, world, state)
            print(f"det={r.get('detection_correct')} gen={r.get('generation_correct')} "
                  f"e2e={r.get('end_to_end')}")


def analyze(state):
    """Compute all metrics."""
    print("\n" + "=" * 70)
    print("STAGE 4A — ANALYSIS")
    print("=" * 70)

    for cond in ["ASAR", "B2"]:
        results = [v for k, v in state["results"].items() if k.endswith(f"_{cond}")]
        if not results:
            continue

        print(f"\n  --- {cond} ---")

        # Separate by world type
        regime_fail = [r for r in results if not r.get("world_id", "").startswith(("NEG", "DEC"))]
        neg_ctrl = [r for r in results if r.get("world_id", "").startswith("NEG")]
        decoy = [r for r in results if r.get("world_id", "").startswith("DEC")]

        # Detection
        n_det = sum(1 for r in regime_fail if r.get("detection_correct"))
        N_rf = len(regime_fail)
        print(f"\n  DETECTION (regime-failure worlds):")
        print(f"    True detection: {n_det}/{N_rf} = {n_det/N_rf:.3f}" if N_rf else "")

        n_false = sum(1 for r in neg_ctrl + decoy if r.get("false_revision"))
        N_ctrl = len(neg_ctrl) + len(decoy)
        print(f"    False revision (controls): {n_false}/{N_ctrl} = {n_false/N_ctrl:.3f}" if N_ctrl else "")

        # Generation
        gen_results = [r for r in regime_fail if r.get("revision_proposed")]
        n_gen = sum(1 for r in gen_results if r.get("generation_correct"))
        N_gen = len(gen_results)
        print(f"\n  GENERATION (among detected):")
        print(f"    Correct structure: {n_gen}/{N_gen} = {n_gen/N_gen:.3f}" if N_gen else "")

        # End-to-end
        n_e2e = sum(1 for r in regime_fail if r.get("end_to_end"))
        print(f"\n  END-TO-END REGIME RECOVERY:")
        print(f"    {n_e2e}/{N_rf} = {n_e2e/N_rf:.3f}" if N_rf else "")

        # Negative controls
        n_neg_pass = sum(1 for r in neg_ctrl if r.get("end_to_end"))
        print(f"\n  NEGATIVE CONTROLS:")
        print(f"    Correct non-revision: {n_neg_pass}/{len(neg_ctrl)} = {n_neg_pass/len(neg_ctrl):.3f}" if neg_ctrl else "")

        n_dec_pass = sum(1 for r in decoy if r.get("end_to_end"))
        print(f"    Decoy rejection: {n_dec_pass}/{len(decoy)} = {n_dec_pass/len(decoy):.3f}" if decoy else "")

    # Primary contrast
    asar_rf = [v for k, v in state["results"].items()
               if k.endswith("_ASAR") and not k.split("_")[0].startswith(("NEG", "DEC"))]
    b2_rf = [v for k, v in state["results"].items()
             if k.endswith("_B2") and not k.split("_")[0].startswith(("NEG", "DEC"))]

    if asar_rf and b2_rf:
        asar_e2e = sum(1 for r in asar_rf if r.get("end_to_end"))
        b2_e2e = sum(1 for r in b2_rf if r.get("end_to_end"))
        N = len(asar_rf)
        print(f"\n  PRIMARY CONTRAST (ASAR vs B2 reflection):")
        print(f"    ASAR: {asar_e2e}/{N} = {asar_e2e/N:.3f}")
        print(f"    B2:   {b2_e2e}/{N} = {b2_e2e/N:.3f}")
        print(f"    Diff: {(asar_e2e - b2_e2e)/N:+.3f}")

    r = state["resources"]
    print(f"\n  RESOURCES: {r['calls']} calls, {r['input_tokens']+r['output_tokens']} tokens")


def main():
    provider = RemoteLLMProvider(timeout=120)
    state = load_checkpoint()
    run_all(provider, state)
    analyze(state)
    save_checkpoint(state)
    print(f"\n  Saved: {CHECKPOINT}")


if __name__ == "__main__":
    main()
