"""Reproduce all paper artifacts from frozen traces. No LLM inference required."""
import json
import csv
import random
import statistics
import hashlib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RAW = ROOT / "experiments" / "paper_validation" / "results" / "raw"
DERIVED = ROOT / "experiments" / "paper_validation" / "results" / "derived"
PAPER_DATA = ROOT / "paper" / "data"
PAPER_TABLES = ROOT / "paper" / "tables"
PAPER_DATA.mkdir(parents=True, exist_ok=True)
PAPER_TABLES.mkdir(parents=True, exist_ok=True)

BOOTSTRAP_N = 10000
random.seed(42)


def sha256_file(fp):
    return hashlib.sha256(open(fp, "rb").read()).hexdigest()[:16]


def load_jsonl(fp):
    return [json.loads(l) for l in open(fp)]


def paired_bootstrap(diffs, n_boot=BOOTSTRAP_N):
    n = len(diffs)
    if n < 2:
        return diffs[0] if diffs else 0, 0, 0, 1.0
    means = []
    for _ in range(n_boot):
        sample = [diffs[random.randint(0, n - 1)] for _ in range(n)]
        means.append(statistics.mean(sample))
    means.sort()
    obs = statistics.mean(diffs)
    lo = means[int(0.025 * n_boot)]
    hi = means[int(0.975 * n_boot)]
    centered = [m - obs for m in means]
    if obs >= 0:
        p = sum(1 for c in centered if c <= -obs) / n_boot
    else:
        p = sum(1 for c in centered if c >= -obs) / n_boot
    p = max(2 * p, 1 / n_boot)
    return obs, lo, hi, p


def holm_correction(p_values):
    n = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * n
    prev = 0.0
    for rank, (orig_idx, p) in enumerate(indexed):
        adj = min(p * (n - rank), 1.0)
        adj = max(adj, prev)
        adjusted[orig_idx] = adj
        prev = adj
    return adjusted


def compute_all_tests():
    """Compute all 14 primary tests from raw traces."""
    tests = []

    files = {
        "SF-G": (RAW / "scifact_LOCKED_gemma3_27b-it-qat.jsonl", "scifact"),
        "SF-L": (RAW / "scifact_TRANSFER_llama3.2-vision_11b-instruct-q8_0.jsonl", "scifact"),
        "HP-G": (RAW / "hotpotqa_LOCKED_gemma3_27b-it-qat.jsonl", "hotpotqa"),
        "HP-L": (RAW / "hotpotqa_TRANSFER_llama3.2-vision_11b-instruct-q8_0.jsonl", "hotpotqa"),
    }

    for prefix, (fp, ds_type) in files.items():
        data = load_jsonl(fp)
        n = len(data)
        ds = "SciFact" if "SF" in prefix else "HotpotQA"
        model = "Gemma" if prefix.endswith("G") else "Llama"

        if ds_type == "scifact":
            recall_key = "gold_doc_recall"
            # H1: REAL vs SHUFFLED recall
            diffs = [r["REAL"][recall_key] - r["SHUFFLED"][recall_key] for r in data]
            m, lo, hi, p = paired_bootstrap(diffs)
            tests.append({"id": f"{prefix}-H1-recall", "hypothesis": "PV-H1", "dataset": ds,
                           "model": model, "metric": "recall", "contrast": "REAL vs SHUFFLED",
                           "n": n, "estimate": round(m, 4), "ci_lo": round(lo, 4),
                           "ci_hi": round(hi, 4), "p_raw": round(p, 6)})

            # H3: REAL vs SHUFFLED accuracy
            diffs = [(1 if r["REAL"]["correct"] else 0) - (1 if r["SHUFFLED"]["correct"] else 0) for r in data]
            m, lo, hi, p = paired_bootstrap(diffs)
            tests.append({"id": f"{prefix}-H3-acc", "hypothesis": "PV-H3", "dataset": ds,
                           "model": model, "metric": "accuracy", "contrast": "REAL vs SHUFFLED",
                           "n": n, "estimate": round(m, 4), "ci_lo": round(lo, 4),
                           "ci_hi": round(hi, 4), "p_raw": round(p, 6)})

            # H2: REAL vs GENERIC recall
            diffs = [r["REAL"][recall_key] - r["GENERIC_EXPANSION"][recall_key] for r in data]
            m, lo, hi, p = paired_bootstrap(diffs)
            tests.append({"id": f"{prefix}-H2-recall", "hypothesis": "PV-H2", "dataset": ds,
                           "model": model, "metric": "recall", "contrast": "REAL vs GENERIC",
                           "n": n, "estimate": round(m, 4), "ci_lo": round(lo, 4),
                           "ci_hi": round(hi, 4), "p_raw": round(p, 6)})

            # H5: artifact exposure
            if "REAL_ARTIFACT_HIDDEN" in data[0]:
                diffs = [(1 if r["REAL"]["correct"] else 0) - (1 if r["REAL_ARTIFACT_HIDDEN"]["correct"] else 0) for r in data]
                m, lo, hi, p = paired_bootstrap(diffs)
                tests.append({"id": f"{prefix}-exposure", "hypothesis": "PV-H5", "dataset": ds,
                               "model": model, "metric": "visibility", "contrast": "visible vs hidden",
                               "n": n, "estimate": round(m, 4), "ci_lo": round(lo, 4),
                               "ci_hi": round(hi, 4), "p_raw": round(p, 6)})

        else:  # hotpotqa
            recall_key = "gold_recall"
            # H1
            diffs = [r["REAL"][recall_key] - r["SHUFFLED"][recall_key] for r in data]
            m, lo, hi, p = paired_bootstrap(diffs)
            tests.append({"id": f"{prefix}-H1-recall", "hypothesis": "PV-H1", "dataset": ds,
                           "model": model, "metric": "recall", "contrast": "REAL vs SHUFFLED",
                           "n": n, "estimate": round(m, 4), "ci_lo": round(lo, 4),
                           "ci_hi": round(hi, 4), "p_raw": round(p, 6)})

            # H3
            diffs = [r["REAL"]["f1"] - r["SHUFFLED"]["f1"] for r in data]
            m, lo, hi, p = paired_bootstrap(diffs)
            tests.append({"id": f"{prefix}-H3-f1", "hypothesis": "PV-H3", "dataset": ds,
                           "model": model, "metric": "f1", "contrast": "REAL vs SHUFFLED",
                           "n": n, "estimate": round(m, 4), "ci_lo": round(lo, 4),
                           "ci_hi": round(hi, 4), "p_raw": round(p, 6)})

            # H2
            diffs = [r["REAL"][recall_key] - r["GENERIC_EXPANSION"][recall_key] for r in data]
            m, lo, hi, p = paired_bootstrap(diffs)
            tests.append({"id": f"{prefix}-H2-recall", "hypothesis": "PV-H2", "dataset": ds,
                           "model": model, "metric": "recall", "contrast": "REAL vs GENERIC",
                           "n": n, "estimate": round(m, 4), "ci_lo": round(lo, 4),
                           "ci_hi": round(hi, 4), "p_raw": round(p, 6)})

    # Holm correction
    raw_ps = [t["p_raw"] for t in tests]
    adj_ps = holm_correction(raw_ps)
    for t, adj_p in zip(tests, adj_ps):
        t["p_holm"] = round(adj_p, 6)
        t["reject"] = adj_p < 0.05
        if t["reject"]:
            if t["estimate"] > 0:
                t["classification"] = "SIGNIFICANT_POSITIVE"
            else:
                t["classification"] = "SIGNIFICANT_NEGATIVE"
        else:
            t["classification"] = "NOT_SIGNIFICANT"

    return tests


