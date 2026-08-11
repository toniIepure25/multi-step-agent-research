"""
Phase 27 — Static Real-Evidence Benchmark.

Runs cognitive sequences on frozen real-evidence packs and compares
against conditions: Direct, Reflection, B1_extended, best V4 fixed,
primitive greedy.

Requires a running LLM server for LLM-backed conditions.
Without LLM: generates packs and documents protocol.
"""

from __future__ import annotations

import asyncio
import json
import os
import statistics
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.campaign_v5.static_evidence_packs import (
    StaticEvidencePack,
    generate_all_packs,
    save_all_packs,
)

RESULTS_DIR = Path(__file__).parent / "results"
MODEL_NAME = os.environ.get("ASAR_MODEL_NAME", "qwen2.5:7b")


# ---------------------------------------------------------------
# Controlled retrieval interface for evidence packs
# ---------------------------------------------------------------

@dataclass
class EvidencePackState:
    """Agent-visible state for interacting with a static evidence pack."""
    pack: StaticEvidencePack
    retrieved_indices: list[int] = field(default_factory=list)
    hypotheses_generated: list[str] = field(default_factory=list)
    reasoning_artifacts: list[str] = field(default_factory=list)
    attack_artifacts: list[str] = field(default_factory=list)

    def available_evidence_count(self) -> int:
        return len(self.pack.evidence_items) - len(self.retrieved_indices)

    def retrieve_next(self) -> dict | None:
        for i in range(len(self.pack.evidence_items)):
            if i not in self.retrieved_indices:
                self.retrieved_indices.append(i)
                e = self.pack.evidence_items[i]
                return {"item_id": e.item_id, "content": e.content,
                        "source": e.source, "source_type": e.source_type}
        return None

    def get_all_retrieved(self) -> list[dict]:
        return [{"item_id": self.pack.evidence_items[i].item_id,
                 "content": self.pack.evidence_items[i].content,
                 "source": self.pack.evidence_items[i].source}
                for i in self.retrieved_indices]


# ---------------------------------------------------------------
# Scoring against ground truth
# ---------------------------------------------------------------

def score_agent_output(
    output: str,
    pack: StaticEvidencePack,
    retrieved_ids: list[str],
) -> dict[str, float]:
    """Score agent output against evaluator-only ground truth."""
    gt = pack.ground_truth
    out_lower = output.lower()

    best_hyp_kw = gt.best_hypothesis.lower().replace("_", " ")
    claim_correctness = 1.0 if best_hyp_kw in out_lower else 0.0

    for acceptable in gt.acceptable_hypotheses:
        kw = acceptable.lower().replace("_", " ")
        if kw in out_lower:
            claim_correctness = max(claim_correctness, 0.7)

    cited = sum(1 for eid in retrieved_ids
                if eid.lower() in out_lower or
                any(e.content[:30].lower() in out_lower
                    for e in pack.evidence_items if e.item_id == eid))
    evidence_support = cited / max(len(retrieved_ids), 1)

    decisive_found = sum(1 for d in gt.decisive_evidence
                         if d.lower() in out_lower or
                         any(e.content[:30].lower() in out_lower
                             for e in pack.evidence_items if e.item_id == d))
    decisive_coverage = decisive_found / max(len(gt.decisive_evidence), 1)

    contradiction_words = ["however", "contradict", "conflict", "against",
                           "opposite", "challenge", "dispute", "caveat"]
    contradiction_handling = 1.0 if any(w in out_lower for w in contradiction_words) else 0.0

    uncertainty_words = ["uncertain", "unclear", "ambiguous", "mixed",
                         "limited", "depend", "caveat", "may", "might"]
    calibration = min(1.0, sum(1 for w in uncertainty_words if w in out_lower) / 3)

    dep_mentioned = any("depend" in out_lower or "copy" in out_lower or
                        "derived" in out_lower
                        for _, _ in gt.source_dependencies) if gt.source_dependencies else 0.5
    source_independence = float(dep_mentioned) if gt.source_dependencies else 0.5

    return {
        "claim_correctness": round(claim_correctness, 3),
        "evidence_support": round(evidence_support, 3),
        "decisive_coverage": round(decisive_coverage, 3),
        "contradiction_handling": round(contradiction_handling, 3),
        "calibration": round(calibration, 3),
        "source_independence": round(source_independence, 3),
        "composite": round(
            0.25 * claim_correctness +
            0.15 * evidence_support +
            0.20 * decisive_coverage +
            0.15 * contradiction_handling +
            0.15 * calibration +
            0.10 * source_independence, 3),
    }


# ---------------------------------------------------------------
# Sequence conditions on evidence packs
# ---------------------------------------------------------------

