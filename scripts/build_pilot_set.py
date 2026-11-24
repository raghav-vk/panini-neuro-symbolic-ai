#!/usr/bin/env python3
"""Build the community review pilot set (docs/REVIEW_APP_DESIGN.md, stage 0).

Draws proposed splits from the right-word holdout TRAINING split only, and mixes in control items
with a known answer:
- "correct" controls: both DCS words occur at least five times in training, and every other split the
  rules license contains a word that never does;
- "wrong" controls: the proposal is a licensed split other than the DCS split, and neither of its
  words occurs anywhere in training, while the DCS words do.

Every item is checked against an exclusion list before it is used:
- every source group in any dev, test or mixed file of any sandhi split;
- every sentence of the pending expert review sample (data/reviews/silver_sample.jsonl);
- every sentence of the DCS CoNLL-U gold-set reserve and stage 3 dev and test chapters.

Writes, under --output:
- pilot_items.jsonl: what reviewers see, with opaque IDs (P-001...), shuffled;
- manifest.json: inputs, seed, counts, and the SHA-256 of the answer key.
The answer key (which items are controls, their answers and the source IDs) goes to --key, which
must be outside the repository's committed files: if reviewers can read it, controls are useless.
"""

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_expert_review import review_item

SPLITS = ROOT / "data/processed/dcs-silver-slp1-kosha-splits"
CONLLU = ROOT / "data/processed/dcs-conllu-v1/sentences.jsonl"
DCS_MANIFEST = ROOT / "reports/dcs-conllu/split_manifest.json"
PENDING = ROOT / "data/reviews/silver_sample.jsonl"
OUTPUT = ROOT / "data/reviews/pilot"
KEY = ROOT / "data/reviews/pilot/private/answer_key.jsonl"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def norm(sentence):
    return " ".join(sentence.split())


