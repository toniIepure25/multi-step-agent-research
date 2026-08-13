"""Paper Validation Runner — Preregistered causal auditing of semantic artifacts.

Implements all core conditions + SciFact harm decomposition.
Crash-resilient with incremental save and resume.
"""
from __future__ import annotations

import argparse
import asyncio
import functools
import hashlib
import json
import os
import random
import statistics
import sys
import time
import traceback
from pathlib import Path

print = functools.partial(print, flush=True)  # type: ignore[assignment]
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from asar.core.llm import LLMGenerationRequest, LLMMessage, MessageRole
from asar.providers.chat_completions_llm import ChatCompletionsLLMClient

BASE_DIR = Path(__file__).parent
RESULTS_RAW = BASE_DIR / "results" / "raw"
RESULTS_DERIVED = BASE_DIR / "results" / "derived"
TRACES_DIR = BASE_DIR / "traces"
V6_DATA = Path(__file__).resolve().parents[1] / "campaign_v6" / "data"

BASE_URL = "https://inference.ccrolabs.com/v1"
TEMPERATURE = 0.0
MAX_TOKENS = 512
TIMEOUT = 120.0
BATCH_SIZE = 10

# === PROMPT TEMPLATES ===

HYPOTHESIS_SYSTEM = (
    "You are a research scientist. Given a question or claim, generate "
    "a plausible hypothesis about the answer. Output ONLY valid JSON: "
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

QUERY_FROM_ARTIFACT_SYSTEM = (
    "You are a research strategist. Given a hypothesis or analysis, generate "
    "a targeted search query to find evidence. "
    'Output ONLY valid JSON: {"query": "...", "rationale": "..."}'
)

QUERY_DIRECT_SYSTEM = (
    "You are a research strategist. Generate a search query to find "
    "relevant evidence for answering the given question. "
    'Output ONLY valid JSON: {"query": "...", "rationale": "..."}'
)

SCIFACT_REASON_SYSTEM = (
    "You are a research analyst evaluating a scientific claim. "
    "Given a claim, evidence passages, and optionally a hypothesis, "
    "determine whether the evidence supports or refutes the claim. "
    'Output ONLY valid JSON: {"verdict": "SUPPORTS|REFUTES|NOT_ENOUGH_INFO", '
    '"confidence": 0.0-1.0, "reasoning": "..."}'
)

SCIFACT_PARAMETRIC_SYSTEM = (
    "You are a research analyst. Based ONLY on your knowledge (no external "
    "evidence provided), determine whether this scientific claim is likely "
    "true or false. "
    'Output ONLY valid JSON: {"verdict": "SUPPORTS|REFUTES|NOT_ENOUGH_INFO", '
    '"confidence": 0.0-1.0, "reasoning": "..."}'
)

HOTPOT_REASON_SYSTEM = (
    "You are a research analyst. Given a question and evidence passages, "
    "provide a short factual answer. Output ONLY valid JSON: "
    '{"answer": "...", "reasoning": "...", "confidence": 0.0-1.0}'
)

CONTROL_PARAPHRASE_SYSTEM = (
    "You are a text assistant. Rephrase the following text in a different "
    "style but preserving the same length and format. Do NOT add new "
    "information or analysis. Output ONLY the rephrased text."
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
                return json.loads(stripped[s : e + 1])
            except (json.JSONDecodeError, ValueError):
                pass
    return None


async def _llm_call(client, model, system, user, max_retries=3):
    """LLM call with retry."""
    for attempt in range(max_retries):
        try:
            resp = await client.generate(
                LLMGenerationRequest(
                    model=model,
                    messages=[
                        LLMMessage(role=MessageRole.SYSTEM, content=system),
                        LLMMessage(role=MessageRole.USER, content=user),
                    ],
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                )
            )
            return resp.output_text
        except Exception as exc:
            if attempt < max_retries - 1:
                await asyncio.sleep(3 * (attempt + 1))
            else:
                return f"ERROR: {exc}"


def _bm25_retrieve(query, corpus, k=5):
    """BM25-like keyword retrieval."""
    qw = set(w.lower() for w in query.split() if len(w) > 2)
    if not qw:
        return list(corpus.values())[:k]
    scored = []
    for did, doc in corpus.items():
        t = f"{doc.get('title', '')} {doc.get('abstract', '')} {doc.get('text', '')}"
        dw = set(w.lower() for w in t.split() if len(w) > 2)
        scored.append((len(qw & dw), did, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[2] for s in scored[:k]]


def _compute_f1(prediction, gold):
    """Token-level F1 between predicted and gold answer."""
    pred_tokens = prediction.lower().split()
    gold_tokens = gold.lower().split()
    common = set(pred_tokens) & set(gold_tokens)
    if not common:
        return 0.0
    prec = len(common) / len(pred_tokens)
    rec = len(common) / len(gold_tokens)
    return 2 * prec * rec / (prec + rec)


# =============================================================
# SCIFACT CONDITION RUNNER
# =============================================================

async def scifact_condition(client, model, claim, corpus, condition,
                            artifact_text=None, show_artifact_in_answer=True,
                            override_evidence=None):
    """Run one condition on one SciFact claim. Returns trace dict."""
    question = claim["claim"]
    trace = {
        "condition": condition,
        "claim_id": claim["id"],
        "calls": 0,
        "artifact": None,
        "query": None,
        "retrieved_doc_ids": [],
        "gold_doc_ids": claim["gold_doc_ids"],
    }

    # --- PARAMETRIC ONLY ---
    if condition == "PARAMETRIC_ONLY":
        r = await _llm_call(client, model, SCIFACT_PARAMETRIC_SYSTEM,
            f"Scientific claim: {question}\n\nIs this claim supported or refuted?")
        trace["calls"] += 1
        parsed = _parse_json(r)
        verdict = "NOT_ENOUGH_INFO"
        if isinstance(parsed, dict):
            verdict = parsed.get("verdict", "NOT_ENOUGH_INFO")
        elif "support" in r.lower():
            verdict = "SUPPORTS"
        elif "refute" in r.lower():
            verdict = "REFUTES"
        trace["predicted"] = verdict
        trace["correct"] = verdict.upper() == claim["label"].upper()
        trace["gold_doc_recall"] = 0.0
        trace["gold_doc_precision"] = 0.0
        trace["rationale_recall"] = 0.0
        return trace

    # --- GOLD RATIONALE ONLY ---
    if condition in ("GOLD_RATIONALE_ONLY", "GOLD_DOC_FULL"):
        gold_ev = claim.get("gold_evidence", {})
        if condition == "GOLD_RATIONALE_ONLY":
            ev_parts = []
            for doc_id, sent_data in gold_ev.items():
                doc = corpus.get(doc_id, {})
                title = doc.get("title", f"Doc {doc_id}")
                abstract_sents = doc.get("abstract", "").split(". ")
                for sent_group in sent_data:
                    for idx in sent_group:
                        if idx < len(abstract_sents):
                            ev_parts.append(f"[{title}] {abstract_sents[idx]}")
            ev_text = "\n".join(ev_parts[:10]) if ev_parts else "(no rationale found)"
        else:
            ev_parts = []
            for doc_id in gold_ev:
                doc = corpus.get(doc_id, {})
                title = doc.get("title", f"Doc {doc_id}")
                abstract = doc.get("abstract", "")[:500]
                ev_parts.append(f"[{title}] {abstract}")
            ev_text = "\n".join(ev_parts[:5]) if ev_parts else "(no gold docs found)"

        r = await _llm_call(client, model, SCIFACT_REASON_SYSTEM,
            f"Claim: {question}\nEvidence:\n{ev_text}\n\nDoes the evidence support or refute the claim?")
        trace["calls"] += 1
        parsed = _parse_json(r)
        verdict = "NOT_ENOUGH_INFO"
        if isinstance(parsed, dict):
            verdict = parsed.get("verdict", "NOT_ENOUGH_INFO")
        elif "support" in r.lower():
            verdict = "SUPPORTS"
        elif "refute" in r.lower():
            verdict = "REFUTES"
        trace["predicted"] = verdict
        trace["correct"] = verdict.upper() == claim["label"].upper()
        trace["gold_doc_recall"] = 1.0
        trace["gold_doc_precision"] = 1.0
        trace["rationale_recall"] = 1.0 if condition == "GOLD_RATIONALE_ONLY" else 0.5
        return trace

    # --- STANDARD CONDITIONS ---
    # Step 1: Artifact generation
    if condition == "REAL":
        artifact = await _llm_call(client, model, HYPOTHESIS_SYSTEM,
            f"Scientific claim: {question}\n\nGenerate a hypothesis about whether this claim is supported by evidence.")
        trace["calls"] += 1
        trace["artifact"] = artifact
        trace["artifact_chars"] = len(artifact)
    elif condition == "SHUFFLED":
        _ = await _llm_call(client, model, HYPOTHESIS_SYSTEM,
            f"Scientific claim: {question}\n\nGenerate a hypothesis about whether this claim is supported by evidence.")
        trace["calls"] += 1
        artifact = artifact_text or "(shuffled placeholder)"
        trace["artifact"] = artifact
        trace["artifact_chars"] = len(artifact)
    elif condition == "NEUTRAL":
        artifact = await _llm_call(client, model, NEUTRAL_SYSTEM,
            f"Scientific claim: {question}\n\nRestate the key entities and relationships.")
        trace["calls"] += 1
        trace["artifact"] = artifact
        trace["artifact_chars"] = len(artifact)
    elif condition == "GENERIC_EXPANSION":
        artifact = await _llm_call(client, model, EXPANSION_SYSTEM,
            f"Question: Is the following claim supported? {question}\n\nExpand into search terms.")
        trace["calls"] += 1
        trace["artifact"] = artifact
        trace["artifact_chars"] = len(artifact)
    elif condition == "DIRECT":
        _ = await _llm_call(client, model, CONTROL_PARAPHRASE_SYSTEM,
            f"Rephrase: {question}")
        trace["calls"] += 1
        artifact = ""
        trace["artifact"] = ""
        trace["artifact_chars"] = 0
    elif condition == "REAL_ARTIFACT_HIDDEN":
        artifact = await _llm_call(client, model, HYPOTHESIS_SYSTEM,
            f"Scientific claim: {question}\n\nGenerate a hypothesis about whether this claim is supported by evidence.")
        trace["calls"] += 1
        trace["artifact"] = artifact
        trace["artifact_chars"] = len(artifact)
        show_artifact_in_answer = False
    else:
        artifact = ""

    # Step 2: Query generation
    if condition in ("REAL", "SHUFFLED", "NEUTRAL", "REAL_ARTIFACT_HIDDEN"):
        q_text = await _llm_call(client, model, QUERY_FROM_ARTIFACT_SYSTEM,
            f"Analysis: {artifact[:300]}\n\nGenerate a search query to find relevant scientific evidence.")
        trace["calls"] += 1
    elif condition == "GENERIC_EXPANSION":
        q_text = artifact
    else:
        q_text = await _llm_call(client, model, QUERY_DIRECT_SYSTEM,
            f"Question: Is this claim supported? {question}\n\nGenerate a search query.")
        trace["calls"] += 1

    parsed_q = _parse_json(q_text) if q_text else None
    query = (parsed_q.get("query", q_text[:200]) if isinstance(parsed_q, dict)
             else (parsed_q[:200] if isinstance(parsed_q, str) else (q_text[:200] if q_text else question)))
    trace["query"] = query[:300]

    # Step 3: Retrieve
    if override_evidence is not None:
        retrieved = override_evidence
    else:
        retrieved = _bm25_retrieve(query, corpus, k=5)

    retrieved_ids = set(str(d.get("doc_id", "")) for d in retrieved)
    gold_ids = set(claim["gold_doc_ids"])
    trace["retrieved_doc_ids"] = list(retrieved_ids)
    trace["gold_doc_recall"] = len(retrieved_ids & gold_ids) / max(1, len(gold_ids))
    trace["gold_doc_precision"] = len(retrieved_ids & gold_ids) / max(1, len(retrieved_ids))

    # Rationale-level metrics
    gold_ev = claim.get("gold_evidence", {})
    rationale_found = 0
    rationale_total = 0
    for doc_id, sent_groups in gold_ev.items():
        for group in sent_groups:
            rationale_total += len(group)
            if doc_id in retrieved_ids:
                rationale_found += len(group)
    trace["rationale_recall"] = rationale_found / max(1, rationale_total)

    # Step 4: Answer
    ev_text = "\n".join(
        f"[{d.get('doc_id', '?')}] {d.get('title', '')}: {d.get('abstract', '')[:300]}"
        for d in retrieved[:3]
    )
    if show_artifact_in_answer and artifact and condition not in ("DIRECT", "GENERIC_EXPANSION"):
        hyp_text = artifact[:200]
    else:
        hyp_text = "(no hypothesis)"

    r = await _llm_call(client, model, SCIFACT_REASON_SYSTEM,
        f"Claim: {question}\nHypothesis: {hyp_text}\nEvidence:\n{ev_text}\n\nDoes the evidence support or refute the claim?")
    trace["calls"] += 1

    parsed_a = _parse_json(r)
    verdict = "NOT_ENOUGH_INFO"
    if isinstance(parsed_a, dict):
        verdict = parsed_a.get("verdict", "NOT_ENOUGH_INFO")
    elif "support" in r.lower():
        verdict = "SUPPORTS"
    elif "refute" in r.lower():
        verdict = "REFUTES"

    trace["predicted"] = verdict
    trace["correct"] = verdict.upper() == claim["label"].upper()
    return trace


# =============================================================
# HOTPOTQA CONDITION RUNNER
# =============================================================

async def hotpot_condition(client, model, task, condition,
                           artifact_text=None, show_artifact_in_answer=True):
    """Run one condition on one HotpotQA task."""
    question = task["question"]
    trace = {
        "condition": condition,
        "task_id": task["id"],
        "calls": 0,
        "artifact": None,
        "query": None,
    }

    # Step 1: Artifact
    if condition == "REAL":
        artifact = await _llm_call(client, model, HYPOTHESIS_SYSTEM,
            f"Question: {question}\n\nGenerate a hypothesis about the likely answer.")
        trace["calls"] += 1
        trace["artifact_chars"] = len(artifact)
    elif condition == "SHUFFLED":
        _ = await _llm_call(client, model, HYPOTHESIS_SYSTEM,
            f"Question: {question}\n\nGenerate a hypothesis about the likely answer.")
        trace["calls"] += 1
        artifact = artifact_text or "(shuffled)"
        trace["artifact_chars"] = len(artifact)
    elif condition == "NEUTRAL":
        artifact = await _llm_call(client, model, NEUTRAL_SYSTEM,
            f"Question: {question}\n\nRestate key entities.")
        trace["calls"] += 1
        trace["artifact_chars"] = len(artifact)
    elif condition == "GENERIC_EXPANSION":
        artifact = await _llm_call(client, model, EXPANSION_SYSTEM,
            f"Question: {question}\n\nExpand into search terms.")
        trace["calls"] += 1
        trace["artifact_chars"] = len(artifact)
    else:  # DIRECT
        _ = await _llm_call(client, model, CONTROL_PARAPHRASE_SYSTEM,
            f"Rephrase: {question}")
        trace["calls"] += 1
        artifact = ""
        trace["artifact_chars"] = 0

    # Step 2: Query
    if condition in ("REAL", "SHUFFLED", "NEUTRAL"):
        q_text = await _llm_call(client, model, QUERY_FROM_ARTIFACT_SYSTEM,
            f"Analysis: {artifact[:300]}\n\nGenerate a search query.")
        trace["calls"] += 1
    elif condition == "GENERIC_EXPANSION":
        q_text = artifact
    else:
        q_text = await _llm_call(client, model, QUERY_DIRECT_SYSTEM,
            f"Question: {question}\n\nGenerate a search query.")
        trace["calls"] += 1

    parsed_q = _parse_json(q_text) if q_text else None
    query = (parsed_q.get("query", q_text[:200]) if isinstance(parsed_q, dict)
             else (parsed_q[:200] if isinstance(parsed_q, str) else (q_text[:200] if q_text else question)))
    trace["query"] = query[:300]

    # Step 3: Retrieve
    paragraphs = {}
    for title, text in task["paragraphs"].items():
        paragraphs[title] = {"title": title, "text": text, "doc_id": title}
    retrieved = _bm25_retrieve(query, paragraphs, k=3)
    retrieved_titles = set(d.get("title", d.get("doc_id", "")) for d in retrieved)
    gold_titles = set(task["gold_titles"])
    trace["gold_title_recall"] = len(retrieved_titles & gold_titles) / max(1, len(gold_titles))
    trace["gold_title_precision"] = len(retrieved_titles & gold_titles) / max(1, len(retrieved_titles))
    trace["retrieved_titles"] = list(retrieved_titles)

    # Step 4: Answer
    ev_text = "\n".join(f"[{d.get('title', '?')}] {d.get('text', d.get('abstract', ''))[:300]}" for d in retrieved)
    hyp_text = artifact[:200] if (artifact and show_artifact_in_answer and condition not in ("DIRECT", "GENERIC_EXPANSION")) else "(none)"

    a_text = await _llm_call(client, model, HOTPOT_REASON_SYSTEM,
        f"Question: {question}\nHypothesis: {hyp_text}\nEvidence:\n{ev_text}\n\nAnswer concisely.")
    trace["calls"] += 1

    parsed_a = _parse_json(a_text)
    predicted = (parsed_a.get("answer", a_text[:100]) if isinstance(parsed_a, dict)
                 else (parsed_a[:100] if isinstance(parsed_a, str) else a_text[:100]))
    trace["predicted_answer"] = predicted[:200]
    trace["f1"] = _compute_f1(predicted, task["answer"])
    trace["em"] = 1.0 if predicted.strip().lower() == task["answer"].strip().lower() else 0.0
    return trace


# =============================================================
# DATASET LOADERS
# =============================================================

def load_scifact():
    corpus = {}
    with open(V6_DATA / "scifact" / "corpus.jsonl") as f:
        for line in f:
            doc = json.loads(line)
            did = str(doc["doc_id"])
            corpus[did] = {
                "doc_id": did,
                "title": doc.get("title", ""),
                "abstract": " ".join(doc.get("abstract", [])),
            }

    claims = []
    with open(V6_DATA / "scifact" / "claims_dev.jsonl") as f:
        for line in f:
            c = json.loads(line)
            gold_docs = {}
            if c.get("evidence"):
                for doc_id_str, sents in c["evidence"].items():
                    gold_docs[doc_id_str] = sents
            if gold_docs:
                claims.append({
                    "id": c["id"],
                    "claim": c["claim"],
                    "label": c.get("label", "NOT_ENOUGH_INFO"),
                    "gold_doc_ids": list(gold_docs.keys()),
                    "gold_evidence": gold_docs,
                })
    return corpus, claims


def load_hotpotqa():
    with open(V6_DATA / "hotpotqa" / "hotpot_dev_distractor.json") as f:
        data = json.load(f)
    tasks = []
    for item in data:
        paragraphs = {}
        for title, sents in item["context"]:
            paragraphs[title] = " ".join(sents)
        gold_titles = list(set(sf[0] for sf in item.get("supporting_facts", [])))
        tasks.append({
            "id": item["_id"],
            "question": item["question"],
            "answer": item["answer"],
            "type": item.get("type", ""),
            "paragraphs": paragraphs,
            "gold_titles": gold_titles,
        })
    return tasks


# =============================================================
# MAIN RUNNER
# =============================================================

async def run_scifact_validation(client, model, mode="locked"):
    """Run SciFact validation."""
    corpus, all_claims = load_scifact()
    split = json.loads((BASE_DIR / "splits" / "scifact_locked.json").read_text())

    if mode == "locked":
        task_ids = set(split["locked_confirmatory"])
        label = "LOCKED"
    elif mode == "transfer":
        task_ids = set(split["same_task_transfer"])
        label = "TRANSFER"
    else:
        task_ids = set(c["id"] for c in all_claims)
        label = "ALL"

    claims = [c for c in all_claims if c["id"] in task_ids]
    n = len(claims)
    model_tag = model.replace(":", "_")
    out_file = RESULTS_RAW / f"scifact_{label}_{model_tag}.jsonl"

    print(f"\n{'='*60}")
    print(f"SCIFACT {label} (N={n}, model={model})")
    print(f"{'='*60}")

    # Pre-generate artifacts for shuffle
    art_file = RESULTS_RAW / f"scifact_artifacts_{label}_{model_tag}.json"
    artifacts = {}
    if art_file.exists():
        artifacts = {int(k): v for k, v in json.loads(art_file.read_text()).items()}
        print(f"  Loaded {len(artifacts)} cached artifacts")

    needs_gen = [c for c in claims if c["id"] not in artifacts]
    if needs_gen:
        print(f"  Generating {len(needs_gen)} artifacts...")
        for i, c in enumerate(needs_gen):
            text = await _llm_call(client, model, HYPOTHESIS_SYSTEM,
                f"Scientific claim: {c['claim']}\n\nGenerate a hypothesis about whether this claim is supported by evidence.")
            if "ERROR:" not in text:
                artifacts[c["id"]] = text
            else:
                artifacts[c["id"]] = f"(generation failed for {c['id']})"
            if (i + 1) % 20 == 0:
                print(f"    Generated {i+1}/{len(needs_gen)}")
                art_file.write_text(json.dumps({str(k): v for k, v in artifacts.items()}, indent=2))
        art_file.write_text(json.dumps({str(k): v for k, v in artifacts.items()}, indent=2))
        print(f"  Generated {len(artifacts)} total artifacts")

    # Deterministic shuffle map
    cids = sorted(artifacts.keys())
    shuffle_map = {}
    for i, cid in enumerate(cids):
        partner = cids[(i + 7) % len(cids)]
        if partner == cid:
            partner = cids[(i + 1) % len(cids)]
        shuffle_map[cid] = artifacts[partner]

    # Load completed
    done_ids = set()
    results = []
    if out_file.exists():
        with open(out_file) as f:
            for line in f:
                r = json.loads(line)
                results.append(r)
                done_ids.add(r["claim_id"])
        print(f"  Resuming: {len(done_ids)} already done")

    core_conditions = ["DIRECT", "NEUTRAL", "GENERIC_EXPANSION", "REAL", "SHUFFLED"]
    diag_conditions = ["PARAMETRIC_ONLY", "REAL_ARTIFACT_HIDDEN"]
    all_conditions = core_conditions + diag_conditions

    batch_count = 0
    for ci, claim in enumerate(claims):
        if claim["id"] in done_ids:
            continue
        if batch_count >= BATCH_SIZE:
            print(f"  Batch of {BATCH_SIZE} done. Rerun to continue.")
            break

        display = claim["claim"][:50].encode("ascii", errors="replace").decode()
        print(f"  [{time.strftime('%H:%M:%S')}] Claim {ci+1}/{n}: {display}...")

        row = {"claim_id": claim["id"], "label": claim["label"]}
        try:
            for cond in all_conditions:
                art = shuffle_map.get(claim["id"]) if cond == "SHUFFLED" else None
                trace = await scifact_condition(
                    client, model, claim, corpus, cond, artifact_text=art
                )
                row[cond] = {
                    "correct": trace["correct"],
                    "predicted": trace["predicted"],
                    "gold_doc_recall": trace["gold_doc_recall"],
                    "gold_doc_precision": trace.get("gold_doc_precision", 0),
                    "rationale_recall": trace.get("rationale_recall", 0),
                    "calls": trace["calls"],
                    "artifact_chars": trace.get("artifact_chars", 0),
                }
            with open(out_file, "a") as f:
                f.write(json.dumps(row) + "\n")
            results.append(row)
            batch_count += 1
        except Exception as exc:
            print(f"    ERROR: {exc}")
            traceback.print_exc()
            break

    # Summary
    if results:
        print(f"\n  --- SciFact {label} Progress ({len(results)}/{n}) ---")
        for cond in all_conditions:
            accs = [r[cond]["correct"] for r in results if cond in r]
            recs = [r[cond]["gold_doc_recall"] for r in results if cond in r]
            if accs:
                print(f"  {cond:25s}: acc={statistics.mean(accs):.3f}  recall={statistics.mean(recs):.3f}")

        if len(results) >= 10 and "REAL" in results[0] and "SHUFFLED" in results[0]:
            ra = [1 if r["REAL"]["correct"] else 0 for r in results]
            sa = [1 if r["SHUFFLED"]["correct"] else 0 for r in results]
            rr = [r["REAL"]["gold_doc_recall"] for r in results]
            sr = [r["SHUFFLED"]["gold_doc_recall"] for r in results]
            da = [ra[i] - sa[i] for i in range(len(results))]
            dr = [rr[i] - sr[i] for i in range(len(results))]
            ma, mr = statistics.mean(da), statistics.mean(dr)
            sea = statistics.stdev(da) / len(da)**0.5 if len(da) > 1 else 0
            ser = statistics.stdev(dr) / len(dr)**0.5 if len(dr) > 1 else 0
            print(f"\n  REAL-SHUFFLED (acc):    {ma:+.4f} CI [{ma-1.96*sea:+.4f}, {ma+1.96*sea:+.4f}]")
            print(f"  REAL-SHUFFLED (recall): {mr:+.4f} CI [{mr-1.96*ser:+.4f}, {mr+1.96*ser:+.4f}]")

    return results


async def run_hotpotqa_validation(client, model, mode="locked"):
    """Run HotpotQA validation."""
    all_tasks = load_hotpotqa()
    split = json.loads((BASE_DIR / "splits" / "hotpotqa_locked.json").read_text())

    if mode == "locked":
        task_ids = set(split["locked_confirmatory"])
        label = "LOCKED"
    elif mode == "transfer":
        task_ids = set(split["same_task_transfer"])
        label = "TRANSFER"
    else:
        raise ValueError(f"Unknown mode: {mode}")

    tasks = [t for t in all_tasks if t["id"] in task_ids]
    n = len(tasks)
    model_tag = model.replace(":", "_")
    out_file = RESULTS_RAW / f"hotpotqa_{label}_{model_tag}.jsonl"

    print(f"\n{'='*60}")
    print(f"HOTPOTQA {label} (N={n}, model={model})")
    print(f"{'='*60}")

    # Pre-generate artifacts
    art_file = RESULTS_RAW / f"hotpotqa_artifacts_{label}_{model_tag}.json"
    artifacts = {}
    if art_file.exists():
        artifacts = json.loads(art_file.read_text())
        print(f"  Loaded {len(artifacts)} cached artifacts")

    needs_gen = [t for t in tasks if t["id"] not in artifacts]
    if needs_gen:
        print(f"  Generating {len(needs_gen)} artifacts...")
        for i, t in enumerate(needs_gen):
            text = await _llm_call(client, model, HYPOTHESIS_SYSTEM,
                f"Question: {t['question']}\n\nGenerate a hypothesis about the likely answer.")
            if "ERROR:" not in text:
                artifacts[t["id"]] = text
            else:
                artifacts[t["id"]] = f"(generation failed for {t['id']})"
            if (i + 1) % 50 == 0:
                print(f"    Generated {i+1}/{len(needs_gen)}")
                art_file.write_text(json.dumps(artifacts, indent=2))
        art_file.write_text(json.dumps(artifacts, indent=2))
        print(f"  Generated {len(artifacts)} total artifacts")

    # Shuffle map
    tids = sorted(artifacts.keys())
    shuffle_map = {}
    for i, tid in enumerate(tids):
        partner = tids[(i + 7) % len(tids)]
        if partner == tid:
            partner = tids[(i + 1) % len(tids)]
        shuffle_map[tid] = artifacts[partner]

    # Load completed
    done_ids = set()
    results = []
    if out_file.exists():
        with open(out_file) as f:
            for line in f:
                r = json.loads(line)
                results.append(r)
                done_ids.add(r["task_id"])
        print(f"  Resuming: {len(done_ids)} already done")

    conditions = ["DIRECT", "NEUTRAL", "GENERIC_EXPANSION", "REAL", "SHUFFLED"]
    batch_count = 0

    for ti, task in enumerate(tasks):
        if task["id"] in done_ids:
            continue
        if batch_count >= BATCH_SIZE:
            print(f"  Batch of {BATCH_SIZE} done. Rerun to continue.")
            break

        display = task["question"][:50].encode("ascii", errors="replace").decode()
        print(f"  [{time.strftime('%H:%M:%S')}] Task {ti+1}/{n}: {display}...")

        row = {"task_id": task["id"], "answer": task["answer"]}
        try:
            for cond in conditions:
                art = shuffle_map.get(task["id"]) if cond == "SHUFFLED" else None
                trace = await hotpot_condition(client, model, task, cond, artifact_text=art)
                row[cond] = {
                    "f1": trace["f1"],
                    "em": trace["em"],
                    "gold_recall": trace["gold_title_recall"],
                    "gold_precision": trace.get("gold_title_precision", 0),
                    "calls": trace["calls"],
                    "artifact_chars": trace.get("artifact_chars", 0),
                }
            with open(out_file, "a") as f:
                f.write(json.dumps(row) + "\n")
            results.append(row)
            batch_count += 1
        except Exception as exc:
            print(f"    ERROR: {exc}")
            traceback.print_exc()
            break

    # Summary
    if results:
        print(f"\n  --- HotpotQA {label} Progress ({len(results)}/{n}) ---")
        for cond in conditions:
            f1s = [r[cond]["f1"] for r in results if cond in r]
            recs = [r[cond]["gold_recall"] for r in results if cond in r]
            if f1s:
                print(f"  {cond:25s}: F1={statistics.mean(f1s):.3f}  recall={statistics.mean(recs):.3f}")

    return results


async def main():
    parser = argparse.ArgumentParser(description="Paper Validation Runner")
    parser.add_argument("--dataset", required=True, choices=["scifact", "hotpotqa"])
    parser.add_argument("--mode", default="locked", choices=["locked", "transfer"])
    parser.add_argument("--model", default="gemma3:27b-it-qat")
    parser.add_argument("--batch-size", type=int, default=10)
    args = parser.parse_args()

    global BATCH_SIZE
    BATCH_SIZE = args.batch_size

    RESULTS_RAW.mkdir(parents=True, exist_ok=True)

    client = ChatCompletionsLLMClient(base_url=BASE_URL, timeout=TIMEOUT)

    print(f"Paper Validation Runner")
    print(f"Dataset: {args.dataset}  Mode: {args.mode}  Model: {args.model}")
    print(f"Batch: {BATCH_SIZE}  Temperature: {TEMPERATURE}")

    if args.dataset == "scifact":
        await run_scifact_validation(client, args.model, args.mode)
    elif args.dataset == "hotpotqa":
        await run_hotpotqa_validation(client, args.model, args.mode)


if __name__ == "__main__":
    asyncio.run(main())
