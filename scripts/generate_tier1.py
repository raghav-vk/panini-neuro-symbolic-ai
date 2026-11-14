#!/usr/bin/env python3
"""RLCD stage 3, step 1: Tier 1 synthetic clauses, generated from the reviewed tables (plan section 4).

Samples clauses whose participants fit each root's role frame (data/rlcd/frames.tsv, with
stem classes from data/rlcd/stem_classes.tsv), derives them with the stage 2 compiler and keeps
the licit ones. Person and number follow the agreeing participant, so the sampler proposes only
clauses the constraint layer should accept; any rejection is counted and reported.

Every sentence is synthetic, never attested (protocol section 8.4). While any table row is still
draft_unreviewed (issue #78), the output is marked not for training.

Writes the dataset to data/processed/rlcd-tier1-v0/ (not committed; it regenerates exactly from
the seed), its manifest to reports/rlcd-stage3/, and a stratified sample for the text reader to
data/reviews/.
"""

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.clause import KARMAKATVA, STEMS, read_tsv
from panini.derive import Compiler
from panini.translit import slp1_to_iast

FRAMES = ROOT / "data/rlcd/frames.tsv"
CLASSES = ROOT / "data/rlcd/stem_classes.tsv"
LAKARAS = ["Lat", "Lit", "Lut", "Lrt", "Lot", "Lan", "VidhiLin", "AshirLin", "Lun", "Lrn"]
VACANAS = ["Eka", "Dvi", "Bahu"]
OPTIONAL = {"karaRa": 0.3, "aDikaraRa": 0.3}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_frames():
    frames = []
    for row in read_tsv(FRAMES):
        roles = {r: set(row[r].split(",")) for r in ("kartf", "karman", "karaRa", "aDikaraRa") if row[r] != "-"}
        frames.append({"code": row["code"], "aupadeshika": row["aupadeshika"], "gloss": row["gloss"], "roles": roles})
    return frames


def sample_clause(frame, compiler, members, rng):
    """One clause proposal for a root frame; None if a role has no fitting stem."""
    d = next(r for r in read_tsv_cached() if r["code"] == frame["code"])
    kind = compiler.karmakatva[(frame["code"], ())]
    has_karman = "karman" in frame["roles"] and kind == "sakarmaka"
    if has_karman:
        prayoga = "Karmani" if rng.random() < 0.3 else "Kartari"
    else:
        prayoga = "Bhave" if kind == "akarmaka" and rng.random() < 0.2 else "Kartari"
    roles = ["kartf"]
    if has_karman and (prayoga == "Karmani" or rng.random() < 0.8):
        roles.append("karman")
    roles += [r for r, p in OPTIONAL.items() if r in frame["roles"] and rng.random() < p]
    used, participants = set(), []
    for role in roles:
        options = sorted({s for c in frame["roles"][role] for s in members.get(c, ())} - used)
        if role != "kartf" or prayoga != "Kartari":
            options = [s for s in options if s not in ("asmad", "yuzmad")] or options
        if not options:
            return None
        stem = rng.choice(options)
        used.add(stem)
        lingas = sorted(compiler.stems[stem]["lingas"])
        linga = "Pum" if stem in ("asmad", "yuzmad") else rng.choice(lingas)
        participants.append({"role": role, "stem": stem, "linga": linga, "vacana": rng.choice(VACANAS)})
    agree = {"Kartari": "kartf", "Karmani": "karman"}.get(prayoga)
    if agree:
        p = next(x for x in participants if x["role"] == agree)
        purusha = {"asmad": "Uttama", "yuzmad": "Madhyama"}.get(p["stem"], "Prathama")
        vacana = p["vacana"]
    else:
        purusha, vacana = "Prathama", "Eka"
    return {"schema_version": "0.3.0", "dhatu": {"aupadeshika": d["aupadeshika"], "gana": d["gana"], "code": d["code"]},
            "upasargas": [], "prayoga": prayoga, "lakara": rng.choice(LAKARAS), "purusha": purusha, "vacana": vacana,
            "participants": participants}


_TSV = []


def read_tsv_cached():
    if not _TSV:
        _TSV.extend(read_tsv(KARMAKATVA))
    return _TSV


def labelled(clause_id, clause, result):
    words = []
    for w in result["words"]:
        forms = [f["text"] for f in w["forms"]]
        entry = {"form": forms[0], "alternatives": forms[1:], "role": w["role"],
                 "round_trip": w["forms"][0]["round_trip"]}
        if w["role"] == "kriyA":
            entry.update({k: clause[k] for k in ("prayoga", "lakara", "purusha", "vacana")}, dhatu=clause["dhatu"]["code"])
        else:
            p = next(x for x in clause["participants"] if x["role"] == w["role"])
            entry.update(stem=p["stem"], linga=p["linga"], vacana=p["vacana"], vibhakti=w["vibhakti"])
        words.append(entry)
    return {"id": clause_id, "text": result["text"], "words": words, "clause": clause,
            "provenance": "tier1_synthetic", "attested": False}


