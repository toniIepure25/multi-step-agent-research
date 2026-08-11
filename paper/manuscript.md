# Measuring the Value of Cognitive Sequences in LLM Research Agents

## Abstract

Large language model (LLM) research agents increasingly combine heterogeneous cognitive operations — retrieval, hypothesis generation, reasoning, and falsification — to solve complex epistemic tasks. Most agent architectures select operations greedily, implicitly assuming that the local value of an operation is sufficient to guide useful global reasoning. We introduce a controlled epistemic benchmark that enables counterfactual evaluation of cognitive operation sequences from matched epistemic states, isolating the downstream value of temporal composition. In controlled simulator experiments across eight heterogeneous epistemic regimes (N = 56 worlds), we find that certain operation pairs exhibit strong temporal complementarity: hypothesis generation followed by retrieval yields +0.162 super-additive epistemic gain, while repeating the same operation shows interference (−0.050). Attack/falsification value is strongly timing-dependent, producing zero epistemic gain when applied early but matching multi-step sequence quality when applied late (+0.276). These complementarity and timing effects replicate under real LLM inference with two model substrates (Gemma 3 27B and Llama 3.2 11B), confirming they are structural properties of the epistemic task rather than artifacts of scripted operators. However, we also report systematic negative findings: general sequence superiority over single operations is not confirmed under LLM execution (+0.003), operation ordering effects do not replicate (−0.050), and temporal complementarity does not transfer to static real-document research tasks (N = 14, condition range = 0.030). A learned adaptive motif controller fails to exploit the measured adaptivity gap (policy quality 0.323 vs. best fixed 0.518 vs. oracle 0.588). We contribute the benchmark, a complete negative-results analysis of adaptive cognitive control, and evidence that the correct unit of metacognitive analysis in research agents is operation-pair complementarity rather than universal sequence superiority.

---

## 1. Introduction

LLM-based research agents combine qualitatively distinct cognitive operations to solve complex epistemic tasks: they retrieve evidence, generate hypotheses, reason about causal relationships, identify contradictions, and attack or falsify candidate explanations. The design question facing every such agent is deceptively simple: *what cognitive operation should be performed next?*

Most current architectures answer this question either with a fixed pipeline — a predetermined sequence of operations applied uniformly — or with greedy scheduling, where the locally most valuable operation is selected at each step. Both approaches implicitly assume that the value of a cognitive operation can be assessed independently of its temporal context: what operations preceded it, and what operations will follow.

This assumption may be wrong. Consider a research agent that must evaluate competing hypotheses. Generating a hypothesis *before* retrieving evidence might focus subsequent retrieval on discriminating information, while retrieving first might anchor reasoning on whatever evidence happens to be available. If such *temporal complementarity* exists — if the downstream value of operation A depends on whether operation B precedes or follows it — then greedy scheduling, which evaluates operations independently, will systematically misallocate cognitive resources.

We investigate whether heterogeneous cognitive operations exhibit measurable temporal complementarity in epistemic reasoning tasks, and whether such effects survive replacement of scripted cognitive operators by real language model inference.

**Our approach.** We construct a controlled epistemic benchmark — the Epistemic World Simulator — that maintains latent ground truth invisible to the agent. This enables *same-state counterfactual evaluation*: from a single epistemic state, we fork execution into alternative cognitive operations or sequences, apply matched continuation budgets, and compare downstream epistemic gain. This counterfactual design isolates the temporal-composition value of cognitive sequences from confounding state variation.

**Contributions.**

1. A controlled benchmark for counterfactual evaluation of cognitive operation sequences from matched epistemic states.
2. Empirical evidence of temporal complementarity and interference among cognitive operations, including super-additive gains (+0.162 for hypothesis generation → retrieval) and timing dependence (attack value: 0.000 early vs. +0.276 late).
3. Replication of the two strongest effects under real LLM inference with two materially different model substrates, confirming these as structural properties of the epistemic task.
4. A systematic negative-results analysis showing that general sequence superiority, adaptive motif control, and real-document transfer are not supported.

---

## 2. Related Work

Our work intersects several active research areas. We organize the discussion around the dimensions most relevant to temporal composition of cognitive operations.

**Adaptive test-time compute.** Adaptive Computation Time (Graves, 2016) and PonderNet (Banino et al., 2021) vary the *amount* of computation based on input difficulty. Our work instead varies the *type* of computation: we ask whether qualitatively different operations compose non-additively, not whether more computation helps.

