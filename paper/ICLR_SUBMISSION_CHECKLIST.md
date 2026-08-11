# ICLR 2027 Submission Checklist

## Pre-Submission (Before Sep 11, 2026 AOE)

### Author & Abstract Registration
- [ ] Author list finalized (no additions after abstract deadline)
- [ ] OpenReview profile created/updated for all authors
- [ ] Abstract registered on OpenReview
- [ ] Keywords selected
- [ ] Subject areas selected

### Abstract Text
```
Large language model (LLM) research agents combine heterogeneous cognitive
operations—retrieval, hypothesis generation, reasoning, and falsification—to
solve epistemic tasks. Most architectures select operations greedily, assuming
local value suffices. We introduce a controlled benchmark enabling same-state
counterfactual evaluation of cognitive operation sequences. In controlled
experiments (N=56), specific operation pairs exhibit super-additive temporal
complementarity (hypothesis → retrieval: +0.162, 95% CI [0.135, 0.188]).
These structural effects persist under real LLM execution with two model
substrates. We also report systematic negative findings: sequence superiority
is not confirmed, adaptive control fails, and curated-evidence transfer is
not supported. The benchmark, temporal-complementarity evidence, and
negative-results analysis constitute our contributions.
```

### TL;DR
Controlled benchmark reveals temporal complementarity among cognitive
operations in LLM agents; effects replicate under LLM execution but
adaptive control and real-evidence transfer fail.

### Keywords
```
cognitive operations, temporal complementarity, LLM agents, counterfactual
evaluation, epistemic reasoning, metacognitive control, negative results
```

## Full Paper (Before Sep 16, 2026 AOE)

### Manuscript
- [x] main.tex written
- [ ] Official ICLR 2027 template applied
- [ ] Page count ≤ 9 (main text)
- [ ] All tables legible at paper scale
- [ ] All figures legible at paper scale

### Double-Blind Audit
- [x] No author names in main text
- [x] No GitHub/repository URLs
- [x] No institutional affiliations (beyond "Anonymous")
- [ ] PDF metadata scrubbed
- [x] Self-citations in third person
- [x] No acknowledgements

### Required Statements
- [x] AI use statement (Appendix B)
- [x] Reproducibility statement (Appendix A)

### Figures
- [x] Figure 2: Complementarity matrix
- [x] Figure 3: Attack timing
- [x] Figure 4: Adaptive control failure
- [x] Figure 5: Cross-level replication

### Bibliography
- [x] references.bib created
- [ ] All citations verified against primary sources
- [ ] No broken citations after compilation

### Supplementary Material
- [ ] Code package prepared (anonymous)
- [ ] Raw result artifacts included
- [ ] Prompt templates documented

## Post-Submission
- [ ] Author response prepared (after reviews)
- [ ] Camera-ready deadline tracked
