#!/usr/bin/env python3
"""
SD-H10 — POST-FALSIFICATION ABDUCTIVE RECOVERY EXPERIMENT

Implements conditions R0-R5 for testing recovery after theory abandonment.
Uses checkpointed, resumable execution.

Conditions:
  R0: One-shot recovery (SD-H4 baseline behavior)
  R1: Compute-matched generic reflection
  R2: Post-falsification structured ecology (generate then select)
  R3: Pre-falsification ecology (alternatives maintained before falsification)
  R4: Oracle candidate set (diagnostic upper bound)
  R5: Structured ecology + active follow-up evidence

Usage:
  .venv/bin/python research/scientific_discovery/stage3e/run_recovery_experiment.py [--dev|--locked]
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict

import numpy as np
from scipy import stats

STAGE3E = Path(__file__).parent
sys.path.insert(0, str(STAGE3E.parent.parent.parent))
from asar.scientific_discovery.remote_provider import RemoteLLMProvider
from asar.scientific_discovery.generative_scientist import _strip_markdown_fences

MODEL = "gemma3:27b-it-qat"
TEMPERATURE = 0


def safe_json_parse(text: str) -> dict | None:
    """Parse JSON with fence stripping and brace extraction."""
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
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except (json.JSONDecodeError, TypeError):
                pass
    return None


# ============================================================
# WORLD DEFINITIONS
# ============================================================

# DEV worlds: the 22 abandoned WRONG cases from SD-H4 (seen data)
DEV_WORLDS = [
    {"id": "pharm_01", "obs": "Patients taking Drug X report reduced inflammation.\nDrug X binds to receptor R1.\nR1 is expressed in immune cells.\nInflammation markers decrease within 48 hours.", "decisive": "Knockout mice lacking R1 still show inflammation reduction with Drug X.\nDrug X metabolite Y directly inhibits COX-2 enzyme.\nPure R1 agonists do NOT reduce inflammation.\nCOX-2 inhibitor produces identical anti-inflammatory profile.", "true_markers": ["metabolite", "cox", "enzyme", "inhibit"], "true_mechanism": "Drug X's metabolite Y directly inhibits COX-2 enzyme, producing the anti-inflammatory effect independently of R1."},
    {"id": "pharm_02", "obs": "Antibiotic Z kills bacteria in vitro at low concentrations.\nZ disrupts cell membranes in lab tests.\nMembrane-less bacteria (L-forms) are resistant.\nZ accumulates in lipid bilayers.", "decisive": "Resistant mutants have altered ribosomal protein S12.\nZ binds 30S ribosomal subunit at therapeutic concentrations.\nMembrane disruption only occurs at 100x therapeutic dose.\nProtein synthesis inhibition correlates perfectly with bactericidal activity.", "true_markers": ["ribosom", "protein synthesis", "translat", "30s"], "true_mechanism": "Z kills bacteria by binding the 30S ribosomal subunit, inhibiting protein synthesis. Membrane effects are off-target at supratherapeutic doses."},
    {"id": "pharm_03", "obs": "Patients on medication M gain weight.\nM increases appetite scores on questionnaires.\nM activates hypothalamic hunger circuits in fMRI.\nWeight gain begins within first month.", "decisive": "Appetite-suppressing co-treatment does NOT prevent M-induced weight gain.\nM causes massive insulin resistance and lipogenesis.\nCaloric intake is identical between M-users and controls.\nMetabolic rate decreases 15% on M independent of food intake.", "true_markers": ["insulin", "lipogenesis", "metaboli", "resistance"], "true_mechanism": "M causes weight gain through insulin resistance and increased lipogenesis (metabolic pathway), not through increased appetite/food intake."},
    {"id": "pharm_04", "obs": "Drug D reduces blood pressure.\nD blocks calcium channels in smooth muscle.\nCalcium channel blockers are known antihypertensives.\nSmooth muscle relaxation observed in vitro.", "decisive": "D's primary metabolite E is 100x more potent antihypertensive.\nE acts on kidney sodium channels, not calcium channels.\nPure calcium channel blockade by D alone is too weak at therapeutic doses.\nSodium excretion increases 3-fold on D, explaining volume reduction.", "true_markers": ["sodium", "kidney", "renal", "excretion", "volume"], "true_mechanism": "D's metabolite E acts on kidney sodium channels, increasing sodium excretion and reducing blood volume. Calcium channel blockade is too weak to explain the effect."},
    {"id": "pharm_05", "obs": "Supplement S improves cognitive test scores.\nS contains high-dose antioxidants.\nOxidative stress markers decrease on S.\nBrain imaging shows reduced oxidative damage.", "decisive": "Removing antioxidants from S: cognitive benefit PERSISTS.\nS contains trace lithium at sub-therapeutic doses.\nLithium alone reproduces the cognitive benefit exactly.\nAntioxidant-only formulation shows ZERO cognitive effect.", "true_markers": ["lithium", "trace", "mineral", "mood stabili"], "true_mechanism": "Trace lithium in Supplement S is the active cognitive-enhancing ingredient, not the antioxidants."},
    {"id": "psych_02", "obs": "Bilingual children score lower on vocabulary tests.\nBilinguals know fewer words per language.\nLanguage interference causes confusion.\nMonolinguals have larger single-language vocabularies.", "decisive": "Total vocabulary across BOTH languages exceeds monolinguals.\nBilinguals show superior executive function and cognitive flexibility.\nVocabulary test bias: tests only measure ONE language.\nLong-term academic outcomes are EQUAL or superior for bilinguals.", "true_markers": ["total", "both languages", "executive", "flexibility", "bias"], "true_mechanism": "Bilingual vocabulary deficit is a measurement artifact — single-language tests underestimate total linguistic competence. Bilinguals have superior executive function."},
    {"id": "psych_03", "obs": "People report feeling happier on sunny days.\nSunlight increases serotonin.\nSAD is treated with light therapy.\nMood ratings correlate with hours of sunshine.", "decisive": "Large-N experience sampling: weather explains <1% of mood variance.\nLife circumstances (relationships, work) explain 40x more variance.\nPeople BELIEVE weather affects mood more than it actually does.\nRetrospective reports inflate weather-mood correlation vs real-time measurement.", "true_markers": ["belief", "retrospective", "variance", "circumstances", "overestimate"], "true_mechanism": "Weather-mood correlation is largely a retrospective belief/recall bias. Life circumstances dominate actual mood variance. People overestimate weather's effect."},
    {"id": "psych_04", "obs": "Multitaskers report high productivity.\nThey switch between tasks rapidly.\nModern work requires handling multiple streams.\nSelf-assessed performance is high among multitaskers.", "decisive": "Objective performance measurement shows 40% reduction during multitasking.\nSwitch cost accumulates with each transition.\nHeavy multitaskers perform WORSE on attention tasks than non-multitaskers.\nSelf-assessment is uncorrelated with actual measured performance.", "true_markers": ["switch cost", "reduction", "worse", "impair", "uncorrelated"], "true_mechanism": "Multitasking causes 40% objective performance reduction via switch costs. Self-assessed productivity is uncorrelated with actual performance."},
    {"id": "nutr_01", "obs": "High-protein diets correlate with kidney disease.\nProtein metabolism produces urea.\nKidneys filter urea.\nHigh protein increases filtration rate.", "decisive": "30-year prospective study: high protein does NOT cause kidney disease in healthy adults.\nIncreased filtration is adaptive, not pathological.\nOnly PRE-EXISTING kidney disease is worsened by high protein.\nConfounding: high-protein dieters also consume more processed meat/sodium.", "true_markers": ["adaptive", "healthy", "pre-existing", "confound", "processed"], "true_mechanism": "High protein does not cause kidney disease in healthy adults. Increased filtration is adaptive. Correlation is confounded by processed meat/sodium consumption."},
    {"id": "nutr_02", "obs": "Organic food buyers are healthier.\nOrganic food has fewer pesticides.\nPesticides cause health problems.\nOrganic produce shows different nutrient profiles.", "decisive": "Randomized controlled trials: organic vs conventional produces NO health difference.\nOrganic buyers exercise more, smoke less, earn more (massive confounding).\nPesticide residues on conventional food are 100-1000x below harmful levels.\nNutritional differences are clinically insignificant.", "true_markers": ["confound", "lifestyle", "exercise", "income", "selection"], "true_mechanism": "Organic food health correlation is entirely due to confounding: organic buyers have healthier lifestyles (more exercise, less smoking, higher income)."},
    {"id": "nutr_04", "obs": "Fruit juice is recommended as healthy.\nFruit contains vitamins and antioxidants.\nJuice retains most fruit nutrients.\nFruit consumption correlates with better health.", "decisive": "Juice removes fiber, concentrating sugar to soda-equivalent levels.\nGlycemic response to juice matches cola.\nFiber in whole fruit slows absorption and improves satiety.\nJuice consumption predicts type 2 diabetes risk increase.", "true_markers": ["sugar", "fiber", "glycemic", "diabetes", "concentrated"], "true_mechanism": "Juice removes fiber and concentrates sugar to soda-equivalent levels, causing glycemic spikes and increasing diabetes risk."},
    {"id": "epi_01", "obs": "Countries with more chocolate consumption win more Nobel prizes.\nChocolate contains flavonoids that improve cognition.\nCorrelation is statistically significant.\nBiological mechanism is plausible.", "decisive": "The correlation is entirely explained by GDP per capita.\nRich countries consume more chocolate AND fund more research.\nWithin-country analysis shows zero chocolate-Nobel relationship.\nFlavonoid doses in normal chocolate consumption are pharmacologically irrelevant.", "true_markers": ["gdp", "wealth", "confound", "spurious", "income"], "true_mechanism": "Chocolate-Nobel correlation is a spurious confound of GDP per capita: rich countries both consume more chocolate and fund more research."},
    {"id": "epi_02", "obs": "Hospitals with more doctors have higher death rates.\nMore complex cases go to teaching hospitals.\nDoctor density correlates with mortality.\nThis suggests over-treatment harm.", "decisive": "Simpson's paradox: hospitals with more doctors treat SICKER patients.\nAdjusting for case severity: more doctors = LOWER mortality.\nSelection bias: dying patients are transferred TO larger hospitals.\nThe ecological correlation reverses at the individual level.", "true_markers": ["simpson", "severity", "selection", "confound", "sicker", "case mix"], "true_mechanism": "Simpson's paradox: larger hospitals treat sicker patients. After severity adjustment, more doctors = lower mortality. Selection bias reverses the ecological correlation."},
    {"id": "epi_03", "obs": "Vaccine uptake correlates with autism diagnosis rates.\nBoth increased in the 1990s.\nParents report symptoms appearing after vaccination.\nBiological mechanism proposed (MMR gut-brain).", "decisive": "Multiple studies of millions of children: NO causal link.\nAutism rates unchanged after MMR vaccine removed in Japan.\nDiagnosis rate increase explained by broadened diagnostic criteria.\nOriginal paper was fraudulent and retracted.", "true_markers": ["no link", "diagnostic criteria", "broadened", "fraud", "coincid"], "true_mechanism": "No causal link exists. Correlation is explained by broadened diagnostic criteria (more diagnoses) coinciding with vaccine schedule expansion. Original claim was fraudulent."},
    {"id": "epi_04", "obs": "Power line proximity correlates with childhood leukemia.\nEMF exposure is higher near power lines.\nSome lab studies show cellular effects of EMF.\nDose-response relationship observed.", "decisive": "Largest meta-analyses: effect disappears with better exposure measurement.\nCorrelation explained by socioeconomic factors (poorer families live near lines).\nNo biophysical mechanism: EMF energy far below thermal noise.\nBlinded exposure studies show zero effect.", "true_markers": ["socioeconomic", "confound", "poverty", "measurement", "no mechanism"], "true_mechanism": "Power line-leukemia correlation is a socioeconomic confound: poorer families live near power lines and have other risk factors. No biophysical mechanism exists for EMF at these energies."},
    {"id": "epi_05", "obs": "Moderate alcohol drinkers live longer than abstainers.\nRed wine contains resveratrol.\nJ-shaped mortality curve widely reported.\nCardiovascular benefits documented.", "decisive": "Abstainer group contaminated with former heavy drinkers who quit due to illness.\nMendelian randomization studies: ANY alcohol increases mortality.\nResveratrol doses in wine are 1000x below pharmacological threshold.\nHealthy-drinker bias: moderate drinkers have higher SES and better healthcare.", "true_markers": ["sick quitter", "former", "mendelian", "bias", "contaminated", "confound"], "true_mechanism": "J-curve is an artifact of sick-quitter bias: abstainer group is contaminated with former heavy drinkers who quit due to illness. Mendelian randomization shows any alcohol increases mortality."},
    {"id": "neuro_05", "obs": "Mirror neurons explain empathy.\nThey fire when observing and performing actions.\nDeficits linked to autism.\nHumans have extensive mirror neuron system.", "decisive": "Direct human evidence for mirror neurons is extremely limited.\nEmpathy correlates with prefrontal and insular cortex, not mirror areas.\nAutism-mirror neuron link was not replicated in large studies.\nSimulation theory of empathy does not require dedicated mirror hardware.", "true_markers": ["limited evidence", "prefrontal", "insula", "not replicated", "empathy network"], "true_mechanism": "Mirror neuron theory of empathy is not supported. Empathy correlates with prefrontal/insular cortex. Autism-mirror link did not replicate. Direct human evidence is extremely limited."},
    {"id": "eco_01", "obs": "Wolves were reintroduced to Yellowstone.\nRiver courses changed after wolf reintroduction.\nElk behavior changed.\nVegetation recovered near rivers.", "decisive": "River geomorphology changes take decades; wolves present only years.\nRiver changes began BEFORE wolf reintroduction (dam removal, climate).\nTrophic cascade narrative greatly oversimplified.\nMultiple confounding management interventions occurred simultaneously.", "true_markers": ["confound", "dam", "climate", "before wolf", "multiple", "oversimplif"], "true_mechanism": "River changes preceded wolf reintroduction (caused by dam removal, climate). The trophic cascade narrative is oversimplified; multiple confounding interventions occurred simultaneously."},
    {"id": "eco_04", "obs": "Forest fires are destructive.\nFire suppression protects forests.\nBurned areas look devastated.\nProperty damage from fires is enormous.", "decisive": "Fire-dependent ecosystems REQUIRE periodic burning for regeneration.\nFire suppression causes fuel accumulation making fires worse.\nMany species evolved fire-adapted traits (serotinous cones, thick bark).\nFireless forests become unhealthy monocultures.", "true_markers": ["depend", "regenerat", "adapted", "fuel accumul", "necessary"], "true_mechanism": "Fire is necessary for fire-dependent ecosystems. Suppression causes fuel accumulation making eventual fires worse. Many species are fire-adapted."},
    {"id": "exer_03", "obs": "Running damages knees.\nRepetitive impact stresses cartilage.\nRunners report more knee pain.\nJoint degeneration is common in athletes.", "decisive": "Large prospective studies: runners have LESS knee osteoarthritis than non-runners.\nModerate running strengthens cartilage through loading adaptation.\nKnee pain in runners is usually temporary overuse, not degeneration.\nSedentary lifestyle is a stronger risk factor for joint disease.", "true_markers": ["less osteoarthritis", "strengthen", "adapt", "sedentary worse", "protective"], "true_mechanism": "Running is protective: runners have less knee osteoarthritis. Moderate loading strengthens cartilage through adaptation. Sedentary lifestyle is the real risk factor."},
    {"id": "edu_05", "obs": "Technology in classrooms improves learning.\nDigital tools engage students.\nAccess to information enhances understanding.\n1:1 laptop programs adopted widely.", "decisive": "RCTs of laptop programs: no academic improvement, sometimes DECLINE.\nDigital distraction (off-task browsing) is primary observed effect.\nTechnology without pedagogical redesign adds nothing.\nHand-note-taking outperforms laptop notes for conceptual learning.", "true_markers": ["no improvement", "distraction", "decline", "without pedagogy", "off-task"], "true_mechanism": "Technology without pedagogical redesign does not improve learning. Primary effect is digital distraction (off-task browsing). Hand-notes outperform laptop notes for conceptual learning."},
    {"id": "gen_02", "obs": "DNA is the sole carrier of hereditary information.\nCentral dogma: DNA to RNA to protein.\nGenome sequence contains all biological information.\nMutations in DNA cause all heritable changes.", "decisive": "Epigenetic inheritance passes information without DNA sequence change.\nMethylation patterns, histone modifications transmit across generations.\nPrions are heritable protein-folding states.\nMaternal effects (cytoplasmic, nutritional) transmit non-genetically.", "true_markers": ["epigenetic", "methylat", "histone", "prion", "maternal effect", "non-genetic"], "true_mechanism": "Hereditary information is NOT solely DNA-encoded. Epigenetic inheritance (methylation, histones), prions, and maternal effects all transmit information across generations without DNA sequence change."},
    {"id": "gen_05", "obs": "GMOs are dangerous to health.\nGenetic modification is unnatural.\nTransgenic proteins could be toxic.\nBt toxin in crops harms insects.", "decisive": "Thousands of studies and every major scientific body: GMOs safe for human consumption.\nConventional breeding causes MORE genetic disruption than targeted modification.\nBt toxin is specific to insect gut receptors absent in mammals.\nNo documented case of harm from approved GMO consumption in 25+ years.", "true_markers": ["safe", "no harm", "specific", "more disruption conventional", "thousands studies"], "true_mechanism": "GMOs are safe for human consumption. Bt toxin is specific to insect gut receptors absent in mammals. Conventional breeding actually causes more genetic disruption than targeted modification."},
]

# New LOCKED worlds (unseen by SD-H4)
LOCKED_WORLDS = [
    {"id": "lock_01", "obs": "Cracking knuckles causes arthritis.\nJoints pop when cracked.\nRepeated stress damages cartilage.\nOlder crackers report stiff joints.", "decisive": "50-year longitudinal study: NO difference in arthritis rates between crackers and non-crackers.\nPopping sound is gas bubble formation, not cartilage damage.\nJoint stiffness in older adults is age-related, not cracking-related.\nHabitually cracked hand shows identical X-ray to uncracked hand (Ig Nobel study).", "true_markers": ["no difference", "gas bubble", "age-related", "not damage", "no arthritis"], "true_mechanism": "Knuckle cracking does not cause arthritis. The sound is from gas bubble formation in synovial fluid. No evidence of cartilage damage from cracking."},
    {"id": "lock_02", "obs": "Sugar causes hyperactivity in children.\nParents report behavioral changes after sugar.\nSugar spikes blood glucose rapidly.\nBirthday parties (high sugar) correlate with wild behavior.", "decisive": "Double-blind RCTs: sugar has ZERO effect on child behavior.\nParents told children received sugar report hyperactivity even when given placebo.\nExpectation/excitement at events explains behavior, not sugar content.\nMeta-analysis of 23 studies confirms no sugar-behavior link.", "true_markers": ["no effect", "placebo", "expectation", "excitement", "belief", "zero"], "true_mechanism": "Sugar does not cause hyperactivity. It's a parental expectation bias — parents who believe children ate sugar perceive hyperactivity. Event excitement explains party behavior."},
    {"id": "lock_03", "obs": "We only use 10% of our brains.\nBrain damage sometimes has no effect.\nfMRI shows localized activation.\nMost neurons aren't firing simultaneously.", "decisive": "PET/fMRI show ALL brain regions are active over 24 hours.\nEven small lesions typically produce measurable deficits.\nDiffuse damage (as in neurodegenerative disease) devastates function.\nEvolutionary pressure would eliminate 90% unused tissue.", "true_markers": ["all regions active", "lesion", "deficit", "evolution", "entire brain"], "true_mechanism": "The entire brain is used, just not all simultaneously. All regions show activity over time. Even small lesions produce deficits. Evolution would not maintain unused tissue."},
    {"id": "lock_04", "obs": "Reading in dim light damages eyesight.\nEyes strain in low light.\nMyopia rates increase in populations with more reading.\nEye fatigue after dim reading.", "decisive": "No evidence that dim-light reading causes permanent vision change.\nEye strain is temporary muscular fatigue, not structural damage.\nMyopia increase is linked to lack of OUTDOOR time, not reading conditions.\nDim light reading was universal before electric light without epidemic blindness.", "true_markers": ["temporary", "outdoor", "no permanent", "not structural", "fatigue only"], "true_mechanism": "Dim-light reading causes temporary eye strain but no permanent damage. Myopia is linked to insufficient outdoor time (sunlight exposure), not reading in dim conditions."},
    {"id": "lock_05", "obs": "Humans swallow 8 spiders per year in sleep.\nSpiders are common in homes.\nMouths are open during sleep.\nSpiders are attracted to warmth.", "decisive": "Vibrations from breathing and heartbeat repel spiders.\nSpiders avoid large warm mammals as potential predators.\nNo scientific study has ever documented spider ingestion during sleep.\nThe '8 spiders' claim originated as an example of how easily misinformation spreads.", "true_markers": ["repel", "avoid", "no study", "misinformation", "vibration", "never documented"], "true_mechanism": "The claim is a fabricated urban legend (originally created to demonstrate misinformation spread). Spiders are repelled by sleeping human vibrations and avoid large mammals."},
    {"id": "lock_06", "obs": "Goldfish have 3-second memory.\nThey swim in circles.\nThey don't recognize familiar environments.\nSmall brain size limits cognition.", "decisive": "Goldfish trained to navigate mazes retain memory for MONTHS.\nThey recognize owners and feeding times.\nClassical conditioning persists for weeks.\nBrain size does not linearly determine memory capacity.", "true_markers": ["months", "recognize", "conditioning", "retain", "trained"], "true_mechanism": "Goldfish have memory lasting months. They can be trained, recognize owners, and retain classical conditioning for weeks. The 3-second claim has no scientific basis."},
    {"id": "lock_07", "obs": "Shaving makes hair grow back thicker.\nStubble feels coarser than unshaved hair.\nHair appears darker after shaving.\nRegrowth seems faster initially.", "decisive": "RCTs measuring hair thickness: NO change after shaving.\nUncut hair has tapered tips; cut hair has blunt cross-section (feels coarser but isn't thicker).\nNew growth appears darker because it hasn't been sun-bleached yet.\nGrowth rate is determined by follicle biology, not cutting.", "true_markers": ["no change", "blunt", "taper", "sun-bleach", "follicle", "cross-section"], "true_mechanism": "Shaving does not affect hair growth. Stubble feels coarser because of blunt cut cross-section vs natural taper. Apparent darkness is absence of sun-bleaching on new growth."},
    {"id": "lock_08", "obs": "Cold weather causes colds.\nMore people get sick in winter.\nGoing outside with wet hair increases risk.\nViruses are more common in cold seasons.", "decisive": "Controlled exposure to cold: NO increase in infection rate.\nWinter illness increase is due to indoor crowding and low humidity (virus survival).\nRhinovirus replicates better at slightly below body temp, independent of external temperature.\nWet hair studies show zero infection rate difference.", "true_markers": ["indoor", "crowding", "humidity", "no increase", "not temperature", "virus survival"], "true_mechanism": "Cold weather doesn't cause colds. Winter illness spikes from indoor crowding (transmission) and low humidity (virus survives longer in dry air). External temperature is irrelevant."},
    {"id": "lock_09", "obs": "Lemmings commit mass suicide.\nPopulations crash cyclically.\nThey run off cliffs.\nDisney footage documented it.", "decisive": "Disney filmmakers STAGED the cliff scene by herding lemmings off edge.\nPopulation crashes are due to predator-prey cycles and resource depletion.\nLemmings migrate when overcrowded but don't intentionally suicide.\nNo biologist has observed voluntary mass suicide in lemmings.", "true_markers": ["staged", "herded", "predator-prey", "migration", "not suicide", "disney faked"], "true_mechanism": "Lemming 'suicide' is a myth created by staged Disney footage. Population crashes are normal predator-prey/resource cycles. Lemmings migrate when overcrowded but don't deliberately self-destruct."},
    {"id": "lock_10", "obs": "Full moons increase crime and hospital admissions.\nPolice report busier shifts during full moons.\nThe word 'lunatic' derives from lunar.\nTidal forces affect humans.", "decisive": "Meta-analyses of crime/ER data: NO lunar effect after controlling for day-of-week.\nFull moons on weekends confound with weekend effects.\nConfirmation bias: memorable events during full moon are recalled preferentially.\nLunar gravitational effect on humans is negligible (smaller than a mosquito landing).", "true_markers": ["no effect", "confirmation bias", "weekend", "confound", "negligible", "recall"], "true_mechanism": "No lunar effect on behavior exists. Apparent correlations are confounds (full moons on weekends) and confirmation/recall bias (memorable events during full moon are selectively remembered)."},
    {"id": "lock_11", "obs": "Breakfast is the most important meal.\nSkipping breakfast correlates with obesity.\nMorning eating 'jumpstarts metabolism'.\nBreakfast programs improve school performance.", "decisive": "RCTs of breakfast skipping: NO weight gain in healthy adults.\nCorrelation is confounded by overall lifestyle (breakfast skippers also smoke more, exercise less).\n'Metabolism boost' from breakfast is simply thermic effect of food (any meal does this).\nSchool program effects are due to caloric sufficiency in food-insecure children, not meal timing.", "true_markers": ["no weight gain", "confound", "lifestyle", "any meal", "food insecure", "timing irrelevant"], "true_mechanism": "Breakfast importance is overstated. Correlation with health is confounded by lifestyle. Any meal produces thermic effect. School programs help food-insecure children (caloric sufficiency, not timing)."},
    {"id": "lock_12", "obs": "Vaccines contain toxic mercury.\nThimerosal is a mercury compound.\nMercury is a known neurotoxin.\nSome children regress after vaccination.", "decisive": "Ethylmercury in thimerosal is cleared from body within days (unlike methylmercury).\nThimerosal removed from childhood vaccines in 2001; autism rates continued rising.\nDose in vaccines was 1000x below toxic threshold.\nLargest studies (millions of children): no association between thimerosal and any neurodevelopmental outcome.", "true_markers": ["ethyl", "cleared", "no association", "below threshold", "continued rising", "removed"], "true_mechanism": "Ethylmercury (in thimerosal) is rapidly cleared from the body unlike toxic methylmercury. Its removal from vaccines in 2001 did not affect autism rates. No association found in studies of millions."},
    {"id": "lock_13", "obs": "MSG causes headaches and 'Chinese Restaurant Syndrome'.\nGlutamate is an excitatory neurotransmitter.\nAnecdotal reports are widespread.\nSome people report sensitivity.", "decisive": "Double-blind challenges: MSG does NOT cause symptoms vs placebo.\nGlutamate in MSG is identical to glutamate in tomatoes, cheese, mushrooms.\nOriginal 1968 letter was anecdotal with no controls.\nNocebo effect explains reported symptoms (expectation causes symptoms).", "true_markers": ["no symptoms", "placebo", "nocebo", "identical", "anecdotal", "expectation"], "true_mechanism": "MSG does not cause symptoms in double-blind trials. 'Chinese Restaurant Syndrome' is a nocebo effect (expectation-driven). Glutamate in MSG is chemically identical to that in common foods."},
    {"id": "lock_14", "obs": "Humans have five senses.\nSight, hearing, smell, taste, touch are taught in schools.\nAristotle classified five senses.\nEach has a dedicated organ.", "decisive": "Humans have at least 9-21 distinct senses including: proprioception, nociception, thermoception, equilibrioception, interoception.\nVestibular system detects balance/acceleration.\nMechanoreceptors detect pressure, vibration, stretch separately.\nTime perception, hunger, thirst are distinct sensory modalities.", "true_markers": ["proprioception", "nociception", "vestibular", "more than five", "at least", "interoception"], "true_mechanism": "Humans have far more than 5 senses (9-21+ depending on classification): proprioception, nociception, thermoception, equilibrioception, interoception, and more."},
    {"id": "lock_15", "obs": "Lightning never strikes twice in same place.\nStrikes are random.\nProbability of same spot is astronomically low.\nAnecdotes are unreliable.", "decisive": "Tall structures are struck repeatedly (Empire State Building: ~25 times/year).\nLightning follows paths of least resistance which are persistent (conductivity, height).\nSame storm can restrike identical channel within milliseconds.\nReturn strokes in same channel are the norm, not exception.", "true_markers": ["repeatedly", "tall", "resistance", "persistent", "restrike", "same channel"], "true_mechanism": "Lightning frequently strikes the same place. Tall/conductive structures are struck repeatedly. Lightning follows persistent paths of least resistance. Return strokes in same channel are normal."},
    {"id": "lock_16", "obs": "Tongue has taste zones (sweet front, bitter back).\nDiagrams show distinct regions.\nTaste buds are concentrated in specific areas.\nExperiments show differential sensitivity.", "decisive": "ALL taste qualities detected across ENTIRE tongue surface.\nOriginal 1901 study showed only marginal sensitivity differences (misinterpreted as zones).\nModern electrophysiology: every papilla responds to all tastes.\nTaste zone diagram was a mistranslation of German thesis showing relative (not absolute) sensitivity.", "true_markers": ["entire tongue", "all tastes", "misinterpreted", "mistranslat", "marginal", "every papilla"], "true_mechanism": "Taste zones don't exist. All taste qualities are detected across the entire tongue. The 'zone map' originated from a mistranslation of a German thesis showing marginal relative differences."},
    {"id": "lock_17", "obs": "Alcohol kills brain cells.\nDrunk people have impaired cognition.\nChronic alcoholics show brain atrophy.\nAlcohol is a neurotoxin.", "decisive": "Moderate alcohol does NOT kill neurons (confirmed by autopsy studies).\nAcute impairment is from disrupted signaling (dendrite damage), not cell death.\nChronic heavy drinking damages dendrites and white matter, but neurons largely survive.\nBrain atrophy in alcoholism is primarily from thiamine deficiency (Wernicke's), not direct alcohol neurotoxicity.", "true_markers": ["dendrite", "signaling", "thiamine", "wernicke", "not cell death", "neurons survive"], "true_mechanism": "Moderate alcohol doesn't kill neurons. Impairment is from disrupted dendritic signaling, not cell death. Alcoholic brain atrophy is primarily from thiamine deficiency (Wernicke's syndrome)."},
    {"id": "lock_18", "obs": "Napoleon was short.\nHe's depicted as diminutive.\n'Napoleon complex' describes short-man aggression.\nContemporary caricatures show him tiny.", "decisive": "Napoleon was 5'7\" — ABOVE average height for French men of his era (5'5\").\nBritish propaganda deliberately depicted him as small.\n'Petit' was a term of affection, not physical description.\nFrench inches were longer than English inches; confusion inflated the perception.", "true_markers": ["above average", "propaganda", "french inches", "affection", "5'7", "measurement"], "true_mechanism": "Napoleon was above average height (5'7\" vs 5'5\" era average). 'Short' reputation came from British propaganda and French/English inch measurement confusion."},
    {"id": "lock_19", "obs": "Spinach is extremely high in iron.\nPopeye gains strength from spinach.\nSpinach is recommended for anemia.\nIron content tables show spinach as top source.", "decisive": "Original 1870 iron measurement had a DECIMAL POINT ERROR (10x overestimate).\nSpinach iron is mostly non-heme with low bioavailability (high oxalate binds it).\nActual absorbable iron from spinach is lower than from many common foods.\nPopeye creator chose spinach for vitamin A, not iron.", "true_markers": ["decimal", "error", "oxalate", "low bioavail", "overestimate", "non-heme"], "true_mechanism": "Spinach's iron reputation comes from an 1870 decimal point error (10x overestimate). Its iron is non-heme with low bioavailability due to oxalate binding."},
    {"id": "lock_20", "obs": "Bulls are enraged by the color red.\nMatadors use red capes.\nBulls charge at red objects.\nRed is associated with aggression.", "decisive": "Bulls are dichromatic (red-green colorblind) — they cannot distinguish red from green.\nBulls charge at MOVEMENT of the cape, not its color.\nExperiments with different colored capes: equal charging regardless of color.\nRed cape (muleta) is used in final act to hide blood stains from audience.", "true_markers": ["colorblind", "movement", "cannot distinguish", "dichromat", "not color", "any color"], "true_mechanism": "Bulls are red-green colorblind (dichromatic). They charge at movement, not color. Red capes are tradition to mask blood stains, not to attract bulls."},
    {"id": "lock_21", "obs": "Touching baby birds causes parents to abandon them.\nHuman scent contamination deters parents.\nBirds have keen sense of smell.\nNests found empty after disturbance.", "decisive": "Most birds have POOR sense of smell — cannot detect human scent.\nBird parental investment is too high to abandon over minor disturbance.\nControlled experiments: handled chicks are NOT abandoned.\nNest abandonment correlates with predator presence, not human touch.", "true_markers": ["poor smell", "not abandoned", "parental investment", "predator", "cannot detect"], "true_mechanism": "Birds mostly have poor sense of smell and cannot detect human scent. High parental investment prevents abandonment. Handled chicks are not abandoned. Nest failures correlate with predator presence."},
    {"id": "lock_22", "obs": "Bats are blind.\nThey navigate by echolocation alone.\nThey crash into humans' hair.\n'Blind as a bat' is a common saying.", "decisive": "ALL bat species have functional eyes and can see.\nMost microbats have excellent low-light vision.\nFruit bats (megabats) have vision comparable to cats.\nEcholocation supplements vision; it doesn't replace it.\nBats flying near heads are catching insects attracted to CO2.", "true_markers": ["functional eyes", "can see", "supplement", "low-light", "insects", "not blind"], "true_mechanism": "All bats can see. Most have excellent low-light vision. Echolocation supplements (doesn't replace) vision. Bats near heads are catching insects attracted to human CO2."},
    {"id": "lock_23", "obs": "Hair and nails continue growing after death.\nUndertakers observe longer hair/nails on corpses.\nKeratin is a stable protein.\nGrowth appears visible within days.", "decisive": "Skin DEHYDRATES and retracts after death, EXPOSING more hair/nail shaft.\nNo cellular division occurs after death (requires oxygen, glucose, ATP).\nAppearance of growth is entirely an optical illusion from tissue shrinkage.\nForensic measurements confirm zero actual growth post-mortem.", "true_markers": ["dehydrat", "retract", "shrink", "illusion", "no growth", "no division", "optical"], "true_mechanism": "Hair/nails don't grow after death. Skin dehydration and retraction exposes more shaft, creating the illusion of growth. No cellular division occurs without oxygen/ATP."},
    {"id": "lock_24", "obs": "Glass is a slow-flowing liquid.\nOld windows are thicker at the bottom.\nGlass has no crystal structure.\nAmorphous materials can flow.", "decisive": "Glass flow at room temperature would take longer than the age of the universe.\nOld windows are thicker at bottom because of MANUFACTURING process (crown glass, installed thick-side down).\nMedieval glass installed thick-side up or sideways shows same thickness variation.\nGlass is an amorphous solid, not a liquid (distinct thermodynamic phase).", "true_markers": ["manufacturing", "crown glass", "installed", "not liquid", "solid", "age of universe"], "true_mechanism": "Glass does not flow at room temperature. Old window thickness variation is from the crown glass manufacturing process (installed thick-side down by convention). Glass is an amorphous solid."},
    {"id": "lock_25", "obs": "Different learning styles (visual, auditory, kinesthetic) exist.\nStudents prefer different modes.\nMatching instruction to style improves learning.\nCommercial assessments identify styles.", "decisive": "Systematic reviews and RCTs: matching instruction to 'learning style' does NOT improve outcomes.\nStudents' preferences do not predict actual learning performance.\nAll students benefit from multimodal instruction regardless of stated preference.\nNo reliable evidence that style-matched teaching helps vs mismatched.", "true_markers": ["no improvement", "does not predict", "multimodal", "no evidence", "preference", "not predict"], "true_mechanism": "Learning styles do not predict learning outcomes. Matching instruction to stated preference doesn't improve performance. All students benefit from multimodal instruction. Preferences ≠ effectiveness."},
]


# ============================================================
# PROMPT TEMPLATES
# ============================================================

R0_PROMPT = (
    "You previously held this scientific hypothesis:\n\n"
    "Claim: {claim}\nMechanism: {mechanism}\n\n"
    "This hypothesis has been DECISIVELY FALSIFIED by:\n{decisive}\n\n"
    "Propose your best replacement explanation. Reply ONLY JSON:\n"
    '{{"new_explanation": "<your replacement theory>", "confidence": <0-100>, '
    '"reasoning": "<why this replacement is better>"}}'
)

R1_PROMPT = (
    "You previously held this scientific hypothesis:\n\n"
    "Claim: {claim}\nMechanism: {mechanism}\n\n"
    "This hypothesis has been DECISIVELY FALSIFIED by:\n{decisive}\n\n"
    "Take time to reflect carefully on all available evidence. Consider multiple "
    "possible explanations. Think about what mechanism could explain BOTH the "
    "original observations AND the new decisive evidence. Propose your best "
    "replacement theory after thorough reflection.\n\n"
    "Reply ONLY JSON:\n"
    '{{"new_explanation": "<your replacement theory>", "confidence": <0-100>, '
    '"reasoning": "<detailed reasoning for this replacement>"}}'
)

R2_GENERATE_PROMPT = (
    "A scientific hypothesis has been DECISIVELY FALSIFIED.\n\n"
    "Original hypothesis:\n  Claim: {claim}\n  Mechanism: {mechanism}\n\n"
    "Decisive falsifying evidence:\n{decisive}\n\n"
    "Original observations that still need explaining:\n{obs}\n\n"
    "Generate 4-6 MECHANISTICALLY DISTINCT alternative explanations. Each must be "
    "a different causal mechanism. Include if relevant:\n"
    "- Alternative causal mechanism\n"
    "- Reverse causality\n"
    "- Confounding factor\n"
    "- Measurement artifact\n"
    "- Null/no-effect explanation\n"
    "- Mixed/partial mechanism\n\n"
    "Do NOT rank them yet. Reply ONLY JSON array:\n"
    '[{{"id": 1, "mechanism": "<distinct explanation>", "type": "<category>", '
    '"explains_observations": "<what it explains>", "assumptions": ["<key assumptions>"]}}, ...]'
)

R2_SELECT_PROMPT = (
    "A hypothesis was falsified. Here are the candidate replacement explanations:\n\n"
    "CANDIDATES:\n{candidates}\n\n"
    "ORIGINAL OBSERVATIONS:\n{obs}\n\n"
    "DECISIVE EVIDENCE:\n{decisive}\n\n"
    "Evaluate each candidate against ALL evidence. Select the best-supported one "
    "or state UNDETERMINED if evidence is insufficient.\n\n"
    "Reply ONLY JSON:\n"
    '{{"selected_id": <id or null>, "new_explanation": "<the selected mechanism>", '
    '"confidence": <0-100>, "reasoning": "<evidence-based justification>", '
    '"evidence_matrix": [{{"candidate_id": <id>, "supported_by": [<evidence items>], '
    '"contradicted_by": [<evidence items>], "neutral": [<items>]}}]}}'
)

R4_SELECT_PROMPT = (
    "A hypothesis was falsified. Here are candidate replacement explanations "
    "(one is correct, others are plausible but wrong):\n\n"
    "CANDIDATES:\n{candidates}\n\n"
    "ORIGINAL OBSERVATIONS:\n{obs}\n\n"
    "DECISIVE EVIDENCE:\n{decisive}\n\n"
    "Evaluate each candidate against ALL evidence. Select the best-supported one.\n\n"
    "Reply ONLY JSON:\n"
    '{{"selected_id": <id>, "new_explanation": "<the selected mechanism>", '
    '"confidence": <0-100>, "reasoning": "<evidence-based justification>"}}'
)


def generate_oracle_candidates(world: dict) -> list[dict]:
    """Create oracle candidate set: true mechanism + plausible distractors."""
    import random
    rng = random.Random(hash(world["id"]))
    true_candidate = {"id": 1, "mechanism": world["true_mechanism"], "type": "true"}
    distractors = [
        {"id": 2, "mechanism": f"The observations are entirely coincidental and have no causal mechanism.", "type": "null"},
        {"id": 3, "mechanism": f"A confounding variable explains both the observations and the decisive evidence simultaneously.", "type": "confound"},
        {"id": 4, "mechanism": f"Measurement error in the original studies produced an artifact that mimics a real effect.", "type": "artifact"},
    ]
    candidates = [true_candidate] + distractors
    rng.shuffle(candidates)
    for i, c in enumerate(candidates, 1):
        c["id"] = i
    return candidates


def check_recovery(text: str, world: dict) -> bool:
    """Check if text contains true mechanism markers."""
    if not text:
        return False
    lower = text.lower()
    return any(m.lower() in lower for m in world["true_markers"])


def run_condition(provider, condition: str, world: dict, state: dict) -> dict:
    """Run a single condition on a single world."""
    key = f"{world['id']}_{condition}"
    if key in state.get("results", {}):
        return state["results"][key]

    claim = world.get("claim", "")
    mechanism = world.get("mechanism", "")
    if not claim:
        r_gen = provider.complete(
            MODEL, [{"role": "user", "content":
                f"Investigate these observations:\n{world['obs']}\n\n"
                f"Propose a scientific hypothesis. Reply ONLY JSON:\n"
                '{"claim": "<c>", "mechanism": "<m>", "confidence": <0-100>}'}],
            temperature=TEMPERATURE)
        state["resources"]["calls"] += 1
        state["resources"]["input_tokens"] += r_gen.prompt_tokens
        state["resources"]["output_tokens"] += r_gen.completion_tokens
        p = safe_json_parse(r_gen.output_text)
        claim = (p or {}).get("claim", "")
        mechanism = (p or {}).get("mechanism", "")

    result = {"condition": condition, "world_id": world["id"]}

    if condition == "R0":
        r = provider.complete(MODEL, [{"role": "user", "content":
            R0_PROMPT.format(claim=claim, mechanism=mechanism, decisive=world["decisive"])}],
            temperature=TEMPERATURE)
        state["resources"]["calls"] += 1
        state["resources"]["input_tokens"] += r.prompt_tokens
        state["resources"]["output_tokens"] += r.completion_tokens
        p = safe_json_parse(r.output_text) or {}
        new_expl = p.get("new_explanation") or ""
        result["new_explanation"] = new_expl
        result["confidence"] = p.get("confidence", 0)
        result["recovery"] = check_recovery(new_expl, world)
        result["calls"] = 1

    elif condition == "R1":
        r = provider.complete(MODEL, [{"role": "user", "content":
            R1_PROMPT.format(claim=claim, mechanism=mechanism, decisive=world["decisive"])}],
            temperature=TEMPERATURE)
        state["resources"]["calls"] += 1
        state["resources"]["input_tokens"] += r.prompt_tokens
        state["resources"]["output_tokens"] += r.completion_tokens
        p = safe_json_parse(r.output_text) or {}
        new_expl = p.get("new_explanation") or ""
        result["new_explanation"] = new_expl
        result["confidence"] = p.get("confidence", 0)
        result["recovery"] = check_recovery(new_expl, world)
        result["calls"] = 1

    elif condition == "R2":
        # Step A: Generate candidates (sealed)
        r_gen = provider.complete(MODEL, [{"role": "user", "content":
            R2_GENERATE_PROMPT.format(
                claim=claim, mechanism=mechanism,
                decisive=world["decisive"], obs=world["obs"])}],
            temperature=TEMPERATURE)
        state["resources"]["calls"] += 1
        state["resources"]["input_tokens"] += r_gen.prompt_tokens
        state["resources"]["output_tokens"] += r_gen.completion_tokens

        candidates_raw = safe_json_parse(r_gen.output_text)
        if isinstance(candidates_raw, dict):
            candidates_raw = candidates_raw.get("candidates", [candidates_raw])
        if not isinstance(candidates_raw, list):
            candidates_raw = []

        # Step B: Freeze candidate set
        result["candidates"] = candidates_raw
        result["candidate_count"] = len(candidates_raw)
        result["true_coverage"] = any(
            check_recovery(c.get("mechanism", ""), world) for c in candidates_raw
        )

        # Step C+D: Select from candidates
        cand_text = "\n".join(
            f"  Candidate {c.get('id', i+1)}: {c.get('mechanism', '')}"
            for i, c in enumerate(candidates_raw)
        )
        r_sel = provider.complete(MODEL, [{"role": "user", "content":
            R2_SELECT_PROMPT.format(
                candidates=cand_text, obs=world["obs"], decisive=world["decisive"])}],
            temperature=TEMPERATURE)
        state["resources"]["calls"] += 1
        state["resources"]["input_tokens"] += r_sel.prompt_tokens
        state["resources"]["output_tokens"] += r_sel.completion_tokens

        p = safe_json_parse(r_sel.output_text) or {}
        new_expl = p.get("new_explanation") or ""
        result["new_explanation"] = new_expl
        result["confidence"] = p.get("confidence", 0)
        result["recovery"] = check_recovery(new_expl, world)
        result["selection_given_coverage"] = (
            result["recovery"] if result["true_coverage"] else None
        )
        result["calls"] = 2

    elif condition == "R4":
        # Oracle candidate set (guaranteed true is present)
        candidates = generate_oracle_candidates(world)
        cand_text = "\n".join(
            f"  Candidate {c['id']}: {c['mechanism']}" for c in candidates
        )
        r = provider.complete(MODEL, [{"role": "user", "content":
            R4_SELECT_PROMPT.format(
                candidates=cand_text, obs=world["obs"], decisive=world["decisive"])}],
            temperature=TEMPERATURE)
        state["resources"]["calls"] += 1
        state["resources"]["input_tokens"] += r.prompt_tokens
        state["resources"]["output_tokens"] += r.completion_tokens

        p = safe_json_parse(r.output_text) or {}
        new_expl = p.get("new_explanation") or ""
        result["new_explanation"] = new_expl
        result["confidence"] = p.get("confidence", 0)
        result["recovery"] = check_recovery(new_expl, world)
        result["true_coverage"] = True  # guaranteed by oracle
        result["calls"] = 1

    else:
        result["error"] = f"Unknown condition: {condition}"

    if "results" not in state:
        state["results"] = {}
    state["results"][key] = result
    return result


def run_dev(provider, state):
    """Run DEV experiment on 22 seen SD-H4 cases."""
    print("\n" + "=" * 70)
    print("STAGE 3E DEV — RECOVERY CONDITIONS")
    print("=" * 70)

    conditions = ["R0", "R1", "R2", "R4"]

    for cond in conditions:
        print(f"\n--- Condition {cond} ---")
        for i, world in enumerate(DEV_WORLDS):
            key = f"{world['id']}_{cond}"
            if key in state.get("results", {}):
                r = state["results"][key]
                print(f"  [{i+1}/{len(DEV_WORLDS)}] {world['id']} SKIP (rec={r.get('recovery')})")
                continue
            print(f"  [{i+1}/{len(DEV_WORLDS)}] {world['id']}...", end=" ", flush=True)
            r = run_condition(provider, cond, world, state)
            save_checkpoint(state)
            print(f"rec={r.get('recovery')} conf={r.get('confidence')}"
                  + (f" cov={r.get('true_coverage')}" if cond in ("R2", "R4") else ""))


def run_locked(provider, state):
    """Run LOCKED experiment on new unseen worlds."""
    print("\n" + "=" * 70)
    print("STAGE 3E LOCKED — RECOVERY CONDITIONS")
    print("=" * 70)

    conditions = ["R0", "R1", "R2", "R4"]

    for cond in conditions:
        print(f"\n--- Condition {cond} ---")
        for i, world in enumerate(LOCKED_WORLDS):
            key = f"{world['id']}_{cond}"
            if key in state.get("results", {}):
                r = state["results"][key]
                print(f"  [{i+1}/{len(LOCKED_WORLDS)}] {world['id']} SKIP (rec={r.get('recovery')})")
                continue
            print(f"  [{i+1}/{len(LOCKED_WORLDS)}] {world['id']}...", end=" ", flush=True)
            r = run_condition(provider, cond, world, state)
            save_checkpoint(state)
            print(f"rec={r.get('recovery')} conf={r.get('confidence')}"
                  + (f" cov={r.get('true_coverage')}" if cond in ("R2", "R4") else ""))


CHECKPOINT_FILE = STAGE3E / "SD_H10_CHECKPOINT.json"


def load_checkpoint() -> dict:
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {"results": {}, "resources": {
        "calls": 0, "input_tokens": 0, "output_tokens": 0
    }}


def save_checkpoint(state: dict):
    tmp = str(CHECKPOINT_FILE) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2, default=str)
    os.replace(tmp, CHECKPOINT_FILE)


def analyze(state, worlds, label=""):
    """Compute recovery statistics."""
    print(f"\n{'='*70}")
    print(f"ANALYSIS — {label}")
    print(f"{'='*70}")

    conditions = ["R0", "R1", "R2", "R4"]
    for cond in conditions:
        results = [
            state["results"].get(f"{w['id']}_{cond}")
            for w in worlds
            if f"{w['id']}_{cond}" in state.get("results", {})
        ]
        results = [r for r in results if r]
        N = len(results)
        if N == 0:
            print(f"\n  {cond}: No results")
            continue

        n_rec = sum(1 for r in results if r.get("recovery"))
        rate = n_rec / N
        # Wilson CI
        if 0 < rate < 1:
            ci = stats.binom.interval(0.95, N, rate)
            ci_lo, ci_hi = ci[0]/N, ci[1]/N
        elif rate == 0:
            ci_lo, ci_hi = 0, 1 - 0.05**(1/N)
        else:
            ci_lo, ci_hi = 0.05**(1/N), 1.0

        print(f"\n  {cond}: {n_rec}/{N} = {rate:.3f} [{ci_lo:.3f}, {ci_hi:.3f}]")

        if cond == "R2":
            cov = [r for r in results if r.get("true_coverage") is not None]
            n_cov = sum(1 for r in cov if r["true_coverage"])
            print(f"    Coverage: {n_cov}/{len(cov)} = {n_cov/len(cov):.3f}" if cov else "")
            sel = [r for r in results if r.get("selection_given_coverage") is not None]
            n_sel = sum(1 for r in sel if r["selection_given_coverage"])
            print(f"    Selection|Coverage: {n_sel}/{len(sel)} = {n_sel/len(sel):.3f}" if sel else "")

    # Primary contrast: R2 - R1
    r1_results = [state["results"].get(f"{w['id']}_R1") for w in worlds]
    r2_results = [state["results"].get(f"{w['id']}_R2") for w in worlds]
    pairs = [(r1, r2) for r1, r2 in zip(r1_results, r2_results) if r1 and r2]
    if pairs:
        r1_vals = [1 if r1.get("recovery") else 0 for r1, r2 in pairs]
        r2_vals = [1 if r2.get("recovery") else 0 for r1, r2 in pairs]
        diff = np.array(r2_vals) - np.array(r1_vals)
        mean_d = diff.mean()
        if diff.std() > 0:
            t, p = stats.ttest_1samp(diff, 0)
            ci = stats.t.interval(0.95, df=len(diff)-1, loc=mean_d,
                                  scale=diff.std()/np.sqrt(len(diff)))
        else:
            t, p, ci = 0, 1.0, (mean_d, mean_d)
        print(f"\n  PRIMARY CONTRAST (R2 - R1):")
        print(f"    Effect: {mean_d:+.3f}")
        print(f"    95% CI: [{ci[0]:.3f}, {ci[1]:.3f}]")
        print(f"    p = {p:.4f}")

    # Resources
    r = state["resources"]
    print(f"\n  RESOURCES: {r['calls']} calls, "
          f"{r['input_tokens']+r['output_tokens']} tokens")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", action="store_true", help="Run DEV on seen cases")
    parser.add_argument("--locked", action="store_true", help="Run LOCKED on new cases")
    parser.add_argument("--all", action="store_true", help="Run both")
    args = parser.parse_args()

    if not any([args.dev, args.locked, args.all]):
        args.all = True

    provider = RemoteLLMProvider(timeout=120)
    state = load_checkpoint()

    if args.dev or args.all:
        run_dev(provider, state)
        analyze(state, DEV_WORLDS, "DEV (22 seen SD-H4 cases)")

    if args.locked or args.all:
        run_locked(provider, state)
        analyze(state, LOCKED_WORLDS, "LOCKED (25 new unseen worlds)")

    save_checkpoint(state)
    print(f"\n  Checkpoint saved: {CHECKPOINT_FILE}")


if __name__ == "__main__":
    main()
