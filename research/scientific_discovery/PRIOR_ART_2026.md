# Prior Art Audit — Scientific AI Discovery (2024–2026)

**Date:** 2026-08-14
**Purpose:** Honest assessment of what exists before claiming novelty

---

## 1. Direct Prior Art — AI Scientific Discovery Systems

### Google AI Co-Scientist (2025–2026)
- **What it does:** Multi-agent scientific hypothesis generation with tournament-based ranking, literature grounding, and self-refinement
- **Mechanisms:** Hypothesis generation, ranking, literature verification, iterative refinement
- **Evaluation:** Expert evaluation on biomedical hypotheses; some validated experimentally
- **Overlap with ASAR:** Hypothesis ecology, multi-agent critique, novelty checking
- **Gap ASAR addresses:** Co-Scientist focuses on generation + ranking. Does NOT explicitly measure: falsification, belief revision after contradictory evidence, theory abandonment, ontology revision, discriminative experiment design
- **Classification:** DIRECT PRIOR ART (hypothesis generation/ranking); DISTINCT CONTRIBUTION (falsification/revision evaluation)

### The AI Scientist / AI Scientist v2 (Sakana AI, 2024–2025)
- **What it does:** End-to-end paper generation: idea → experiment → writeup → review
- **Mechanisms:** LLM-driven experiment design, code generation, automated review
- **Evaluation:** Paper quality, review scores
- **Overlap with ASAR:** Automated experiment execution, self-review
- **Gap ASAR addresses:** AI Scientist does not maintain persistent hypothesis ecology, does not perform falsification, does not revise beliefs across experiments, does not evaluate self-correction
- **Classification:** CONCEPTUAL NEIGHBOR (experiment execution); DISTINCT CONTRIBUTION (scientific process evaluation)

### FutureHouse / WikiCrow / PaperQA2 (2024–2026)
- **What it does:** Literature-grounded question answering and synthesis at scale
- **Mechanisms:** Multi-step retrieval, source verification, synthesis
- **Evaluation:** Factual accuracy, source grounding
- **Overlap with ASAR:** Evidence retrieval, source verification
- **Gap ASAR addresses:** FutureHouse tools are retrieval/synthesis systems, not hypothesis-testing systems. No falsification, no experiment design, no belief revision
- **Classification:** CLOSE MECHANISM (retrieval/synthesis); DISTINCT CONTRIBUTION (scientific reasoning)

---

## 2. Benchmarks and Evaluation Frameworks

### ProjectionBench (2025–2026)
- **What it does:** Progressive scientific information revelation; evaluates hypothesis generation at each stage
- **Evaluation:** Hypothesis similarity to eventual discovery
- **Overlap with ASAR:** Progressive revelation design; hypothesis quality evaluation
- **Gap ASAR addresses:** ProjectionBench measures hypothesis similarity. ASAR evaluates falsification, experiment design, belief revision, self-correction — process quality, not just outcome similarity
- **Classification:** EVALUATION OVERLAP (hypothesis generation); DISTINCT CONTRIBUTION (process evaluation)

### ResearchBench (2025)
- **What it does:** Evaluates research agents on inspiration retrieval, hypothesis composition, hypothesis ranking
- **Evaluation:** Retrieval recall, hypothesis quality, ranking accuracy
- **Overlap with ASAR:** Hypothesis generation and ranking
- **Gap ASAR addresses:** ResearchBench does not evaluate: prediction derivation, falsification, experiment discrimination, belief revision, theory abandonment
- **Classification:** EVALUATION OVERLAP (hypothesis generation/ranking); DISTINCT CONTRIBUTION (falsification + revision)

### HypoBench (2025–2026)
- **What it does:** Evaluates LLM hypothesis generation capability across scientific domains
- **Evaluation:** Quality, diversity, novelty of generated hypotheses
- **Overlap with ASAR:** Hypothesis generation quality
- **Gap ASAR addresses:** HypoBench evaluates generation only. ASAR evaluates what happens AFTER generation: testing, falsification, revision
- **Classification:** EVALUATION OVERLAP (generation); DISTINCT CONTRIBUTION (post-generation process)

### AstaBench (2025–2026)
- **What it does:** Broad scientific research task evaluation
- **Evaluation:** Multiple research competencies
- **Overlap with ASAR:** General scientific capability measurement
- **Gap ASAR addresses:** AstaBench is broad capability assessment. ASAR deeply evaluates the specific capability of scientific self-correction
- **Classification:** EVALUATION OVERLAP (broad); DISTINCT CONTRIBUTION (self-correction depth)

### PaperBench (2025)
- **What it does:** End-to-end replication of AI research papers
- **Evaluation:** Code implementation, experiment reproduction
- **Overlap with ASAR:** Experiment execution, method understanding
- **Gap ASAR addresses:** PaperBench measures replication, not discovery. ASAR measures whether systems can generate AND KILL hypotheses
- **Classification:** CONCEPTUAL NEIGHBOR (experiment execution); DISTINCT CONTRIBUTION (discovery process)

### FrontierScience (2025–2026)
- **What it does:** Expert-level scientific reasoning evaluation
- **Evaluation:** Scientific reasoning quality
- **Overlap with ASAR:** Scientific reasoning capability
- **Gap ASAR addresses:** FrontierScience evaluates reasoning quality. ASAR evaluates reasoning UNDER ADVERSARIAL SELF-CORRECTION conditions
- **Classification:** EVALUATION OVERLAP (reasoning); DISTINCT CONTRIBUTION (self-correction conditions)

