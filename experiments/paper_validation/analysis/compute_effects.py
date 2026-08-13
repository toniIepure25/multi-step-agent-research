"""Compute primary effects and bootstrap CIs for paper validation results."""
import json
import random
import statistics
import sys
from pathlib import Path

RESULTS_RAW = Path(__file__).resolve().parent.parent / "results" / "raw"
RESULTS_DERIVED = Path(__file__).resolve().parent.parent / "results" / "derived"
RESULTS_DERIVED.mkdir(parents=True, exist_ok=True)

BOOTSTRAP_N = 10000
CI_LEVEL = 0.95
random.seed(42)


def paired_bootstrap_ci(diffs, n_boot=BOOTSTRAP_N, ci=CI_LEVEL):
    """Task-level paired bootstrap percentile CI."""
    n = len(diffs)
    if n < 2:
        m = diffs[0] if diffs else 0
        return m, m, m
    means = []
    for _ in range(n_boot):
        sample = [diffs[random.randint(0, n - 1)] for _ in range(n)]
        means.append(statistics.mean(sample))
    means.sort()
    alpha = (1 - ci) / 2
    lo = means[int(alpha * n_boot)]
    hi = means[int((1 - alpha) * n_boot)]
    return statistics.mean(diffs), lo, hi


def mcnemar_test(cc, cw, wc, ww):
    """McNemar chi-squared for paired binary outcomes."""
    b, c = cw, wc
    if b + c == 0:
        return 0.0, 1.0
    chi2 = (abs(b - c) - 1) ** 2 / (b + c) if (b + c) > 0 else 0
    from math import exp, sqrt, pi
    p = exp(-chi2 / 2) if chi2 < 30 else 0.0
    return chi2, p


def analyze_scifact(filepath, label=""):
    """Analyze SciFact results."""
    results = []
    with open(filepath) as f:
        for line in f:
            results.append(json.loads(line))

    n = len(results)
    print(f"\n{'='*60}")
    print(f"SCIFACT {label} (N={n})")
    print(f"{'='*60}")

    conditions = ["DIRECT", "NEUTRAL", "GENERIC_EXPANSION", "REAL", "SHUFFLED",
                   "PARAMETRIC_ONLY", "REAL_ARTIFACT_HIDDEN"]

    # Basic summary
    for cond in conditions:
        if cond not in results[0]:
            continue
        accs = [r[cond]["correct"] for r in results]
        recs = [r[cond]["gold_doc_recall"] for r in results]
        rat_recs = [r[cond].get("rationale_recall", 0) for r in results]
        print(f"  {cond:25s}: acc={statistics.mean(accs):.3f}  doc_recall={statistics.mean(recs):.3f}  rat_recall={statistics.mean(rat_recs):.3f}")

    effects = {}

    # Primary contrasts
    for control, ctrl_name in [("SHUFFLED", "shuffled"), ("GENERIC_EXPANSION", "generic")]:
        if control not in results[0]:
            continue
        acc_diffs = [(1 if r["REAL"]["correct"] else 0) - (1 if r[control]["correct"] else 0) for r in results]
        rec_diffs = [r["REAL"]["gold_doc_recall"] - r[control]["gold_doc_recall"] for r in results]
        rat_diffs = [r["REAL"].get("rationale_recall", 0) - r[control].get("rationale_recall", 0) for r in results]

        for metric, diffs in [("accuracy", acc_diffs), ("doc_recall", rec_diffs), ("rat_recall", rat_diffs)]:
            m, lo, hi = paired_bootstrap_ci(diffs)
            key = f"REAL_vs_{ctrl_name}_{metric}"
            effects[key] = {"effect": round(m, 4), "ci_lo": round(lo, 4), "ci_hi": round(hi, 4), "n": n}
            sig = "*" if (lo > 0 or hi < 0) else ""
            print(f"\n  REAL vs {control} ({metric}): {m:+.4f} [{lo:+.4f}, {hi:+.4f}] {sig}")

    # Answer flip analysis (if PARAMETRIC_ONLY available)
    if "PARAMETRIC_ONLY" in results[0]:
        print(f"\n  --- Answer Flip Analysis ---")
        for cond in ["REAL", "SHUFFLED", "NEUTRAL", "DIRECT", "GENERIC_EXPANSION", "REAL_ARTIFACT_HIDDEN"]:
            if cond not in results[0]:
                continue
            cc = cw = wc = ww = 0
            for r in results:
                p_correct = r["PARAMETRIC_ONLY"]["correct"]
                c_correct = r[cond]["correct"]
                if p_correct and c_correct: cc += 1
                elif p_correct and not c_correct: cw += 1
                elif not p_correct and c_correct: wc += 1
                else: ww += 1
            total = cc + cw + wc + ww
            print(f"  {cond:25s}: CC={cc:3d} CW={cw:3d}(harmful) WC={wc:3d}(helpful) WW={ww:3d}")
            effects[f"flips_{cond}"] = {"CC": cc, "CW": cw, "WC": wc, "WW": ww}

    # Artifact exposure comparison
    if "REAL_ARTIFACT_HIDDEN" in results[0] and "REAL" in results[0]:
        vis_acc = [1 if r["REAL"]["correct"] else 0 for r in results]
        hid_acc = [1 if r["REAL_ARTIFACT_HIDDEN"]["correct"] else 0 for r in results]
        diff = [vis_acc[i] - hid_acc[i] for i in range(n)]
        m, lo, hi = paired_bootstrap_ci(diff)
        effects["artifact_exposure_effect"] = {"effect": round(m, 4), "ci_lo": round(lo, 4), "ci_hi": round(hi, 4)}
        print(f"\n  Artifact Visible vs Hidden (acc): {m:+.4f} [{lo:+.4f}, {hi:+.4f}]")

    return effects