def generate(count, seed, compiler):
    """count distinct licit clauses: (rows, rejection counts, attempts). Every root is tried first."""
    rng = random.Random(seed)
    frames = [f for f in load_frames() if "kartf" in f["roles"]]
    members = {}
    for row in read_tsv(CLASSES):
        for c in row["classes"].split(","):
            members.setdefault(c, set()).add(row["stem"])
    seen, rows, rejected, attempts = set(), [], Counter(), 0
    while len(rows) < count:
        attempts += 1
        if attempts > count * 50:
            raise RuntimeError(f"only {len(rows)} distinct clauses after {attempts} attempts")
        frame = frames[(attempts - 1) % len(frames)] if attempts <= len(frames) else rng.choice(frames)
        clause = sample_clause(frame, compiler, members, rng)
        if clause is None:
            rejected["no_fitting_stem"] += 1
            continue
        key = json.dumps(clause, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        result = compiler.compile_clause(clause)
        if not result["valid"]:
            for v in result["violations"]:
                rejected[v["code"]] += 1
            continue
        rows.append(labelled(f"T1-{len(rows) + 1:06d}", clause, result))
    return rows, rejected, attempts


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--count", type=int, default=10000)
    p.add_argument("--seed", type=int, default=1729)
    p.add_argument("--sample", type=int, default=100, help="sentences for the text reader's naturalness review")
    p.add_argument("--output", type=Path, default=ROOT / "data/processed/rlcd-tier1-v0")
    args = p.parse_args()
    rows, rejected, attempts = generate(args.count, args.seed, Compiler())
    args.output.mkdir(parents=True, exist_ok=True)
    data = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    (args.output / "sentences.jsonl").write_text(data)

    tables = {str(path.relative_to(ROOT)): path for path in (KARMAKATVA, STEMS, FRAMES, CLASSES)}
    unreviewed = sum(r["status"] == "draft_unreviewed" for path in tables.values() for r in read_tsv(path))
    count = lambda key: dict(sorted(Counter(key(r) for r in rows).items()))
    manifest = {
        "dataset": "rlcd-tier1-v0", "plan": "docs/RLCD_TRANSITION_PLAN.md, stage 3 step 1",
        "seed": args.seed, "sentences": len(rows), "attempts": attempts, "rejected": dict(rejected),
        "sha256": hashlib.sha256(data.encode()).hexdigest(),
        "tables": {name: sha256(path) for name, path in tables.items()},
        "table_rows_unreviewed": unreviewed,
        "for_training": unreviewed == 0,
        "vidyut": version("vidyut"),
        "words": sum(len(r["words"]) for r in rows),
        "forms_not_in_kosha": sum(w["round_trip"] != "verified" for r in rows for w in r["words"]),
        "by_root": count(lambda r: r["clause"]["dhatu"]["code"]),
        "by_lakara": count(lambda r: r["clause"]["lakara"]),
        "by_prayoga": count(lambda r: r["clause"]["prayoga"]),
        "by_purusha": count(lambda r: r["clause"]["purusha"]),
        "by_word_count": count(lambda r: len(r["words"])),
    }
    out = ROOT / "reports/rlcd-stage3"
    out.mkdir(parents=True, exist_ok=True)
    (out / "tier1_manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")

    # Stratified naturalness sample: every root, then the rest at random.
    sample_rng, by_root = random.Random(args.seed + 1), {}
    for r in rows:
        by_root.setdefault(r["clause"]["dhatu"]["code"], []).append(r)
    picked = [sample_rng.choice(v) for _, v in sorted(by_root.items())]
    rest = [r for r in rows if r not in picked]
    picked += sample_rng.sample(rest, max(0, args.sample - len(picked)))
    picked.sort(key=lambda r: r["id"])
    reviews = ROOT / "data/reviews"
    (reviews / "rlcd_tier1_sample.jsonl").write_text("".join(
        json.dumps({"id": r["id"], "text": r["text"], "naturalness": "pending", "note": ""}, ensure_ascii=False) + "\n"
        for r in picked))
    lines = ["# Tier 1 Synthetic Sentences: Naturalness Sample", "",
             f"{len(picked)} sentences from `rlcd-tier1-v0` (seed {args.seed}), at least one per root. They were",
             "generated by rule from draft tables and are not attested. Words are shown without sandhi between them.",
             "Please mark each in `rlcd_tier1_sample.jsonl` as `natural`, `odd` or `wrong`, with a note for",
             "anything not natural. Grammar is checked separately; this review is about sense and usage.", "",
             "| ID | Sentence (IAST) | Verb | Prayoga | Lakāra |", "| --- | --- | --- | --- | --- |"]
    gloss = {f["code"]: f["gloss"] for f in load_frames()}
    for r in picked:
        c = r["clause"]
        lines.append(f"| {r['id']} | {slp1_to_iast(r['text'])} | {gloss[c['dhatu']['code']]} | {c['prayoga']} | {c['lakara']} |")
    (reviews / "rlcd_tier1_sample.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({k: manifest[k] for k in ("sentences", "attempts", "rejected", "words", "forms_not_in_kosha",
                                               "table_rows_unreviewed", "for_training")}, indent=1))


if __name__ == "__main__":
    main()
