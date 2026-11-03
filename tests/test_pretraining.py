"""Pretraining corpora filters, rule-guided near misses and the pretraining encoder."""

import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.pretraining import (MASK, alter_words, build_corpora, corpus_vocabulary, encode, mask_spans,
                                near_misses, normalize, vowel_confusions, word_ids)
from panini.rules import load_rules

HELD = "tatra Svetena haMsena gacCati devadattaH saha"
# Two distinct shared 30-character spans with HELD (31 shared characters) against one.
NEAR = "anyat Svetena haMsena gacCati devadattaH"
ONE_SPAN = "Svetena haMsena gacCati devada iti"


def sentence(sent_id, text, lemmas=(("tatra",),)):
    return {"sent_id": sent_id, "sentence": text, "lemmas": [list(w) for w in lemmas]}


def corpora(extra, lemmas=frozenset()):
    return build_corpora([sentence(1, HELD), *extra], {1}, set(lemmas))


def test_normalize_collapses_whitespace():
    assert normalize("  kroDas  tvapaRqitEH \t SaSvat   ") == "kroDas tvapaRqitEH SaSvat"


def test_held_out_sentences_are_removed():
    pa, pb, removed = corpora([sentence(2, "rAmo vanaM gacCati")])
    assert [r["sent_id"] for r in pa] == [r["sent_id"] for r in pb] == [2]
    assert removed["held_out"] == [1]


def test_exact_duplicates_are_removed_after_normalisation():
    pa, _, removed = corpora([sentence(2, "  " + HELD.replace(" ", "   ") + "  ")])
    assert pa == []
    assert removed["exact_duplicate"] == [{"sent_id": 2, "copy_of": 1}]


def test_near_duplicates_need_two_shared_spans():
    pa, _, removed = corpora([sentence(2, NEAR), sentence(3, ONE_SPAN)])
    assert [r["sent_id"] for r in pa] == [3]
    assert [r["sent_id"] for r in removed["near_duplicate"]] == [2]
    assert removed["near_duplicate"][0]["closest"] == 1


def test_missing_held_out_id_is_an_error():
    with pytest.raises(ValueError):
        build_corpora([sentence(2, "rAmo vanaM gacCati")], {1}, set())


def test_p_b_drops_held_lemmas_matched_in_slp1():
    # DCS_pick lemmas are IAST; held-out right-word lemmas are SLP1.
    rows = [sentence(2, "rAmo vanaM gacCati", [("rāma",), ("vana",), ("gam",)]),
            sentence(3, "sItA tatra", [("sītā",), ("tatra",)])]
    pa, pb, removed = corpora(rows, {"vana"})
    assert [r["sent_id"] for r in pa] == [2, 3]
    assert [r["sent_id"] for r in pb] == [3]
    assert removed["held_lemma"] == [2]
    _, pb, _ = corpora(rows, {"sItA"})
    assert [r["sent_id"] for r in pb] == [2]


def test_corpus_rows_carry_text_only():
    pa, _, _ = corpora([sentence(2, "rAmo vanaM gacCati")])
    assert set(pa[0]) == {"sent_id", "text"}


def test_vowel_confusions_come_from_the_rules():
    confusions = vowel_confusions(load_rules(ROOT / "data/rules/development_sandhi.jsonl"))
    assert confusions["initial"] == {"A": ["a"], "E": ["e"], "I": ["i"], "O": ["o"], "U": ["u"],
                                     "a": ["A"], "e": ["E"], "i": ["I"], "o": ["O"], "u": ["U"]}
    assert confusions["final"] == {"A": ["a"], "I": ["i"], "U": ["u"], "a": ["A"], "i": ["I"], "u": ["U"]}


CONFUSIONS = {"initial": {"a": ["A"], "A": ["a"]}, "final": {"a": ["A"], "A": ["a"]}}


def test_near_misses_exclude_attested_words():
    assert near_misses("Agata", CONFUSIONS, set()) == ["AgatA", "agata"]
    assert near_misses("Agata", CONFUSIONS, {"agata"}) == ["AgatA"]
    assert near_misses("gam", CONFUSIONS, set()) == []
    assert corpus_vocabulary(["ca Agata", "ca"]) == {"ca", "Agata"}


def test_alter_words_labels_altered_attested_and_unalterable():
    text, labels = alter_words("Agata gam ca", CONFUSIONS, {"ca", "cA"}, random.Random(0), rate=1.0)
    words = text.split(" ")
    assert labels == [1, -100, -100]
    assert words[0] in {"agata", "AgatA"} and words[1:] == ["gam", "ca"]
    text, labels = alter_words("Agata gam", CONFUSIONS, set(), random.Random(0), rate=0.0)
    assert (text, labels) == ("Agata gam", [0, -100])


