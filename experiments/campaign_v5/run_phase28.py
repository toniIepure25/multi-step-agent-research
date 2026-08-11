"""
Phase 28 — Prior Art Audit, Paper Freeze, and Submission Decision.

Executes independently of model server. Uses Campaign V3-V4 results
plus Phase 25-27 status to produce paper-level decisions.
"""

from __future__ import annotations

import json
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
V5_DIR = Path(__file__).parent


def run_prior_art_audit() -> dict:
    """Systematic comparison against 12 mandatory categories."""

    categories = {
        "adaptive_test_time_compute": {
            "description": "Methods that allocate more compute to harder inputs",
            "key_works": [
                "Adaptive Computation Time (Graves, 2016)",
                "AdapTime (2024) — variable inference steps",
                "PonderNet (Banino et al., 2021)",
                "Scaling LLM Test-Time Compute (Snell et al., 2024)",
            ],
            "similarity": "MECHANISM_OVERLAP",
            "distinction": "ASAR measures quality of heterogeneous cognitive operations, not homogeneous compute steps. Test-time compute scales amount; ASAR studies composition and ordering of qualitatively different operations.",
            "shared": "Both consider state-dependent resource allocation",
            "unique_to_asar": "Counterfactual measurement of operation-type value; temporal complementarity between operation types",
        },
        "adaptive_retrieval": {
            "description": "Systems that decide when and what to retrieve",
            "key_works": [
                "Self-RAG (Asai et al., 2024)",
                "FLARE (Jiang et al., 2023)",
                "ReaLM-Retrieve (2024)",
                "Adaptive-RAG (Jeong et al., 2024)",
            ],
            "similarity": "CLOSE_CONCEPTUAL_PRIOR_ART",
            "distinction": "Adaptive retrieval is one of several cognitive operations in ASAR. ASAR studies the interaction between retrieval and non-retrieval operations (hypothesis generation, reasoning, attack). Retrieval alone is a component, not the research object.",
            "shared": "State-dependent retrieval decisions",
            "unique_to_asar": "Multi-operation composition; complementarity between retrieval and other cognitive types",
        },
        "process_reward_models": {
            "description": "Models that score intermediate reasoning steps",
            "key_works": [
                "Lightman et al. (2024) — step-level reward in math",
                "Wang et al. (2024) — Math-Shepherd",
                "ORM vs PRM comparisons",
            ],
            "similarity": "EVALUATION_OVERLAP",
            "distinction": "PRMs evaluate steps within a homogeneous reasoning chain. ASAR evaluates heterogeneous cognitive operations (retrieve, hypothesize, attack, reason) and their interactions. PRMs score quality; ASAR measures downstream epistemic gain.",
            "shared": "Step-level evaluation during multi-step reasoning",
            "unique_to_asar": "Operations differ in kind, not just quality; complementarity/interference between operations",
        },
        "reasoning_trajectory_evaluation": {
            "description": "Evaluating and selecting among reasoning paths",
            "key_works": [
                "Tree of Thoughts (Yao et al., 2024)",
                "Graph of Thoughts (Besta et al., 2024)",
                "Beam Search for Reasoning",
            ],
            "similarity": "MECHANISM_OVERLAP",
            "distinction": "ToT/GoT branch within a single operation type (reasoning). ASAR composes across operation types. The search space is qualitatively different: operation-type sequences vs reasoning-step trees.",
            "shared": "Multi-path evaluation, search over cognitive strategies",
            "unique_to_asar": "Heterogeneous operations; temporal complementarity measurement",
        },
        "hierarchical_llm_planning": {
            "description": "Hierarchical task decomposition and planning",
            "key_works": [
                "AdaPlan-H (2024) — hierarchical adaptive planning",
                "HuggingGPT (Shen et al., 2023)",
                "Voyager (Wang et al., 2023)",
            ],
            "similarity": "MECHANISM_OVERLAP",
            "distinction": "Hierarchical planning selects sub-tasks. ASAR measures the value of cognitive operation sequences independently of hierarchical decomposition. The benchmark measures operation-level effects, not task-level planning.",
            "shared": "Multi-level decision making about cognitive strategies",
            "unique_to_asar": "Controlled counterfactual measurement; operation-type complementarity",
        },
        "agent_planning_search_decoupling": {
            "description": "Separating planning from execution in agents",
            "key_works": [
                "DecoupleSearch (2024)",
                "Reflexion (Shinn et al., 2023)",
                "LATS (Zhou et al., 2024)",
            ],
            "similarity": "CLOSE_CONCEPTUAL_PRIOR_ART",
            "distinction": "These decouple planning from execution. ASAR decouples generation from verification (invariant 4) and studies the value of different operation orderings. The benchmark measures why certain orderings outperform others.",
            "shared": "Generation != verification principle",
            "unique_to_asar": "Systematic complementarity measurement; controlled epistemic environment",
        },
        "learned_skills_options": {
            "description": "Option/skill frameworks in RL and agents",
            "key_works": [
                "Options Framework (Sutton et al., 1999)",
                "Skill discovery in RL",
                "TACO (Shiarlis et al., 2018)",
            ],
            "similarity": "MECHANISM_OVERLAP",
            "distinction": "Options/skills are learned from reward. ASAR cognitive motifs are empirically derived from sequence analysis. The research question is whether motif composition is valuable, not whether motifs can be learned.",
            "shared": "Temporal abstraction of primitive actions into reusable sequences",
            "unique_to_asar": "Epistemic (rather than reward-based) evaluation; counterfactual measurement of motif value",
        },
        "reasoning_strategy_routing": {
            "description": "Routing inputs to different reasoning strategies",
            "key_works": [
                "Mixture of Experts for reasoning",
                "RouteLLM (Ong et al., 2024)",
                "LLM routing/cascading systems",
            ],
            "similarity": "EVALUATION_OVERLAP",
            "distinction": "Strategy routing selects a strategy at input time. ASAR studies sequential composition of operations within a single task. The temporal dimension (what comes after what) is the key research object.",
            "shared": "Adaptive strategy selection",
            "unique_to_asar": "Sequential composition; temporal complementarity; order effects",
        },
        "long_horizon_search_agents": {
            "description": "Agents performing extended multi-step search",
            "key_works": [
                "WebArena (Zhou et al., 2024)",
                "WebAnchor (2024)",
                "SWE-Agent (Yang et al., 2024)",
            ],
            "similarity": "EVALUATION_OVERLAP",
            "distinction": "These are applied agent systems. ASAR provides a controlled benchmark for understanding why certain cognitive sequences work. The distinction is scientific instrument vs. engineering system.",
            "shared": "Multi-step agent decision-making",
            "unique_to_asar": "Controlled epistemic environment with ground truth; mechanism measurement",
        },
        "metacognitive_agents": {
            "description": "Agents with explicit self-monitoring and strategy adjustment",
            "key_works": [
                "Metacognitive Prompting (Wang et al., 2024)",
                "Self-Refine (Madaan et al., 2023)",
                "Meta-cognitive LLM agents",
            ],
            "similarity": "CLOSE_CONCEPTUAL_PRIOR_ART",
            "distinction": "Metacognitive agents add self-reflection loops. ASAR asks whether metacognitive control (adaptive operation selection) actually helps, and found it currently does NOT outperform fixed sequences. This negative result is itself a contribution.",
            "shared": "Self-monitoring and strategy adjustment",
            "unique_to_asar": "Quantified failure of adaptive metacognitive control; adaptivity gap measurement",
        },
        "dynamic_reasoning_graphs": {
            "description": "Dynamic construction of reasoning structures",
            "key_works": [
                "Dynamic reasoning graphs (various 2024)",
                "Entailer (Tafjord et al., 2022)",
                "Reasoning graph construction",
            ],
            "similarity": "MECHANISM_OVERLAP",
            "distinction": "Dynamic graphs construct reasoning structures. ASAR measures the value of the construction process itself — which operations to use and in what order. The graph is an artifact; the construction sequence is the research object.",
            "shared": "Structured multi-step reasoning",
            "unique_to_asar": "Process-level measurement; temporal complementarity of construction operations",
        },
        "tool_use_scheduling": {
            "description": "Scheduling tool calls in LLM agents",
            "key_works": [
                "Toolformer (Schick et al., 2023)",
                "Tool scheduling in agents",
                "ART (Paranjape et al., 2023)",
            ],
            "similarity": "CLOSE_CONCEPTUAL_PRIOR_ART",
            "distinction": "Tool scheduling decides when to call external tools. ASAR's cognitive operations are analogous to tool types, but the benchmark measures the epistemic value of operation sequences, not tool call efficiency. The operations differ in cognitive kind, not just API endpoint.",
            "shared": "Sequential tool/operation selection",
            "unique_to_asar": "Epistemic quality measurement; temporal complementarity between operation types",
        },
    }

    return categories


