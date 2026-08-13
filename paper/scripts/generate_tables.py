"""Generate final LaTeX tables from paper data CSVs."""
import csv
import json
from pathlib import Path

PAPER_DATA = Path(__file__).resolve().parent.parent / "data"
PAPER_TABLES = Path(__file__).resolve().parent.parent / "tables"
PAPER_TABLES.mkdir(parents=True, exist_ok=True)
DERIVED = Path(__file__).resolve().parent.parent.parent / "experiments" / "paper_validation" / "results" / "derived"


def table1_conditions():
    """Table 1: Performance across conditions."""
    rows = list(csv.DictReader(open(PAPER_DATA / "final_model_transfer.csv")))

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Performance across conditions. Retrieval = gold evidence recall. Task = accuracy (SciFact) or F1 (HotpotQA). $N$: SciFact--Gemma = 88 unseen, SciFact--Llama = 100, HotpotQA--Gemma = 300 unseen, HotpotQA--Llama = 100.}",
        r"\label{tab:conditions}",
        r"\small",
        r"\begin{tabular}{lcccccccc}",
        r"\toprule",
        r"& \multicolumn{2}{c}{SciFact$\times$Gemma} & \multicolumn{2}{c}{SciFact$\times$Llama} & \multicolumn{2}{c}{HotpotQA$\times$Gemma} & \multicolumn{2}{c}{HotpotQA$\times$Llama} \\",
        r"\cmidrule(lr){2-3} \cmidrule(lr){4-5} \cmidrule(lr){6-7} \cmidrule(lr){8-9}",
        r"Condition & Retr. & Task & Retr. & Task & Retr. & Task & Retr. & Task \\",
        r"\midrule",
    ]

    cond_order = ["DIRECT", "NEUTRAL", "GENERIC_EXPANSION", "REAL", "SHUFFLED"]
    cond_tex = {"DIRECT": r"\textsc{Direct}", "NEUTRAL": r"\textsc{Neutral}",
                "GENERIC_EXPANSION": r"\textsc{Generic}", "REAL": r"\textsc{Real}",
                "SHUFFLED": r"\textsc{Shuffled}"}
    ds_model_order = [("SciFact", "Gemma"), ("SciFact", "Llama"), ("HotpotQA", "Gemma"), ("HotpotQA", "Llama")]

    lookup = {}
    for r in rows:
        lookup[(r["dataset"], r["model"], r["condition"])] = r

    for cond in cond_order:
        cells = []
        for ds, mod in ds_model_order:
            key = (ds, mod, cond)
            if key in lookup:
                cells.append(f"{float(lookup[key]['retrieval']):.3f} & {float(lookup[key]['task']):.3f}")
            else:
                cells.append("-- & --")
        lines.append(f"{cond_tex[cond]} & " + " & ".join(cells) + r" \\")

    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    out = PAPER_TABLES / "table1_conditions.tex"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"  Wrote: {out}")


def table2_setup():
    """Table 2: Experimental setup / resource usage."""
    rows = list(csv.DictReader(open(PAPER_DATA / "final_resource_usage.csv")))

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Condition design and resource budget. All retrieval-based conditions use the same model, retriever (BM25), and top-$k$=5.}",
        r"\label{tab:setup}",
        r"\small",
        r"\begin{tabular}{lccccc}",
        r"\toprule",
        r"Condition & Artifact & Query & Answer & Retrieval & Total Calls \\",
        r"\midrule",
    ]

    cond_tex = {"DIRECT": r"\textsc{Direct}", "NEUTRAL": r"\textsc{Neutral}",
                "GENERIC_EXPANSION": r"\textsc{Generic}", "REAL": r"\textsc{Real}",
                "SHUFFLED": r"\textsc{Shuffled}", "PARAMETRIC_ONLY": r"\textsc{Parametric}",
                "REAL_ARTIFACT_HIDDEN": r"\textsc{Real-Hidden}"}

    for r in rows:
        cond = cond_tex.get(r["condition"], r["condition"])
        lines.append(f"{cond} & {r['artifact_calls']} & {r['query_calls']} & {r['answer_calls']} & {r['retrieval_calls']} & {r['total_calls']} \\\\")

    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    out = PAPER_TABLES / "table2_setup.tex"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"  Wrote: {out}")