def analyze_hotpotqa(filepath, label=""):
    """Analyze HotpotQA results."""
    results = []
    with open(filepath) as f:
        for line in f:
            results.append(json.loads(line))

    n = len(results)
    print(f"\n{'='*60}")
    print(f"HOTPOTQA {label} (N={n})")
    print(f"{'='*60}")

    conditions = ["DIRECT", "NEUTRAL", "GENERIC_EXPANSION", "REAL", "SHUFFLED"]

    for cond in conditions:
        if cond not in results[0]:
            continue
        f1s = [r[cond]["f1"] for r in results]
        recs = [r[cond]["gold_recall"] for r in results]
        print(f"  {cond:25s}: F1={statistics.mean(f1s):.3f}  recall={statistics.mean(recs):.3f}")

    effects = {}

    for control, ctrl_name in [("SHUFFLED", "shuffled"), ("GENERIC_EXPANSION", "generic")]:
        if control not in results[0]:
            continue
        f1_diffs = [r["REAL"]["f1"] - r[control]["f1"] for r in results]
        rec_diffs = [r["REAL"]["gold_recall"] - r[control]["gold_recall"] for r in results]

        for metric, diffs in [("f1", f1_diffs), ("recall", rec_diffs)]:
            m, lo, hi = paired_bootstrap_ci(diffs)
            key = f"REAL_vs_{ctrl_name}_{metric}"
            effects[key] = {"effect": round(m, 4), "ci_lo": round(lo, 4), "ci_hi": round(hi, 4), "n": n}
            sig = "*" if (lo > 0 or hi < 0) else ""
            print(f"\n  REAL vs {control} ({metric}): {m:+.4f} [{lo:+.4f}, {hi:+.4f}] {sig}")

    return effects


def main():
    all_effects = {}

    # SciFact locked
    sf_locked = RESULTS_RAW / "scifact_LOCKED_gemma3_27b-it-qat.jsonl"
    if sf_locked.exists():
        all_effects["scifact_locked_gemma"] = analyze_scifact(sf_locked, "LOCKED Gemma")

    # SciFact transfer (Llama same tasks)
    sf_transfer = RESULTS_RAW / "scifact_TRANSFER_llama3.2-vision_11b-instruct-q8_0.jsonl"
    if sf_transfer.exists():
        all_effects["scifact_transfer_llama"] = analyze_scifact(sf_transfer, "TRANSFER Llama")

    # HotpotQA locked
    hp_locked = RESULTS_RAW / "hotpotqa_LOCKED_gemma3_27b-it-qat.jsonl"
    if hp_locked.exists():
        all_effects["hotpotqa_locked_gemma"] = analyze_hotpotqa(hp_locked, "LOCKED Gemma")

    # HotpotQA transfer
    hp_transfer = RESULTS_RAW / "hotpotqa_TRANSFER_llama3.2-vision_11b-instruct-q8_0.jsonl"
    if hp_transfer.exists():
        all_effects["hotpotqa_transfer_llama"] = analyze_hotpotqa(hp_transfer, "TRANSFER Llama")

    # Save
    out = RESULTS_DERIVED / "primary_effects.json"
    with open(out, "w") as f:
        json.dump(all_effects, f, indent=2)
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
