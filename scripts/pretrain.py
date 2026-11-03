#!/usr/bin/env python3
"""Pretrain the byte encoder on P-A or P-B (docs/PRETRAINING_PLAN.md sections 4, 5 and 8).

Span-masked byte modelling and rule-guided real-or-near-miss discrimination. Progress is
checked on dev sentences without labels; the test set is never read.
"""

import argparse
import hashlib
import json
import platform
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.pretraining import (SIZES, batch_disc, batch_mlm, corpus_vocabulary, disc_loss, evaluate, learning_rate,
                                make_encoder, mlm_loss, padded, vowel_confusions)
from panini.rules import load_rules


def read_texts(path):
    return [json.loads(line)["text"] for line in path.read_text(encoding="utf-8").splitlines()]


def epoch_batches(texts, size, rng):
    """One shuffled pass, batched within 64-byte length buckets so short sentences are not padded to 256."""
    buckets = {}
    for i, text in enumerate(texts):
        buckets.setdefault(padded(len(text), 64), []).append(i)
    batches = []
    for ids in buckets.values():
        rng.shuffle(ids)
        batches += [[texts[i] for i in ids[k:k + size]] for k in range(0, len(ids), size)]
    rng.shuffle(batches)
    return batches


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", type=Path, default=ROOT / "data/processed/pretrain-v1/P-A.jsonl")
    p.add_argument("--dev", type=Path, default=ROOT / "data/processed/pretrain-v1/dev_sentences.jsonl")
    p.add_argument("--rules", type=Path, default=ROOT / "data/rules/development_sandhi.jsonl")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--size", choices=sorted(SIZES), default="S")
    p.add_argument("--objectives", nargs="+", choices=["mlm", "disc"], default=["mlm", "disc"])
    p.add_argument("--steps", type=int, default=1000)
    p.add_argument("--batch-size", type=int, default=128)
    p.add_argument("--lr", type=float, default=5e-4)
    p.add_argument("--warmup", type=int, default=500)
    p.add_argument("--eval-every", type=int, default=250)
    p.add_argument("--save-every", type=int, help="also keep encoder-step<N>.pt every N steps, so the stopping point can be chosen on dev")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--device", default="mps")
    args = p.parse_args()
    import torch
    if "test" in args.corpus.name or "test" in args.dev.name:
        p.error("pretraining never reads test data")
    args.output.mkdir(parents=True, exist_ok=False)
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device(args.device)
    texts, dev = read_texts(args.corpus), read_texts(args.dev)
    vocabulary = corpus_vocabulary(texts)  # the corpus's own words, so P-B never sees held-out words here either
    confusions = vowel_confusions(load_rules(args.rules))
    model = make_encoder(**SIZES[args.size], max_length=256).to(device)
    if max(map(len, texts)) > model.max_length:
        raise ValueError("a corpus sentence exceeds max_length; nothing is truncated silently")
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    parameters = sum(x.numel() for x in model.parameters())
    record = {"configuration": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
              "corpus_sha256": hashlib.sha256(args.corpus.read_bytes()).hexdigest(),
              "dev_sha256": hashlib.sha256(args.dev.read_bytes()).hexdigest(),
              "rules_sha256": hashlib.sha256(args.rules.read_bytes()).hexdigest(),
              "corpus_sentences": len(texts), "corpus_bytes": sum(map(len, texts)), "vocabulary": len(vocabulary),
              "confusions": confusions, "parameters": parameters, "torch": torch.__version__,
              "platform": platform.platform(), "device": str(device),
              "note": "MPS is not bit-for-bit deterministic; compare seeds, not single runs.", "history": []}
    print(f"{parameters:,} parameters, {len(texts):,} sentences, device {device}", flush=True)
    save = lambda path: torch.save({"state_dict": model.state_dict(), "config": model.config, "size": args.size,
                                    "objectives": args.objectives, "confusions": confusions,
                                    "corpus_sha256": record["corpus_sha256"], "step": step + 1}, path)
    rng, cache = random.Random(args.seed), {}
    batches, seen_bytes = [], 0
    sync = torch.mps.synchronize if device.type == "mps" else (lambda: None)
    start = time.perf_counter()
    window = {"mlm": torch.zeros((), device=device), "disc": torch.zeros((), device=device), "n": 0}
    for step in range(args.steps):
        if not batches:
            batches = epoch_batches(texts, args.batch_size, rng)
        batch = batches.pop()
        seen_bytes += sum(map(len, batch))
        for group in optimizer.param_groups:
            group["lr"] = learning_rate(step, args.steps, args.lr, args.warmup)
        # One backward per objective: the summed loss's gradient, with one activation graph in memory at a time.
        optimizer.zero_grad()
        if "mlm" in args.objectives:
            part, _, _ = mlm_loss(model, *batch_mlm(batch, rng, device))
            part.backward()
            window["mlm"] += part.detach()
        if "disc" in args.objectives:
            part, _ = disc_loss(model, *batch_disc(batch, confusions, vocabulary, rng, device, cache))
            part.backward()
            window["disc"] += part.detach()
        window["n"] += 1
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        if args.save_every and (step + 1) % args.save_every == 0 and step + 1 < args.steps:
            save(args.output / f"encoder-step{step + 1}.pt")
        if (step + 1) % args.eval_every == 0 or step + 1 == args.steps:
            sync()
            elapsed = time.perf_counter() - start
            entry = {"step": step + 1, "seconds": elapsed, "epochs": seen_bytes / record["corpus_bytes"],
                     "train_mlm_loss": window["mlm"].item() / window["n"] if "mlm" in args.objectives else None,
                     "train_disc_loss": window["disc"].item() / window["n"] if "disc" in args.objectives else None,
                     "dev": evaluate(model, dev, confusions, vocabulary, device)}
            window = {"mlm": torch.zeros((), device=device), "disc": torch.zeros((), device=device), "n": 0}
            record["history"].append(entry)
            d = entry["dev"]
            print(f"step {step + 1}: {elapsed:.0f}s epochs={entry['epochs']:.3f} masked_acc={d['masked_byte_accuracy']:.3f} "
                  f"disc_bal={d['disc_balanced_accuracy']:.3f}", flush=True)
            (args.output / "pretrain.json").write_text(json.dumps(record, indent=2) + "\n")
    sync()
    elapsed = time.perf_counter() - start
    record["timing"] = {"seconds": elapsed, "seconds_per_step_including_eval": elapsed / args.steps,
                        "bytes_per_second": seen_bytes / elapsed,
                        "estimated_seconds_per_epoch": record["corpus_bytes"] / (seen_bytes / elapsed)}
    save(args.output / "encoder.pt")
    (args.output / "pretrain.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record["timing"], indent=2))


if __name__ == "__main__":
    main()
