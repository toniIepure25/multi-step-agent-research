# Prior Art — Stage 4: Representational Regime Revision

## Date: 2026-08-15

---

## 1. Separable Pathways for Causal Reasoning (arXiv:2604.20039)

**Focus:** Architectural scaffolding that enables hypothesis-space restructuring in LLM agents.

| Dimension | Status |
|-----------|--------|
| Detect inadequacy? | YES — identifies when hypothesis space is saturated |
| Expand hypothesis space? | YES — adds new causal pathways |
| Change representation? | PARTIAL — expands variables but not functional form |
| Preserve provenance? | UNCLEAR |
| Held-out validation? | YES |
| False-revision control? | NOT EXPLICITLY |
| Rollback? | NO |
| Causal ablations? | YES |
| LLM generation? | YES |
| Active experiments? | NO |
| Complexity penalty? | NO |

**Overlap with ASAR:** Both detect hypothesis-space insufficiency. Separable Pathways focuses on *architectural scaffolding* for reasoning, while ASAR focuses on *empirical validation* of regime transitions.

**ASAR distinction:** ASAR requires validated held-out improvement + false-revision control + rollback + complexity penalty. Separable Pathways does not enforce validated acceptance.

---

## 2. Self-Revising Discovery Systems (arXiv:2606.01444)

**Focus:** Categorical framework for treating scientific discovery as revision of representational regime.

| Dimension | Status |
|-----------|--------|
| Detect inadequacy? | THEORETICAL (categorical signal) |
| Expand hypothesis space? | YES (fundamental to framework) |
| Change representation? | YES (core thesis: revision of representational regime) |
| Preserve provenance? | YES (functorial transport) |
| Held-out validation? | THEORETICAL |
| False-revision control? | NOT EMPIRICALLY |
| Rollback? | THEORETICAL |
| Causal ablations? | NO (theoretical paper) |
| LLM generation? | NOT IMPLEMENTED |
| Active experiments? | NOT IMPLEMENTED |
| Complexity penalty? | THEORETICAL (description length) |

**Overlap with ASAR:** Direct conceptual overlap on representational regime revision. The categorical framework provides the formal language; ASAR provides empirical evaluation.

**ASAR distinction:** ASAR implements and *empirically evaluates* regime revision with controlled experiments, false-revision rate measurement, held-out validation, and behavioral ablations. The categorical framework is theoretical — it does not measure whether systems actually perform correct revisions or control false revisions.

---

## 3. PiEvo (arXiv:2602.06448)

**Focus:** Principle-Evolvable Scientific Discovery via Uncertainty Minimization. Evolves scientific principles (representation-level objects) through iterative refinement.

| Dimension | Status |
|-----------|--------|
| Detect inadequacy? | IMPLICIT (uncertainty signal) |
| Expand hypothesis space? | YES (principle evolution) |
| Change representation? | YES (principle mutation/crossover) |
| Preserve provenance? | PARTIAL (lineage via evolution) |
| Held-out validation? | YES |
| False-revision control? | IMPLICIT (selection pressure) |
| Rollback? | IMPLICIT (population retains old) |
| Causal ablations? | NO |
| LLM generation? | YES |
| Active experiments? | NO |
| Complexity penalty? | IMPLICIT (fitness-based) |

**Overlap with ASAR:** Both change representation-level objects. PiEvo uses evolutionary search over principles; ASAR uses structured detection→generation→validation.

**ASAR distinction:** ASAR explicitly separates detection, generation, and validation as distinct testable stages. PiEvo optimizes end-to-end via evolution without diagnosing which stage fails. ASAR measures false-revision explicitly; PiEvo relies on selection pressure. ASAR performs active experiment design for regime discrimination.

---

## 4. FALSIFYBENCH

| Dimension | Status |
|-----------|--------|
| Detect inadequacy? | NO (tests within fixed hypothesis space) |
| Expand hypothesis space? | NO |
| Change representation? | NO |
| Preserve provenance? | N/A |
| Held-out validation? | N/A for representation |
| False-revision control? | N/A |
| Rollback? | N/A |
| Causal ablations? | NO |
| LLM generation? | YES |
| Active experiments? | YES (iterative testing) |
| Complexity penalty? | N/A |

**Overlap:** Minimal — FALSIFYBENCH operates within a fixed rule space.

**ASAR distinction:** ASAR's Stage 4 specifically tests CHANGING the representational space, which FALSIFYBENCH does not address.

---

## 5. Google AI Co-Scientist (Nature 2026)

| Dimension | Status |
|-----------|--------|
| Detect inadequacy? | IMPLICIT |
| Expand hypothesis space? | YES (generates novel hypotheses) |
| Change representation? | UNCLEAR (end-to-end system) |
| Preserve provenance? | YES |
| Held-out validation? | YES (wet-lab validation) |
| False-revision control? | NOT EXPLICIT |
| Rollback? | NOT DESCRIBED |
| Causal ablations? | NO |
| LLM generation? | YES |
| Active experiments? | YES |
| Complexity penalty? | NOT DESCRIBED |

**Overlap:** Both aim at scientific discovery with LLMs.

**ASAR distinction:** ASAR provides controlled, reproducible measurement of *representational regime change* with explicit false-revision control. Co-Scientist optimizes for end-to-end discovery without isolating the representation-change mechanism.

---

## WHAT EXACT EXPERIMENT CAN ASAR RUN THAT THESE SYSTEMS DO NOT?

### ASAR's Unique Experimental Contribution

**Controlled measurement of regime-revision correctness with:**

1. **Formal expressivity verification**: Evaluator proves truth ∉ expressible(R0) but truth ∈ expressible(R*). No other system verifies this formally.

2. **False-revision rate under negative controls**: Worlds where R0 IS sufficient, testing whether the system inappropriately revises. No comparison system measures this.

3. **Held-out validation gate**: Regime transitions must improve prediction on unseen evidence. Explicitly measured and compared to complexity cost.

4. **Behavioral ablation**: Each mechanism component (detector, foundry, validation, complexity gate, active testing) is independently ablated. Causal attribution of benefit.

5. **Rollback measurement**: Testing whether the system can reject revisions that initially looked promising but fail validation.

6. **Active regime discrimination**: Using experiment design to distinguish between competing representational changes.

### Novelty Assessment

| Capability | Closest existing | ASAR addition |
|-----------|-----------------|---------------|
| Detection | PiEvo uncertainty | Explicit structured detection with false-alarm rate |
| Generation | Separable Pathways | Typed regime transitions, transport, complexity |
| Validation | Generic held-out | Formal expressivity + controlled negative worlds |
| False-revision | None explicit | First-class negative control measurement |
| Rollback | None empirical | Measured rejection after initial acceptance |
| Active discrimination | None for regime | Experiment design for representation choice |

### Verdict

**NOVELTY: SUFFICIENT (conditional on implementation)**

No existing system provides controlled empirical measurement of ALL of:
- regime-failure detection accuracy
- false-revision control
- validated regime transitions with held-out improvement
- complexity-penalized acceptance
- behavioral ablation of each component
- active experiment design for regime discrimination

The ASAR Stage 4 experiment is distinct from prior art. It is NOT merely "our agent can revise ontology" (which Self-Revising Discovery and PiEvo already claim theoretically). It is: **"we can measure how well an agent revises its representation, including when it shouldn't."**
