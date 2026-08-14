# Scientific Discovery Hypotheses

**Namespace:** SD-H (Scientific Discovery Hypotheses)
**Status:** Pre-implementation — to be tested via controlled benchmarks

---

## SD-H1 — Falsification Advantage

**Claim:** A falsification-first workflow (actively seeking disconfirming evidence before confirming) improves recovery from misleading initial theories compared to standard generation-and-ranking approaches.

**Causal mechanism:** Explicitly searching for falsifiers before committing to a theory reduces the chance of confirmation-locked reasoning trajectories.

**Predictions if true:**
- Under confirmation-trap worlds, falsification-first achieves faster belief correction
- Refutation sensitivity (RS) is higher for falsification-first vs. baselines
- Theory stickiness is lower

**Predictions if false:**
- Falsification search wastes compute without improving outcomes
- LLMs cannot reliably generate valid falsifiers
- Generated falsifiers are too weak to cause belief change

**Falsifiers:**
- If falsification-first shows no RS improvement under matched compute
- If generated falsifiers are systematically invalid (target wrong assumptions)

**Maturity:** H2 (falsifiable hypothesis — no empirical test yet)

---

## SD-H2 — Hypothesis Ecology

**Claim:** Maintaining mechanistically distinct alternative explanations simultaneously reduces premature commitment to wrong theories.

**Causal mechanism:** Diverse alternatives provide fallback positions when the leading theory fails, preventing the system from rationalizing contradictory evidence.

**Predictions if true:**
- Systems with ecology maintain viable alternatives after leading hypothesis is refuted
- Recovery accuracy is higher than single-hypothesis tracking
- Mechanism diversity correlates with better ontology-failure detection

**Predictions if false:**
- Maintaining many hypotheses simply dilutes confidence without improving accuracy
- LLMs generate near-paraphrases regardless of diversity pressure
- Compute spent on alternatives would be better spent on deeper testing of fewer hypotheses

**Falsifiers:**
- If diversity-scored ecology performs equally to single-best-hypothesis tracking under matched compute
- If generated "alternatives" are systematically paraphrases (low mechanism diversity)

**Maturity:** H2

---

## SD-H3 — Discriminative Experiment Selection

**Claim:** Information/discrimination-based experiment choice reduces oracle regret compared to confirmation-seeking or random experiment selection.

**Causal mechanism:** Experiments that maximally distinguish between live hypotheses (rather than confirm the leader) produce more decisive evidence per unit cost.

**Predictions if true:**
- Oracle regret is lower for discrimination-based selection
- Fewer experiment rounds needed to reach correct posterior ranking
- Cost-adjusted information gain is higher

**Predictions if false:**
- LLM-estimated discrimination scores are poorly calibrated
- Confirmation-seeking experiments are equally informative in practice
- The overhead of computing discrimination scores exceeds the information gain

**Falsifiers:**
- If random experiment selection achieves equivalent oracle regret
- If LLM discrimination scores have near-zero correlation with true information gain

**Maturity:** H2

---

## SD-H4 — Self-Correction (Theory Abandonment)

**Claim:** An AI system with explicit abandonment thresholds and ad-hoc complexity penalties appropriately abandons self-generated hypotheses after decisive falsification.

**Causal mechanism:** Explicit thresholds override the tendency to rationalize contradictory evidence; complexity penalties prevent unlimited rescue assumptions.

**Predictions if true:**
- Abandonment latency is bounded after decisive falsifiers
- Self-authorship bias (differential treatment of self-generated vs. external hypotheses) is reduced compared to baseline
- False-theory survival time decreases with explicit thresholds

**Predictions if false:**
- LLMs override explicit thresholds through rationalization
- Thresholds cause premature abandonment of correct hypotheses
- Self-authorship bias is not a real phenomenon in LLMs (no differential treatment)

**Falsifiers:**
- If system retains high confidence on refuted self-generated hypotheses despite threshold mechanism
- If threshold-based abandonment increases false-abandonment rate without reducing false-retention rate

**Maturity:** H2

---

## SD-H5 — Evidence Independence

**Claim:** Provenance-aware evidence aggregation (tracking source independence) reduces confidence inflation from redundant sources.

**Causal mechanism:** Recognizing that five citations of the same original study are not five independent confirmations prevents overconfidence.

