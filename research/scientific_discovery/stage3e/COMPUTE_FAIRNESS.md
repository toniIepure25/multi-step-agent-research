# Compute Fairness — Stage 3E Recovery Conditions

## Protocol

Each condition was evaluated on the same worlds with the same model (gemma3:27b-it-qat)
at temperature=0. All conditions receive the same evidence and hypothesis information.

## Cost Comparison (LOCKED: 25 worlds)

| Condition | Calls/world | Total calls | Approx tokens/world | Total tokens |
|-----------|-------------|-------------|---------------------|-------------|
| R0 | 1 | 25 | ~600 | ~15,000 |
| R1 | 1 | 25 | ~800 | ~20,000 |
| R2 | 2 | 50 | ~1,600 | ~40,000 |
| R4 | 1 | 25 | ~600 | ~15,000 |

## Performance / Cost Ratio

| Condition | Recovery | Cost (relative) | Recovery/Cost |
|-----------|----------|----------------|---------------|
| R0 | 76.0% | 1.0x | 0.760 |
| R1 | 80.0% | 1.3x | 0.615 |
| R2 | 60.0% | 2.7x | 0.222 |
| R4 | 100% | 1.0x | 1.000 (diagnostic only) |

## Conclusion

R0 (simple one-shot) has the best performance/cost ratio for normal operation.
R1 provides marginal improvement at marginal cost.
R2 provides WORSE performance at HIGHER cost — dominated on both dimensions.
R4 is a diagnostic and not applicable to normal operation.

## Equal-Workflow Comparison

All conditions use the same basic workflow:
1. Receive hypothesis + decisive evidence
2. Produce replacement explanation

R2 adds:
- Multi-candidate generation step
- Explicit candidate evaluation step
- Final selection step

This additional workflow complexity HURTS rather than helps.
