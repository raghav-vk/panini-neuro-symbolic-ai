#!/usr/bin/env python3
"""The one sandhi pretraining test run, with the settings frozen by protocol amendment 0.9 (section 11.7).

docs/SANDHI_PRETRAINING_TEST_AMENDMENT.md, as corrected by its erratum. Before reading the test file, it
checks that:
- every encoder, the training, dev and test split files, the rules and the Vidyut data release match
  the hashes in reports/pretraining-v1/frozen_test_settings.json
- the code and the frozen settings are committed (no uncommitted change to scripts/, src/ or the file)
- no earlier test result exists (one run only; --rerun-after-crash REASON allows a re-run after a crash
  that produced no results, and records the reason)

It then, for each frozen encoder, scores every candidate's two words alone (and, descriptively, in their
sentence) on the training split and the scored file, trains the linear_features_short_vowel arms (seed 7)
on the training split, and scores the test file. It selects and tunes nothing, and writes only to
reports/pretraining-v1/test/.

--smoke runs the same pipeline on dev into a scratch directory, to check the code against the recorded
dev results without reading test. The test hash is not checked in that mode, and nothing is written
under reports/.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from compare_paired import exact_mcnemar
from fetch_vidyut_data import SHA256 as VIDYUT_SHA256
from panini.calibration import bootstrap
from panini.experiment_data import digest
from panini.pretraining import load_encoder, neural_lexicon_scores
from panini.ranking import LinearBaseline, metrics

FROZEN = ROOT / "reports/pretraining-v1/frozen_test_settings.json"
RULES = ROOT / "data/rules/development_sandhi.jsonl"
OUTPUT = ROOT / "reports/pretraining-v1/test"
RESULT = "sandhi_pretraining_test.json"
PA_SEEDS = (7, 11, 19)
MARGIN = 0.010
COVERAGE_BAND = (0.71, 0.86)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]


def verify(frozen, smoke=False):
    """Hash mismatches as messages; an empty list means everything matches."""
    problems = []
    for key, encoder in frozen["encoders"].items():
        path = ROOT / encoder["path"]
        if not path.exists() or sha256(path) != encoder["sha256"]:
            problems.append(f"encoder {key} differs from the frozen hash")
    split_dir = ROOT / frozen["split_dir"]
    for name in ("train", "dev") if smoke else ("train", "dev", "test"):
        path = split_dir / f"{name}.jsonl"
        if not path.exists() or sha256(path) != frozen["split_sha256"][name]:
            problems.append(f"{name} split file differs from the frozen hash")
    if digest(RULES.read_text()) != frozen["rules_sha256"]:
        problems.append("rules differ from the frozen hash")
    if VIDYUT_SHA256 != frozen["vidyut_data_sha256"]:
        problems.append("Vidyut data release differs from the frozen hash")
    return problems


def code_state():
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "scripts", "src", str(FROZEN.relative_to(ROOT))],
                           cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return head, dirty


def annotate(rows, scores):
    """Copies of rows whose candidates carry neural_left and neural_right, in candidate order."""
    it = iter(scores)
    out = []
    for row in rows:
        candidates = []
        for c in row["candidates"]:
            left, right = next(it)
            candidates.append({**c, "neural_left": left, "neural_right": right})
        out.append({**row, "candidates": candidates})
    return out


def run_arm(train, scored, kosha, neural, seed):
    start = time.perf_counter()
    model = LinearBaseline(train, kosha, seed=seed, neural=neural)
    report, predictions = metrics(scored, [model.score(r) for r in scored])
    correct = np.array([p["correct"] for p in predictions], float)
    confidence = np.array([p["confidence"] for p in predictions])
    per_rule = {}
    for row, hit in zip(scored, correct):
        entry = per_rule.setdefault(row["rule_id"], [0, 0])
        entry[0] += 1
        entry[1] += int(hit)
    block = {"top1": report["top1"], "top1_tie_averaged": report["top1_tie_averaged"],
             "candidate_recall": report["candidate_recall"], "tied_top_rows": report["tied_top_rows"],
             "per_rule": {k: {"examples": n, "top1": c / n} for k, (n, c) in sorted(per_rule.items())},
             "seconds": time.perf_counter() - start}
    return block, correct, confidence


def gate(confidence, correct, tau):
    accept = confidence >= tau
    return {"tau": tau, "coverage": float(accept.mean()),
            "accepted_accuracy": float(correct[accept].mean()) if accept.any() else None}


def paired(arms, reference, clusters, resamples):
    """Per-seed differences, McNemar, and the source-group bootstrap interval of the seed-mean difference."""
    diffs = np.stack([a - reference for a in arms])
    per_seed = [float(d.mean()) for d in diffs]
    mcnemar = [exact_mcnemar(int(((a == 1) & (reference == 0)).sum()), int(((a == 0) & (reference == 1)).sum()))
               for a in arms]
    seed_mean = diffs.mean(0)
    ci = bootstrap(clusters, lambda idx: float(seed_mean[idx].mean()), resamples=resamples, seed=1729)
    return {"per_seed": per_seed, "mean": float(np.mean(per_seed)), "ci95": ci, "mcnemar_p": mcnemar}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--frozen", type=Path, default=FROZEN)
    p.add_argument("--device", default="mps", help="device for the encoder word scores")
    p.add_argument("--resamples", type=int, default=1000)
    p.add_argument("--rerun-after-crash", metavar="REASON")
    p.add_argument("--smoke", type=Path, metavar="SCRATCH_DIR", help="run on dev into this directory instead")
    args = p.parse_args()
    frozen = json.loads(args.frozen.read_text())
    scored_name, out = ("dev", args.smoke) if args.smoke else ("test", OUTPUT)
    problems = verify(frozen, smoke=bool(args.smoke))
    head, dirty = code_state()
    if dirty and not args.smoke:
        problems.append("uncommitted changes under scripts/, src/ or the frozen settings")
    if (out / RESULT).exists() and not args.rerun_after_crash:
        problems.append("a result already exists here; the test file is read once")
    if problems:
        raise SystemExit("refusing to run:\n- " + "\n- ".join(problems))

    split_dir = ROOT / frozen["split_dir"]
    train = read_jsonl(split_dir / "train.jsonl")
    scored = read_jsonl(split_dir / f"{scored_name}.jsonl")
    clusters = [r["source_group"] for r in scored]
    seed = frozen["ranker"]["seed"]
    tau = frozen["gate"]["tau"]
    result = {"amendment": "0.9 (protocol section 11.7, docs/SANDHI_PRETRAINING_TEST_AMENDMENT.md, with its erratum)",
              "data": "dev (smoke)" if args.smoke else "right-word holdout test file",
              "data_sha256": sha256(split_dir / f"{scored_name}.jsonl"), "code_commit": head,
              "rerun_after_crash": args.rerun_after_crash, "device": args.device, "examples": len(scored),
              "source_groups": len(set(clusters)), "train_examples": len(train), "arms": {}}
    correct, confidence = {}, {}
    block, correct["R-K"], _ = run_arm(train, scored, kosha=True, neural=False, seed=seed)
    result["arms"]["R-K"] = {**block, "role": "reference"}
    print("R-K", round(block["top1"], 4), flush=True)

    plan = [(f"P-A-seed{s}", f"seed{s}", True, "confirmatory") for s in PA_SEEDS]
    plan += [(f"P-A-seed{s}", f"seed{s}-in-sentence", False, "descriptive") for s in PA_SEEDS]
    plan += [("P-B-seed7", "PB", True, "descriptive")]
    loaded = {}
    for encoder_key, suffix, alone, role in plan:
        if encoder_key not in loaded:
            loaded.clear()
            loaded[encoder_key] = load_encoder(ROOT / frozen["encoders"][encoder_key]["path"], args.device)[0]
        model = loaded[encoder_key]
        start = time.perf_counter()
        train_n = annotate(train, neural_lexicon_scores(model, train, args.device, context=not alone))
        scored_n = annotate(scored, neural_lexicon_scores(model, scored, args.device, context=not alone))
        scoring_seconds = time.perf_counter() - start
        for arm, kosha in (("R-N", False), ("R-KN", True)):
            key = f"{arm}-{suffix}"
            block, correct[key], confidence[key] = run_arm(train_n, scored_n, kosha=kosha, neural=True, seed=seed)
            block.update(role=role, encoder=encoder_key, words_scored="alone" if alone else "in sentence",
                         word_scoring_seconds=scoring_seconds)
            if arm == "R-KN":
                block["gate"] = gate(confidence[key], correct[key], tau)
            result["arms"][key] = block
            print(key, round(block["top1"], 4), flush=True)

    for key in result["arms"]:
        if key != "R-K":
            a, r = correct[key], correct["R-K"]
            result["arms"][key]["vs_R-K"] = {"difference": float((a - r).mean()), "wins": int(((a == 1) & (r == 0)).sum()),
                                             "losses": int(((a == 0) & (r == 1)).sum()),
                                             "mcnemar_p": exact_mcnemar(int(((a == 1) & (r == 0)).sum()),
                                                                        int(((a == 0) & (r == 1)).sum()))}
    rn = [correct[f"R-N-seed{s}"] for s in PA_SEEDS]
    rkn = [correct[f"R-KN-seed{s}"] for s in PA_SEEDS]
    hyp = {}
    d = paired(rn, correct["R-K"], clusters, args.resamples)
    hyp["T-P1"] = {"claim": f"R-N is non-inferior to R-K (margin {MARGIN})", **d,
                   "supported": all(x > -MARGIN for x in d["per_seed"]) and d["ci95"][0] > -MARGIN}
    hyp["T-P1s"] = {"claim": "R-N beats R-K", **d, "supported": all(x > 0 for x in d["per_seed"]) and d["ci95"][0] > 0}
    d = paired(rkn, correct["R-K"], clusters, args.resamples)
    hyp["T-P2"] = {"claim": "R-KN beats R-K", **d, "supported": all(x > 0 for x in d["per_seed"]) and d["ci95"][0] > 0}
    coverage = [result["arms"][f"R-KN-seed{s}"]["gate"]["coverage"] for s in PA_SEEDS]
    hyp["T-P3"] = {"claim": f"R-KN coverage at tau = {tau} lies within {list(COVERAGE_BAND)} for every seed",
                   "per_seed": coverage,
                   "supported": all(COVERAGE_BAND[0] <= c <= COVERAGE_BAND[1] for c in coverage)}
    result["hypotheses"] = hyp
    out.mkdir(parents=True, exist_ok=True)
    (out / RESULT).write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    (out / "SUMMARY.md").write_text(summary(result))
    print(summary(result))


def summary(r):
    lines = [f"# Sandhi Pretraining: Frozen Test Run (generated; {r['data']})", "",
             f"Amendment {r['amendment']}. Code at commit `{r['code_commit']}`. {r['examples']} examples in "
             f"{r['source_groups']} source groups; intervals are 95% source-group bootstrap intervals of the "
             "seed-mean difference against R-K. No multiplicity correction.", "", "## Confirmatory hypotheses", ""]
    for name, h in r["hypotheses"].items():
        verdict = "**supported**" if h["supported"] else "**not supported**"
        if "ci95" in h:
            lines.append(f"- **{name}** {h['claim']}: per seed " + ", ".join(f"{x:+.4f}" for x in h["per_seed"])
                         + f"; mean {h['mean']:+.4f} [{h['ci95'][0]:+.4f}, {h['ci95'][1]:+.4f}]; McNemar p "
                         + ", ".join(f"{x:.2g}" for x in h["mcnemar_p"]) + f"; {verdict}")
        else:
            lines.append(f"- **{name}** {h['claim']}: coverage " + ", ".join(f"{x:.3f}" for x in h["per_seed"]) + f"; {verdict}")
    lines += ["", "## Arms", "",
              "| Arm | Role | Words scored | Top-1 | Tie-averaged | vs R-K | McNemar p | Gate coverage | Accepted accuracy |",
              "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for key, a in r["arms"].items():
        vs = a.get("vs_R-K")
        g = a.get("gate")
        lines.append(f"| {key} | {a['role']} | {a.get('words_scored', '—')} | {a['top1']:.3f} | {a['top1_tie_averaged']:.3f} | "
                     + (f"{vs['difference']:+.3f} | {vs['mcnemar_p']:.2g} | " if vs else "— | — | ")
                     + (f"{g['coverage']:.3f} | {g['accepted_accuracy']:.3f} |" if g else "— | — |"))
    lines += ["", "## Per rule (top-1)", ""]
    keys = ["R-K"] + [f"R-N-seed{s}" for s in PA_SEEDS] + [f"R-KN-seed{s}" for s in PA_SEEDS]
    lines += ["| Rule | Examples | " + " | ".join(keys) + " |", "| --- | ---: |" + " ---: |" * len(keys)]
    for rule, v in r["arms"]["R-K"]["per_rule"].items():
        lines.append(f"| {rule} | {v['examples']} | " + " | ".join(f"{r['arms'][k]['per_rule'][rule]['top1']:.3f}" for k in keys) + " |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
