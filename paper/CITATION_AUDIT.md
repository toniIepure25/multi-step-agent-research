# Citation Audit

Every citation used in the manuscript, with the claim it supports and verification status.

| # | Paper | Year | Venue/Status | Claim Supported | Primary Source | Verified |
|---|-------|------|-------------|----------------|---------------|---------|
| C1 | Asai et al., "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection" | 2024 | ICLR 2024 | State-dependent retrieval decisions in LLM agents | Yes | SAFE |
| C2 | Jiang et al., "Active Retrieval Augmented Generation" (FLARE) | 2023 | EMNLP 2023 | Adaptive retrieval based on generation confidence | Yes | SAFE |
| C3 | Yao et al., "Tree of Thoughts: Deliberate Problem Solving with Large Language Models" | 2024 | NeurIPS 2023 | Multi-path exploration of reasoning strategies | Yes | SAFE |
| C4 | Besta et al., "Graph of Thoughts: Solving Elaborate Problems with Large Language Models" | 2024 | AAAI 2024 | Graph-structured reasoning with aggregation | Yes | SAFE |
| C5 | Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning" | 2023 | NeurIPS 2023 | Self-reflection for iterative agent improvement | Yes | SAFE |
| C6 | Zhou et al., "Language Agent Tree Search Unifies Reasoning, Acting, and Planning in Language Models" (LATS) | 2024 | ICML 2024 | Search over reasoning trajectories | Yes | SAFE |
| C7 | Madaan et al., "Self-Refine: Iterative Refinement with Self-Feedback" | 2023 | NeurIPS 2023 | Iterative self-improvement without external feedback | Yes | SAFE |
| C8 | Schick et al., "Toolformer: Language Models Can Teach Themselves to Use Tools" | 2023 | NeurIPS 2023 | LLMs learning to schedule tool use | Yes | SAFE |
| C9 | Paranjape et al., "ART: Automatic multi-step Reasoning and Tool-use for large language models" | 2023 | arXiv 2023 | Automatic reasoning with tool selection | Yes | SAFE |
| C10 | Lightman et al., "Let's Verify Step by Step" | 2024 | ICLR 2024 | Process reward models for step-level evaluation | Yes | SAFE |
| C11 | Wang et al., "Math-Shepherd: Verify and Reinforce LLMs Step-by-step without Human Annotations" | 2024 | ACL 2024 | Automated step-level verification | Yes | SAFE |
| C12 | Sutton et al., "Between MDPs and Semi-MDPs: A Framework for Temporal Abstraction in Reinforcement Learning" | 1999 | Artificial Intelligence | Options/temporal abstraction in RL | Yes | SAFE |
| C13 | Graves, "Adaptive Computation Time for Recurrent Neural Networks" | 2016 | arXiv 2016 | Variable computation based on input difficulty | Yes | SAFE |
| C14 | Banino et al., "PonderNet: Learning to Ponder" | 2021 | ICML 2021 Workshop | Learned halting for variable computation | Yes | SAFE |
| C15 | Shen et al., "HuggingGPT: Solving AI Tasks with ChatGPT and its Friends in Hugging Face" | 2023 | NeurIPS 2023 | Hierarchical multi-model orchestration | Yes | SAFE |
| C16 | Wang et al., "Voyager: An Open-Ended Embodied Agent with Large Language Models" | 2023 | arXiv 2023 | Open-ended skill acquisition | Yes | SAFE |
| C17 | Yang et al., "SWE-Agent: Agent-Computer Interfaces Enable Automated Software Engineering" | 2024 | arXiv 2024 | Multi-step agent decision-making | Yes | SAFE |
| C18 | Zhou et al., "WebArena: A Realistic Web Environment for Building Autonomous Agents" | 2024 | ICLR 2024 | Web agent benchmark | Yes | SAFE |
| C19 | Tafjord et al., "Entailer: Answering Questions with Faithful and Truthful Chains of Reasoning" | 2022 | EMNLP 2022 | Faithful reasoning chains | Yes | SAFE |

## Novelty Claim Verification

The claim "We did not identify prior work that combines controlled same-state counterfactual evaluation with explicit measurement of downstream complementarity among heterogeneous epistemic operations" is supported by the prior-art audit (PRIOR_ART_MATRIX.csv). No cited work scores "Yes" on all of: Counterfactual Same-State, Temporal Complementarity, and Heterogeneous Epistemic Ops simultaneously.

**Status: SAFE** — the audit supports the novelty claim as stated. The claim does not assert no related work exists, only that the specific combination is novel.

## Notes

- All venues verified against publicly available proceedings/preprint servers as of 2026-08.
- Some papers have multiple versions (arXiv + conference). Conference venue is listed where available.
- No citation is used to support a stronger claim than the cited paper makes.
