"""Cross-family rules, safe conversion, leakage controls and trainable ranking."""

import copy
import json
import pickle
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.rules import load_rules, apply_rule, RuleValidationError
from panini.candidates import enumerate_candidates, forward, gold_indices
from panini.dcs import decode_record, DCSDecodeError, slp1_to_iast, boundary_proposals
from panini.experiment_data import synthetic_examples, split_examples, validate_reviewed
from panini.ranking import Baseline, metrics, model_text, select_threshold

RULES = load_rules(ROOT / "data/rules/development_sandhi.jsonl")
CHECKS = [json.loads(line) for line in (ROOT / "data/rules/development_checks.jsonl").read_text().splitlines()]


@pytest.mark.parametrize("rule", RULES, ids=lambda r: r.rule_id)
def test_draft_positive_and_inverse_roundtrip(rule):
    for example in rule.examples:
        candidates = enumerate_candidates(example.surface, RULES, example.tags)
        assert any(c["left"] == example.left and c["right"] == example.right for c in candidates)
        for candidate in candidates:
            assert all(p["output"] == example.surface for p in candidate["proofs"])


@pytest.mark.parametrize("check", CHECKS, ids=lambda c: c["rule_id"] + "-" + c["reason"])
def test_negative_checks(check):
    rule = next(r for r in RULES if r.rule_id == check["rule_id"])
    assert apply_rule(rule, check["left"], check["right"], check["tags"]) is None


def test_drafts_cannot_pass_publication_gate():
    with pytest.raises(RuleValidationError, match="publication gate"):
        load_rules(ROOT / "data/rules/development_sandhi.jsonl", publication_ready=True)


def test_registry_blocks_unknown_and_contradictory_tags():
    with pytest.raises(RuleValidationError, match="unregistered"):
        enumerate_candidates("x", RULES, ["made_up_condition"])
    assert apply_rule(RULES[0], "a", "a", ["pada_boundary", "compound_internal"]) is None
    with pytest.raises(TypeError):
        enumerate_candidates("a", RULES, "pada_boundary")


def test_precedence_is_pair_local_and_optional_retains_alternative():
    rule = RULES[0]
    high = replace(rule, rule_id="SDH-099", precedence=999,
                   operation=replace(rule.operation, emit="X"))
    assert [t.rule_id for t in forward([rule, high], "a", "a", ["pada_boundary"])] == ["SDH-099"]
    assert len(forward([rule, replace(high, optional=True)], "a", "a", ["pada_boundary"])) == 2
    # Other underlying pairs are not suppressed merely because a priority is high.
    high = replace(RULES[1], precedence=999)
    assert any(c["left"] == "a" for c in enumerate_candidates("ā", [rule, high], ["pada_boundary"]))


def state():
    return {"lemmas": [["ābhīra", "gopāla"], ["ca"]], "cng": [["3", "39"], ["2"]],
            "dcs_chunks": ["ābhīra", "gopāla", "ca"], "sentence": "ABIrAgopAlA ca", "sent_id": 100}


def legacy(value):
    # Test-owned primitive fixture serialization only, never external unpickling.
    return b"(i__main__\nDCS\n" + pickle.dumps(value, protocol=0)[:-1] + b"b."


def test_decoder_preserves_nested_annotations_and_proposes_not_gold():
    result = decode_record(legacy(state()))
    assert result == state()
    proposals = list(boundary_proposals(result))
    assert len(proposals) == 2
    assert proposals[0]["left"] is None
    assert proposals[0]["boundary_kind"] == "within_chunk"
    assert proposals[1]["boundary_kind"] == "between_chunks"
    assert slp1_to_iast("rAmaH gacCati") == "rāmaḥ gacchati"


@pytest.mark.parametrize("payload", [b"cos\nsystem\n(S'touch /tmp/never'\ntR.", b"(iother\nDCS\n.", b"N.", b"garbage", b"", b"(i__main__\nDCS\n(dp0\nS'a'\ng0\nsb."])
def test_decoder_rejects_unsafe_or_malformed_records(payload):
    with pytest.raises(DCSDecodeError):
        decode_record(payload)


