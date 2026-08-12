"""
Campaign V6 Completion — Semantic Causality & External Transfer.

Tests H-REE-20 (semantic mediation) and H-REE-23 (exogenous transfer).

Usage:
    python experiments/campaign_v6/run_completion.py --phase sim_intervention
    python experiments/campaign_v6/run_completion.py --phase scifact
    python experiments/campaign_v6/run_completion.py --phase hotpotqa
    python experiments/campaign_v6/run_completion.py --phase all
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
V6_BASE_SEED = 314159
TEMPERATURE = 0.0
MAX_TOKENS_OP = 512
TIMEOUT = 120.0

NEUTRAL_SYSTEM = (
    "You are a research assistant. Restate the research context "
    "and relevant entities WITHOUT proposing an explanation, answer, "
    "hypothesis, evidence target, or reasoning conclusion. "
    "Simply describe what is known so far. Output ONLY a factual restatement."
)

EXPANSION_SYSTEM = (
    "You are a search query optimizer. Expand the given question into "
    "a richer search query with related terms, synonyms, and concepts. "
    "Do NOT hypothesize or answer. Output ONLY the expanded query text."
)

HYPOTHESIS_SYSTEM = (
    "You are a research scientist. Given evidence and a question, generate "
    "a plausible hypothesis. Output ONLY valid JSON: "
    "{\"hypothesis\": \"...\", \"reasoning\": \"...\", \"confidence\": 0.0-1.0}"
)

QUERY_FROM_HYPOTHESIS_SYSTEM = (
    "You are a research strategist. Given a hypothesis, generate a targeted "
    "search query to find evidence that would test this hypothesis. "
    "Output ONLY valid JSON: {\"query\": \"...\", \"rationale\": \"...\"}"
)

QUERY_DIRECT_SYSTEM = (
    "You are a research strategist. Generate a search query to find "
    "relevant evidence for answering the given question. "
    "Output ONLY valid JSON: {\"query\": \"...\", \"rationale\": \"...\"}"
)

REASON_SYSTEM = (
    "You are a research analyst. Given a question, a hypothesis (if any), "
    "and evidence, evaluate the hypothesis and produce a final answer. "
    "Output ONLY valid JSON: {\"answer\": \"...\", \"verdict\": \"SUPPORTS|REFUTES|NOT_ENOUGH_INFO\", "
    "\"confidence\": 0.0-1.0, \"supporting_evidence\": [\"...\"]}"
)


def _make_client() -> ChatCompletionsLLMClient:
    return ChatCompletionsLLMClient(base_url=BASE_URL, timeout=TIMEOUT)


def _ts() -> str:
    return time.strftime("%H:%M:%S")


def _parse_json(text: str) -> dict | None:
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


async def llm_call(
    client: ChatCompletionsLLMClient,
    model_id: str,
    system: str,
    user: str,
) -> tuple[str, dict]:
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
            "prompt_chars": len(system) + len(user),
            "response_chars": len(resp.output_text),
        }
        return resp.output_text, usage
    except Exception as e:
        return f"ERROR: {e}", {
            "input_tokens": 0, "output_tokens": 0,
            "latency": time.time() - t0, "error": str(e),
            "prompt_chars": len(system) + len(user), "response_chars": 0,
        }


# ===================================================================
# SIMULATOR SEMANTIC INTERVENTION (H-REE-20 on controlled worlds)
# ===================================================================


def generate_v6_worlds(n_per_regime: int = 4) -> list[LatentWorld]:
    worlds = []
    for regime_name, generator in V4_REGIME_GENERATORS.items():
        for i in range(n_per_regime):
            seed = V6_BASE_SEED + abs(hash(regime_name)) % 10000 + i
            world = generator(index=i, seed=seed)
            world.world_id = f"{regime_name}_{V6_BASE_SEED}_{i}"
            worlds.append(world)
    return worlds


def _query_conditioned_retrieve(sim, query):
    available = [
        e for e in sim.world.evidence_pool
        if e.evidence_id not in sim._retrieved and e.is_accessible
    ]
    if not available:
        return None
    if query and query.strip():
        qw = set(w.lower() for w in query.split() if len(w) > 2)
        scored = []
        for e in available:
            cw = set(w.lower() for w in e.content.split() if len(w) > 2)
            scored.append((len(qw & cw), e.information_value, e))
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
    }


def _bind_hypothesis(llm_text, sim, evidence):
    candidates = [
        h for hid, h in sim.world.hypotheses.items()
        if hid not in sim._generated_hypotheses
    ]
    if not candidates:
        return None
    best_match, best_score = None, -1
    if llm_text:
        lw = set(w.lower() for w in llm_text.split() if len(w) > 2)
        for h in candidates:
            hw = set(w.lower() for w in h.statement.split() if len(w) > 2)
            s = len(lw & hw)
            if s > best_score:
                best_score = s
                best_match = h
    if best_score < 2:
        eids = [e["evidence_id"] for e in evidence]
        hints = []
        for eid in eids:
            for e in sim.world.evidence_pool:
                if e.evidence_id == eid:
                    hints.extend(e.supports_hypotheses)
                    break
        prioritized = sorted(candidates,
            key=lambda h: (1.0 if h.hypothesis_id in hints else 0.0, h.initial_plausibility),
            reverse=True)
        best_match = prioritized[0]
        best_score = 0
    if best_match is None:
        return None
    sim._generated_hypotheses.add(best_match.hypothesis_id)
    return {
        "hypothesis_id": best_match.hypothesis_id,
        "statement": best_match.statement,
        "initial_plausibility": best_match.initial_plausibility,
        "llm_text": llm_text,
        "binding_score": best_score,
    }


async def _sim_condition(client, model_id, world, condition, artifact_text=None):
    """Run one condition on one simulator world.

    Pipeline: artifact_generation → query → retrieve → reason → evaluate.
    All conditions except DIRECT use 4 LLM calls.
    DIRECT uses 3 LLM calls (no artifact generation).
    """
    sim = EpistemicWorldSimulator(world, seed=42)
    trace = {"condition": condition, "world_id": world.world_id, "calls": 0}
    evidence = []
    hypotheses = []
    posteriors = {}
    hidden_vars = set()

    ev_text = "(no evidence yet)"
    true_hyp = world.hypotheses.get(world.true_hypothesis_id)
    task_desc = f"Task: determine which hypothesis is correct among {len(world.hypotheses)} candidates."
    if true_hyp:
        h_stmts = [h.statement for h in world.hypotheses.values()]
        task_desc = f"Determine which of these explanations is correct: {'; '.join(h_stmts[:3])}"

    # --- STEP 1: Artifact generation ---
    if condition == "REAL":
        text, u = await llm_call(client, model_id, HYPOTHESIS_SYSTEM,
            f"Context: {task_desc}\nEvidence: {ev_text}\n\nGenerate a hypothesis.")
        trace["calls"] += 1
        trace["artifact_raw"] = text[:300]
        trace["artifact_chars"] = len(text)
        parsed = _parse_json(text) or {"hypothesis": text[:200]}
        hyp = _bind_hypothesis(parsed.get("hypothesis", text[:200]), sim, evidence)
        if hyp:
            hypotheses.append(hyp)
            posteriors[hyp["hypothesis_id"]] = hyp["initial_plausibility"]
            trace["bound_hyp_id"] = hyp["hypothesis_id"]
            trace["bound_correct"] = (hyp["hypothesis_id"] == world.true_hypothesis_id)

    elif condition == "SHUFFLED":
        if artifact_text is None:
            artifact_text = "Some hypothesis from another domain."
        text = artifact_text
        trace["artifact_raw"] = text[:300]
        trace["artifact_chars"] = len(text)
        # Still make an LLM call for compute matching
        _, u = await llm_call(client, model_id, HYPOTHESIS_SYSTEM,
            f"Context: {task_desc}\nEvidence: {ev_text}\n\nGenerate a hypothesis.")
        trace["calls"] += 1
        hyp = _bind_hypothesis(text, sim, evidence)
        if hyp:
            hypotheses.append(hyp)
            posteriors[hyp["hypothesis_id"]] = hyp["initial_plausibility"]
            trace["bound_hyp_id"] = hyp["hypothesis_id"]
            trace["bound_correct"] = (hyp["hypothesis_id"] == world.true_hypothesis_id)

    elif condition == "NEUTRAL":
        text, u = await llm_call(client, model_id, NEUTRAL_SYSTEM,
            f"Context: {task_desc}\nEvidence: {ev_text}\n\nRestate the context factually.")
        trace["calls"] += 1
        trace["artifact_raw"] = text[:300]
        trace["artifact_chars"] = len(text)
        # Neutral does NOT bind to a hypothesis — that's the point
        # Use the sim's default hypothesis generation path without LLM input
        sim_hyp = sim.generate_hypothesis([])
        if sim_hyp:
            hypotheses.append(sim_hyp)
            posteriors[sim_hyp["hypothesis_id"]] = sim_hyp["initial_plausibility"]

    elif condition == "GENERIC_EXPANSION":
        text, u = await llm_call(client, model_id, EXPANSION_SYSTEM,
            f"Question: {task_desc}\n\nExpand into a richer search query.")
        trace["calls"] += 1
        trace["artifact_raw"] = text[:300]
        trace["artifact_chars"] = len(text)
        sim_hyp = sim.generate_hypothesis([])
        if sim_hyp:
            hypotheses.append(sim_hyp)
            posteriors[sim_hyp["hypothesis_id"]] = sim_hyp["initial_plausibility"]

    elif condition == "DIRECT":
        # No artifact generation call — go straight to query
        sim_hyp = sim.generate_hypothesis([])
        if sim_hyp:
            hypotheses.append(sim_hyp)
            posteriors[sim_hyp["hypothesis_id"]] = sim_hyp["initial_plausibility"]

    # --- STEP 2: Query generation ---
    if hypotheses:
        h_fmt = "; ".join(f"[{h['hypothesis_id']}] {h['statement']}" for h in hypotheses)
        q_text, u = await llm_call(client, model_id, QUERY_FROM_HYPOTHESIS_SYSTEM,
            f"Hypothesis: {h_fmt}\n\nGenerate a search query to test this hypothesis.")
    else:
        q_text, u = await llm_call(client, model_id, QUERY_DIRECT_SYSTEM,
            f"Question: {task_desc}\n\nGenerate a search query.")
    trace["calls"] += 1
    trace["query_raw"] = q_text[:200]

    parsed_q = _parse_json(q_text)
    query = parsed_q.get("query", q_text[:100]) if parsed_q else q_text[:100]
    trace["query_used"] = query[:100]

    # --- STEP 3: Retrieve evidence ---
    ev = _query_conditioned_retrieve(sim, query)
    if ev:
        evidence.append(ev)
    ev2 = _query_conditioned_retrieve(sim, query)
    if ev2:
        evidence.append(ev2)
    trace["evidence_ids"] = [e["evidence_id"] for e in evidence]
    trace["evidence_count"] = len(evidence)

    # Compute gold evidence overlap
    gold_evidence_ids = set()
    for e in world.evidence_pool:
        if world.true_hypothesis_id in e.supports_hypotheses:
            gold_evidence_ids.add(e.evidence_id)
    retrieved_ids = set(trace["evidence_ids"])
    gold_recall = len(retrieved_ids & gold_evidence_ids) / max(1, len(gold_evidence_ids))
    trace["gold_evidence_recall"] = gold_recall
    trace["gold_evidence_total"] = len(gold_evidence_ids)

    # --- STEP 4: Reason ---
    if hypotheses and evidence:
        reason_out = sim.reason(
            [h["hypothesis_id"] for h in hypotheses],
            [e["evidence_id"] for e in evidence],
        )
        for hid, score in reason_out["consistency_scores"].items():
            posteriors[hid] = score

    ev_fmt = "\n".join(f"[{e['evidence_id']}] {e['content']}" for e in evidence) or "(none)"
    h_fmt = "; ".join(f"[{h['hypothesis_id']}] {h['statement']}" for h in hypotheses) or "(none)"
    r_text, u = await llm_call(client, model_id, REASON_SYSTEM,
        f"Question: {task_desc}\nHypothesis: {h_fmt}\nEvidence:\n{ev_fmt}\n\nEvaluate and answer.")
    trace["calls"] += 1
    trace["reason_raw"] = r_text[:200]

    # --- STEP 5: Evaluate ---
    ev_sources = {e["source_id"]: e.get("parent_source") for e in evidence}
    qvec = sim.evaluate(posteriors, hidden_vars, set(), ev_sources)
    trace["scalar_quality"] = qvec.scalar_quality()
    trace["quality_vector"] = qvec.to_dict()

    return trace


async def run_sim_intervention(client, model_id):
    """H-REE-20 on simulator: REAL vs SHUFFLED vs NEUTRAL."""
    print(f"\n{'='*60}")
    print(f"H-REE-20 -- SIMULATOR SEMANTIC INTERVENTION")
    print(f"{'='*60}\n")

    worlds = generate_v6_worlds()
    print(f"  Generated {len(worlds)} worlds")

    # Pre-generate REAL artifacts for shuffling
    print(f"  [{_ts()}] Pre-generating REAL artifacts for shuffle assignment...")
    real_artifacts = {}
    for w in worlds:
        sim = EpistemicWorldSimulator(w, seed=42)
        true_hyp = w.hypotheses.get(w.true_hypothesis_id)
        task_desc = f"Determine correct hypothesis among {len(w.hypotheses)} candidates."
        if true_hyp:
            stmts = [h.statement for h in w.hypotheses.values()]
            task_desc = f"Determine which is correct: {'; '.join(stmts[:3])}"
        text, _ = await llm_call(client, model_id, HYPOTHESIS_SYSTEM,
            f"Context: {task_desc}\nEvidence: (no evidence yet)\n\nGenerate a hypothesis.")
        real_artifacts[w.world_id] = text
    print(f"    Generated {len(real_artifacts)} artifacts")

    # Create deterministic shuffle pairing
    world_ids = sorted(real_artifacts.keys())
    shuffle_map = {}
    for i, wid in enumerate(world_ids):
        partner = world_ids[(i + 7) % len(world_ids)]  # deterministic offset
        if partner == wid:
            partner = world_ids[(i + 1) % len(world_ids)]
        shuffle_map[wid] = real_artifacts[partner]

    # Manipulation check: real vs shuffled relevance
    print(f"  [{_ts()}] Running manipulation check...")
    manip_checks = []
    for w in worlds:
        real_text = real_artifacts[w.world_id]
        shuf_text = shuffle_map[w.world_id]
        real_words = set(wd.lower() for wd in real_text.split() if len(wd) > 3)
        shuf_words = set(wd.lower() for wd in shuf_text.split() if len(wd) > 3)
        # Task keywords from hypotheses
        task_words = set()
        for h in w.hypotheses.values():
            task_words.update(wd.lower() for wd in h.statement.split() if len(wd) > 3)
        real_relevance = len(real_words & task_words) / max(1, len(task_words))
        shuf_relevance = len(shuf_words & task_words) / max(1, len(task_words))
        manip_checks.append({
            "world_id": w.world_id,
            "real_relevance": real_relevance,
            "shuf_relevance": shuf_relevance,
            "real_len": len(real_text),
            "shuf_len": len(shuf_text),
            "length_ratio": len(shuf_text) / max(1, len(real_text)),
        })
    mean_real_rel = statistics.mean(m["real_relevance"] for m in manip_checks)
    mean_shuf_rel = statistics.mean(m["shuf_relevance"] for m in manip_checks)
    mean_len_ratio = statistics.mean(m["length_ratio"] for m in manip_checks)
    manip_pass = mean_real_rel > mean_shuf_rel
    print(f"    Real relevance: {mean_real_rel:.3f}")
    print(f"    Shuffled relevance: {mean_shuf_rel:.3f}")
    print(f"    Length ratio: {mean_len_ratio:.3f}")
    print(f"    Manipulation check: {'PASS' if manip_pass else 'FAIL'}")

    # Run conditions
    conditions = ["REAL", "SHUFFLED", "NEUTRAL", "GENERIC_EXPANSION", "DIRECT"]
    results = []

    for wi, w in enumerate(worlds):
        print(f"  [{_ts()}] World {wi+1}/{len(worlds)}: {w.world_id}")
        world_result = {"world_id": w.world_id}

        for cond in conditions:
            art = shuffle_map.get(w.world_id) if cond == "SHUFFLED" else None
            trace = await _sim_condition(client, model_id, w, cond, artifact_text=art)
            world_result[cond] = {
                "quality": trace["scalar_quality"],
                "gold_recall": trace.get("gold_evidence_recall", 0),
                "evidence_count": trace.get("evidence_count", 0),
                "calls": trace["calls"],
                "bound_correct": trace.get("bound_correct", None),
                "artifact_chars": trace.get("artifact_chars", 0),
            }
            print(f"    {cond}: Q={trace['scalar_quality']:.4f} recall={trace.get('gold_evidence_recall', 0):.3f} calls={trace['calls']}")

        results.append(world_result)

    # Save results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"semantic_intervention_{model_id.replace(':', '_')}.jsonl"
    with open(out, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    # Save manipulation check
    mc_out = RESULTS_DIR / "manipulation_check.json"
    mc_out.write_text(json.dumps({
        "mean_real_relevance": mean_real_rel,
        "mean_shuffled_relevance": mean_shuf_rel,
        "mean_length_ratio": mean_len_ratio,
        "pass": manip_pass,
        "per_world": manip_checks,
    }, indent=2))

    # Analysis
    print(f"\n  --- H-REE-20 Simulator Results ---")
    for cond in conditions:
        quals = [r[cond]["quality"] for r in results]
        recalls = [r[cond]["gold_recall"] for r in results]
        print(f"  {cond:20s}: Q={statistics.mean(quals):.4f} +/- {statistics.stdev(quals):.4f}  "
              f"recall={statistics.mean(recalls):.3f}")

    # Primary contrast: REAL vs SHUFFLED
    diffs_q = [r["REAL"]["quality"] - r["SHUFFLED"]["quality"] for r in results]
    diffs_r = [r["REAL"]["gold_recall"] - r["SHUFFLED"]["gold_recall"] for r in results]
    mean_dq = statistics.mean(diffs_q)
    mean_dr = statistics.mean(diffs_r)
    se_dq = statistics.stdev(diffs_q) / len(diffs_q)**0.5 if len(diffs_q) > 1 else 0
    se_dr = statistics.stdev(diffs_r) / len(diffs_r)**0.5 if len(diffs_r) > 1 else 0
    print(f"\n  REAL - SHUFFLED (quality): {mean_dq:+.4f} (95% CI [{mean_dq-1.96*se_dq:+.4f}, {mean_dq+1.96*se_dq:+.4f}])")
    print(f"  REAL - SHUFFLED (recall):  {mean_dr:+.4f} (95% CI [{mean_dr-1.96*se_dr:+.4f}, {mean_dr+1.96*se_dr:+.4f}])")

    print(f"\n  Saved: {out}")
    print(f"  Saved: {mc_out}")

    return results, manip_pass


# ===================================================================
# EXTERNAL DATASET: SCIFACT (H-REE-23)
# ===================================================================


async def _download_scifact(data_dir: Path):
    """Download SciFact dataset if not present."""
    corpus_file = data_dir / "corpus.jsonl"
    claims_file = data_dir / "claims_dev.jsonl"

    if corpus_file.exists() and claims_file.exists():
        print(f"  SciFact already downloaded")
        return

    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading SciFact from S3...")

    import tarfile
    import tempfile
    import urllib.request

    tar_url = "https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz"
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        urllib.request.urlretrieve(tar_url, tmp_path)
        with tarfile.open(tmp_path, "r:gz") as tar:
            for member in tar.getmembers():
                basename = Path(member.name).name
                if basename in ("corpus.jsonl", "claims_dev.jsonl", "claims_train.jsonl"):
                    member.name = basename
                    tar.extract(member, path=str(data_dir))
        print(f"  Downloaded and extracted SciFact")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _load_scifact(data_dir: Path) -> tuple[dict, list]:
    """Load SciFact corpus and claims."""
    corpus = {}
    with open(data_dir / "corpus.jsonl") as f:
        for line in f:
            doc = json.loads(line)
            doc_id = str(doc["doc_id"])
            abstract = " ".join(doc.get("abstract", []))
            corpus[doc_id] = {
                "doc_id": doc_id,
                "title": doc.get("title", ""),
                "abstract": abstract,
            }

    claims = []
    with open(data_dir / "claims_dev.jsonl") as f:
        for line in f:
            c = json.loads(line)
            gold_docs = {}
            if c.get("evidence"):
                for doc_id_str, sents in c["evidence"].items():
                    gold_docs[doc_id_str] = sents
            claims.append({
                "id": c["id"],
                "claim": c["claim"],
                "label": c.get("label", "NOT_ENOUGH_INFO"),
                "gold_doc_ids": list(gold_docs.keys()),
                "gold_evidence": gold_docs,
            })

    return corpus, claims


def _bm25_retrieve(query: str, corpus: dict, k: int = 5) -> list[dict]:
    """Simple BM25-like keyword retrieval."""
    qwords = set(w.lower() for w in query.split() if len(w) > 2)
    if not qwords:
        return list(corpus.values())[:k]

    scored = []
    for doc_id, doc in corpus.items():
        text = f"{doc['title']} {doc['abstract']}"
        dwords = set(w.lower() for w in text.split() if len(w) > 2)
        overlap = len(qwords & dwords)
        scored.append((overlap, doc_id, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[2] for s in scored[:k]]


async def _scifact_condition(client, model_id, claim, corpus, condition, artifact_text=None):
    """Run one condition on one SciFact claim."""
    trace = {"condition": condition, "claim_id": claim["id"], "calls": 0}
    question = claim["claim"]

    # --- STEP 1: Artifact generation ---
    if condition == "REAL":
        text, u = await llm_call(client, model_id, HYPOTHESIS_SYSTEM,
            f"Scientific claim: {question}\n\nGenerate a hypothesis about whether this claim is supported by evidence.")
        trace["calls"] += 1
        trace["artifact_raw"] = text[:300]
        trace["artifact_chars"] = len(text)

    elif condition == "SHUFFLED":
        text = artifact_text or "A hypothesis from another domain."
        _, u = await llm_call(client, model_id, HYPOTHESIS_SYSTEM,
            f"Scientific claim: {question}\n\nGenerate a hypothesis about whether this claim is supported by evidence.")
        trace["calls"] += 1
        trace["artifact_raw"] = text[:300]
        trace["artifact_chars"] = len(text)

    elif condition == "NEUTRAL":
        text, u = await llm_call(client, model_id, NEUTRAL_SYSTEM,
            f"Scientific claim: {question}\n\nRestate the key entities and relationships.")
        trace["calls"] += 1
        trace["artifact_raw"] = text[:300]
        trace["artifact_chars"] = len(text)

    elif condition == "GENERIC_EXPANSION":
        text, u = await llm_call(client, model_id, EXPANSION_SYSTEM,
            f"Question: Is the following claim supported? {question}\n\nExpand into search terms.")
        trace["calls"] += 1
        trace["artifact_raw"] = text[:300]
        trace["artifact_chars"] = len(text)

    elif condition == "DIRECT":
        text = ""

    # --- STEP 2: Query ---
    if condition in ("REAL", "SHUFFLED") and text:
        q_text, u = await llm_call(client, model_id, QUERY_FROM_HYPOTHESIS_SYSTEM,
            f"Hypothesis: {text[:300]}\n\nGenerate a search query to find evidence.")
        trace["calls"] += 1
    elif condition == "GENERIC_EXPANSION":
        q_text = text  # expansion IS the query
    else:
        q_text, u = await llm_call(client, model_id, QUERY_DIRECT_SYSTEM,
            f"Question: Is this claim supported? {question}\n\nGenerate a search query.")
        trace["calls"] += 1
    trace["query_raw"] = q_text[:200] if q_text else ""

    parsed_q = _parse_json(q_text) if q_text else None
    query = parsed_q.get("query", q_text[:200]) if parsed_q else (q_text[:200] if q_text else question)

    # --- STEP 3: Retrieve ---
    retrieved = _bm25_retrieve(query, corpus, k=5)
    trace["retrieved_doc_ids"] = [d["doc_id"] for d in retrieved]

    gold_ids = set(claim["gold_doc_ids"])
    retrieved_ids = set(trace["retrieved_doc_ids"])
    recall = len(retrieved_ids & gold_ids) / max(1, len(gold_ids)) if gold_ids else 0
    precision = len(retrieved_ids & gold_ids) / max(1, len(retrieved_ids)) if retrieved_ids else 0
    trace["gold_doc_recall"] = recall
    trace["gold_doc_precision"] = precision

    # --- STEP 4: Reason + Answer ---
    ev_text = "\n".join(f"[{d['doc_id']}] {d['title']}: {d['abstract'][:300]}" for d in retrieved[:3])
    hyp_text = text[:200] if text else "(no hypothesis)"
    r_text, u = await llm_call(client, model_id, REASON_SYSTEM,
        f"Claim: {question}\nHypothesis: {hyp_text}\nEvidence:\n{ev_text}\n\nDoes the evidence support or refute the claim?")
    trace["calls"] += 1
    trace["answer_raw"] = r_text[:200]

    parsed_a = _parse_json(r_text)
    predicted_verdict = "NOT_ENOUGH_INFO"
    if parsed_a:
        predicted_verdict = parsed_a.get("verdict", "NOT_ENOUGH_INFO")
    else:
        rl = r_text.lower()
        if "support" in rl:
            predicted_verdict = "SUPPORTS"
        elif "refute" in rl:
            predicted_verdict = "REFUTES"

    trace["predicted_verdict"] = predicted_verdict
    trace["gold_label"] = claim["label"]
    trace["correct"] = (predicted_verdict.upper() == claim["label"].upper())

    return trace


async def run_scifact(client, model_id):
    """H-REE-23 on SciFact."""
    print(f"\n{'='*60}")
    print(f"H-REE-23 -- SCIFACT EXTERNAL TRANSFER")
    print(f"{'='*60}\n")

    data_dir = Path(__file__).parent / "data" / "scifact"
    await _download_scifact(data_dir)

    corpus, claims = _load_scifact(data_dir)
    print(f"  Corpus: {len(corpus)} documents")
    print(f"  Claims: {len(claims)} (dev set)")

    # Filter to claims with gold evidence (meaningful for retrieval evaluation)
    evaluable = [c for c in claims if c["gold_doc_ids"]]
    print(f"  Evaluable (with gold evidence): {len(evaluable)}")

    # Hash and freeze split
    split_hash = hashlib.sha256(json.dumps([c["id"] for c in evaluable]).encode()).hexdigest()[:16]
    print(f"  Task ID hash: {split_hash}")

    # Limit to manageable N for locked execution
    locked_n = min(100, len(evaluable))
    locked_claims = evaluable[:locked_n]
    print(f"  LOCKED N: {locked_n}")

    # Pre-generate REAL artifacts for shuffling (with retry)
    print(f"  [{_ts()}] Pre-generating artifacts for shuffle...")
    real_artifacts = {}
    artifact_cache = RESULTS_DIR / f"scifact_artifacts_{model_id.replace(':', '_')}.json"
    if artifact_cache.exists():
        real_artifacts = json.loads(artifact_cache.read_text())
        real_artifacts = {int(k): v for k, v in real_artifacts.items()}
        print(f"    Loaded {len(real_artifacts)} cached artifacts")

    for ci, c in enumerate(locked_claims):
        if c["id"] in real_artifacts:
            continue
        for retry in range(3):
            try:
                text, _ = await llm_call(client, model_id, HYPOTHESIS_SYSTEM,
                    f"Scientific claim: {c['claim']}\n\nGenerate a hypothesis about whether this claim is supported.")
                if "ERROR:" not in text:
                    real_artifacts[c["id"]] = text
                    break
            except Exception as e:
                print(f"    Retry {retry+1}/3 for claim {c['id']}: {e}")
                import asyncio as _aio
                await _aio.sleep(5)
        else:
            real_artifacts[c["id"]] = f"Unable to generate hypothesis for claim {c['id']}"
        if (ci + 1) % 20 == 0:
            print(f"    Pre-generated {ci+1}/{locked_n} artifacts")
            artifact_cache.write_text(json.dumps({str(k): v for k, v in real_artifacts.items()}, indent=2))
    artifact_cache.write_text(json.dumps({str(k): v for k, v in real_artifacts.items()}, indent=2))
    print(f"    Pre-generated {len(real_artifacts)} total artifacts")

    # Deterministic shuffle
    claim_ids = sorted(real_artifacts.keys())
    shuffle_map = {}
    for i, cid in enumerate(claim_ids):
        partner = claim_ids[(i + 7) % len(claim_ids)]
        if partner == cid:
            partner = claim_ids[(i + 1) % len(claim_ids)]
        shuffle_map[cid] = real_artifacts[partner]

    # Run conditions with incremental save and resume support
    conditions = ["DIRECT", "NEUTRAL", "GENERIC_EXPANSION", "REAL", "SHUFFLED"]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"scifact_{model_id.replace(':', '_')}.jsonl"

    done_ids: set[int] = set()
    results = []
    if out.exists():
        with open(out) as f:
            for line in f:
                r = json.loads(line)
                results.append(r)
                done_ids.add(r["claim_id"])
        print(f"  Resuming: {len(done_ids)} claims already completed")

    batch_limit = int(os.environ.get("V6_BATCH_SIZE", "0"))
    batch_done = 0

    for ci, claim in enumerate(locked_claims):
        if claim["id"] in done_ids:
            continue
        if batch_limit > 0 and batch_done >= batch_limit:
            print(f"  Batch limit {batch_limit} reached, stopping. Rerun to continue.")
            break
        if (ci + 1) % 10 == 0 or ci == 0:
            print(f"  [{_ts()}] Claim {ci+1}/{locked_n}: {claim['claim'][:60]}...")

        claim_result = {"claim_id": claim["id"], "label": claim["label"]}
        for cond in conditions:
            art = shuffle_map.get(claim["id"]) if cond == "SHUFFLED" else None
            trace = await _scifact_condition(client, model_id, claim, corpus, cond, artifact_text=art)
            claim_result[cond] = {
                "correct": trace["correct"],
                "predicted": trace["predicted_verdict"],
                "gold_recall": trace["gold_doc_recall"],
                "gold_precision": trace["gold_doc_precision"],
                "calls": trace["calls"],
                "artifact_chars": trace.get("artifact_chars", 0),
            }
        results.append(claim_result)
        with open(out, "a") as f:
            f.write(json.dumps(claim_result) + "\n")
        batch_done += 1

    # Analysis
    print(f"\n  --- SciFact Results (N={locked_n}) ---")
    for cond in conditions:
        accs = [r[cond]["correct"] for r in results]
        recalls = [r[cond]["gold_recall"] for r in results]
        acc = statistics.mean(accs)
        recall = statistics.mean(recalls)
        print(f"  {cond:20s}: accuracy={acc:.3f}  gold_recall={recall:.3f}")

    # Primary contrast
    real_acc = [1 if r["REAL"]["correct"] else 0 for r in results]
    shuf_acc = [1 if r["SHUFFLED"]["correct"] else 0 for r in results]
    real_rec = [r["REAL"]["gold_recall"] for r in results]
    shuf_rec = [r["SHUFFLED"]["gold_recall"] for r in results]

    diff_acc = [real_acc[i] - shuf_acc[i] for i in range(len(results))]
    diff_rec = [real_rec[i] - shuf_rec[i] for i in range(len(results))]
    m_acc = statistics.mean(diff_acc)
    m_rec = statistics.mean(diff_rec)
    se_acc = statistics.stdev(diff_acc) / len(diff_acc)**0.5 if len(diff_acc) > 1 else 0
    se_rec = statistics.stdev(diff_rec) / len(diff_rec)**0.5 if len(diff_rec) > 1 else 0

    print(f"\n  REAL - SHUFFLED (accuracy): {m_acc:+.4f} (95% CI [{m_acc-1.96*se_acc:+.4f}, {m_acc+1.96*se_acc:+.4f}])")
    print(f"  REAL - SHUFFLED (recall):   {m_rec:+.4f} (95% CI [{m_rec-1.96*se_rec:+.4f}, {m_rec+1.96*se_rec:+.4f}])")

    print(f"\n  Saved: {out}")
    return results


# ===================================================================
# EXTERNAL DATASET: HOTPOTQA (H-REE-23)
# ===================================================================


async def _download_hotpotqa(data_dir: Path):
    """Download HotpotQA distractor dev set."""
    dev_file = data_dir / "hotpot_dev_distractor.json"
    if dev_file.exists():
        print(f"  HotpotQA already downloaded")
        return

    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading HotpotQA dev distractor...")
    import urllib.request
    urls = [
        "http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json",
        "https://rajpurkar.github.io/SQuAD-explorer/dataset/hotpot_dev_distractor_v1.json",
    ]
    downloaded = False
    for url in urls:
        try:
            urllib.request.urlretrieve(url, str(dev_file))
            print(f"  Downloaded {dev_file.stat().st_size // 1024 // 1024}MB from {url}")
            downloaded = True
            break
        except Exception as e:
            print(f"  Failed {url}: {e}")
    if not downloaded:
        raise RuntimeError("Could not download HotpotQA from any source")


def _load_hotpotqa(data_dir: Path, max_n: int = 200) -> list[dict]:
    """Load HotpotQA distractor setting."""
    with open(data_dir / "hotpot_dev_distractor.json") as f:
        data = json.load(f)

    tasks = []
    for item in data[:max_n]:
        paragraphs = {}
        for title, sents in item["context"]:
            paragraphs[title] = " ".join(sents)

        gold_titles = set()
        for sf in item.get("supporting_facts", []):
            gold_titles.add(sf[0])

        tasks.append({
            "id": item["_id"],
            "question": item["question"],
            "answer": item["answer"],
            "type": item.get("type", ""),
            "level": item.get("level", ""),
            "paragraphs": paragraphs,
            "gold_titles": list(gold_titles),
        })

    return tasks


def _hotpot_retrieve(query: str, paragraphs: dict, k: int = 3) -> list[tuple[str, str]]:
    """BM25-like retrieval over HotpotQA distractor paragraphs."""
    qw = set(w.lower() for w in query.split() if len(w) > 2)
    scored = []
    for title, text in paragraphs.items():
        tw = set(w.lower() for w in f"{title} {text}".split() if len(w) > 2)
        scored.append((len(qw & tw), title, text))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(s[1], s[2]) for s in scored[:k]]


HOTPOT_REASON_SYSTEM = (
    "You are a research analyst. Given a question and evidence passages, "
    "provide a short factual answer. Output ONLY valid JSON: "
    "{\"answer\": \"...\", \"reasoning\": \"...\", \"confidence\": 0.0-1.0}"
)


async def _hotpot_condition(client, model_id, task, condition, artifact_text=None):
    """Run one condition on one HotpotQA question."""
    trace = {"condition": condition, "task_id": task["id"], "calls": 0}
    question = task["question"]

    # STEP 1: Artifact
    if condition == "REAL":
        text, u = await llm_call(client, model_id, HYPOTHESIS_SYSTEM,
            f"Question: {question}\n\nGenerate a hypothesis about the likely answer.")
        trace["calls"] += 1
        trace["artifact_chars"] = len(text)
    elif condition == "SHUFFLED":
        text = artifact_text or "A hypothesis from another domain."
        _, u = await llm_call(client, model_id, HYPOTHESIS_SYSTEM,
            f"Question: {question}\n\nGenerate a hypothesis about the likely answer.")
        trace["calls"] += 1
        trace["artifact_chars"] = len(text)
    elif condition == "NEUTRAL":
        text, u = await llm_call(client, model_id, NEUTRAL_SYSTEM,
            f"Question: {question}\n\nRestate key entities.")
        trace["calls"] += 1
        trace["artifact_chars"] = len(text)
    elif condition == "GENERIC_EXPANSION":
        text, u = await llm_call(client, model_id, EXPANSION_SYSTEM,
            f"Question: {question}\n\nExpand into search terms.")
        trace["calls"] += 1
        trace["artifact_chars"] = len(text)
    elif condition == "DIRECT":
        text = ""

    # STEP 2: Query
    if condition in ("REAL", "SHUFFLED") and text:
        q_text, u = await llm_call(client, model_id, QUERY_FROM_HYPOTHESIS_SYSTEM,
            f"Hypothesis: {text[:300]}\n\nGenerate a search query.")
        trace["calls"] += 1
    elif condition == "GENERIC_EXPANSION":
        q_text = text
    else:
        q_text, u = await llm_call(client, model_id, QUERY_DIRECT_SYSTEM,
            f"Question: {question}\n\nGenerate a search query.")
        trace["calls"] += 1

    parsed_q = _parse_json(q_text) if q_text else None
    query = parsed_q.get("query", q_text[:200]) if parsed_q else (q_text[:200] if q_text else question)

    # STEP 3: Retrieve
    retrieved = _hotpot_retrieve(query, task["paragraphs"], k=3)
    retrieved_titles = set(t for t, _ in retrieved)
    gold_titles = set(task["gold_titles"])
    recall = len(retrieved_titles & gold_titles) / max(1, len(gold_titles)) if gold_titles else 0
    trace["gold_title_recall"] = recall
    trace["retrieved_titles"] = list(retrieved_titles)

    # STEP 4: Answer
    ev_text = "\n".join(f"[{t}] {p[:300]}" for t, p in retrieved)
    hyp_text = text[:200] if text else "(none)"
    a_text, u = await llm_call(client, model_id, HOTPOT_REASON_SYSTEM,
        f"Question: {question}\nHypothesis: {hyp_text}\nEvidence:\n{ev_text}\n\nAnswer concisely.")
    trace["calls"] += 1
    trace["answer_raw"] = a_text[:200]

    parsed_a = _parse_json(a_text)
    predicted = parsed_a.get("answer", a_text[:100]) if parsed_a else a_text[:100]
    trace["predicted_answer"] = predicted[:200]

    # F1 scoring
    gold = task["answer"].lower().split()
    pred_tokens = predicted.lower().split()
    common = set(gold) & set(pred_tokens)
    if common:
        prec = len(common) / len(pred_tokens)
        rec = len(common) / len(gold)
        f1 = 2 * prec * rec / (prec + rec)
    else:
        f1 = 0.0
    em = 1.0 if predicted.strip().lower() == task["answer"].strip().lower() else 0.0
    trace["f1"] = f1
    trace["em"] = em

    return trace


async def run_hotpotqa(client, model_id):
    """H-REE-23 on HotpotQA."""
    print(f"\n{'='*60}")
    print(f"H-REE-23 -- HOTPOTQA EXTERNAL TRANSFER")
    print(f"{'='*60}\n")

    data_dir = Path(__file__).parent / "data" / "hotpotqa"
    await _download_hotpotqa(data_dir)

    tasks = _load_hotpotqa(data_dir, max_n=200)
    print(f"  Tasks loaded: {len(tasks)}")

    locked_n = min(100, len(tasks))
    locked_tasks = tasks[:locked_n]

    split_hash = hashlib.sha256(json.dumps([t["id"] for t in locked_tasks]).encode()).hexdigest()[:16]
    print(f"  Task ID hash: {split_hash}")
    print(f"  LOCKED N: {locked_n}")

    # Pre-generate artifacts for shuffle (with retry and cache)
    print(f"  [{_ts()}] Pre-generating artifacts...")
    real_artifacts = {}
    artifact_cache = RESULTS_DIR / f"hotpotqa_artifacts_{model_id.replace(':', '_')}.json"
    if artifact_cache.exists():
        real_artifacts = json.loads(artifact_cache.read_text())
        print(f"    Loaded {len(real_artifacts)} cached artifacts")

    for ti, t in enumerate(locked_tasks):
        if t["id"] in real_artifacts:
            continue
        for retry in range(3):
            try:
                text, _ = await llm_call(client, model_id, HYPOTHESIS_SYSTEM,
                    f"Question: {t['question']}\n\nGenerate a hypothesis about the likely answer.")
                if "ERROR:" not in text:
                    real_artifacts[t["id"]] = text
                    break
            except Exception as e:
                print(f"    Retry {retry+1}/3 for task {t['id']}: {e}")
                import asyncio as _aio
                await _aio.sleep(5)
        else:
            real_artifacts[t["id"]] = f"Unable to generate hypothesis for task {t['id']}"
        if (ti + 1) % 20 == 0:
            print(f"    Pre-generated {ti+1}/{locked_n} artifacts")
            artifact_cache.write_text(json.dumps(real_artifacts, indent=2))
    artifact_cache.write_text(json.dumps(real_artifacts, indent=2))
    print(f"    Pre-generated {len(real_artifacts)} total artifacts")

    task_ids = sorted(real_artifacts.keys())
    shuffle_map = {}
    for i, tid in enumerate(task_ids):
        partner = task_ids[(i + 7) % len(task_ids)]
        if partner == tid:
            partner = task_ids[(i + 1) % len(task_ids)]
        shuffle_map[tid] = real_artifacts[partner]

    # Run conditions with incremental save and resume
    conditions = ["DIRECT", "NEUTRAL", "GENERIC_EXPANSION", "REAL", "SHUFFLED"]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"hotpotqa_{model_id.replace(':', '_')}.jsonl"

    done_ids: set[str] = set()
    results = []
    if out.exists():
        with open(out) as f:
            for line in f:
                r = json.loads(line)
                results.append(r)
                done_ids.add(r["task_id"])
        print(f"  Resuming: {len(done_ids)} tasks already completed")

    batch_limit = int(os.environ.get("V6_BATCH_SIZE", "0"))
    batch_done = 0

    for ti, task in enumerate(locked_tasks):
        if task["id"] in done_ids:
            continue
        if batch_limit > 0 and batch_done >= batch_limit:
            print(f"  Batch limit {batch_limit} reached, stopping. Rerun to continue.")
            break
        if (ti + 1) % 10 == 0 or ti == 0:
            print(f"  [{_ts()}] Task {ti+1}/{locked_n}: {task['question'][:60]}...")

        task_result = {"task_id": task["id"], "answer": task["answer"]}
        for cond in conditions:
            art = shuffle_map.get(task["id"]) if cond == "SHUFFLED" else None
            trace = await _hotpot_condition(client, model_id, task, cond, artifact_text=art)
            task_result[cond] = {
                "f1": trace["f1"],
                "em": trace["em"],
                "gold_recall": trace["gold_title_recall"],
                "calls": trace["calls"],
                "artifact_chars": trace.get("artifact_chars", 0),
            }
        results.append(task_result)
        with open(out, "a") as f:
            f.write(json.dumps(task_result) + "\n")
        batch_done += 1

    # Analysis
    print(f"\n  --- HotpotQA Results (N={locked_n}) ---")
    for cond in conditions:
        f1s = [r[cond]["f1"] for r in results]
        recalls = [r[cond]["gold_recall"] for r in results]
        print(f"  {cond:20s}: F1={statistics.mean(f1s):.3f}  gold_recall={statistics.mean(recalls):.3f}")

    real_f1 = [r["REAL"]["f1"] for r in results]
    shuf_f1 = [r["SHUFFLED"]["f1"] for r in results]
    real_rec = [r["REAL"]["gold_recall"] for r in results]
    shuf_rec = [r["SHUFFLED"]["gold_recall"] for r in results]

    diff_f1 = [real_f1[i] - shuf_f1[i] for i in range(len(results))]
    diff_rec = [real_rec[i] - shuf_rec[i] for i in range(len(results))]
    m_f1 = statistics.mean(diff_f1)
    m_rec = statistics.mean(diff_rec)
    se_f1 = statistics.stdev(diff_f1) / len(diff_f1)**0.5 if len(diff_f1) > 1 else 0
    se_rec = statistics.stdev(diff_rec) / len(diff_rec)**0.5 if len(diff_rec) > 1 else 0

    print(f"\n  REAL - SHUFFLED (F1):       {m_f1:+.4f} (95% CI [{m_f1-1.96*se_f1:+.4f}, {m_f1+1.96*se_f1:+.4f}])")
    print(f"  REAL - SHUFFLED (recall):   {m_rec:+.4f} (95% CI [{m_rec-1.96*se_rec:+.4f}, {m_rec+1.96*se_rec:+.4f}])")

    print(f"\n  Saved: {out}")
    return results


# ===================================================================
# MAIN
# ===================================================================

async def main():
    parser = argparse.ArgumentParser(description="V6 Completion Runner")
    parser.add_argument("--phase", default="sim_intervention",
        choices=["sim_intervention", "scifact", "hotpotqa", "all"])
    parser.add_argument("--model", default=PRIMARY_MODEL)
    parser.add_argument("--batch-size", type=int, default=0,
        help="Process at most this many new items per run (0=unlimited)")
    args = parser.parse_args()
    os.environ["V6_BATCH_SIZE"] = str(args.batch_size)

    client = _make_client()
    model_id = args.model

    print(f"Campaign V6 Completion -- Semantic Causality & External Transfer")
    print(f"Model: {model_id}")
    print(f"Remote: {BASE_URL}")
    print(f"Temperature: {TEMPERATURE}")
    print()

    if args.phase in ("sim_intervention", "all"):
        await run_sim_intervention(client, model_id)

    if args.phase in ("scifact", "all"):
        await run_scifact(client, model_id)

    if args.phase in ("hotpotqa", "all"):
        await run_hotpotqa(client, model_id)

    print(f"\n{'='*60}")
    print(f"V6 completion execution finished")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
