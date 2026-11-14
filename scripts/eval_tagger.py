#!/usr/bin/env python3
"""Evaluate the RLCD stage 3 baselines and tagger runs on dev, as pre-registered.

docs/RLCD_TRANSITION_PLAN.md, "Stage 3 Training Pre-Registered Settings": B0 to B2 and the
N1 to N3 runs; full-tag and per-head accuracy, unseen forms, per text, calibration with
cross-fitted per-head temperatures, abstention, compute, and the H-S3-1 and H-S3-2 decision
rules with chapter-bootstrap intervals. The test part is never read.

Writes reports/rlcd-stage3/tagger_dev.json and SUMMARY_TAGGER.md.
"""

import argparse
import hashlib
import json
import platform
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from panini import calibration as cal
from panini.lexicon import pausal_variants
from panini.tagger import HEADS, INDEX, batch, chunks, make_tagger, sentence_items, tag
from train_tagger import CHAPTERS, classical_chunks

DEV = ROOT / "data/processed/dcs-conllu-v1/dev.jsonl"
SYSTEMS = {"N1": "pretrained, cross-entropy", "N2": "scratch, cross-entropy", "N3": "pretrained, Brier"}
SEEDS = (7, 11, 19)
LAKARA = {"Lat": "Lat", "Lan": "Lan", "VidhiLin": "VidhiLin", "Lot": "Lot", "AshirLin": "AshirLin", "Lrn": "Lrn",
          "Lit": "Lit|Lun", "Lun": "Lit|Lun", "Lrt": "Lrt|Lut", "Lut": "Lrt|Lut", "Let": "other"}
NONE = ("NONE",) * 5


def read_dev(path):
    """Dev words with a form: forms per chunk, gold tags, chapter of each word, dropped count."""
    items, gold, forms, chapter, dropped, truncated = [], [], [], [], 0, 0
    for line in Path(path).open(encoding="utf-8"):
        s = json.loads(line)
        kept, empty = sentence_items(s["words"])
        dropped += empty
        pieces, cut = chunks([f for _, f in kept])
        truncated += cut
        for piece in pieces:
            tags = [tag(s["words"][kept[j][0]]) for j, _ in piece]
            items.append(([f for _, f in piece], tags))
            gold += tags
            forms += [f for _, f in piece]
            chapter += [s["chapter_id"]] * len(piece)
    return items, gold, forms, chapter, dropped, truncated


def kosha_tags(kosha, form):
    """Tag tuples of every kosha analysis of the form (pausal variants)."""
    out = set()
    for variant in pausal_variants(form):
        for e in kosha.get(variant):
            if getattr(e, "is_avyaya", False):
                out.add(NONE)
            elif hasattr(e, "pratipadika_entry"):
                out.add((e.vibhakti.name, e.vacana.name, e.linga.name, "NONE", "NONE"))
            elif hasattr(e, "dhatu_entry"):
                out.add(("NONE", e.vacana.name, "NONE", e.purusha.name, LAKARA.get(e.lakara.name, "other")))
    return out


def baselines(train_items, forms, kosha_path):
    by_form, prior = {}, Counter()
    for chunk_forms, tags in train_items:
        for f, t in zip(chunk_forms, tags):
            by_form.setdefault(f, Counter())[t] += 1
            prior[t] += 1
    majority = tuple(Counter(t[k] for t in prior.elements()).most_common(1)[0][0] for k in range(5))
    lookup = {f: max(c.items(), key=lambda x: (x[1], x[0]))[0] for f, c in by_form.items()}
    from vidyut.kosha import Kosha
    kosha = Kosha(str(kosha_path))
    b2, from_kosha = [], 0
    for f in forms:
        if f in lookup:
            b2.append(lookup[f])
            continue
        options = kosha_tags(kosha, f)
        if options:
            from_kosha += 1
            b2.append(max(options, key=lambda t: (prior[t], t)))
        else:
            b2.append(majority)
    return {"B0": [majority] * len(forms), "B1": [lookup.get(f, majority) for f in forms], "B2": b2}, set(lookup), from_kosha