def exclusions(splits=SPLITS, conllu=CONLLU, dcs_manifest=DCS_MANIFEST, pending=PENDING):
    """Source groups and normalised sentences no pilot item may come from."""
    groups, sentences = set(), set()
    for split in sorted(p for p in splits.iterdir() if p.is_dir()):
        for name in ("dev", "test", "mixed"):
            for row in read_jsonl(split / f"{name}.jsonl"):
                groups.add(row["source_group"])
                sentences.add(norm(row["source_sentence"]))
    for row in read_jsonl(pending):
        sentences.add(norm(row["sentence"]))
    manifest = json.loads(dcs_manifest.read_text())
    chapters = {str(c) for c in manifest["gold_reserve"]["chapters"]}
    for part in ("dev", "test"):
        chapters |= {str(c) for c in manifest["evaluation"][part]["chapters"]}
    with open(conllu, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if str(row["chapter_id"]) in chapters:
                sentences.add(norm(row["text_slp1"]))
    return groups, sentences


def eligible(row, groups, sentences):
    return (row["source_group"] not in groups and norm(row["source_sentence"]) not in sentences
            and row["rule_id"] != "UNSUPPORTED" and len(row["gold_indices"]) == 1)


def word_counts(train):
    counts = Counter()
    for row in train:
        counts[row["left"]] += 1
        counts[row["right"]] += 1
    return counts


def clear_correct(row, counts, minimum=5):
    """The DCS split is the only licensed split made of training words."""
    gold_index = row["gold_indices"][0]
    gold = row["candidates"][gold_index]
    if counts[gold["left"]] < minimum or counts[gold["right"]] < minimum:
        return False
    return all(counts[c["left"]] == 0 or counts[c["right"]] == 0
               for i, c in enumerate(row["candidates"]) if i != gold_index)


def wrong_candidate(row, counts):
    """A licensed non-DCS split whose two words never occur in training, if the DCS words do."""
    gold = row["candidates"][row["gold_indices"][0]]
    if counts[gold["left"]] < 2 or counts[gold["right"]] < 2:
        return None
    for i, c in enumerate(row["candidates"]):
        if i != row["gold_indices"][0] and counts[c["left"]] == 0 and counts[c["right"]] == 0:
            return c
    return None


def build(train, groups, sentences, real, controls, seed):
    """(public items, answer key), shuffled together with opaque IDs."""
    rng = random.Random(seed)
    pool = [r for r in train if eligible(r, groups, sentences)]
    rng.shuffle(pool)
    counts = word_counts(train)
    used_groups, chosen = set(), []

    def take(row, kind, proposal=None):
        used_groups.add(row["source_group"])
        item = review_item(row)
        if proposal is not None:
            item["proposed_left"], item["proposed_right"] = proposal["left"], proposal["right"]
        gold = row["candidates"][row["gold_indices"][0]]
        chosen.append((item, {"kind": kind, "source_id": row["example_id"], "rule_id": row["rule_id"],
                              "tags": row.get("tags", ["pada_boundary"]), "dcs_left": gold["left"], "dcs_right": gold["right"],
                              "expected": {"real": None, "control_correct": "correct", "control_wrong": "wrong"}[kind]}))

    n_correct = controls // 2
    for row in pool:
        if sum(k["kind"] == "control_correct" for _, k in chosen) >= n_correct:
            break
        if row["source_group"] not in used_groups and clear_correct(row, counts):
            take(row, "control_correct")
    for row in pool:
        if sum(k["kind"] == "control_wrong" for _, k in chosen) >= controls - n_correct:
            break
        if row["source_group"] not in used_groups and (c := wrong_candidate(row, counts)) is not None:
            take(row, "control_wrong", c)
    for row in pool:
        if sum(k["kind"] == "real" for _, k in chosen) >= real:
            break
        if row["source_group"] not in used_groups:
            take(row, "real")
    if len(chosen) != real + controls:
        raise SystemExit(f"only {len(chosen)} of {real + controls} items could be drawn")
    rng.shuffle(chosen)
    items, key = [], []
    for number, (item, entry) in enumerate(chosen, 1):
        item_id = f"P-{number:03d}"
        items.append({**item, "item_id": item_id})
        key.append({"item_id": item_id, **entry})
    return items, key


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--train", type=Path, default=SPLITS / "strict_right_lemma/train.jsonl")
    p.add_argument("--output", type=Path, default=OUTPUT)
    p.add_argument("--key", type=Path, default=KEY)
    p.add_argument("--real", type=int, default=48)
    p.add_argument("--controls", type=int, default=12)
    p.add_argument("--seed", type=int, default=2026)
    args = p.parse_args()
    groups, sentences = exclusions()
    train = read_jsonl(args.train)
    items, key = build(train, groups, sentences, args.real, args.controls, args.seed)
    for item in items:
        if norm(item["sentence"]) in sentences:
            raise SystemExit(f"{item['item_id']}: excluded sentence slipped through")
    args.output.mkdir(parents=True, exist_ok=True)
    args.key.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output / "pilot_items.jsonl", items)
    write_jsonl(args.key, key)
    manifest = {
        "source": "DCS_pick (Krishna et al. 2017, CC BY 4.0), silver right-word holdout training split",
        "design": "docs/REVIEW_APP_DESIGN.md, stage 0 pilot",
        "inputs": {"train": sha256(args.train), "split_manifest": sha256(DCS_MANIFEST), "pending_review": sha256(PENDING)},
        "seed": args.seed, "items": len(items),
        "kinds": dict(Counter(k["kind"] for k in key)),
        "excluded_source_groups": len(groups), "excluded_sentences": len(sentences),
        "outputs": {"pilot_items.jsonl": sha256(args.output / "pilot_items.jsonl")},
        "answer_key_sha256": sha256(args.key),
        "controls_vetted": False,
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("items", "kinds", "excluded_source_groups", "excluded_sentences")}))
    print(f"answer key (do not commit): {args.key}")


if __name__ == "__main__":
    main()
