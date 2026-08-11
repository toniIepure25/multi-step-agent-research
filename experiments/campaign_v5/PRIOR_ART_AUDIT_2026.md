# Prior Art Audit — August 2026

**Campaign:** V5, Phase 28
**Date:** 2026-08-10
**Coverage:** 12 mandatory comparison categories, 30+ key works

## Overall Assessment

**Novelty Classification: DISTINCT_CONTRIBUTION**

No existing work provides a controlled counterfactual benchmark for measuring the downstream epistemic value of composing qualitatively different cognitive operations. The closest neighbors each address a subset of the ASAR research question.

### Similarity Distribution

| Category Type | Count |
|---------------|-------|
| MECHANISM_OVERLAP | 5 |
| CLOSE_CONCEPTUAL_PRIOR_ART | 4 |
| EVALUATION_OVERLAP | 3 |
| DIRECT_PRIOR_ART | 0 |

## Category-by-Category Analysis

### 1. Adaptive Test-Time Compute — MECHANISM_OVERLAP

**Key works:**
- Adaptive Computation Time (Graves, 2016)
- AdapTime (2024)
- PonderNet (Banino et al., 2021)
- Scaling LLM Test-Time Compute (Snell et al., 2024)

**Shared:** Both consider state-dependent resource allocation.

**Distinction:** Test-time compute scales *amount* of homogeneous computation. ASAR studies *composition and ordering* of qualitatively different operations. The research objects differ: "how much compute" vs "what kind of cognition and in what order."

### 2. Adaptive Retrieval — CLOSE_CONCEPTUAL_PRIOR_ART

**Key works:**
- Self-RAG (Asai et al., 2024)
- FLARE (Jiang et al., 2023)
- ReaLM-Retrieve (2024)
- Adaptive-RAG (Jeong et al., 2024)

**Shared:** State-dependent retrieval decisions.

**Distinction:** Retrieval is one of several cognitive operations in ASAR. The research object is the *interaction* between retrieval and non-retrieval operations (hypothesis generation, reasoning, attack). Retrieval-only systems study when to retrieve; ASAR studies how retrieval composes with other cognitive types.

### 3. Process Reward Models — EVALUATION_OVERLAP

**Key works:**
- Lightman et al. (2024) — step-level reward in math
- Wang et al. (2024) — Math-Shepherd
- ORM vs PRM comparisons

**Shared:** Step-level evaluation during multi-step reasoning.

**Distinction:** PRMs evaluate steps within a *homogeneous* reasoning chain. ASAR evaluates *heterogeneous* cognitive operations and their interactions. PRMs score quality; ASAR measures downstream epistemic gain of operation-type sequences.

### 4. Reasoning Trajectory Evaluation — MECHANISM_OVERLAP

**Key works:**
- Tree of Thoughts (Yao et al., 2024)
- Graph of Thoughts (Besta et al., 2024)
- Beam Search for Reasoning

**Shared:** Multi-path evaluation, search over cognitive strategies.

**Distinction:** ToT/GoT branch within a single operation type (reasoning). ASAR composes *across* operation types. The search space is qualitatively different: operation-type sequences vs reasoning-step trees.

### 5. Hierarchical LLM Planning — MECHANISM_OVERLAP

**Key works:**
- AdaPlan-H (2024)
- HuggingGPT (Shen et al., 2023)
- Voyager (Wang et al., 2023)

**Shared:** Multi-level decision making about cognitive strategies.

**Distinction:** Hierarchical planning selects sub-tasks. ASAR measures the *value* of cognitive operation sequences independently of hierarchical decomposition. The benchmark measures operation-level effects, not task-level planning quality.

### 6. Agent Planning/Search Decoupling — CLOSE_CONCEPTUAL_PRIOR_ART

**Key works:**
- DecoupleSearch (2024)
- Reflexion (Shinn et al., 2023)
- LATS (Zhou et al., 2024)

**Shared:** Generation != verification principle.

**Distinction:** These decouple planning from execution. ASAR studies the *value of different operation orderings* and provides controlled counterfactual measurement of sequence effects.

### 7. Learned Skills/Options — MECHANISM_OVERLAP

