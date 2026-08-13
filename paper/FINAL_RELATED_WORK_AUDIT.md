# Final Related Work Audit (August 2026)

## Category 1: Query Rewriting and Hypothesis-Conditioned Retrieval

| Work | Classification | Overlap | Distinction |
|------|---------------|---------|-------------|
| Query2Doc (Wang et al., 2023) | MECHANISM OVERLAP | Generates pseudo-documents to expand queries | Evaluates retrieval only; does not trace downstream reasoning effects |
| HyDE (Gao et al., 2023) | DIRECT PRIOR ART | Generates hypothetical documents for dense retrieval | Evaluates retrieval quality; does not evaluate end-to-end task utility or compare against generic expansion |
| Step-Back Prompting (Zheng et al., 2024) | CONCEPTUAL NEIGHBOR | Uses abstracted questions for retrieval | Evaluates task accuracy; does not decompose retrieval vs reasoning stages |
| Self-RAG (Asai et al., 2024) | MECHANISM OVERLAP | Adaptive retrieval with self-reflection | Optimizes retrieval decisions; does not experimentally manipulate artifact content |

**Our distinction:** We do not propose a new retrieval method. We experimentally audit whether improved retrieval from intermediate artifacts translates to improved reasoning, finding that it does not universally do so.

## Category 2: Adaptive RAG / Retrieval Utility

| Work | Classification | Overlap | Distinction |
|------|---------------|---------|-------------|
| FLARE (Jiang et al., 2023) | CONCEPTUAL NEIGHBOR | Active retrieval during generation | Focuses on when to retrieve; we focus on what retrieval does to downstream quality |
| Adaptive-RAG (Jeong et al., 2024) | CONCEPTUAL NEIGHBOR | Routes queries by complexity | Optimizes retrieval strategy; does not evaluate the sign of retrieval's downstream effect |
| IRCoT (Trivedi et al., 2023) | MECHANISM OVERLAP | Interleaves retrieval and chain-of-thought | Evaluates combined performance; does not isolate retrieval's causal contribution |

**Our distinction:** These works assume retrieval is beneficial and optimize when/how to do it. We question whether retrieval improvement is reliably beneficial.

## Category 3: RAG Distraction / Context Conflict

| Work | Classification | Overlap | Distinction |
|------|---------------|---------|-------------|
| When Not to Trust LLMs (Chen et al., 2024) | DIRECT PRIOR ART | Studies when retrieved context harms generation | Focuses on irrelevant/contradictory context; we show harm from relevant evidence correctly retrieved |
| Lost in the Middle (Liu et al., 2024) | EVALUATION OVERLAP | Position effects in long context | Studies attention distribution; we study task-structure-dependent integration failure |
| Noise in RAG (Cuconasu et al., 2024) | MECHANISM OVERLAP | Studies distractor documents in RAG | Adds noise to retrieval; we show harm from improved retrieval |

**Our distinction:** Prior distraction work shows that BAD retrieval hurts. We show that IMPROVED retrieval (more gold evidence) can also hurt, depending on task structure. This is a different finding.

## Category 4: LLM Agent Evaluation

| Work | Classification | Overlap | Distinction |
|------|---------------|---------|-------------|
| AgentBench (Liu et al., 2024) | EVALUATION OVERLAP | Benchmarks agent capabilities | End-to-end evaluation; does not decompose pipeline stages |
| ToolBench (Qin et al., 2024) | DISTINCT | Tool use evaluation | Different focus (tool selection vs cognitive artifacts) |
| GAIA (Mialon et al., 2024) | EVALUATION OVERLAP | Multi-step reasoning benchmark | Evaluates final answers; does not audit intermediate artifacts |

**Our distinction:** We do not benchmark overall agent capability. We audit the causal contribution of one specific pipeline component.

## Category 5: Counterfactual / Causal Agent Evaluation

| Work | Classification | Overlap | Distinction |
|------|---------------|---------|-------------|
| Causal Abstraction (Geiger et al., 2024) | CONCEPTUAL NEIGHBOR | Causal analysis of neural network components | Applies to internal representations; we apply to pipeline stages |
| Counterfactual Skill Evaluation | CONCEPTUAL NEIGHBOR | Evaluates adding/removing agent skills | We randomize artifact content rather than skill presence |

**Our distinction:** We use randomized content interventions (real vs shuffled vs neutral vs generic) rather than presence/absence ablations, providing finer-grained causal evidence about WHAT matters in the artifact.

## Novelty Statement (verified against audit)

> Prior work has studied hypothesis-conditioned retrieval (HyDE), query rewriting (Query2Doc), adaptive retrieval (FLARE, Self-RAG), and context distraction effects in RAG. We use matched randomized interventions on intermediate artifact content and follow their effects through query formation, evidence acquisition, and final task performance under equalized compute. This reveals cases where retrieval improvements reverse sign downstream — a finding distinct from prior distraction work, which shows harm from bad retrieval rather than from improved retrieval.

## Assessment

The novelty survives the audit. The closest work (HyDE) proposes a retrieval method and evaluates retrieval quality. We evaluate end-to-end utility of the same type of intervention and find it dissociates. No existing work (as of August 2026) systematically shows that improved gold evidence recall can harm task performance in a controlled, preregistered design.
