#!/usr/bin/env python3
"""Apply the pre-registered DCS division (docs/RLCD_TRANSITION_PLAN.md, stage 3; approved 2026-11-14).

- gold-set reserve: every chapter of eight whole clean kavya texts; never written out here
- stage 3 dev and test: every other classical clean chapter, by SHA-256 of "rlcd-stage3:" + chapter ID
- stage 3 train: every remaining sentence, except matches with the right-word holdout source sentences

Reads reports/dcs-conllu/overlap_by_chapter.jsonl and data/processed/dcs-conllu-v1/sentences.jsonl
(scripts/convert_dcs_conllu.py). Writes train, dev and test JSONL next to the sentences, and the
committed reports/dcs-conllu/split_manifest.json. Sentence text of the reserve and of test is not
inspected; only counts are recorded.
"""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD_RESERVE = ("Saundarānanda", "Āryāsaptaśatī", "Narmamālā", "Kokilasaṃdeśa", "Bhallaṭaśataka", "Haṃsasaṃdeśa",
                "Caurapañcaśikā", "Mukundamālā")


def classical(chapter):
    return chapter["vedic"] is False and chapter["time_slot"] != "1"


def clean(chapter):
    return chapter["exact"] == 0 and chapter["near"] == 0


def evaluation_part(chapter_id):
    return "test" if hashlib.sha256(f"rlcd-stage3:{chapter_id}".encode()).digest()[0] & 1 else "dev"


def assign(chapters):
    """chapter ID -> 'gold_reserve' | 'dev' | 'test' | 'train'."""
    texts = {c["text"] for c in chapters}
    missing = set(GOLD_RESERVE) - texts
    if missing:
        raise ValueError(f"reserve texts not in DCS: {sorted(missing)}")
    out = {}
    for c in chapters:
        if c["text"] in GOLD_RESERVE:
            if not (clean(c) and classical(c)):
                raise ValueError(f"reserve chapter {c['chapter_id']} is not clean and classical")
            out[c["chapter_id"]] = "gold_reserve"
        elif classical(c) and clean(c):
            out[c["chapter_id"]] = evaluation_part(c["chapter_id"])
        else:
            out[c["chapter_id"]] = "train"
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--chapters", type=Path, default=ROOT / "reports/dcs-conllu/overlap_by_chapter.jsonl")
    p.add_argument("--data", type=Path, default=ROOT / "data/processed/dcs-conllu-v1")
    p.add_argument("--manifest", type=Path, default=ROOT / "reports/dcs-conllu/split_manifest.json")
    args = p.parse_args()
    chapters = [json.loads(line) for line in args.chapters.read_text(encoding="utf-8").splitlines()]
    part = assign(chapters)
    text_of = {c["chapter_id"]: c["text"] for c in chapters}
    counts, words, dropped, per_text = Counter(), Counter(), Counter(), {"dev": Counter(), "test": Counter()}
    files = {name: (args.data / f"{name}.jsonl").open("w", encoding="utf-8") for name in ("train", "dev", "test")}
    for line in (args.data / "sentences.jsonl").open(encoding="utf-8"):
        s = json.loads(line)
        where = part[s["chapter_id"]]
        if where == "gold_reserve":
            counts[where] += 1
            continue
        if s["held"]:
            if where != "train":
                raise ValueError(f"evaluation chapter {s['chapter_id']} has a held-out match")
            dropped["held_out_match"] += 1
            continue
        counts[where] += 1
        words[where] += len(s["words"])
        if where in per_text:
            per_text[where][text_of[s["chapter_id"]]] += 1
        files[where].write(line)
    for f in files.values():
        f.close()
    manifest = {
        "rule": "docs/RLCD_TRANSITION_PLAN.md, stage 3, DCS division (approved 2026-11-14)",
        "gold_reserve": {"texts": list(GOLD_RESERVE), "chapters": sorted(k for k, v in part.items() if v == "gold_reserve"),
                         "sentences": counts["gold_reserve"]},
        "evaluation": {name: {"chapters": sorted(k for k, v in part.items() if v == name), "sentences": counts[name],
                              "words": words[name], "texts": dict(per_text[name].most_common())} for name in ("dev", "test")},
        "train": {"chapters": sum(v == "train" for v in part.values()), "sentences": counts["train"], "words": words["train"],
                  "dropped": dict(dropped)},
        "sha256": {name: hashlib.sha256((args.data / f"{name}.jsonl").read_bytes()).hexdigest() for name in ("train", "dev", "test")},
        "inputs_sha256": {"overlap_by_chapter": hashlib.sha256(args.chapters.read_bytes()).hexdigest(),
                          "sentences": hashlib.sha256((args.data / "sentences.jsonl").read_bytes()).hexdigest()},
    }
    args.manifest.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: (v if k in ("train",) else {"sentences": v["sentences"]}) for k, v in manifest.items()
                      if k in ("gold_reserve", "train")}, ensure_ascii=False),
          {n: (manifest["evaluation"][n]["sentences"], len(manifest["evaluation"][n]["chapters"]),
               len(manifest["evaluation"][n]["texts"])) for n in ("dev", "test")})


if __name__ == "__main__":
    main()
