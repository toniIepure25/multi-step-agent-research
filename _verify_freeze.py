"""Part 1: Freeze verification — validate all hashes, registries, and replay statistics."""
import json, hashlib, os, random, statistics
from pathlib import Path

RAW = Path("experiments/paper_validation/results/raw")
DERIVED = Path("experiments/paper_validation/results/derived")

def sha256_file(fp):
    return hashlib.sha256(open(fp, "rb").read()).hexdigest()[:16]

print("=" * 70)
print("PART 1 — FREEZE VERIFICATION")
print("=" * 70)

# 1. Raw traces
print("\n[1] RAW TRACE VERIFICATION")
expected = {
    "scifact_LOCKED_gemma3_27b-it-qat.jsonl": 88,
    "scifact_TRANSFER_llama3.2-vision_11b-instruct-q8_0.jsonl": 100,
    "hotpotqa_LOCKED_gemma3_27b-it-qat.jsonl": 300,
    "hotpotqa_TRANSFER_llama3.2-vision_11b-instruct-q8_0.jsonl": 100,
}
for fname, exp_n in expected.items():
    fp = RAW / fname
    n = sum(1 for _ in open(fp))
    h = sha256_file(fp)
    status = "PASS" if n == exp_n else "FAIL"
    print(f"  [{status}] {fname}: N={n} (expected {exp_n})  SHA256={h}")

# 2. Artifact files
print("\n[2] ARTIFACT FILES")
for fname in sorted(os.listdir(RAW)):
    if fname.endswith(".json"):
        fp = RAW / fname
        d = json.load(open(fp))
        print(f"  {fname}: {len(d)} entries  SHA256={sha256_file(fp)}")

# 3. Preregistration
print("\n[3] PREREGISTRATION INTEGRITY")
for f in ["PREREGISTRATION.md", "PREREGISTRATION.json"]:
    fp = Path("experiments/paper_validation") / f
    print(f"  {f}: SHA256={sha256_file(fp)}")

# 4. Task splits
print("\n[4] TASK SPLIT HASHES")
for f in ["scifact_locked.json", "hotpotqa_locked.json"]:
    fp = Path("experiments/paper_validation/splits") / f
    if fp.exists():
        d = json.load(open(fp))
        print(f"  {f}: SHA256={sha256_file(fp)}  keys={list(d.keys())}")

# 5. Result registry
print("\n[5] RESULT REGISTRY")
reg = json.load(open("experiments/paper_validation/RESULT_REGISTRY.json"))
meta = reg["meta"]
print(f"  preregistration_sha: {meta['preregistration_sha']}")
print(f"  discovery_sha: {meta['discovery_sha']}")
for hid, hval in reg["hypotheses"].items():
    print(f"  {hid} ({hval['name']}): {hval['verdict']}")

# 6. Formal statistics replay
print("\n[6] FORMAL STATISTICS REPLAY")
fs = json.load(open(DERIVED / "formal_statistics.json"))
print(f"  n_tests: {fs['n_tests']}")
print(f"  method: {fs['method']}")
sig = sum(1 for t in fs["tests"] if t["significant_holm"])
print(f"  significant_holm: {sig}/{fs['n_tests']}")

# 7. Independent Holm reconstruction
print("\n[7] INDEPENDENT HOLM RECONSTRUCTION")
raw_ps = [t["p_raw"] for t in fs["tests"]]
n_t = len(raw_ps)
indexed = sorted(enumerate(raw_ps), key=lambda x: x[1])
reconstructed = [0.0] * n_t
prev = 0.0
for rank, (orig_idx, p) in enumerate(indexed):
    adj = p * (n_t - rank)
    adj = max(adj, prev)
    adj = min(adj, 1.0)
    reconstructed[orig_idx] = round(adj, 6)
    prev = adj

mismatches = 0
for i, t in enumerate(fs["tests"]):
    stored = t["p_holm"]
    recon = reconstructed[i]
    match = "PASS" if abs(stored - recon) < 1e-5 else "FAIL"
    if match == "FAIL":
        mismatches += 1
        print(f"  [FAIL] {t['id']}: stored={stored} reconstructed={recon}")

if mismatches == 0:
    print(f"  [PASS] All {n_t} Holm p-values reconstruct correctly")

# 8. Regenerate primary effects independently
print("\n[8] INDEPENDENT PRIMARY EFFECT VERIFICATION")
random.seed(42)

def bootstrap_mean(diffs, n_boot=10000):
    n = len(diffs)
    means = []
    for _ in range(n_boot):
        sample = [diffs[random.randint(0, n - 1)] for _ in range(n)]
        means.append(statistics.mean(sample))
    means.sort()
    return statistics.mean(diffs), means[int(0.025*n_boot)], means[int(0.975*n_boot)]

# SciFact Gemma: REAL vs SHUFFLED recall
sf_g = [json.loads(l) for l in open(RAW / "scifact_LOCKED_gemma3_27b-it-qat.jsonl")]
diffs = [r["REAL"]["gold_doc_recall"] - r["SHUFFLED"]["gold_doc_recall"] for r in sf_g]
m, lo, hi = bootstrap_mean(diffs)
print(f"  SF-G REAL vs SHUFFLED recall: {m:+.4f} [{lo:+.4f}, {hi:+.4f}]")

# HotpotQA Gemma: REAL vs SHUFFLED recall
hp_g = [json.loads(l) for l in open(RAW / "hotpotqa_LOCKED_gemma3_27b-it-qat.jsonl")]
diffs = [r["REAL"]["gold_recall"] - r["SHUFFLED"]["gold_recall"] for r in hp_g]
m, lo, hi = bootstrap_mean(diffs)
print(f"  HP-G REAL vs SHUFFLED recall: {m:+.4f} [{lo:+.4f}, {hi:+.4f}]")

# HotpotQA Gemma: REAL vs SHUFFLED F1
diffs = [r["REAL"]["f1"] - r["SHUFFLED"]["f1"] for r in hp_g]
m, lo, hi = bootstrap_mean(diffs)
print(f"  HP-G REAL vs SHUFFLED F1:     {m:+.4f} [{lo:+.4f}, {hi:+.4f}]")

# SciFact Gemma: REAL vs SHUFFLED accuracy
diffs = [(1 if r["REAL"]["correct"] else 0) - (1 if r["SHUFFLED"]["correct"] else 0) for r in sf_g]
m, lo, hi = bootstrap_mean(diffs)
print(f"  SF-G REAL vs SHUFFLED acc:    {m:+.4f} [{lo:+.4f}, {hi:+.4f}]")

print("\n" + "=" * 70)
print("FREEZE VERIFICATION COMPLETE")
print("=" * 70)
