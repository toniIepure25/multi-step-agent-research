"""Formal statistical analysis with Holm correction for paper validation results."""
import json
import random
import statistics
from pathlib import Path

RESULTS_RAW = Path(__file__).resolve().parent.parent / "results" / "raw"
RESULTS_DERIVED = Path(__file__).resolve().parent.parent / "results" / "derived"
RESULTS_DERIVED.mkdir(parents=True, exist_ok=True)

BOOTSTRAP_N = 10000
random.seed(42)


def paired_bootstrap(diffs, n_boot=BOOTSTRAP_N):
    """Return (mean, lo, hi, p_value) via percentile bootstrap."""
    n = len(diffs)
    if n < 2:
        m = diffs[0] if diffs else 0
        return m, m, m, 1.0
    means = []
    for _ in range(n_boot):
        sample = [diffs[random.randint(0, n - 1)] for _ in range(n)]
        means.append(statistics.mean(sample))
    means.sort()
    lo = means[int(0.025 * n_boot)]
    hi = means[int(0.975 * n_boot)]
    obs = statistics.mean(diffs)
    centered = [m - obs for m in means]
    if obs >= 0:
        p = sum(1 for c in centered if c <= -obs) / n_boot
    else:
        p = sum(1 for c in centered if c >= -obs) / n_boot
    p = max(2 * p, 1 / n_boot)  # two-sided
    return obs, lo, hi, p


def holm_correction(p_values):
    """Holm-Bonferroni correction. Returns adjusted p-values."""
    n = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * n
    prev = 0.0
    for rank, (orig_idx, p) in enumerate(indexed):
        adj = p * (n - rank)
        adj = max(adj, prev)
        adj = min(adj, 1.0)
        adjusted[orig_idx] = adj
        prev = adj
    return adjusted


def load_results(filepath):
    results = []
    with open(filepath) as f:
        for line in f:
            results.append(json.loads(line))
    return results


