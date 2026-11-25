#!/usr/bin/env python3
"""Which Sanskrit texts the pretraining corpora come from (version 0.5, docs/PRETRAINING_PLAN.md).

DCS_pick, the pretraining source, records only sentence numbers, not text names, and its numbers
differ from the current DCS sentence IDs. This script recovers each sentence's text by matching its
letters (SLP1, all non-letters removed, at least 12 letters) against the pinned DCS CoNLL-U checkout
(scripts/fetch_dcs_conllu.py), which names the text of every sentence. A sentence found in several
texts (shared verses) is split equally between them.

Writes corpus_texts.json and CORPUS_TEXTS.md to --output (default reports/pretraining-v1).
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.translit import iast_to_slp1

CONLLU = ROOT / "data/external/dcs-conllu/dcs/data/conllu/files"
CORPORA = ROOT / "data/processed/pretrain-v1"
MIN_LETTERS = 12


def letters(text):
    return re.sub(r"[^a-zA-Z]", "", text)


def index_texts(conllu=CONLLU):
    """{normalised sentence: set of text names} from the CoNLL-U files."""
    index = defaultdict(set)
    for path in sorted(conllu.rglob("*.conllu")):
        name = None
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("## text:"):
                    name = line[8:].strip()
                elif line.startswith("# text = "):
                    key = letters(iast_to_slp1(line[9:].strip()))
                    if len(key) >= MIN_LETTERS and name:
                        index[key].add(name)
    return index


def attribute(rows, index):
    counts, matched, shared = Counter(), 0, 0
    for row in rows:
        names = index.get(letters(row["text"]))
        if not names:
            continue
        matched += 1
        shared += len(names) > 1
        for name in names:
            counts[name] += 1 / len(names)
    return {"sentences": len(rows), "matched": matched, "in_several_texts": shared,
            "texts": {name: round(n, 1) for name, n in counts.most_common()}}


def markdown(result, top=40):
    a, b = result["P-A"], result["P-B"]
    total = sum(a["texts"].values())
    lines = ["# Texts in the Pretraining Corpora (Version 0.5)", "",
             "The encoder was pretrained on **P-A**: every DCS_pick sentence (Krishna et al. 2017, CC BY 4.0) "
             "except the sandhi dev and test sentences and their copies. **P-B** also drops every sentence "
             "containing a held-out test word. Both are in SLP1. See `docs/PRETRAINING_PLAN.md` section 3.", "",
             "DCS_pick does not record text names, so each sentence is matched by its letters against the DCS "
             f"CoNLL-U treebank at its pinned commit (`datasets/dcs_conllu_manifest.json`; script "
             "`scripts/attribute_pretraining_texts.py`). {a['matched']:,} of {a['sentences']:,} "
             f"P-A sentences ({a['matched'] / a['sentences']:.1%}) matched a named text; the rest differ from the "
             "current DCS text, or are too short to match safely. A verse found in several texts is split "
             f"equally between them ({a['in_several_texts']:,} sentences).", "",
             f"P-A draws on **{len(a['texts'])} texts**, and P-B on {len(b['texts'])}. Their "
             f"{top} largest, by share of the matched P-A sentences:", "",
             "| # | Text | P-A sentences | Share | P-B sentences |", "| ---: | --- | ---: | ---: | ---: |"]
    for i, (name, n) in enumerate(list(a["texts"].items())[:top], 1):
        lines.append(f"| {i} | {name} | {n:,.0f} | {n / total:.1%} | {b['texts'].get(name, 0):,.0f} |")
    rest = list(a["texts"].items())[top:]
    lines += ["", f"The other {len(rest)} texts together hold {sum(n for _, n in rest):,.0f} sentences "
              f"({sum(n for _, n in rest) / total:.1%}). The full list is in `corpus_texts.json`.", "",
              "The stage 3 test (version 0.8) used only DCS chapters with no sentence in DCS_pick, so the "
              "encoder had not seen them (`docs/RLCD_TRANSITION_PLAN.md`, stage 3)."]
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--corpora", type=Path, default=CORPORA)
    p.add_argument("--conllu", type=Path, default=CONLLU)
    p.add_argument("--output", type=Path, default=ROOT / "reports/pretraining-v1")
    args = p.parse_args()
    index = index_texts(args.conllu)
    result = {"method": "letters-only SLP1 match against the pinned DCS CoNLL-U (datasets/dcs_conllu_manifest.json); "
                        "shared verses split equally",
              "min_letters": MIN_LETTERS}
    for corpus in ("P-A", "P-B"):
        with open(args.corpora / f"{corpus}.jsonl", encoding="utf-8") as f:
            result[corpus] = attribute([json.loads(line) for line in f if line.strip()], index)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "corpus_texts.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n",
                                                   encoding="utf-8")
    (args.output / "CORPUS_TEXTS.md").write_text(markdown(result), encoding="utf-8")
    print(f"P-A: {result['P-A']['matched']:,} of {result['P-A']['sentences']:,} matched, {len(result['P-A']['texts'])} texts")


if __name__ == "__main__":
    main()
