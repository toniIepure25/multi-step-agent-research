# Figure 1: Same-State Counterfactual Evaluation

Conceptual diagram showing:

```
                    E_t (Epistemic State at step t)
                    ┌──────────────┐
                    │ Evidence: R_t │
                    │ Hypotheses: H_t│
                    │ Inferences: I_t│
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
         [gen_hyp]     [retrieve]    [attack]
              │            │            │
              ▼            ▼            ▼
           E_{t+1,A}    E_{t+1,B}   E_{t+1,C}
              │            │            │
     matched budget  matched budget  matched budget
              │            │            │
              ▼            ▼            ▼
           Q(A)         Q(B)         Q(C)
              │            │            │
              └────────────┼────────────┘
                           │
                    ΔQ = counterfactual
                    operation value
```

All three forks start from identical E_t.
Any quality difference is attributable to the operation choice, not state variation.