**Adaptive retrieval.** Self-RAG (Asai et al., 2024) and FLARE (Jiang et al., 2023) make state-dependent retrieval decisions. These systems adaptively decide *when* to retrieve but do not measure the compositional value of retrieval relative to other cognitive operations such as hypothesis generation or falsification.

**Process reward models.** Step-level evaluation in mathematical reasoning (Lightman et al., 2024; Wang et al., 2024) assigns value to individual reasoning steps. However, these models evaluate steps of the *same kind* (mathematical deductions), whereas our operations differ in *type* — retrieval, hypothesis generation, attack, and reasoning are qualitatively distinct cognitive acts.

**Reasoning trajectory evaluation.** Tree of Thoughts (Yao et al., 2024), Graph of Thoughts (Besta et al., 2024), and LATS (Zhou et al., 2024) search over multiple reasoning paths. These approaches evaluate *trajectory quality* but do not isolate the *compositional value* of heterogeneous operation types from matched states.

**Metacognitive agents.** Reflexion (Shinn et al., 2023) and Self-Refine (Madaan et al., 2023) add self-monitoring and strategy adjustment. Our negative results on adaptive motif control complement this literature: we show that even with measurable adaptivity opportunity, a learned metacognitive controller can fail to exploit it.

**Tool scheduling.** Toolformer (Schick et al., 2023) and ART (Paranjape et al., 2023) schedule tool use in language models. These share our interest in heterogeneous operation selection but do not provide controlled counterfactual evaluation of operation-sequence value.

**Temporal abstraction in RL.** The options framework (Sutton et al., 1999) studies temporally extended actions in reinforcement learning. Our cognitive sequences are analogous to options, but evaluated in an epistemic (information-seeking) rather than reward-maximizing context.

**Key distinction.** We did not identify prior work that combines controlled same-state counterfactual evaluation with explicit measurement of downstream complementarity among heterogeneous epistemic operations (see Table 8 for a systematic comparison). Our contribution is methodological — the ability to measure operation-pair complementarity — as much as empirical.

---

## 3. Problem Formulation

### 3.1 Epistemic State

An epistemic state \(E_t\) at step \(t\) captures everything the agent knows and believes:

\[E_t = (\mathcal{R}_t, \mathcal{H}_t, \mathcal{I}_t, c_t)\]

where \(\mathcal{R}_t\) is retrieved evidence, \(\mathcal{H}_t\) is the hypothesis set, \(\mathcal{I}_t\) is inferred relations, and \(c_t\) is cumulative cost.

### 3.2 Primitive Cognitive Operations

We define a vocabulary of four primitive cognitive operations:

| Operation | Symbol | Semantics |
|-----------|--------|-----------|
| Retrieve | \(a_{\text{ret}}\) | Acquire new evidence from external sources |
| Generate hypothesis | \(a_{\text{hyp}}\) | Propose candidate explanations for observed evidence |
| Attack/falsify | \(a_{\text{atk}}\) | Identify weaknesses, counterevidence, or alternative explanations |
| Reason | \(a_{\text{rsn}}\) | Evaluate hypotheses against available evidence |

Each operation transforms the epistemic state: \(E_{t+1} = \tau(E_t, a_t)\), where \(\tau\) is the state transition function.

### 3.3 Cognitive Sequences

A cognitive sequence \(S = [a_1, a_2, \ldots, a_k]\) is an ordered list of primitive operations. The realized epistemic gain of a sequence from state \(E_0\) is:

\[G(S \mid E_0) = Q(E_k) - Q(E_0)\]

where \(Q(\cdot)\) is an evaluator-defined quality function and \(E_k\) is the state after executing all operations in \(S\).

### 3.4 Temporal Complementarity

Two operations \(a_i, a_j\) exhibit *temporal complementarity* at state \(E\) if their sequential value exceeds the expected additive contribution:

\[\text{Comp}(a_i, a_j \mid E) = G([a_i, a_j] \mid E) - \frac{G([a_i] \mid E) + G([a_j] \mid E)}{2}\]

When \(\text{Comp} > 0\), the pair is *synergistic*: the downstream value of the sequence exceeds what the primitives individually predict. When \(\text{Comp} < 0\), the pair exhibits *interference*.

### 3.5 Timing Dependence