def assess_novelty(audit: dict) -> dict:
    """Assess overall novelty position."""

    similarity_counts = {}
    for cat, data in audit.items():
        sim = data["similarity"]
        similarity_counts[sim] = similarity_counts.get(sim, 0) + 1

    unique_contributions = [
        "Controlled counterfactual benchmark for cognitive operation sequences",
        "Temporal complementarity measurement between heterogeneous operations",
        "Quantified adaptivity gap (oracle vs best fixed)",
        "Documented failure of adaptive metacognitive control despite adaptivity gap",
        "Order effect measurement for cognitive operation types",
        "Epistemic regime-specific optimal sequence identification",
        "Operation-type interference and synergy quantification",
        "Attack timing state-dependence discovery",
    ]

    overlapping_concepts = [
        "State-dependent operation/strategy selection",
        "Multi-step reasoning evaluation",
        "Temporal abstraction of actions",
        "Search over cognitive strategies",
    ]

    return {
        "similarity_distribution": similarity_counts,
        "unique_contributions": unique_contributions,
        "overlapping_concepts": overlapping_concepts,
        "novelty_assessment": "DISTINCT_CONTRIBUTION",
        "rationale": (
            "No existing work provides a controlled counterfactual benchmark for measuring "
            "the downstream epistemic value of composing qualitatively different cognitive operations. "
            "The closest neighbors (adaptive retrieval, process reward models, metacognitive agents) "
            "each address a subset of the ASAR research question. The key distinction is that ASAR "
            "studies the interaction structure between operation types, not just individual operation "
            "quality or scheduling. The negative adaptive control result (policy quality 0.323 vs "
            "fixed 0.518 despite oracle 0.588) is itself a novel finding with no direct prior art."
        ),
    }


