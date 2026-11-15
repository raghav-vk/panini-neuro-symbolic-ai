#!/usr/bin/env python3
"""The one RLCD stage 3 test run, with the settings frozen by protocol amendment 0.8 (section 11.6).

docs/STAGE3_TEST_AMENDMENT.md. Before reading the test part, it checks that:
- every checkpoint, the training and test files and the Vidyut data release match the hashes
  in reports/rlcd-stage3/frozen_test_settings.json
- the code is committed (no uncommitted change to scripts/ or src/)
- no earlier test result exists (one run only; --rerun-after-crash REASON allows a re-run
  after a crash that produced no results, and records the reason)

It fits nothing on test: J4 and the gate threshold tau are applied as frozen. It reuses the dev
evaluator's functions (scripts/eval_tagger.py, scripts/joint_calibration.py) unchanged, and writes
only to reports/rlcd-stage3/test/.

--smoke runs the same pipeline on dev into a scratch directory, to check the code without
reading test. The test hash is not checked in that mode, and nothing is written under reports/.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from eval_tagger import (CHAPTERS, DEV, accuracy_block, baselines, bootstrap_index, neural_logits, ratio_ci,
                         read_dev, softmax, weighted_ece)
from fetch_vidyut_data import SHA256 as VIDYUT_SHA256
from joint_calibration import EPS, features, logistic_predict, nll_values
from panini.tagger import HEADS, INDEX
from train_tagger import TRAIN, classical_chunks

FROZEN = ROOT / "reports/rlcd-stage3/frozen_test_settings.json"
TEST = ROOT / "data/processed/dcs-conllu-v1/test.jsonl"
OUTPUT = ROOT / "reports/rlcd-stage3/test"
KSS = "Kathāsaritsāgara"
SEEDS = (7, 11, 19)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify(frozen, test_path, smoke=False):
    """Hash mismatches as messages; an empty list means everything matches."""
    problems = []
    for key, run in frozen["runs"].items():
        path = ROOT / run["checkpoint"]
        if not path.exists() or sha256(path) != run["sha256"]:
            problems.append(f"checkpoint {key} differs from the frozen hash")
    if sha256(TRAIN) != frozen["train_sha256"]:
        problems.append("training file differs from the frozen hash")
    if not smoke and sha256(test_path) != frozen["test_sha256"]:
        problems.append("test file differs from the frozen hash")
    if VIDYUT_SHA256 != frozen["vidyut_data_sha256"]:
        problems.append("Vidyut data release differs from the frozen hash")
    return problems


def code_state():
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "scripts", "src"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    return head, dirty


def hypothesis(samples_by_seed, per_seed, direction):
    """Every seed in the stated direction and the 95% interval of the mean excluding 0."""
    mean_samples = np.mean(samples_by_seed, 0)
    ci = [float(np.percentile(mean_samples, 2.5)), float(np.percentile(mean_samples, 97.5))]
    if direction > 0:
        supported = all(x > 0 for x in per_seed) and ci[0] > 0
    else:
        supported = all(x < 0 for x in per_seed) and ci[1] < 0
    return {"per_seed": per_seed, "mean": float(np.mean(per_seed)), "ci95": ci, "supported": supported}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--frozen", type=Path, default=FROZEN)
    p.add_argument("--device", default="mps")
    p.add_argument("--resamples", type=int, default=1000)
    p.add_argument("--rerun-after-crash", metavar="REASON")
    p.add_argument("--smoke", type=Path, metavar="SCRATCH_DIR", help="run on dev into this directory instead")
    args = p.parse_args()
    frozen = json.loads(args.frozen.read_text())
    data, out = (DEV, args.smoke) if args.smoke else (TEST, OUTPUT)
    problems = verify(frozen, data, smoke=bool(args.smoke))
    head, dirty = code_state()
    if dirty and not args.smoke:
        problems.append("uncommitted changes under scripts/ or src/")
    if (out / "stage3_test.json").exists() and not args.smoke and not args.rerun_after_crash:
        problems.append("a test result already exists; the test part is read once")
    if problems:
        raise SystemExit("refusing to run:\n- " + "\n- ".join(problems))

    texts = {json.loads(l)["chapter_id"]: json.loads(l)["text"] for l in CHAPTERS.read_text(encoding="utf-8").splitlines()}
    items, gold, forms, chapter, dropped, truncated = read_dev(data)
    text = np.array([texts[c] for c in chapter])
    gold_idx = np.array([[INDEX[h][g[k]] for k, h in enumerate(HEADS)] for g in gold])
    train_items, _, _, _ = classical_chunks()
    base, train_forms, from_kosha = baselines(train_items, forms, ROOT / "data/external/vidyut-0.4.0/kosha")
    unseen = np.array([f not in train_forms for f in forms])
    counts, word_chapter = bootstrap_index(chapter, args.resamples)
    outside = text != KSS
    every = np.ones(len(gold), bool)
    result = {"amendment": "0.8 (protocol section 11.6, docs/STAGE3_TEST_AMENDMENT.md)",
              "data": "dev (smoke)" if args.smoke else "stage 3 test part", "data_sha256": sha256(data),
              "code_commit": head, "rerun_after_crash": args.rerun_after_crash,
              "deviation": "Frozen mode implemented as scripts/run_stage3_test.py, reusing the dev evaluator's "
                           "functions, not as options of eval_tagger.py and joint_calibration.py (amendment section 4).",
              "words": len(gold), "dropped_words": dropped, "truncated_words": truncated, "chapters": len(set(chapter)),
              "words_outside_kss": int(outside.sum()), "unseen_form_words": int(unseen.sum()), "b2_from_kosha": from_kosha,
              "systems": {}}
    full = {}
    result["systems"]["B2"], full["B2"] = accuracy_block(base["B2"], gold, unseen, text.tolist(), word_chapter, counts)
    nll = {}
    for system in ("N1", "N2", "N3"):
        for seed in SEEDS:
            key = f"{system}-seed{seed}"
            logits, _ = neural_logits(ROOT / frozen["runs"][key]["checkpoint"], items, args.device)
            probs = {h: softmax(logits[h]) for h in HEADS}
            pred_idx = np.stack([probs[h].argmax(1) for h in HEADS], 1)
            pred = [tuple(HEADS[h][i] for h, i in zip(HEADS, row)) for row in pred_idx]
            block, full[key] = accuracy_block(pred, gold, unseen, text.tolist(), word_chapter, counts)
            y = (pred_idx == gold_idx).all(1).astype(float)
            log_p = np.log(np.clip(np.stack([probs[h].max(1) for h in HEADS], 1), EPS, 1))
            confidences = {"J0": np.exp(log_p.sum(1))}
            if system == "N1":
                j4 = frozen["runs"][key]["J4"]
                confidences["J4"] = logistic_predict(features(log_p, "J4"), np.array([j4["a"], j4["b"]]))
            calibration = {}
            for name, conf in confidences.items():
                value, samples = ratio_ci(nll_values(conf, y), every, counts, word_chapter)
                nll[(key, name)] = (value["value"], samples)
                calibration[name] = {"nll": value, "brier": ratio_ci((conf - y) ** 2, every, counts, word_chapter)[0],
                                     "ece_equal_mass": weighted_ece(conf, y, np.ones(len(y))),
                                     "mean_confidence": float(conf.mean()), "accuracy": float(y.mean())}
            if system == "N1":
                tau = frozen["runs"][key]["tau_90_coverage"]
                accept = confidences["J4"] >= tau
                block["gate"] = {"tau": tau, "coverage": float(accept.mean()),
                                 "accepted_full_tag": float(y[accept].mean()) if accept.any() else None}
            block["calibration"] = calibration
            block["role"] = "descriptive" if system == "N3" else "confirmatory"
            result["systems"][key] = block
            print(key, round(block["full_tag"]["value"], 4), flush=True)

    def paired(a_keys, b_keys, mask):
        diffs = [ratio_ci(full[a] - full[b], mask, counts, word_chapter) for a, b in zip(a_keys, b_keys)]
        return [d[0]["value"] for d in diffs], [d[1] for d in diffs]

    n1, n2 = [f"N1-seed{s}" for s in SEEDS], [f"N2-seed{s}" for s in SEEDS]
    hyp = {}
    per, samples = paired(n1, n2, every)
    hyp["T-1"] = {"claim": "N1 beats N2 on full-tag accuracy", **hypothesis(samples, per, +1)}
    per, samples = paired(n1, ["B2"] * 3, every)
    hyp["T-2"] = {"claim": "N1 beats B2 on full-tag accuracy, pooled", **hypothesis(samples, per, +1)}
    per, samples = paired(["B2"] * 3, n1, outside)
    hyp["T-2b"] = {"claim": "B2 beats N1 outside Kathasaritsagara (difference B2 - N1)", **hypothesis(samples, per, +1)}
    per = [nll[(k, "J4")][0] - nll[(k, "J0")][0] for k in n1]
    samples = [nll[(k, "J4")][1] - nll[(k, "J0")][1] for k in n1]
    hyp["T-3"] = {"claim": "frozen J4 has lower NLL than J0 (difference J4 - J0)", **hypothesis(samples, per, -1)}
    coverage = [result["systems"][k]["gate"]["coverage"] for k in n1]
    hyp["T-4"] = {"claim": "test coverage at the frozen tau lies within [0.85, 0.95] for every seed",
                  "per_seed": coverage, "supported": all(0.85 <= c <= 0.95 for c in coverage)}
    result["hypotheses"] = hyp
    out.mkdir(parents=True, exist_ok=True)
    (out / "stage3_test.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    (out / "SUMMARY.md").write_text(summary(result))
    print(summary(result))


def summary(r):
    lines = [f"# RLCD Stage 3: Frozen Test Run (generated; {r['data']})", "",
             f"Amendment {r['amendment']}. Code at commit `{r['code_commit']}`. {r['words']:,} words in {r['chapters']} "
             f"chapters ({r['dropped_words']} without a form dropped); {r['words_outside_kss']:,} outside Kathāsaritsāgara; "
             f"{r['unseen_form_words']:,} with forms unseen in training. Intervals: 95% chapter bootstrap.", "",
             "## Confirmatory hypotheses", ""]
    for name, h in r["hypotheses"].items():
        if "ci95" in h:
            lines.append(f"- **{name}** {h['claim']}: per seed " + ", ".join(f"{x:+.4f}" for x in h["per_seed"])
                         + f"; mean {h['mean']:+.4f} [{h['ci95'][0]:+.4f}, {h['ci95'][1]:+.4f}]; "
                         + ("**supported**" if h["supported"] else "**not supported**"))
        else:
            lines.append(f"- **{name}** {h['claim']}: coverage " + ", ".join(f"{x:.3f}" for x in h["per_seed"])
                         + "; " + ("**supported**" if h["supported"] else "**not supported**"))
    lines += ["", "## Systems", "", "| System | Role | Full tag | Unseen forms | vibhakti | vacana | liṅga | puruṣa | lakāra |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for key, b in r["systems"].items():
        f = lambda x: "—" if x["value"] is None else f"{x['value']:.3f} [{x['ci95'][0]:.3f}, {x['ci95'][1]:.3f}]"
        heads = " | ".join(f"{b['heads'][h]['applicable']['value']:.3f}" for h in HEADS)
        lines.append(f"| {key} | {b.get('role', 'baseline')} | {f(b['full_tag'])} | {f(b['full_tag_unseen_forms'])} | {heads} |")
    lines += ["", "## Calibration and gate (N1; N3 descriptive)", "",
              "| Run | Calibrator | NLL | ECE | Mean conf. / accuracy | Gate coverage | Accepted full tag |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for key, b in r["systems"].items():
        for name, c in b.get("calibration", {}).items():
            gate = b.get("gate") if name == "J4" else None
            lines.append(f"| {key} | {name} | {c['nll']['value']:.4f} | {c['ece_equal_mass']:.4f} | "
                         f"{c['mean_confidence']:.3f} / {c['accuracy']:.3f} | "
                         + (f"{gate['coverage']:.3f} | {gate['accepted_full_tag']:.3f} |" if gate else "— | — |"))
    lines += ["", "## Per text (N1 seed 7 against B2)", "", "| Text | Words | N1 seed 7 | B2 |", "| --- | ---: | ---: | ---: |"]
    pt, b2 = r["systems"]["N1-seed7"]["per_text"], r["systems"]["B2"]["per_text"]
    for t, v in sorted(pt.items(), key=lambda x: -x[1]["words"]):
        lines.append(f"| {t} | {v['words']:,} | {v['full_tag']:.3f} | {b2[t]['full_tag']:.3f} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