def neural_logits(path, items, device, size=64):
    """Per-head logits for every dev word, in order: {head: (words, options)}."""
    import torch
    state = torch.load(path, map_location="cpu", weights_only=False)
    model = make_tagger(None, dropout=0.0)
    model.load_state_dict(state["state_dict"])
    model.to(device).eval()
    out = {h: [] for h in HEADS}
    order = sorted(range(len(items)), key=lambda i: len(" ".join(items[i][0])))
    parts = {}
    with torch.no_grad():
        for start in range(0, len(order), size):
            group = [items[i] for i in order[start:start + size]]
            tokens, ids, _, words = batch(group, device, labelled=False)
            logits = model(tokens, ids, words)
            for k, i in enumerate(order[start:start + size]):
                n = len(items[i][0])
                parts[i] = {h: logits[h][k, :n].float().cpu().numpy() for h in HEADS}
    for i in range(len(items)):
        for h in HEADS:
            out[h].append(parts[i][h])
    return {h: np.concatenate(v) for h, v in out.items()}, state["record"]


def softmax(x, beta=1.0):
    z = beta * (x - x.max(1, keepdims=True))
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


def fit_beta(logits, y):
    def nll(beta):
        z = beta * logits
        z = z - z.max(1, keepdims=True)
        return float((np.log(np.exp(z).sum(1)) - z[np.arange(len(y)), y]).mean())
    return cal.fit_beta(nll)


def bootstrap_index(chapter, resamples=1000, seed=1729):
    """Chapter multiplicities per resample: (resamples, chapters) and the chapter index of every word."""
    keys = sorted(set(chapter))
    pos = {k: i for i, k in enumerate(keys)}
    word_chapter = np.array([pos[c] for c in chapter])
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(keys), size=(resamples, len(keys)))
    counts = np.stack([np.bincount(d, minlength=len(keys)) for d in draws])
    return counts, word_chapter


def ratio_ci(values, mask, counts, word_chapter):
    """Point value and 95% interval of mean(values[mask]) under chapter resampling."""
    num = np.bincount(word_chapter[mask], weights=values[mask], minlength=counts.shape[1])
    den = np.bincount(word_chapter[mask], minlength=counts.shape[1]).astype(float)
    if den.sum() == 0:
        return {"value": None, "ci95": None}, np.zeros(len(counts))
    point = num.sum() / den.sum()
    samples = (counts @ num) / np.maximum(counts @ den, 1)
    return {"value": float(point), "ci95": [float(np.percentile(samples, 2.5)), float(np.percentile(samples, 97.5))]}, samples


def weighted_ece(conf, correct, weights, bins=10):
    order = np.argsort(conf, kind="stable")
    c, y, w = conf[order], correct[order], weights[order]
    cum = np.cumsum(w) - w
    which = np.minimum((cum / w.sum() * bins).astype(int), bins - 1)
    W = np.bincount(which, weights=w, minlength=bins)
    C = np.bincount(which, weights=w * c, minlength=bins)
    A = np.bincount(which, weights=w * y, minlength=bins)
    keep = W > 0
    return float((np.abs(A[keep] - C[keep])).sum() / w.sum())


def accuracy_block(pred, gold, unseen, chapter_text, word_chapter, counts):
    pred_a, gold_a = np.array(pred), np.array(gold)
    full = (pred_a == gold_a).all(1).astype(float)
    every = np.ones(len(gold), bool)
    block = {"full_tag": ratio_ci(full, every, counts, word_chapter)[0],
             "full_tag_unseen_forms": ratio_ci(full, unseen, counts, word_chapter)[0], "heads": {}}
    for k, h in enumerate(HEADS):
        right = (pred_a[:, k] == gold_a[:, k]).astype(float)
        applicable = gold_a[:, k] != "NONE"
        predicted_none = pred_a[:, k] == "NONE"
        values = [v for v in HEADS[h] if (gold_a[:, k] == v).any()]
        block["heads"][h] = {
            "applicable": ratio_ci(right, applicable, counts, word_chapter)[0],
            "none_predictions": float(right[predicted_none].mean()) if predicted_none.any() else None,
            "macro": float(np.mean([right[gold_a[:, k] == v].mean() for v in values])),
        }
    per_text = {}
    for text in sorted(set(chapter_text)):
        m = np.array([t == text for t in chapter_text])
        per_text[text] = {"words": int(m.sum()), "full_tag": float(full[m].mean())}
    block["per_text"] = per_text
    return block, full


