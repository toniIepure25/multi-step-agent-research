"""
Campaign V5 — Complete LLM Execution Runner.

Phases 25-27 against remote inference at inference.ccrolabs.com.
Replaces placeholder scripts with real LLM execution.

Usage:
    python experiments/campaign_v5/run_v5_execution.py [--phase 25|26|27|all]
    python experiments/campaign_v5/run_v5_execution.py --phase 25
    python experiments/campaign_v5/run_v5_execution.py --phase 26
    python experiments/campaign_v5/run_v5_execution.py --phase 27
    python experiments/campaign_v5/run_v5_execution.py --phase all
"""

from __future__ import annotations

import argparse
import asyncio
import functools
import hashlib
import json
import os
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
from asar.evaluation.simulator import EpistemicWorldSimulator, LatentWorld
from asar.providers.chat_completions_llm import ChatCompletionsLLMClient

RESULTS_DIR = Path(__file__).parent / "results"
BASE_URL = "https://inference.ccrolabs.com/v1"
PRIMARY_MODEL = "gemma3:27b-it-qat"
TRANSFER_MODEL = "llama3.2-vision:11b-instruct-q8_0"
V4_BASE_SEED = 271828
TEMPERATURE = 0.0
MAX_TOKENS_OP = 512
MAX_TOKENS_STRUCT = 256
TIMEOUT = 120.0


def _make_client() -> ChatCompletionsLLMClient:
    return ChatCompletionsLLMClient(base_url=BASE_URL, timeout=TIMEOUT)


def _ts() -> str:
    return time.strftime("%H:%M:%S")


# ===================================================================
# PHASE 25 — CAPABILITY GATE
# ===================================================================

GATE_PROMPTS = {
    "evidence_interpretation": {
        "system": "You are a research analyst. Interpret the given evidence and explain what it supports or contradicts. Be specific and concise.",
        "template": "Evidence: \"{content}\"\nSource reliability: {reliability}/1.0\n\nIn 2-3 sentences, what does this evidence support or contradict?",
    },
    "hypothesis_generation": {
        "system": "You are a research scientist. Given evidence, generate a plausible hypothesis. Output ONLY valid JSON: {{\"hypothesis\": \"...\", \"reasoning\": \"...\", \"confidence\": 0.0-1.0}}",
        "template": "Evidence observed:\n{evidence}\n\nGenerate one hypothesis explaining these observations. Output ONLY JSON.",
    },
    "alternative_hypothesis": {
        "system": "You are a research scientist. Generate a GENUINELY DIFFERENT alternative hypothesis from the one given. Output ONLY valid JSON: {{\"hypothesis\": \"...\", \"reasoning\": \"...\", \"confidence\": 0.0-1.0}}",
        "template": "Current hypothesis: \"{hypothesis}\"\nEvidence:\n{evidence}\n\nGenerate an alternative hypothesis. Output ONLY JSON.",
    },
    "reasoning": {
        "system": "You are a research analyst. Evaluate hypothesis consistency with evidence. Output ONLY valid JSON: {{\"evaluations\": [{{\"hypothesis\": \"...\", \"score\": 0.0-1.0, \"reasoning\": \"...\"}}]}}",
        "template": "Hypotheses:\n{hypotheses}\n\nEvidence:\n{evidence}\n\nEvaluate each hypothesis against the evidence. Output ONLY JSON.",
    },
    "contradiction_identification": {
        "system": "You are a critical analyst. Identify contradictions. Output ONLY valid JSON: {{\"contradictions\": [{{\"item_a\": \"...\", \"item_b\": \"...\", \"explanation\": \"...\"}}]}}",
        "template": "Items:\n{items}\n\nIdentify contradictions between these items. Output ONLY JSON.",
    },
    "attack_hypothesis": {
        "system": "You are a scientific critic. Identify weaknesses and falsifiers. Output ONLY valid JSON: {{\"weaknesses\": [\"...\"], \"falsifiers\": [\"...\"], \"missing_info\": [\"...\"]}}",
        "template": "Hypothesis: \"{hypothesis}\"\nEvidence:\n{evidence}\n\nCritique this hypothesis. Output ONLY JSON.",
    },
    "missing_information": {
        "system": "You are a research strategist. Identify missing information. Output ONLY valid JSON: {{\"missing\": [{{\"description\": \"...\", \"importance\": 1-5, \"type\": \"...\"}}]}}",
        "template": "Hypotheses:\n{hypotheses}\nEvidence:\n{evidence}\n\nWhat critical information is missing? Output ONLY JSON.",
    },
    "retrieval_query": {
        "system": "You are a research strategist. Generate a targeted search query. Output ONLY valid JSON: {{\"query\": \"...\", \"rationale\": \"...\", \"discriminating_power\": 0.0-1.0}}",
        "template": "Hypothesis A: \"{hyp_a}\"\nHypothesis B: \"{hyp_b}\"\nEvidence:\n{evidence}\n\nGenerate a query to discriminate between these hypotheses. Output ONLY JSON.",
    },
    "synthesis": {
        "system": "You are a research synthesizer. Produce a grounded conclusion. Output ONLY valid JSON: {{\"conclusion\": \"...\", \"confidence\": 0.0-1.0, \"supporting_evidence\": [\"...\"], \"caveats\": [\"...\"]}}",
        "template": "Hypotheses:\n{hypotheses}\nEvidence:\n{evidence}\n\nSynthesize a conclusion. Output ONLY JSON.",
    },
    "structured_output": {
        "system": "You must respond with ONLY a valid JSON object matching this schema: {{\"answer\": \"string\", \"confidence\": 0.0-1.0, \"reasoning\": \"string\"}}. No other text before or after the JSON.",
        "template": "Question: What is the most likely explanation for the following observation?\nObservation: \"{observation}\"\n\nRespond with ONLY valid JSON.",
    },
}


