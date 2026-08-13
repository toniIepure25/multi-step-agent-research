"""Generate LaTeX tables for the paper from validation results."""
import json
from pathlib import Path

DERIVED = Path(__file__).resolve().parent.parent / "results" / "derived"
TABLES = Path(__file__).resolve().parent.parent / "tables"
TABLES.mkdir(parents=True, exist_ok=True)


def load_stats():
    with open(DERIVED / "formal_statistics.json") as f:
        return json.load(f)


def table1_condition_summary():
    """Table 1: Condition performance summary across datasets and models."""
    RAW = Path(__file__).resolve().parent.parent / "results" / "raw"

    datasets = [
        ("SciFact", "Gemma", RAW / "scifact_LOCKED_gemma3_27b-it-qat.jsonl", "accuracy", "doc_recall"),
        ("SciFact", "Llama", RAW / "scifact_TRANSFER_llama3.2-vision_11b-instruct-q8_0.jsonl", "accuracy", "doc_recall"),
        ("HotpotQA", "Gemma", RAW / "hotpotqa_LOCKED_gemma3_27b-it-qat.jsonl", "f1", "gold_recall"),
        ("HotpotQA", "Llama", RAW / "hotpotqa_TRANSFER_llama3.2-vision_11b-instruct-q8_0.jsonl", "f1", "gold_recall"),
    ]

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Performance across conditions, datasets, and models. Retrieval = gold evidence recall. Task = accuracy (SciFact) or F1 (HotpotQA).}",
        r"\label{tab:conditions}",
        r"\small",
        r"\begin{tabular}{ll" + "cc" * 4 + "}",
        r"\toprule",
        r"& & \multicolumn{2}{c}{SciFact$\times$Gemma} & \multicolumn{2}{c}{SciFact$\times$Llama} & \multicolumn{2}{c}{HotpotQA$\times$Gemma} & \multicolumn{2}{c}{HotpotQA$\times$Llama} \\",
        r"\cmidrule(lr){3-4} \cmidrule(lr){5-6} \cmidrule(lr){7-8} \cmidrule(lr){9-10}",
        r"Condition & & Retr. & Task & Retr. & Task & Retr. & Task & Retr. & Task \\",
        r"\midrule",
    ]

    conditions_order = ["DIRECT", "NEUTRAL", "GENERIC_EXPANSION", "REAL", "SHUFFLED", "PARAMETRIC_ONLY", "REAL_ARTIFACT_HIDDEN"]
    cond_labels = {
        "DIRECT": r"\textsc{Direct}",
        "NEUTRAL": r"\textsc{Neutral}",
        "GENERIC_EXPANSION": r"\textsc{Generic}",
        "REAL": r"\textsc{Real}",
        "SHUFFLED": r"\textsc{Shuffled}",
        "PARAMETRIC_ONLY": r"\textsc{Parametric}",
        "REAL_ARTIFACT_HIDDEN": r"\textsc{Real-Hidden}",
    }

    all_data = {}
    for ds_name, model_name, filepath, task_key, retr_key in datasets:
        results = []
        with open(filepath) as f:
            for line in f:
                results.append(json.loads(line))
        key = f"{ds_name}x{model_name}"
        all_data[key] = {}
        for cond in conditions_order:
            if cond not in results[0]:
                all_data[key][cond] = (None, None)
                continue
            import statistics
            if task_key == "accuracy":
                task_vals = [1 if r[cond]["correct"] else 0 for r in results]
            else:
                task_vals = [r[cond][task_key] for r in results]
            if retr_key == "doc_recall":
                retr_vals = [r[cond]["gold_doc_recall"] for r in results]
            else:
                retr_vals = [r[cond][retr_key] for r in results]
            all_data[key][cond] = (statistics.mean(retr_vals), statistics.mean(task_vals))

    for cond in conditions_order:
        label = cond_labels[cond]
        cells = []
        for ds_name, model_name, _, _, _ in datasets:
            key = f"{ds_name}x{model_name}"
            retr, task = all_data[key].get(cond, (None, None))
            if retr is None:
                cells.append("-- & --")
            else:
                cells.append(f"{retr:.3f} & {task:.3f}")
        lines.append(f"{label} & & " + " & ".join(cells) + r" \\")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])

    return "\n".join(lines)


