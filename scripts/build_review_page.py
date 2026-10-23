#!/usr/bin/env python3
"""Build a local-only browser worksheet from pending DCS boundary proposals."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.input.read_text().splitlines() if line.strip()]
    template = (ROOT / "src/review/worksheet.html").read_text()
    data = json.dumps(rows, ensure_ascii=False).replace("<", "\\u003c")
    output = args.output or args.input.with_name("review.html")
    output.write_text(template.replace("__REVIEW_DATA__", data), encoding="utf-8")
    print(f"Built local review worksheet: {output.resolve()} ({len(rows)} proposals)")


if __name__ == "__main__":
    main()