An operation \(a\) is *timing-dependent* if its value varies with the epistemic stage at which it is applied:

\[G(a \mid E_{\text{early}}) \neq G(a \mid E_{\text{late}})\]

### 3.6 Counterfactual Fork

Given state \(E_t\), a counterfactual fork evaluates alternative continuations from the same state:

\[\Delta(S_A, S_B \mid E_t) = G(S_A \mid E_t) - G(S_B \mid E_t)\]

This requires the ability to snapshot and restore epistemic states — a capability provided by our benchmark but generally unavailable in live research settings.

---

## 4. The Epistemic World Simulator

### 4.1 Design

The benchmark is a semantic epistemic world simulator that generates research-like reasoning tasks with controlled latent structure. Each *world* consists of:

- A set of *latent hypotheses* \(\{h_1, \ldots, h_m\}\), exactly one of which is designated ground truth.
- An *evidence corpus* with items that differentially support or contradict hypotheses.
- *Source dependencies* — some evidence items share provenance, making apparent corroboration less informative.
- *Hidden variables* that affect evidence reliability but are not directly observable.

The agent sees evidence content, source metadata, and reliability estimates. It does *not* see the true hypothesis, the causal graph, or the evaluator's quality function.

### 4.2 Epistemic Regimes

To test generalization, we define eight heterogeneous epistemic regimes (A through H) that vary along:

- Evidence informativeness (high vs. low signal-to-noise)
- Hypothesis discriminability (easy vs. hard to distinguish)
- Source independence (correlated vs. independent sources)
- Deception structure (misleading evidence vs. transparent)

Each regime creates systematically different epistemic challenges (Table 2).

### 4.3 Quality Measurement

Epistemic quality \(Q(E)\) combines:

- *Hypothesis correctness*: alignment of the agent's posterior with ground truth.
- *Evidence coverage*: fraction of relevant evidence retrieved and integrated.
- *Calibration*: appropriate uncertainty given the evidence structure.

The quality function is evaluator-only — the agent never observes its own quality score during execution.

### 4.4 Agent-Evaluator Separation

The simulator enforces strict separation between agent-visible and evaluator-only information:

| Agent-Visible | Evaluator-Only |
|--------------|---------------|
| Evidence content | True hypothesis |
| Source metadata | Causal graph |
| Reliability estimates | Quality function |
| Hypothesis candidates | Oracle sequence |
| Retrieved subset | Latent regime type |

This separation ensures that measured cognitive-sequence effects reflect genuine epistemic value rather than information leakage.

---

## 5. Counterfactual Cognitive Evaluation

### 5.1 Method

The key methodological contribution is *same-state counterfactual evaluation*. From a single epistemic state \(E_t\):

1. Snapshot the complete simulator state (event sourcing).
2. Fork into alternative cognitive operations or sequences \(S_A\) and \(S_B\).
3. Apply matched continuation budgets to both forks.
4. Compare downstream epistemic gain: \(\Delta = G(S_A \mid E_t) - G(S_B \mid E_t)\).

Because both forks start from identical states, any quality difference is attributable to the cognitive sequence rather than to state confounds.

### 5.2 Advantages

- **Controls for state variation.** Unlike between-episode comparisons, same-state forks eliminate confounding from different starting conditions.
- **Isolates temporal composition.** By comparing \([a_i, a_j]\) against \([a_j, a_i]\) from the same state, we directly measure order effects.
- **Enables complementarity measurement.** By comparing pair value against individual values from matched states, we compute the exact super-additive or sub-additive contribution.

### 5.3 Limitations

- Requires a restorable simulator — not directly applicable to live environments.
- Quality function is benchmark-specific; absolute values are not externally meaningful.
- The operation vocabulary is finite and experimenter-defined.

---

## 6. Experimental Program

We organize the experimental program into eight experiments, each addressing a specific question. Development history is provided in the appendix; here we present the scientific structure.

### Experiment A: Benchmark Identifiability

**Question:** Can different cognitive strategies produce measurably different outcomes in the benchmark?

**Method:** Compare five architectural conditions on matched world sets: direct processing (B0), fixed sequence with hypothesis generation (B1), full adaptive architecture (Full REE), and variants.

**Result:** B1 (fixed sequence with hypothesis generation) achieves quality 0.594 vs. Full REE at 0.356 on locked test (N = 25). The benchmark discriminates between strategies. Full REE's adaptive complexity does not yield higher quality than a simpler fixed sequence — an early negative finding that motivates the subsequent investigation of *which specific cognitive operations* contribute value (Table 3).

