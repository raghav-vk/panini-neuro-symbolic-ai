#!/usr/bin/env python3
"""Build original, narrow draft encodings and a review packet."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.rules import SandhiRule

# Unicode is essential for the Sanskrit source texts and IAST string probes.
SPECS = [
    ("a-dirgha", "vowel", "6.1.101", "akaḥ savarṇe dīrghaḥ", ["a", "ā"], ["a", "ā"], "ā", "drop_match", [], ["left_pragrhya"], "a", "a", "ā"),
    ("i-dirgha", "vowel", "6.1.101", "akaḥ savarṇe dīrghaḥ", ["i", "ī"], ["i", "ī"], "ī", "drop_match", [], ["left_pragrhya"], "i", "i", "ī"),
    ("a-i-guna", "vowel", "6.1.87", "ādguṇaḥ", ["a", "ā"], ["i", "ī"], "e", "drop_match", [], ["left_pragrhya"], "a", "i", "e"),
    ("a-u-guna", "vowel", "6.1.87", "ādguṇaḥ", ["a", "ā"], ["u", "ū"], "o", "drop_match", [], ["left_pragrhya"], "a", "u", "o"),
    ("i-a-yan", "vowel", "6.1.77", "iko yaṇaci", ["i", "ī"], ["a"], "y", "keep_match", [], ["left_pragrhya"], "i", "a", "ya"),
    ("u-a-yan", "vowel", "6.1.77", "iko yaṇaci", ["u", "ū"], ["a"], "v", "keep_match", [], ["left_pragrhya"], "u", "a", "va"),
    ("t-c-palatal", "consonant", "8.4.40", "stoḥ ścunā ścuḥ", ["t"], ["c"], "c", "keep_match", [], [], "t", "c", "cc"),
    ("t-l-assimilation", "consonant", "8.4.60", "tor li", ["t"], ["l"], "l", "keep_match", [], [], "t", "l", "ll"),
    ("m-k-anusvara", "nasal", "8.3.23", "mo 'nusvāraḥ", ["m"], ["k"], "ṃ", "keep_match", [], [], "m", "k", "ṃk"),
    ("m-t-anusvara", "nasal", "8.3.23", "mo 'nusvāraḥ", ["m"], ["t"], "ṃ", "keep_match", [], [], "m", "t", "ṃt"),
    ("visarga-t", "visarga", "8.3.34", "visarjanīyasya saḥ", ["ḥ"], ["t"], "s", "keep_match", ["right_second_not_sibilant"], [], "ḥ", "ta", "sta"),
    ("pragrhya-i-a", "non_application", "6.1.125", "plutapragṛhyā aci nityam", ["ī"], ["a"], "ī", "keep_match", ["left_pragrhya"], [], "ī", "a", "īa"),
    # Added after the DCS silver coverage audit; appended so earlier rule IDs stay stable.
    ("a-e-vrddhi", "vowel", "6.1.88", "vṛddhir eci", ["a", "ā"], ["e", "ai"], "ai", "drop_match", [], ["left_pragrhya"], "a", "e", "ai"),
    ("a-o-vrddhi", "vowel", "6.1.88", "vṛddhir eci", ["a", "ā"], ["o", "au"], "au", "drop_match", [], ["left_pragrhya"], "a", "o", "au"),
    ("u-dirgha", "vowel", "6.1.101", "akaḥ savarṇe dīrghaḥ", ["u", "ū"], ["u", "ū"], "ū", "drop_match", [], ["left_pragrhya"], "u", "u", "ū"),
    ("a-r-guna", "vowel", "6.1.87", "ādguṇaḥ", ["a", "ā"], ["ṛ"], "ar", "drop_match", [], ["left_pragrhya"], "a", "ṛ", "ar"),
    ("i-yan-other", "vowel", "6.1.77", "iko yaṇaci", ["i", "ī"], ["ā", "u", "ū", "e", "o", "ṛ"], "y", "keep_match", [], ["left_pragrhya"], "i", "e", "ye"),
    ("u-yan-other", "vowel", "6.1.77", "iko yaṇaci", ["u", "ū"], ["ā", "i", "ī", "e", "o", "ṛ"], "v", "keep_match", [], ["left_pragrhya"], "u", "e", "ve"),
]


def build():
    sources = {r["sutra_id"]: r for r in map(json.loads, (ROOT / "data/sources/ashtadhyayi_sandhi_sutras.jsonl").read_text().splitlines())}
    rules, checks, queue = [], [], []
    for i, (name, family, sutra, iast, lefts, rights, emit, right_action, required, forbidden, left, right, surface) in enumerate(SPECS, 1):
        source = sources[sutra]
        rid = f"SDH-{i:03}"
        tags = ["pada_boundary", *required]
        rule = {
            "schema_version": 1, "rule_id": rid, "name": name,
            "scope": "non_application" if family == "non_application" else f"external_{family}_sandhi",
            "status": "draft",
            "source": {"sutra_ids": [sutra], "text_iast": iast, "text_devanagari": source["text_devanagari"],
                       "interpretation": f"Draft single-step subset: {left} + {right} -> {surface}. Only enumerated boundary strings and supplied tags are covered; exceptions and interactions require review.",
                       "url": source["source"]["url"], "commit": source["source"]["commit"], "license": "TO_VERIFY"},
            "match": {"left_suffixes": lefts, "right_prefixes": rights, "required_tags": tags, "forbidden_tags": forbidden},
            "operation": {"kind": "rewrite", "left": "drop_match", "emit": emit, "right": right_action},
            "precedence": 200 if family == "non_application" else 100, "optional": False,
            "examples": [{"left": p + left, "right": right + q, "surface": p + surface + q, "tags": tags,
                          "source": "constructed_phonological_probe", "notes": "Mechanical string probe, not an attested lexical or grammatical judgement."}
                         for p, q in [("", ""), ("ka", "na")]],
            "counterexamples": [{"left": left, "right": right, "reason": "Do not apply when pada_boundary is absent; see executable checks."}],
            "review": {"author": "Project Panini development workflow", "reviewer": "", "reviewed_at": ""},
            "notes": "Not a full sutra implementation. Nasal alternatives/derivation chains and lexical/morphological exceptions are not covered. Tags are supplied, not inferred. No expert approval."}
        SandhiRule.from_mapping(rule)
        rules.append(rule)
        checks.append({"rule_id": rid, "left": left, "right": right, "tags": required, "expected": None, "reason": "missing pada boundary"})
        if forbidden:
            checks.append({"rule_id": rid, "left": left, "right": right, "tags": tags + forbidden, "expected": None, "reason": "blocked prerequisite"})
        if required:
            checks.append({"rule_id": rid, "left": left, "right": right, "tags": ["pada_boundary"], "expected": None, "reason": "unknown prerequisite"})
        checks.append({"rule_id": rid, "left": "x", "right": right, "tags": tags, "expected": None, "reason": "nonmatching boundary"})
        queue.append({"rule_id": rid, "sutra_ids": [sutra], "family": family, "status": "pending", "reviewer": "", "reviewed_at": "",
                      "scope_correct": None, "examples_correct": None, "exceptions_complete": None, "precedence_correct": None, "decision": "pending", "notes": ""})
    for name, rows in {"data/rules/development_sandhi.jsonl": rules, "data/rules/development_checks.jsonl": checks,
                       "data/reviews/rule_queue.template.jsonl": queue}.items():
        path = ROOT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    lines = ["# First Sandhi Review Packet", "", f"All {len(rules)} records are drafts. Passing tests are not expert approval.", "",
             "Record decisions in a copy of rule_queue.template.jsonl, not the generated template.", "Review scope, prerequisites, exceptions, variants, derivation order, and positive/negative cases.", ""]
    for rule in rules:
        lines += [f"## {rule['rule_id']}: {rule['name']}", "", f"Sutra {rule['source']['sutra_ids'][0]}: {rule['source']['text_devanagari']}", "",
                  rule["source"]["interpretation"], "", f"Required tags: {', '.join(rule['match']['required_tags'])}.",
                  f"Blocked tags: {', '.join(rule['match']['forbidden_tags']) or 'none encoded'}.", "",
                  "Decision: pending. Reviewer/date: pending. Corrections and missing exceptions: __________", ""]
    (ROOT / "data/reviews/REVIEW_PACKET.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Built {len(rules)} draft rules and {len(checks)} executable negative checks.")


if __name__ == "__main__":
    build()
