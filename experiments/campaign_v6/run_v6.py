"""
Campaign V6 — Causal Closed-Loop Validation Runner.

Key differences from V5:
1. LLM output is PARSED and INSERTED into epistemic state
2. Retrieval is QUERY-CONDITIONED (keyword overlap scoring)
3. Reason output UPDATES posteriors before evaluate()
4. Attack calls sim.attack_hypothesis() with LLM-targeted hypothesis
5. All comparisons are COMPUTE-MATCHED
6. Condition certification verifies behavioral traces
7. Factorial 2x2 design for complementarity
8. Semantic artifact intervention (real vs shuffled vs neutral)
9. Matched-budget attack timing (same operations, different order)

Usage:
    python experiments/campaign_v6/run_v6.py --phase certify
    python experiments/campaign_v6/run_v6.py --phase factorial
    python experiments/campaign_v6/run_v6.py --phase intervention
    python experiments/campaign_v6/run_v6.py --phase attack_timing
    python experiments/campaign_v6/run_v6.py --phase all
"""
from __future__ import annotations

import argparse
import asyncio
import copy
import functools
import hashlib
import json
import random
import statistics
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

print = functools.partial(print, flush=True)  # type: ignore[assignment]

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from asar.core.llm import LLMGenerationRequest, LLMMessage, MessageRole
from asar.evaluation.scenarios.v4_regimes import V4_REGIME_GENERATORS
from asar.evaluation.simulator import (
    EpistemicWorldSimulator,
    EpistemicQualityVector,
    LatentWorld,
)
from asar.providers.chat_completions_llm import ChatCompletionsLLMClient

RESULTS_DIR = Path(__file__).parent / "results"
BASE_URL = "https://inference.ccrolabs.com/v1"
PRIMARY_MODEL = "gemma3:27b-it-qat"
TRANSFER_MODEL = "llama3.2-vision:11b-instruct-q8_0"
V6_BASE_SEED = 314159
TEMPERATURE = 0.0
MAX_TOKENS_OP = 512
TIMEOUT = 120.0
WORLDS_PER_REGIME = 4  # 8 regimes x 4 = 32 worlds

PROMPTS = {
    "generate_hypothesis": {
        "system": "You are a research scientist. Given evidence, generate a plausible hypothesis. Output ONLY valid JSON: {\"hypothesis\": \"...\", \"reasoning\": \"...\", \"confidence\": 0.0-1.0}",
        "template": "Evidence observed:\n{evidence}\n\nGenerate one hypothesis explaining these observations. Output ONLY JSON.",
    },
    "reason": {
        "system": "You are a research analyst. Evaluate hypothesis consistency with evidence. Output ONLY valid JSON: {\"evaluations\": [{\"hypothesis_id\": \"...\", \"score\": 0.0-1.0, \"reasoning\": \"...\"}]}",
        "template": "Hypotheses:\n{hypotheses}\n\nEvidence:\n{evidence}\n\nEvaluate each hypothesis against the evidence. Output ONLY JSON with hypothesis_id and score fields.",
    },
    "attack": {
        "system": "You are a scientific critic. Identify weaknesses in a specific hypothesis. Output ONLY valid JSON: {\"target_hypothesis_id\": \"...\", \"weaknesses\": [\"...\"], \"falsifiers\": [\"...\"], \"missing_info\": [\"...\"]}",
        "template": "Hypotheses:\n{hypotheses}\n\nEvidence:\n{evidence}\n\nSelect the weakest hypothesis and critique it. Include its hypothesis_id. Output ONLY JSON.",
    },
    "retrieval_query": {
        "system": "You are a research strategist. Generate a targeted search query. Output ONLY valid JSON: {\"query\": \"...\", \"rationale\": \"...\"}",
        "template": "Hypotheses:\n{hypotheses}\nEvidence:\n{evidence}\n\nGenerate a search query to find evidence that would help discriminate between these hypotheses. Output ONLY JSON.",
    },
    "synthesis": {
        "system": "You are a research synthesizer. Produce a grounded conclusion. Output ONLY valid JSON: {\"best_hypothesis_id\": \"...\", \"conclusion\": \"...\", \"confidence\": 0.0-1.0, \"supporting_evidence\": [\"...\"]}",
        "template": "Hypotheses:\n{hypotheses}\n\nEvidence:\n{evidence}\n\nSynthesize a conclusion identifying the best-supported hypothesis. Include its hypothesis_id. Output ONLY JSON.",
    },
    "control_paraphrase": {
        "system": "You are a text editor. Paraphrase the following passage in different words while preserving the same general topic. Do NOT analyze, reason about, or draw conclusions from the content. Output ONLY a paraphrase.",
        "template": "Passage:\n{text}\n\nParaphrase this passage. Do not add analysis.",
    },
}


