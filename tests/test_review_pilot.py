"""Community review pilot: transliteration of answers, set building and scoring."""

import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from panini.rules import load_rules
from panini.translit import to_slp1
import build_pilot_set
import score_pilot

RULES = load_rules(ROOT / "data/rules/development_sandhi.jsonl")


def test_to_slp1_reads_iast_and_devanagari():
    assert to_slp1(" cāpi ") == "cApi"
    pytest.importorskip("vidyut")
    assert to_slp1("चापि") == "cApi"
    assert to_slp1("गच्छति") == "gacCati"


def test_devanagari_view_keeps_the_span_on_the_highlighted_word():
    pytest.importorskip("vidyut")
    from build_review_page import devanagari_view
    item = {"item_id": "x", "sentence": "sa cApi Sakrasya", "span": [3, 7], "surface": "cApi",
            "proposed_left": "ca", "proposed_right": "api", "left_lemma": "ca", "right_lemma": "api"}
    shown = devanagari_view(item)
    assert shown["sentence"][shown["span"][0]:shown["span"][1]] == "चापि"
    with pytest.raises(ValueError):
        devanagari_view({**item, "span": [4, 7], "surface": "Api"})


def row(example_id, group, sentence, candidates, gold=0, rule="SDH-001"):
    surface = sentence.split()[0]
    return {"example_id": example_id, "source_group": group, "source_sentence": sentence,
            "source_span": [0, len(surface)], "source_surface": surface, "rule_id": rule,
            "candidates": [{"left": l, "right": r} for l, r in candidates], "gold_indices": [gold],
            "left": candidates[gold][0], "right": candidates[gold][1],
            "left_lemma": candidates[gold][0], "right_lemma": candidates[gold][1]}


def test_build_excludes_evaluation_data_and_draws_controls():
    common = [row(f"c{i}", f"g{i}", f"cApi x{i}", [("ca", "api"), ("cA", "Api")]) for i in range(6)]
    train = common + [row("w", "gw", "tvapi z", [("tu", "api"), ("tU", "Api")]),
                      row("bad", "excluded", "cApi y", [("ca", "api")]),
                      row("sent", "g-sent", "cApi held out", [("ca", "api")])]
    items, key = build_pilot_set.build(train, {"excluded"}, {"cApi held out"}, real=2, controls=2, seed=1)
    sources = {k["source_id"] for k in key}
    assert not sources & {"bad", "sent"}
    assert Counter(k["kind"] for k in key) == {"real": 2, "control_correct": 1, "control_wrong": 1}
    assert [i["item_id"] for i in items] == ["P-001", "P-002", "P-003", "P-004"]
    wrong = next(k for k in key if k["kind"] == "control_wrong")
    shown = next(i for i in items if i["item_id"] == wrong["item_id"])
    assert (shown["proposed_left"], shown["proposed_right"]) == ("cA", "Api")


def answer(item_id, decision, left="", right=""):
    return {"item_id": item_id, "decision": decision, "left": left, "right": right, "notes": ""}


def test_scoring_rewards_accuracy_and_queues_unresolved_items():
    items = [{"item_id": "P-1", "surface": "cApi", "proposed_left": "cA", "proposed_right": "api"},
             {"item_id": "P-2", "surface": "cApi", "proposed_left": "ca", "proposed_right": "api"},
             {"item_id": "P-3", "surface": "cApi", "proposed_left": "cA", "proposed_right": "Api"},
             {"item_id": "C-1", "surface": "cApi", "proposed_left": "ca", "proposed_right": "api"},
             {"item_id": "C-2", "surface": "cApi", "proposed_left": "cA", "proposed_right": "Api"}]
    key = [{"item_id": "P-1", "kind": "real"}, {"item_id": "P-2", "kind": "real"}, {"item_id": "P-3", "kind": "real"},
           {"item_id": "C-1", "kind": "control_correct", "expected": "correct", "dcs_left": "ca", "dcs_right": "api"},
           {"item_id": "C-2", "kind": "control_wrong", "expected": "wrong", "dcs_left": "ca", "dcs_right": "api"}]
    careful = [answer("P-1", "wrong", "ca", "api"), answer("P-2", "correct"), answer("P-3", "wrong", "x", "y"),
               answer("C-1", "correct"), answer("C-2", "wrong", "ca", "api")]
    second = [answer("P-1", "wrong", "ca", "api"), answer("P-2", "correct"), answer("P-3", "wrong", "x", "y"),
              answer("C-1", "correct"), answer("C-2", "wrong", "ca", "api")]
    yes_man = [answer(i["item_id"], "correct") for i in items]
    result = score_pilot.score(items, key, {"careful": careful, "second": second, "yes": yes_man}, RULES)
    r = result["reviewers"]
    assert r["careful"]["control_accuracy"] == 1.0 and r["yes"]["control_accuracy"] == 0.5
    assert result["resolved"]["P-1"] == {**result["resolved"]["P-1"], "status": "resolved", "decision": "wrong",
                                         "correction": ["ca", "api"], "derivable": True}
    assert result["resolved"]["P-3"]["status"] == "outside_rule_inventory"
    assert set(result["expert_queue"]) == {"P-1", "P-3"}
    # careful: P-1 accepted correction 3, P-2 agreement 1, P-3 unresolved 0, controls 2 + 3
    assert r["careful"]["points"] == 9
    assert r["careful"]["on_leaderboard"] and not r["yes"]["on_leaderboard"]


def test_fleiss_kappa():
    assert score_pilot.fleiss_kappa([[2, 0], [0, 2]]) == pytest.approx(1.0)
    assert score_pilot.fleiss_kappa([[1, 1], [1, 1]]) == pytest.approx(-1.0)
    assert score_pilot.fleiss_kappa([]) is None
