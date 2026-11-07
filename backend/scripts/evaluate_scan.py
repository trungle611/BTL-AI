"""Evaluate frozen test predictions. No API calls or prompt tuning here.

CSV columns: image_id,ground_truth_food_id,split,candidate_1,candidate_2,candidate_3,
status,latency_ms. Empty ground truth denotes an out-of-catalog image.
"""
import argparse
import csv
import json
import statistics


def evaluate(path, split="test"):
    with open(path, encoding="utf-8-sig", newline="") as file:
        rows = [r for r in csv.DictReader(file) if r["split"] == split]
    known = [r for r in rows if r["ground_truth_food_id"]]
    unknown = [r for r in rows if not r["ground_truth_food_id"]]
    def ratio(n, d):
        return round(n / d, 4) if d else None
    latencies = sorted(float(r["latency_ms"]) for r in rows if r.get("latency_ms"))
    def percentile(p):
        if not latencies:
            return None
        index = (len(latencies) - 1) * p
        low = int(index)
        high = min(low + 1, len(latencies) - 1)
        return round(latencies[low] + (latencies[high] - latencies[low]) * (index - low), 1)
    return {
        "split": split, "n_total": len(rows), "n_known": len(known), "n_unknown": len(unknown),
        "top1": ratio(sum(r["candidate_1"] == r["ground_truth_food_id"] for r in known), len(known)),
        "top3": ratio(sum(r["ground_truth_food_id"] in [r[f"candidate_{i}"] for i in (1,2,3)] for r in known), len(known)),
        "unknown_handling": ratio(sum(r["status"] == "unknown" for r in unknown), len(unknown)),
        "latency_p50_ms": percentile(0.5), "latency_p95_ms": percentile(0.95),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("predictions_csv")
    parser.add_argument("--split", default="test")
    args = parser.parse_args()
    print(json.dumps(evaluate(args.predictions_csv, args.split), ensure_ascii=False, indent=2))
