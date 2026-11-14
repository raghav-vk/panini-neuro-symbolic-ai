#!/usr/bin/env python3
"""Train one RLCD stage 3 tagger run (N1, N2 or N3) with the pre-registered settings.

docs/RLCD_TRANSITION_PLAN.md, "Stage 3 Training Pre-Registered Settings". Training data is the
classical part of the stage 3 training pool. Dev and test are never read here, and no
checkpoint is chosen: the final one is saved.
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
from panini.pretraining import learning_rate
from panini.tagger import MAX_BYTES, batch, chunks, loss, make_tagger, sentence_items, tag

SYSTEMS = {"N1": ("pretrained", "ce"), "N2": ("scratch", "ce"), "N3": ("pretrained", "brier")}
CHAPTERS = ROOT / "reports/dcs-conllu/overlap_by_chapter.jsonl"
TRAIN = ROOT / "data/processed/dcs-conllu-v1/train.jsonl"


def classical_chunks(train=TRAIN, chapters=CHAPTERS):
    """(forms, tags) chunks of the classical training sentences, and the number of truncated words."""
    rows = [json.loads(line) for line in Path(chapters).read_text(encoding="utf-8").splitlines()]
    classical = {r["chapter_id"] for r in rows if r["vedic"] is False and r["time_slot"] != "1"}
    out, truncated, dropped, sentences = [], 0, 0, 0
    for line in Path(train).open(encoding="utf-8"):
        s = json.loads(line)
        if s["chapter_id"] not in classical:
            continue
        sentences += 1
        kept, empty = sentence_items(s["words"])
        dropped += empty
        pieces, cut = chunks([f for _, f in kept])
        truncated += cut
        for piece in pieces:
            out.append(([form for _, form in piece], [tag(s["words"][kept[j][0]]) for j, _ in piece]))
    return out, truncated, dropped, sentences


def buckets(items, size, rng):
    """One shuffled pass, batched within 64-byte length buckets."""
    groups = {}
    for item in items:
        groups.setdefault(min(MAX_BYTES, -(-len(" ".join(item[0])) // 64) * 64), []).append(item)
    batches = []
    for group in groups.values():
        rng.shuffle(group)
        batches += [group[i:i + size] for i in range(0, len(group), size)]
    rng.shuffle(batches)
    return batches


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--system", choices=sorted(SYSTEMS), required=True)
    p.add_argument("--seed", type=int, required=True, help="fine-tuning seed; N1 and N3 use the P-A encoder of the same seed")
    p.add_argument("--passes", type=int, default=2)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--warmup", type=int, default=500)
    p.add_argument("--device", default="mps")
    p.add_argument("--max-steps", type=int, help="stop early (smoke tests only; never for reported runs)")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    import torch
    init, kind = SYSTEMS[args.system]
    output = args.output or ROOT / f"runs/tagger-{args.system}-seed{args.seed}"
    output.mkdir(parents=True, exist_ok=False)
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    rng = random.Random(args.seed)
    encoder = ROOT / f"runs/pretrain-S-PA-seed{args.seed}/encoder.pt"
    state = torch.load(encoder, map_location="cpu", weights_only=True) if init == "pretrained" else None
    items, truncated, dropped, sentences = classical_chunks()
    model = make_tagger(state).to(args.device)
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    per_pass = len(buckets(items, args.batch_size, random.Random(0)))
    steps = min(args.max_steps or 10 ** 9, per_pass * args.passes)
    record = {"system": args.system, "init": init, "loss": kind, "seed": args.seed, "configuration": {
                  k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
              "encoder": str(encoder.relative_to(ROOT)) if state else None,
              "encoder_sha256": hashlib.sha256(encoder.read_bytes()).hexdigest() if state else None,
              "train_sha256": hashlib.sha256(TRAIN.read_bytes()).hexdigest(),
              "sentences": sentences, "chunks": len(items), "truncated_words": truncated, "dropped_words": dropped,
              "steps": steps, "parameters": sum(x.numel() for x in model.parameters()),
              "torch": torch.__version__, "platform": platform.platform(), "history": []}
    step, start, running = 0, time.time(), []
    while step < steps:
        for group in buckets(items, args.batch_size, rng):
            if step >= steps:
                break
            for g in optimizer.param_groups:
                g["lr"] = learning_rate(step, steps, args.lr, args.warmup)
            tokens, ids, labels, words = batch(group, args.device)
            value = loss(model(tokens, ids, words), labels, kind)
            optimizer.zero_grad(set_to_none=True)
            value.backward()
            optimizer.step()
            running.append(value.detach())
            step += 1
            if step % 500 == 0 or step == steps:
                mean = torch.stack(running).mean().item()
                running = []
                record["history"].append({"step": step, "train_loss": mean, "seconds": round(time.time() - start, 1)})
                print(f"step {step}/{steps} loss {mean:.4f} {time.time() - start:.0f}s", flush=True)
    record["seconds"] = round(time.time() - start, 1)
    torch.save({"state_dict": model.state_dict(), "encoder_config": model.encoder.config, "record": record},
               output / "tagger.pt")
    (output / "train.json").write_text(json.dumps(record, indent=1) + "\n")


if __name__ == "__main__":
    main()
