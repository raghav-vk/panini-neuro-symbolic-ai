"""External word-list flags: pausal normalisation, annotation and ranker features."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))
from panini.lexicon import annotate, pausal_variants
from panini.ranking import build_lexicon, feature_count, lexical_features


class FakeLexicon:
    def __init__(self, words):
        self.words = words

    def known(self, iast):
        return iast in self.words


@pytest.mark.parametrize("surface, pausal", [("asurAH", "asurAs"), ("udakaM", "udakam"), ("Adityo", "Adityas"),
                                             ("etaj", "etat"), ("apravfttiS", "apravfttis"), ("deva", "devas")])
def test_pausal_variants_undo_word_final_sandhi(surface, pausal):
    assert {surface, pausal} <= pausal_variants(surface)


def test_annotation_and_features_use_candidate_strings_only():
    row = {"left": "ca", "right": "āgata", "rule_id": "SDH-001",
           "candidates": [{"left": "ca", "right": "āgata", "proofs": [{"rule_id": "SDH-001"}]},
                          {"left": "ca", "right": "agata", "proofs": [{"rule_id": "SDH-001"}]}]}
    annotate([row], FakeLexicon({"ca", "āgata"}))
    assert [(c["kosha_left"], c["kosha_right"]) for c in row["candidates"]] == [(True, True), (True, False)]
    lexicon = build_lexicon([row], external=True)
    assert feature_count(lexicon) == 7 == len(lexical_features(lexicon, row, row["candidates"][0]))
    assert lexical_features(lexicon, row, row["candidates"][1])[-2:] == [1.0, 0.0]
    assert len(lexical_features(build_lexicon([row]), row, row["candidates"][0])) == feature_count(build_lexicon([row])) == 5


def test_external_ranker_trains_and_roundtrips(tmp_path):
    torch = pytest.importorskip("torch")
    from test_development_pipeline import enriched
    from panini.ranking import make_transformer, predict_neural, train_neural
    rows = enriched()
    annotate(rows, FakeLexicon({c["left"] for r in rows[::2] for c in r["candidates"]}))
    model, _ = train_neural(rows[:40], rows[40:50], epochs=1, width=16, layers=1, external_lexicon=True)
    assert model.lexicon["external"] and model.lexical.in_features == 7
    path = tmp_path / "model.pt"
    torch.save({"state_dict": model.state_dict(), "lexicon": model.lexicon}, path)
    state = torch.load(path, weights_only=True)
    restored = make_transformer(width=16, layers=1, lexicon=state["lexicon"])
    restored.load_state_dict(state["state_dict"])
    assert predict_neural(model, rows[50:60]) == predict_neural(restored, rows[50:60])