def _score_json_compliance(output: str) -> dict[str, Any]:
    """Score structured output compliance."""
    stripped = output.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        stripped = "\n".join(lines).strip()
    is_json = stripped.startswith("{") or stripped.startswith("[")
    valid = False
    parsed = None
    if is_json:
        try:
            parsed = json.loads(stripped)
            valid = True
        except json.JSONDecodeError:
            pass
    return {"is_json": is_json, "valid_json": valid, "parsed": parsed,
            "score": (0.5 * is_json + 0.5 * valid)}


def _score_hypothesis_gen(output: str, world: LatentWorld) -> dict[str, Any]:
    """Score hypothesis generation against ground truth."""
    json_score = _score_json_compliance(output)
    true_hyp = world.hypotheses.get(world.true_hypothesis_id)
    true_recovered = False
    if true_hyp:
        kws = [w.lower() for w in true_hyp.statement.split() if len(w) > 3]
        out_lower = output.lower()
        matches = sum(1 for kw in kws if kw in out_lower)
        true_recovered = matches >= max(2, len(kws) // 3)
    return {
        "json_valid": json_score["valid_json"],
        "true_recovered": true_recovered,
        "score": 0.4 * true_recovered + 0.3 * json_score["valid_json"] + 0.3 * json_score["is_json"],
    }


def _score_reasoning(output: str, world: LatentWorld) -> dict[str, Any]:
    """Score reasoning against ground truth."""
    json_score = _score_json_compliance(output)
    true_hyp = world.hypotheses.get(world.true_hypothesis_id)
    out_lower = output.lower()
    correct_direction = False
    if true_hyp:
        kws = [w.lower() for w in true_hyp.statement.split() if len(w) > 3][:3]
        if any(kw in out_lower for kw in kws):
            if any(w in out_lower for w in ["correct", "supported", "consistent", "high", "strong", "likely"]):
                correct_direction = True
    return {
        "json_valid": json_score["valid_json"],
        "correct_direction": correct_direction,
        "score": 0.4 * correct_direction + 0.3 * json_score["valid_json"] + 0.3 * json_score["is_json"],
    }


def _score_evidence_interpretation(output: str, world: LatentWorld) -> dict[str, Any]:
    """Score evidence interpretation — natural language, not JSON."""
    out_lower = output.lower()
    has_substance = len(output.strip()) > 20
    mentions_support_contradict = any(
        w in out_lower for w in ["support", "contradict", "suggest", "indicate",
                                  "consistent", "inconsistent", "evidence for",
                                  "evidence against", "implies", "confirms"])
    true_hyp = world.hypotheses.get(world.true_hypothesis_id)
    relevant_to_truth = False
    if true_hyp:
        kws = [w.lower() for w in true_hyp.statement.split() if len(w) > 3][:4]
        relevant_to_truth = any(kw in out_lower for kw in kws)
    return {
        "has_substance": has_substance,
        "mentions_support_contradict": mentions_support_contradict,
        "relevant_to_truth": relevant_to_truth,
        "score": (0.3 * has_substance + 0.4 * mentions_support_contradict + 0.3 * relevant_to_truth),
    }


def _score_attack(output: str, world: LatentWorld) -> dict[str, Any]:
    """Score attack/falsification."""
    json_score = _score_json_compliance(output)
    out_lower = output.lower()
    has_weakness = any(w in out_lower for w in
                       ["weakness", "flaw", "assumption", "limitation", "counter",
                        "alternative", "falsif", "contradict", "problem"])
    return {
        "json_valid": json_score["valid_json"],
        "has_weakness": has_weakness,
        "score": 0.4 * has_weakness + 0.3 * json_score["valid_json"] + 0.3 * json_score["is_json"],
    }


async def run_phase25(client: ChatCompletionsLLMClient, model_id: str) -> dict:
    """Execute the full capability gate for one model."""
    print(f"\n{'='*70}")
    print(f"PHASE 25 — CAPABILITY GATE: {model_id}")
    print(f"{'='*70}")

    regimes = list(V4_REGIME_GENERATORS.values())
    worlds = []
    for gen_fn in regimes:
        for i in range(3):
            worlds.append(gen_fn(index=i, seed=V4_BASE_SEED + i))

    gate_results: dict[str, list[dict]] = defaultdict(list)
    raw_traces: list[dict] = []
    total_calls = 0
    total_input_tokens = 0
    total_output_tokens = 0

    for wi, world in enumerate(worlds):
        sim = EpistemicWorldSimulator(world)
        ev = sim.retrieve("")
        ev_list = [ev] if ev else []
        ev_text = "\n".join(f"- {e['content']}" for e in ev_list) if ev_list else "(no evidence)"
        hyp = sim.generate_hypothesis([e["evidence_id"] for e in ev_list] if ev_list else [])
        hyp_text = hyp["statement"] if hyp else "unknown hypothesis"
        hyp2 = sim.generate_hypothesis([e["evidence_id"] for e in ev_list] if ev_list else [])
        hyp2_text = hyp2["statement"] if hyp2 else "alternative"

        ops_to_test = [
            ("evidence_interpretation", {"content": ev_list[0]["content"] if ev_list else "general observation", "reliability": ev_list[0].get("source_reliability", 0.7) if ev_list else 0.7}),
            ("hypothesis_generation", {"evidence": ev_text}),
            ("alternative_hypothesis", {"hypothesis": hyp_text, "evidence": ev_text}),
            ("reasoning", {"hypotheses": f"1. {hyp_text}\n2. {hyp2_text}", "evidence": ev_text}),
            ("contradiction_identification", {"items": f"A: {ev_text}\nB: Hypothesis states '{hyp_text}'"}),
            ("attack_hypothesis", {"hypothesis": hyp_text, "evidence": ev_text}),
            ("missing_information", {"hypotheses": hyp_text, "evidence": ev_text}),
            ("retrieval_query", {"hyp_a": hyp_text, "hyp_b": hyp2_text, "evidence": ev_text}),
            ("synthesis", {"hypotheses": f"1. {hyp_text}\n2. {hyp2_text}", "evidence": ev_text}),
            ("structured_output", {"observation": ev_list[0]["content"][:100] if ev_list else "An anomalous pattern was observed"}),
        ]

        for op_name, kwargs in ops_to_test:
            prompt_data = GATE_PROMPTS[op_name]
            user_content = prompt_data["template"].format(**kwargs)
            start = time.perf_counter()
            try:
                resp = await client.generate(LLMGenerationRequest(
                    model=model_id,
                    messages=[
                        LLMMessage(role=MessageRole.SYSTEM, content=prompt_data["system"]),
                        LLMMessage(role=MessageRole.USER, content=user_content),
                    ],
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS_STRUCT if op_name == "structured_output" else MAX_TOKENS_OP,
                ))
                elapsed = (time.perf_counter() - start) * 1000
                total_calls += 1
                total_input_tokens += resp.usage.input_tokens
                total_output_tokens += resp.usage.output_tokens

                if op_name == "evidence_interpretation":
                    scoring = _score_evidence_interpretation(resp.output_text, world)
                elif op_name in ("hypothesis_generation", "alternative_hypothesis"):
                    scoring = _score_hypothesis_gen(resp.output_text, world)
                elif op_name == "reasoning":
                    scoring = _score_reasoning(resp.output_text, world)
                elif op_name in ("attack_hypothesis",):
                    scoring = _score_attack(resp.output_text, world)
                else:
                    scoring = _score_json_compliance(resp.output_text)

                gate_results[op_name].append(scoring)
                raw_traces.append({
                    "model": model_id, "operation": op_name,
                    "world_id": world.world_id, "score": scoring["score"],
                    "input_tokens": resp.usage.input_tokens,
                    "output_tokens": resp.usage.output_tokens,
                    "latency_ms": round(elapsed),
                    "raw_output": resp.output_text[:300],
                })

            except Exception as exc:
                elapsed = (time.perf_counter() - start) * 1000
                gate_results[op_name].append({"score": 0})
                raw_traces.append({
                    "model": model_id, "operation": op_name,
                    "world_id": world.world_id, "score": 0,
                    "error": str(exc)[:200], "latency_ms": round(elapsed),
                })

        if (wi + 1) % 4 == 0:
            print(f"  [{_ts()}] {wi+1}/{len(worlds)} worlds evaluated ({total_calls} calls)")

    # Summarize
    summary = {}
    core_ops = ["evidence_interpretation", "hypothesis_generation", "reasoning", "structured_output"]
    gate_passed = True

    print(f"\n  {'Operation':35s} {'Mean':>7s} {'N':>4s} {'Status':>8s}")
    print("  " + "-" * 60)
    for op_name in GATE_PROMPTS:
        scores = [r["score"] for r in gate_results[op_name]]
        mean = statistics.mean(scores) if scores else 0
        status = "PASS" if mean > 0.3 else "FAIL"
        if op_name in core_ops and mean <= 0.3:
            gate_passed = False
        print(f"  {op_name:35s} {mean:6.3f} {len(scores):4d} {status:>8s}")
        summary[op_name] = {
            "mean": round(mean, 4),
            "n": len(scores),
            "std": round(statistics.stdev(scores), 4) if len(scores) > 1 else 0,
            "status": status,
        }

    classification = "VALID_EXPERIMENTAL_SUBSTRATE" if gate_passed else "INVALID_EXPERIMENTAL_SUBSTRATE"
    print(f"\n  MODEL: {model_id}")
    print(f"  CLASSIFICATION: {classification}")
    print(f"  TOTAL CALLS: {total_calls}")
    print(f"  TOTAL TOKENS: {total_input_tokens} in / {total_output_tokens} out")

    result = {
        "model": model_id, "classification": classification,
        "gate_passed": gate_passed, "summary": summary,
        "total_calls": total_calls,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
    }

    model_tag = model_id.split(":")[0].replace(".", "_")
    with open(RESULTS_DIR / f"phase25_gate_{model_tag}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    with open(RESULTS_DIR / f"phase25_traces_{model_tag}.jsonl", "w", encoding="utf-8") as f:
        for t in raw_traces:
            f.write(json.dumps(t, default=str) + "\n")

    return result


# ===================================================================
# PHASE 26 — LLM SEQUENCE REPLICATION
# ===================================================================

REPLICATION_SEQUENCES = {
    "B1_extended": ["retrieve", "generate_hypothesis", "retrieve",
                    "generate_hypothesis", "reason", "retrieve", "reason"],
    "single_retrieve": ["retrieve"],
    "single_gen_hyp": ["generate_hypothesis"],
    "explore": ["generate_hypothesis", "retrieve"],
    "discriminate": ["retrieve", "generate_hypothesis", "reason"],
    "reversed_B1": ["reason", "generate_hypothesis", "retrieve",
                    "generate_hypothesis", "retrieve"],
    "attack_early": ["attack_hypothesis"],
    "attack_late": ["retrieve", "generate_hypothesis", "retrieve",
                    "generate_hypothesis", "reason", "attack_hypothesis"],
}


async def _llm_cognitive_op(
    client: ChatCompletionsLLMClient,
    model_id: str,
    operation: str,
    world: LatentWorld,
    sim: EpistemicWorldSimulator,
    evidence: list[dict],
    hypotheses: list[dict],
) -> dict:
    """Execute one LLM cognitive operation. Returns trace dict."""
    ev_text = "\n".join(f"- {e.get('content', '')[:80]}" for e in evidence) or "(no evidence)"
    hyp_text = "\n".join(f"- {h.get('statement', '')[:80]}" for h in hypotheses) or "(no hypotheses)"

    if operation == "retrieve":
        prompt = GATE_PROMPTS["retrieval_query"]
        h_a = hypotheses[0]["statement"][:80] if hypotheses else "unknown"
        h_b = hypotheses[1]["statement"][:80] if len(hypotheses) > 1 else "alternative"
        user = prompt["template"].format(hyp_a=h_a, hyp_b=h_b, evidence=ev_text)
        system = prompt["system"]
    elif operation == "generate_hypothesis":
        prompt = GATE_PROMPTS["hypothesis_generation"]
        user = prompt["template"].format(evidence=ev_text)
        system = prompt["system"]
    elif operation == "reason":
        prompt = GATE_PROMPTS["reasoning"]
        user = prompt["template"].format(hypotheses=hyp_text, evidence=ev_text)
        system = prompt["system"]
    elif operation == "attack_hypothesis":
        prompt = GATE_PROMPTS["attack_hypothesis"]
        target = hypotheses[0]["statement"][:80] if hypotheses else "the primary hypothesis"
        user = prompt["template"].format(hypothesis=target, evidence=ev_text)
        system = prompt["system"]
    else:
        return {"operation": operation, "success": False, "score": 0, "error": "unknown_op"}

    start = time.perf_counter()
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
        elapsed = (time.perf_counter() - start) * 1000

        if operation == "generate_hypothesis":
            scoring = _score_hypothesis_gen(resp.output_text, world)
        elif operation == "reason":
            scoring = _score_reasoning(resp.output_text, world)
        elif operation == "attack_hypothesis":
            scoring = _score_attack(resp.output_text, world)
        else:
            scoring = _score_json_compliance(resp.output_text)

        return {
            "operation": operation, "success": True, "score": scoring["score"],
            "latency_ms": round(elapsed),
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
            "raw_output": resp.output_text[:200],
        }
    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "operation": operation, "success": False, "score": 0,
            "latency_ms": round(elapsed), "error": str(exc)[:200],
        }


async def run_llm_sequence(
    client: ChatCompletionsLLMClient,
    model_id: str,
    world: LatentWorld,
    sequence: list[str],
    seq_name: str,
) -> dict:
    """Run a cognitive sequence: simulator for environment, LLM for cognition."""
    sim = EpistemicWorldSimulator(world, seed=42)
    evidence: list[dict] = []
    hypotheses: list[dict] = []
    op_traces: list[dict] = []
    total_in = 0
    total_out = 0
    total_lat = 0

    for op in sequence:
        if op == "retrieve":
            ev = sim.retrieve("")
            if ev:
                evidence.append(ev)

        trace = await _llm_cognitive_op(
            client, model_id, op, world, sim, evidence, hypotheses)
        op_traces.append(trace)
        total_in += trace.get("input_tokens", 0)
        total_out += trace.get("output_tokens", 0)
        total_lat += trace.get("latency_ms", 0)

        if op == "generate_hypothesis":
            hyp = sim.generate_hypothesis(
                [e["evidence_id"] for e in evidence])
            if hyp:
                hypotheses.append(hyp)
        elif op == "reason" and hypotheses:
            sim.reason(
                [h["hypothesis_id"] for h in hypotheses],
                [e["evidence_id"] for e in evidence])

    hyps_dict = {h["hypothesis_id"]: h.get("initial_plausibility", 0.5)
                 for h in hypotheses}
    ev_sources = {e.get("source_id", ""): e.get("parent_source") for e in evidence}
    quality = sim.evaluate(hyps_dict, set(), set(), ev_sources)

    return {
        "world_id": world.world_id,
        "sequence_name": seq_name,
        "sequence": sequence,
        "model": model_id,
        "scalar_quality": quality.scalar_quality(),
        "step_results": op_traces,
        "total_input_tokens": total_in,
        "total_output_tokens": total_out,
        "total_latency_ms": total_lat,
        "hypothesis_count": len(hypotheses),
        "evidence_count": len(evidence),
        "monetary_cost": 0,
        "cost_note": "private_infrastructure",
    }


async def run_phase26(client: ChatCompletionsLLMClient, model_id: str) -> dict:
    """Execute Phase 26 replication for one model."""
    print(f"\n{'='*70}")
    print(f"PHASE 26 — LLM SEQUENCE REPLICATION: {model_id}")
    print(f"{'='*70}")

    worlds = []
    for gen_fn in V4_REGIME_GENERATORS.values():
        for i in range(2):
            worlds.append(gen_fn(index=i, seed=V4_BASE_SEED + 200 + i))

    all_results: list[dict] = []
    total_calls = 0

    for wi, world in enumerate(worlds):
        for seq_name, seq in REPLICATION_SEQUENCES.items():
            result = await run_llm_sequence(client, model_id, world, seq, seq_name)
            all_results.append(result)
            total_calls += len(seq)
            q = result["scalar_quality"]
            toks = result["total_input_tokens"] + result["total_output_tokens"]
            print(f"  [{_ts()}] {world.world_id[:20]:20s} {seq_name:18s} q={q:.4f} tok={toks}")

        if (wi + 1) % 4 == 0:
            print(f"  --- {wi+1}/{len(worlds)} worlds complete ---")

    # Analyze
    by_seq = defaultdict(list)
    for r in all_results:
        by_seq[r["sequence_name"]].append(r["scalar_quality"])

    print(f"\n  {'Sequence':25s} {'Mean':>8s} {'Std':>8s} {'N':>4s}")
    print("  " + "-" * 50)
    for name, scores in sorted(by_seq.items(), key=lambda x: -statistics.mean(x[1])):
        m = statistics.mean(scores)
        s = statistics.stdev(scores) if len(scores) > 1 else 0
        print(f"  {name:25s} {m:7.4f} {s:8.4f} {len(scores):4d}")

    # Replication verdicts
    b1 = statistics.mean(by_seq.get("B1_extended", [0]))
    singles = {k: statistics.mean(v) for k, v in by_seq.items() if k.startswith("single_")}
    max_single = max(singles.values()) if singles else 0

    explore_m = statistics.mean(by_seq.get("explore", [0]))
    discrim_m = statistics.mean(by_seq.get("discriminate", [0]))
    single_gh = statistics.mean(by_seq.get("single_gen_hyp", [0]))
    single_r = statistics.mean(by_seq.get("single_retrieve", [0]))
    rev_b1 = statistics.mean(by_seq.get("reversed_B1", [0]))
    atk_early = statistics.mean(by_seq.get("attack_early", [0]))
    atk_late = statistics.mean(by_seq.get("attack_late", [0]))

    verdicts = {}

    def _classify(name: str, condition: bool, effect: float) -> str:
        if abs(effect) < 0.01:
            v = "INCONCLUSIVE"
        elif condition:
            v = "REPLICATED" if abs(effect) > 0.03 else "PARTIALLY_REPLICATED"
        else:
            v = "NOT_REPLICATED"
        verdicts[name] = {"verdict": v, "effect": round(effect, 4)}
        return v

    r1 = _classify("R1_sequence_superiority", b1 > max_single, b1 - max_single)
    r2_comp = explore_m + discrim_m - single_gh - single_r
    r2 = _classify("R2_complementarity", r2_comp > 0, r2_comp / 2)
    r4 = _classify("R4_order_effects", b1 > rev_b1, b1 - rev_b1)
    r5 = _classify("R5_attack_timing", atk_late > atk_early, atk_late - atk_early)
    r6 = _classify("R6_fixed_vs_greedy", b1 > max_single, b1 - max_single)

    print(f"\n  --- REPLICATION VERDICTS ---")
    for test, data in verdicts.items():
        print(f"  [{data['verdict']:22s}] {test:30s} effect={data['effect']:+.4f}")

    replicated_count = sum(1 for v in verdicts.values() if v["verdict"] in ("REPLICATED", "PARTIALLY_REPLICATED"))

    model_tag = model_id.split(":")[0].replace(".", "_")
    with open(RESULTS_DIR / f"phase26_results_{model_tag}.jsonl", "w", encoding="utf-8") as f:
        for r in all_results:
            f.write(json.dumps(r, default=str) + "\n")

    (RESULTS_DIR / f"phase26_verdicts_{model_tag}.json").write_text(
        json.dumps({"model": model_id, "verdicts": verdicts,
                     "replicated_count": replicated_count,
                     "means": {k: round(statistics.mean(v), 4) for k, v in by_seq.items()},
                     "total_results": len(all_results)},
                    indent=2), encoding="utf-8")

    return {"model": model_id, "verdicts": verdicts, "by_seq": {k: round(statistics.mean(v), 4) for k, v in by_seq.items()}, "replicated_count": replicated_count}


# ===================================================================
# PHASE 27 — STATIC REAL-EVIDENCE
# ===================================================================

async def run_phase27(client: ChatCompletionsLLMClient, model_id: str) -> dict:
    """Execute Phase 27 static evidence evaluation."""
    print(f"\n{'='*70}")
    print(f"PHASE 27 — STATIC REAL-EVIDENCE: {model_id}")
    print(f"{'='*70}")

    from experiments.campaign_v5.static_evidence_packs import generate_all_packs, StaticEvidencePack

    all_packs = generate_all_packs()
    rich_packs = [p for p in all_packs if not any(
        p.evidence_items[0].content.startswith("Primary study supporting")
        for _ in [1] if len(p.evidence_items) > 0)]

    rich_ids = {"cog_01", "cog_02", "cog_03", "cog_04", "cog_05",
                "ai_01", "ai_02", "ai_03", "ai_04", "ai_05",
                "bio_01", "econ_01", "hist_01", "soc_01"}
    packs = [p for p in all_packs if p.pack_id in rich_ids]
    print(f"  Using {len(packs)} fully-specified evidence packs")

    conditions = {
        "direct": ["retrieve_all", "synthesize"],
        "reflection": ["retrieve_all", "synthesize", "critique", "revise"],
        "B1_extended": ["retrieve", "generate_hypothesis", "retrieve",
                        "generate_hypothesis", "reason", "retrieve", "synthesize"],
        "FULL_EXPLORE": ["generate_hypothesis", "retrieve", "generate_hypothesis",
                         "retrieve", "reason", "retrieve", "synthesize"],
        "greedy_primitive": ["retrieve", "retrieve", "retrieve", "retrieve", "synthesize"],
    }

    all_results: list[dict] = []

    for pack in packs:
        for cond_name, cond_seq in conditions.items():
            result = await _run_static_condition(client, model_id, pack, cond_name, cond_seq)
            all_results.append(result)
            print(f"  [{_ts()}] {pack.pack_id:12s} {cond_name:18s} composite={result.get('composite', 0):.3f}")

    by_cond = defaultdict(list)
    by_domain = defaultdict(lambda: defaultdict(list))
    for r in all_results:
        by_cond[r["condition"]].append(r.get("composite", 0))
        by_domain[r["domain"]][r["condition"]].append(r.get("composite", 0))

    print(f"\n  {'Condition':25s} {'Mean':>8s} {'Std':>8s} {'N':>4s}")
    print("  " + "-" * 50)
    for name, scores in sorted(by_cond.items(), key=lambda x: -statistics.mean(x[1])):
        m = statistics.mean(scores)
        s = statistics.stdev(scores) if len(scores) > 1 else 0
        print(f"  {name:25s} {m:7.3f} {s:8.3f} {len(scores):4d}")

    model_tag = model_id.split(":")[0].replace(".", "_")
    with open(RESULTS_DIR / f"phase27_results_{model_tag}.jsonl", "w", encoding="utf-8") as f:
        for r in all_results:
            f.write(json.dumps(r, default=str) + "\n")

    (RESULTS_DIR / f"phase27_summary_{model_tag}.json").write_text(
        json.dumps({"model": model_id,
                     "n_packs": len(packs),
                     "conditions": {k: {"mean": round(statistics.mean(v), 4),
                                        "std": round(statistics.stdev(v) if len(v) > 1 else 0, 4),
                                        "n": len(v)} for k, v in by_cond.items()},
                     "domains": {d: {c: round(statistics.mean(s), 4) for c, s in cs.items()}
                                 for d, cs in by_domain.items()},
                     }, indent=2), encoding="utf-8")

    return {"model": model_id, "by_cond": {k: round(statistics.mean(v), 4) for k, v in by_cond.items()}, "n_packs": len(packs)}


async def _run_static_condition(
    client: ChatCompletionsLLMClient,
    model_id: str,
    pack: Any,
    cond_name: str,
    cond_seq: list[str],
) -> dict:
    """Run one condition on one static evidence pack."""
    retrieved: list[dict] = []
    hypotheses: list[str] = []
    critiques: list[str] = []
    retrieve_idx = 0
    total_tokens = 0
    start = time.perf_counter()

    for op in cond_seq:
        if op == "retrieve_all":
            for item in pack.evidence_items:
                retrieved.append({"item_id": item.item_id, "content": item.content,
                                  "source": item.source, "source_type": item.source_type})
        elif op == "retrieve":
            if retrieve_idx < len(pack.evidence_items):
                item = pack.evidence_items[retrieve_idx]
                retrieved.append({"item_id": item.item_id, "content": item.content,
                                  "source": item.source, "source_type": item.source_type})
                retrieve_idx += 1
        elif op == "generate_hypothesis":
            ev_text = "\n".join(f"- [{r['item_id']}] {r['content'][:80]}" for r in retrieved)
            try:
                resp = await client.generate(LLMGenerationRequest(
                    model=model_id,
                    messages=[
                        LLMMessage(role=MessageRole.SYSTEM, content="Generate a hypothesis for the evidence. Output JSON: {\"hypothesis\": \"...\", \"reasoning\": \"...\", \"confidence\": 0.0-1.0}"),
                        LLMMessage(role=MessageRole.USER, content=f"Question: {pack.task_question}\nEvidence:\n{ev_text}"),
                    ],
                    temperature=TEMPERATURE, max_tokens=MAX_TOKENS_OP))
                hypotheses.append(resp.output_text[:200])
                total_tokens += resp.usage.total_tokens
            except Exception:
                pass
        elif op == "reason":
            ev_text = "\n".join(f"- [{r['item_id']}] {r['content'][:80]}" for r in retrieved)
            hyp_text = "\n".join(f"- {h[:80]}" for h in hypotheses) or "(none)"
            try:
                resp = await client.generate(LLMGenerationRequest(
                    model=model_id,
                    messages=[
                        LLMMessage(role=MessageRole.SYSTEM, content="Evaluate hypotheses against evidence. Output JSON."),
                        LLMMessage(role=MessageRole.USER, content=f"Question: {pack.task_question}\nHypotheses:\n{hyp_text}\nEvidence:\n{ev_text}"),
                    ],
                    temperature=TEMPERATURE, max_tokens=MAX_TOKENS_OP))
                total_tokens += resp.usage.total_tokens
            except Exception:
                pass
        elif op in ("synthesize", "revise"):
            ev_text = "\n".join(f"- [{r['item_id']}] {r['content'][:80]}" for r in retrieved)
            hyp_text = "\n".join(hypotheses[:3]) if hypotheses else "(none)"
            critique_text = "\n".join(critiques[:2]) if critiques else ""
            instruction = "Synthesize a final conclusion" if op == "synthesize" else "Revise based on critique"
            try:
                resp = await client.generate(LLMGenerationRequest(
                    model=model_id,
                    messages=[
                        LLMMessage(role=MessageRole.SYSTEM, content=f"{instruction}. Reference evidence. Address contradictions. State uncertainty. Output JSON: {{\"conclusion\": \"...\", \"confidence\": 0.0-1.0, \"supporting_evidence\": [...], \"caveats\": [...]}}"),
                        LLMMessage(role=MessageRole.USER, content=f"Question: {pack.task_question}\nEvidence:\n{ev_text}\nHypotheses:\n{hyp_text}" + (f"\nCritique:\n{critique_text}" if critique_text else "")),
                    ],
                    temperature=TEMPERATURE, max_tokens=MAX_TOKENS_OP))
                total_tokens += resp.usage.total_tokens

                scores = _score_static_output(resp.output_text, pack, [r["item_id"] for r in retrieved])
                return {
                    "pack_id": pack.pack_id, "domain": pack.domain,
                    "condition": cond_name, "composite": scores["composite"],
                    "scores": scores, "total_tokens": total_tokens,
                    "latency_ms": round((time.perf_counter() - start) * 1000),
                    "evidence_retrieved": len(retrieved),
                    "hypotheses_generated": len(hypotheses),
                    "model": model_id, "raw_output": resp.output_text[:300],
                }
            except Exception as exc:
                return {
                    "pack_id": pack.pack_id, "domain": pack.domain,
                    "condition": cond_name, "composite": 0, "error": str(exc)[:200],
                    "model": model_id,
                }
        elif op == "critique":
            ev_text = "\n".join(f"- {r['content'][:60]}" for r in retrieved)
            try:
                resp = await client.generate(LLMGenerationRequest(
                    model=model_id,
                    messages=[
                        LLMMessage(role=MessageRole.SYSTEM, content="Critique the analysis. Identify weaknesses, missing evidence, alternatives."),
                        LLMMessage(role=MessageRole.USER, content=f"Question: {pack.task_question}\nEvidence:\n{ev_text}\nHypotheses:\n{chr(10).join(hypotheses[:2])}"),
                    ],
                    temperature=TEMPERATURE, max_tokens=MAX_TOKENS_OP))
                critiques.append(resp.output_text[:200])
                total_tokens += resp.usage.total_tokens
            except Exception:
                pass

    return {"pack_id": pack.pack_id, "domain": pack.domain,
            "condition": cond_name, "composite": 0, "model": model_id,
            "note": "sequence did not reach synthesis"}


def _score_static_output(output: str, pack: Any, retrieved_ids: list[str]) -> dict:
    """Score agent output against evaluator-only ground truth."""
    gt = pack.ground_truth
    out_lower = output.lower()

    best_kw = gt.best_hypothesis.lower().replace("_", " ")
    claim_correctness = 1.0 if best_kw in out_lower else 0.0
    for acc in gt.acceptable_hypotheses:
        if acc.lower().replace("_", " ") in out_lower:
            claim_correctness = max(claim_correctness, 0.7)

    cited = sum(1 for eid in retrieved_ids
                if eid.lower() in out_lower or
                any(e.content[:25].lower() in out_lower
                    for e in pack.evidence_items if e.item_id == eid))
    evidence_support = cited / max(len(retrieved_ids), 1)

    decisive_found = sum(1 for d in gt.decisive_evidence
                         if d.lower() in out_lower or
                         any(e.content[:25].lower() in out_lower
                             for e in pack.evidence_items if e.item_id == d))
    decisive_coverage = decisive_found / max(len(gt.decisive_evidence), 1)

    contradiction_handling = 1.0 if any(
        w in out_lower for w in ["however", "contradict", "conflict", "against",
                                  "challenge", "caveat", "disagree", "tension"]) else 0.0

    uncertainty_words = ["uncertain", "unclear", "ambiguous", "mixed",
                         "limited", "depend", "caveat", "may", "might", "possible"]
    calibration = min(1.0, sum(1 for w in uncertainty_words if w in out_lower) / 3)

    dep_aware = 0.5
    if gt.source_dependencies:
        dep_aware = 1.0 if any(w in out_lower for w in ["depend", "deriv", "copy", "same source", "independent"]) else 0.0

    composite = (0.25 * claim_correctness + 0.15 * evidence_support +
                 0.20 * decisive_coverage + 0.15 * contradiction_handling +
                 0.15 * calibration + 0.10 * dep_aware)

    return {
        "claim_correctness": round(claim_correctness, 3),
        "evidence_support": round(evidence_support, 3),
        "decisive_coverage": round(decisive_coverage, 3),
        "contradiction_handling": round(contradiction_handling, 3),
        "calibration": round(calibration, 3),
        "source_independence": round(dep_aware, 3),
        "composite": round(composite, 3),
    }


# ===================================================================
# MAIN
# ===================================================================

async def main():
    parser = argparse.ArgumentParser(description="Campaign V5 LLM Execution")
    parser.add_argument("--phase", default="all", choices=["25", "26", "27", "all"])
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    client = _make_client()

    print(f"Remote: {BASE_URL}")
    print(f"Primary model: {PRIMARY_MODEL}")
    print(f"Transfer model: {TRANSFER_MODEL}")

    if args.phase in ("25", "all"):
        p25a = await run_phase25(client, PRIMARY_MODEL)
        if not p25a["gate_passed"]:
            print(f"\n  PRIMARY MODEL FAILED GATE. Trying transfer model...")
            p25a = await run_phase25(client, TRANSFER_MODEL)
            if p25a["gate_passed"]:
                print(f"  Transfer model passed — swapping to primary")

        p25b = await run_phase25(client, TRANSFER_MODEL)

    if args.phase in ("26", "all"):
        p26a = await run_phase26(client, PRIMARY_MODEL)
        p26b = await run_phase26(client, TRANSFER_MODEL)

    if args.phase in ("27", "all"):
        p27a = await run_phase27(client, PRIMARY_MODEL)

    print(f"\n{'='*70}")
    print(f"CAMPAIGN V5 EXECUTION COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
