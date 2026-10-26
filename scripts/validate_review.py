#!/usr/bin/env python3
"""Check a reviewer's file before it is committed.

    validate_review.py answers ITEMS ANSWERS [--ids IDS]
    validate_review.py rules RULES QUEUE

Exits 1 and lists every problem if the file is incomplete or malformed.
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

DECISIONS = {"correct", "wrong", "not_boundary", "unsure"}
RULE_DECISIONS = {"approve", "revise", "reject"}
RULE_CHECKS = ("scope_correct", "examples_correct", "exceptions_complete", "precedence_correct")


def read_jsonl(path):
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise SystemExit(f"{path}:{number}: not valid JSON ({error.msg})")
    return rows


def check_signature(where, row, errors):
    if not str(row.get("reviewer", "")).strip():
        errors.append(f"{where}: reviewer is empty")
    try:
        datetime.date.fromisoformat(str(row.get("reviewed_at", "")))
    except ValueError:
        errors.append(f"{where}: reviewed_at must be a date like 2026-11-02")


def check_answers(items, answers, ids=None):
    by_id = {item["item_id"]: item for item in items}
    expected = set(ids) if ids is not None else set(by_id)
    errors, seen = [], set()
    if not expected <= set(by_id):
        errors.append(f"IDs not in the item file: {sorted(expected - set(by_id))}")
    for number, row in enumerate(answers, 1):
        item_id, where = row.get("item_id"), f"line {number}"
        if item_id not in expected:
            errors.append(f"{where}: {item_id!r} is not an item of this review")
            continue
        where = f"{where} ({item_id})"
        if item_id in seen:
            errors.append(f"{where}: answered more than once")
        seen.add(item_id)
        decision = row.get("decision")
        if decision not in DECISIONS:
            errors.append(f"{where}: decision must be one of {sorted(DECISIONS)}")
        if decision == "wrong":
            left, right = str(row.get("left", "")).strip(), str(row.get("right", "")).strip()
            item = by_id[item_id]
            if not left or not right:
                errors.append(f"{where}: 'wrong' needs both corrected words")
            elif (left, right) == (item["proposed_left"], item["proposed_right"]):
                errors.append(f"{where}: the correction is the same as the proposal")
        if decision == "unsure" and not str(row.get("notes", "")).strip():
            errors.append(f"{where}: 'unsure' needs a note")
        check_signature(where, row, errors)
    if expected - seen:
        missing = sorted(expected - seen)
        errors.append(f"{len(missing)} items have no answer, for example {missing[:5]}")
    if len({(r.get("reviewer"), r.get("reviewed_at")) for r in answers}) > 1:
        errors.append("reviewer or reviewed_at differs between lines")
    return errors


def check_rules(rules, queue):
    rule_ids = [rule["rule_id"] for rule in rules]
    errors, seen = [], set()
    for number, row in enumerate(queue, 1):
        rule_id, where = row.get("rule_id"), f"line {number} ({row.get('rule_id')})"
        if rule_id not in rule_ids:
            errors.append(f"{where}: unknown rule")
            continue
        if rule_id in seen:
            errors.append(f"{where}: reviewed more than once")
        seen.add(rule_id)
        if row.get("decision") not in RULE_DECISIONS:
            errors.append(f"{where}: decision must be one of {sorted(RULE_DECISIONS)}")
        for check in RULE_CHECKS:
            if not isinstance(row.get(check), bool):
                errors.append(f"{where}: {check} must be true or false")
        needs_note = row.get("decision") in {"revise", "reject"} or any(row.get(c) is False for c in RULE_CHECKS)
        if needs_note and not str(row.get("notes", "")).strip():
            errors.append(f"{where}: explain the problem in notes")
        check_signature(where, row, errors)
    missing = [r for r in rule_ids if r not in seen]
    if missing:
        errors.append(f"rules without a review: {missing}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="kind", required=True)
    a = sub.add_parser("answers")
    a.add_argument("items", type=Path)
    a.add_argument("answers", type=Path)
    a.add_argument("--ids", type=Path, help="JSON list of the item IDs this reviewer was given")
    r = sub.add_parser("rules")
    r.add_argument("rules", type=Path)
    r.add_argument("queue", type=Path)
    args = parser.parse_args()
    if args.kind == "answers":
        ids = json.loads(args.ids.read_text(encoding="utf-8")) if args.ids else None
        errors = check_answers(read_jsonl(args.items), read_jsonl(args.answers), ids)
        target = args.answers
    else:
        errors = check_rules(read_jsonl(args.rules), read_jsonl(args.queue))
        target = args.queue
    for error in errors:
        print(error)
    if errors:
        print(f"{target}: {len(errors)} problems")
        sys.exit(1)
    print(f"{target}: OK")


if __name__ == "__main__":
    main()
