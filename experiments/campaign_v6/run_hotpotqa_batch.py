"""Batch HotpotQA runner — processes N tasks per invocation, crash-resilient."""
from __future__ import annotations

import asyncio
import functools
import hashlib
import json
import os
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
DATA_DIR = Path(__file__).parent / "data" / "hotpotqa"
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
    'Output ONLY valid JSON: {"query": "...", "rationale": "..."}'
)
QUERY_DIRECT_SYSTEM = (
    "You are a research strategist. Generate a search query to find "
    "relevant evidence for answering the given question. "
    'Output ONLY valid JSON: {"query": "...", "rationale": "..."}'
)
HOTPOT_REASON_SYSTEM = (
    "You are a research analyst. Given a question and evidence passages, "
    "provide a short factual answer. Output ONLY valid JSON: "
    '{"answer": "...", "reasoning": "...", "confidence": 0.0-1.0}'
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


def _hotpot_retrieve(query, paragraphs, k=3):
    qw = set(w.lower() for w in query.split() if len(w) > 2)
    scored = []
    for title, text in paragraphs.items():
        tw = set(w.lower() for w in f"{title} {text}".split() if len(w) > 2)
        scored.append((len(qw & tw), title, text))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(s[1], s[2]) for s in scored[:k]]


async def run_condition(client, task, condition, artifact_text=None):
    question = task["question"]
    result = {"condition": condition, "calls": 0}

    # Step 1: Artifact
    if condition == "REAL":
        text, _ = await _call(client, HYPOTHESIS_SYSTEM,
            f"Question: {question}\n\nGenerate a hypothesis about the likely answer.")
        result["calls"] += 1
        result["artifact_chars"] = len(text)
    elif condition == "SHUFFLED":
        text = artifact_text or "Hypothesis from another domain."
        _, _ = await _call(client, HYPOTHESIS_SYSTEM,
            f"Question: {question}\n\nGenerate a hypothesis about the likely answer.")
        result["calls"] += 1
        result["artifact_chars"] = len(text)
    elif condition == "NEUTRAL":
        text, _ = await _call(client, NEUTRAL_SYSTEM,
            f"Question: {question}\n\nRestate key entities.")
        result["calls"] += 1
        result["artifact_chars"] = len(text)
    elif condition == "GENERIC_EXPANSION":
        text, _ = await _call(client, EXPANSION_SYSTEM,
            f"Question: {question}\n\nExpand into search terms.")
        result["calls"] += 1
        result["artifact_chars"] = len(text)
    else:  # DIRECT
        text = ""

    # Step 2: Query
    if condition in ("REAL", "SHUFFLED") and text:
        q_text, _ = await _call(client, QUERY_FROM_HYP_SYSTEM,
            f"Hypothesis: {text[:300]}\n\nGenerate a search query.")
        result["calls"] += 1
    elif condition == "GENERIC_EXPANSION":
        q_text = text
    else:
        q_text, _ = await _call(client, QUERY_DIRECT_SYSTEM,
            f"Question: {question}\n\nGenerate a search query.")
        result["calls"] += 1

    parsed_q = _parse_json(q_text) if q_text else None
    query = parsed_q.get("query", q_text[:200]) if parsed_q else (q_text[:200] if q_text else question)

    # Step 3: Retrieve
    retrieved = _hotpot_retrieve(query, task["paragraphs"], k=3)
    retrieved_titles = set(t for t, _ in retrieved)
    gold_titles = set(task["gold_titles"])
    recall = len(retrieved_titles & gold_titles) / max(1, len(gold_titles)) if gold_titles else 0
    result["gold_recall"] = recall
    result["retrieved_titles"] = list(retrieved_titles)

    # Step 4: Answer
    ev_text = "\n".join(f"[{t}] {p[:300]}" for t, p in retrieved)
    hyp_text = text[:200] if text else "(none)"
    a_text, _ = await _call(client, HOTPOT_REASON_SYSTEM,
        f"Question: {question}\nHypothesis: {hyp_text}\nEvidence:\n{ev_text}\n\nAnswer concisely.")
    result["calls"] += 1

    parsed_a = _parse_json(a_text)
    predicted = parsed_a.get("answer", a_text[:100]) if parsed_a else a_text[:100]
    result["predicted_answer"] = predicted[:200]

    gold = task["answer"].lower().split()
    pred_tokens = predicted.lower().split()
    common = set(gold) & set(pred_tokens)
    if common:
        prec = len(common) / len(pred_tokens)
        rec = len(common) / len(gold)
        result["f1"] = 2 * prec * rec / (prec + rec)
    else:
        result["f1"] = 0.0
    result["em"] = 1.0 if predicted.strip().lower() == task["answer"].strip().lower() else 0.0

    return result


def download_hotpotqa():
    dev_file = DATA_DIR / "hotpot_dev_distractor.json"
    if dev_file.exists():
        print(f"HotpotQA already downloaded")
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading HotpotQA...")
    import urllib.request
    urls = [
        "https://web.archive.org/web/20250512032701id_/http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json",
        "http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json",
    ]
    for url in urls:
        try:
            urllib.request.urlretrieve(url, str(dev_file))
            print(f"Downloaded {dev_file.stat().st_size // 1024 // 1024}MB")
            return
        except Exception as e:
            print(f"Failed {url}: {e}")
    raise RuntimeError("Could not download HotpotQA")


