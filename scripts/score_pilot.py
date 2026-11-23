#!/usr/bin/env python3
"""Score the community review pilot (docs/REVIEW_APP_DESIGN.md, stage 0).

    score_pilot.py ANSWERS [ANSWERS ...] [--key KEY] [--output DIR]

Points are given only here, after every answer is in:
- a control item judged correctly: 2 points (+1 more for the exact split on a "wrong" control);
- a real item that agrees with the resolved answer: 1 point, or 3 for a correction that becomes
  the resolved answer and that the rule layer can turn back into the surface;
- "unsure": 0 points, never a penalty.

Real items are resolved by a vote weighted by each reviewer's control accuracy. An item without a
clear majority, or whose resolved correction no rule derives, goes to the expert queue. The
leaderboard lists only reviewers with control accuracy of at least --min-accuracy who answered at
least 80% of the items.

Writes results.json, LEADERBOARD.md and EXPERT_QUEUE.md (IAST) to --output, which defaults to an
uncommitted directory: publishing names is the reviewers' choice.
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from build_pilot_set import KEY, OUTPUT
from panini.candidates import forward
from panini.rules import load_rules
from panini.translit import slp1_to_iast, to_slp1
from validate_review import check_answers, read_jsonl

RULES = ROOT / "data/rules/development_sandhi.jsonl"
DECISIONS = ("correct", "wrong", "not_boundary", "unsure")


def normalise(answer):
    """The decision and, for "wrong", the corrected split in SLP1."""
    if answer["decision"] != "wrong":
        return answer["decision"], None
    return "wrong", (to_slp1(answer["left"]), to_slp1(answer["right"]))


def derivable(rules, surface, split, tags):
    return any(t.output == surface for t in forward(rules, *split, tuple(tags)))


def fleiss_kappa(table):
    """table: one list of category counts per item, each summing to the same number of raters."""
    if not table:
        return None
    raters = sum(table[0])
    if raters < 2 or any(sum(row) != raters for row in table):
        return None
    n = len(table)
    p_cat = [sum(row[j] for row in table) / (n * raters) for j in range(len(table[0]))]
    p_item = [(sum(c * c for c in row) - raters) / (raters * (raters - 1)) for row in table]
    p_bar, p_e = sum(p_item) / n, sum(p * p for p in p_cat)
    return None if p_e == 1 else (p_bar - p_e) / (1 - p_e)


def score(items, key, answer_sets, rules, min_accuracy=0.85, min_share=0.8):
    by_id = {i["item_id"]: i for i in items}
    key = {k["item_id"]: k for k in key}
    reviewers = {}
    for name, answers in answer_sets.items():
        reviewers[name] = {a["item_id"]: normalise(a) for a in answers if a.get("decision") in DECISIONS}

    stats = {}
    for name, answers in reviewers.items():
        passed = judged = exact = 0
        for item_id, (decision, split) in answers.items():
            k = key[item_id]
            if k["kind"] == "real" or decision == "unsure":
                continue
            judged += 1
            if decision == k["expected"]:
                passed += 1
                exact += k["kind"] == "control_wrong" and split == (k["dcs_left"], k["dcs_right"])
        stats[name] = {"answered": len(answers), "controls_judged": judged, "controls_passed": passed,
                       "exact_control_corrections": exact,
                       "control_accuracy": passed / judged if judged else None,
                       "unsure": sum(d == "unsure" for d, _ in answers.values())}

    resolved, queue = {}, []
    for item_id, k in key.items():
        if k["kind"] != "real":
            continue
        votes = defaultdict(float)
        splits = Counter()
        for name, answers in reviewers.items():
            if item_id not in answers or answers[item_id][0] == "unsure":
                continue
            decision, split = answers[item_id]
            votes[decision] += stats[name]["control_accuracy"] or 0.0
            if split:
                splits[split] += 1
        total = sum(votes.values())
        surface = by_id[item_id]["surface"]
        entry = {"votes": dict(votes)}
        if not votes or total == 0:
            entry["status"] = "no_votes"
        else:
            winner = max(votes, key=lambda d: votes[d])
            entry["status"] = "resolved" if votes[winner] > total / 2 and sum(1 for a in reviewers.values()
                                                                             if item_id in a and a[item_id][0] != "unsure") >= 2 else "disputed"
            entry["decision"] = winner
            if winner == "wrong" and splits:
                split = splits.most_common(1)[0][0]
                entry["correction"] = list(split)
                entry["derivable"] = derivable(rules, surface, split, k.get("tags", ["pada_boundary"]))
                if not entry["derivable"]:
                    entry["status"] = "outside_rule_inventory"
        resolved[item_id] = entry
        if entry["status"] != "resolved" or entry.get("decision") != "correct":
            queue.append(item_id)

    for name, answers in reviewers.items():
        points = 0
        for item_id, (decision, split) in answers.items():
            k, r = key[item_id], resolved.get(item_id)
            if decision == "unsure":
                continue
            if k["kind"] != "real":
                if decision == k["expected"]:
                    points += 2 + (k["kind"] == "control_wrong" and split == (k["dcs_left"], k["dcs_right"]))
            elif r and r["status"] == "resolved" and decision == r["decision"]:
                points += 3 if split and list(split) == r.get("correction") and r.get("derivable") else 1
        s = stats[name]
        s["points"] = points
        s["on_leaderboard"] = bool(s["control_accuracy"] is not None and s["control_accuracy"] >= min_accuracy
                                   and s["answered"] >= min_share * len(items))

    real_ids = [i for i, k in key.items() if k["kind"] == "real"]
    complete = [n for n, a in reviewers.items() if all(i in a for i in real_ids)]
    table = [[sum(reviewers[n][i][0] == d for n in complete) for d in DECISIONS] for i in real_ids] if len(complete) >= 2 else []
    return {"reviewers": stats, "resolved": resolved, "expert_queue": queue,
            "agreement": {"fleiss_kappa_real_items": fleiss_kappa(table), "reviewers_with_every_real_item": len(complete)}}


def leaderboard(result):
    rows = sorted(((n, s) for n, s in result["reviewers"].items() if s["on_leaderboard"]), key=lambda x: -x[1]["points"])
    lines = ["# Community Review Pilot: Leaderboard", "",
             "Points come from agreeing with the resolved answer and from hidden control items.", "",
             "| Rank | Reviewer | Points | Control accuracy | Answered |", "| ---: | --- | ---: | ---: | ---: |"]
    lines += [f"| {i} | {n} | {s['points']} | {s['control_accuracy']:.0%} | {s['answered']} |" for i, (n, s) in enumerate(rows, 1)]
    kappa = result["agreement"]["fleiss_kappa_real_items"]
    lines += ["", f"Agreement on real items (Fleiss' kappa): {'—' if kappa is None else f'{kappa:.2f}'}."]
    return "\n".join(lines) + "\n"


def expert_queue(result, items):
    by_id = {i["item_id"]: i for i in items}
    lines = ["# Community Review Pilot: Expert Queue", "",
             "Items the pilot could not settle, or settled as wrong. Transliteration is IAST.", "",
             "| Item | Fused form | Proposed | Status | Votes | Crowd correction |", "| --- | --- | --- | --- | --- | --- |"]
    for item_id in result["expert_queue"]:
        it, r = by_id[item_id], result["resolved"][item_id]
        votes = ", ".join(f"{d} {w:.2f}" for d, w in sorted(r["votes"].items()))
        fix = " + ".join(slp1_to_iast(w) for w in r["correction"]) if r.get("correction") else ""
        lines.append(f"| {item_id} | {slp1_to_iast(it['surface'])} | {slp1_to_iast(it['proposed_left'])} + "
                     f"{slp1_to_iast(it['proposed_right'])} | {r['status']} | {votes} | {fix} |")
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("answers", type=Path, nargs="+")
    p.add_argument("--items", type=Path, default=OUTPUT / "pilot_items.jsonl")
    p.add_argument("--key", type=Path, default=KEY)
    p.add_argument("--rules", type=Path, default=RULES)
    p.add_argument("--min-accuracy", type=float, default=0.85)
    p.add_argument("--output", type=Path, default=ROOT / "runs/pilot-scores")
    args = p.parse_args()
    items, key = read_jsonl(args.items), read_jsonl(args.key)
    answer_sets, problems = {}, {}
    for path in args.answers:
        answers = read_jsonl(path)
        names = {a.get("reviewer", "").strip() for a in answers} - {""}
        name = names.pop() if len(names) == 1 else path.stem
        if name in answer_sets:
            raise SystemExit(f"{path}: reviewer {name!r} appears in two files")
        answer_sets[name] = answers
        problems[name] = check_answers(items, answers)
    result = score(items, key, answer_sets, load_rules(args.rules), args.min_accuracy)
    result["validation_problems"] = {n: e for n, e in problems.items() if e}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "results.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    (args.output / "LEADERBOARD.md").write_text(leaderboard(result))
    (args.output / "EXPERT_QUEUE.md").write_text(expert_queue(result, items))
    print(leaderboard(result))
    for name, errors in result["validation_problems"].items():
        print(f"{name}: {len(errors)} validation problems, for example {errors[:3]}")
    print(f"{len(result['expert_queue'])} items in the expert queue; written to {args.output}")


if __name__ == "__main__":
    main()