STATIC_SEQUENCES = {
    "direct": ["retrieve_all", "synthesize"],
    "reflection": ["retrieve_all", "synthesize", "critique", "revise"],
    "B1_extended": ["retrieve", "generate_hypothesis", "retrieve",
                    "generate_hypothesis", "reason", "retrieve", "reason"],
    "FULL_EXPLORE": ["generate_hypothesis", "retrieve", "generate_hypothesis",
                     "retrieve", "generate_hypothesis", "retrieve", "reason",
                     "retrieve", "reason"],
    "greedy_primitive": ["retrieve", "retrieve", "retrieve", "retrieve",
                         "reason"],
}


async def run_static_sequence_llm(
    pack: StaticEvidencePack,
    sequence_name: str,
    sequence: list[str],
    client: Any,
) -> dict[str, Any]:
    """Run a sequence on a static evidence pack using LLM."""
    state = EvidencePackState(pack=pack)
    start = time.perf_counter()
    total_tokens = 0

    from asar.core.llm import LLMGenerationRequest, LLMMessage, MessageRole

    for op in sequence:
        if op in ("retrieve", "retrieve_all"):
            if op == "retrieve_all":
                while state.available_evidence_count() > 0:
                    state.retrieve_next()
            else:
                state.retrieve_next()

        elif op == "generate_hypothesis":
            retrieved = state.get_all_retrieved()
            ev_text = "\n".join(f"- {r['content'][:100]}" for r in retrieved)
            try:
                resp = await client.generate(LLMGenerationRequest(
                    model=MODEL_NAME,
                    messages=[
                        LLMMessage(role=MessageRole.SYSTEM,
                                   content="Generate a hypothesis explaining the evidence. Output JSON: {hypothesis, reasoning, confidence}"),
                        LLMMessage(role=MessageRole.USER,
                                   content=f"Question: {pack.task_question}\nEvidence:\n{ev_text}"),
                    ],
                    temperature=0.3, max_tokens=300))
                state.hypotheses_generated.append(resp.output_text[:200])
                total_tokens += resp.usage.total_tokens
            except Exception:
                pass

        elif op == "reason":
            retrieved = state.get_all_retrieved()
            ev_text = "\n".join(f"- {r['content'][:100]}" for r in retrieved)
            hyp_text = "\n".join(f"- {h[:100]}" for h in state.hypotheses_generated)
            try:
                resp = await client.generate(LLMGenerationRequest(
                    model=MODEL_NAME,
                    messages=[
                        LLMMessage(role=MessageRole.SYSTEM,
                                   content="Evaluate hypotheses against evidence. Output JSON: {evaluations: [{hypothesis, score, reasoning}]}"),
                        LLMMessage(role=MessageRole.USER,
                                   content=f"Question: {pack.task_question}\nHypotheses:\n{hyp_text}\nEvidence:\n{ev_text}"),
                    ],
                    temperature=0.3, max_tokens=400))
                state.reasoning_artifacts.append(resp.output_text[:200])
                total_tokens += resp.usage.total_tokens
            except Exception:
                pass

        elif op in ("synthesize", "revise"):
            retrieved = state.get_all_retrieved()
            ev_text = "\n".join(f"- [{r['item_id']}] {r['content'][:80]}" for r in retrieved)
            hyp_text = "\n".join(state.hypotheses_generated[:3]) if state.hypotheses_generated else "(none)"
            critique_text = "\n".join(state.attack_artifacts[:2]) if state.attack_artifacts else ""

            instruction = "Synthesize a final conclusion" if op == "synthesize" else "Revise your conclusion based on critique"
            try:
                resp = await client.generate(LLMGenerationRequest(
                    model=MODEL_NAME,
                    messages=[
                        LLMMessage(role=MessageRole.SYSTEM,
                                   content=f"{instruction}. Reference specific evidence. Address contradictions. State uncertainty. Output JSON: {{conclusion, confidence, supporting_evidence, caveats}}"),
                        LLMMessage(role=MessageRole.USER,
                                   content=f"Question: {pack.task_question}\nEvidence:\n{ev_text}\nHypotheses:\n{hyp_text}\n{f'Critique: {critique_text}' if critique_text else ''}"),
                    ],
                    temperature=0.3, max_tokens=500))
                total_tokens += resp.usage.total_tokens

                retrieved_ids = [r["item_id"] for r in retrieved]
                scores = score_agent_output(resp.output_text, pack, retrieved_ids)
                elapsed = (time.perf_counter() - start) * 1000

                return {
                    "pack_id": pack.pack_id,
                    "domain": pack.domain,
                    "sequence_name": sequence_name,
                    "scores": scores,
                    "composite": scores["composite"],
                    "total_tokens": total_tokens,
                    "latency_ms": elapsed,
                    "evidence_retrieved": len(state.retrieved_indices),
                    "hypotheses_generated": len(state.hypotheses_generated),
                }
            except Exception as exc:
                return {
                    "pack_id": pack.pack_id, "domain": pack.domain,
                    "sequence_name": sequence_name, "error": str(exc)[:200],
                    "composite": 0,
                }

        elif op == "critique":
            retrieved = state.get_all_retrieved()
            ev_text = "\n".join(f"- {r['content'][:80]}" for r in retrieved)
            try:
                resp = await client.generate(LLMGenerationRequest(
                    model=MODEL_NAME,
                    messages=[
                        LLMMessage(role=MessageRole.SYSTEM,
                                   content="Critique the current analysis. Identify weaknesses, missing evidence, alternative explanations."),
                        LLMMessage(role=MessageRole.USER,
                                   content=f"Question: {pack.task_question}\nEvidence:\n{ev_text}\nCurrent hypotheses:\n{chr(10).join(state.hypotheses_generated[:2])}"),
                    ],
                    temperature=0.3, max_tokens=300))
                state.attack_artifacts.append(resp.output_text[:200])
                total_tokens += resp.usage.total_tokens
            except Exception:
                pass

    elapsed = (time.perf_counter() - start) * 1000
    return {
        "pack_id": pack.pack_id, "domain": pack.domain,
        "sequence_name": sequence_name,
        "composite": 0, "total_tokens": total_tokens,
        "latency_ms": elapsed, "note": "sequence did not reach synthesis",
    }


