#!/usr/bin/env python3
"""Recompute reported metrics from saved scores and independently replay proofs."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.rules import load_rules
from panini.candidates import enumerate_candidates, gold_indices
from panini.experiment_data import digest
from panini.ranking import metrics


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--rules", type=Path, default=ROOT / "data/rules/development_sandhi.jsonl")
    args = p.parse_args()
    results = json.loads((args.run / "results.json").read_text())
    manifest = results["data_manifest"]
    if manifest["rules_sha256"] != digest(args.rules.read_text()):
        raise ValueError("rule snapshot mismatch")
    rules, cache = load_rules(args.rules), {}
    for entry in results["results"]:
        split = entry["split"]
        if split not in cache:
            for name in ("train", "dev", "test"):
                path = args.data / split / f"{name}.jsonl"
                if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["splits"][split]["file_sha256"][name]:
                    raise ValueError("frozen dataset hash mismatch")
            cache[split] = [json.loads(line) for line in (args.data / split / "test.jsonl").read_text().splitlines()]
            for row in cache[split]:
                candidates = enumerate_candidates(row["surface"], rules, row["tags"])
                if json.loads(json.dumps(candidates)) != row["candidates"]:
                    raise ValueError("candidate forward replay mismatch")
                if gold_indices(row, candidates) != row["gold_indices"]:
                    raise ValueError("gold candidate index mismatch")
        path = args.run / f"{split}-{entry['model']}-{entry['seed']}-predictions.jsonl"
        predictions = [json.loads(line) for line in path.read_text().splitlines()]
        if [r["example_id"] for r in cache[split]] != [r["example_id"] for r in predictions]:
            raise ValueError("prediction identity/order mismatch")
        scores = [r["scores"] for r in predictions]
        for key in ("test", "selective_test"):
            observed, _ = metrics(cache[split], scores, entry[key]["threshold"])
            if observed != entry[key]:
                raise ValueError(f"saved metrics mismatch: {split}/{entry['model']}/{key}")
    print(f"Verified {len(results['results'])} evaluations from saved scores; replayed all {sum(map(len, cache.values()))} test candidate sets.")


if __name__ == "__main__":
    main()