def load_hotpotqa(max_n=200):
    with open(DATA_DIR / "hotpot_dev_distractor.json") as f:
        data = json.load(f)
    tasks = []
    for item in data[:max_n]:
        paragraphs = {}
        for title, sents in item["context"]:
            paragraphs[title] = " ".join(sents)
        gold_titles = set()
        for sf in item.get("supporting_facts", []):
            gold_titles.add(sf[0])
        tasks.append({"id": item["_id"], "question": item["question"],
            "answer": item["answer"], "type": item.get("type", ""),
            "paragraphs": paragraphs, "gold_titles": list(gold_titles)})
    return tasks


async def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    download_hotpotqa()

    tasks = load_hotpotqa(max_n=200)
    locked = tasks[:100]
    print(f"Tasks: {len(tasks)}  Locked: {len(locked)}")

    split_hash = hashlib.sha256(json.dumps([t["id"] for t in locked]).encode()).hexdigest()[:16]
    print(f"Task ID hash: {split_hash}")

    # Pre-generate artifacts with caching
    art_file = RESULTS_DIR / f"hotpotqa_artifacts_{PRIMARY_MODEL.replace(':', '_')}.json"
    artifacts = {}
    if art_file.exists():
        artifacts = json.loads(art_file.read_text())
        print(f"Loaded {len(artifacts)} cached artifacts")

    client = ChatCompletionsLLMClient(base_url=BASE_URL, timeout=TIMEOUT)

    needs_gen = [t for t in locked if t["id"] not in artifacts]
    if needs_gen:
        print(f"Generating {len(needs_gen)} new artifacts...")
        for i, t in enumerate(needs_gen):
            for retry in range(3):
                try:
                    text, _ = await _call(client, HYPOTHESIS_SYSTEM,
                        f"Question: {t['question']}\n\nGenerate a hypothesis about the likely answer.")
                    if "ERROR:" not in text:
                        artifacts[t["id"]] = text
                        break
                except Exception as e:
                    print(f"  Retry {retry+1}: {e}")
                    await asyncio.sleep(5)
            else:
                artifacts[t["id"]] = f"Unable to generate for {t['id']}"
            if (i + 1) % 20 == 0:
                print(f"  Generated {i+1}/{len(needs_gen)}")
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
    out_file = RESULTS_DIR / f"hotpotqa_{PRIMARY_MODEL.replace(':', '_')}.jsonl"
    done_ids = set()
    results = []
    if out_file.exists():
        with open(out_file) as f:
            for line in f:
                r = json.loads(line)
                results.append(r)
                done_ids.add(r["task_id"])
    print(f"Already done: {len(done_ids)}")

    remaining = [t for t in locked if t["id"] not in done_ids]
    if not remaining:
        print("All 100 tasks completed!")
    else:
        print(f"Remaining: {len(remaining)}  Processing batch of {min(BATCH, len(remaining))}")

    conditions = ["DIRECT", "NEUTRAL", "GENERIC_EXPANSION", "REAL", "SHUFFLED"]
    batch_count = 0

    for task in remaining:
        if batch_count >= BATCH:
            print(f"Batch of {BATCH} done. Rerun to continue.")
            break
        ti = next(i for i, t in enumerate(locked) if t["id"] == task["id"])
        q_display = task['question'][:50].encode('ascii', errors='replace').decode()
        print(f"  [{time.strftime('%H:%M:%S')}] Task {ti+1}/100: {q_display}...")

        task_result = {"task_id": task["id"], "answer": task["answer"]}
        try:
            for cond in conditions:
                art = shuffle_map.get(task["id"]) if cond == "SHUFFLED" else None
                r = await run_condition(client, task, cond, artifact_text=art)
                task_result[cond] = {
                    "f1": r["f1"], "em": r["em"],
                    "gold_recall": r["gold_recall"],
                    "calls": r["calls"],
                    "artifact_chars": r.get("artifact_chars", 0),
                }
            with open(out_file, "a") as f:
                f.write(json.dumps(task_result) + "\n")
            results.append(task_result)
            batch_count += 1
        except Exception as exc:
            print(f"    ERROR: {exc}")
            traceback.print_exc()
            break

    if len(results) >= 5:
        print(f"\n--- HotpotQA Progress ({len(results)}/100) ---")
        for cond in conditions:
            f1s = [r[cond]["f1"] for r in results if cond in r]
            recs = [r[cond]["gold_recall"] for r in results if cond in r]
            if f1s:
                print(f"  {cond:20s}: F1={statistics.mean(f1s):.3f}  recall={statistics.mean(recs):.3f}")

        if len(results) >= 10:
            rf = [r["REAL"]["f1"] for r in results]
            sf = [r["SHUFFLED"]["f1"] for r in results]
            rr = [r["REAL"]["gold_recall"] for r in results]
            sr = [r["SHUFFLED"]["gold_recall"] for r in results]
            df = [rf[i] - sf[i] for i in range(len(results))]
            dr = [rr[i] - sr[i] for i in range(len(results))]
            mf, mr = statistics.mean(df), statistics.mean(dr)
            sef = statistics.stdev(df) / len(df)**0.5 if len(df) > 1 else 0
            ser = statistics.stdev(dr) / len(dr)**0.5 if len(dr) > 1 else 0
            print(f"\n  REAL-SHUFFLED (F1):     {mf:+.4f} CI [{mf-1.96*sef:+.4f}, {mf+1.96*sef:+.4f}]")
            print(f"  REAL-SHUFFLED (recall): {mr:+.4f} CI [{mr-1.96*ser:+.4f}, {mr+1.96*ser:+.4f}]")


if __name__ == "__main__":
    asyncio.run(main())