**Key works:**
- Options Framework (Sutton et al., 1999)
- Skill discovery in RL
- TACO (Shiarlis et al., 2018)

**Shared:** Temporal abstraction of primitive actions into reusable sequences.

**Distinction:** Options/skills are learned from reward. ASAR cognitive motifs are empirically derived from sequence analysis. The research question is whether motif composition is *valuable*, not whether motifs can be *learned*.

### 8. Reasoning Strategy Routing — EVALUATION_OVERLAP

**Key works:**
- Mixture of Experts for reasoning
- RouteLLM (Ong et al., 2024)
- LLM routing/cascading systems

**Shared:** Adaptive strategy selection.

**Distinction:** Strategy routing selects a strategy at input time. ASAR studies *sequential composition* of operations within a single task. The temporal dimension (what comes after what) is the key research object.

### 9. Long-Horizon Search Agents — EVALUATION_OVERLAP

**Key works:**
- WebArena (Zhou et al., 2024)
- WebAnchor (2024)
- SWE-Agent (Yang et al., 2024)

**Shared:** Multi-step agent decision-making.

**Distinction:** These are applied agent systems. ASAR provides a *controlled benchmark* for understanding *why* certain cognitive sequences work. Scientific instrument vs engineering system.

### 10. Metacognitive Agents — CLOSE_CONCEPTUAL_PRIOR_ART

**Key works:**
- Metacognitive Prompting (Wang et al., 2024)
- Self-Refine (Madaan et al., 2023)
- Meta-cognitive LLM agents

**Shared:** Self-monitoring and strategy adjustment.

**Distinction:** Metacognitive agents add self-reflection loops and assume adaptive control helps. ASAR *asks whether* metacognitive control actually helps, and found it currently does NOT outperform fixed sequences. This negative result is itself a contribution.

### 11. Dynamic Reasoning Graphs — MECHANISM_OVERLAP

**Key works:**
- Dynamic reasoning graphs (various 2024)
- Entailer (Tafjord et al., 2022)

**Shared:** Structured multi-step reasoning.

**Distinction:** Dynamic graphs construct reasoning structures. ASAR measures the *value of the construction process itself* — which operations to use and in what order.

### 12. Tool-Use Scheduling — CLOSE_CONCEPTUAL_PRIOR_ART

**Key works:**
- Toolformer (Schick et al., 2023)
- ART (Paranjape et al., 2023)

**Shared:** Sequential tool/operation selection.

**Distinction:** Tool scheduling optimizes *when* to call external tools. ASAR's cognitive operations are analogous to tool types, but the benchmark measures *epistemic value* of operation sequences, not tool call efficiency.

## Unique ASAR Contributions (Not Found in Prior Art)

1. **Controlled counterfactual benchmark** for cognitive operation sequences with ground truth
2. **Temporal complementarity measurement** between heterogeneous operations
3. **Quantified adaptivity gap** (state-conditioned oracle vs best fixed sequence)
4. **Documented failure** of adaptive metacognitive control despite measurable adaptivity gap
5. **Order effect measurement** for cognitive operation types
6. **Epistemic regime-specific** optimal sequence identification
7. **Operation-type interference and synergy** quantification
8. **Attack timing state-dependence** discovery

## Research Object Comparison

| Framework | Input | Decision | Measures |
|-----------|-------|----------|----------|
| Test-time compute | Input difficulty | How much compute | Output quality |
| Adaptive retrieval | Reasoning state | Retrieve or not | Retrieval relevance |
| Process reward | Reasoning step | Step quality | Reward signal |
| Hierarchical planning | Task state | Sub-task selection | Task completion |
| **ASAR benchmark** | **Epistemic state** | **Which cognitive operation(s), in what order** | **Counterfactual downstream epistemic gain** |

The ASAR research object is:
```
epistemic state × candidate composition of qualitatively different cognitive operations
→ counterfactually measured downstream epistemic gain
```

This combination is not studied by any single prior work.

## Conclusion

The ASAR epistemic sequence benchmark represents a **DISTINCT_CONTRIBUTION** with mechanism overlaps to several existing research directions but no direct prior art for the specific research object (temporal complementarity of heterogeneous cognitive operations measured counterfactually in a controlled epistemic environment).
