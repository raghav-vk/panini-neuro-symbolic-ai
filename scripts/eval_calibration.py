#!/usr/bin/env python3
"""RLCD stage 1: calibration, abstention and routing on dev (docs/RLCD_TRANSITION_PLAN.md, section 4).

Runs the pre-registered settings of the plan's stage 1 on observed model outputs:

- R: saved H-P2 linear-ranker predictions, one per P-A encoder seed
- E: the three-seed ensemble, as the slow path
- N: the discriminator's per-word P(attested), recomputed from each final checkpoint

Temperatures are fitted by 2-fold cross-fitting and every metric uses out-of-fold
predictions. The test set is never read. scripts/simulate_calibration.py is the earlier
simulation and is not used here.
"""

import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini import calibration as cal

SEEDS = (7, 11, 19)
PREDICTIONS = "strict_right_lemma-linear_features_short_vowel-None-predictions.jsonl"
RUNS = {7: "runs/final-nc-hp2", 11: "runs/eval-pretrain-S-PA-seed11-nc-hp2", 19: "runs/eval-pretrain-S-PA-seed19-nc-hp2"}
TAUS = (0.85, 0.95)
COSTS = (0.01, 0.02, 0.05)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]


def cross_fit(items, folds, nll):
    """Out-of-fold inverse temperature per item, and the beta fitted on each held-in fold."""
    betas = {}
    for held_out in (0, 1):
        betas[held_out] = cal.fit_beta(lambda b: nll([x for x, f in zip(items, folds) if f != held_out], b))
    return [betas[f] for f in folds], betas


def calibration_block(confidence, correct, clusters, resamples):
    def with_interval(fn):
        return {"value": fn(range(len(confidence))),
                "ci95": cal.bootstrap(clusters, fn, resamples=resamples)}
    pick = lambda idx: ([confidence[i] for i in idx], [correct[i] for i in idx])
    return {
        "accuracy": with_interval(lambda idx: sum(correct[i] for i in idx) / len(idx)),
        "mean_confidence": with_interval(lambda idx: sum(confidence[i] for i in idx) / len(idx)),
        "ece_equal_mass": with_interval(lambda idx: cal.ece(*pick(idx))),
        "ece_equal_width": with_interval(lambda idx: cal.ece(*pick(idx), equal_mass=False)),
        "brier": with_interval(lambda idx: cal.brier(*pick(idx))),
        "nll": with_interval(lambda idx: cal.correctness_nll(*pick(idx))),
        "bins_equal_mass": cal.bins(confidence, correct),
        "bins_equal_width": cal.bins(confidence, correct, equal_mass=False),
    }


