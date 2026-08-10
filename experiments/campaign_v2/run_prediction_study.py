"""
Phase 15 — Can Epistemic State Predict Best Cognitive Action?

Uses counterfactual data to build transparent action-value models.
Tests whether rich epistemic state features outperform simple counts.
Split by scenario family (not random rows) to prevent leakage.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

RESULTS_DIR = Path(__file__).parent / "results"


def load_data():
    records = []
    for line in open(RESULTS_DIR / "counterfactual_v2.jsonl"):
        records.append(json.loads(line))
    return records


def extract_features(record: dict) -> dict:
    """Extract state feature vectors from counterfactual record."""
    return {
        "hypothesis_entropy": record.get("hypothesis_entropy", 0),
        "top_margin": record.get("top_margin", 0),
        "budget_fraction": record.get("budget_fraction", 1),
        "contradiction_density": record.get("contradiction_density", 0),
        "ignorance_priority": record.get("ignorance_priority", 0),
        "workspace_saturation": record.get("workspace_saturation", 0),
        "hypothesis_count": record.get("hypothesis_count", 0),
        "evidence_count": record.get("evidence_count", 0),
        "ignorance_count": record.get("ignorance_count", 0),
        "step": record.get("step", 0),
    }


def extract_minimal_features(record: dict) -> dict:
    """Minimal count-only features."""
    return {
        "evidence_count": record.get("evidence_count", 0),
        "hypothesis_count": record.get("hypothesis_count", 0),
        "step": record.get("step", 0),
        "budget_fraction": record.get("budget_fraction", 1),
    }


def compute_best_actions(records: list[dict]) -> dict[str, str]:
    """For each source state, determine the best action."""
    by_state = defaultdict(list)
    for r in records:
        by_state[r["source_state_id"]].append(r)

    best_actions = {}
    for state_id, outcomes in by_state.items():
        best = max(outcomes, key=lambda o: o["realized_quality"])
        best_actions[state_id] = best["forced_action"]
    return best_actions


def majority_baseline(train_best: dict[str, str]) -> str:
    """Return the most common best action in training data."""
    counter = Counter(train_best.values())
    return counter.most_common(1)[0][0]


def family_specific_baseline(
    records: list[dict],
    test_family: str,
) -> str:
    """For the given family, find the best action by mean quality."""
    by_action = defaultdict(list)
    for r in records:
        if r["family"] != test_family:
            by_action[r["forced_action"]].append(r["realized_quality"])
    if not by_action:
        return "retrieve"
    return max(by_action, key=lambda a: statistics.mean(by_action[a]))


def simple_rule_policy(features: dict) -> str:
    """Interpretable rule-based policy from state features."""
    if features.get("evidence_count", 0) == 0:
        return "retrieve"
    if features.get("hypothesis_count", 0) < 2 and features.get("evidence_count", 0) >= 1:
        return "generate_hypothesis"
    if features.get("hypothesis_count", 0) >= 2 and features.get("evidence_count", 0) >= 2:
        return "reason"
    return "retrieve"


def evaluate_policy(
    policy_fn,
    test_records: list[dict],
    best_actions: dict[str, str],
) -> dict:
    """Evaluate a policy against best-action oracle on test data."""
    correct = 0
    total = 0
    regrets = []

    by_state = defaultdict(list)
    for r in test_records:
        by_state[r["source_state_id"]].append(r)

    for state_id, outcomes in by_state.items():
        if state_id not in best_actions:
            continue

        oracle_action = best_actions[state_id]
        features = extract_features(outcomes[0])
        predicted = policy_fn(features)

        total += 1
        if predicted == oracle_action:
            correct += 1

        oracle_quality = max(o["realized_quality"] for o in outcomes)
        predicted_quality = 0.0
        for o in outcomes:
            if o["forced_action"] == predicted:
                predicted_quality = o["realized_quality"]
                break

        regrets.append(oracle_quality - predicted_quality)

    accuracy = correct / total if total > 0 else 0
    mean_regret = statistics.mean(regrets) if regrets else 0

    return {
        "accuracy": round(accuracy, 4),
        "mean_regret": round(mean_regret, 4),
        "n": total,
    }


def main():
    print("=" * 60)
    print("PHASE 15 - ACTION VALUE PREDICTION STUDY")
    print("=" * 60)

    records = load_data()
    families = list(set(r["family"] for r in records))

    best_actions = compute_best_actions(records)
    print(f"\nTotal records: {len(records)}")
    print(f"Distinct states: {len(best_actions)}")
    print(f"Families: {families}")

    # Best action distribution
    print("\n--- ORACLE BEST ACTION DISTRIBUTION ---")
    action_dist = Counter(best_actions.values())
    for action, count in action_dist.most_common():
        print(f"  {action:25s}: {count} ({count/len(best_actions)*100:.1f}%)")

    # Leave-one-family-out cross-validation
    print("\n--- LEAVE-ONE-FAMILY-OUT EVALUATION ---")

    policies = {
        "majority_baseline": None,
        "family_baseline": None,
        "simple_rule": lambda f: simple_rule_policy(f),
        "always_retrieve": lambda f: "retrieve",
        "always_reason": lambda f: "reason",
        "always_gen_hyp": lambda f: "generate_hypothesis",
        "always_stop": lambda f: "stop",
    }

    all_results = defaultdict(list)

    for test_family in families:
        train_records = [r for r in records if r["family"] != test_family]
        test_records = [r for r in records if r["family"] == test_family]
        test_best = {k: v for k, v in best_actions.items()
                     if any(r["source_state_id"] == k and r["family"] == test_family for r in test_records)}
        train_best = {k: v for k, v in best_actions.items() if k not in test_best}

        maj_action = majority_baseline(train_best)
        fam_action = family_specific_baseline(train_records, test_family)

        for policy_name, policy_fn in policies.items():
            if policy_name == "majority_baseline":
                fn = lambda f, a=maj_action: a
            elif policy_name == "family_baseline":
                fn = lambda f, a=fam_action: a
            else:
                fn = policy_fn

            result = evaluate_policy(fn, test_records, test_best)
            all_results[policy_name].append(result)

    print(f"\n{'Policy':25s} {'Accuracy':>10s} {'Regret':>10s} {'N':>6s}")
    print("-" * 55)
    for policy_name in policies:
        results = all_results[policy_name]
        accs = [r["accuracy"] for r in results]
        regs = [r["mean_regret"] for r in results]
        ns = [r["n"] for r in results]
        mean_acc = statistics.mean(accs) if accs else 0
        mean_reg = statistics.mean(regs) if regs else 0
        total_n = sum(ns)
        print(f"  {policy_name:25s} {mean_acc:9.4f} {mean_reg:10.4f} {total_n:6d}")

    # Feature importance analysis
    print("\n--- FEATURE IMPORTANCE (correlation with best-action accuracy) ---")
    feature_names = ["hypothesis_entropy", "top_margin", "budget_fraction",
                     "contradiction_density", "ignorance_priority", "workspace_saturation",
                     "evidence_count", "hypothesis_count", "step"]

    by_state = defaultdict(list)
    for r in records:
        by_state[r["source_state_id"]].append(r)

    for feat_name in feature_names:
        feat_vals = []
        rule_correct = []
        for state_id, outcomes in by_state.items():
            if state_id not in best_actions:
                continue
            features = extract_features(outcomes[0])
            predicted = simple_rule_policy(features)
            oracle = best_actions[state_id]
            feat_vals.append(features.get(feat_name, 0))
            rule_correct.append(1.0 if predicted == oracle else 0.0)

        if len(set(feat_vals)) > 1 and len(feat_vals) > 2:
            n = len(feat_vals)
            mf = sum(feat_vals) / n
            mc = sum(rule_correct) / n
            cov = sum((f - mf) * (c - mc) for f, c in zip(feat_vals, rule_correct)) / n
            sf = (sum((f - mf) ** 2 for f in feat_vals) / n) ** 0.5
            sc = (sum((c - mc) ** 2 for c in rule_correct) / n) ** 0.5
            corr = cov / (sf * sc) if sf > 0 and sc > 0 else 0
            print(f"  {feat_name:25s}: r = {corr:+.4f}")

    # Save results
    summary = {
        "total_records": len(records),
        "distinct_states": len(best_actions),
        "families": families,
        "best_action_distribution": dict(action_dist),
        "policy_results": {
            name: {
                "mean_accuracy": round(statistics.mean([r["accuracy"] for r in results]), 4),
                "mean_regret": round(statistics.mean([r["mean_regret"] for r in results]), 4),
            }
            for name, results in all_results.items()
        },
    }
    (RESULTS_DIR / "prediction_study_v2.json").write_text(json.dumps(summary, indent=2))
    print(f"\nResults saved to {RESULTS_DIR / 'prediction_study_v2.json'}")


if __name__ == "__main__":
    main()