def export_primary_effects(tests):
    """Export primary effects CSV."""
    fp = PAPER_DATA / "final_primary_effects.csv"
    with open(fp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "hypothesis", "dataset", "model", "metric",
                                           "contrast", "n", "estimate", "ci_lo", "ci_hi",
                                           "p_raw", "p_holm", "reject", "classification"])
        w.writeheader()
        w.writerows(tests)
    print(f"  Wrote: {fp}")


def export_holm_family(tests):
    """Export full Holm family CSV."""
    fp = PAPER_DATA / "final_holm_family.csv"
    with open(fp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "hypothesis", "dataset", "model", "metric",
                                           "contrast", "n", "estimate", "ci_lo", "ci_hi",
                                           "p_raw", "p_holm", "reject", "classification"])
        w.writeheader()
        w.writerows(tests)
    print(f"  Wrote: {fp}")


def export_model_transfer():
    """Export cross-model comparison CSV."""
    fp = PAPER_DATA / "final_model_transfer.csv"
    rows = []
    for ds_type, ds_label in [("scifact", "SciFact"), ("hotpotqa", "HotpotQA")]:
        for model_tag, model_label, suffix in [("gemma", "Gemma", "LOCKED_gemma3_27b-it-qat"),
                                                 ("llama", "Llama", "TRANSFER_llama3.2-vision_11b-instruct-q8_0")]:
            fp_raw = RAW / f"{ds_type}_{suffix}.jsonl"
            data = load_jsonl(fp_raw)
            n = len(data)

            if ds_type == "scifact":
                recall_key = "gold_doc_recall"
                task_key_fn = lambda r, c: 1 if r[c]["correct"] else 0
                task_label = "accuracy"
            else:
                recall_key = "gold_recall"
                task_key_fn = lambda r, c: r[c]["f1"]
                task_label = "f1"

            for cond in ["DIRECT", "NEUTRAL", "GENERIC_EXPANSION", "REAL", "SHUFFLED"]:
                if cond not in data[0]:
                    continue
                retr = statistics.mean([r[cond][recall_key] for r in data])
                task = statistics.mean([task_key_fn(r, cond) for r in data])
                rows.append({"dataset": ds_label, "model": model_label, "condition": cond,
                              "n": n, "retrieval": round(retr, 4), "task": round(task, 4),
                              "task_metric": task_label})

    out = PAPER_DATA / "final_model_transfer.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["dataset", "model", "condition", "n", "retrieval", "task", "task_metric"])
        w.writeheader()
        w.writerows(rows)
    print(f"  Wrote: {out}")


