#!/usr/bin/env python3
"""Prepare all three holdouts and certificate-bearing candidate sets."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.rules import load_rules
from panini.candidates import enumerate_candidates, gold_indices
from panini.experiment_data import synthetic_examples, split_examples, validate_reviewed, validate_silver, digest


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rules", type=Path, default=ROOT / "data/rules/development_sandhi.jsonl")
    source = p.add_mutually_exclusive_group()
    source.add_argument("--examples", type=Path, help="independently reviewed boundaries; omit for synthetic smoke data")
    source.add_argument("--silver-examples", type=Path, help="unreviewed DCS alignments from extract_dcs_boundaries.py")
    p.add_argument("--per-rule", type=int, default=200)
    p.add_argument("--seed", type=int, default=1729)
    p.add_argument("--output", type=Path, default=ROOT / "data/processed/development")
    args = p.parse_args()
    rules = load_rules(args.rules)
    if args.examples:
        records = [validate_reviewed(json.loads(line), rules) for line in args.examples.read_text().splitlines() if line.strip()]
    elif args.silver_examples:
        records = [validate_silver(json.loads(line), rules) for line in args.silver_examples.read_text().splitlines() if line.strip()]
    else:
        records = synthetic_examples(rules, args.per_rule, args.seed)
    args.output.mkdir(parents=True, exist_ok=False)
    write_jsonl(args.output / "examples.jsonl", records)
    kind = "reviewed_corpus" if args.examples else "dcs_silver_alignment" if args.silver_examples else "synthetic_engineering_smoke"
    manifest = {"data_kind": kind,
                "rules_sha256": digest(args.rules.read_text()), "rules": [r.rule_id for r in rules],
                "rules_expert_reviewed": sum(r.status == "expert_reviewed" for r in rules), "splits": {}}
    for method in ("source_random", "pair", "strict_lemma", "strict_right_lemma"):
        splits, audit = split_examples(records, method, args.seed)
        directory = args.output / method
        directory.mkdir()
        for name, rows in splits.items():
            enriched = []
            for row in rows:
                candidates = enumerate_candidates(row["surface"], rules, row["tags"])
                enriched.append({**row, "candidates": candidates, "gold_indices": gold_indices(row, candidates)})
            write_jsonl(directory / f"{name}.jsonl", enriched)
            audit.setdefault("file_sha256", {})[name] = hashlib.sha256((directory / f"{name}.jsonl").read_bytes()).hexdigest()
            audit.setdefault("candidate_coverage", {})[name] = {
                "examples": len(enriched), "covered": sum(bool(r["gold_indices"]) for r in enriched),
                "ambiguous": sum(len(r["candidates"]) > 1 for r in enriched),
                "total_candidates": sum(len(r["candidates"]) for r in enriched)}
        (directory / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
        manifest["splits"][method] = audit
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({m: a["counts"] for m, a in manifest["splits"].items()}, indent=2))


if __name__ == "__main__":
    main()
