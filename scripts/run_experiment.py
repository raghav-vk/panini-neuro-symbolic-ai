#!/usr/bin/env python3
"""Run CPU baselines, tiny rankers and ablations on frozen development artifacts."""

import argparse
import hashlib
import json
import platform
import resource
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.ranking import Baseline, metrics, select_threshold, train_neural, predict_neural


CAVEATS = {
    "synthetic_engineering_smoke": (
        "Not evidence of Sanskrit accuracy or contextual understanding.",
        "Coverage is circular on generator-derived probes. Empty synthetic contexts cannot establish contextual gains."),
    "dcs_silver_alignment": (
        "Attested DCS surfaces aligned automatically from DCS lemma annotations; draft rules and silver data are not expert reviewed.",
        "Alignment does not consult the rules, so candidate recall measures rule coverage of the extracted scope only."),
    "reviewed_corpus": (
        "Independently reviewed boundaries; check the data manifest for rule review status.",
        "Candidate recall is measured against reviewed gold analyses."),
}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", type=Path, default=ROOT / "data/processed/development")
    p.add_argument("--output", type=Path, default=ROOT / "runs/development")
    p.add_argument("--splits", nargs="+", choices=["source_random", "pair", "strict_lemma", "strict_right_lemma"],
                   help="default: every split in the data manifest")
    p.add_argument("--seeds", nargs="+", type=int, default=[7, 11, 19, 23, 29])
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--width", type=int, default=64)
    p.add_argument("--layers", type=int, default=2)
    p.add_argument("--max-length", type=int, default=192)
    p.add_argument("--pooling", choices=["mean", "cls"], default="mean")
    p.add_argument("--mark-boundary", action="store_true", help="add an explicit junction field to model inputs")
    p.add_argument("--lexical", action="store_true", help="add a training-split word/rule count feature head")
    p.add_argument("--train-limit", type=int, help="learning-curve subset; sampled by fixed training-only hash")
    p.add_argument("--baselines-only", action="store_true")
    p.add_argument("--ablations", action="store_true")
    args = p.parse_args()
    if args.epochs < 1 or args.width < 4 or args.width % 4 or args.layers < 1 or (args.train_limit is not None and args.train_limit < 1):
        p.error("invalid training dimensions, epochs, or limit")
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((args.data / "manifest.json").read_text())
    args.splits = args.splits or list(manifest["splits"])
    results = {"data_kind": manifest["data_kind"], "data_manifest": manifest, "configuration": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
               "python": sys.version, "platform": platform.platform(), "device": "cpu", "results": []}
    if not args.baselines_only:
        import torch
        results["torch"] = torch.__version__
    for split in args.splits:
        for name in ("train", "dev", "test"):
            actual = hashlib.sha256((args.data / split / f"{name}.jsonl").read_bytes()).hexdigest()
            expected = manifest["splits"][split].get("file_sha256", {}).get(name)
            if actual != expected:
                raise ValueError(f"{split}/{name}: frozen data hash mismatch; prepare a new dataset version")
        rows = {name: [json.loads(line) for line in (args.data / split / f"{name}.jsonl").read_text().splitlines()] for name in ("train", "dev", "test")}
        if any(not values for values in rows.values()):
            raise ValueError(f"{split}: empty train/dev/test; expand data before training")
        if args.train_limit:
            rows["train"] = sorted(rows["train"], key=lambda r: hashlib.sha256(r["example_id"].encode()).hexdigest())[:args.train_limit]
        variants = [(name, None) for name in ("symbolic_order", "frequency", "frequency_short_vowel", "character_bigram")]
        if not args.baselines_only:
            modes = ["tiny_full"] + (["tiny_no_rules", "tiny_no_context"] if args.ablations else [])
            variants += [(name, seed) for name in modes for seed in args.seeds]
        for name, seed in variants:
            start = time.perf_counter()
            info = {}
            if seed is None:
                model = Baseline(name, rows["train"])
                dev_scores = [model.score(r) for r in rows["dev"]]
                fit_seconds = time.perf_counter() - start
                predict_start = time.perf_counter()
                scores = [model.score(r) for r in rows["test"]]
            else:
                rules, context = name != "tiny_no_rules", name != "tiny_no_context"
                model, info = train_neural(rows["train"], rows["dev"], seed=seed, epochs=args.epochs, width=args.width, layers=args.layers,
                                           use_rules=rules, use_context=context, max_length=args.max_length,
                                           pooling=args.pooling, mark_boundary=args.mark_boundary, lexical=args.lexical)
                dev_scores = predict_neural(model, rows["dev"], rules, context)
                fit_seconds = time.perf_counter() - start
                predict_start = time.perf_counter()
                scores = predict_neural(model, rows["test"], rules, context)
            predict_seconds = time.perf_counter() - predict_start
            threshold = select_threshold(rows["dev"], dev_scores)
            if seed is not None:
                torch.save({"state_dict": model.state_dict(), "width": args.width, "layers": args.layers, "max_length": args.max_length,
                            "pooling": args.pooling, "mark_boundary": args.mark_boundary, "lexicon": model.lexicon, "use_rules": rules, "use_context": context, "threshold": threshold,
                            "rules_sha256": manifest["rules_sha256"]}, args.output / f"{split}-{name}-{seed}.pt")
            report, predictions = metrics(rows["test"], scores)
            selective, _ = metrics(rows["test"], scores, threshold)
            rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024**2 if sys.platform == "darwin" else 1024)
            entry = {"split": split, "model": name, "seed": seed, "test": report, "selective_test": selective,
                     "fit_seconds_including_dev": fit_seconds, "test_inference_seconds": predict_seconds,
                     "process_peak_rss_mib_cumulative": rss, "train_examples": len(rows["train"]), **info}
            results["results"].append(entry)
            (args.output / f"{split}-{name}-{seed}-predictions.jsonl").write_text("".join(json.dumps(r) + "\n" for r in predictions))
            (args.output / "results.json").write_text(json.dumps(results, indent=2) + "\n")
            print(f"{split} {name} seed={seed}: top1={report['top1']:.3f} tie_avg={report['top1_tie_averaged']:.3f} recall={report['candidate_recall']:.3f} fit={fit_seconds:.1f}s", flush=True)
    lines = ["# Development Experiment Results", "", f"Data: **{manifest['data_kind']}**. {CAVEATS.get(manifest['data_kind'], CAVEATS['synthetic_engineering_smoke'])[0]}", "",
             "| Split | Model | Seeds | Mean top-1 | SD | Tie-averaged top-1 | Candidate recall |", "|---|---|---:|---:|---:|---:|---:|"]
    for split in args.splits:
        for name in dict.fromkeys(r["model"] for r in results["results"]):
            group = [r for r in results["results"] if r["split"] == split and r["model"] == name]
            values = [r["test"]["top1"] for r in group]
            tie_averaged = statistics.mean(r["test"]["top1_tie_averaged"] for r in group)
            lines.append(f"| {split} | {name} | {len(group)} | {statistics.mean(values):.4f} | {statistics.stdev(values) if len(values)>1 else 0:.4f} | {tie_averaged:.4f} | {group[0]['test']['candidate_recall']:.4f} |")
    lines += ["", CAVEATS.get(manifest["data_kind"], CAVEATS["synthetic_engineering_smoke"])[1],
              "Source-random and pair splits may coincide when source groups already identify pairs. Strict mixed rows remain excluded and counted.",
              "Top-1 breaks score ties by candidate index, which is alphabetical; tie-averaged top-1 is the expected score under random tie-breaking.",
              "Hyperparameters fixed before test; epoch and abstention threshold selected on dev only. Test is not used for training.",
              "Intervals in JSON are itemwise Wilson intervals, not source-cluster bootstrap intervals. RSS is cumulative process peak, not model-only memory.",
              "No unconstrained generative baseline or independently reviewed Sanskrit benchmark is claimed by this smoke experiment."]
    (args.output / "SUMMARY.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