async def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("PHASE 27 — STATIC REAL-EVIDENCE BENCHMARK")
    print("=" * 70)

    # Step 1: Generate packs
    packs = save_all_packs()
    print(f"\n  Evidence packs generated: {len(packs)}")
    print(f"  Domains: {set(p.domain for p in packs)}")

    # Step 2: Check for LLM
    base_url = os.environ.get("ASAR_OPENAI_BASE_URL")
    if not base_url:
        print("""
  MODEL SERVER: NOT CONFIGURED
  Evidence packs are saved and ready.
  To execute Phase 27 with LLM:
    1. Start model server
    2. Set ASAR_OPENAI_BASE_URL and ASAR_MODEL_NAME
    3. Re-run this script

  PROTOCOL SAVED. EXECUTION BLOCKED.
        """)

        (RESULTS_DIR / "phase27_protocol.json").write_text(json.dumps({
            "status": "PROTOCOL_READY",
            "packs_generated": len(packs),
            "domains": list(set(p.domain for p in packs)),
            "conditions": list(STATIC_SEQUENCES.keys()),
            "metrics": ["claim_correctness", "evidence_support", "decisive_coverage",
                        "contradiction_handling", "calibration", "source_independence"],
            "model_required": True,
            "model_available": False,
        }, indent=2))
        return

    # Step 3: Run all conditions
    from asar.providers.chat_completions_llm import ChatCompletionsLLMClient
    client = ChatCompletionsLLMClient(base_url=base_url)

    all_results: list[dict] = []
    for pack in packs:
        for seq_name, seq in STATIC_SEQUENCES.items():
            result = await run_static_sequence_llm(pack, seq_name, seq, client)
            all_results.append(result)
            print(f"  {pack.pack_id:12s} {seq_name:20s} composite={result.get('composite', 0):.3f}")

    # Step 4: Analyze
    by_condition = defaultdict(list)
    by_domain = defaultdict(lambda: defaultdict(list))
    for r in all_results:
        by_condition[r["sequence_name"]].append(r.get("composite", 0))
        by_domain[r["domain"]][r["sequence_name"]].append(r.get("composite", 0))

    print(f"\n  {'Condition':25s} {'Mean':>8s} {'Std':>8s} {'N':>4s}")
    print("  " + "-" * 50)
    for name, scores in sorted(by_condition.items(), key=lambda x: -statistics.mean(x[1])):
        m = statistics.mean(scores)
        s = statistics.stdev(scores) if len(scores) > 1 else 0
        print(f"  {name:25s} {m:7.3f} {s:8.3f} {len(scores):4d}")

    with open(RESULTS_DIR / "phase27_static_evidence.jsonl", "w") as f:
        for r in all_results:
            f.write(json.dumps(r, default=str) + "\n")

    (RESULTS_DIR / "phase27_summary.json").write_text(json.dumps({
        "conditions": {k: {
            "mean": round(statistics.mean(v), 4),
            "std": round(statistics.stdev(v) if len(v) > 1 else 0, 4),
            "n": len(v),
        } for k, v in by_condition.items()},
        "domains": {d: {c: {
            "mean": round(statistics.mean(scores), 4),
            "n": len(scores),
        } for c, scores in conds.items()} for d, conds in by_domain.items()},
    }, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