def main():
    tests = []

    # SciFact Gemma LOCKED
    sf_g = RESULTS_RAW / "scifact_LOCKED_gemma3_27b-it-qat.jsonl"
    if sf_g.exists():
        data = load_results(sf_g)
        n = len(data)
        # REAL vs SHUFFLED recall
        diffs = [r["REAL"]["gold_doc_recall"] - r["SHUFFLED"]["gold_doc_recall"] for r in data]
        m, lo, hi, p = paired_bootstrap(diffs)
        tests.append({"id": "SF-G-H1-recall", "label": "SciFact×Gemma REAL vs SHUFFLED recall",
                       "n": n, "effect": m, "ci": [lo, hi], "p_raw": p, "hypothesis": "PV-H1"})

        # REAL vs SHUFFLED accuracy
        diffs = [(1 if r["REAL"]["correct"] else 0) - (1 if r["SHUFFLED"]["correct"] else 0) for r in data]
        m, lo, hi, p = paired_bootstrap(diffs)
        tests.append({"id": "SF-G-H3-acc", "label": "SciFact×Gemma REAL vs SHUFFLED accuracy",
                       "n": n, "effect": m, "ci": [lo, hi], "p_raw": p, "hypothesis": "PV-H3"})

        # REAL vs GENERIC recall
        diffs = [r["REAL"]["gold_doc_recall"] - r["GENERIC_EXPANSION"]["gold_doc_recall"] for r in data]
        m, lo, hi, p = paired_bootstrap(diffs)
        tests.append({"id": "SF-G-H2-recall", "label": "SciFact×Gemma REAL vs GENERIC recall",
                       "n": n, "effect": m, "ci": [lo, hi], "p_raw": p, "hypothesis": "PV-H2"})

        # Artifact exposure
        diffs = [(1 if r["REAL"]["correct"] else 0) - (1 if r["REAL_ARTIFACT_HIDDEN"]["correct"] else 0) for r in data]
        m, lo, hi, p = paired_bootstrap(diffs)
        tests.append({"id": "SF-G-exposure", "label": "SciFact×Gemma artifact visible vs hidden",
                       "n": n, "effect": m, "ci": [lo, hi], "p_raw": p, "hypothesis": "PV-H5"})

    # SciFact Llama TRANSFER
    sf_l = RESULTS_RAW / "scifact_TRANSFER_llama3.2-vision_11b-instruct-q8_0.jsonl"
    if sf_l.exists():
        data = load_results(sf_l)
        n = len(data)
        diffs = [r["REAL"]["gold_doc_recall"] - r["SHUFFLED"]["gold_doc_recall"] for r in data]
        m, lo, hi, p = paired_bootstrap(diffs)
        tests.append({"id": "SF-L-H1-recall", "label": "SciFact×Llama REAL vs SHUFFLED recall",
                       "n": n, "effect": m, "ci": [lo, hi], "p_raw": p, "hypothesis": "PV-H1"})

        diffs = [(1 if r["REAL"]["correct"] else 0) - (1 if r["SHUFFLED"]["correct"] else 0) for r in data]
        m, lo, hi, p = paired_bootstrap(diffs)
        tests.append({"id": "SF-L-H3-acc", "label": "SciFact×Llama REAL vs SHUFFLED accuracy",
                       "n": n, "effect": m, "ci": [lo, hi], "p_raw": p, "hypothesis": "PV-H3"})

        diffs = [r["REAL"]["gold_doc_recall"] - r["GENERIC_EXPANSION"]["gold_doc_recall"] for r in data]
        m, lo, hi, p = paired_bootstrap(diffs)
        tests.append({"id": "SF-L-H2-recall", "label": "SciFact×Llama REAL vs GENERIC recall",
                       "n": n, "effect": m, "ci": [lo, hi], "p_raw": p, "hypothesis": "PV-H2"})

        diffs = [(1 if r["REAL"]["correct"] else 0) - (1 if r["REAL_ARTIFACT_HIDDEN"]["correct"] else 0) for r in data]
        m, lo, hi, p = paired_bootstrap(diffs)
        tests.append({"id": "SF-L-exposure", "label": "SciFact×Llama artifact visible vs hidden",
                       "n": n, "effect": m, "ci": [lo, hi], "p_raw": p, "hypothesis": "PV-H5"})

    # HotpotQA Gemma LOCKED
    hp_g = RESULTS_RAW / "hotpotqa_LOCKED_gemma3_27b-it-qat.jsonl"
    if hp_g.exists():
        data = load_results(hp_g)
        n = len(data)
        diffs = [r["REAL"]["gold_recall"] - r["SHUFFLED"]["gold_recall"] for r in data]
        m, lo, hi, p = paired_bootstrap(diffs)
        tests.append({"id": "HP-G-H1-recall", "label": "HotpotQA×Gemma REAL vs SHUFFLED recall",
                       "n": n, "effect": m, "ci": [lo, hi], "p_raw": p, "hypothesis": "PV-H1"})

        diffs = [r["REAL"]["f1"] - r["SHUFFLED"]["f1"] for r in data]
        m, lo, hi, p = paired_bootstrap(diffs)
        tests.append({"id": "HP-G-H3-f1", "label": "HotpotQA×Gemma REAL vs SHUFFLED F1",
                       "n": n, "effect": m, "ci": [lo, hi], "p_raw": p, "hypothesis": "PV-H3"})

        diffs = [r["REAL"]["gold_recall"] - r["GENERIC_EXPANSION"]["gold_recall"] for r in data]
        m, lo, hi, p = paired_bootstrap(diffs)
        tests.append({"id": "HP-G-H2-recall", "label": "HotpotQA×Gemma REAL vs GENERIC recall",
                       "n": n, "effect": m, "ci": [lo, hi], "p_raw": p, "hypothesis": "PV-H2"})

    # HotpotQA Llama TRANSFER
    hp_l = RESULTS_RAW / "hotpotqa_TRANSFER_llama3.2-vision_11b-instruct-q8_0.jsonl"
    if hp_l.exists():
        data = load_results(hp_l)
        n = len(data)
        diffs = [r["REAL"]["gold_recall"] - r["SHUFFLED"]["gold_recall"] for r in data]
        m, lo, hi, p = paired_bootstrap(diffs)
        tests.append({"id": "HP-L-H1-recall", "label": "HotpotQA×Llama REAL vs SHUFFLED recall",
                       "n": n, "effect": m, "ci": [lo, hi], "p_raw": p, "hypothesis": "PV-H1"})

        diffs = [r["REAL"]["f1"] - r["SHUFFLED"]["f1"] for r in data]
        m, lo, hi, p = paired_bootstrap(diffs)
        tests.append({"id": "HP-L-H3-f1", "label": "HotpotQA×Llama REAL vs SHUFFLED F1",
                       "n": n, "effect": m, "ci": [lo, hi], "p_raw": p, "hypothesis": "PV-H3"})

        diffs = [r["REAL"]["gold_recall"] - r["GENERIC_EXPANSION"]["gold_recall"] for r in data]
        m, lo, hi, p = paired_bootstrap(diffs)
        tests.append({"id": "HP-L-H2-recall", "label": "HotpotQA×Llama REAL vs GENERIC recall",
                       "n": n, "effect": m, "ci": [lo, hi], "p_raw": p, "hypothesis": "PV-H2"})

    # Holm correction
    raw_ps = [t["p_raw"] for t in tests]
    adj_ps = holm_correction(raw_ps)
    for t, adj_p in zip(tests, adj_ps):
        t["p_holm"] = round(adj_p, 6)
        t["significant_holm"] = adj_p < 0.05
        t["effect"] = round(t["effect"], 4)
        t["ci"] = [round(t["ci"][0], 4), round(t["ci"][1], 4)]
        t["p_raw"] = round(t["p_raw"], 6)

    # Print table
    print(f"\n{'='*100}")
    print(f"FORMAL STATISTICAL RESULTS — {len(tests)} tests, Holm-corrected")
    print(f"{'='*100}")
    print(f"{'ID':<18} {'Effect':>8} {'95% CI':>20} {'p_raw':>10} {'p_holm':>10} {'Sig':>5}  Hypothesis")
    print("-" * 100)
    for t in tests:
        ci_str = f"[{t['ci'][0]:+.4f}, {t['ci'][1]:+.4f}]"
        sig = "***" if t["p_holm"] < 0.001 else ("**" if t["p_holm"] < 0.01 else ("*" if t["p_holm"] < 0.05 else ""))
        print(f"{t['id']:<18} {t['effect']:>+8.4f} {ci_str:>20} {t['p_raw']:>10.6f} {t['p_holm']:>10.6f} {sig:>5}  {t['hypothesis']}")

    # Summary by hypothesis
    print(f"\n{'='*60}")
    print("HYPOTHESIS VERDICTS (Holm-corrected)")
    print(f"{'='*60}")
    by_hyp = {}
    for t in tests:
        by_hyp.setdefault(t["hypothesis"], []).append(t)
    for hyp, ts in sorted(by_hyp.items()):
        sig_count = sum(1 for t in ts if t["significant_holm"])
        print(f"\n  {hyp}: {sig_count}/{len(ts)} tests significant after correction")
        for t in ts:
            s = "Y" if t["significant_holm"] else "N"
            print(f"    {s} {t['id']}: {t['effect']:+.4f} (p_holm={t['p_holm']:.4f})")

    # Save
    out = RESULTS_DERIVED / "formal_statistics.json"
    with open(out, "w") as f:
        json.dump({"tests": tests, "n_tests": len(tests), "method": "paired_bootstrap_10000_holm"}, f, indent=2)
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