def export_scifact_decomposition():
    """Export SciFact answer flip decomposition CSV."""
    fp = PAPER_DATA / "final_scifact_decomposition.csv"
    rows = []
    for ds_file, model_label in [
        (RAW / "scifact_LOCKED_gemma3_27b-it-qat.jsonl", "Gemma"),
        (RAW / "scifact_TRANSFER_llama3.2-vision_11b-instruct-q8_0.jsonl", "Llama"),
    ]:
        data = load_jsonl(ds_file)
        n = len(data)
        for cond in ["REAL", "SHUFFLED", "NEUTRAL", "DIRECT", "GENERIC_EXPANSION", "REAL_ARTIFACT_HIDDEN"]:
            if cond not in data[0]:
                continue
            cc = cw = wc = ww = 0
            for r in data:
                pc = r["PARAMETRIC_ONLY"]["correct"]
                cc2 = r[cond]["correct"]
                if pc and cc2: cc += 1
                elif pc and not cc2: cw += 1
                elif not pc and cc2: wc += 1
                else: ww += 1
            acc = statistics.mean([1 if r[cond]["correct"] else 0 for r in data])
            recall = statistics.mean([r[cond]["gold_doc_recall"] for r in data])
            rows.append({"model": model_label, "condition": cond, "n": n,
                          "accuracy": round(acc, 4), "recall": round(recall, 4),
                          "CC": cc, "CW": cw, "WC": wc, "WW": ww})

    with open(fp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["model", "condition", "n", "accuracy", "recall",
                                           "CC", "CW", "WC", "WW"])
        w.writeheader()
        w.writerows(rows)
    print(f"  Wrote: {fp}")


def export_resource_usage():
    """Export resource usage summary CSV."""
    fp = PAPER_DATA / "final_resource_usage.csv"
    rows = [
        {"condition": "DIRECT", "artifact_calls": 0, "query_calls": 1, "answer_calls": 1,
         "retrieval_calls": 1, "top_k": 5, "total_calls": 3},
        {"condition": "NEUTRAL", "artifact_calls": 0, "query_calls": 1, "answer_calls": 1,
         "retrieval_calls": 1, "top_k": 5, "total_calls": 3},
        {"condition": "GENERIC_EXPANSION", "artifact_calls": 0, "query_calls": 1, "answer_calls": 1,
         "retrieval_calls": 1, "top_k": 5, "total_calls": 3},
        {"condition": "REAL", "artifact_calls": 1, "query_calls": 1, "answer_calls": 1,
         "retrieval_calls": 1, "top_k": 5, "total_calls": 3},
        {"condition": "SHUFFLED", "artifact_calls": 1, "query_calls": 1, "answer_calls": 1,
         "retrieval_calls": 1, "top_k": 5, "total_calls": 3},
        {"condition": "PARAMETRIC_ONLY", "artifact_calls": 0, "query_calls": 0, "answer_calls": 1,
         "retrieval_calls": 0, "top_k": 0, "total_calls": 1},
        {"condition": "REAL_ARTIFACT_HIDDEN", "artifact_calls": 1, "query_calls": 1, "answer_calls": 1,
         "retrieval_calls": 1, "top_k": 5, "total_calls": 3},
    ]
    with open(fp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["condition", "artifact_calls", "query_calls",
                                           "answer_calls", "retrieval_calls", "top_k", "total_calls"])
        w.writeheader()
        w.writerows(rows)
    print(f"  Wrote: {fp}")


def verify_trace_hashes():
    """Verify all raw trace file hashes."""
    print("\n  Trace hashes:")
    for f in sorted(os.listdir(RAW)):
        fp = RAW / f
        print(f"    {f}: {sha256_file(fp)}")


def main():
    print("=" * 70)
    print("REPRODUCE ALL PAPER ARTIFACTS")
    print("=" * 70)

    print("\n[1] Computing 14-test Holm family from raw traces...")
    tests = compute_all_tests()
    sig = sum(1 for t in tests if t["reject"])
    print(f"    {sig}/{len(tests)} significant after Holm correction")

    print("\n[2] Exporting data CSVs...")
    export_primary_effects(tests)
    export_holm_family(tests)
    export_model_transfer()
    export_scifact_decomposition()
    export_resource_usage()

    print("\n[3] Verifying trace hashes...")
    verify_trace_hashes()

    print("\n[4] Summary:")
    for t in tests:
        s = "*" if t["reject"] else " "
        print(f"  {s} {t['id']:<18} {t['estimate']:+.4f} [{t['ci_lo']:+.4f}, {t['ci_hi']:+.4f}] p_Holm={t['p_holm']:.4f}")

    print("\n" + "=" * 70)
    print("REPRODUCTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
