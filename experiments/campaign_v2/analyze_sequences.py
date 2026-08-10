"""Quick analysis of operator sequences from Campaign V2."""
import json
from collections import Counter
from pathlib import Path

records = [json.loads(l) for l in open(Path(__file__).parent / "results" / "all_records.jsonl")]

full_ree = [r for r in records if r["architecture"] == "full_ree" and r.get("budget_tokens") == 5000]
b1 = [r for r in records if r["architecture"] == "B1_reflection"][:10]

print("=== full_ree operator sequences (first 10) ===")
for r in full_ree[:10]:
    wid = r["world_id"]
    q = r["scalar_quality"]
    hyps = r["hypothesis_count"]
    ign = r["ignorance_count"]
    ev = r["evidence_count"]
    ops = r["operator_sequence"]
    print(f"  {wid:35s} q={q:.3f} h={hyps} i={ign} e={ev} ops={ops}")

print(f"\nfull_ree op distribution:")
all_ops = []
for r in full_ree:
    all_ops.extend(r["operator_sequence"])
for op, count in Counter(all_ops).most_common():
    print(f"  {op}: {count}")

print(f"\n=== B1 sequences (first 5) ===")
for r in b1[:5]:
    wid = r["world_id"]
    q = r["scalar_quality"]
    hyps = r["hypothesis_count"]
    ev = r["evidence_count"]
    ops = r["operator_sequence"]
    print(f"  {wid:35s} q={q:.3f} h={hyps} e={ev} ops={ops}")

# Compute per-family results
from collections import defaultdict
by_family = defaultdict(lambda: defaultdict(list))
for r in records:
    parts = r["world_id"].split("_")
    family = "_".join(parts[:-2]) if len(parts) > 2 else parts[0]
    by_family[family][r["architecture"]].append(r["scalar_quality"])

print("\n=== Per-family quality means ===")
for family in sorted(by_family.keys()):
    archs = by_family[family]
    print(f"\n  {family}:")
    for arch in sorted(archs.keys()):
        scores = archs[arch]
        mean = sum(scores) / len(scores)
        print(f"    {arch:20s}: {mean:.4f} (n={len(scores)})")
