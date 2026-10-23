#!/usr/bin/env python3
"""Verify and safely convert DCS records, preserving a rejection audit."""

import argparse
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.dcs import decode_record, boundary_proposals
from audit_dcs_archive import verify_archive_identity


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", type=Path, default=ROOT / "datasets/DCS_pick.zip")
    p.add_argument("--manifest", type=Path, default=ROOT / "datasets/dcs_source_manifest.json")
    p.add_argument("--output", type=Path, default=ROOT / "data/processed/dcs")
    p.add_argument("--limit", type=int, default=0, help="0 converts all records")
    p.add_argument("--review-count", type=int, default=200)
    args = p.parse_args()
    if args.limit < 0 or args.review_count < 0:
        p.error("counts must be nonnegative")
    identity, problems = verify_archive_identity(args.archive, args.manifest)
    if problems:
        p.error("; ".join(problems))
    args.output.mkdir(parents=True, exist_ok=False)
    counts, seen, reviews = Counter(), set(), 0
    with zipfile.ZipFile(args.archive) as archive, (args.output / "sentences.jsonl").open("w") as out, (args.output / "rejected.jsonl").open("w") as rejected, (args.output / "boundary_review.jsonl").open("w") as review:
        names = sorted(n for n in archive.namelist() if n.endswith(".p"))
        if len(names) != len(set(names)):
            raise ValueError("duplicate ZIP member names")
        for name in names[:args.limit or None]:
            counts["examined"] += 1
            try:
                if archive.getinfo(name).file_size > 1_000_000:
                    raise ValueError("oversized member")
                record = decode_record(archive.read(name))
                if record["sent_id"] in seen:
                    raise ValueError("duplicate sentence identity")
                seen.add(record["sent_id"])
                out.write(json.dumps({**record, "source_member": name, "source_sha256": identity["sha256"]}, ensure_ascii=False) + "\n")
                counts["converted"] += 1
                if reviews < args.review_count:
                    try:
                        for proposal in boundary_proposals(record):
                            if reviews >= args.review_count:
                                break
                            proposal["source_sha256"] = identity["sha256"]
                            review.write(json.dumps(proposal, ensure_ascii=False) + "\n")
                            reviews += 1
                    except ValueError:
                        counts["review_surface_unsupported"] += 1
            except ValueError as exc:
                counts["rejected"] += 1
                rejected.write(json.dumps({"member": name, "reason": str(exc)}) + "\n")
    report = {"schema_version": 1, "archive": identity, "counts": dict(counts), "review_proposals": reviews,
              "selection": "sorted ZIP member order; initial review queue is convenience sample, not representative evaluation",
              "expert_reviewed_boundaries": 0, "decoder": "primitive protocol-0 stack interpreter; no pickle.load", "license": "CC-BY-4.0"}
    (args.output / "conversion_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
