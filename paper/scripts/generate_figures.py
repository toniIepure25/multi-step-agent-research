"""Generate publication-quality figures for the paper.
Requires: matplotlib. Run: python paper/scripts/generate_figures.py
"""
import json
import csv
import random
import statistics
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MPL = True
except ImportError:
    HAS_MPL = False
    print("WARNING: matplotlib not available. Generating data only.")

ROOT = Path(__file__).resolve().parent.parent.parent
RAW = ROOT / "experiments" / "paper_validation" / "results" / "raw"
FIGURES = ROOT / "paper" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

BOOTSTRAP_N = 10000
random.seed(42)


def paired_bootstrap(diffs, n_boot=BOOTSTRAP_N):
    n = len(diffs)
    means = []
    for _ in range(n_boot):
        sample = [diffs[random.randint(0, n - 1)] for _ in range(n)]
        means.append(statistics.mean(sample))
    means.sort()
    return statistics.mean(diffs), means[int(0.025*n_boot)], means[int(0.975*n_boot)]


def load_jsonl(fp):
    return [json.loads(l) for l in open(fp)]


def fig2_retrieval_reasoning_plane():
    """Figure 2: Retrieval gain vs downstream gain — the signature figure."""
    if not HAS_MPL:
        print("  Skipping fig2 (no matplotlib)")
        return

    cells = {
        "SciFact x Gemma": (RAW / "scifact_LOCKED_gemma3_27b-it-qat.jsonl", "scifact"),
        "SciFact x Llama": (RAW / "scifact_TRANSFER_llama3.2-vision_11b-instruct-q8_0.jsonl", "scifact"),
        "HotpotQA x Gemma": (RAW / "hotpotqa_LOCKED_gemma3_27b-it-qat.jsonl", "hotpotqa"),
        "HotpotQA x Llama": (RAW / "hotpotqa_TRANSFER_llama3.2-vision_11b-instruct-q8_0.jsonl", "hotpotqa"),
    }

    fig, ax = plt.subplots(1, 1, figsize=(7, 5.5))

    colors = {"SciFact x Gemma": "#d62728", "SciFact x Llama": "#ff7f0e",
              "HotpotQA x Gemma": "#1f77b4", "HotpotQA x Llama": "#2ca02c"}
    markers = {"SciFact x Gemma": "s", "SciFact x Llama": "^",
               "HotpotQA x Gemma": "o", "HotpotQA x Llama": "D"}

    for label, (fp, ds_type) in cells.items():
        data = load_jsonl(fp)
        if ds_type == "scifact":
            r_diffs = [r["REAL"]["gold_doc_recall"] - r["SHUFFLED"]["gold_doc_recall"] for r in data]
            y_diffs = [(1 if r["REAL"]["correct"] else 0) - (1 if r["SHUFFLED"]["correct"] else 0) for r in data]
        else:
            r_diffs = [r["REAL"]["gold_recall"] - r["SHUFFLED"]["gold_recall"] for r in data]
            y_diffs = [r["REAL"]["f1"] - r["SHUFFLED"]["f1"] for r in data]

        r_m, r_lo, r_hi = paired_bootstrap(r_diffs)
        y_m, y_lo, y_hi = paired_bootstrap(y_diffs)

        ax.errorbar(r_m, y_m,
                    xerr=[[r_m - r_lo], [r_hi - r_m]],
                    yerr=[[y_m - y_lo], [y_hi - y_m]],
                    fmt=markers[label], color=colors[label], markersize=10,
                    capsize=4, capthick=1.5, linewidth=1.5, label=label, zorder=5)

    ax.axhline(0, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.axvline(0, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)

    ax.fill_between([0, 0.65], 0, 0.25, alpha=0.06, color="green")
    ax.fill_between([0, 0.65], -0.5, 0, alpha=0.06, color="red")

    ax.text(0.45, 0.15, "Positive\nTransfer", fontsize=9, color="green", alpha=0.7, ha="center", style="italic")
    ax.text(0.45, -0.35, "Retrieval-Reasoning\nDissociation", fontsize=9, color="red", alpha=0.7, ha="center", style="italic")

    ax.set_xlabel(r"$\Delta$ Retrieval (REAL $-$ SHUFFLED)", fontsize=12)
    ax.set_ylabel(r"$\Delta$ Task Performance (REAL $-$ SHUFFLED)", fontsize=12)
    ax.set_title("Retrieval Gain vs. Downstream Utility", fontsize=13, fontweight="bold")
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.set_xlim(-0.05, 0.65)
    ax.set_ylim(-0.5, 0.25)
    ax.grid(True, alpha=0.2)

    plt.tight_layout()
    out = FIGURES / "fig2_retrieval_reasoning_plane.pdf"
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.savefig(FIGURES / "fig2_retrieval_reasoning_plane.png", dpi=200, bbox_inches="tight")
    plt.close()
    print(f"  Wrote: {out}")


def fig3_model_transfer():
    """Figure 3: Forest plot of retrieval and task effects by dataset x model."""
    if not HAS_MPL:
        print("  Skipping fig3 (no matplotlib)")
        return

    cells = [
        ("SF x Gemma", RAW / "scifact_LOCKED_gemma3_27b-it-qat.jsonl", "scifact"),
        ("SF x Llama", RAW / "scifact_TRANSFER_llama3.2-vision_11b-instruct-q8_0.jsonl", "scifact"),
        ("HP x Gemma", RAW / "hotpotqa_LOCKED_gemma3_27b-it-qat.jsonl", "hotpotqa"),
        ("HP x Llama", RAW / "hotpotqa_TRANSFER_llama3.2-vision_11b-instruct-q8_0.jsonl", "hotpotqa"),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)

    for panel_idx, (title, contrast_label) in enumerate([
        ("Retrieval Effect\n(REAL - SHUFFLED)", "retrieval"),
        ("Task Effect\n(REAL - SHUFFLED)", "task"),
    ]):
        ax = axes[panel_idx]
        y_positions = list(range(len(cells)))

        for i, (label, fp, ds_type) in enumerate(cells):
            data = load_jsonl(fp)
            if ds_type == "scifact":
                if contrast_label == "retrieval":
                    diffs = [r["REAL"]["gold_doc_recall"] - r["SHUFFLED"]["gold_doc_recall"] for r in data]
                else:
                    diffs = [(1 if r["REAL"]["correct"] else 0) - (1 if r["SHUFFLED"]["correct"] else 0) for r in data]
            else:
                if contrast_label == "retrieval":
                    diffs = [r["REAL"]["gold_recall"] - r["SHUFFLED"]["gold_recall"] for r in data]
                else:
                    diffs = [r["REAL"]["f1"] - r["SHUFFLED"]["f1"] for r in data]

            m, lo, hi = paired_bootstrap(diffs)
            color = "#d62728" if "SF" in label else "#1f77b4"
            ax.errorbar(m, i, xerr=[[m - lo], [hi - m]], fmt="o", color=color,
                        markersize=8, capsize=5, capthick=1.5, linewidth=1.5)

        ax.axvline(0, color="gray", linestyle="--", linewidth=0.8)
        ax.set_yticks(y_positions)
        ax.set_yticklabels([c[0] for c in cells])
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xlabel("Effect size", fontsize=10)
        ax.grid(True, axis="x", alpha=0.2)

    plt.tight_layout()
    out = FIGURES / "fig3_model_transfer.pdf"
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.savefig(FIGURES / "fig3_model_transfer.png", dpi=200, bbox_inches="tight")
    plt.close()
    print(f"  Wrote: {out}")


def fig4_scifact_decomposition():
    """Figure 4: SciFact answer flip stacked bar chart."""
    if not HAS_MPL:
        print("  Skipping fig4 (no matplotlib)")
        return

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    for ax_idx, (fp, model_label) in enumerate([
        (RAW / "scifact_LOCKED_gemma3_27b-it-qat.jsonl", "Gemma (N=88)"),
        (RAW / "scifact_TRANSFER_llama3.2-vision_11b-instruct-q8_0.jsonl", "Llama (N=100)"),
    ]):
        data = load_jsonl(fp)
        ax = axes[ax_idx]
        conditions = ["SHUFFLED", "NEUTRAL", "DIRECT", "REAL", "GENERIC_EXPANSION", "REAL_ARTIFACT_HIDDEN"]
        cond_short = ["SHUF", "NEUT", "DIRECT", "REAL", "GENERIC", "HIDDEN"]
        cc_vals, cw_vals, wc_vals, ww_vals = [], [], [], []

        for cond in conditions:
            if cond not in data[0]:
                cc_vals.append(0); cw_vals.append(0); wc_vals.append(0); ww_vals.append(0)
                continue
            cc = cw = wc = ww = 0
            for r in data:
                pc = r["PARAMETRIC_ONLY"]["correct"]
                cc2 = r[cond]["correct"]
                if pc and cc2: cc += 1
                elif pc and not cc2: cw += 1
                elif not pc and cc2: wc += 1
                else: ww += 1
            n = len(data)
            cc_vals.append(cc/n); cw_vals.append(cw/n); wc_vals.append(wc/n); ww_vals.append(ww/n)

        x = range(len(conditions))
        ax.bar(x, cc_vals, label="CC (correct->correct)", color="#2ca02c", alpha=0.8)
        ax.bar(x, wc_vals, bottom=cc_vals, label="WC (helpful flip)", color="#1f77b4", alpha=0.8)
        cw_bottom = [cc_vals[i] + wc_vals[i] for i in range(len(conditions))]
        ax.bar(x, cw_vals, bottom=cw_bottom, label="CW (harmful flip)", color="#d62728", alpha=0.8)
        ww_bottom = [cw_bottom[i] + cw_vals[i] for i in range(len(conditions))]
        ax.bar(x, ww_vals, bottom=ww_bottom, label="WW (wrong->wrong)", color="#7f7f7f", alpha=0.6)

        ax.set_xticks(x)
        ax.set_xticklabels(cond_short, rotation=30, ha="right", fontsize=9)
        ax.set_ylabel("Proportion", fontsize=10)
        ax.set_title(f"Answer Flips: {model_label}", fontsize=11, fontweight="bold")
        ax.set_ylim(0, 1.05)
        if ax_idx == 1:
            ax.legend(loc="upper right", fontsize=8, framealpha=0.9)

    plt.tight_layout()
    out = FIGURES / "fig4_scifact_decomposition.pdf"
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.savefig(FIGURES / "fig4_scifact_decomposition.png", dpi=200, bbox_inches="tight")
    plt.close()
    print(f"  Wrote: {out}")


def fig5_pipeline_effects():
    """Figure 5: Bar chart of retrieval and task performance by condition."""
    if not HAS_MPL:
        print("  Skipping fig5 (no matplotlib)")
        return

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    configs = [
        ("SciFact x Gemma", RAW / "scifact_LOCKED_gemma3_27b-it-qat.jsonl", "scifact"),
        ("SciFact x Llama", RAW / "scifact_TRANSFER_llama3.2-vision_11b-instruct-q8_0.jsonl", "scifact"),
        ("HotpotQA x Gemma", RAW / "hotpotqa_LOCKED_gemma3_27b-it-qat.jsonl", "hotpotqa"),
        ("HotpotQA x Llama", RAW / "hotpotqa_TRANSFER_llama3.2-vision_11b-instruct-q8_0.jsonl", "hotpotqa"),
    ]
    conditions = ["DIRECT", "NEUTRAL", "GENERIC_EXPANSION", "REAL", "SHUFFLED"]
    cond_short = ["DIRECT", "NEUTRAL", "GENERIC", "REAL", "SHUFFLED"]
    colors = ["#7f7f7f", "#bcbd22", "#17becf", "#1f77b4", "#d62728"]

    for idx, (title, fp, ds_type) in enumerate(configs):
        ax = axes[idx // 2][idx % 2]
        data = load_jsonl(fp)

        retr_vals = []
        task_vals = []
        for cond in conditions:
            if cond not in data[0]:
                retr_vals.append(0)
                task_vals.append(0)
                continue
            if ds_type == "scifact":
                retr_vals.append(statistics.mean([r[cond]["gold_doc_recall"] for r in data]))
                task_vals.append(statistics.mean([1 if r[cond]["correct"] else 0 for r in data]))
            else:
                retr_vals.append(statistics.mean([r[cond]["gold_recall"] for r in data]))
                task_vals.append(statistics.mean([r[cond]["f1"] for r in data]))

        x = range(len(conditions))
        width = 0.35
        bars1 = ax.bar([xi - width/2 for xi in x], retr_vals, width, label="Retrieval", color=colors, alpha=0.6)
        bars2 = ax.bar([xi + width/2 for xi in x], task_vals, width, label="Task", color=colors, alpha=0.9,
                        edgecolor="black", linewidth=0.5)

        ax.set_xticks(x)
        ax.set_xticklabels(cond_short, rotation=30, ha="right", fontsize=8)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_ylim(0, 1.1)
        task_label = "Accuracy" if ds_type == "scifact" else "F1"
        ax.legend(["Retrieval", task_label], fontsize=8, loc="upper right")
        ax.grid(True, axis="y", alpha=0.2)

    plt.tight_layout()
    out = FIGURES / "fig5_pipeline_effects.pdf"
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.savefig(FIGURES / "fig5_pipeline_effects.png", dpi=200, bbox_inches="tight")
    plt.close()
    print(f"  Wrote: {out}")


def main():
    print("Generating paper figures...")
    fig2_retrieval_reasoning_plane()
    fig3_model_transfer()
    fig4_scifact_decomposition()
    fig5_pipeline_effects()
    print("Done.")


if __name__ == "__main__":
    main()