def table2_primary_effects():
    """Table 2: Primary confirmatory effects with Holm correction."""
    stats = load_stats()

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Primary confirmatory effects. Paired bootstrap (10{,}000 resamples) with Holm correction over 14 simultaneous tests. Bold = significant at $\alpha=0.05$ after correction.}",
        r"\label{tab:effects}",
        r"\small",
        r"\begin{tabular}{lllrccc}",
        r"\toprule",
        r"Hyp. & Dataset$\times$Model & Contrast & Effect & 95\% CI & $p_\text{Holm}$ & $N$ \\",
        r"\midrule",
    ]

    for t in stats["tests"]:
        eff = f"{t['effect']:+.3f}"
        if t["significant_holm"]:
            eff = r"\textbf{" + eff + "}"
        ci = f"[{t['ci'][0]:+.3f}, {t['ci'][1]:+.3f}]"
        p_str = f"{t['p_holm']:.4f}" if t['p_holm'] >= 0.001 else "<.001"
        if t["significant_holm"]:
            p_str = r"\textbf{" + p_str + "}"

        parts = t["id"].split("-")
        ds = "SciFact" if parts[0] == "SF" else "HotpotQA"
        model = "Gemma" if parts[1] == "G" else "Llama"
        metric = parts[-1]
        contrast_parts = t["label"].split(" ", 1)[1] if " " in t["label"] else t["label"]

        lines.append(f"{t['hypothesis']} & {ds}$\\times${model} & {metric} & {eff} & {ci} & {p_str} & {t['n']} \\\\")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])
    return "\n".join(lines)


def table3_answer_flips():
    """Table 3: Answer flip analysis for SciFact."""
    RAW = Path(__file__).resolve().parent.parent / "results" / "raw"

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Answer flip analysis on SciFact. CC = correct$\to$correct, CW = correct$\to$wrong (harmful), WC = wrong$\to$correct (helpful), WW = wrong$\to$wrong. Baseline: \textsc{Parametric-Only}.}",
        r"\label{tab:flips}",
        r"\small",
        r"\begin{tabular}{l cccc cccc}",
        r"\toprule",
        r"& \multicolumn{4}{c}{Gemma ($N$=88)} & \multicolumn{4}{c}{Llama ($N$=100)} \\",
        r"\cmidrule(lr){2-5} \cmidrule(lr){6-9}",
        r"Condition & CC & CW & WC & WW & CC & CW & WC & WW \\",
        r"\midrule",
    ]

    flips = {}
    for ds_file, model in [
        (RAW / "scifact_LOCKED_gemma3_27b-it-qat.jsonl", "gemma"),
        (RAW / "scifact_TRANSFER_llama3.2-vision_11b-instruct-q8_0.jsonl", "llama"),
    ]:
        results = []
        with open(ds_file) as f:
            for line in f:
                results.append(json.loads(line))
        for cond in ["REAL", "SHUFFLED", "NEUTRAL", "DIRECT", "GENERIC_EXPANSION", "REAL_ARTIFACT_HIDDEN"]:
            if cond not in results[0]:
                continue
            cc = cw = wc = ww = 0
            for r in results:
                pc = r["PARAMETRIC_ONLY"]["correct"]
                cc2 = r[cond]["correct"]
                if pc and cc2: cc += 1
                elif pc and not cc2: cw += 1
                elif not pc and cc2: wc += 1
                else: ww += 1
            flips[(model, cond)] = (cc, cw, wc, ww)

    cond_labels = {
        "REAL": r"\textsc{Real}",
        "SHUFFLED": r"\textsc{Shuffled}",
        "NEUTRAL": r"\textsc{Neutral}",
        "DIRECT": r"\textsc{Direct}",
        "GENERIC_EXPANSION": r"\textsc{Generic}",
        "REAL_ARTIFACT_HIDDEN": r"\textsc{Real-Hidden}",
    }

    for cond in ["REAL", "SHUFFLED", "NEUTRAL", "DIRECT", "GENERIC_EXPANSION", "REAL_ARTIFACT_HIDDEN"]:
        g = flips.get(("gemma", cond), ("--","--","--","--"))
        l = flips.get(("llama", cond), ("--","--","--","--"))
        lines.append(f"{cond_labels[cond]} & {g[0]} & {g[1]} & {g[2]} & {g[3]} & {l[0]} & {l[1]} & {l[2]} & {l[3]} \\\\")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])
    return "\n".join(lines)


def main():
    t1 = table1_condition_summary()
    t2 = table2_primary_effects()
    t3 = table3_answer_flips()

    with open(TABLES / "table1_conditions.tex", "w") as f:
        f.write(t1)
    print(f"Wrote: {TABLES / 'table1_conditions.tex'}")

    with open(TABLES / "table2_effects.tex", "w") as f:
        f.write(t2)
    print(f"Wrote: {TABLES / 'table2_effects.tex'}")

    with open(TABLES / "table3_flips.tex", "w") as f:
        f.write(t3)
    print(f"Wrote: {TABLES / 'table3_flips.tex'}")

    print("\n--- TABLE 1 ---")
    print(t1)
    print("\n--- TABLE 2 ---")
    print(t2)
    print("\n--- TABLE 3 ---")
    print(t3)


if __name__ == "__main__":
    main()
