# Table 1: Cognitive Operations and Semantics

| Operation | Symbol | Input | Output | Standalone Value (V4) |
|-----------|--------|-------|--------|-----------------------|
| Retrieve | \(a_{\text{ret}}\) | Query (implicit or explicit) | Evidence items with source metadata | 0.050 |
| Generate hypothesis | \(a_{\text{hyp}}\) | Available evidence, current hypotheses | New candidate hypothesis with reasoning | 0.273 |
| Attack / falsify | \(a_{\text{atk}}\) | Current hypotheses, evidence | Weaknesses, counterevidence, alternatives | 0.000 |
| Reason | \(a_{\text{rsn}}\) | Hypotheses, evidence | Evaluated support/contradiction for each hypothesis | 0.000 |

*Standalone value = mean epistemic quality gain from executing the operation in isolation from a matched epistemic state (V4, N = 56 worlds across 8 regimes). Source: `campaign_v4/results/complementarity_matrix.json`, field `single_means`.*
