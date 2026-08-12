"""Power analysis from V6 variance."""
import json, statistics, math

def power_n(sd, sesoi, alpha=0.05, power=0.80):
    z_a = 1.96
    z_b = 0.842
    return math.ceil(((z_a + z_b) * sd / sesoi) ** 2)

sf = []
with open("experiments/campaign_v6/results/scifact_gemma3_27b-it-qat.jsonl") as f:
    for line in f:
        sf.append(json.loads(line))

hp = []
with open("experiments/campaign_v6/results/hotpotqa_gemma3_27b-it-qat.jsonl") as f:
    for line in f:
        hp.append(json.loads(line))

results = {}

# SciFact
sf_recall_diff = [r["REAL"]["gold_recall"] - r["SHUFFLED"]["gold_recall"] for r in sf]
sf_acc_diff = [(1 if r["REAL"]["correct"] else 0) - (1 if r["SHUFFLED"]["correct"] else 0) for r in sf]
sf_gen_diff = [r["REAL"]["gold_recall"] - r["GENERIC_EXPANSION"]["gold_recall"] for r in sf]

results["scifact"] = {
    "real_vs_shuffled_recall": {
        "observed_effect": round(statistics.mean(sf_recall_diff), 4),
        "sd_paired": round(statistics.stdev(sf_recall_diff), 4),
        "sesoi": 0.06,
        "required_n_80pct": power_n(statistics.stdev(sf_recall_diff), 0.06),
        "available_unseen": 88,
    },
    "real_vs_shuffled_accuracy": {
        "observed_effect": round(statistics.mean(sf_acc_diff), 4),
        "sd_paired": round(statistics.stdev(sf_acc_diff), 4),
        "sesoi": 0.08,
        "required_n_80pct": power_n(statistics.stdev(sf_acc_diff), 0.08),
        "available_unseen": 88,
    },
    "real_vs_generic_recall": {
        "observed_effect": round(statistics.mean(sf_gen_diff), 4),
        "sd_paired": round(statistics.stdev(sf_gen_diff), 4),
        "sesoi": 0.04,
        "required_n_80pct": power_n(statistics.stdev(sf_gen_diff), 0.04),
        "available_unseen": 88,
    },
}

# HotpotQA
hp_recall_diff = [r["REAL"]["gold_recall"] - r["SHUFFLED"]["gold_recall"] for r in hp]
hp_f1_diff = [r["REAL"]["f1"] - r["SHUFFLED"]["f1"] for r in hp]
hp_gen_diff = [r["REAL"]["gold_recall"] - r["GENERIC_EXPANSION"]["gold_recall"] for r in hp]

results["hotpotqa"] = {
    "real_vs_shuffled_recall": {
        "observed_effect": round(statistics.mean(hp_recall_diff), 4),
        "sd_paired": round(statistics.stdev(hp_recall_diff), 4),
        "sesoi": 0.06,
        "required_n_80pct": power_n(statistics.stdev(hp_recall_diff), 0.06),
        "available_unseen": 7305,
    },
    "real_vs_shuffled_f1": {
        "observed_effect": round(statistics.mean(hp_f1_diff), 4),
        "sd_paired": round(statistics.stdev(hp_f1_diff), 4),
        "sesoi": 0.05,
        "required_n_80pct": power_n(statistics.stdev(hp_f1_diff), 0.05),
        "available_unseen": 7305,
    },
    "real_vs_generic_recall": {
        "observed_effect": round(statistics.mean(hp_gen_diff), 4),
        "sd_paired": round(statistics.stdev(hp_gen_diff), 4),
        "sesoi": 0.04,
        "required_n_80pct": power_n(statistics.stdev(hp_gen_diff), 0.04),
        "available_unseen": 7305,
    },
}

for ds, tests in results.items():
    print(f"\n{ds}:")
    for name, t in tests.items():
        eff = t["observed_effect"]
        sd = t["sd_paired"]
        sesoi = t["sesoi"]
        n_req = t["required_n_80pct"]
        avail = t["available_unseen"]
        sufficient = "YES" if avail >= n_req else "NO"
        print(f"  {name}: effect={eff:.4f} SD={sd} SESOI={sesoi} N_req={n_req} avail={avail} sufficient={sufficient}")

with open("experiments/paper_validation/POWER_ANALYSIS.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nWritten POWER_ANALYSIS.json")