def test_decoder_rejects_trailing_bytes_size_and_alignment():
    for payload in [legacy(state()) + b"x", legacy({**state(), "cng": []})]:
        with pytest.raises(DCSDecodeError):
            decode_record(payload)
    with pytest.raises(DCSDecodeError, match="byte limit"):
        decode_record(legacy(state()), max_bytes=2)


@pytest.mark.parametrize("method", ["source_random", "pair", "strict_lemma", "strict_right_lemma"])
def test_splits_are_reproducible_and_grouped(method):
    records = synthetic_examples(RULES, per_rule=40)
    first, audit = split_examples(records, method)
    second, _ = split_examples(list(reversed(records)), method)
    assert first == second
    assert sum(audit["counts"].values()) == len(records)
    for overlap in audit["overlaps"].values():
        assert overlap["sources"] == overlap["surfaces"] == 0
        if method == "strict_lemma":
            assert overlap["lemmas_including_context"] == 0


def test_context_participates_in_strict_holdout():
    records = synthetic_examples(RULES[:1], per_rule=100)
    for record in records:
        record["context"] = "shared word"
        record["context_lemmas"] = ["shared"]
    splits, audit = split_examples(records, "strict_lemma")
    assert sum(bool(splits[name]) for name in ("train", "dev", "test")) <= 1
    assert audit["counts"]["mixed"] > 0


def test_duplicate_source_linkage_is_preserved():
    rows = synthetic_examples(RULES[:1], per_rule=20)
    duplicate = {**rows[0], "example_id": "duplicate", "source_group": rows[1]["source_group"]}
    splits, audit = split_examples([*rows, duplicate], "source_random")
    assert audit["duplicates_removed"] == 1
    location = {r["example_id"]: name for name, items in splits.items() for r in items}
    assert location[rows[0]["example_id"]] == location[rows[1]["example_id"]]


def test_pending_dcs_cannot_be_used_as_gold():
    with pytest.raises(ValueError, match="independent review"):
        validate_reviewed(next(boundary_proposals(state())), RULES)


def test_lemma_whitespace_does_not_create_holdout_aliases():
    rows = synthetic_examples(RULES[:1], per_rule=40)
    clean, _ = split_examples(rows, "strict_lemma")
    for row in rows:
        row["left_lemma"] = " " + row["left_lemma"] + " "
    spaced, _ = split_examples(rows, "strict_lemma")
    assert clean == spaced


def test_reviewed_surface_alignment_and_unsupported_coverage():
    row = next(boundary_proposals(state()))
    row.update(review_status="expert_reviewed", reviewer="Test-only fixture", reviewed_at="2026-09-14",
               left="x", right="y", surface="ābhīrā", source_span=[0, 6], rule_id="unsupported",
               external_boundary_confirmed=True, tags=["pada_boundary"])
    assert validate_reviewed(row, RULES)["family"] == "unsupported"
    row["source_span"] = [1, 6]
    with pytest.raises(ValueError, match="source span"):
        validate_reviewed(row, RULES)


def enriched(per_rule=10):
    result = synthetic_examples(RULES, per_rule)
    for row in result:
        row["candidates"] = enumerate_candidates(row["surface"], RULES, row["tags"])
        row["gold_indices"] = gold_indices(row, row["candidates"])
    return result


def test_metrics_include_coverage_failures_and_multiple_gold():
    row = enriched(1)[0]
    row["gold_indices"] = [0, 1]
    uncovered = {**row, "example_id": "missing", "candidates": [], "gold_indices": []}
    result, _ = metrics([row, uncovered], [[0.0] * len(row["candidates"]), []])
    assert result["candidate_recall"] == result["top1"] == 0.5
    assert result["conditional_top1"] == 1
    assert result["abstention_rate"] == 0.5
    assert select_threshold([uncovered], [[]]) > 1