def calibration_block(logits, gold, chapter, counts, word_chapter):
    folds = np.array([hashlib.sha256(f"rlcd-stage3-cal:{c}".encode()).digest()[0] & 1 for c in chapter])
    y = {h: np.array([INDEX[h][g[k]] for g in gold]) for k, h in enumerate(HEADS)}
    temps, raw_top, cal_top = {}, [], []
    for h in HEADS:
        temps[h], top = {}, np.empty(len(gold))
        for held in (0, 1):
            b = fit_beta(logits[h][folds != held], y[h][folds != held])
            temps[h][held] = 1 / b
            top[folds == held] = softmax(logits[h][folds == held], b).max(1)
        raw_top.append(softmax(logits[h]).max(1))
        cal_top.append(top)
    pred = np.stack([logits[h].argmax(1) for h in HEADS], 1)
    truth = np.stack([y[h] for h in HEADS], 1)
    correct = (pred == truth).all(1).astype(float)
    out = {"temperature_by_fold": temps}
    for name, tops in (("raw", raw_top), ("calibrated", cal_top)):
        conf = np.prod(np.stack(tops, 1), 1)
        w = np.ones(len(conf))  # unweighted point estimate
        samples = [weighted_ece(conf, correct, counts[r][word_chapter].astype(float)) for r in range(len(counts))]
        out[name] = {
            "mean_confidence": float(conf.mean()),
            "ece_equal_mass": {"value": weighted_ece(conf, correct, w),
                               "ci95": [float(np.percentile(samples, 2.5)), float(np.percentile(samples, 97.5))]},
            "brier": float(((conf - correct) ** 2).mean()),
            "nll": float(-np.mean(np.log(np.clip(np.where(correct == 1, conf, 1 - conf), 1e-12, 1)))),
        }
        if name == "calibrated":
            c, y_ = conf.tolist(), correct.astype(int).tolist()
            out["abstention"] = {"aurc": cal.aurc(c, y_),
                                 "full_tag_at_coverage": {x: cal.accuracy_at_coverage(c, y_, x) for x in (0.90, 0.95)}}
    return out


def timing(path, items, devices):
    import torch
    out = {}
    for device in devices:
        if device == "mps" and not torch.backends.mps.is_available():
            continue
        neural_logits(path, items[:256], device)
        runs = []
        for _ in range(3):
            start = time.perf_counter()
            neural_logits(path, items, device)
            runs.append(round(time.perf_counter() - start, 2))
        out[device] = runs
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dev", type=Path, default=DEV)
    p.add_argument("--runs", type=Path, default=ROOT / "runs")
    p.add_argument("--kosha", type=Path, default=ROOT / "data/external/vidyut-0.4.0/kosha")
    p.add_argument("--device", default="mps")
    p.add_argument("--timing-devices", nargs="*", default=["mps", "cpu"])
    p.add_argument("--resamples", type=int, default=1000)
    p.add_argument("--output", type=Path, default=ROOT / "reports/rlcd-stage3")
    args = p.parse_args()
    if "test" in args.dev.name:
        p.error("the test part is sealed")
    rows = {json.loads(l)["chapter_id"]: json.loads(l)["text"] for l in CHAPTERS.read_text(encoding="utf-8").splitlines()}
    items, gold, forms, chapter, dropped, truncated = read_dev(args.dev)
    train_items, _, _, _ = classical_chunks()
    base, train_forms, from_kosha = baselines(train_items, forms, args.kosha)
    unseen = np.array([f not in train_forms for f in forms])
    counts, word_chapter = bootstrap_index(chapter, args.resamples)
    chapter_text = [rows[c] for c in chapter]
    result = {"dev": str(args.dev.relative_to(ROOT)) if args.dev.is_relative_to(ROOT) else str(args.dev), "dev_sha256": hashlib.sha256(args.dev.read_bytes()).hexdigest(),
              "words": len(gold), "dropped_words": dropped, "truncated_words": truncated, "chapters": len(set(chapter)),
              "unseen_form_words": int(unseen.sum()), "b2_from_kosha": from_kosha,
              "platform": platform.platform(), "systems": {}}
    full = {}
    for name, pred in base.items():
        result["systems"][name], full[name] = accuracy_block(pred, gold, unseen, chapter_text, word_chapter, counts)
    for system in SYSTEMS:
        for seed in SEEDS:
            path = args.runs / f"tagger-{system}-seed{seed}/tagger.pt"
            if not path.exists():
                continue
            logits, record = neural_logits(path, items, args.device)
            pred = [tuple(HEADS[h][i] for h, i in zip(HEADS, row))
                    for row in np.stack([logits[h].argmax(1) for h in HEADS], 1)]
            key = f"{system}-seed{seed}"
            block, full[key] = accuracy_block(pred, gold, unseen, chapter_text, word_chapter, counts)
            block["calibration"] = calibration_block(logits, gold, chapter, counts, word_chapter)
            block["training"] = {k: record[k] for k in ("steps", "seconds", "parameters", "chunks", "dropped_words")}
            result["systems"][key] = block
    every = np.ones(len(gold), bool)
    hyp = {}
    for name, (a, b) in {"H-S3-1": ("N1", "B2"), "H-S3-2": ("N1", "N2")}.items():
        keys = [f"{a}-seed{s}" for s in SEEDS]
        refs = [b] * 3 if b.startswith("B") else [f"{b}-seed{s}" for s in SEEDS]
        if not all(k in full for k in keys + refs):
            continue
        diffs = [ratio_ci(full[k] - full[r], every, counts, word_chapter) for k, r in zip(keys, refs)]
        mean_samples = np.mean([d[1] for d in diffs], 0)
        ci = [float(np.percentile(mean_samples, 2.5)), float(np.percentile(mean_samples, 97.5))]
        per_seed = [d[0]["value"] for d in diffs]
        hyp[name] = {"comparison": f"{a} - {b}", "per_seed_difference": per_seed,
                     "mean_difference": float(np.mean(per_seed)), "ci95": ci,
                     "supported": all(x > 0 for x in per_seed) and ci[0] > 0}
    result["hypotheses"] = hyp
    first = args.runs / "tagger-N1-seed7/tagger.pt"
    if args.timing_devices and first.exists():
        result["timing_seconds"] = timing(first, items, args.timing_devices)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "tagger_dev.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    (args.output / "SUMMARY_TAGGER.md").write_text(summary(result))
    print(summary(result))