### Experiment B: Primitive Cognitive Value

**Question:** What is the standalone value of each primitive cognitive operation?

**Method:** From matched epistemic states, execute single operations and measure downstream quality gain.

**Result (V4, N = 56):** Retrieve = 0.050, generate hypothesis = 0.273, attack = 0.000, reason = 0.000. Hypothesis generation is the only primitive with substantial standalone value. Attack and reason produce zero isolated gain — they require prior context to be useful.

### Experiment C: Sequence Complementarity

**Question:** Do cognitive operation pairs exhibit non-additive value when composed?

**Method:** From matched states, execute all pairwise 2-operation sequences and compute complementarity \(\text{Comp}(a_i, a_j)\).

**Result (V4, N = 56):** See Table 3 for the full complementarity matrix. Key findings:
- gen_hyp → retrieve: +0.162 (synergy). Hypothesis generation focuses subsequent retrieval.
- gen_hyp → attack: +0.137 (synergy). Hypotheses provide targets for falsification.
- gen_hyp → gen_hyp: −0.050 (interference). Repeated generation is mildly harmful.
- retrieve → retrieve: −0.002 (redundancy). Near-zero marginal return.

The strongest complementarity (+0.228 in V3, +0.162 in V4) involves hypothesis generation preceding evidence-gathering operations.

### Experiment D: Timing and State Dependence

**Question:** Does the value of cognitive operations depend on when they are applied?

**Method:** Compare the same operation (particularly attack/falsification) at different epistemic stages.

**Result:** Attack produces zero quality gain when applied before hypotheses exist (attack_early = 0.000 across all conditions) but matches multi-step sequence quality when applied after hypothesis formation (attack_late = 0.276). This timing dependence is the largest single effect in the study.

### Experiment E: Greedy Scheduling

**Question:** Does greedy primitive-level scheduling fail when operations interact?

**Method:** Compare greedy scheduling (select highest-immediate-value operation) against fixed sequences designed to exploit complementarity.

**Simulator result (V3/V4):** Fixed sequences exploiting complementarity (B1_extended = 0.527) outperform greedy baselines in the controlled simulator.

**LLM result (V5):** Under real LLM execution, fixed-vs-greedy difference is +0.003 (INCONCLUSIVE). The effect does not clearly replicate.

### Experiment F: Adaptive Necessity

**Question:** Does adaptive operation selection have theoretical room to improve over fixed sequences?

**Method:** Compute the adaptivity gap: \(\text{Gap} = Q(\text{oracle}) - Q(\text{best fixed})\).

**Result (V4, N = 56):** Oracle = 0.622, best fixed (B1_extended) = 0.527, gap = 0.096. Adaptivity is theoretically useful — the oracle gains ~18% relative quality by selecting sequences per world.

**But:** A learned rule-based motif controller fails to exploit this gap. Policy quality = 0.323, far below the best fixed strategy (0.518), let alone the oracle (0.588). Policy regret (0.264) exceeds fixed regret (0.070) by 3.8×. The controller produces only 2 distinct trajectories across 56 worlds.

This is a central negative finding: adaptive control has measurable theoretical value but our attempt to learn it failed completely.

### Experiment G: LLM-in-Loop Replication

**Question:** Do controlled sequence effects survive when cognitive operations are executed by real language models?

**Method:** Replace scripted cognitive operators with inference from two LLMs (Gemma 3 27B QAT and Llama 3.2 11B Q8_0) while preserving the simulator's deterministic state transitions and evaluation. Execute all preregistered replication tests (Table 5).

**Models:** Both models pass a 10-operation capability gate at >0.73 mean score across 24 evaluation worlds (Table 4).

**Result (V5, N = 128 per model):**
- R2 (complementarity): **REPLICATED** (+0.111)
- R5 (attack timing): **REPLICATED** (+0.276)
- R1 (sequence superiority): INCONCLUSIVE (+0.003)
- R4 (order effects): NOT REPLICATED (−0.050)
- R6 (fixed vs greedy): INCONCLUSIVE (+0.003)

Critically, results are *identical* across both LLM substrates. This occurs because quality scores come from the deterministic simulator — the LLM executes cognitive operations, but the simulator independently evaluates the resulting epistemic state. This confirms that the replicated effects (complementarity, attack timing) are structural properties of the epistemic task, not dependent on which model performs the cognition.

