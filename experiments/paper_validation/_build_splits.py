"""Build frozen task splits for paper validation."""
import hashlib
import json
from pathlib import Path

SPLITS_DIR = Path("experiments/paper_validation/splits")

# === SCIFACT ===
claims = []
with open("experiments/campaign_v6/data/scifact/claims_dev.jsonl") as f:
    for line in f:
        c = json.loads(line)
        gold_docs = {}
        if c.get("evidence"):
            for doc_id_str, sents in c["evidence"].items():
                gold_docs[doc_id_str] = sents
        if gold_docs:
            claims.append({
                "id": c["id"],
                "claim": c["claim"],
                "label": c.get("label", "NOT_ENOUGH_INFO"),
                "gold_doc_ids": list(gold_docs.keys()),
                "gold_evidence": gold_docs,
            })

# V6 seen = first 100
v6_seen_ids = set(c["id"] for c in claims[:100])
unseen = [c for c in claims if c["id"] not in v6_seen_ids]
seen = [c for c in claims if c["id"] in v6_seen_ids]

sf_split = {
    "dataset": "scifact",
    "source": "allenai/scifact dev split",
    "total_evaluable": len(claims),
    "v6_seen": len(seen),
    "unseen": len(unseen),
    "locked_confirmatory": [c["id"] for c in unseen],
    "same_task_transfer": [c["id"] for c in seen],
    "locked_n": len(unseen),
    "same_task_n": len(seen),
    "split_hash": hashlib.sha256(
        json.dumps([c["id"] for c in unseen], sort_keys=True).encode()
    ).hexdigest()[:16],
    "power_note": "Underpowered for small effects (N=88 < 239 required). "
                  "Report CI width honestly. Consider pooling with same-task "
                  "transfer for secondary analysis.",
}
with open(SPLITS_DIR / "scifact_locked.json", "w") as f:
    json.dump(sf_split, f, indent=2)
print(f"SciFact: {sf_split['locked_n']} locked, {sf_split['same_task_n']} same-task, hash={sf_split['split_hash']}")

# === HOTPOTQA ===
with open("experiments/campaign_v6/data/hotpotqa/hotpot_dev_distractor.json") as f:
    hotpot_all = json.load(f)

v6_hp_seen = set()
with open("experiments/campaign_v6/results/hotpotqa_gemma3_27b-it-qat.jsonl") as f:
    for line in f:
        r = json.loads(line)
        v6_hp_seen.add(r["task_id"])

# Select 300 unseen tasks (101-400 in dev set)
unseen_hp = [h for h in hotpot_all if h["_id"] not in v6_hp_seen]
locked_hp = unseen_hp[:300]
seen_hp = [h for h in hotpot_all if h["_id"] in v6_hp_seen]

hp_split = {
    "dataset": "hotpotqa",
    "source": "hotpot_dev_distractor_v1.json (Wayback archive)",
    "total_dev": len(hotpot_all),
    "v6_seen": len(v6_hp_seen),
    "unseen": len(unseen_hp),
    "locked_confirmatory": [h["_id"] for h in locked_hp],
    "same_task_transfer": [h["_id"] for h in seen_hp],
    "locked_n": len(locked_hp),
    "same_task_n": len(seen_hp),
    "split_hash": hashlib.sha256(
        json.dumps([h["_id"] for h in locked_hp], sort_keys=True).encode()
    ).hexdigest()[:16],
}
with open(SPLITS_DIR / "hotpotqa_locked.json", "w") as f:
    json.dump(hp_split, f, indent=2)
print(f"HotpotQA: {hp_split['locked_n']} locked, {hp_split['same_task_n']} same-task, hash={hp_split['split_hash']}")

print("\nDone. Splits frozen.")