def ranker(dev, resamples):
    """R per seed, E, abstention, routing and the cost-aware gate."""
    gold = [r["gold_indices"][0] if r["gold_indices"] else None for r in dev]
    clusters = [r["source_group"] for r in dev]
    folds = [cal.fold(c) for c in clusters]
    out, probs, inputs = {"seeds": {}}, {}, {}
    for seed in SEEDS:
        path = ROOT / RUNS[seed] / PREDICTIONS
        rows = read_jsonl(path)
        if [r["example_id"] for r in rows] != [r["example_id"] for r in dev]:
            raise ValueError(f"{path}: examples differ from dev")
        scores = [r["scores"] for r in rows]
        items = list(zip(scores, gold))
        beta, betas = cross_fit(items, folds, cal.ranker_nll)
        raw = [cal.softmax(s) for s in scores]
        scaled = [cal.softmax(s, b) for s, b in zip(scores, beta)]
        correct = [int(g is not None and cal.argmax(s) == g) for s, g in zip(scores, gold)]
        if correct != [int(r["correct"]) for r in rows]:
            raise ValueError(f"{path}: recomputed top-1 differs from the saved predictions")
        probs[seed] = scaled
        inputs[str(seed)] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
        raw_conf = [max(p) for p in raw]
        conf = [max(p) for p in scaled]
        out["seeds"][seed] = {
            "temperature_by_fold": {f: 1 / b for f, b in betas.items()},
            "raw": calibration_block(raw_conf, correct, clusters, resamples),
            "calibrated": calibration_block(conf, correct, clusters, resamples),
            "_confidence": conf, "_correct": correct,
        }
    ensemble = [[sum(probs[s][i][k] for s in SEEDS) / len(SEEDS) for k in range(len(dev[i]["candidates"]))]
                for i in range(len(dev))]
    e_correct = [int(g is not None and cal.argmax(p) == g) for p, g in zip(ensemble, gold)]
    out["ensemble"] = calibration_block([max(p) for p in ensemble], e_correct, clusters, resamples)

    for seed in SEEDS:
        block = out["seeds"][seed]
        conf, correct = block.pop("_confidence"), block.pop("_correct")
        block["abstention"] = {
            "aurc": cal.aurc(conf, correct),
            "risk_coverage": cal.risk_coverage(conf, correct),
            "accuracy_at_coverage": {c: cal.accuracy_at_coverage(conf, correct, c) for c in (0.90, 0.95)},
            "thresholds": [cal.threshold(conf, correct, t) for t in TAUS],
        }
        block["routing_to_ensemble"] = {
            "all_fast": sum(correct) / len(correct), "all_slow": sum(e_correct) / len(e_correct),
            "thresholds": [cal.route(conf, correct, e_correct, t) for t in TAUS],
        }
        gates = {}
        for cost in COSTS:
            per_fold = []
            for held_out in (0, 1):
                fit = [i for i, f in enumerate(folds) if f != held_out]
                score = [i for i, f in enumerate(folds) if f == held_out]
                sub = lambda idx, xs: [xs[i] for i in idx]
                tau = cal.best_tau(sub(fit, conf), sub(fit, correct), sub(fit, e_correct), cost)
                per_fold.append({"held_out_fold": held_out, "tau": tau, "items": len(score),
                                 **{k: v for k, v in cal.route(sub(score, conf), sub(score, correct),
                                                               sub(score, e_correct), tau).items() if k != "tau"}})
            n = sum(p["items"] for p in per_fold)
            learned = {k: sum(p[k] * p["items"] for p in per_fold) / n for k in ("accuracy", "routed")}
            learned["reward"] = learned["accuracy"] - cost * learned["routed"]
            fixed = [{**r, "reward": r["accuracy"] - cost * r["routed"]}
                     for r in (cal.route(conf, correct, e_correct, t) for t in TAUS)]
            gates[cost] = {"learned": learned, "folds": per_fold, "fixed": fixed}
        block["cost_aware_gate"] = gates
    out["inputs"] = inputs
    out["folds"] = {"items_in_fold_1": sum(folds), "items": len(folds), "clusters": len(set(clusters))}
    return out


def noul(args, resamples):
    """N per seed: the discriminator as a calibrated yes/no question, after the reproduction check."""
    from panini.pretraining import corpus_vocabulary, discriminator_words, load_encoder, vowel_confusions
    from panini.rules import load_rules
    texts = [r["text"] for r in read_jsonl(args.dev_sentences)]
    vocabulary = corpus_vocabulary([r["text"] for r in read_jsonl(args.corpus)])
    confusions = vowel_confusions(load_rules(args.rules))
    out = {"inputs": {"dev_sentences_sha256": sha256(args.dev_sentences), "corpus_sha256": sha256(args.corpus)},
           "seeds": {}}
    for seed in SEEDS:
        encoder = ROOT / f"runs/pretrain-S-PA-seed{seed}/encoder.pt"
        record = json.loads((ROOT / f"reports/pretraining-v1/pretrain_S_PA_seed{seed}.json").read_text())
        if record["dev_sha256"] != out["inputs"]["dev_sentences_sha256"]:
            raise ValueError(f"seed {seed}: dev sentences differ from the pretraining record")
        expected = record["history"][-1]["dev"]
        model, _ = load_encoder(encoder, args.device)
        words = discriminator_words(model, texts, confusions, vocabulary, args.device)
        altered = [z > 0 for _, z, y in words if y == 1]
        attested = [z <= 0 for _, z, y in words if y == 0]
        check = {"altered_words": len(altered), "attested_words": len(attested),
                 "altered_accuracy": sum(altered) / len(altered), "attested_accuracy": sum(attested) / len(attested)}
        reproduced = (check["altered_words"] == expected["disc_altered_words"]
                      and check["attested_words"] == expected["disc_attested_words"]
                      and abs(check["altered_accuracy"] - expected["disc_altered_accuracy"]) < 1e-12
                      and abs(check["attested_accuracy"] - expected["disc_attested_accuracy"]) < 1e-12)
        block = {"encoder": str(encoder.relative_to(ROOT)), "encoder_sha256": sha256(encoder),
                 "reproduction": {"observed": check, "expected": {k: expected[k] for k in (
                     "disc_altered_words", "disc_attested_words", "disc_altered_accuracy", "disc_attested_accuracy")},
                     "passed": reproduced}}
        out["seeds"][seed] = block
        if not reproduced:
            continue  # pre-registered: N is not reported for this seed
        # The head predicts "altered"; the Noul asks "attested?", so its logit is minus the head's.
        items = [(-z, 1 - y) for _, z, y in words]
        clusters = [i for i, _, _ in words]
        folds = [cal.fold(f"sentence-{i}") for i in clusters]
        beta, betas = cross_fit(items, folds, cal.binary_nll)

        def top_label(scale):
            p = [cal.sigmoid(b * x) for (x, _), b in zip(items, scale)]
            return [max(q, 1 - q) for q in p], [int((q >= 0.5) == bool(y)) for q, (_, y) in zip(p, items)]
        raw_conf, raw_correct = top_label([1.0] * len(items))
        conf, correct = top_label(beta)
        block["temperature_by_fold"] = {f: 1 / b for f, b in betas.items()}
        block["raw"] = calibration_block(raw_conf, raw_correct, clusters, resamples)
        block["calibrated"] = calibration_block(conf, correct, clusters, resamples)
    return out


