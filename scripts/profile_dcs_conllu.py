#!/usr/bin/env python3
"""Count sentences, words, morphological features and treebank relations in the DCS CoNLL-U checkout.

Reads data/external/dcs-conllu (scripts/fetch_dcs_conllu.py) and writes reports/dcs-conllu/profile.json.
Words are syntactic words (lines numbered 1, 2, ...); multiword-token lines (1-3) are not counted.
"""

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ROOT / "data/external/dcs-conllu/dcs/data/conllu/files"


def words(path):
    for line in path.open(encoding="utf-8"):
        if line[:1].isdigit():
            cols = line.rstrip("\n").split("\t")
            if len(cols) >= 10 and "-" not in cols[0]:
                yield cols


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--files", type=Path, default=FILES)
    p.add_argument("--output", type=Path, default=ROOT / "reports/dcs-conllu/profile.json")
    args = p.parse_args()
    feats, finite, deprels, annotators = Counter(), Counter(), Counter(), Counter()
    sentences = count = 0
    texts = sorted(d.name for d in args.files.iterdir() if d.is_dir())
    for f in sorted(args.files.rglob("*.conllu")):
        sentences += sum(line.startswith("# sent_id") for line in f.open(encoding="utf-8"))
        for cols in words(f):
            count += 1
            fs = dict(x.split("=", 1) for x in cols[5].split("|") if "=" in x)
            feats.update(f"{k}={v}" for k, v in fs.items())
            if cols[3] == "VERB" and "Person" in fs:
                finite[f"{fs.get('Tense')}|{fs.get('Mood')}|{fs.get('Voice', 'unmarked')}"] += 1
    parsed_words = 0
    for f in sorted(args.files.rglob("*.conllu_parsed")):
        for cols in words(f):
            parsed_words += 1
            deprels[cols[7]] += 1
            marks = [x[10:] for x in cols[9].split("|") if x.startswith("Annotator=")]
            annotators[marks[0] if marks else "none"] += 1
    record = {"texts": len(texts), "conllu_files": sum(1 for _ in args.files.rglob("*.conllu")),
              "sentences": sentences, "words": count,
              "features": dict(feats.most_common()), "finite_verbs_tense_mood_voice": dict(finite.most_common()),
              "treebank": {"files": sum(1 for _ in args.files.rglob("*.conllu_parsed")), "words": parsed_words,
                           "annotator": dict(annotators.most_common()), "deprel": dict(deprels.most_common())}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: record[k] for k in ("texts", "conllu_files", "sentences", "words")}),
          json.dumps(record["treebank"]["annotator"]))


if __name__ == "__main__":
    main()
