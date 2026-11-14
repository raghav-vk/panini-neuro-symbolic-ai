#!/usr/bin/env python3
"""Fetch the DCS CoNLL-U files at a pinned commit and record their hashes (docs/GOLD_SET_PLAN.md section 3).

Sparse checkout of dcs/data/conllu from OliverHellwig/sanskrit only. The data is CC BY 4.0
(Hellwig, The Digital Corpus of Sanskrit, 2010-2024). It is a local dependency under
data/external/, never committed. The committed record is datasets/dcs_conllu_manifest.json:
commit, file count, bytes, and one SHA-256 over every file's path and hash, so a later
checkout can be verified with --verify.
"""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/OliverHellwig/sanskrit.git"
COMMIT = "8aeed5a1343d0e48b64eb32af8c00e8c6eb29359"  # HEAD on 2026-11-14
SUBDIR = "dcs/data/conllu"
MANIFEST = ROOT / "datasets/dcs_conllu_manifest.json"


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def inventory(base):
    files = sorted(p for p in (base / SUBDIR).rglob("*") if p.is_file())
    lines = [f"{p.relative_to(base / SUBDIR).as_posix()} {hashlib.sha256(p.read_bytes()).hexdigest()}" for p in files]
    return {"files": len(files), "conllu_files": sum(p.suffix == ".conllu" for p in files),
            "bytes": sum(p.stat().st_size for p in files),
            "tree_sha256": hashlib.sha256("\n".join(lines).encode()).hexdigest()}, lines


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=ROOT / "data/external/dcs-conllu")
    p.add_argument("--verify", action="store_true", help="check an existing checkout against the committed manifest")
    args = p.parse_args()
    if not args.verify:
        if args.output.exists():
            raise SystemExit(f"{args.output} exists; use --verify, or remove it to fetch again")
        args.output.mkdir(parents=True)
        git("init", "-q", cwd=args.output)
        git("remote", "add", "origin", REPO, cwd=args.output)
        git("sparse-checkout", "set", "--no-cone", SUBDIR + "/", cwd=args.output)
        git("fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", COMMIT, cwd=args.output)
        git("checkout", "-q", "FETCH_HEAD", cwd=args.output)
    head = git("rev-parse", "HEAD", cwd=args.output)
    if head != COMMIT:
        raise SystemExit(f"checkout is at {head}, expected {COMMIT}")
    summary, lines = inventory(args.output)
    (args.output / "files.sha256").write_text("\n".join(lines) + "\n")
    record = {"source": REPO, "commit": COMMIT, "path": SUBDIR, "license": "CC BY 4.0",
              "citation": "Hellwig, The Digital Corpus of Sanskrit (DCS), 2010-2024", **summary}
    if args.verify:
        expected = json.loads(MANIFEST.read_text())
        if {k: expected[k] for k in record} != record:
            raise SystemExit("checkout differs from datasets/dcs_conllu_manifest.json")
        print("verified against", MANIFEST.relative_to(ROOT))
    else:
        MANIFEST.write_text(json.dumps(record, indent=1) + "\n")
        print(json.dumps(record, indent=1))


if __name__ == "__main__":
    main()