def test_model_input_never_reads_gold_fields_and_empty_context_ablation_is_identical():
    row = enriched(1)[0]
    candidate = row["candidates"][0]
    text = model_text(row, candidate)
    row.update(left="SECRET", right="SECRET", rule_id="SECRET", left_lemma="SECRET", gold_indices=[999])
    assert model_text(row, candidate) == text
    assert "SECRET" not in text
    assert model_text(row, candidate, use_context=False) == text


def test_tiny_ranker_trains_and_roundtrips(tmp_path):
    torch = pytest.importorskip("torch")
    from panini.ranking import train_neural, predict_neural, make_transformer
    rows = enriched(5)
    model, info = train_neural(rows[:40], rows[40:50], epochs=1, width=16, layers=1)
    scores = predict_neural(model, rows[50:60])
    assert info["parameters"] < 100_000
    assert len(scores) == 10
    path = tmp_path / "model.pt"
    torch.save(model.state_dict(), path)
    restored = make_transformer(width=16, layers=1)
    restored.load_state_dict(torch.load(path, weights_only=True))
    assert predict_neural(restored, rows[50:60]) == scores


def test_cli_prepares_and_runs_baselines(tmp_path):
    data, output = tmp_path / "data", tmp_path / "run"
    subprocess.run([sys.executable, str(ROOT / "scripts/prepare_experiment.py"), "--per-rule", "40", "--output", str(data)], check=True, capture_output=True)
    command = [sys.executable, str(ROOT / "scripts/run_experiment.py"), "--data", str(data), "--output", str(output), "--baselines-only"]
    subprocess.run(command, check=True, capture_output=True)
    assert len(json.loads((output / "results.json").read_text())["results"]) == 16
    subprocess.run([sys.executable, str(ROOT / "scripts/verify_run.py"), "--data", str(data), "--run", str(output)], check=True, capture_output=True)
    with (data / "source_random/train.jsonl").open("a") as handle:
        handle.write("\n")
    command[command.index(str(output))] = str(tmp_path / "tampered")
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode != 0 and "hash mismatch" in result.stderr


def test_tie_averaged_top1_removes_index_tie_break():
    row = {"example_id": "x", "rule_id": "SDH-001", "surface": "ā", "gold_indices": [0],
           "candidates": [{"left": "a", "right": "a", "proofs": []}, {"left": "ā", "right": "a", "proofs": []}]}
    result, _ = metrics([row], [[0.0, 0.0]])
    assert result["top1"] == 1.0 and result["top1_tie_averaged"] == 0.5 and result["tied_top_rows"] == 1
    result, _ = metrics([row], [[1.0, 0.0]])
    assert result["top1_tie_averaged"] == 1.0 and result["tied_top_rows"] == 0


def test_frequency_short_vowel_breaks_frequency_ties_toward_short_vowels():
    from panini.ranking import Baseline
    row = {"candidates": [{"left": "ca", "right": "āpi", "proofs": []}, {"left": "ca", "right": "api", "proofs": []}]}
    scores = Baseline("frequency_short_vowel", []).score(row)
    assert scores[1] > scores[0]


@pytest.mark.parametrize("pooling, mark_boundary", [("cls", False), ("mean", True)])
def test_ranker_options_train_and_roundtrip(tmp_path, pooling, mark_boundary):
    torch = pytest.importorskip("torch")
    from panini.ranking import train_neural, predict_neural, make_transformer
    rows = enriched()
    model, _ = train_neural(rows[:40], rows[40:50], epochs=1, width=16, layers=1, pooling=pooling, mark_boundary=mark_boundary)
    path = tmp_path / "model.pt"
    torch.save(model.state_dict(), path)
    restored = make_transformer(width=16, layers=1, pooling=pooling, mark_boundary=mark_boundary)
    restored.load_state_dict(torch.load(path, weights_only=True))
    assert predict_neural(model, rows[50:60]) == predict_neural(restored, rows[50:60])
