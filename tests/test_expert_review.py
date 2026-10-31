"""Review preparation, worksheet building and the reviewer-file validator."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_review_page import iast_item
from prepare_expert_review import overlap_ids, review_item
from validate_review import check_answers, check_rules

REVIEWS = ROOT / "data/reviews"
ITEMS = [{"item_id": "A", "proposed_left": "ca", "proposed_right": "api"},
         {"item_id": "B", "proposed_left": "tu", "proposed_right": "iha"}]
SIGNED = {"reviewer": "R", "reviewed_at": "2026-11-02"}


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_review_items_are_slp1_and_shown_in_iast_with_iast_offsets():
    row = {"example_id": "X", "source_sentence": "kfzRaH cApi Sakrasya  ", "source_span": [7, 11],
           "source_surface": "cApi", "left": "ca", "right": "api", "left_lemma": "ca", "right_lemma": "api"}
    item = review_item(row)
    assert item["sentence"] == "kfzRaH cApi Sakrasya" and item["span"] == [7, 11] and item["surface"] == "cApi"
    shown = iast_item({**item, "sentence": "Bavati kfzRaH cApi", "span": [14, 18]})
    assert shown["sentence"] == "bhavati kṛṣṇaḥ cāpi" and shown["sentence"][slice(*shown["span"])] == "cāpi"
    try:
        review_item({**row, "source_span": [2, 6]})
    except ValueError:
        return
    raise AssertionError("a misaligned span must be rejected")


def test_overlap_is_seeded_and_sorted():
    items = [{"item_id": f"I{i:03d}"} for i in range(200)]
    first = overlap_ids(items, 50, 2026)
    assert first == overlap_ids(list(reversed(items)), 50, 2026) == sorted(first)
    assert len(set(first)) == 50 and first != overlap_ids(items, 50, 7)


def test_answers_validator_accepts_complete_file():
    answers = [{"item_id": "A", "decision": "correct", **SIGNED},
               {"item_id": "B", "decision": "wrong", "left": "tu", "right": "ihā", **SIGNED}]
    # Answers are IAST from the worksheet; items are SLP1.
    same = [{"item_id": "A", "decision": "wrong", "left": "ca", "right": "api", **SIGNED}]
    assert "same as the proposal" in "\n".join(check_answers(ITEMS, same, ids=["A"]))
    assert check_answers(ITEMS, answers) == []
    assert check_answers(ITEMS, answers[1:], ids=["B"]) == []


def test_answers_validator_reports_each_problem():
    answers = [{"item_id": "A", "decision": "wrong", "left": "ca", "right": "api", **SIGNED},
               {"item_id": "A", "decision": "unsure", **SIGNED},
               {"item_id": "Z", "decision": "correct", **SIGNED},
               {"item_id": "B", "decision": "maybe", "reviewer": "", "reviewed_at": "soon"}]
    text = "\n".join(check_answers(ITEMS, answers))
    for expected in ("same as the proposal", "answered more than once", "'unsure' needs a note",
                     "not an item of this review", "decision must be one of", "reviewer is empty",
                     "reviewed_at must be a date", "differs between lines"):
        assert expected in text
    assert "1 items have no answer" in "\n".join(check_answers(ITEMS, answers[:1]))


def test_rules_validator():
    rules = [{"rule_id": "SDH-001"}, {"rule_id": "SDH-002"}]
    good = {"decision": "approve", "scope_correct": True, "examples_correct": True,
            "exceptions_complete": True, "precedence_correct": True, "notes": "", **SIGNED}
    assert check_rules(rules, [{**good, "rule_id": "SDH-001"}, {**good, "rule_id": "SDH-002"}]) == []
    bad = [{**good, "rule_id": "SDH-001", "decision": "revise"},
           {**good, "rule_id": "SDH-009", "exceptions_complete": None}]
    text = "\n".join(check_rules(rules, bad))
    assert "explain the problem" in text and "unknown rule" in text and "['SDH-002']" in text


def test_committed_review_files_are_consistent():
    items = read_jsonl(REVIEWS / "silver_sample.jsonl")
    ids = {item["item_id"] for item in items}
    overlap = json.loads((REVIEWS / "silver_overlap_ids.json").read_text())
    assert len(items) == len(ids) == 200 and len(overlap) == 50 and set(overlap) <= ids
    for item in items:
        start, end = item["span"]
        assert "".join(list(item["sentence"])[start:end]) == item["surface"]
    rules = read_jsonl(ROOT / "data/rules/development_sandhi.jsonl")
    assert [r["rule_id"] for r in read_jsonl(REVIEWS / "rule_queue.template.jsonl")] == [r["rule_id"] for r in rules]


def test_verify_worksheet_embeds_only_selected_items(tmp_path):
    output = tmp_path / "page.html"
    subprocess.run([sys.executable, str(ROOT / "scripts/build_review_page.py"), str(REVIEWS / "silver_sample.jsonl"),
                    "--mode", "verify", "--ids", str(REVIEWS / "silver_overlap_ids.json"),
                    "--answers-name", "x.jsonl", "--output", str(output)], check=True, capture_output=True)
    page = output.read_text(encoding="utf-8")
    assert "__REVIEW_DATA__" not in page and "__REVIEW_CONFIG__" not in page
    assert page.count('"item_id"') == 50 and '"answers_name": "x.jsonl"' in page
