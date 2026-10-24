#!/usr/bin/env python3
"""Copy prepared splits, flagging each candidate's words as known or unknown in the Vidyut kosha."""

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from panini.lexicon import KoshaLexicon, annotate
from fetch_vidyut_data import SHA256, URL

TERMS = ("Vidyut 0.4.0 prebuilt kosha (MIT code). Built from learnsanskrit.org (CC0), Sanskrit Heritage "
         "(LGPLLR) and Monier-Williams (CC BY-NC-SA 3.0) data. Local research dependency; flags derived from it "
         "are not redistributed.")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", type=Path, required=True, help="output directory of prepare_experiment.py")
    p.add_argument("--kosha", type=Path, default=ROOT / "data/external/vidyut-0.4.0/kosha")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    lexicon = KoshaLexicon(args.kosha)
    manifest = json.loads((args.data / "manifest.json").read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    stats = {}
    for split, audit in manifest["splits"].items():
        (args.output / split).mkdir()
        for path in sorted((args.data / split).iterdir()):
            if path.suffix != ".jsonl":
                shutil.copy(path, args.output / split / path.name)
                continue
            rows = annotate([json.loads(line) for line in path.read_text().splitlines()], lexicon)
            (args.output / split / path.name).write_text(
                "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
            if path.stem in audit.get("file_sha256", {}):
                audit["file_sha256"][path.stem] = hashlib.sha256((args.output / split / path.name).read_bytes()).hexdigest()
            candidates = [c for r in rows for c in r["candidates"]]
            stats[f"{split}/{path.stem}"] = {"candidates": len(candidates),
                                             "kosha_right_known": sum(c["kosha_right"] for c in candidates) / max(len(candidates), 1)}
    for name in ("examples.jsonl",):
        if (args.data / name).exists():
            shutil.copy(args.data / name, args.output / name)
    manifest["external_lexicon"] = {"name": "vidyut-kosha", "url": URL, "archive_sha256": SHA256, "terms": TERMS,
                                    "fields": ["kosha_left", "kosha_right"], "stats": stats}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