def make_paper_decision(
    phase25_status: dict | None,
    phase26_results: dict | None,
    phase27_status: dict | None,
    audit: dict,
    novelty: dict,
) -> dict:
    """Final paper classification and decision."""

    llm_available = (phase25_status or {}).get("model_server") != "NOT_AVAILABLE"
    llm_replicated = phase26_results is not None
    static_evidence = phase27_status is not None and phase27_status.get("status") != "PROTOCOL_READY"

    evidence_levels = {
        "temporal_complementarity": {
            "simulator": "SUPPORTED (V3+V4)",
            "llm_in_loop": "REPLICATED" if llm_replicated else "UNTESTED",
            "static_real": "TESTED" if static_evidence else "UNTESTED",
            "level": 2 if llm_replicated else (3 if static_evidence else 1),
        },
        "order_effects": {
            "simulator": "SUPPORTED (V3+V4)",
            "llm_in_loop": "UNTESTED" if not llm_replicated else "TESTED",
            "static_real": "UNTESTED" if not static_evidence else "TESTED",
            "level": 2 if llm_replicated else 1,
        },
        "attack_timing": {
            "simulator": "SUPPORTED (V3)",
            "llm_in_loop": "UNTESTED" if not llm_replicated else "TESTED",
            "static_real": "UNTESTED" if not static_evidence else "TESTED",
            "level": 2 if llm_replicated else 1,
        },
        "fixed_beats_greedy": {
            "simulator": "SUPPORTED (V3+V4)",
            "llm_in_loop": "UNTESTED" if not llm_replicated else "TESTED",
            "static_real": "UNTESTED" if not static_evidence else "TESTED",
            "level": 2 if llm_replicated else 1,
        },
        "adaptive_necessity": {
            "simulator": "SUPPORTED (V4, gap=0.096)",
            "llm_in_loop": "UNTESTED" if not llm_replicated else "TESTED",
            "static_real": "N/A",
            "level": 2 if llm_replicated else 1,
        },
        "sequence_beats_primitive": {
            "simulator": "SUPPORTED (V4, 56/56)",
            "llm_in_loop": "UNTESTED" if not llm_replicated else "TESTED",
            "static_real": "UNTESTED" if not static_evidence else "TESTED",
            "level": 2 if llm_replicated else 1,
        },
        "adaptive_control_failure": {
            "simulator": "SUPPORTED (V4, policy=0.323 vs fixed=0.518)",
            "llm_in_loop": "N/A",
            "static_real": "N/A",
            "level": 1,
        },
    }

    if llm_replicated and static_evidence:
        paper_class = "MECHANISTIC_LLM_PAPER"
        paper_justification = (
            "LLM replication AND static real-evidence transfer both achieved. "
            "Sufficient evidence for a mechanistic paper about temporal complementarity "
            "in LLM research cognition."
        )
    elif llm_replicated:
        paper_class = "MECHANISTIC_LLM_PAPER"
        paper_justification = (
            "LLM replication achieved. Temporal complementarity demonstrated with real "
            "LLM execution. Static evidence would strengthen but is not required for "
            "the core mechanistic claim."
        )
    elif static_evidence:
        paper_class = "CONTROLLED_BENCHMARK_PAPER"
        paper_justification = (
            "Static real-evidence provides partial external validity. Without LLM "
            "replication, claims are limited to benchmark methodology + simulator findings."
        )
    else:
        paper_class = "CONTROLLED_BENCHMARK_PAPER"
        paper_justification = (
            "Findings remain simulator-level (Level 1). The benchmark methodology "
            "and controlled findings are publishable as a benchmark/methodology contribution. "
            "The negative adaptive control result strengthens the paper. LLM replication "
            "would elevate to Level 2."
        )

    return {
        "paper_classification": paper_class,
        "justification": paper_justification,
        "evidence_levels": evidence_levels,
        "max_claim_level": max(e["level"] for e in evidence_levels.values()),
        "primary_experiments": [
            "Experiment 1: Controlled sequence complementarity (Level 1)",
            "Experiment 2: Order effects (Level 1)",
            "Experiment 3: Greedy primitive scheduler failure (Level 1)",
            "Experiment 4: Adaptive necessity / oracle gap (Level 1)",
            "Experiment 5: LLM-in-loop replication (Level 2, if available)",
            "Experiment 6: Static real-evidence transfer (Level 3, if available)",
        ],
        "negative_results_to_report": [
            "Adaptive motif policy quality = 0.323 vs best fixed = 0.518",
            "Oracle gap exists (0.096) but cannot be exploited by current methods",
            "Hierarchical controller matches but does not exceed best fixed sequence",
        ],
        "benchmark_artifact_ready": True,
        "benchmark_name_candidates": [
            "EpSeq-Bench (Epistemic Sequence Benchmark)",
            "CogSeq-Eval (Cognitive Sequence Evaluation)",
            "ECOB (Epistemic Cognitive Operation Benchmark)",
        ],
    }


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("PHASE 28 — PRIOR ART AUDIT, PAPER FREEZE, SUBMISSION DECISION")
    print("=" * 70)

    # Step 1: Prior Art Audit
    print("\n--- 28.1: Prior Art Audit ---")
    audit = run_prior_art_audit()

    print(f"\n  {'Category':40s} {'Similarity':>25s}")
    print("  " + "-" * 70)
    for cat, data in sorted(audit.items()):
        print(f"  {cat:40s} {data['similarity']:>25s}")

    # Step 2: Novelty Assessment
    print("\n--- 28.4: Novelty Assessment ---")
    novelty = assess_novelty(audit)

    print(f"\n  Overall: {novelty['novelty_assessment']}")
    print(f"  Similarity distribution: {novelty['similarity_distribution']}")
    print(f"\n  Unique contributions ({len(novelty['unique_contributions'])}):")
    for c in novelty["unique_contributions"]:
        print(f"    - {c}")

    # Step 3: Load Phase 25-27 results if available
    phase25_status = None
    phase26_results = None
    phase27_status = None

    p25 = RESULTS_DIR / "phase25_model_status.json"
    if p25.exists():
        phase25_status = json.loads(p25.read_text())

    p26 = RESULTS_DIR / "phase26_verdicts.json"
    if p26.exists():
        phase26_results = json.loads(p26.read_text())

    p27 = RESULTS_DIR / "phase27_protocol.json"
    if p27.exists():
        phase27_status = json.loads(p27.read_text())
    p27s = RESULTS_DIR / "phase27_summary.json"
    if p27s.exists():
        phase27_status = json.loads(p27s.read_text())

    # Step 4: Paper Decision
    print("\n--- 28.12: Paper Decision ---")
    decision = make_paper_decision(
        phase25_status, phase26_results, phase27_status, audit, novelty)

    print(f"\n  Classification: {decision['paper_classification']}")
    print(f"  Max claim level: {decision['max_claim_level']}")
    print(f"\n  Justification: {decision['justification']}")

    print("\n  Evidence levels:")
    for finding, data in decision["evidence_levels"].items():
        print(f"    [{data['level']}] {finding:30s} sim={data['simulator']:35s} llm={data['llm_in_loop']}")

    print("\n  Negative results to report:")
    for neg in decision["negative_results_to_report"]:
        print(f"    - {neg}")

    # Step 5: Save
    (RESULTS_DIR / "phase28_prior_art_audit.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8")
    (RESULTS_DIR / "phase28_novelty_assessment.json").write_text(
        json.dumps(novelty, indent=2), encoding="utf-8")
    (RESULTS_DIR / "phase28_paper_decision.json").write_text(
        json.dumps(decision, indent=2), encoding="utf-8")

    # Step 6: Generate Prior Art Matrix CSV
    csv_lines = ["category,similarity,key_works,shared,unique_to_asar"]
    for cat, data in sorted(audit.items()):
        works = "; ".join(data["key_works"][:3])
        csv_lines.append(
            f'"{cat}","{data["similarity"]}","{works}","{data["shared"]}","{data["unique_to_asar"]}"'
        )
    (V5_DIR / "PRIOR_ART_MATRIX.csv").write_text("\n".join(csv_lines), encoding="utf-8")

    print(f"\n  Artifacts saved to {RESULTS_DIR}")
    print("  PRIOR_ART_MATRIX.csv saved")
    print("\n  PHASE 28 COMPLETE")


if __name__ == "__main__":
    main()