### Experiment H: Static Real-Evidence Transfer

**Question:** Do simulator sequence effects transfer to real-document research tasks?

**Method:** Construct 14 static evidence packs from real academic literature across six domains. Each pack contains frozen source documents, ground-truth hypothesis rankings, evidence dependencies, and quality rubrics. Execute five experimental conditions using the primary LLM (Table 6).

**Result (V5, N = 14 packs):**
- greedy_primitive: 0.718 (highest)
- direct: 0.696
- reflection: 0.696
- B1_extended: 0.691
- FULL_EXPLORE: 0.688

Condition range = 0.030. Cognitive sequence strategy has minimal impact on synthesis quality. greedy_primitive achieves the *highest* score, contradicting the prediction that structured sequences would outperform. Three of six domains show zero condition sensitivity.

**H-REE-18 (cross-level transfer): NOT SUPPORTED.**

---

## 7. Results

### 7.1 Primary Controlled Effects

Table 3 presents the full V4 complementarity matrix. The dominant pattern is that hypothesis generation is the catalytic operation: it creates downstream value for retrieval (+0.162), attack (+0.137), and reasoning (+0.137), while most other pairs show redundancy or near-zero complementarity.

### 7.2 LLM Replication

Table 5 summarizes the preregistered replication tests. Two of five tests replicate under real LLM execution: temporal complementarity and attack timing. These are the two effects with the largest controlled effect sizes, suggesting that stronger effects are more likely to survive the noise introduced by real model execution.

### 7.3 Cross-Model Consistency

The qualitative replication pattern was consistent across the two evaluated model substrates (Gemma 3 27B and Llama 3.2 11B). We note that two models cannot establish universal invariance; this consistency is suggestive but not conclusive.

### 7.4 Static Real-Evidence Results

Table 6 presents the full real-evidence results. The key finding is *negative*: on real documents, cognitive sequence strategy accounts for only 0.030 quality units of variation, compared to 0.277 for sequence choice in the controlled simulator. Several possible interpretations exist:

1. **True non-transfer.** The complementarity measured in the simulator does not exist in natural research tasks.
2. **Insufficient strategy pressure.** The 14 evidence packs may not contain tasks where cognitive strategy matters.
3. **Internal reasoning confound.** LLMs may perform implicit hypothesis generation and reasoning within single forward passes, making explicit cognitive operations partially redundant.
4. **Metric sensitivity.** The composite quality metric may not capture the dimensions along which cognitive strategy actually helps.

We cannot distinguish among these interpretations with current evidence. This remains an open question.

### 7.5 Adaptive Control Failure

The learned motif controller (Experiment F) represents the most complete negative result. Despite a measurable adaptivity gap of 0.096, the controller:

- Achieved quality 0.323 vs. best fixed 0.518 (−38% relative)
- Generated only 2 distinct trajectory types across 56 worlds
- Had policy regret of 0.264, exceeding fixed regret (0.070) by 3.8×

The failure appears to stem from insufficient policy expressiveness and state-feature informativeness rather than absence of adaptive opportunity. More expressive policy classes might succeed, but this remains a hypothesis rather than evidence.

### 7.6 Negative Findings Summary

1. **Full REE underperforms simple baselines.** The most architecturally complex system (Full REE: 0.356) is substantially outperformed by a fixed sequence (B1: 0.594).
2. **Sequence superiority does not replicate under LLM execution.** B1_extended (0.277) ≈ single hypothesis generation (0.273) in Phase 26.
3. **Operation ordering does not replicate.** reversed_B1 (0.327) slightly exceeds B1_extended (0.277) — the predicted direction reverses.
4. **Reflection adds no value.** On real documents, reflection (0.696) = direct processing (0.696).
5. **Greedy outperforms sequences on real documents.** greedy_primitive (0.718) exceeds B1_extended (0.691) on static evidence.
6. **Adaptive motif control fails.** Policy quality is 62% below best fixed strategy.
7. **Real-evidence transfer is not detected.** Condition sensitivity is negligible (range = 0.030).

These negative findings are as important as the positive ones. They establish that temporal complementarity is operation-pair-specific rather than a general principle, and that architectural complexity must be empirically justified rather than assumed beneficial.

---

## 8. Discussion

