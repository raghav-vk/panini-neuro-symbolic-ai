#!/usr/bin/env python3
"""Joint calibration of the stage 3 whole-tag confidence, as pre-registered.

docs/RLCD_TRANSITION_PLAN.md, "Stage 3 Joint Calibration Pre-Registered Settings". Calibrators
J0 (raw product), JT (per-head temperatures, then the product), J1 (Platt on the log product),
J2 (logistic on the five log head probabilities) and J3 (isotonic on the product), each fitted by
the NLL of whole-tag correctness. The primary scheme is cross-fitting over the stage 3 dev chapter
folds; the secondary one fits on Kathasaritsagara and scores the other texts. Dev only.

Writes reports/rlcd-stage3/joint_calibration.json and JOINT_CALIBRATION.md. With
--calibrators J0 J3 J4 J5 --name platt_calibration it runs the logit Platt calibrators J4 (Platt
on logit c0) and J5 (logistic on the five head logits) of "Stage 3 Logit Platt Calibration
Pre-Registered Settings" and writes platt_calibration.json and PLATT_CALIBRATION.md instead.
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
sys.path.insert(0, str(ROOT / "scripts"))
from panini import calibration as cal
from panini.tagger import HEADS, INDEX
from eval_tagger import (CHAPTERS, DEV, bootstrap_index, fit_beta, neural_logits, ratio_ci, read_dev, softmax,
                         weighted_ece)

RUNS = {"N1": (7, 11, 19), "N3": (7, 11, 19)}
CALIBRATORS = ("J0", "JT", "J1", "J2", "J3", "J4", "J5")
HYPOTHESES = {"H-J1": ("J2", "J0"), "H-J2": ("J2", "JT"), "H-J3": ("J4", "J0"), "H-J4": ("J5", "J0")}
TRANSFER_TEXT = "Kathāsaritsāgara"
EPS = 1e-12


def logistic_fit(x, y, iterations=50):
    """Unpenalised logistic regression by Newton's method; x includes the intercept column."""
    w = np.zeros(x.shape[1])
    for _ in range(iterations):
        p = 1 / (1 + np.exp(-(x @ w)))
        gradient = x.T @ (p - y)
        hessian = (x * (p * (1 - p))[:, None]).T @ x
        step = np.linalg.solve(hessian + 1e-9 * np.eye(len(w)), gradient)
        w -= step
        if np.abs(step).max() < 1e-10:
            break
    return w


def logistic_predict(x, w):
    return 1 / (1 + np.exp(-(x @ w)))


def isotonic_fit(c, y):
    """Pool-adjacent-violators: increasing step function of c; returns (thresholds, values)."""
    order = np.argsort(c, kind="stable")
    cs, ys = c[order], y[order]
    blocks = []  # [sum y, count, max c]
    for ci, yi in zip(cs, ys):
        blocks.append([yi, 1.0, ci])
        while len(blocks) > 1 and blocks[-2][0] / blocks[-2][1] >= blocks[-1][0] / blocks[-1][1]:
            s, n, top = blocks.pop()
            blocks[-1][0] += s
            blocks[-1][1] += n
            blocks[-1][2] = top
    return np.array([b[2] for b in blocks]), np.array([b[0] / b[1] for b in blocks])


def isotonic_predict(c, model):
    tops, values = model
    return values[np.minimum(np.searchsorted(tops, c, side="left"), len(values) - 1)]


def logit(p):
    p = np.clip(p, EPS, 1 - EPS)
    return np.log(p) - np.log1p(-p)


def features(log_p, kind):
    """J1: log c0. J2: log p_i. J4: logit c0. J5: logit p_i. Each with an intercept column."""
    ones = np.ones((len(log_p), 1))
    if kind == "J1":
        x = log_p.sum(1, keepdims=True)
    elif kind == "J2":
        x = log_p
    elif kind == "J4":
        x = logit(np.exp(log_p.sum(1, keepdims=True)))
    else:
        x = logit(np.exp(log_p))
    return np.hstack([x, ones])


