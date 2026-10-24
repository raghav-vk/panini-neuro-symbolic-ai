#!/usr/bin/env python3
"""Inspect proof-bearing analyses using symbolic order or a trained tiny ranker."""

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.rules import load_rules
from panini.candidates import enumerate_candidates
from panini.experiment_data import digest
from panini.ranking import make_transformer, predict_neural


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("surface")
    p.add_argument("--rules", type=Path, default=ROOT / "data/rules/development_sandhi.jsonl")
    p.add_argument("--tags", nargs="*", default=["pada_boundary"])
    p.add_argument("--context", default="")
    p.add_argument("--checkpoint", type=Path)
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--kosha", type=Path, default=ROOT / "data/external/vidyut-0.4.0/kosha",
                   help="needed for checkpoints trained with --external-lexicon")
    args = p.parse_args()
    candidates = enumerate_candidates(args.surface, load_rules(args.rules), args.tags)
    threshold, values = 0.0, [0.0] * len(candidates)
    if args.checkpoint:
        import torch
        torch.set_num_threads(2)
        state = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
        if state["rules_sha256"] != digest(args.rules.read_text()):
            p.error("checkpoint was trained with a different rule snapshot")
        model = make_transformer(state["width"], state["layers"], max_length=state["max_length"],
                                 pooling=state.get("pooling", "mean"), mark_boundary=state.get("mark_boundary", False),
                                 lexicon=state.get("lexicon"))
        model.load_state_dict(state["state_dict"])
        if (state.get("lexicon") or {}).get("external"):
            from panini.lexicon import KoshaLexicon, annotate
            annotate([{"candidates": candidates}], KoshaLexicon(args.kosha))
        values = predict_neural(model, [{"surface": args.surface, "context": args.context, "candidates": candidates}], state["use_rules"], state["use_context"])[0]
        threshold = state["threshold"]
    ranked = sorted(range(len(values)), key=lambda i: (-values[i], i))
    confidence = 1 / sum(math.exp(v - max(values)) for v in values) if values else 0
    print(json.dumps({"surface": args.surface, "tags_supplied_not_inferred": args.tags, "candidate_count": len(candidates),
                      "abstained": not ranked or confidence < threshold, "threshold": threshold,
                      "warning": "Draft subset consistency, not expert grammatical validation.",
                      "analyses": [{**candidates[i], "score": values[i]} for i in ranked[:args.top_k]]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
