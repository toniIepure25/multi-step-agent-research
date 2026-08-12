"""Batch SciFact runner — processes N claims per invocation, crash-resilient."""
from __future__ import annotations

import asyncio
import functools
import hashlib
import json
import os
import signal
import statistics
import sys
import time
import traceback
from pathlib import Path

print = functools.partial(print, flush=True)  # type: ignore[assignment]
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from asar.core.llm import LLMGenerationRequest, LLMMessage, MessageRole
from asar.providers.chat_completions_llm import ChatCompletionsLLMClient

RESULTS_DIR = Path(__file__).parent / "results"
DATA_DIR = Path(__file__).parent / "data" / "scifact"
BASE_URL = "https://inference.ccrolabs.com/v1"
PRIMARY_MODEL = "gemma3:27b-it-qat"
TEMPERATURE = 0.0
MAX_TOKENS = 512
TIMEOUT = 120.0
BATCH = 10

HYPOTHESIS_SYSTEM = (
    "You are a research scientist. Given evidence and a question, generate "
    "a plausible hypothesis. Output ONLY valid JSON: "
    '{"hypothesis": "...", "reasoning": "...", "confidence": 0.0-1.0}'
)
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
QUERY_FROM_HYP_SYSTEM = (
    "You are a research strategist. Given a hypothesis, generate a targeted "
    "search query to find evidence that would test this hypothesis. "
    "Output ONLY valid JSON: {\"query\": \"...\", \"rationale\": \"...\"}"
)
QUERY_DIRECT_SYSTEM = (
    "You are a research strategist. Generate a search query to find "
    "relevant evidence for answering the given question. "
    'Output ONLY valid JSON: {"query": "...", "rationale": "..."}'
)
REASON_SYSTEM = (
    "You are a research analyst. Given a question, a hypothesis (if any), "
    "and evidence, evaluate the hypothesis and produce a final answer. "
    'Output ONLY valid JSON: {"answer": "...", "verdict": "SUPPORTS|REFUTES|NOT_ENOUGH_INFO", '
    '"confidence": 0.0-1.0, "supporting_evidence": ["..."]}'
)


def _parse_json(text: str) -> dict | None:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        stripped = "\n".join(lines).strip()
    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        s = stripped.find("{")
        e = stripped.rfind("}")
        if s >= 0 and e > s:
            try:
                return json.loads(stripped[s:e + 1])
            except (json.JSONDecodeError, ValueError):
                pass
    return None


async def _call(client, system, user):
    t0 = time.time()
    try:
        resp = await client.generate(LLMGenerationRequest(
            model=PRIMARY_MODEL,
            messages=[
                LLMMessage(role=MessageRole.SYSTEM, content=system),
                LLMMessage(role=MessageRole.USER, content=user),
            ],
            temperature=TEMPERATURE, max_tokens=MAX_TOKENS,
        ))
        return resp.output_text, time.time() - t0
    except Exception as exc:
        return f"ERROR: {exc}", time.time() - t0


