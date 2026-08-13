# Final Submission Checklist

## Scientific Gates

| Gate | Status | Evidence |
|------|--------|----------|
| RAW_TRACE_HASHES | PASS | _verify_freeze.py: all 8 files match expected SHA256 |
| PREREGISTRATION_INTEGRITY | PASS | SHA256=2739e101619fc50b, committed at 8950ba9 |
| UNSEEN_TASK_VALIDATION | PASS | SciFact 88 unseen, HotpotQA 300 unseen |
| TRACE_CERTIFICATION | PASS | All traces contain condition, query, retrieval, answer |
| CALL_FAIRNESS | PASS | REAL/SHUFFLED/NEUTRAL = 3 calls; DIRECT/GENERIC = 3 calls |
| RETRIEVAL_FAIRNESS | PASS | All conditions use BM25 top-5 on same corpus |
| STATISTICAL_INDEPENDENCE | PASS | Task-level paired bootstrap, no within-task pooling |
| HOLM_RECONSTRUCTION | PASS | Independent reconstruction matches stored values |
| FORMAL_STATISTICS_REPLAY | PASS | reproduce_all.py: 9/14 significant matches |
| RESULT_REGISTRY | PASS | All 5 hypotheses documented with verdicts |
| CLAIM_AUDIT | PASS | FINAL_CLAIM_LADDER.md maps every claim to evidence |
| CITATION_AUDIT | PENDING | Related work audit done (FINAL_RELATED_WORK_AUDIT.md) |
| FIGURE_REPRODUCTION | PASS | generate_figures.py produces 4 figures from raw traces |
| TABLE_REPRODUCTION | PASS | generate_tables.py produces 5 tables from CSVs |
| ANONYMITY_SCAN | PENDING | Must verify no identifying information in paper |
| LATEX_COMPILE | PENDING | Requires ICLR template integration |
| PAGE_LIMIT | PENDING | Target: 9 pages (ICLR) |
| FULL_TEST_SUITE | PASS | 446 passed, 1 skipped |

## Artifact Inventory

### Paper Documents
- [x] FINAL_REPOSITIONING.md
- [x] FINAL_TITLE_AUDIT.md
- [x] FINAL_ABSTRACT.md
- [x] FINAL_CONTRIBUTIONS.md
- [x] FINAL_CLAIM_LADDER.md
- [x] FINAL_NEGATIVE_FINDINGS.md
- [x] FINAL_RELATED_WORK_AUDIT.md
- [x] FINAL_REVIEW_SIMULATION.md
- [x] FINAL_META_REVIEW.md
- [x] FINAL_VENUE_DECISION.md
- [x] FINAL_SUBMISSION_CHECKLIST.md (this file)

### Data
- [x] final_primary_effects.csv
- [x] final_holm_family.csv
- [x] final_model_transfer.csv
- [x] final_scifact_decomposition.csv
- [x] final_resource_usage.csv

### Figures
- [x] fig2_retrieval_reasoning_plane.pdf — Signature dissociation figure
- [x] fig3_model_transfer.pdf — Forest plot of effects by dataset x model
- [x] fig4_scifact_decomposition.pdf — Answer flip stacked bars
- [x] fig5_pipeline_effects.pdf — Retrieval vs task by condition
- [ ] fig1_causal_audit.pdf — Methodology diagram (manual creation needed)

### Tables
- [x] table1_conditions.tex — Condition performance summary
- [x] table2_setup.tex — Experimental resource budget
- [x] table3_primary_results.tex — Holm-corrected effects
- [x] table4_scifact_mechanism.tex — Answer flip analysis
- [x] table5_claim_boundary.tex — Claim boundary summary

### Scripts
- [x] reproduce_all.py — Full reproduction from raw traces
- [x] generate_figures.py — Figure generation
- [x] generate_tables.py — Table generation

## Remaining Work
1. Write the ICLR LaTeX manuscript (main.tex + appendix.tex)
2. Create Figure 1 (methodology diagram)
3. Finalize references.bib
4. Anonymity scan
5. Final page count verification
