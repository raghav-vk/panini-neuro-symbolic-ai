#!/usr/bin/env python3
"""Build the decontaminated pretraining corpora P-A and P-B (docs/PRETRAINING_PLAN.md section 3)."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.experiment_data import right_word_lemmas
from panini.pretraining import MIN_SHARED_SPANS, SPAN, build_corpora, normalize


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def summary(rows):
    return {"sentences": len(rows), "characters": sum(len(r["text"]) for r in rows),
            "distinct_sentences": len({r["text"] for r in rows})}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sentences", type=Path, default=ROOT / "data/processed/dcs/sentences.jsonl")
    p.add_argument("--split", type=Path, default=ROOT / "data/processed/dcs-silver-slp1-splits/strict_right_lemma",
                   help="right-word holdout directory; its dev and test source sentences are removed")
    p.add_argument("--output", type=Path, default=ROOT / "data/processed/pretrain-v1")
    p.add_argument("--report", type=Path, default=ROOT / "reports/pretraining-v1/corpus_audit.json")
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    held_ids, lemmas, dev_ids = set(), set(), set()
    for part in ("dev", "test"):
        for line in (args.split / f"{part}.jsonl").read_text().splitlines():
            row = json.loads(line)
            sent_id = int(row["source_group"].removeprefix("DCS-"))
            held_ids.add(sent_id)
            if part == "dev":
                dev_ids.add(sent_id)
            lemmas |= right_word_lemmas(row)
    sentences = [json.loads(line) for line in args.sentences.read_text(encoding="utf-8").splitlines()]
    pa, pb, removed = build_corpora(sentences, held_ids, lemmas)
    write_jsonl(args.output / "P-A.jsonl", pa)
    write_jsonl(args.output / "P-B.jsonl", pb)
    # Dev sentences only, for label-free checks during pretraining (plan section 8 step 3). Test is never written.
    write_jsonl(args.output / "dev_sentences.jsonl",
                [{"sent_id": s["sent_id"], "text": normalize(s["sentence"])} for s in sentences if s["sent_id"] in dev_ids])
    kept = {r["sent_id"] for r in pa}
    audit = {
        "plan": "docs/PRETRAINING_PLAN.md section 3; protocol section 11.3",
        "inputs": {"sentences": str(args.sentences.relative_to(ROOT)), "sentences_sha256": sha256(args.sentences),
                   "split": str(args.split.relative_to(ROOT)),
                   "split_sha256": {part: sha256(args.split / f"{part}.jsonl") for part in ("dev", "test")},
                   "corpus_sentences": len(sentences), "corpus_characters": sum(len(s["sentence"]) for s in sentences)},
        "sources_read": ["DCS_pick sentences (CC BY 4.0)", "right-word holdout dev and test files (sentence IDs and right-word lemmas only)"],
        "kosha_used": False,
        "definitions": {
            "normalisation": "DCS_pick's three non-SLP1 vowel characters mapped (ṝ to F, ± to x, ² to X); whitespace runs collapsed to one space, ends stripped",
            "not_slp1": "any character other than SLP1 letters, avagraha and space remains: editorial markers, digits, unknown signs; removed from both corpora",
            "exact_duplicate": "normalised text equal to a held-out sentence",
            "near_duplicate": f"shares at least {MIN_SHARED_SPANS} distinct {SPAN}-character substrings with any held-out sentence",
            "held_lemma": "DCS lemma annotation (IAST, converted to SLP1) includes a held-out right-word lemma; P-B only"},
        "held_out": {"dev_sentences": len(dev_ids), "test_sentences": len(held_ids - dev_ids), "sentences": len(held_ids),
                     "right_word_lemmas": len(lemmas), "right_word_lemmas_sha256": hashlib.sha256("\n".join(sorted(lemmas)).encode()).hexdigest()},
        "removed": {"held_out": len(removed["held_out"]), "exact_duplicate": len(removed["exact_duplicate"]),
                    "near_duplicate": len(removed["near_duplicate"]), "not_slp1": len(removed["not_slp1"]),
                    "held_lemma_P-B": len(removed["held_lemma"]),
                    "empty_after_normalisation": len(sentences) - len(held_ids) - len(removed["exact_duplicate"])
                    - len(removed["near_duplicate"]) - len(removed["not_slp1"]) - len(pa)},
        "plan_figures_2026-10-24": {
            "held_out": 1801, "exact_duplicate": 44, "near_duplicate": 425, "P-B_before_duplicate_removal": 349450,
            "note": "The near-duplicate method of 2026-10-24 was not recorded. Its 425 could not be reproduced on SLP1 or IAST "
                    "text; the stated definition gives the count above, which removes more."},
        "corpora": {"P-A": {**summary(pa), "sha256": sha256(args.output / "P-A.jsonl")},
                    "P-B": {**summary(pb), "sha256": sha256(args.output / "P-B.jsonl")},
                    "dev_sentences": {"sentences": len(dev_ids), "sha256": sha256(args.output / "dev_sentences.jsonl")}},
        "checks": {"held_out_in_P-A": len(held_ids & kept), "held_out_in_P-B": len(held_ids & {r["sent_id"] for r in pb}),
                   "P-B_subset_of_P-A": {r["sent_id"] for r in pb} <= kept},
        "removed_ids": {"exact_duplicate": removed["exact_duplicate"], "near_duplicate": removed["near_duplicate"],
                        "not_slp1": removed["not_slp1"],
                        "held_lemma_sha256": hashlib.sha256(json.dumps(removed["held_lemma"]).encode()).hexdigest()},
    }
    if audit["checks"]["held_out_in_P-A"] or audit["checks"]["held_out_in_P-B"] or not audit["checks"]["P-B_subset_of_P-A"]:
        raise AssertionError("decontamination check failed")
    text = json.dumps(audit, indent=2, ensure_ascii=False) + "\n"
    (args.output / "audit.json").write_text(text, encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(text, encoding="utf-8")
    print(json.dumps({k: audit[k] for k in ("removed", "corpora")}, indent=2))


if __name__ == "__main__":
    main()
