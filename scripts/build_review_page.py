#!/usr/bin/env python3
"""Build a local-only browser worksheet from review items.

The default "boundary" mode edits pending DCS boundary proposals. The "verify"
mode shows items from scripts/prepare_expert_review.py and records one
decision per item (correct, wrong with a correction, not a boundary, unsure).
Verify items are stored in SLP1 and shown in IAST, converted here. With --devanagari the page also
carries a Devanagari rendering (needs vidyut) and lets the reviewer switch between the two scripts.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.translit import slp1_to_devanagari, slp1_to_iast

SANSKRIT_FIELDS = ("surface", "proposed_left", "proposed_right", "left_lemma", "right_lemma")


def iast_item(item):
    """An SLP1 review item as the reviewer sees it; the span becomes IAST code points."""
    start, end = item["span"]
    before = slp1_to_iast(item["sentence"][:start])
    shown = {**item, **{k: slp1_to_iast(item[k]) for k in SANSKRIT_FIELDS}, "sentence": slp1_to_iast(item["sentence"])}
    shown["span"] = [len(before), len(before) + len(shown["surface"])]
    return shown


def devanagari_view(item):
    """The reviewer-facing fields of an SLP1 item in Devanagari, with the span in its code points.

    The span must cover whole space-separated words, so the prefix converts on its own.
    """
    start, end = item["span"]
    sentence = item["sentence"]
    if (start and sentence[start - 1] != " ") or (end < len(sentence) and sentence[end] != " "):
        raise ValueError(f"{item['item_id']}: span does not cover whole words")
    before = slp1_to_devanagari(sentence[:start])
    shown = {k: slp1_to_devanagari(item[k]) for k in SANSKRIT_FIELDS}
    shown["sentence"] = slp1_to_devanagari(sentence)
    shown["span"] = [len(before), len(before) + len(shown["surface"])]
    if shown["sentence"][shown["span"][0]:shown["span"][1]] != shown["surface"]:
        raise ValueError(f"{item['item_id']}: Devanagari span does not match the surface")
    return shown


def embed(value):
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--mode", choices=["boundary", "verify"], default="boundary")
    parser.add_argument("--ids", type=Path, help="verify mode: JSON list of item IDs to include")
    parser.add_argument("--title", default="Verify proposed splits")
    parser.add_argument("--answers-name", default="answers.jsonl", help="verify mode: exported file name")
    parser.add_argument("--devanagari", action="store_true", help="verify mode: add Devanagari, shown by default")
    parser.add_argument("--round", type=Path, help="verify mode: round.json; adds a countdown and sealed hand-in")
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.mode == "boundary":
        page = (ROOT / "src/review/worksheet.html").read_text(encoding="utf-8").replace("__REVIEW_DATA__", embed(rows))
    else:
        if args.ids:
            wanted = set(json.loads(args.ids.read_text(encoding="utf-8")))
            rows = [r for r in rows if r["item_id"] in wanted]
            if len(rows) != len(wanted):
                parser.error("some IDs are not in the input")
        rows = [{**iast_item(r), **({"devanagari": devanagari_view(r)} if args.devanagari else {})} for r in rows]
        config = {"title": args.title, "answers_name": args.answers_name, "devanagari": args.devanagari}
        if args.round:
            r = json.loads(args.round.read_text(encoding="utf-8"))
            config["round"] = {k: r[k] for k in ("round", "closes", "hand_in_url", "public_key_spki")}
        page = ((ROOT / "src/review/verify.html").read_text(encoding="utf-8")
                .replace("__REVIEW_CONFIG__", embed(config)).replace("__REVIEW_DATA__", embed(rows)))
    output = args.output or args.input.with_name("review.html")
    output.write_text(page, encoding="utf-8")
    print(f"Built local review worksheet: {output.resolve()} ({len(rows)} items)")


if __name__ == "__main__":
    main()