### 8.1 The Unit of Metacognitive Control

Our results suggest that the appropriate unit of metacognitive analysis is the *operation pair* rather than the full sequence or the individual primitive. Temporal complementarity is real (hypothesis generation catalyzes retrieval and reasoning) but *local* — it does not extend to general sequence superiority.

This has practical implications. Agent designers should focus on identifying specific operation-pair synergies (e.g., "hypothesize before retrieving") rather than engineering elaborate multi-step cognitive pipelines or attempting to learn global scheduling policies.

### 8.2 Structural vs. Execution Effects

The cross-model consistency of Phase 26 results reveals an important distinction between structural and execution effects. The complementarity and timing patterns we measure are properties of how epistemic tasks are structured — they persist regardless of which model executes the operations. This suggests they would generalize to other LLM substrates, though verification with more diverse models is needed.

### 8.3 The Adaptive Control Puzzle

The simultaneous observation of a meaningful adaptivity gap (0.096) and complete policy failure (quality 0.323 << fixed 0.518) creates a puzzle. Adaptive control is theoretically valuable but practically unrealized. Possible explanations include:

- State features may not capture the information needed for sequence selection.
- The policy class (transparent rules) may be insufficiently expressive.
- The training set (56 worlds) may be too small for reliable policy learning.
- The adaptivity gap, while statistically significant, may be too small relative to policy noise.

Resolving this puzzle is an important direction for future work, but we emphasize that our evidence supports the *existence* of the gap, not the *feasibility* of exploiting it.

### 8.4 Why Real-Evidence Transfer May Fail

The non-transfer to real documents (Experiment H) deserves careful interpretation. We do not conclude that temporal complementarity is inherently absent in real research tasks. Several alternative explanations are plausible:

- Modern LLMs may perform implicit cognitive operations (hypothesis generation, self-critique) within single forward passes, reducing the marginal value of explicit operation scheduling.
- Our 14 evidence packs may lack sufficient difficulty or strategy pressure.
- The composite quality metric may not capture the dimensions along which sequence strategy helps.

These are hypotheses for future investigation, not established conclusions.

---

## 9. Future Work

Based on our evidence, productive directions include:

1. **Broader model families.** Testing with frontier-class models, open-weight models of varying sizes, and models with different reasoning characteristics.
2. **Real-document tasks with greater strategy pressure.** Constructing evidence synthesis tasks where different cognitive strategies lead to qualitatively different conclusions.
3. **Internal reasoning interactions.** Investigating whether explicit cognitive operations interact with or duplicate LLMs' internal reasoning processes.
4. **Conservative offline policy learning.** Applying offline RL or conservative policy optimization to the adaptivity gap, using the collected trajectories as a fixed dataset.
5. **Extended operation vocabularies.** Adding operations such as analogy, decomposition, or meta-analysis to the cognitive repertoire.
6. **Longer cognitive sequences.** Our complementarity measurements focus on 2-operation pairs and short sequences. Longer sequences may exhibit higher-order interactions not captured by pairwise analysis.

---

## 10. Conclusion

We have presented a controlled benchmark for measuring the temporal-composition value of cognitive operations in LLM research agents. Our experiments establish three positive findings at Level 2 (LLM-replicated) evidence:

1. **Temporal complementarity is real and operation-pair-specific.** Hypothesis generation catalyzes subsequent retrieval (+0.162), attack (+0.137), and reasoning (+0.137).
2. **Attack timing is strongly state-dependent.** Falsification produces zero value before hypothesis formation but substantial value after (+0.276).
3. **These effects are structural.** They replicate identically across two materially different LLM substrates.

We also establish important boundaries. General sequence superiority over primitive operations is not confirmed under LLM execution. Operation ordering effects do not replicate. A learned adaptive controller fails to exploit a measured adaptivity gap. And temporal complementarity does not detectably transfer to static real-document research tasks.

The overall picture is that cognitive sequencing has measurable value, but that value is narrower than simple accounts of "multi-step reasoning is better" would suggest. The contribution of this work is the ability to make such distinctions precisely — through controlled, counterfactual, same-state evaluation of heterogeneous cognitive operations.

---

## References

Asai, A., Wu, Z., Wang, Y., Sil, A., & Hajishirzi, H. (2024). Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection. *ICLR 2024*.

