#!/usr/bin/env python3
"""Extract silver external vowel-sandhi boundaries from converted DCS sentences."""

import argparse
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.candidates import forward
from panini.dcs import external_vowel_boundaries
from panini.rules import load_rules


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def label(example, rules):
    """Rules label an already aligned example; they never decide the alignment."""
    proofs = [t for t in forward(rules, example["left"], example["right"], example["tags"])
              if t.output == example["surface"]]
    example["rule_id"] = proofs[0].rule_id if len(proofs) == 1 else "UNSUPPORTED" if not proofs else "AMBIGUOUS"
    example["matching_rule_ids"] = sorted(t.rule_id for t in proofs)
    return example


def review_sample(examples, size, seed):
    """Round-robin across junction types so rare patterns reach expert audit."""
    strata = defaultdict(list)
    for example in examples:
        strata["+".join(example["vowel_pair"]) + "→" + example["observed_junction"]].append(example)
    rng = random.Random(seed)
    for rows in strata.values():
        rng.shuffle(rows)
    sample, order = [], sorted(strata, key=lambda k: (-len(strata[k]), k))
    while len(sample) < size and any(strata.values()):
        for key in order:
            if strata[key] and len(sample) < size:
                sample.append(strata[key].pop())
    return sorted(sample, key=lambda r: r["example_id"])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sentences", type=Path, default=ROOT / "data/processed/dcs/sentences.jsonl")
    p.add_argument("--rules", type=Path, default=ROOT / "data/rules/development_sandhi.jsonl")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--context-window", type=int, default=1, help="neighbouring whitespace chunks on each side")
    p.add_argument("--review-sample", type=int, default=200)
    p.add_argument("--seed", type=int, default=1729)
    args = p.parse_args()
    if args.context_window < 0 or args.review_sample < 0:
        p.error("counts must be nonnegative")
    rules = load_rules(args.rules)
    args.output.mkdir(parents=True, exist_ok=False)
    counts, junctions, rule_counts, pairs, examples = Counter(), Counter(), Counter(), Counter(), []
    with args.sentences.open(encoding="utf-8") as handle:
        for line in handle:
            counts["sentences"] += 1
            for example, reason in external_vowel_boundaries(json.loads(line), args.context_window):
                if reason:
                    counts[reason] += 1
                    continue
                examples.append(label(example, rules))
                junctions["+".join(example["vowel_pair"]) + "→" + example["observed_junction"]] += 1
                rule_counts[example["rule_id"]] += 1
                pairs[(example["left_lemma"], example["right_lemma"])] += 1
    counts["extracted"] = len(examples)
    with (args.output / "examples.jsonl").open("w", encoding="utf-8") as out:
        for example in examples:
            out.write(json.dumps(example, ensure_ascii=False, sort_keys=True) + "\n")
    sample = review_sample(examples, args.review_sample, args.seed)
    with (args.output / "review_sample.jsonl").open("w", encoding="utf-8") as out:
        for example in sample:
            out.write(json.dumps({**example, "review_status": "pending", "reviewer": "", "reviewed_at": "",
                                  "review_decision": "", "notes": ""}, ensure_ascii=False, sort_keys=True) + "\n")
    report = {
        "schema_version": 1, "data_kind": "dcs_silver_alignment",
        "sentences_sha256": file_sha256(args.sentences), "rules_sha256": file_sha256(args.rules),
        "context_window": args.context_window, "counts": dict(counts),
        "supported_by_rules": sum(v for k, v in rule_counts.items() if k not in {"UNSUPPORTED", "AMBIGUOUS"}),
        "rule_counts": dict(rule_counts.most_common()), "junctions": dict(junctions.most_common()),
        "distinct_left_lemmas": len({a for a, _ in pairs}), "distinct_right_lemmas": len({b for _, b in pairs}),
        "top_lemma_pairs": [[a, b, n] for (a, b), n in pairs.most_common(25)],
        "review_sample": {"size": len(sample), "strategy": "round-robin over vowel_pair→junction strata", "seed": args.seed},
        "scope": ("Indeclinable left words opening a whitespace chunk, joined to a vowel-initial word that runs "
                  "to the chunk end. Alignment uses DCS lemmas and the attested surface, not sandhi rules. "
                  "Silver data: not expert reviewed."),
    }
    (args.output / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("counts", "supported_by_rules", "rule_counts")}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
