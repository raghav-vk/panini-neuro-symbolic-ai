"""Rule-independent DCS alignment into silver external vowel-sandhi examples."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from panini.dcs import external_vowel_boundaries
from panini.translit import iast_hiatus_ambiguous, iast_to_slp1, is_slp1_word, slp1_to_iast
from panini.experiment_data import validate_reviewed, validate_silver
from panini.rules import load_rules
from extract_dcs_boundaries import label

RULES = load_rules(ROOT / "data/rules/development_sandhi.jsonl")


def record(sentence, lemmas, cng, sent_id=7):
    return {"sentence": sentence, "lemmas": lemmas, "cng": cng, "sent_id": sent_id,
            "dcs_chunks": [x for group in lemmas for x in group]}


def extract(*args, **kwargs):
    return list(external_vowel_boundaries(record(*args), **kwargs))


def test_iast_slp1_roundtrip():
    for word in ["cāpi", "caiva", "ṛṣi", "mahārṣi", "uparatnacatuṣṭayam", "kṛṣṇaḥ"]:
        assert slp1_to_iast(iast_to_slp1(word)) == word
    assert iast_to_slp1("caiva") == "cEva"
    assert slp1_to_iast("a~") == "am\u0310"  # anunāsika
    assert iast_to_slp1("am\u0310") == iast_to_slp1("a~") == "a~" and is_slp1_word("a~")
    assert iast_hiatus_ambiguous("caiva") and not iast_hiatus_ambiguous("cāpi")
    assert slp1_to_iast("kąp", strict=False) == "kąp"
    with pytest.raises(ValueError):
        slp1_to_iast("kąp")
    assert is_slp1_word("cEva") and is_slp1_word("atho'pi") and not is_slp1_word("cāpi")


def test_indeclinable_left_aligns_with_observed_junction():
    [(example, reason)] = extract("rAmaH cApi gacCati", [["rāma"], ["ca", "api"], ["gam"]], [["29"], ["2", "2"], ["-190"]])
    assert reason is None
    assert (example["left"], example["right"], example["surface"]) == ("ca", "api", "cApi")
    assert example["observed_junction"] == "A" and example["vowel_pair"] == ["a", "a"]
    assert example["source_sentence"][slice(*example["source_span"])] == "cApi"
    assert example["context"] == "rAmaH _ gacCati"
    assert set(example["context_lemmas"]) == {"rAma", "gam"}
    assert label(example, RULES)["rule_id"] == "SDH-001"


def test_right_word_spans_its_compound_to_the_chunk_end():
    [(example, _)] = extract("coparatnacatuzwayam", [["ca", "uparatna", "catuṣṭaya"]], [["2", "3", "31"]])
    assert (example["left"], example["right"]) == ("ca", "uparatnacatuzwayam")
    assert example["observed_junction"] == "o" and example["context"] == ""
    assert example["context_lemmas"] == ["catuzwaya"]
    assert label(example, RULES)["rule_id"] == "SDH-004"


def test_vrddhi_junction_is_labelled_by_the_added_rule():
    [(example, _)] = extract("cEva", [["ca", "eva"]], [["2", "2"]])
    assert example["observed_junction"] == "E"
    assert label(example, RULES)["rule_id"] == "SDH-013"


def test_uncovered_junction_is_labelled_unsupported():
    # Purvarupa (6.1.109) is not encoded yet.
    example = {"left": "atho", "right": "api", "surface": "atho'pi", "tags": ["pada_boundary"]}
    assert label(example, RULES)["rule_id"] == "UNSUPPORTED"


@pytest.mark.parametrize("sentence, lemmas, cng, reason", [
    ("devAtra", [["deva", "atra"]], [["39", "2"]], "inflected_left_form_unknown"),
    ("rAjendraH", [["rāja", "indra"]], [["3", "29"]], "compound_internal_left"),
    ("tatOcApi", [["tatas", "ca", "api"]], [["2", "2", "2"]], "left_not_chunk_initial"),
    ("cApyeva", [["ca", "api", "eva"]], [["2", "2", "2"]], "right_end_fused"),
    ("cApi gacCati", [["ca", "api"]], [["2", "2"]], "chunk_group_mismatch"),
    ("cAti", [["ca", "api"]], [["2", "2"]], "junction_unresolved"),
    ("cAsIt", [["ca", "as"]], [["2", "-23"]], "right_verb_initial_uncertain"),
    ("maharzayaH", [["mahā", "ṛṣi"]], [["2", "39"]], "left_compound_prefix"),
])
def test_boundaries_without_determined_forms_are_rejected(sentence, lemmas, cng, reason):
    results = extract(sentence, lemmas, cng)
    assert reason in [r for _, r in results]
    assert not any(example for example, _ in results)


def test_silver_examples_validate_but_never_pass_as_reviewed():
    [(example, _)] = extract("cApi", [["ca", "api"]], [["2", "2"]])
    label(example, RULES)
    assert validate_silver(dict(example), RULES)["family"] != "unsupported"
    with pytest.raises(ValueError, match="independent review"):
        validate_reviewed(dict(example), RULES)
    with pytest.raises(ValueError, match="reviewer confirmation"):
        validate_silver({**example, "external_boundary_confirmed": True}, RULES)
    with pytest.raises(ValueError, match="extractor"):
        validate_silver({**example, "review_status": "expert_reviewed"}, RULES)


def test_cli_extracts_and_prepares_silver_splits(tmp_path):
    rows = [record("cApi", [["ca", "api"]], [["2", "2"]], 1),
            record("tatra coparatnam", [["tatra"], ["ca", "uparatna"]], [["2"], ["2", "29"]], 2),
            record("devAtra", [["deva", "atra"]], [["39", "2"]], 3)]
    sentences = tmp_path / "sentences.jsonl"
    sentences.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    extracted, prepared = tmp_path / "silver", tmp_path / "prepared"
    subprocess.run([sys.executable, str(ROOT / "scripts/extract_dcs_boundaries.py"), "--sentences", str(sentences),
                    "--output", str(extracted)], check=True, capture_output=True)
    report = json.loads((extracted / "report.json").read_text())
    assert report["counts"]["extracted"] == 2 and report["counts"]["inflected_left_form_unknown"] == 1
    assert report["review_sample"]["size"] == 2
    subprocess.run([sys.executable, str(ROOT / "scripts/prepare_experiment.py"), "--silver-examples",
                    str(extracted / "examples.jsonl"), "--output", str(prepared)], check=True, capture_output=True)
    assert json.loads((prepared / "manifest.json").read_text())["data_kind"] == "dcs_silver_alignment"


def test_right_word_holdout_shares_left_words_and_counts_types_once():
    from panini.experiment_data import split_examples
    rows = []
    for i, right in enumerate(["api", "atra", "anya", "artha", "eva", "iti", "upari", "asya"] * 3):
        surface = iast_to_slp1("c" + {"a": "ā", "e": "ai", "i": "e", "u": "o"}[right[0]] + right[1:])
        [(example, _)] = external_vowel_boundaries(record(surface, [["ca", right]], [["2", "2"]], sent_id=i))
        rows.append({**label(example, RULES), "context": f"ctx{i}", "context_lemmas": [f"ctx{i}"]})
    splits, audit = split_examples(rows, "strict_right_lemma")
    assert audit["duplicates_removed"] == 16  # contexts differ, but each analysis type is kept once
    assert sum(len(v) for v in splits.values()) == 8
    assert all(o["right_word_lemmas"] == 0 for o in audit["overlaps"].values())