def fmt(x):
    if x["value"] is None:
        return "—"
    return f"{x['value']:.3f} [{x['ci95'][0]:.3f}, {x['ci95'][1]:.3f}]"


def summary(r):
    lines = ["# RLCD Stage 3: Tagger on Dev (generated)", "",
             f"Dev only; pre-registered in `docs/RLCD_TRANSITION_PLAN.md`. {r['words']:,} words in {r['chapters']} chapters "
             f"({r['dropped_words']} without a form dropped); {r['unseen_form_words']:,} words have forms unseen in training. "
             "Intervals: 95% chapter bootstrap.", "",
             "| System | Full tag | Full tag, unseen forms | vibhakti | vacana | liṅga | puruṣa | lakāra |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for name, b in r["systems"].items():
        heads = " | ".join(f"{b['heads'][h]['applicable']['value']:.3f}" for h in HEADS)
        lines.append(f"| {name} | {fmt(b['full_tag'])} | {fmt(b['full_tag_unseen_forms'])} | {heads} |")
    lines += ["", "Head columns: accuracy on words whose gold value is not NONE.", "", "## Hypotheses", ""]
    for name, h in r["hypotheses"].items():
        lines.append(f"- **{name}** ({h['comparison']}): per seed " + ", ".join(f"{x:+.3f}" for x in h["per_seed_difference"])
                     + f"; mean {h['mean_difference']:+.3f} [{h['ci95'][0]:+.3f}, {h['ci95'][1]:+.3f}]; "
                     + ("supported" if h["supported"] else "not supported"))
    neural = {k: v for k, v in r["systems"].items() if "calibration" in v}
    if neural:
        lines += ["", "## Calibration and abstention (word confidence = product of five head probabilities)", "",
                  "| Run | ECE raw | ECE calibrated | Brier cal. | NLL cal. | AURC | Full tag at 90% / 95% coverage | Train min |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        for k, v in neural.items():
            c = v["calibration"]
            a = c["abstention"]
            lines.append(f"| {k} | {fmt(c['raw']['ece_equal_mass'])} | {fmt(c['calibrated']['ece_equal_mass'])} | "
                         f"{c['calibrated']['brier']:.4f} | {c['calibrated']['nll']:.4f} | {a['aurc']:.4f} | "
                         f"{a['full_tag_at_coverage'][0.9]:.3f} / {a['full_tag_at_coverage'][0.95]:.3f} | "
                         f"{v['training']['seconds'] / 60:.1f} |")
    if "timing_seconds" in r:
        lines += ["", "Tagging all dev words with one encoder (N1 seed 7), seconds per run: "
                  + "; ".join(f"{d}: {', '.join(map(str, t))}" for d, t in r["timing_seconds"].items())]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