def _bm25(query, corpus, k=5):
    qw = set(w.lower() for w in query.split() if len(w) > 2)
    if not qw:
        return list(corpus.values())[:k]
    scored = []
    for did, doc in corpus.items():
        t = f"{doc['title']} {doc['abstract']}"
        dw = set(w.lower() for w in t.split() if len(w) > 2)
        scored.append((len(qw & dw), did, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[2] for s in scored[:k]]


async def run_condition(client, claim, corpus, condition, artifact_text=None):
    question = claim["claim"]
    result = {"condition": condition, "calls": 0}

    # Step 1: Artifact
    if condition == "REAL":
        text, _ = await _call(client, HYPOTHESIS_SYSTEM,
            f"Scientific claim: {question}\n\nGenerate a hypothesis about whether this claim is supported by evidence.")
        result["calls"] += 1
        result["artifact_chars"] = len(text)
    elif condition == "SHUFFLED":
        text = artifact_text or "Hypothesis from another domain."
        _, _ = await _call(client, HYPOTHESIS_SYSTEM,
            f"Scientific claim: {question}\n\nGenerate a hypothesis about whether this claim is supported by evidence.")
        result["calls"] += 1
        result["artifact_chars"] = len(text)
    elif condition == "NEUTRAL":
        text, _ = await _call(client, NEUTRAL_SYSTEM,
            f"Scientific claim: {question}\n\nRestate the key entities and relationships.")
        result["calls"] += 1
        result["artifact_chars"] = len(text)
    elif condition == "GENERIC_EXPANSION":
        text, _ = await _call(client, EXPANSION_SYSTEM,
            f"Question: Is the following claim supported? {question}\n\nExpand into search terms.")
        result["calls"] += 1
        result["artifact_chars"] = len(text)
    else:  # DIRECT
        text = ""

    # Step 2: Query
    if condition in ("REAL", "SHUFFLED") and text:
        q_text, _ = await _call(client, QUERY_FROM_HYP_SYSTEM,
            f"Hypothesis: {text[:300]}\n\nGenerate a search query to find evidence.")
        result["calls"] += 1
    elif condition == "GENERIC_EXPANSION":
        q_text = text
    else:
        q_text, _ = await _call(client, QUERY_DIRECT_SYSTEM,
            f"Question: Is this claim supported? {question}\n\nGenerate a search query.")
        result["calls"] += 1

    parsed_q = _parse_json(q_text) if q_text else None
    query = parsed_q.get("query", q_text[:200]) if parsed_q else (q_text[:200] if q_text else question)

    # Step 3: Retrieve
    retrieved = _bm25(query, corpus, k=5)
    retrieved_ids = set(d["doc_id"] for d in retrieved)
    gold_ids = set(claim["gold_doc_ids"])
    recall = len(retrieved_ids & gold_ids) / max(1, len(gold_ids)) if gold_ids else 0
    precision = len(retrieved_ids & gold_ids) / max(1, len(retrieved_ids)) if retrieved_ids else 0
    result["gold_recall"] = recall
    result["gold_precision"] = precision

    # Step 4: Reason
    ev_text = "\n".join(f"[{d['doc_id']}] {d['title']}: {d['abstract'][:300]}" for d in retrieved[:3])
    hyp_text = text[:200] if text else "(no hypothesis)"
    r_text, _ = await _call(client, REASON_SYSTEM,
        f"Claim: {question}\nHypothesis: {hyp_text}\nEvidence:\n{ev_text}\n\nDoes the evidence support or refute the claim?")
    result["calls"] += 1

    parsed_a = _parse_json(r_text)
    predicted = "NOT_ENOUGH_INFO"
    if parsed_a:
        predicted = parsed_a.get("verdict", "NOT_ENOUGH_INFO")
    else:
        rl = r_text.lower()
        if "support" in rl:
            predicted = "SUPPORTS"
        elif "refute" in rl:
            predicted = "REFUTES"

    result["predicted"] = predicted
    result["correct"] = (predicted.upper() == claim["label"].upper())
    return result


async def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    corpus = {}
    with open(DATA_DIR / "corpus.jsonl") as f:
        for line in f:
            doc = json.loads(line)
            did = str(doc["doc_id"])
            corpus[did] = {"doc_id": did, "title": doc.get("title", ""),
                           "abstract": " ".join(doc.get("abstract", []))}

    claims = []
    with open(DATA_DIR / "claims_dev.jsonl") as f:
        for line in f:
            c = json.loads(line)
            gold_docs = {}
            if c.get("evidence"):
                for doc_id_str, sents in c["evidence"].items():
                    gold_docs[doc_id_str] = sents
            if gold_docs:
                claims.append({"id": c["id"], "claim": c["claim"],
                    "label": c.get("label", "NOT_ENOUGH_INFO"),
                    "gold_doc_ids": list(gold_docs.keys()), "gold_evidence": gold_docs})

    locked = claims[:100]
    print(f"Corpus: {len(corpus)}  Evaluable: {len(claims)}  Locked: {len(locked)}")

    # Load artifacts
    art_file = RESULTS_DIR / f"scifact_artifacts_{PRIMARY_MODEL.replace(':', '_')}.json"
    artifacts = json.loads(art_file.read_text()) if art_file.exists() else {}
    artifacts = {int(k): v for k, v in artifacts.items()}

    # Shuffle map
    cids = sorted(artifacts.keys())
    shuffle_map = {}
    for i, cid in enumerate(cids):
        partner = cids[(i + 7) % len(cids)]
        if partner == cid:
            partner = cids[(i + 1) % len(cids)]
        shuffle_map[cid] = artifacts[partner]

    # Load completed
    out_file = RESULTS_DIR / f"scifact_{PRIMARY_MODEL.replace(':', '_')}.jsonl"
    done_ids = set()
    results = []
    if out_file.exists():
        with open(out_file) as f:
            for line in f:
                r = json.loads(line)
                results.append(r)
                done_ids.add(r["claim_id"])
    print(f"Already done: {len(done_ids)}")

    remaining = [c for c in locked if c["id"] not in done_ids]
    if not remaining:
        print("All 100 claims completed!")
    else:
        print(f"Remaining: {len(remaining)}  Processing batch of {min(BATCH, len(remaining))}")

    client = ChatCompletionsLLMClient(base_url=BASE_URL, timeout=TIMEOUT)
    conditions = ["DIRECT", "NEUTRAL", "GENERIC_EXPANSION", "REAL", "SHUFFLED"]
    batch_count = 0

    for claim in remaining:
        if batch_count >= BATCH:
            print(f"Batch of {BATCH} done. Rerun to continue.")
            break
        ci = next(i for i, c in enumerate(locked) if c["id"] == claim["id"])
        claim_display = claim['claim'][:50].encode('ascii', errors='replace').decode()
        print(f"  [{time.strftime('%H:%M:%S')}] Claim {ci+1}/100: {claim_display}...")

        claim_result = {"claim_id": claim["id"], "label": claim["label"]}
        try:
            for cond in conditions:
                art = shuffle_map.get(claim["id"]) if cond == "SHUFFLED" else None
                r = await run_condition(client, claim, corpus, cond, artifact_text=art)
                claim_result[cond] = {
                    "correct": r["correct"], "predicted": r["predicted"],
                    "gold_recall": r["gold_recall"], "gold_precision": r["gold_precision"],
                    "calls": r["calls"], "artifact_chars": r.get("artifact_chars", 0),
                }
            with open(out_file, "a") as f:
                f.write(json.dumps(claim_result) + "\n")
            results.append(claim_result)
            batch_count += 1
        except Exception as exc:
            print(f"    ERROR: {exc}")
            traceback.print_exc()
            break

    # Print summary if we have enough results
    if len(results) >= 5:
        print(f"\n--- SciFact Progress ({len(results)}/100) ---")
        for cond in conditions:
            accs = [r[cond]["correct"] for r in results if cond in r]
            recs = [r[cond]["gold_recall"] for r in results if cond in r]
            if accs:
                print(f"  {cond:20s}: acc={statistics.mean(accs):.3f}  recall={statistics.mean(recs):.3f}")

        if len(results) >= 10:
            real_a = [1 if r["REAL"]["correct"] else 0 for r in results]
            shuf_a = [1 if r["SHUFFLED"]["correct"] else 0 for r in results]
            real_r = [r["REAL"]["gold_recall"] for r in results]
            shuf_r = [r["SHUFFLED"]["gold_recall"] for r in results]
            da = [real_a[i] - shuf_a[i] for i in range(len(results))]
            dr = [real_r[i] - shuf_r[i] for i in range(len(results))]
            ma, mr = statistics.mean(da), statistics.mean(dr)
            sea = statistics.stdev(da) / len(da)**0.5 if len(da) > 1 else 0
            ser = statistics.stdev(dr) / len(dr)**0.5 if len(dr) > 1 else 0
            print(f"\n  REAL-SHUFFLED (acc):    {ma:+.4f} CI [{ma-1.96*sea:+.4f}, {ma+1.96*sea:+.4f}]")
            print(f"  REAL-SHUFFLED (recall): {mr:+.4f} CI [{mr-1.96*ser:+.4f}, {mr+1.96*ser:+.4f}]")


if __name__ == "__main__":
    asyncio.run(main())