---

## 3. Related Mechanisms and Approaches

### Scientific Debate / Multi-Agent Debate (2024–2026)
- **What it does:** Multiple LLM agents argue for/against positions
- **Mechanisms:** Multi-perspective argumentation, adversarial critique
- **Overlap with ASAR:** Red team concept, multiple perspectives
- **Gap:** Debate systems typically don't maintain persistent belief states, don't perform quantitative belief revision, don't design experiments to resolve disagreements
- **Classification:** CLOSE MECHANISM (multi-agent critique); DISTINCT CONTRIBUTION (persistent state + experiment-driven resolution)

### Self-Correcting LLMs / Reflexion / Self-Refine (2023–2025)
- **What it does:** LLMs that revise outputs based on feedback
- **Mechanisms:** Generate → evaluate → revise loop
- **Overlap with ASAR:** Self-correction concept
- **Gap:** These systems correct surface errors in single outputs. ASAR evaluates whether systems correct THEORETICAL COMMITMENTS over extended scientific investigations with external evidence
- **Classification:** CONCEPTUAL NEIGHBOR (self-correction); DISTINCT CONTRIBUTION (theory-level revision vs. output-level refinement)

### Bayesian Experimental Design (classical)
- **What it does:** Optimal experiment selection to maximize information gain
- **Mechanisms:** Expected information gain, KL divergence optimization
- **Overlap with ASAR:** Experiment design, information gain scoring
- **Gap:** Classical BED assumes known likelihood models. ASAR operates with LLM-estimated likelihoods and heuristic approximations
- **Classification:** CLOSE MECHANISM (experiment design theory); DISTINCT CONTRIBUTION (LLM-based operationalization + broader scientific loop)

### Active Learning / Bayesian Optimization (classical)
- **What it does:** Sequential experiment selection to optimize objectives
- **Overlap with ASAR:** Sequential decision-making under uncertainty
- **Gap:** These optimize known objectives. ASAR handles open-ended scientific discovery where the hypothesis space itself may be wrong
- **Classification:** CONCEPTUAL NEIGHBOR

---

## 4. Novelty Assessment

### What ASAR can potentially do that prior systems do NOT cover:

1. **Falsification evaluation** — Measuring whether AI systems search for disconfirming evidence (not just confirming)
2. **Belief revision measurement** — Quantifying how beliefs change after decisive evidence
3. **Theory abandonment evaluation** — Measuring whether systems appropriately kill wrong hypotheses
4. **Self-authorship bias measurement** — Testing whether systems protect self-generated vs. external hypotheses differently
5. **Ontology revision evaluation** — Measuring recognition that the hypothesis space itself is wrong
6. **Discrimination-based experiment design** — Measuring whether experiments distinguish hypotheses (not just confirm leading theory)
7. **Integrated scientific process benchmark** — Evaluating the FULL cycle (generate → predict → falsify → revise → abandon) as a unified process

### Honest novelty classification:

| Capability | Novelty status |
|-----------|---------------|
| Hypothesis generation | KNOWN (Co-Scientist, HypoBench, ResearchBench) |
| Multi-agent critique | KNOWN (debate systems, Co-Scientist tournament) |
| Experiment execution | KNOWN (AI Scientist, PaperBench) |
| Literature retrieval | KNOWN (FutureHouse, RAG systems) |
| Falsification evaluation | POSSIBLY_NOVEL (no existing benchmark specifically measures this) |
| Belief revision measurement | POSSIBLY_NOVEL (no benchmark measures post-evidence belief change) |
| Theory abandonment evaluation | POSSIBLY_NOVEL |
| Ontology revision evaluation | POSSIBLY_NOVEL |
| Self-authorship bias measurement | POSSIBLY_NOVEL |
| Integrated falsification-to-revision benchmark | POSSIBLY_NOVEL |

### Critical novelty test:

> What can ASAR do or measure that AI Co-Scientist + ResearchBench + ProjectionBench do not already cover?

**Answer:** The specific measurement of scientific SELF-CORRECTION — whether AI systems can reliably identify and abandon their own wrong hypotheses after decisive falsification, under controlled conditions where ground truth is known.

This is the candidate distinct contribution. If this is already well-covered by a system we're unaware of, novelty must be downgraded.

---

## 5. Closest Direct Comparisons

| Dimension | Closest system | ASAR distinction |
|-----------|---------------|-----------------|
| Hypothesis generation | AI Co-Scientist | ASAR evaluates what happens AFTER generation |
| Benchmark | ProjectionBench + ResearchBench | ASAR measures falsification, not just similarity |
| Self-correction | Reflexion / Self-Refine | ASAR measures theory-level revision, not output refinement |
| Experiment design | Bayesian Experimental Design | ASAR operationalizes with LLMs in open-ended domains |
| Scientific agent | AI Scientist | ASAR focuses on self-correction evaluation, not paper production |

---

## 6. Risk: Novelty May Not Survive

If during implementation we discover that:
- AI Co-Scientist already performs falsification internally (unpublished)
- A 2026 system already benchmarks belief revision in AI scientists
- ProjectionBench v2 adds self-correction metrics

Then ASAR's novelty must be honestly downgraded and the contribution reframed.

The project's value does NOT depend on being first. It depends on being rigorous.
