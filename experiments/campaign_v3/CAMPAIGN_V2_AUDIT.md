# Campaign V2 Scientific Audit

## A. Identifiability Gate: Two Failed Criteria

Phase 14 identifiability gate passed 5/7 criteria. The two failures:

### Criterion 6: B4 and Full REE must be behaviorally distinguishable

**Expected**: B4 (with DiversityAwareMarket or alternative scheduler) and Full REE
should produce different operator sequences and quality on scenarios where
mechanism differences should matter.

**Observed**: self_model, stopping_policy, and epistemic_market ablation flags
produce identical behavior. The controller defaults mask interventions:
- `self_model=False` sets neutral prior (1.0), but no custom self_model is
  injected in standard runs, so default (0.7) applies either way
- `stopping_policy=False` passes `None`, but the controller recreates
  `StoppingPolicy()` from defaults
- `epistemic_market=False` passes `RoundRobinMarket` but the controller
  received `None` and defaulted to `EpistemicMarket()` in Campaign V2

**Root cause**: The ablation→controller pathway for self_model, stopping, and market
was implemented in `SemanticBenchmarkRunner` but the controller's `__init__` defaults
override `None` values. The fix requires passing explicit neutral/disabled objects
rather than `None`.

**Threat to V2 conclusions**: LOW for primary findings. The headline claim
(B1 > Full REE, hypothesis ecology d≈1.4) relies on hypothesis_ecology and
ignorance_ledger ablations which ARE correctly wired. The non-causal ablation
findings are correctly reported as negative results. However, the claim that
"self-model has no effect" may be invalid — it was never properly tested.

**Must repair before V3**: YES for self_model and market ablation.

### Criterion 7: self_model ON/OFF must affect action choice

**Expected**: With self_model OFF, operators should use neutral capability
priors (1.0 success rate) instead of empirical rates, changing bid rankings.

**Observed**: No behavioral difference because the standard campaign doesn't
inject a custom `SelfModelSummary`, so the default (0.7 overall) is used
regardless of the ablation flag.

**Root cause**: Same as Criterion 6 — the intervention is only effective when
a non-default `SelfModelSummary` is explicitly provided AND the ablation flag
replaces it with neutral (1.0). In the ablation campaign, a custom SM was
provided but the controller defaulted `None` to `SelfModelSummary()`.

**Threat to V2 conclusions**: LOW. H-REE-01 was correctly classified
INCONCLUSIVE. No claim was made about self-model effectiveness.

**Must repair before V3**: YES — need to verify controller actually receives
and uses the ablation-modified self_model.

## B. H-REE Numbering Reconciliation

See `HYPOTHESIS_CANONICAL_MAPPING.md` (companion document).

The V2 FINAL_REPORT_V2.md contains a numbering swap between H-REE-05 and H-REE-10.
This does NOT alter the scientific conclusions (verdicts are correctly attributed
to the right mechanisms), but the IDs are inconsistent with the canonical source.
