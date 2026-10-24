#!/usr/bin/env python3
"""Paired test-set comparison of seeded rankers against one baseline, from saved predictions."""

import argparse
import json
import math
import random
from pathlib import Path


def load(path):
    return {r["example_id"]: r["correct"] for r in map(json.loads, path.open(encoding="utf-8"))}


def exact_mcnemar(wins, losses):
    n, k = wins + losses, min(wins, losses)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--split", default="strict_right_lemma")
    p.add_argument("--baseline", default="frequency_short_vowel")
    p.add_argument("--models", nargs="+", default=["tiny_full", "tiny_no_rules", "tiny_no_context"])
    p.add_argument("--seeds", nargs="+", type=int, default=[7, 11, 19, 23, 29])
    p.add_argument("--bootstrap", type=int, default=5000)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()
    base = load(args.run / f"{args.split}-{args.baseline}-None-predictions.jsonl")
    ids = sorted(base)
    report = {"split": args.split, "baseline": args.baseline, "examples": len(ids),
              "baseline_top1": sum(base.values()) / len(ids), "models": {},
              "note": "Itemwise paired bootstrap over test examples of the seed-mean accuracy difference; "
                      "exact McNemar per seed. Baseline correctness uses index tie-breaking."}
    for model in args.models:
        runs = [load(args.run / f"{args.split}-{model}-{s}-predictions.jsonl") for s in args.seeds]
        if any(set(r) != set(ids) for r in runs):
            raise SystemExit(f"{model}: prediction ids differ from the baseline")
        per_seed = []
        for seed, run in zip(args.seeds, runs):
            wins = sum(run[i] and not base[i] for i in ids)
            losses = sum(base[i] and not run[i] for i in ids)
            per_seed.append({"seed": seed, "top1": sum(run.values()) / len(ids), "wins": wins, "losses": losses,
                             "mcnemar_p": exact_mcnemar(wins, losses)})
        diff = [sum(r[i] for r in runs) / len(runs) - base[i] for i in ids]
        rng = random.Random(args.seed)
        boots = sorted(sum(diff[rng.randrange(len(ids))] for _ in ids) / len(ids) for _ in range(args.bootstrap))
        report["models"][model] = {"mean_difference": sum(diff) / len(ids),
                                   "ci95": [boots[int(0.025 * args.bootstrap)], boots[int(0.975 * args.bootstrap) - 1]],
                                   "per_seed": per_seed}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