def fit_score(kind, train, test, log_p, y, logits, gold_idx):
    """Calibrated confidence of the test words for one calibrator fitted on the train words."""
    if kind == "J0":
        return np.exp(log_p[test].sum(1))
    if kind == "JT":
        out = np.ones(test.sum())
        for k, h in enumerate(HEADS):
            beta = fit_beta(logits[h][train], gold_idx[:, k][train])
            out *= softmax(logits[h][test], beta).max(1)
        return out
    if kind in ("J1", "J2", "J4", "J5"):
        x = features(log_p, kind)
        return logistic_predict(x[test], logistic_fit(x[train], y[train]))
    return isotonic_predict(np.exp(log_p[test].sum(1)), isotonic_fit(np.exp(log_p[train].sum(1)), y[train]))


def nll_values(conf, y):
    c = np.clip(conf, EPS, 1 - EPS)
    return -(y * np.log(c) + (1 - y) * np.log(1 - c))


def block(conf, y, mask, counts, word_chapter):
    every = mask
    nll, nll_samples = ratio_ci(nll_values(conf, y), every, counts, word_chapter)
    brier, _ = ratio_ci((conf - y) ** 2, every, counts, word_chapter)
    sub_c, sub_y = conf[mask], y[mask]
    chapters = word_chapter[mask]
    samples = [weighted_ece(sub_c, sub_y, counts[r][chapters].astype(float)) for r in range(len(counts))]
    c_list, y_list = sub_c.tolist(), sub_y.astype(int).tolist()
    return {"nll": nll, "brier": brier,
            "ece_equal_mass": {"value": weighted_ece(sub_c, sub_y, np.ones(mask.sum())),
                               "ci95": [float(np.percentile(samples, 2.5)), float(np.percentile(samples, 97.5))]},
            "mean_confidence": float(sub_c.mean()), "accuracy": float(sub_y.mean()),
            "aurc": cal.aurc(c_list, y_list),
            "full_tag_at_coverage": {x: cal.accuracy_at_coverage(c_list, y_list, x) for x in (0.90, 0.95)}}, nll_samples


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dev", type=Path, default=DEV)
    p.add_argument("--runs", type=Path, default=ROOT / "runs")
    p.add_argument("--device", default="mps")
    p.add_argument("--resamples", type=int, default=1000)
    p.add_argument("--output", type=Path, default=ROOT / "reports/rlcd-stage3")
    p.add_argument("--calibrators", nargs="+", choices=CALIBRATORS, default=["J0", "JT", "J1", "J2", "J3"])
    p.add_argument("--name", default="joint_calibration", help="report base name")
    args = p.parse_args()
    chosen = tuple(args.calibrators)
    if "test" in args.dev.name:
        p.error("the test part is sealed")
    texts = {json.loads(l)["chapter_id"]: json.loads(l)["text"] for l in CHAPTERS.read_text(encoding="utf-8").splitlines()}
    items, gold, forms, chapter, dropped, _ = read_dev(args.dev)
    text = np.array([texts[c] for c in chapter])
    folds = np.array([hashlib.sha256(f"rlcd-stage3-cal:{c}".encode()).digest()[0] & 1 for c in chapter])
    gold_idx = np.array([[INDEX[h][g[k]] for k, h in enumerate(HEADS)] for g in gold])
    counts, word_chapter = bootstrap_index(chapter, args.resamples)
    largest = [t for t, _ in Counter(text.tolist()).most_common(8)]
    result = {"dev_words": len(gold), "chapters": len(set(chapter)), "transfer_fit_text": TRANSFER_TEXT,
              "transfer_scored_words": int((text != TRANSFER_TEXT).sum()), "runs": {}}
    nll_samples = {}
    for system, seeds in RUNS.items():
        for seed in seeds:
            key = f"{system}-seed{seed}"
            logits, _ = neural_logits(args.runs / f"tagger-{key}/tagger.pt", items, args.device)
            probs = {h: softmax(logits[h]) for h in HEADS}
            pred = np.stack([probs[h].argmax(1) for h in HEADS], 1)
            y = (pred == gold_idx).all(1).astype(float)
            log_p = np.log(np.clip(np.stack([probs[h].max(1) for h in HEADS], 1), EPS, 1))
            run = {"accuracy": float(y.mean()), "cross_fit": {}, "transfer": {}, "per_text_ece": {}}
            everyone = np.ones(len(y), bool)
            for kind in chosen:
                conf = np.empty(len(y))
                for held in (0, 1):
                    conf[folds == held] = fit_score(kind, folds != held, folds == held, log_p, y, logits, gold_idx)
                run["cross_fit"][kind], nll_samples[(key, kind)] = block(conf, y, everyone, counts, word_chapter)
                run["per_text_ece"][kind] = {t: weighted_ece(conf[text == t], y[text == t], np.ones((text == t).sum()))
                                             for t in largest}
                fit_on, score_on = text == TRANSFER_TEXT, text != TRANSFER_TEXT
                transferred = np.zeros(len(y))
                transferred[score_on] = fit_score(kind, fit_on, score_on, log_p, y, logits, gold_idx)
                run["transfer"][kind] = block(transferred, y, score_on, counts, word_chapter)[0]
            result["runs"][key] = run
            print(key, {k: round(run["cross_fit"][k]["nll"]["value"], 4) for k in chosen}, flush=True)
    hyp = {}
    for name, (a, b) in HYPOTHESES.items():
        if a not in chosen or b not in chosen:
            continue
        keys = [f"N1-seed{s}" for s in RUNS["N1"]]
        per_seed = [result["runs"][k]["cross_fit"][a]["nll"]["value"] - result["runs"][k]["cross_fit"][b]["nll"]["value"]
                    for k in keys]
        samples = np.mean([nll_samples[(k, a)] - nll_samples[(k, b)] for k in keys], 0)
        ci = [float(np.percentile(samples, 2.5)), float(np.percentile(samples, 97.5))]
        hyp[name] = {"comparison": f"NLL {a} - {b}", "per_seed": per_seed, "mean": float(np.mean(per_seed)), "ci95": ci,
                     "supported": all(x < 0 for x in per_seed) and ci[1] < 0}
    result["hypotheses"] = hyp
    args.output.mkdir(parents=True, exist_ok=True)
    result["calibrators"] = list(chosen)
    (args.output / f"{args.name}.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    (args.output / f"{args.name.upper()}.md").write_text(summary(result))
    print(summary(result))


def fmt(x, d=4):
    return f"{x['value']:.{d}f} [{x['ci95'][0]:.{d}f}, {x['ci95'][1]:.{d}f}]"


def summary(r):
    lines = ["# RLCD Stage 3: Joint Calibration of the Whole-Tag Confidence (generated)", "",
             f"Dev only, post hoc (pre-registered in `docs/RLCD_TRANSITION_PLAN.md` after the per-head result was seen). "
             f"{r['dev_words']:,} words in {r['chapters']} chapters. Cross-fit: 2 folds over chapters. "
             "Intervals: 95% chapter bootstrap.", "", "## Hypotheses (N1 seeds 7, 11, 19)", ""]
    for name, h in r["hypotheses"].items():
        lines.append(f"- **{name}** ({h['comparison']}): per seed " + ", ".join(f"{x:+.4f}" for x in h["per_seed"])
                     + f"; mean {h['mean']:+.4f} [{h['ci95'][0]:+.4f}, {h['ci95'][1]:+.4f}]; "
                     + ("supported" if h["supported"] else "not supported"))
    for scheme, title in (("cross_fit", "Cross-fit (primary)"), ("transfer", f"Transfer: fitted on {r['transfer_fit_text']}, "
                                                                            f"scored on the other texts ({r['transfer_scored_words']:,} words)")):
        lines += ["", f"## {title}", "",
                  "| Run | Calibrator | NLL | ECE | Brier | Mean conf. / accuracy | AURC | Full tag at 90% / 95% |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        for key, run in r["runs"].items():
            for kind, b in run[scheme].items():
                lines.append(f"| {key} | {kind} | {fmt(b['nll'])} | {fmt(b['ece_equal_mass'])} | {b['brier']['value']:.4f} | "
                             f"{b['mean_confidence']:.3f} / {b['accuracy']:.3f} | {b['aurc']:.4f} | "
                             f"{b['full_tag_at_coverage'][0.9]:.3f} / {b['full_tag_at_coverage'][0.95]:.3f} |")
    chosen = r["calibrators"]
    lines += ["", "## ECE per text (cross-fit, N1 seed 7)", "", "| Text | " + " | ".join(chosen) + " |",
              "| --- | " + " | ".join("---" for _ in chosen) + " |"]
    run = r["runs"]["N1-seed7"]["per_text_ece"]
    for t in run["J0"]:
        lines.append(f"| {t} | " + " | ".join(f"{run[k][t]:.3f}" for k in chosen) + " |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
