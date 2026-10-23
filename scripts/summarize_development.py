#!/usr/bin/env python3
"""Publish compact local development evidence without raw corpora/checkpoints."""

import argparse
import hashlib
import importlib.metadata
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--dcs", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    results = json.loads((args.run / "results.json").read_text())
    dcs = json.loads((args.dcs / "conversion_report.json").read_text())
    for filename in ("results.json", "SUMMARY.md"):
        shutil.copyfile(args.run / filename, args.output / filename)
    shutil.copyfile(args.dcs / "conversion_report.json", args.output / "dcs_conversion.json")
    shutil.copyfile(args.dcs / "rejected.jsonl", args.output / "dcs_rejected.jsonl")
    paths = sorted({*ROOT.glob("src/**/*.py"), *ROOT.glob("src/review/*.html"), *ROOT.glob("scripts/*.py"), *ROOT.glob("scripts/*.cjs"), *ROOT.glob("data/rules/*.jsonl"), *ROOT.glob("data/schemas/*.json")})
    source_hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    environment = {name: importlib.metadata.version(name) for name in ("torch", "numpy", "pytest")}
    (args.output / "reproducibility.json").write_text(json.dumps({"source_file_sha256": source_hashes, "packages": environment}, indent=2) + "\n")
    neural = [row for row in results["results"] if row["seed"] is not None]
    counts = dcs["counts"]
    extra = ["", "## Conversion and Resources", "",
             f"DCS: {counts['examined']:,} examined; {counts['converted']:,} converted; {counts.get('rejected',0)} quarantined. {dcs['review_proposals']} initial review proposals; none expert reviewed.", "",
             f"Tiny ranker: {neural[0]['parameters']:,} parameters on CPU. {len(neural)} neural fits across holdouts, seeds and variants.",
             f"Fit times including development evaluation: {min(r['fit_seconds_including_dev'] for r in neural):.2f} to {max(r['fit_seconds_including_dev'] for r in neural):.2f} seconds per fit.",
             f"Maximum cumulative process RSS: {max(r['process_peak_rss_mib_cumulative'] for r in neural):.1f} MiB. This is not isolated model memory.", "",
             "Raw checkpoints and item predictions remain under the original run directory, excluded from Git. JSON metrics, corpus rejection reasons and code hashes are retained here.",
             "Do not substitute these probe scores for the manuscript's planned independent-corpus results."]
    with (args.output / "SUMMARY.md").open("a") as handle:
        handle.write("\n".join(extra) + "\n")
    print(args.output / "SUMMARY.md")


if __name__ == "__main__":
    main()
