#!/usr/bin/env python3
"""Copy prepared train and dev splits, adding the pretrained encoder's word scores (plan section 6.1).

Each candidate gains neural_left and neural_right: the discriminator's log probability that the word is
attested, not a rule-guided near miss. The test file is not read or written, so runs on this data are
dev-only until the settings are frozen (docs/PRETRAINING_PLAN.md section 8).
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.pretraining import load_encoder, neural_lexicon_scores


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", type=Path, required=True, help="prepare_experiment.py or annotate_lexicon.py output")
    p.add_argument("--split", default="strict_right_lemma")
    p.add_argument("--encoder", type=Path, required=True, help="scripts/pretrain.py checkpoint")
    p.add_argument("--no-context", action="store_true", help="score the two words alone, not in their sentence")
    p.add_argument("--device", default="mps")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    model, state = load_encoder(args.encoder, args.device)
    manifest = json.loads((args.data / "manifest.json").read_text())
    audit = manifest["splits"][args.split]
    (args.output / args.split).mkdir(parents=True, exist_ok=False)
    stats, hashes = {}, {}
    for name in ("train", "dev"):
        rows = [json.loads(line) for line in (args.data / args.split / f"{name}.jsonl").read_text().splitlines()]
        scores = iter(neural_lexicon_scores(model, rows, args.device, context=not args.no_context))
        for row in rows:
            for candidate in row["candidates"]:
                candidate["neural_left"], candidate["neural_right"] = next(scores)
        path = args.output / args.split / f"{name}.jsonl"
        path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        gold = [r["candidates"][i] for r in rows for i in r["gold_indices"]]
        other = [c for r in rows for i, c in enumerate(r["candidates"]) if i not in r["gold_indices"]]
        mean = lambda xs: sum(xs) / len(xs) if xs else None
        stats[name] = {"candidates": len(gold) + len(other),
                       "mean_neural_right_gold": mean([c["neural_right"] for c in gold]),
                       "mean_neural_right_other": mean([c["neural_right"] for c in other])}
    audit = {**audit, "file_sha256": hashes, "test_withheld": True}
    manifest["splits"] = {args.split: audit}
    manifest["neural_lexicon"] = {"encoder": str(args.encoder), "encoder_sha256": hashlib.sha256(args.encoder.read_bytes()).hexdigest(),
                                  "encoder_step": state.get("step"), "corpus_sha256": state["corpus_sha256"],
                                  "objectives": state["objectives"], "context": not args.no_context,
                                  "fields": ["neural_left", "neural_right"], "stats": stats}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest["neural_lexicon"], indent=2))


if __name__ == "__main__":
    main()