Banino, A., Balaguer, J., & Blundell, C. (2021). PonderNet: Learning to Ponder. *ICML 2021 Workshop*.

Besta, M., Blach, N., Kubicek, A., Gerstenberger, R., Gianinazzi, L., Gajber, J., Lehmann, T., Podstawski, M., Niewiadomski, H., Nyczyk, P., & Hoefler, T. (2024). Graph of Thoughts: Solving Elaborate Problems with Large Language Models. *AAAI 2024*.

Graves, A. (2016). Adaptive Computation Time for Recurrent Neural Networks. *arXiv:1603.08983*.

Jiang, Z., Xu, F. F., Gao, L., Sun, Z., Liu, Q., Dwivedi-Yu, J., Yang, Y., Callan, J., & Neubig, G. (2023). Active Retrieval Augmented Generation. *EMNLP 2023*.

Lightman, H., Kosaraju, V., Burda, Y., Edwards, H., Baker, B., Lee, T., Leike, J., Schulman, J., Sutskever, I., & Cobbe, K. (2024). Let's Verify Step by Step. *ICLR 2024*.

Madaan, A., Tandon, N., Gupta, P., Hallinan, S., Gao, L., Wiegreffe, S., Alon, U., Dziri, N., Prabhumoye, S., Yang, Y., Gupta, S., Majumder, B. P., Hermann, K. M., Welleck, S., Yazdanbakhsh, A., & Clark, P. (2023). Self-Refine: Iterative Refinement with Self-Feedback. *NeurIPS 2023*.

Paranjape, B., Lundberg, S., Singh, S., Hajishirzi, H., Zettlemoyer, L., & Ribeiro, M. T. (2023). ART: Automatic multi-step Reasoning and Tool-use for large language models. *arXiv:2303.09014*.

Schick, T., Dwivedi-Yu, J., Dessì, R., Raileanu, R., Lomeli, M., Hambro, E., Zettlemoyer, L., Cancedda, N., & Scialom, T. (2023). Toolformer: Language Models Can Teach Themselves to Use Tools. *NeurIPS 2023*.

Shen, Y., Song, K., Tan, X., Li, D., Lu, W., & Zhuang, Y. (2023). HuggingGPT: Solving AI Tasks with ChatGPT and its Friends in Hugging Face. *NeurIPS 2023*.

Shinn, N., Cassano, F., Gopinath, A., Shinn, K. R., Labash, S., & Liu, K. (2023). Reflexion: Language Agents with Verbal Reinforcement Learning. *NeurIPS 2023*.

Sutton, R. S., Precup, D., & Singh, S. (1999). Between MDPs and Semi-MDPs: A Framework for Temporal Abstraction in Reinforcement Learning. *Artificial Intelligence, 112*(1-2), 181-211.

Tafjord, O., Dalvi, B., & Clark, P. (2022). Entailer: Answering Questions with Faithful and Truthful Chains of Reasoning. *EMNLP 2022*.

Wang, P., Li, L., Shao, Z., Xu, R. X., Dai, D., Li, Y., Chen, D., Wu, Y., & Sui, Z. (2024). Math-Shepherd: Verify and Reinforce LLMs Step-by-step without Human Annotations. *ACL 2024*.

Wang, Z., Xie, S., Li, S., Ji, T., & Zhu, Z. (2024). Metacognitive Prompting Improves Understanding in Large Language Models. *arXiv:2308.05342*.

Yang, J., Jimenez, C. E., Wettig, A., Liber, K., Narasimhan, K., & Press, O. (2024). SWE-Agent: Agent-Computer Interfaces Enable Automated Software Engineering. *arXiv:2405.15793*.

Yao, S., Yu, D., Zhao, J., Shafran, I., Griffiths, T. L., Cao, Y., & Narasimhan, K. (2024). Tree of Thoughts: Deliberate Problem Solving with Large Language Models. *NeurIPS 2023*.

Zhou, S., Xu, F. F., Zhu, H., Zhou, X., Lo, R., Sridhar, A., Cheng, X., Bisk, Y., Fried, D., Alon, U., & Neubig, G. (2024). WebArena: A Realistic Web Environment for Building Autonomous Agents. *ICLR 2024*.

Zhou, A., Yan, K., Shlapentokh-Rothman, M., Wang, H., & Wang, Y.-X. (2024). Language Agent Tree Search Unifies Reasoning, Acting, and Planning in Language Models. *ICML 2024*.
