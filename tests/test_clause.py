"""RLCD clause schema, constraint layer and Vidyut compilation (plan stage 2)."""

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.clause import (VIOLATIONS, check, load_karmakatva, load_stems, read_tsv, schema, structural_errors,
                           vibhakti)

FIXTURES = [json.loads(line) for line in (ROOT / "data/rlcd/clause_fixtures.jsonl").read_text().splitlines()]
DHATUPATHA_TSV = ROOT / "data/external/vidyut-0.4.0/prakriya/dhatupatha.tsv"
GANAS = ["Bhvadi", "Adadi", "Juhotyadi", "Divadi", "Svadi", "Tudadi", "Rudhadi", "Tanadi", "Kryadi", "Curadi"]


def dhatupatha():
    """(code, aupadeshika, gana) from the Dhatupatha file; gana from the code's first two digits.

    Rows whose root is "-" are placeholders, which Vidyut's loader also skips.
    """
    return {(r["code"], r["dhatu"], GANAS[int(r["code"][:2]) - 1]) for r in read_tsv(DHATUPATHA_TSV) if r["dhatu"] != "-"}


def test_fixture_ids_are_unique_and_codes_are_known():
    assert len({f["id"] for f in FIXTURES}) == len(FIXTURES)
    assert {c for f in FIXTURES for c in f["violations"]} <= set(VIOLATIONS)


def test_every_table_root_is_its_dhatupatha_entry():
    index = dhatupatha()
    for row in read_tsv(ROOT / "data/rlcd/dhatu_constraints.tsv"):
        assert (row["code"], row["aupadeshika"], row["gana"]) in index, row
        assert row["karmakatva"] in {"sakarmaka", "akarmaka"}
        assert row["status"] == "draft_unreviewed"


def test_stem_table_fields():
    for stem, entry in load_stems().items():
        assert entry["kind"] in {"basic", "nyap"}, stem
        assert entry["lingas"] <= {"Pum", "Stri", "Napumsaka"}, stem
        assert not re.search("[kgcjwqtdpb]h", stem), f"{stem}: SLP1 writes aspirates as capitals (raTa, not ratha)"


def test_schema_rejects_shape_errors():
    good = FIXTURES[0]["clause"]
    assert structural_errors(good) == []
    assert structural_errors({**good, "extra": 1}) == ["unknown field extra"]
    assert "missing lakara" in structural_errors({k: v for k, v in good.items() if k != "lakara"})
    bad = {**good, "participants": [{**good["participants"][0], "role": "sambanDa_zazWI"}]}
    assert structural_errors(bad) == ["participant 0 role 'sambanDa_zazWI' not allowed"]
    assert schema()["$defs"]["role"]["enum"] == ["kartf", "karman", "karaRa", "aDikaraRa"]


def test_vibhakti_follows_prayoga():
    assert vibhakti("kartf", "Kartari") == "Prathama" and vibhakti("kartf", "Karmani") == "Trtiya"
    assert vibhakti("karman", "Karmani") == "Prathama" and vibhakti("aDikaraRa", "Kartari") == "Saptami"


@pytest.mark.parametrize("fixture", [f for f in FIXTURES if "NO_DERIVATION" not in f["violations"]],
                         ids=lambda f: f["id"])
def test_pure_layer_matches_fixtures(fixture):
    """Every violation except NO_DERIVATION is decided without Vidyut."""
    got = sorted(v.code for v in check(fixture["clause"], dhatupatha(), load_karmakatva(), load_stems()))
    assert got == fixture["violations"]


@pytest.fixture(scope="module")
def compiler():
    pytest.importorskip("vidyut")
    if not (ROOT / "data/external/vidyut-0.4.0/kosha").exists():
        pytest.skip("Vidyut data not fetched (scripts/fetch_vidyut_data.py)")
    from panini.derive import Compiler
    return Compiler()


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["id"])
def test_compiler_matches_fixtures(compiler, fixture):
    result = compiler.compile_clause(fixture["clause"])
    assert result["valid"] == fixture["valid"]
    assert sorted(v["code"] for v in result["violations"]) == fixture["violations"]
    if fixture["valid"]:
        assert [sorted(f["text"] for f in w["forms"]) for w in result["words"]] == fixture["words"]
        assert all(f["sutras"] for w in result["words"] for f in w["forms"])


def test_compiler_index_matches_the_dhatupatha_file(compiler):
    assert compiler.dhatupatha == dhatupatha()


def test_dataset_structure_example_compiles(compiler):
    record = json.loads((ROOT / "docs/dataset-structure.json").read_text())
    result = compiler.compile_clause(record["rlcd_ast"])
    assert result["valid"] and result["text"] == record["target_sanskrit_slp1_pausal"]