def table3_primary_results():
    """Table 3: Primary confirmatory effects with Holm correction."""
    tests = list(csv.DictReader(open(PAPER_DATA / "final_holm_family.csv")))

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Primary confirmatory effects. Paired bootstrap (10{,}000 resamples) with Holm correction over 14 simultaneous tests. Bold = significant at $\alpha=0.05$.}",
        r"\label{tab:effects}",
        r"\small",
        r"\begin{tabular}{llllrccl}",
        r"\toprule",
        r"Hyp. & Dataset & Model & Metric & \multicolumn{1}{c}{$\hat{\Delta}$} & 95\% CI & $p_\text{Holm}$ & $N$ \\",
        r"\midrule",
    ]

    for t in tests:
        eff = float(t["estimate"])
        reject = t["reject"] == "True"
        eff_str = f"{eff:+.3f}"
        if reject:
            eff_str = r"\textbf{" + eff_str + "}"
        ci = f"[{float(t['ci_lo']):+.3f}, {float(t['ci_hi']):+.3f}]"
        p_holm = float(t["p_holm"])
        p_str = f"{p_holm:.4f}" if p_holm >= 0.001 else "<.001"
        if reject:
            p_str = r"\textbf{" + p_str + "}"
        lines.append(f"{t['hypothesis']} & {t['dataset']} & {t['model']} & {t['metric']} & {eff_str} & {ci} & {p_str} & {t['n']} \\\\")

    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    out = PAPER_TABLES / "table3_primary_results.tex"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"  Wrote: {out}")


def table4_scifact_mechanism():
    """Table 4: SciFact answer flip analysis."""
    rows = list(csv.DictReader(open(PAPER_DATA / "final_scifact_decomposition.csv")))

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{SciFact answer flip analysis. CC = correct$\to$correct, CW = correct$\to$wrong (harmful), WC = wrong$\to$correct (helpful), WW = wrong$\to$wrong. Baseline: \textsc{Parametric-Only}.}",
        r"\label{tab:flips}",
        r"\small",
        r"\begin{tabular}{llrrrrrr}",
        r"\toprule",
        r"Model & Condition & Acc. & Recall & CC & CW & WC & WW \\",
        r"\midrule",
    ]

    cond_tex = {"REAL": r"\textsc{Real}", "SHUFFLED": r"\textsc{Shuffled}",
                "NEUTRAL": r"\textsc{Neutral}", "DIRECT": r"\textsc{Direct}",
                "GENERIC_EXPANSION": r"\textsc{Generic}", "REAL_ARTIFACT_HIDDEN": r"\textsc{Real-Hid.}"}

    for r in rows:
        cond = cond_tex.get(r["condition"], r["condition"])
        lines.append(f"{r['model']} & {cond} & {float(r['accuracy']):.3f} & {float(r['recall']):.3f} & {r['CC']} & {r['CW']} & {r['WC']} & {r['WW']} \\\\")

    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    out = PAPER_TABLES / "table4_scifact_mechanism.tex"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"  Wrote: {out}")


def table5_claim_boundary():
    """Table 5: What the paper claims and does not claim."""
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Claim boundaries. Each finding is classified by evidence strength.}",
        r"\label{tab:claims}",
        r"\small",
        r"\begin{tabular}{lll}",
        r"\toprule",
        r"Finding & Evidence & Status \\",
        r"\midrule",
        r"Semantic artifacts improve retrieval & 4/4 cells sig. & \textbf{Supported} \\",
        r"Hypothesis specificity helps retrieval & 0/4 cells sig. & Not supported \\",
        r"Retrieval--reasoning dissociation & 3/4 cells sig. & \textbf{Supported} \\",
        r"Cross-model qualitative replication & All directions match & \textbf{Supported} \\",
        r"Direct hypothesis anchoring & 0/2 cells sig. & Not supported \\",
        r"Evidence integration bottleneck & Consistent with flips & Characterized \\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    out = PAPER_TABLES / "table5_claim_boundary.tex"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"  Wrote: {out}")


def main():
    print("Generating paper tables...")
    table1_conditions()
    table2_setup()
    table3_primary_results()
    table4_scifact_mechanism()
    table5_claim_boundary()
    print("Done.")


if __name__ == "__main__":
    main()