def timing(args, dev):
    """Seconds to score every dev row with one encoder (words alone, as in H-P2), per device."""
    import torch
    from panini.pretraining import load_encoder, neural_lexicon_scores
    out = {}
    for device in args.timing_devices:
        if device == "mps" and not torch.backends.mps.is_available():
            continue
        model, _ = load_encoder(ROOT / "runs/pretrain-S-PA-seed7/encoder.pt", device)
        neural_lexicon_scores(model, dev[:64], device, context=False)  # warm-up
        runs = []
        for _ in range(3):
            start = time.perf_counter()
            neural_lexicon_scores(model, dev, device, context=False)
            runs.append(time.perf_counter() - start)
        out[device] = {"seconds": runs, "rows": len(dev), "candidates": sum(len(r["candidates"]) for r in dev)}
    return out


def fmt(block, key, digits=3):
    v = block[key]
    return f"{v['value']:.{digits}f} [{v['ci95'][0]:.{digits}f}, {v['ci95'][1]:.{digits}f}]"


def summary(result):
    lines = ["# RLCD Stage 1: Calibration, Abstention and Routing (Dev)", "",
             "**Dev only.** Pre-registered in `docs/RLCD_TRANSITION_PLAN.md` (stage 1). The test set was not read.",
             "Temperatures are 2-fold cross-fitted; all figures use out-of-fold predictions. Intervals are 95%",
             "cluster bootstrap (1,000 resamples). Produced by `scripts/eval_calibration.py`; full numbers in",
             "`calibration.json`.", "", "## R: H-P2 linear ranker (988 dev examples)", "",
             "| Seed | Version | Accuracy | Mean confidence | ECE (equal mass) | ECE (equal width) | Brier | NLL |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    r = result["ranker"]
    for seed, block in r["seeds"].items():
        for version in ("raw", "calibrated"):
            b = block[version]
            lines.append(f"| {seed} | {version} | {fmt(b, 'accuracy')} | {fmt(b, 'mean_confidence')} | "
                         f"{fmt(b, 'ece_equal_mass')} | {fmt(b, 'ece_equal_width')} | {fmt(b, 'brier')} | {fmt(b, 'nll')} |")
    e = r["ensemble"]
    lines += [f"| E (3 seeds) | calibrated members | {fmt(e, 'accuracy')} | {fmt(e, 'mean_confidence')} | "
              f"{fmt(e, 'ece_equal_mass')} | {fmt(e, 'ece_equal_width')} | {fmt(e, 'brier')} | {fmt(e, 'nll')} |", "",
              "Temperatures by held-out fold: " + "; ".join(
                  f"seed {s}: " + ", ".join(f"{t:.3f}" for t in b["temperature_by_fold"].values())
                  for s, b in r["seeds"].items()), "",
              "## Abstention (calibrated R)", "",
              "| Seed | AURC | Accuracy at 90% coverage | at 95% | τ = 0.85: coverage / accuracy | τ = 0.95: coverage / accuracy |",
              "| --- | --- | --- | --- | --- | --- |"]
    for seed, block in r["seeds"].items():
        a = block["abstention"]
        t = {x["tau"]: x for x in a["thresholds"]}
        lines.append(f"| {seed} | {a['aurc']:.4f} | {a['accuracy_at_coverage'][0.9]:.3f} | {a['accuracy_at_coverage'][0.95]:.3f} | "
                     + " | ".join(f"{t[x]['coverage']:.3f} / {t[x]['accepted_accuracy']:.3f}" for x in TAUS) + " |")
    lines += ["", "## Routing uncertain items to the ensemble", "",
              "| Seed | R everywhere | E everywhere | τ = 0.85: accuracy / routed | τ = 0.95: accuracy / routed |",
              "| --- | --- | --- | --- | --- |"]
    for seed, block in r["seeds"].items():
        g = block["routing_to_ensemble"]
        t = {x["tau"]: x for x in g["thresholds"]}
        lines.append(f"| {seed} | {g['all_fast']:.3f} | {g['all_slow']:.3f} | "
                     + " | ".join(f"{t[x]['accuracy']:.3f} / {t[x]['routed']:.3f}" for x in TAUS) + " |")
    lines += ["", "## Cost-aware gate (offline contextual bandit, full-information feedback)", "",
              "Reward = correct − c × routed. The learned threshold is fitted on one fold and scored on the other.", "",
              "| Seed | c | Learned: reward / accuracy / routed | τ = 0.85: reward | τ = 0.95: reward |",
              "| --- | --- | --- | --- | --- |"]
    for seed, block in r["seeds"].items():
        for cost, g in block["cost_aware_gate"].items():
            l = g["learned"]
            lines.append(f"| {seed} | {cost} | {l['reward']:.4f} / {l['accuracy']:.3f} / {l['routed']:.3f} | "
                         + " | ".join(f"{f['reward']:.4f}" for f in g["fixed"]) + " |")
    n = result.get("noul")
    if n:
        lines += ["", "## N: discriminator as a Noul (\"Is this word attested?\")", "",
                  "| Seed | Reproduced | Version | Accuracy | Mean confidence | ECE (equal mass) | ECE (equal width) | Brier | NLL |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for seed, block in n["seeds"].items():
            if not block["reproduction"]["passed"]:
                lines.append(f"| {seed} | **no** (not reported) | | | | | | | |")
                continue
            for version in ("raw", "calibrated"):
                b = block[version]
                lines.append(f"| {seed} | yes | {version} | {fmt(b, 'accuracy')} | {fmt(b, 'mean_confidence')} | "
                             f"{fmt(b, 'ece_equal_mass')} | {fmt(b, 'ece_equal_width')} | {fmt(b, 'brier')} | {fmt(b, 'nll')} |")
    t = result.get("timing")
    if t:
        lines += ["", "## Compute", "", f"Encoder parameters: {result['parameters']:,}. R uses 1 encoder pass per item, E uses 3.", "",
                  "| Device | Dev rows | Candidates | Seconds per run (3 runs) |", "| --- | --- | --- | --- |"]
        for device, x in t.items():
            lines.append(f"| {device} | {x['rows']} | {x['candidates']} | " + ", ".join(f"{s:.2f}" for s in x["seconds"]) + " |")
        lines.append(f"\nMeasured on {result['platform']}.")
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dev", type=Path, default=ROOT / "data/processed/neural-pretrain-S-PA-seed11-nc/strict_right_lemma/dev.jsonl",
                   help="dev rows with source groups and gold indices (any annotated copy; only these fields are read)")
    p.add_argument("--dev-sentences", type=Path, default=ROOT / "data/processed/pretrain-v1/dev_sentences.jsonl")
    p.add_argument("--corpus", type=Path, default=ROOT / "data/processed/pretrain-v1/P-A.jsonl")
    p.add_argument("--rules", type=Path, default=ROOT / "data/rules/development_sandhi.jsonl")
    p.add_argument("--device", default="mps", help="device for the discriminator (pretraining evaluated on mps)")
    p.add_argument("--timing-devices", nargs="*", default=["mps", "cpu"])
    p.add_argument("--resamples", type=int, default=1000)
    p.add_argument("--skip-noul", action="store_true")
    p.add_argument("--output", type=Path, default=ROOT / "reports/rlcd-stage1")
    args = p.parse_args()
    if any("test" in Path(x).name for x in (args.dev, args.dev_sentences)):
        p.error("stage 1 never reads test data")
    dev = read_jsonl(args.dev)
    result = {"stage": "RLCD stage 1 (dev)", "plan": "docs/RLCD_TRANSITION_PLAN.md", "dev_sha256": sha256(args.dev),
              "platform": f"{platform.platform()}, Python {platform.python_version()}", "parameters": json.loads((ROOT / "reports/pretraining-v1/pretrain_S_PA_seed7.json").read_text())["parameters"],
              "ranker": ranker(dev, args.resamples)}
    if not args.skip_noul:
        result["noul"] = noul(args, args.resamples)
    if args.timing_devices:
        import torch
        result["torch"] = torch.__version__
        result["timing"] = timing(args, dev)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "calibration.json").write_text(json.dumps(result, indent=1) + "\n")
    (args.output / "SUMMARY.md").write_text(summary(result))
    print(summary(result))


if __name__ == "__main__":
    main()
