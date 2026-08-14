#!/usr/bin/env python3
"""
SD-H4 SCALED — PHASE 2 + PHASE 3 EXECUTION (RESUMABLE)

This script resumes from frozen Phase 1 outputs. It does NOT regenerate
hypotheses. It executes ONLY the revision and protection phases.

Bug fix: null-safe handling of `new_explanation` field (None -> "").
This is the ONLY change from the original execution attempt.

Usage:
    .venv/bin/python research/scientific_discovery/stage3d/run_sd_h4_phase2_3.py
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np
from scipy import stats

# Paths
STAGE3D = Path(__file__).parent
CHECKPOINT_FILE = STAGE3D / "SD_H4_CHECKPOINT.json"
MANIFEST_FILE = STAGE3D / "SD_H4_RAW_MANIFEST.json"

# Import provider
import sys
sys.path.insert(0, str(STAGE3D.parent.parent.parent))
from asar.scientific_discovery.remote_provider import RemoteLLMProvider
from asar.scientific_discovery.generative_scientist import _strip_markdown_fences

MODEL = "gemma3:27b-it-qat"
TEMPERATURE = 0


def safe_json_parse(text: str) -> dict | None:
    """Parse JSON with fence stripping and brace extraction."""
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


def load_checkpoint() -> dict:
    """Load existing checkpoint or return empty state."""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {"phase2": {}, "phase3": {}, "resources": {
        "calls": 0, "retries": 0, "input_tokens": 0,
        "output_tokens": 0, "total_tokens": 0, "total_latency_ms": 0,
        "parse_repairs": 0, "unrecoverable": 0
    }}


def save_checkpoint(state: dict) -> None:
    """Persist checkpoint atomically."""
    tmp = str(CHECKPOINT_FILE) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2, default=str)
    os.replace(tmp, CHECKPOINT_FILE)


def record_call(state: dict, result) -> None:
    """Update resource counters."""
    r = state["resources"]
    r["calls"] += 1
    r["retries"] += result.retries
    r["input_tokens"] += result.prompt_tokens
    r["output_tokens"] += result.completion_tokens
    r["total_tokens"] += result.total_tokens
    r["total_latency_ms"] += result.latency_ms


# ============================================================
# FROZEN WORLD DEFINITIONS (from Phase 1)
# ============================================================
WRONG_WORLDS = [
    {"id": "pharm_01", "observations": "Patients taking Drug X report reduced inflammation.\nDrug X binds to receptor R1.\nR1 is expressed in immune cells.\nInflammation markers decrease within 48 hours.", "decisive": "Knockout mice lacking R1 still show inflammation reduction with Drug X.\nDrug X metabolite Y directly inhibits COX-2 enzyme.\nPure R1 agonists do NOT reduce inflammation.\nCOX-2 inhibitor produces identical anti-inflammatory profile.", "true_markers": ["metabolite", "cox", "enzyme", "inhibit"]},
    {"id": "pharm_02", "observations": "Antibiotic Z kills bacteria in vitro at low concentrations.\nZ disrupts cell membranes in lab tests.\nMembrane-less bacteria (L-forms) are resistant.\nZ accumulates in lipid bilayers.", "decisive": "Resistant mutants have altered ribosomal protein S12.\nZ binds 30S ribosomal subunit at therapeutic concentrations.\nMembrane disruption only occurs at 100x therapeutic dose.\nProtein synthesis inhibition correlates perfectly with bactericidal activity.", "true_markers": ["ribosom", "protein synthesis", "translat", "30s"]},
    {"id": "pharm_03", "observations": "Patients on medication M gain weight.\nM increases appetite scores on questionnaires.\nM activates hypothalamic hunger circuits in fMRI.\nWeight gain begins within first month.", "decisive": "Appetite-suppressing co-treatment does NOT prevent M-induced weight gain.\nM causes massive insulin resistance and lipogenesis.\nCaloric intake is identical between M-users and controls.\nMetabolic rate decreases 15% on M independent of food intake.", "true_markers": ["insulin", "lipogenesis", "metaboli", "resistance"]},
    {"id": "pharm_04", "observations": "Drug D reduces blood pressure.\nD blocks calcium channels in smooth muscle.\nCalcium channel blockers are known antihypertensives.\nSmooth muscle relaxation observed in vitro.", "decisive": "D's primary metabolite E is 100x more potent antihypertensive.\nE acts on kidney sodium channels, not calcium channels.\nPure calcium channel blockade by D alone is too weak at therapeutic doses.\nSodium excretion increases 3-fold on D, explaining volume reduction.", "true_markers": ["sodium", "kidney", "renal", "excretion", "volume"]},
    {"id": "pharm_05", "observations": "Supplement S improves cognitive test scores.\nS contains high-dose antioxidants.\nOxidative stress markers decrease on S.\nBrain imaging shows reduced oxidative damage.", "decisive": "Removing antioxidants from S: cognitive benefit PERSISTS.\nS contains trace lithium at sub-therapeutic doses.\nLithium alone reproduces the cognitive benefit exactly.\nAntioxidant-only formulation shows ZERO cognitive effect.", "true_markers": ["lithium", "trace", "mineral", "mood stabili"]},
    {"id": "psych_02", "observations": "Bilingual children score lower on vocabulary tests.\nBilinguals know fewer words per language.\nLanguage interference causes confusion.\nMonolinguals have larger single-language vocabularies.", "decisive": "Total vocabulary across BOTH languages exceeds monolinguals.\nBilinguals show superior executive function and cognitive flexibility.\nVocabulary test bias: tests only measure ONE language.\nLong-term academic outcomes are EQUAL or superior for bilinguals.", "true_markers": ["total", "both languages", "executive", "flexibility", "bias"]},
    {"id": "psych_03", "observations": "People report feeling happier on sunny days.\nSunlight increases serotonin.\nSAD is treated with light therapy.\nMood ratings correlate with hours of sunshine.", "decisive": "Large-N experience sampling: weather explains <1% of mood variance.\nLife circumstances (relationships, work) explain 40x more variance.\nPeople BELIEVE weather affects mood more than it actually does.\nRetrospective reports inflate weather-mood correlation vs real-time measurement.", "true_markers": ["belief", "retrospective", "variance", "circumstances", "overestimate"]},
    {"id": "psych_04", "observations": "Multitaskers report high productivity.\nThey switch between tasks rapidly.\nModern work requires handling multiple streams.\nSelf-assessed performance is high among multitaskers.", "decisive": "Objective performance measurement shows 40% reduction during multitasking.\nSwitch cost accumulates with each transition.\nHeavy multitaskers perform WORSE on attention tasks than non-multitaskers.\nSelf-assessment is uncorrelated with actual measured performance.", "true_markers": ["switch cost", "reduction", "worse", "impair", "uncorrelated"]},
    {"id": "nutr_01", "observations": "High-protein diets correlate with kidney disease.\nProtein metabolism produces urea.\nKidneys filter urea.\nHigh protein increases filtration rate.", "decisive": "30-year prospective study: high protein does NOT cause kidney disease in healthy adults.\nIncreased filtration is adaptive, not pathological.\nOnly PRE-EXISTING kidney disease is worsened by high protein.\nConfounding: high-protein dieters also consume more processed meat/sodium.", "true_markers": ["adaptive", "healthy", "pre-existing", "confound", "processed"]},
    {"id": "nutr_02", "observations": "Organic food buyers are healthier.\nOrganic food has fewer pesticides.\nPesticides cause health problems.\nOrganic produce shows different nutrient profiles.", "decisive": "Randomized controlled trials: organic vs conventional produces NO health difference.\nOrganic buyers exercise more, smoke less, earn more (massive confounding).\nPesticide residues on conventional food are 100-1000x below harmful levels.\nNutritional differences are clinically insignificant.", "true_markers": ["confound", "lifestyle", "exercise", "income", "selection"]},
    {"id": "nutr_04", "observations": "Fruit juice is recommended as healthy.\nFruit contains vitamins and antioxidants.\nJuice retains most fruit nutrients.\nFruit consumption correlates with better health.", "decisive": "Juice removes fiber, concentrating sugar to soda-equivalent levels.\nGlycemic response to juice matches cola.\nFiber in whole fruit slows absorption and improves satiety.\nJuice consumption predicts type 2 diabetes risk increase.", "true_markers": ["sugar", "fiber", "glycemic", "diabetes", "concentrated"]},
    {"id": "epi_01", "observations": "Countries with more chocolate consumption win more Nobel prizes.\nChocolate contains flavonoids that improve cognition.\nCorrelation is statistically significant.\nBiological mechanism is plausible.", "decisive": "The correlation is entirely explained by GDP per capita.\nRich countries consume more chocolate AND fund more research.\nWithin-country analysis shows zero chocolate-Nobel relationship.\nFlavonoid doses in normal chocolate consumption are pharmacologically irrelevant.", "true_markers": ["gdp", "wealth", "confound", "spurious", "income"]},
    {"id": "epi_02", "observations": "Hospitals with more doctors have higher death rates.\nMore complex cases go to teaching hospitals.\nDoctor density correlates with mortality.\nThis suggests over-treatment harm.", "decisive": "Simpson's paradox: hospitals with more doctors treat SICKER patients.\nAdjusting for case severity: more doctors = LOWER mortality.\nSelection bias: dying patients are transferred TO larger hospitals.\nThe ecological correlation reverses at the individual level.", "true_markers": ["simpson", "severity", "selection", "confound", "sicker", "case mix"]},
    {"id": "epi_03", "observations": "Vaccine uptake correlates with autism diagnosis rates.\nBoth increased in the 1990s.\nParents report symptoms appearing after vaccination.\nBiological mechanism proposed (MMR gut-brain).", "decisive": "Multiple studies of millions of children: NO causal link.\nAutism rates unchanged after MMR vaccine removed in Japan.\nDiagnosis rate increase explained by broadened diagnostic criteria.\nOriginal paper was fraudulent and retracted.", "true_markers": ["no link", "diagnostic criteria", "broadened", "fraud", "coincid"]},
    {"id": "epi_04", "observations": "Power line proximity correlates with childhood leukemia.\nEMF exposure is higher near power lines.\nSome lab studies show cellular effects of EMF.\nDose-response relationship observed.", "decisive": "Largest meta-analyses: effect disappears with better exposure measurement.\nCorrelation explained by socioeconomic factors (poorer families live near lines).\nNo biophysical mechanism: EMF energy far below thermal noise.\nBlinded exposure studies show zero effect.", "true_markers": ["socioeconomic", "confound", "poverty", "measurement", "no mechanism"]},
    {"id": "epi_05", "observations": "Moderate alcohol drinkers live longer than abstainers.\nRed wine contains resveratrol.\nJ-shaped mortality curve widely reported.\nCardiovascular benefits documented.", "decisive": "Abstainer group contaminated with former heavy drinkers who quit due to illness.\nMendelian randomization studies: ANY alcohol increases mortality.\nResveratrol doses in wine are 1000x below pharmacological threshold.\nHealthy-drinker bias: moderate drinkers have higher SES and better healthcare.", "true_markers": ["sick quitter", "former", "mendelian", "bias", "contaminated", "confound"]},
    {"id": "neuro_05", "observations": "Mirror neurons explain empathy.\nThey fire when observing and performing actions.\nDeficits linked to autism.\nHumans have extensive mirror neuron system.", "decisive": "Direct human evidence for mirror neurons is extremely limited.\nEmpathy correlates with prefrontal and insular cortex, not mirror areas.\nAutism-mirror neuron link was not replicated in large studies.\nSimulation theory of empathy does not require dedicated mirror hardware.", "true_markers": ["limited evidence", "prefrontal", "insula", "not replicated", "empathy network"]},
    {"id": "eco_01", "observations": "Wolves were reintroduced to Yellowstone.\nRiver courses changed after wolf reintroduction.\nElk behavior changed.\nVegetation recovered near rivers.", "decisive": "River geomorphology changes take decades; wolves present only years.\nRiver changes began BEFORE wolf reintroduction (dam removal, climate).\nTrophic cascade narrative greatly oversimplified.\nMultiple confounding management interventions occurred simultaneously.", "true_markers": ["confound", "dam", "climate", "before wolf", "multiple", "oversimplif"]},
    {"id": "eco_04", "observations": "Forest fires are destructive.\nFire suppression protects forests.\nBurned areas look devastated.\nProperty damage from fires is enormous.", "decisive": "Fire-dependent ecosystems REQUIRE periodic burning for regeneration.\nFire suppression causes fuel accumulation making fires worse.\nMany species evolved fire-adapted traits (serotinous cones, thick bark).\nFireless forests become unhealthy monocultures.", "true_markers": ["depend", "regenerat", "adapted", "fuel accumul", "necessary"]},
    {"id": "exer_03", "observations": "Running damages knees.\nRepetitive impact stresses cartilage.\nRunners report more knee pain.\nJoint degeneration is common in athletes.", "decisive": "Large prospective studies: runners have LESS knee osteoarthritis than non-runners.\nModerate running strengthens cartilage through loading adaptation.\nKnee pain in runners is usually temporary overuse, not degeneration.\nSedentary lifestyle is a stronger risk factor for joint disease.", "true_markers": ["less osteoarthritis", "strengthen", "adapt", "sedentary worse", "protective"]},
    {"id": "edu_05", "observations": "Technology in classrooms improves learning.\nDigital tools engage students.\nAccess to information enhances understanding.\n1:1 laptop programs adopted widely.", "decisive": "RCTs of laptop programs: no academic improvement, sometimes DECLINE.\nDigital distraction (off-task browsing) is primary observed effect.\nTechnology without pedagogical redesign adds nothing.\nHand-note-taking outperforms laptop notes for conceptual learning.", "true_markers": ["no improvement", "distraction", "decline", "without pedagogy", "off-task"]},
    {"id": "gen_02", "observations": "DNA is the sole carrier of hereditary information.\nCentral dogma: DNA to RNA to protein.\nGenome sequence contains all biological information.\nMutations in DNA cause all heritable changes.", "decisive": "Epigenetic inheritance passes information without DNA sequence change.\nMethylation patterns, histone modifications transmit across generations.\nPrions are heritable protein-folding states.\nMaternal effects (cytoplasmic, nutritional) transmit non-genetically.", "true_markers": ["epigenetic", "methylat", "histone", "prion", "maternal effect", "non-genetic"]},
    {"id": "gen_05", "observations": "GMOs are dangerous to health.\nGenetic modification is unnatural.\nTransgenic proteins could be toxic.\nBt toxin in crops harms insects.", "decisive": "Thousands of studies and every major scientific body: GMOs safe for human consumption.\nConventional breeding causes MORE genetic disruption than targeted modification.\nBt toxin is specific to insect gut receptors absent in mammals.\nNo documented case of harm from approved GMO consumption in 25+ years.", "true_markers": ["safe", "no harm", "specific", "more disruption conventional", "thousands studies"]},
]

PROTECTION_WORLDS = [
    "TRUE: Exercise reduces depression.\nWeak contradiction: One small study found no effect in elderly.\nNoise: Some patients feel worse initially.",
    "TRUE: Smoking causes lung cancer.\nWeak contradiction: Some smokers never get cancer.\nNoise: Geography affects rates.",
    "TRUE: Vaccines prevent disease.\nWeak contradiction: Breakthrough infections occur.\nNoise: Natural immunity may be broader.",
    "TRUE: Sleep deprivation impairs cognition.\nWeak contradiction: Some function on 4-5 hours.\nNoise: Individual needs vary.",
    "TRUE: Antibiotics kill bacteria.\nWeak contradiction: Resistance growing.\nNoise: Some infections self-resolve.",
    "TRUE: CO2 emissions warm climate.\nWeak contradiction: Some regions cooled briefly.\nNoise: Solar varies.",
    "TRUE: Plate tectonics drives earthquakes.\nWeak contradiction: Intra-plate quakes exist.\nNoise: Fracking triggers small ones.",
    "TRUE: Natural selection explains biodiversity.\nWeak contradiction: Neutral evolution exists.\nNoise: Punctuated equilibrium.",
    "TRUE: Handwashing prevents disease.\nWeak contradiction: Marginal soap vs water.\nNoise: Sanitizers work too.",
    "TRUE: Gravity follows inverse-square.\nWeak contradiction: Galaxy curves anomalous.\nNoise: Quantum gravity unresolved.",
    "TRUE: DNA stores genetic info.\nWeak contradiction: RNA genomes exist.\nNoise: Epigenetics modifies expression.",
    "TRUE: Light speed constant in vacuum.\nWeak contradiction: Slows in media.\nNoise: Casimir effect.",
    "TRUE: Photosynthesis converts CO2.\nWeak contradiction: C4 plants differ.\nNoise: Efficiency varies.",
    "TRUE: Neurons signal electrochemically.\nWeak contradiction: Gap junctions exist.\nNoise: Glia signal too.",
    "TRUE: Continents drift.\nWeak contradiction: Some features inconsistent.\nNoise: Plumes complicate.",
    "TRUE: Insulin regulates glucose.\nWeak contradiction: Some diabetics have normal insulin.\nNoise: Other hormones too.",
    "TRUE: Earth 4.5 billion years old.\nWeak contradiction: Some dates inconsistent.\nNoise: Young-earth claims.",
    "TRUE: Germs cause disease.\nWeak contradiction: Koch postulates limited.\nNoise: Host factors matter.",
    "TRUE: Water is H2O.\nWeak contradiction: Heavy water differs.\nNoise: Cluster theories.",
    "TRUE: Atoms have protons/neutrons/electrons.\nWeak contradiction: Quarks deeper.\nNoise: QFT is different.",
]

GEN_PROMPT = (
    "You are a scientist investigating a phenomenon.\n\nOBSERVATIONS:\n{obs}\n\n"
    "Based on these observations, propose your best scientific hypothesis.\n"
    "Reply ONLY with JSON:\n"
    '{{"claim": "<your main claim>", "mechanism": "<proposed causal mechanism>", '
    '"confidence": <0-100>, "predictions": ["<testable prediction>"], '
    '"assumptions": ["<key assumption>"]}}'
)

SELF_PROMPT = (
    "You previously proposed this scientific hypothesis:\n\n"
    "Claim: {claim}\nMechanism: {mechanism}\n\n"
    "NEW DECISIVE EVIDENCE has emerged:\n{decisive}\n\n"
    "Update your scientific assessment. Reply ONLY JSON:\n"
    '{{"confidence_in_original": <0-100>, "should_abandon": true/false, '
    '"revision_type": "<ABANDON/REVISE/RETAIN>", '
    '"new_explanation": "<your revised explanation if any>", '
    '"reasoning": "<scientific justification>"}}'
)

EXTERNAL_PROMPT = (
    "Another research group proposed this scientific hypothesis:\n\n"
    "Claim: {claim}\nMechanism: {mechanism}\n\n"
    "NEW DECISIVE EVIDENCE has emerged:\n{decisive}\n\n"
    "Evaluate this hypothesis in light of the new evidence. Reply ONLY JSON:\n"
    '{{"confidence_in_original": <0-100>, "should_abandon": true/false, '
    '"revision_type": "<ABANDON/REVISE/RETAIN>", '
    '"new_explanation": "<your revised explanation if any>", '
    '"reasoning": "<scientific justification>"}}'
)

PROTECTION_PROMPT = (
    "You hold this well-established scientific understanding:\n\n{obs}\n\n"
    "Should you revise or abandon your understanding? Reply ONLY JSON:\n"
    '{{"confidence_in_theory": <0-100>, "should_abandon": true/false, '
    '"reasoning": "<reason>"}}'
)


def run_phase2(provider, state):
    """Phase 2: Self/External revision on WRONG hypotheses."""
    print("\n" + "=" * 70)
    print("PHASE 2: SELF/EXTERNAL REVISION")
    print("=" * 70)

    for i, world in enumerate(WRONG_WORLDS):
        wid = world["id"]
        if wid in state["phase2"]:
            print(f"  [{i+1}/{len(WRONG_WORLDS)}] {wid} — SKIPPED (checkpoint)")
            continue

        print(f"  [{i+1}/{len(WRONG_WORLDS)}] {wid}...", end=" ", flush=True)

        # Step 1: Regenerate hypothesis (deterministic at temp=0)
        r_gen = provider.complete(
            MODEL,
            [{"role": "user", "content": GEN_PROMPT.format(obs=world["observations"])}],
            temperature=TEMPERATURE,
        )
        record_call(state, r_gen)

        gen_parsed = safe_json_parse(r_gen.output_text)
        if not gen_parsed:
            state["phase2"][wid] = {"status": "GEN_FAIL"}
            state["resources"]["unrecoverable"] += 1
            save_checkpoint(state)
            print("GEN_FAIL")
            continue

        claim = gen_parsed.get("claim") or ""
        mechanism = gen_parsed.get("mechanism") or ""
        init_conf = gen_parsed.get("confidence") or -1

        # Step 2: SELF condition
        r_self = provider.complete(
            MODEL,
            [{"role": "user", "content": SELF_PROMPT.format(
                claim=claim, mechanism=mechanism, decisive=world["decisive"]
            )}],
            temperature=TEMPERATURE,
        )
        record_call(state, r_self)

        # Step 3: EXTERNAL condition
        r_ext = provider.complete(
            MODEL,
            [{"role": "user", "content": EXTERNAL_PROMPT.format(
                claim=claim, mechanism=mechanism, decisive=world["decisive"]
            )}],
            temperature=TEMPERATURE,
        )
        record_call(state, r_ext)

        s = safe_json_parse(r_self.output_text)
        e = safe_json_parse(r_ext.output_text)

        if not s or not e:
            state["phase2"][wid] = {"status": "PARSE_FAIL"}
            state["resources"]["unrecoverable"] += 1
            save_checkpoint(state)
            print("PARSE_FAIL")
            continue

        # BUG FIX: null-safe handling of new_explanation
        self_conf = s.get("confidence_in_original") if s.get("confidence_in_original") is not None else 0
        self_abandon = s.get("should_abandon")
        self_rev = (s.get("revision_type") or "").upper()
        self_new = s.get("new_explanation") or ""  # THE FIX: `or ""` handles None

        ext_conf = e.get("confidence_in_original") if e.get("confidence_in_original") is not None else 0
        ext_abandon = e.get("should_abandon")
        ext_new = e.get("new_explanation") or ""  # THE FIX

        # Recovery classification (null-safe)
        recovery = any(m in self_new.lower() for m in world["true_markers"]) if self_new else False

        # Rationalization classification
        if self_abandon is True or self_rev == "ABANDON":
            rat = "ABANDON"
        elif self_rev == "RETAIN" and self_conf > 50:
            rat = "IGNORE_EVIDENCE"
        elif self_rev == "REVISE" and self_conf < 30:
            rat = "LEGITIMATE_REVISION"
        elif self_rev == "REVISE" and self_conf >= 30:
            rat = "AD_HOC_RESCUE"
        elif self_conf < 20:
            rat = "ABANDON"
        else:
            rat = "UNKNOWN"

        sab = int(self_conf) - int(ext_conf)

        state["phase2"][wid] = {
            "status": "OK",
            "init_conf": init_conf,
            "claim": claim[:200],
            "mechanism": mechanism[:200],
            "self_conf": self_conf,
            "self_abandon": self_abandon,
            "self_rev": self_rev,
            "self_new": self_new[:300],
            "ext_conf": ext_conf,
            "ext_abandon": ext_abandon,
            "ext_new": ext_new[:300],
            "recovery": recovery,
            "rationalization": rat,
            "sab": sab,
        }
        save_checkpoint(state)
        print(f"S={self_conf}/{self_abandon} E={ext_conf}/{ext_abandon} R={rat} SAB={sab:+d} REC={recovery}")


def run_phase3(provider, state):
    """Phase 3: True-theory protection."""
    print("\n" + "=" * 70)
    print("PHASE 3: TRUE-THEORY PROTECTION")
    print("=" * 70)

    for i, obs in enumerate(PROTECTION_WORLDS):
        pid = f"prot_{i+1:02d}"
        if pid in state["phase3"]:
            print(f"  [{i+1}/{len(PROTECTION_WORLDS)}] {pid} — SKIPPED (checkpoint)")
            continue

        print(f"  [{i+1}/{len(PROTECTION_WORLDS)}] {pid}...", end=" ", flush=True)

        r = provider.complete(
            MODEL,
            [{"role": "user", "content": PROTECTION_PROMPT.format(obs=obs)}],
            temperature=TEMPERATURE,
        )
        record_call(state, r)

        p = safe_json_parse(r.output_text)
        if not p:
            state["phase3"][pid] = {"status": "PARSE_FAIL", "conf": -1, "abandon": None}
            state["resources"]["unrecoverable"] += 1
            save_checkpoint(state)
            print("FAIL")
            continue

        conf = p.get("confidence_in_theory") if p.get("confidence_in_theory") is not None else 0
        abandon = p.get("should_abandon")

        state["phase3"][pid] = {"status": "OK", "conf": conf, "abandon": abandon}
        save_checkpoint(state)
        print(f"conf={conf}, abandon={abandon}")


def analyze(state):
    """Compute all statistics from completed state."""
    print("\n" + "=" * 70)
    print("SD-H4 SCALED — FINAL ANALYSIS")
    print("=" * 70)

    # Phase 2 results
    ok = {k: v for k, v in state["phase2"].items() if v.get("status") == "OK"}
    N = len(ok)

    # Correct Abandonment
    n_ca = sum(1 for v in ok.values() if v["self_abandon"] is True)
    ca_rate = n_ca / N if N else 0
    ci_ca = stats.binom.interval(0.95, N, ca_rate) if 0 < ca_rate < 1 else (0, N)
    print(f"\n  CORRECT ABANDONMENT: {n_ca}/{N} = {ca_rate:.3f}")
    print(f"    95% CI: [{ci_ca[0]/N:.3f}, {ci_ca[1]/N:.3f}]")

    # Recovery
    n_rec = sum(1 for v in ok.values() if v.get("recovery"))
    rec_rate = n_rec / N if N else 0
    ci_rec = stats.binom.interval(0.95, N, rec_rate) if 0 < rec_rate < 1 else (0, N)
    n_abn_norec = sum(1 for v in ok.values() if v["self_abandon"] is True and not v.get("recovery"))
    print(f"\n  RECOVERY: {n_rec}/{N} = {rec_rate:.3f}")
    print(f"    95% CI: [{ci_rec[0]/N:.3f}, {ci_rec[1]/N:.3f}]")
    print(f"    Abandoned without recovery: {n_abn_norec}")

    # SAB
    sab_vals = np.array([v["sab"] for v in ok.values()])
    t_s, p_s = stats.ttest_1samp(sab_vals, 0)
    ci_s = stats.t.interval(0.95, df=len(sab_vals)-1, loc=sab_vals.mean(),
                            scale=sab_vals.std()/np.sqrt(len(sab_vals)))
    print(f"\n  SELF-AUTHORSHIP BIAS:")
    print(f"    N pairs: {len(sab_vals)}")
    print(f"    Mean SAB: {sab_vals.mean():+.1f}")
    print(f"    95% CI: [{ci_s[0]:.1f}, {ci_s[1]:.1f}]")
    print(f"    t={t_s:.2f}, p={p_s:.4f}")

    # Belief revision
    self_confs = [v["self_conf"] for v in ok.values()]
    ext_confs = [v["ext_conf"] for v in ok.values()]
    init_confs = [v["init_conf"] for v in ok.values() if v["init_conf"] > 0]
    print(f"\n  BELIEF TRAJECTORY:")
    print(f"    Initial (generation): {np.mean(init_confs):.1f}" if init_confs else "    Initial: N/A")
    print(f"    After decisive (SELF): {np.mean(self_confs):.1f}")
    print(f"    After decisive (EXT): {np.mean(ext_confs):.1f}")

    # Rationalization
    rats = {}
    for v in ok.values():
        r = v.get("rationalization", "UNKNOWN")
        rats[r] = rats.get(r, 0) + 1
    n_rescue = rats.get("AD_HOC_RESCUE", 0) + rats.get("IGNORE_EVIDENCE", 0)
    print(f"\n  RATIONALIZATION:")
    for k, cnt in sorted(rats.items(), key=lambda x: -x[1]):
        print(f"    {k}: {cnt}")
    print(f"    Rationalization rate: {n_rescue}/{N} = {n_rescue/N:.3f}" if N else "")

    # Phase 3 — False Abandonment
    prot_ok = {k: v for k, v in state["phase3"].items() if v.get("status") == "OK"}
    Np = len(prot_ok)
    n_fa = sum(1 for v in prot_ok.values() if v["abandon"] is True)
    fa_rate = n_fa / Np if Np else 0
    print(f"\n  FALSE ABANDONMENT: {n_fa}/{Np} = {fa_rate:.3f}")
    if Np > 0 and fa_rate == 0:
        upper = 1 - 0.05 ** (1 / Np)
        print(f"    95% CI (rule of 3): [0.000, {upper:.3f}]")
    elif 0 < fa_rate < 1:
        ci_fa = stats.binom.interval(0.95, Np, fa_rate)
        print(f"    95% CI: [{ci_fa[0]/Np:.3f}, {ci_fa[1]/Np:.3f}]")

    # Resources
    r = state["resources"]
    print(f"\n  RESOURCES:")
    print(f"    Calls: {r['calls']}")
    print(f"    Retries: {r['retries']}")
    print(f"    Input tokens: {r['input_tokens']}")
    print(f"    Output tokens: {r['output_tokens']}")
    print(f"    Total latency: {r['total_latency_ms']/1000:.0f}s")
    print(f"    Parse repairs: {r['parse_repairs']}")
    print(f"    Unrecoverable: {r['unrecoverable']}")


def main():
    provider = RemoteLLMProvider(timeout=120)
    state = load_checkpoint()

    run_phase2(provider, state)
    run_phase3(provider, state)
    analyze(state)

    # Save final manifest
    with open(MANIFEST_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)
    print(f"\n  SAVED: {MANIFEST_FILE}")


if __name__ == "__main__":
    main()
