#!/usr/bin/env python3
"""RLCD stage 3, step 2: convert the DCS CoNLL-U to SLP1 rows and audit overlap with DCS_pick.

Every DCS sentence is compared with every DCS_pick sentence (the pretraining source), using
the rule of docs/PRETRAINING_PLAN.md: an exact match after normalisation, or at least two
distinct 30-character substrings shared with any DCS_pick sentence. Matches with the right-word
holdout dev and test source sentences are counted separately: those sentences must never reach
stage 3 training. Only the holdout files' sentence IDs are read, as in
scripts/build_pretraining_corpus.py.

Writes data/processed/dcs-conllu-v1/sentences.jsonl (not committed; regenerates from the pinned
checkout) and the committed per-chapter audit reports/dcs-conllu/overlap_by_chapter.jsonl with
its summary overlap_summary.json.
"""

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.dcs_conllu import chapter_id, chapter_info, overlap_text, read_chapter, span_hashes
from panini.pretraining import MIN_SHARED_SPANS, normalize, spans

CONLLU = ROOT / "data/external/dcs-conllu/dcs/data/conllu"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--conllu", type=Path, default=CONLLU)
    p.add_argument("--dcs-pick", type=Path, default=ROOT / "data/processed/dcs/sentences.jsonl")
    p.add_argument("--split", type=Path, default=ROOT / "data/processed/dcs-silver-slp1-splits/strict_right_lemma")
    p.add_argument("--output", type=Path, default=ROOT / "data/processed/dcs-conllu-v1")
    p.add_argument("--report", type=Path, default=ROOT / "reports/dcs-conllu")
    args = p.parse_args()

    held = {}
    for part in ("dev", "test"):
        for line in (args.split / f"{part}.jsonl").read_text().splitlines():
            held[int(json.loads(line)["source_group"].removeprefix("DCS-"))] = part
    pick_text, held_text, held_spans, chunks, buffer = {}, {}, {}, [], []
    for line in args.dcs_pick.open(encoding="utf-8"):
        s = json.loads(line)
        text = overlap_text(normalize(s["sentence"]))
        if not text:
            continue
        pick_text.setdefault(text, s["sent_id"])
        if s["sent_id"] in held:
            held_text[text] = held[s["sent_id"]]
            for piece in spans(text):
                held_spans.setdefault(piece, set()).add(held[s["sent_id"]])
        buffer.extend(span_hashes(text))
        if len(buffer) > 2_000_000:
            chunks.append(np.unique(np.array(buffer, dtype=np.int64)))
            buffer = []
    chunks.append(np.unique(np.array(buffer, dtype=np.int64)))
    pick_spans = np.unique(np.concatenate(chunks))
    if len(set(held.values())) != 2 or len({v for v in held_text.values()}) != 2:
        raise ValueError("held-out sentences not found in DCS_pick")

    def shared(hashes):
        if not hashes:
            return 0
        h = np.fromiter(hashes, dtype=np.int64)
        idx = np.searchsorted(pick_spans, h).clip(max=len(pick_spans) - 1)
        return int((pick_spans[idx] == h).sum())

    info = chapter_info(args.conllu / "lookup/chapter-info.xml")
    args.output.mkdir(parents=True, exist_ok=True)
    chapters, totals = [], Counter()
    with (args.output / "sentences.jsonl").open("w", encoding="utf-8") as out:
        for path in sorted((args.conllu / "files").rglob("*.conllu")):
            cid = chapter_id(path)
            # One chapter (Sikzasamuccaya 10815) has no metadata entry; it is kept but never counts as non-Vedic.
            meta = info.get(cid, {"path": str(path.relative_to(args.conllu / "files")), "text": path.parent.name,
                                  "vedic": None, "syntax_gold": False, "time_slot": None})
            row = {"chapter_id": cid, "path": meta["path"], "text": meta["text"], "vedic": meta["vedic"],
                   "syntax_gold": meta["syntax_gold"], "time_slot": meta["time_slot"],
                   "sentences": 0, "words": 0, "exact": 0, "near": 0, "held_dev": 0, "held_test": 0, "hiatus_ambiguous": 0}
            for s in read_chapter(path):
                text = overlap_text(s["text_slp1"])
                exact = text in pick_text
                near = not exact and shared(span_hashes(text)) >= MIN_SHARED_SPANS
                parts = set()
                if text in held_text:
                    parts.add(held_text[text])
                else:
                    hits = Counter(part for piece in spans(text) if piece in held_spans for part in held_spans[piece])
                    parts |= {part for part, n in hits.items() if n >= MIN_SHARED_SPANS}
                s.update(chapter_id=cid, overlap="exact" if exact else "near" if near else "none",
                         held=sorted(parts))
                out.write(json.dumps(s, ensure_ascii=False) + "\n")
                row["sentences"] += 1
                row["words"] += len(s["words"])
                row["exact"] += exact
                row["near"] += near
                row["held_dev"] += "dev" in parts
                row["held_test"] += "test" in parts
                row["hiatus_ambiguous"] += s["hiatus_ambiguous"]
            chapters.append(row)
            for k in ("sentences", "words", "exact", "near", "held_dev", "held_test", "hiatus_ambiguous"):
                totals[k] += row[k]
    args.report.mkdir(parents=True, exist_ok=True)
    (args.report / "overlap_by_chapter.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in chapters))
    clean = [r for r in chapters if r["exact"] == r["near"] == 0]
    summary = {
        "rule": f"exact normalised match, or at least {MIN_SHARED_SPANS} distinct 30-character substrings shared with DCS_pick",
        "inputs": {"dcs_conllu_manifest": "datasets/dcs_conllu_manifest.json", "dcs_pick_sha256": sha256(args.dcs_pick),
                   "holdout_split_sha256": {part: sha256(args.split / f"{part}.jsonl") for part in ("dev", "test")}},
        "dcs_pick": {"distinct_texts": len(pick_text), "distinct_spans": int(len(pick_spans)),
                     "held_sentences": {part: sum(v == part for v in held.values()) for part in ("dev", "test")}},
        "totals": dict(totals), "chapters": len(chapters),
        "chapters_without_overlap": {"all": len(clean), "non_vedic": sum(r["vedic"] is False for r in clean),
                                     "sentences_non_vedic": sum(r["sentences"] for r in clean if r["vedic"] is False),
                                     "words_non_vedic": sum(r["words"] for r in clean if r["vedic"] is False)},
        "chapters_without_metadata": [r["path"] for r in chapters if r["vedic"] is None],
        "metadata_without_file": sorted(v["path"] for k, v in info.items() if k not in {r["chapter_id"] for r in chapters}),
        "chapters_with_held_overlap": {part: sum(r[f"held_{part}"] > 0 for r in chapters) for part in ("dev", "test")},
        "sentences_sha256": sha256(args.output / "sentences.jsonl"),
    }
    (args.report / "overlap_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