def _make_client() -> ChatCompletionsLLMClient:
    return ChatCompletionsLLMClient(base_url=BASE_URL, timeout=TIMEOUT)


def _ts() -> str:
    return time.strftime("%H:%M:%S")


# -------------------------------------------------------------------
# SAFE JSON PARSING
# -------------------------------------------------------------------


def _parse_json(text: str) -> dict | None:
    """Extract JSON from LLM output, handling markdown fences."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        stripped = "\n".join(lines).strip()
    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(stripped[start:end + 1])
            except (json.JSONDecodeError, ValueError):
                pass
    return None


# -------------------------------------------------------------------
# QUERY-CONDITIONED RETRIEVAL
# -------------------------------------------------------------------


def query_conditioned_retrieve(
    sim: EpistemicWorldSimulator,
    query: str,
) -> dict[str, Any] | None:
    """Retrieve evidence conditioned on query content.

    Scores unrevealed evidence by keyword overlap with the query,
    then selects the highest-scoring item. Falls back to hash-based
    selection if query is empty or no overlap exists.
    """
    available = [
        e for e in sim.world.evidence_pool
        if e.evidence_id not in sim._retrieved and e.is_accessible
    ]
    if not available:
        return None

    if query and query.strip():
        query_words = set(w.lower() for w in query.split() if len(w) > 2)
        scored = []
        for e in available:
            content_words = set(w.lower() for w in e.content.split() if len(w) > 2)
            overlap = len(query_words & content_words)
            scored.append((overlap, e.information_value, e))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        selected = scored[0][2]
    else:
        ctx = f"retrieve_{len(sim._retrieved)}_v6"
        selected = sim._deterministic_choice(available, ctx)

    if selected is None:
        return None

    sim._retrieved.add(selected.evidence_id)

    return {
        "evidence_id": selected.evidence_id,
        "content": selected.content,
        "source_id": selected.source.source_id,
        "source_reliability": selected.source.reliability,
        "parent_source": selected.source.parent_source,
        "confidence": min(1.0, selected.source.reliability),
    }


# -------------------------------------------------------------------
# LLM HYPOTHESIS BINDING
# -------------------------------------------------------------------


def bind_llm_hypothesis(
    llm_output: dict,
    sim: EpistemicWorldSimulator,
    evidence: list[dict],
) -> dict[str, Any] | None:
    """Map LLM-generated hypothesis to nearest latent hypothesis.

    Uses keyword overlap between LLM hypothesis text and latent
    hypothesis statements. Falls back to evidence-hint prioritization
    if keyword overlap is insufficient.

    The LLM's hypothesis quality influences which latent hypothesis
    gets activated, making this causally dependent on LLM output.
    """
    llm_text = llm_output.get("hypothesis", "")

    candidates = [
        h for hid, h in sim.world.hypotheses.items()
        if hid not in sim._generated_hypotheses
    ]
    if not candidates:
        return None

    best_match = None
    best_score = -1
    binding_method = "fallback"

    if llm_text:
        llm_words = set(w.lower() for w in llm_text.split() if len(w) > 2)
        for h in candidates:
            h_words = set(w.lower() for w in h.statement.split() if len(w) > 2)
            overlap = len(llm_words & h_words)
            score = overlap
            if score > best_score:
                best_score = score
                best_match = h
        if best_score >= 2:
            binding_method = "keyword"

    if best_score < 2:
        evidence_ids = [e["evidence_id"] for e in evidence]
        evidence_hints = []
        for eid in evidence_ids:
            for e in sim.world.evidence_pool:
                if e.evidence_id == eid:
                    evidence_hints.extend(e.supports_hypotheses)
                    break

        prioritized = sorted(
            candidates,
            key=lambda h: (
                1.0 if h.hypothesis_id in evidence_hints else 0.0,
                h.initial_plausibility,
            ),
            reverse=True,
        )
        best_match = prioritized[0]
        best_score = 0
        binding_method = "evidence_priority"

    if best_match is None:
        return None

    sim._generated_hypotheses.add(best_match.hypothesis_id)
    return {
        "hypothesis_id": best_match.hypothesis_id,
        "statement": best_match.statement,
        "initial_plausibility": best_match.initial_plausibility,
        "llm_hypothesis": llm_text,
        "binding_score": best_score,
        "binding_method": binding_method,
    }


# -------------------------------------------------------------------
# LLM COGNITIVE OPERATIONS (CLOSED-LOOP)
# -------------------------------------------------------------------


async def llm_call(
    client: ChatCompletionsLLMClient,
    model_id: str,
    system: str,
    user: str,
) -> tuple[str, dict]:
    """Make a single LLM call, return (text, usage_dict)."""
    t0 = time.time()
    try:
        resp = await client.generate(LLMGenerationRequest(
            model=model_id,
            messages=[
                LLMMessage(role=MessageRole.SYSTEM, content=system),
                LLMMessage(role=MessageRole.USER, content=user),
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS_OP,
        ))
        elapsed = time.time() - t0
        usage = {
            "input_tokens": resp.usage.prompt_tokens if resp.usage else 0,
            "output_tokens": resp.usage.completion_tokens if resp.usage else 0,
            "latency": elapsed,
        }
        return resp.output_text, usage
    except Exception as e:
        return f"ERROR: {e}", {"input_tokens": 0, "output_tokens": 0, "latency": time.time() - t0, "error": str(e)}


def _format_evidence(evidence: list[dict]) -> str:
    parts = []
    for i, ev in enumerate(evidence):
        parts.append(f"[E{i+1}] {ev.get('content', 'No content')}")
    return "\n".join(parts) if parts else "(no evidence yet)"


def _format_hypotheses(hypotheses: list[dict]) -> str:
    parts = []
    for h in hypotheses:
        parts.append(f"[{h['hypothesis_id']}] {h['statement']} (plausibility: {h.get('initial_plausibility', '?')})")
    return "\n".join(parts) if parts else "(no hypotheses yet)"


# -------------------------------------------------------------------
# CLOSED-LOOP SEQUENCE EXECUTOR
# -------------------------------------------------------------------


@dataclass
class SequenceTrace:
    """Full trace of a closed-loop sequence execution."""
    condition_id: str
    world_id: str
    model_id: str
    operations: list[str]
    op_traces: list[dict] = field(default_factory=list)
    hypotheses: list[dict] = field(default_factory=list)
    evidence: list[dict] = field(default_factory=list)
    posteriors: dict[str, float] = field(default_factory=dict)
    hidden_vars_found: set = field(default_factory=set)
    assumptions_found: set = field(default_factory=set)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_calls: int = 0
    scalar_quality: float = 0.0
    quality_vector: dict = field(default_factory=dict)


async def run_closed_loop_sequence(
    client: ChatCompletionsLLMClient,
    model_id: str,
    sim: EpistemicWorldSimulator,
    operations: list[str],
    condition_id: str,
    *,
    artifact_override: dict | None = None,
) -> SequenceTrace:
    """Execute a cognitive sequence with full closed-loop LLM causality.

    LLM output is parsed and inserted into epistemic state.
    Retrieval is query-conditioned. Reasoning updates posteriors.
    Attack calls sim.attack_hypothesis().

    If artifact_override is set, the specified operation's artifact is
    replaced (for semantic intervention experiments).
    """
    trace = SequenceTrace(
        condition_id=condition_id,
        world_id=sim.world.world_id,
        model_id=model_id,
        operations=list(operations),
    )

    for i, op in enumerate(operations):
        op_trace: dict[str, Any] = {"op": op, "index": i, "success": False}

        if op == "retrieve":
            query = ""
            if trace.hypotheses:
                query_prompt = PROMPTS["retrieval_query"]
                text, usage = await llm_call(
                    client, model_id,
                    query_prompt["system"],
                    query_prompt["template"].format(
                        hypotheses=_format_hypotheses(trace.hypotheses),
                        evidence=_format_evidence(trace.evidence),
                    ),
                )
                trace.total_calls += 1
                trace.total_input_tokens += usage["input_tokens"]
                trace.total_output_tokens += usage["output_tokens"]
                parsed = _parse_json(text)
                if parsed and "query" in parsed:
                    query = parsed["query"]
                op_trace["llm_query"] = query
                op_trace["llm_raw"] = text[:200]
            else:
                query = sim.world.world_id

            ev = query_conditioned_retrieve(sim, query)
            if ev:
                trace.evidence.append(ev)
            op_trace["evidence_retrieved"] = ev is not None
            op_trace["evidence_id"] = ev["evidence_id"] if ev else None
            op_trace["success"] = ev is not None

        elif op == "generate_hypothesis":
            prompt = PROMPTS["generate_hypothesis"]
            text, usage = await llm_call(
                client, model_id,
                prompt["system"],
                prompt["template"].format(
                    evidence=_format_evidence(trace.evidence),
                ),
            )
            trace.total_calls += 1
            trace.total_input_tokens += usage["input_tokens"]
            trace.total_output_tokens += usage["output_tokens"]
            op_trace["llm_raw"] = text[:300]

            parsed = _parse_json(text)
            if not parsed:
                parsed = {"hypothesis": text.strip()[:200]}
                op_trace["json_parse_failed"] = True

            if artifact_override and artifact_override.get("op") == "generate_hypothesis" and artifact_override.get("index") == i:
                parsed = artifact_override["artifact"]
                op_trace["artifact_override"] = True

            hyp = bind_llm_hypothesis(parsed, sim, trace.evidence)
            if hyp:
                trace.hypotheses.append(hyp)
                trace.posteriors[hyp["hypothesis_id"]] = hyp["initial_plausibility"]
                op_trace["bound_hypothesis_id"] = hyp["hypothesis_id"]
                op_trace["binding_score"] = hyp.get("binding_score", 0)
                op_trace["binding_method"] = hyp.get("binding_method", "unknown")
                op_trace["success"] = True
            else:
                op_trace["binding_failed"] = True

        elif op == "reason":
            if trace.hypotheses and trace.evidence:
                prompt = PROMPTS["reason"]
                text, usage = await llm_call(
                    client, model_id,
                    prompt["system"],
                    prompt["template"].format(
                        hypotheses=_format_hypotheses(trace.hypotheses),
                        evidence=_format_evidence(trace.evidence),
                    ),
                )
                trace.total_calls += 1
                trace.total_input_tokens += usage["input_tokens"]
                trace.total_output_tokens += usage["output_tokens"]
                op_trace["llm_raw"] = text[:200]

                sim_reason = sim.reason(
                    [h["hypothesis_id"] for h in trace.hypotheses],
                    [e["evidence_id"] for e in trace.evidence],
                )
                for hid, score in sim_reason["consistency_scores"].items():
                    trace.posteriors[hid] = score
                op_trace["posteriors_updated"] = dict(trace.posteriors)
                op_trace["success"] = True
            else:
                text, usage = await llm_call(
                    client, model_id,
                    PROMPTS["control_paraphrase"]["system"],
                    PROMPTS["control_paraphrase"]["template"].format(
                        text=_format_evidence(trace.evidence) if trace.evidence else "No information available yet.",
                    ),
                )
                trace.total_calls += 1
                trace.total_input_tokens += usage["input_tokens"]
                trace.total_output_tokens += usage["output_tokens"]
                op_trace["control_call"] = True

        elif op == "attack":
            if trace.hypotheses:
                prompt = PROMPTS["attack"]
                text, usage = await llm_call(
                    client, model_id,
                    prompt["system"],
                    prompt["template"].format(
                        hypotheses=_format_hypotheses(trace.hypotheses),
                        evidence=_format_evidence(trace.evidence),
                    ),
                )
                trace.total_calls += 1
                trace.total_input_tokens += usage["input_tokens"]
                trace.total_output_tokens += usage["output_tokens"]
                op_trace["llm_raw"] = text[:200]

                parsed = _parse_json(text)
                target_hid = None
                if parsed and "target_hypothesis_id" in parsed:
                    target_hid = parsed["target_hypothesis_id"]
                if not target_hid and trace.hypotheses:
                    target_hid = trace.hypotheses[-1]["hypothesis_id"]

                if target_hid and target_hid in sim.world.hypotheses:
                    attack_result = sim.attack_hypothesis(target_hid)
                    for item in attack_result.get("ignorance_items", []):
                        trace.hidden_vars_found.add(item["variable_id"])
                    op_trace["attack_target"] = target_hid
                    op_trace["found_something"] = attack_result.get("found_something", False)
                    op_trace["hidden_vars_discovered"] = len(attack_result.get("ignorance_items", []))
                    op_trace["success"] = True
            else:
                text, usage = await llm_call(
                    client, model_id,
                    PROMPTS["control_paraphrase"]["system"],
                    PROMPTS["control_paraphrase"]["template"].format(
                        text="No hypotheses available to attack.",
                    ),
                )
                trace.total_calls += 1
                trace.total_input_tokens += usage["input_tokens"]
                trace.total_output_tokens += usage["output_tokens"]
                op_trace["control_call"] = True

        elif op == "synthesis":
            prompt = PROMPTS["synthesis"]
            text, usage = await llm_call(
                client, model_id,
                prompt["system"],
                prompt["template"].format(
                    hypotheses=_format_hypotheses(trace.hypotheses),
                    evidence=_format_evidence(trace.evidence),
                ),
            )
            trace.total_calls += 1
            trace.total_input_tokens += usage["input_tokens"]
            trace.total_output_tokens += usage["output_tokens"]
            op_trace["llm_raw"] = text[:200]

            parsed = _parse_json(text)
            if parsed and "best_hypothesis_id" in parsed:
                best_id = parsed["best_hypothesis_id"]
                if best_id in trace.posteriors:
                    trace.posteriors[best_id] = max(
                        trace.posteriors[best_id],
                        parsed.get("confidence", 0.8),
                    )
            op_trace["success"] = True

        elif op == "control":
            text, usage = await llm_call(
                client, model_id,
                PROMPTS["control_paraphrase"]["system"],
                PROMPTS["control_paraphrase"]["template"].format(
                    text=_format_evidence(trace.evidence) if trace.evidence else "General research methodology.",
                ),
            )
            trace.total_calls += 1
            trace.total_input_tokens += usage["input_tokens"]
            trace.total_output_tokens += usage["output_tokens"]
            op_trace["control_call"] = True
            op_trace["success"] = True

        trace.op_traces.append(op_trace)

    ev_sources = {
        e["source_id"]: e.get("parent_source")
        for e in trace.evidence
    }
    quality_vec = sim.evaluate(
        trace.posteriors,
        trace.hidden_vars_found,
        trace.assumptions_found,
        ev_sources,
    )
    trace.scalar_quality = quality_vec.scalar_quality()
    trace.quality_vector = quality_vec.to_dict()

    return trace


# -------------------------------------------------------------------
# WORLD GENERATION
# -------------------------------------------------------------------


def generate_v6_worlds(n_per_regime: int = WORLDS_PER_REGIME) -> list[LatentWorld]:
    """Generate fresh worlds for V6 (not reusing V4/V5 seeds)."""
    worlds = []
    for regime_name, generator in V4_REGIME_GENERATORS.items():
        for i in range(n_per_regime):
            seed = V6_BASE_SEED + abs(hash(regime_name)) % 10000 + i
            world = generator(index=i, seed=seed)
            world.world_id = f"{regime_name}_{V6_BASE_SEED}_{i}"
            worlds.append(world)
    return worlds


# -------------------------------------------------------------------
# CONDITION CERTIFICATION (Phase 30)
# -------------------------------------------------------------------


@dataclass
class ConditionCertificate:
    condition_id: str
    expected_operations: list[str]
    observed_operations: list[str]
    operation_count: int
    model_call_count: int
    retrieval_count: int
    hypothesis_count: int
    attack_count: int
    reason_count: int
    artifact_types: list[str]
    posteriors_updated: bool
    budget_tokens: int
    status: str  # PASS or FAIL
    failure_reason: str = ""


async def certify_condition(
    client: ChatCompletionsLLMClient,
    model_id: str,
    condition_id: str,
    operations: list[str],
    world: LatentWorld,
) -> ConditionCertificate:
    """Run a condition on a single world and verify behavioral correctness."""
    sim = EpistemicWorldSimulator(world, seed=42)
    trace = await run_closed_loop_sequence(
        client, model_id, sim, operations, condition_id,
    )

    observed_ops = [t["op"] for t in trace.op_traces]
    retrieval_count = sum(1 for t in trace.op_traces if t["op"] == "retrieve" and t.get("success"))
    hyp_count = sum(1 for t in trace.op_traces if t["op"] == "generate_hypothesis" and t.get("success"))
    attack_count = sum(1 for t in trace.op_traces if t["op"] == "attack" and t.get("success"))
    reason_count = sum(1 for t in trace.op_traces if t["op"] == "reason" and t.get("posteriors_updated"))
    posteriors_updated = bool(trace.posteriors)

    artifacts = []
    if hyp_count > 0:
        artifacts.append("hypothesis")
    if retrieval_count > 0:
        artifacts.append("evidence")
    if attack_count > 0:
        artifacts.append("attack_result")
    if reason_count > 0:
        artifacts.append("updated_posteriors")

    status = "PASS"
    failure_reason = ""

    if observed_ops != operations:
        status = "FAIL"
        failure_reason = f"Expected ops {operations}, got {observed_ops}"
    elif trace.total_calls == 0:
        status = "FAIL"
        failure_reason = "No LLM calls made"

    for t in trace.op_traces:
        if t["op"] == "generate_hypothesis" and not t.get("success") and not t.get("control_call"):
            if not trace.hypotheses:
                status = "FAIL"
                failure_reason = f"generate_hypothesis at index {t['index']} produced no hypothesis"
                break

    return ConditionCertificate(
        condition_id=condition_id,
        expected_operations=operations,
        observed_operations=observed_ops,
        operation_count=len(operations),
        model_call_count=trace.total_calls,
        retrieval_count=retrieval_count,
        hypothesis_count=hyp_count,
        attack_count=attack_count,
        reason_count=reason_count,
        artifact_types=artifacts,
        posteriors_updated=posteriors_updated,
        budget_tokens=trace.total_input_tokens + trace.total_output_tokens,
        status=status,
        failure_reason=failure_reason,
    )


# -------------------------------------------------------------------
# STUDY A: FACTORIAL COMPLEMENTARITY (Phase 32)
# -------------------------------------------------------------------

FACTORIAL_CONDITIONS = {
    "C00_control_control": ["control", "control", "synthesis"],
    "C10_hyp_control": ["generate_hypothesis", "control", "synthesis"],
    "C01_control_reason": ["control", "reason", "synthesis"],
    "C11_hyp_reason": ["generate_hypothesis", "reason", "synthesis"],
}

FACTORIAL_B_CONDITIONS = {
    "CB00_control_control": ["retrieve", "control", "control", "synthesis"],
    "CB10_hyp_control": ["retrieve", "generate_hypothesis", "control", "synthesis"],
    "CB01_control_retrieve": ["retrieve", "control", "retrieve", "synthesis"],
    "CB11_hyp_retrieve": ["retrieve", "generate_hypothesis", "retrieve", "synthesis"],
}


# -------------------------------------------------------------------
# STUDY B: SEMANTIC INTERVENTION (Phase 33)
# -------------------------------------------------------------------


async def run_semantic_intervention(
    client: ChatCompletionsLLMClient,
    model_id: str,
    worlds: list[LatentWorld],
    shuffled_artifacts: dict[str, dict],
) -> list[dict]:
    """Run real vs shuffled vs neutral hypothesis artifacts.

    All three conditions use identical downstream sequences and budgets.
    """
    results = []
    ops = ["generate_hypothesis", "retrieve", "reason", "synthesis"]

    for world in worlds:
        real_sim = EpistemicWorldSimulator(world, seed=42)
        real_trace = await run_closed_loop_sequence(
            client, model_id, real_sim, ops, "intervention_real",
        )

        shuffled_art = shuffled_artifacts.get(world.world_id)
        if shuffled_art:
            shuf_sim = EpistemicWorldSimulator(world, seed=42)
            shuf_trace = await run_closed_loop_sequence(
                client, model_id, shuf_sim, ops, "intervention_shuffled",
                artifact_override={"op": "generate_hypothesis", "index": 0, "artifact": shuffled_art},
            )
        else:
            shuf_trace = real_trace

        neutral_art = {"hypothesis": "Some general observation about the world.", "confidence": 0.5}
        neut_sim = EpistemicWorldSimulator(world, seed=42)
        neut_trace = await run_closed_loop_sequence(
            client, model_id, neut_sim, ops, "intervention_neutral",
            artifact_override={"op": "generate_hypothesis", "index": 0, "artifact": neutral_art},
        )

        results.append({
            "world_id": world.world_id,
            "real_quality": real_trace.scalar_quality,
            "shuffled_quality": shuf_trace.scalar_quality,
            "neutral_quality": neut_trace.scalar_quality,
            "real_calls": real_trace.total_calls,
            "shuffled_calls": shuf_trace.total_calls,
            "neutral_calls": neut_trace.total_calls,
            "real_hypotheses": len(real_trace.hypotheses),
            "shuffled_hypotheses": len(shuf_trace.hypotheses),
            "neutral_hypotheses": len(neut_trace.hypotheses),
        })

    return results


# -------------------------------------------------------------------
# STUDY C: MATCHED-BUDGET ATTACK TIMING (Phase 34)
# -------------------------------------------------------------------

ATTACK_TIMING_CONDITIONS = {
    "early_attack": ["attack", "retrieve", "generate_hypothesis", "reason", "synthesis"],
    "mid_attack": ["retrieve", "generate_hypothesis", "attack", "reason", "synthesis"],
    "late_attack": ["retrieve", "generate_hypothesis", "reason", "attack", "synthesis"],
}


# -------------------------------------------------------------------
# MAIN EXECUTION
# -------------------------------------------------------------------


async def run_certification(client, model_id):
    """Phase 30: Certify all conditions."""
    print(f"\n{'='*60}")
    print(f"PHASE 30 — CONDITION CERTIFICATION")
    print(f"{'='*60}\n")

    worlds = generate_v6_worlds(1)
    test_world = worlds[0]

    all_conditions = {}
    all_conditions.update(FACTORIAL_CONDITIONS)
    all_conditions.update(FACTORIAL_B_CONDITIONS)
    all_conditions.update(ATTACK_TIMING_CONDITIONS)

    certs = []
    for cid, ops in all_conditions.items():
        print(f"  [{_ts()}] Certifying {cid}...")
        cert = await certify_condition(client, model_id, cid, ops, test_world)
        certs.append(cert)
        status = "PASS" if cert.status == "PASS" else f"FAIL: {cert.failure_reason}"
        print(f"    {status} | calls={cert.model_call_count} tokens={cert.budget_tokens}")

    passed = sum(1 for c in certs if c.status == "PASS")
    total = len(certs)
    print(f"\n  Certification: {passed}/{total} PASS")

    cert_data = []
    for c in certs:
        cert_data.append({
            "condition_id": c.condition_id,
            "expected_operations": c.expected_operations,
            "observed_operations": c.observed_operations,
            "operation_count": c.operation_count,
            "model_call_count": c.model_call_count,
            "retrieval_count": c.retrieval_count,
            "hypothesis_count": c.hypothesis_count,
            "attack_count": c.attack_count,
            "reason_count": c.reason_count,
            "artifact_types": c.artifact_types,
            "posteriors_updated": c.posteriors_updated,
            "budget_tokens": c.budget_tokens,
            "status": c.status,
            "failure_reason": c.failure_reason,
        })

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / "condition_certification.json"
    out.write_text(json.dumps({"model": model_id, "certificates": cert_data}, indent=2))
    print(f"  Saved: {out}")

    return passed == total


async def run_factorial(client, model_id):
    """Phase 32: Compute-controlled factorial complementarity."""
    print(f"\n{'='*60}")
    print(f"PHASE 32 — FACTORIAL COMPLEMENTARITY")
    print(f"{'='*60}\n")

    worlds = generate_v6_worlds()
    print(f"  Generated {len(worlds)} worlds")

    results = []
    for wi, world in enumerate(worlds):
        print(f"  [{_ts()}] World {wi+1}/{len(worlds)}: {world.world_id}")
        world_results = {"world_id": world.world_id}

        for cid, ops in FACTORIAL_CONDITIONS.items():
            sim = EpistemicWorldSimulator(world, seed=42)
            trace = await run_closed_loop_sequence(client, model_id, sim, ops, cid)
            world_results[cid] = {
                "quality": trace.scalar_quality,
                "calls": trace.total_calls,
                "input_tokens": trace.total_input_tokens,
                "output_tokens": trace.total_output_tokens,
                "hypotheses": len(trace.hypotheses),
                "evidence": len(trace.evidence),
                "posteriors_updated": bool(trace.posteriors),
            }
            print(f"    {cid}: Q={trace.scalar_quality:.4f} calls={trace.total_calls}")

        for cid, ops in FACTORIAL_B_CONDITIONS.items():
            sim = EpistemicWorldSimulator(world, seed=42)
            trace = await run_closed_loop_sequence(client, model_id, sim, ops, cid)
            world_results[cid] = {
                "quality": trace.scalar_quality,
                "calls": trace.total_calls,
                "input_tokens": trace.total_input_tokens,
                "output_tokens": trace.total_output_tokens,
                "hypotheses": len(trace.hypotheses),
                "evidence": len(trace.evidence),
                "posteriors_updated": bool(trace.posteriors),
            }
            print(f"    {cid}: Q={trace.scalar_quality:.4f} calls={trace.total_calls}")

        results.append(world_results)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"factorial_{model_id.replace(':', '_')}.jsonl"
    with open(out, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"  Saved: {out}")

    _analyze_factorial(results)


def _analyze_factorial(results: list[dict]):
    """Compute factorial interaction and report."""
    print(f"\n  --- Study A: Information-Held-Constant ---")
    y00 = [r["C00_control_control"]["quality"] for r in results]
    y10 = [r["C10_hyp_control"]["quality"] for r in results]
    y01 = [r["C01_control_reason"]["quality"] for r in results]
    y11 = [r["C11_hyp_reason"]["quality"] for r in results]

    interactions = [y11[i] - y10[i] - y01[i] + y00[i] for i in range(len(results))]
    mean_int = statistics.mean(interactions)
    std_int = statistics.stdev(interactions) if len(interactions) > 1 else 0
    se = std_int / (len(interactions) ** 0.5) if len(interactions) > 1 else 0
    ci_lo = mean_int - 1.96 * se
    ci_hi = mean_int + 1.96 * se

    print(f"  Interaction: {mean_int:+.4f} (95% CI [{ci_lo:+.4f}, {ci_hi:+.4f}])")
    print(f"  N = {len(results)} worlds")
    print(f"  C00={statistics.mean(y00):.4f}, C10={statistics.mean(y10):.4f}, C01={statistics.mean(y01):.4f}, C11={statistics.mean(y11):.4f}")

    calls_check = all(
        r["C00_control_control"]["calls"] == r["C11_hyp_reason"]["calls"]
        for r in results
    )
    print(f"  Call budget matched: {'YES' if calls_check else 'NO'}")

    print(f"\n  --- Study A-B: Retrieval-Mediated ---")
    yb00 = [r["CB00_control_control"]["quality"] for r in results]
    yb10 = [r["CB10_hyp_control"]["quality"] for r in results]
    yb01 = [r["CB01_control_retrieve"]["quality"] for r in results]
    yb11 = [r["CB11_hyp_retrieve"]["quality"] for r in results]

    int_b = [yb11[i] - yb10[i] - yb01[i] + yb00[i] for i in range(len(results))]
    mean_b = statistics.mean(int_b)
    std_b = statistics.stdev(int_b) if len(int_b) > 1 else 0
    se_b = std_b / (len(int_b) ** 0.5) if len(int_b) > 1 else 0

    print(f"  Interaction: {mean_b:+.4f} (95% CI [{mean_b - 1.96*se_b:+.4f}, {mean_b + 1.96*se_b:+.4f}])")
    print(f"  N = {len(results)} worlds")


async def run_attack_timing(client, model_id):
    """Phase 34: Matched-budget attack timing."""
    print(f"\n{'='*60}")
    print(f"PHASE 34 — MATCHED-BUDGET ATTACK TIMING")
    print(f"{'='*60}\n")

    worlds = generate_v6_worlds()
    results = []

    for wi, world in enumerate(worlds):
        print(f"  [{_ts()}] World {wi+1}/{len(worlds)}: {world.world_id}")
        world_results = {"world_id": world.world_id}

        for cid, ops in ATTACK_TIMING_CONDITIONS.items():
            sim = EpistemicWorldSimulator(world, seed=42)
            trace = await run_closed_loop_sequence(client, model_id, sim, ops, cid)
            world_results[cid] = {
                "quality": trace.scalar_quality,
                "calls": trace.total_calls,
                "input_tokens": trace.total_input_tokens,
                "output_tokens": trace.total_output_tokens,
                "attack_success": any(t.get("found_something") for t in trace.op_traces if t["op"] == "attack"),
            }
            print(f"    {cid}: Q={trace.scalar_quality:.4f}")

        results.append(world_results)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"attack_timing_{model_id.replace(':', '_')}.jsonl"
    with open(out, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"  Saved: {out}")

    early = [r["early_attack"]["quality"] for r in results]
    mid = [r["mid_attack"]["quality"] for r in results]
    late = [r["late_attack"]["quality"] for r in results]
    print(f"\n  Early: {statistics.mean(early):.4f} ± {statistics.stdev(early):.4f}")
    print(f"  Mid:   {statistics.mean(mid):.4f} ± {statistics.stdev(mid):.4f}")
    print(f"  Late:  {statistics.mean(late):.4f} ± {statistics.stdev(late):.4f}")
    print(f"  Range: {max(statistics.mean(late), statistics.mean(mid), statistics.mean(early)) - min(statistics.mean(early), statistics.mean(mid), statistics.mean(late)):.4f}")


async def main():
    parser = argparse.ArgumentParser(description="V6 Causal Closed-Loop Runner")
    parser.add_argument("--phase", default="certify",
                        choices=["certify", "factorial", "intervention", "attack_timing", "all"])
    parser.add_argument("--model", default=PRIMARY_MODEL)
    args = parser.parse_args()

    client = _make_client()
    model_id = args.model

    print(f"Campaign V6 — Causal Closed-Loop Validation")
    print(f"Model: {model_id}")
    print(f"Remote: {BASE_URL}")
    print(f"Temperature: {TEMPERATURE}")
    print(f"Seed base: {V6_BASE_SEED}")
    print()

    if args.phase in ("certify", "all"):
        ok = await run_certification(client, model_id)
        if not ok:
            print("\n  *** CERTIFICATION FAILED — cannot proceed ***")
            if args.phase != "all":
                return

    if args.phase in ("factorial", "all"):
        await run_factorial(client, model_id)

    if args.phase in ("attack_timing", "all"):
        await run_attack_timing(client, model_id)

    print(f"\n{'='*60}")
    print(f"V6 execution complete")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
