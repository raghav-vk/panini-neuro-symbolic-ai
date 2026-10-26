#!/usr/bin/env python3
"""Build a local-only browser worksheet from review items.

The default "boundary" mode edits pending DCS boundary proposals. The "verify"
mode shows items from scripts/prepare_expert_review.py and records one
decision per item (correct, wrong with a correction, not a boundary, unsure).
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
        config = {"title": args.title, "answers_name": args.answers_name}
        page = ((ROOT / "src/review/verify.html").read_text(encoding="utf-8")
                .replace("__REVIEW_CONFIG__", embed(config)).replace("__REVIEW_DATA__", embed(rows)))
    output = args.output or args.input.with_name("review.html")
    output.write_text(page, encoding="utf-8")
    print(f"Built local review worksheet: {output.resolve()} ({len(rows)} items)")


if __name__ == "__main__":
    main()
