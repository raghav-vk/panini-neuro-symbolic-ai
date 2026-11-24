"""Time-boxed review rounds: sealing, intake receipts, collection at close, and the report."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
pytest.importorskip("cryptography")
import pilot_round as pr
from panini.rules import load_rules
from score_pilot import score

RULES = load_rules(ROOT / "data/rules/development_sandhi.jsonl")
ROUND = {"round": "t-1", "opens": "2026-11-24T00:00:00Z", "closes": "2026-12-01T23:59:59Z",
         "criteria": {"min_submissions": 2, "min_completion_share": 0.8, "min_median_control_accuracy": 0.85,
                      "min_gwet_ac1": 0.6}}
ITEMS = [{"item_id": "P-1", "surface": "cApi", "proposed_left": "cA", "proposed_right": "api"},
         {"item_id": "P-2", "surface": "cApi", "proposed_left": "ca", "proposed_right": "api"},
         {"item_id": "C-1", "surface": "cApi", "proposed_left": "ca", "proposed_right": "api"},
         {"item_id": "C-2", "surface": "cApi", "proposed_left": "cA", "proposed_right": "Api"}]
KEY = [{"item_id": "P-1", "kind": "real"}, {"item_id": "P-2", "kind": "real"},
       {"item_id": "C-1", "kind": "control_correct", "expected": "correct", "dcs_left": "ca", "dcs_right": "api"},
       {"item_id": "C-2", "kind": "control_wrong", "expected": "wrong", "dcs_left": "ca", "dcs_right": "api"}]


@pytest.fixture(scope="module")
def keys(tmp_path_factory):
    path = tmp_path_factory.mktemp("keys") / "private.pem"
    return pr.make_keys(path), path.read_bytes()


def rows(name, p1=("wrong", "ca", "api")):
    def a(item_id, decision, left="", right=""):
        return {"item_id": item_id, "decision": decision, "left": left, "right": right, "notes": "",
                "reviewer": name, "reviewed_at": "2026-11-25"}
    return [a("P-1", *p1), a("P-2", "correct"), a("C-1", "correct"), a("C-2", "wrong", "ca", "api")]


def payload(name, credit=False, round_id="t-1", answers=None):
    return {"round": round_id, "reviewer": name, "credit": credit, "started_at": "2026-11-25T10:00:00Z",
            "sealed_at": "2026-11-25T10:40:00Z", "answers": rows(name) if answers is None else answers}


def test_seal_round_trip_survives_pasting_into_text(keys):
    public, private = keys
    block = pr.seal(payload("देवदत्त"), public)
    body = f"### Sealed answers\n\n```text\n{block}\n```\n"
    assert pr.unseal(pr.sealed_text(body), private)["reviewer"] == "देवदत्त"
    assert pr.sealed_text("no block here") is None


def test_intake_receipts_only_on_time_readable_answers(keys):
    public, private = keys
    block = pr.seal(payload("a"), public)
    status, details = pr.check_submission(block, "2026-11-26T00:00:00Z", ROUND, ITEMS, private)
    assert status == "received" and details["answered"] == 4 and details["problems"] == 0
    text = pr.reply(status, details, ROUND)
    assert pr.RECEIPT.search(text).group(2) == pr.digest(pr.sealed_text(block))
    assert "correct" not in text.lower().replace("incorrect", "")  # nothing about right or wrong answers

    status, details = pr.check_submission(block, "2026-12-02T00:00:00Z", ROUND, ITEMS, private)
    assert status == "late" and not pr.RECEIPT.search(pr.reply(status, details, ROUND))
    assert pr.check_submission(block[:200] + pr.END, "2026-11-26T00:00:00Z", ROUND, ITEMS, private)[0] == "invalid"
    other = pr.seal(payload("a", round_id="t-0"), public)
    assert pr.check_submission(other, "2026-11-26T00:00:00Z", ROUND, ITEMS, private)[0] == "invalid"


def issue(number, author, created, block, receipted=True, by="github-actions[bot]"):
    comments = [{"author": by, "body": pr.reply("received", {"sha256": pr.digest(pr.sealed_text(block)), "answered": 4,
                                                            "items": 4, "problems": 0, "credit": False}, ROUND)}]
    return {"number": number, "author": author, "created_at": created, "body": block,
            "comments": comments if receipted else []}


def test_collect_takes_the_latest_receipted_on_time_hand_in(keys):
    public, private = keys
    first, second = pr.seal(payload("a"), public), pr.seal(payload("a", credit=True), public)
    edited = pr.seal(payload("b"), public)
    issues = [issue(1, "a", "2026-11-25T00:00:00Z", first), issue(2, "a", "2026-11-26T00:00:00Z", second),
              {**issue(3, "b", "2026-11-25T00:00:00Z", edited), "body": pr.seal(payload("b2"), public)},
              issue(4, "c", "2026-11-25T00:00:00Z", pr.seal(payload("c"), public), by="c"),
              issue(5, "d", "2026-12-02T00:00:00Z", pr.seal(payload("d"), public))]
    chosen = pr.collect(issues, ROUND, private)
    assert set(chosen) == {"a"} and chosen["a"]["issue"] == 2 and chosen["a"]["credit"]


def test_close_scores_and_reports_with_consent_respected(keys):
    public, private = keys
    hand_ins = {"alice": payload("Alice Sharma", credit=True), "bob": payload("Bob"),
                "yes": payload("Yes", answers=[{**r, "decision": "correct", "left": "", "right": ""} for r in rows("Yes")])}
    issues = [issue(n, login, "2026-11-25T00:00:00Z", pr.seal(p, public)) for n, (login, p) in enumerate(hand_ins.items(), 1)]
    submissions = pr.collect(issues, ROUND, private)
    result = score(ITEMS, KEY, {login: p["answers"] for login, p in submissions.items()}, RULES)
    names = pr.display_names(submissions)
    assert names == {"alice": "Alice Sharma", "bob": "Reviewer A", "yes": "Reviewer B"}
    public_result = pr.public_result(result, names)
    assert set(public_result["reviewers"]) == {"Alice Sharma", "Reviewer A", "Reviewer B"}
    text = pr.report(result, submissions, ITEMS, KEY, ROUND)
    assert "3 reviewers handed in on time" in text and "Median control accuracy" in text
    assert "Bob" not in text and "bob" not in text
    assert "40 minutes" in text


def test_ac1_stays_high_when_one_answer_dominates():
    from score_pilot import fleiss_kappa, gwet_ac1
    table = [[3, 0, 0, 0]] * 18 + [[2, 1, 0, 0]] * 2  # 3 raters, almost everything "correct"
    assert fleiss_kappa(table) < 0.1 and gwet_ac1(table) > 0.9