def test_mask_spans_hits_the_rate_and_keeps_labels():
    tokens = encode("a" * 200)
    inputs, labels = mask_spans(tokens, random.Random(3))
    masked = [i for i, x in enumerate(inputs) if x == MASK]
    assert len(masked) == 30
    assert all(labels[i] == tokens[i] for i in masked)
    assert all(labels[i] == -100 for i in range(200) if i not in masked)


def test_word_ids_skip_spaces():
    assert word_ids("ca Agata") == [0, 0, -1, 1, 1, 1, 1, 1]


def test_encoder_losses_and_ranker_compatible_names():
    torch = pytest.importorskip("torch")
    from panini.pretraining import batch_disc, batch_mlm, disc_loss, make_encoder, mlm_loss
    from panini.ranking import make_transformer
    torch.manual_seed(0)
    model = make_encoder(width=16, layers=1, heads=2, max_length=64)
    rng = random.Random(0)
    texts = ["ca Agata", "Agata gam ca Agata"]
    loss, correct, total = mlm_loss(model, *batch_mlm(texts, rng, "cpu"))
    assert loss.item() > 0 and 0 <= correct <= total
    loss, counts = disc_loss(model, *batch_disc(texts, CONFUSIONS, set(), rng, "cpu"))
    loss.backward()
    assert counts["altered"].item() + counts["attested"].item() == 5  # gam has no near miss
    ranker = make_transformer(width=16, layers=1, heads=2, max_length=64)
    shared = {k for k in ranker.state_dict() if not k.startswith("output")}
    assert shared <= set(model.state_dict())


def test_dcs_pick_vowel_characters_are_mapped_and_markers_dropped():
    assert normalize("BrAtṝn k±pta ²") == "BrAtFn kxpta X"
    pa, _, removed = corpora([sentence(2, "nABimUle sTitaM [... O6 ZeiCenJ]"), sentence(3, "BrAtṝn sarvAn")])
    assert [r["text"] for r in pa] == ["BrAtFn sarvAn"]
    assert removed["not_slp1"] == [2]


ROW = {"source_sentence": "kroDas tvapaRqitEH  SaSvat", "source_span": [7, 18],
       "candidates": [{"left": "tu", "right": "apaRqitEH"}, {"left": "tU", "right": "apaRqitEH"}]}


def test_candidate_text_puts_the_words_back_in_the_sentence():
    from panini.pretraining import candidate_text
    assert candidate_text(ROW, ROW["candidates"][0]) == ("kroDas tu apaRqitEH SaSvat", 1)
    assert candidate_text(ROW, ROW["candidates"][1], context=False) == ("tU apaRqitEH", 0)
    assert candidate_text({**ROW, "source_span": [0, 6]}, {"left": "kro", "right": "Das"}) == ("kro Das tvapaRqitEH SaSvat", 0)


def test_neural_scores_are_log_probabilities_per_word():
    pytest.importorskip("torch")
    from panini.pretraining import make_encoder, neural_lexicon_scores
    scores = neural_lexicon_scores(make_encoder(width=16, layers=1, heads=2, max_length=64, dropout=0.0), [ROW], "cpu")
    assert len(scores) == 2 and all(len(s) == 2 and all(x < 0 for x in s) for s in scores)
    assert scores[0][1] != scores[1][1]  # the right word's score sees its neighbour


def test_ranker_starts_from_the_pretrained_encoder():
    torch = pytest.importorskip("torch")
    from panini.pretraining import init_from_pretrained, make_encoder
    from panini.ranking import make_transformer
    encoder = make_encoder(width=16, layers=1, heads=2, max_length=8)
    ranker = make_transformer(width=16, layers=1, heads=2, max_length=12, pooling="cls")
    init_from_pretrained(ranker, {"state_dict": encoder.state_dict()})
    assert torch.equal(ranker.embedding.weight, encoder.embedding.weight[:258])
    assert torch.equal(ranker.position.weight[:8], encoder.position.weight)
    assert torch.equal(ranker.encoder.layers[0].linear1.weight, encoder.encoder.layers[0].linear1.weight)
    with pytest.raises(ValueError):
        init_from_pretrained(make_transformer(width=32, layers=1, heads=2), {"state_dict": encoder.state_dict()})


def test_neural_features_sit_before_the_boundary_vowel_feature():
    from panini.ranking import build_lexicon, feature_count, lexical_features
    row = {"left": "tu", "right": "apaRqitEH", "rule_id": "SDH-006"}
    candidate = {"left": "tU", "right": "apaRqitEH", "proofs": [{"rule_id": "SDH-006"}],
                 "neural_left": -2.5, "neural_right": -0.1}
    lexicon = build_lexicon([row], neural=True, boundary_vowels=True)
    features = lexical_features(lexicon, row, candidate)
    assert feature_count(lexicon) == len(features) == 8
    assert features[-3:] == [-2.5, -0.1, 1.0]