**Predictions if true:**
- Systems with independence tracking show appropriate confidence under duplicate evidence
- Confidence does not scale linearly with citation count from shared root source
- Effective evidence count correlates better with true posterior than raw count

**Predictions if false:**
- Source provenance is too noisy to estimate independence reliably
- Confidence inflation from dependent sources is negligible in practice
- The overhead of tracking provenance exceeds the calibration benefit

**Falsifiers:**
- If duplicate-source condition produces equivalent confidence to independent-source condition (no inflation detected)
- If provenance tracking systematically misclassifies independent sources as dependent

**Maturity:** H2

---

## SD-H6 — Ontology Recovery

**Claim:** A system can detect and recover from situations where all candidate hypotheses share a false premise (incorrect ontological framing).

**Causal mechanism:** Monitoring for systematic failure across ALL hypotheses in the ecology (shared high-confidence predictions failing) triggers frame revision rather than ad-hoc theory rescue.

**Predictions if true:**
- Under ontology-failure worlds, system triggers REVISE_ONTOLOGY at rates above baseline
- New framing improves prediction accuracy
- System avoids infinite cycling among wrong-framed hypotheses

**Predictions if false:**
- LLMs cannot reliably detect shared premises across hypotheses
- Frame revision is triggered spuriously (high false positive rate)
- Generated new frames are not meaningfully different from original

**Falsifiers:**
- If ontology revision rate equals zero or equals spurious-trigger rate in non-failure worlds
- If new frames are semantically equivalent to old frames (name changes only)

**Maturity:** H1 (mechanistic but not yet fully falsifiable — needs world design)

---

## SD-H7 — Time-Capsule Discovery

**Claim:** A system with falsification-first reasoning and discriminative experiment design can reconstruct later-supported hypotheses and discriminative tests from pre-discovery evidence better than strong single-pass baselines.

**Causal mechanism:** The structured scientific loop (generate alternatives → derive predictions → design discriminative tests) provides a richer exploration of the hypothesis space than single-pass generation.

**Predictions if true:**
- Higher mechanistic overlap with eventual discovery
- Better experiment proposals (assessed by post-cutoff evidence)
- Higher diversity of viable hypotheses including correct direction

**Predictions if false:**
- Single-pass frontier LLMs already reach correct hypothesis via parametric knowledge
- Pre-discovery evidence is insufficient to distinguish correct from incorrect theories
- Contamination makes evaluation unreliable

**Falsifiers:**
- If single-pass LLM achieves equivalent mechanistic overlap under matched conditions
- If no pre-discovery evidence trail points toward eventual discovery

**Maturity:** H1 (complex evaluation design required)

---

## SD-H8 — Live Computational Discovery

**Claim:** The system can generate and empirically test a previously unprovided research hypothesis on public data, producing results that survive preregistered analysis and independent replication.

**Causal mechanism:** The full scientific loop (literature → hypothesis → prediction → experiment → analysis → revision) applied to a real computational domain can produce genuine findings.

**Predictions if true:**
- At least one hypothesis survives preregistered statistical test
- Effect replicates on holdout data/alternative specification
- Novelty audit shows no direct prior art for the specific finding

**Predictions if false:**
- Generated hypotheses are too vague for statistical testing
- All tests are underpowered or confounded
- All "novel" findings are rediscoveries

**Falsifiers:**
- Zero hypotheses survive preregistered analysis
- All surviving hypotheses are known findings

**Maturity:** H0 (aspirational — requires Stages 1–5 to be operational first)

---

## Hypothesis Priority for Testing

| Hypothesis | Priority | Reason | Stage |
|-----------|----------|--------|-------|
| SD-H1 | HIGH | Core claim, testable with controlled worlds | Stage 1 |
| SD-H4 | HIGH | Self-correction is the defining capability | Stage 1 |
| SD-H2 | MEDIUM | Supports SD-H1 mechanism | Stage 1 |
| SD-H3 | MEDIUM | Important but requires Stage 2 infrastructure | Stage 2 |
| SD-H5 | MEDIUM | Testable with metamorphic tests early | Stage 1 |
| SD-H6 | LOW (hard) | Requires ontology-failure world design | Stage 3 |
| SD-H7 | LOW (hard) | Requires time-capsule infrastructure + contamination defense | Stage 5 |
| SD-H8 | LOWEST | Aspirational; requires all prior stages | Stage 6 |
