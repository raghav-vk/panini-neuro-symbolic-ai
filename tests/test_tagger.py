"""RLCD stage 3 tagger: labels, chunking, model shapes and losses."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.tagger import HEADS, INDEX, chunks, clean_form, sentence_items, tag


def test_tag_fills_none_and_collapses_other():
    noun = {"form": "nAradam", "vibhakti": "Dvitiya", "vacana": "Eka", "linga": "Pum"}
    verb = {"form": "Bavet", "purusha": "Prathama", "vacana": "Eka", "lakara": "other:Pres|Sub", "voice": "unmarked"}
    assert tag(noun) == ("Dvitiya", "Eka", "Pum", "NONE", "NONE")
    assert tag(verb) == ("NONE", "Eka", "NONE", "Prathama", "other")
    assert tag({"form": "ca"}) == ("NONE",) * 5
    assert all(v in INDEX[h] for h, v in zip(HEADS, tag(verb)))


def test_chunks_keep_whole_words_under_the_limit():
    pieces, truncated = chunks(["aaaa", "bbb", "cc", "d" * 12], limit=10)
    assert [[f for _, f in p] for p in pieces] == [["aaaa", "bbb"], ["cc"], ["d" * 10]]
    assert [[i for i, _ in p] for p in pieces] == [[0, 1], [2], [3]]
    assert truncated == 1
    assert all(len(" ".join(f for _, f in p)) <= 10 for p in pieces)


def test_model_shapes_and_both_losses():
    torch = pytest.importorskip("torch")
    from panini.tagger import batch, loss, make_tagger
    torch.manual_seed(0)
    model = make_tagger(size="S")
    items = [(["nAradam", "paripapracCa"], [("Dvitiya", "Eka", "Pum", "NONE", "NONE"),
                                             ("NONE", "Eka", "NONE", "Prathama", "Lit|Lun")]),
             (["ca"], [("NONE",) * 5])]
    tokens, ids, labels, words = batch(items, "cpu")
    out = model(tokens, ids, words)
    assert {h: tuple(v.shape) for h, v in out.items()} == {h: (2, words, len(o)) for h, o in HEADS.items()}
    assert labels["lakara"][0, 1].item() == INDEX["lakara"]["Lit|Lun"] and labels["vibhakti"][1, 1].item() == -100
    for kind in ("ce", "brier"):
        value = loss(out, labels, kind)
        assert value.item() > 0
    loss(out, labels, "ce").backward()
    assert model.heads["lakara"].weight.grad is not None


def test_pretrained_state_loads_into_the_tagger():
    torch = pytest.importorskip("torch")
    from panini.pretraining import make_encoder
    from panini.tagger import make_tagger
    encoder = make_encoder(width=16, layers=1, heads=2, max_length=64)
    state = {"config": encoder.config, "state_dict": encoder.state_dict()}
    tagger = make_tagger(state)
    assert torch.equal(tagger.encoder.embedding.weight, encoder.embedding.weight)


def test_forms_without_slp1_letters_are_dropped():
    assert clean_form("vAﾱk") == "vAk" and clean_form("_") == ""
    kept, dropped = sentence_items([{"form": "rAmaH"}, {"form": "_"}, {"form": "vanam"}])
    assert kept == [(0, "rAmaH"), (2, "vanam")] and dropped == 1


def test_eval_helpers_match_the_plain_metrics():
    np = pytest.importorskip("numpy")
    sys.path.insert(0, str(ROOT / "scripts"))
    from eval_tagger import bootstrap_index, ratio_ci, weighted_ece
    from panini.calibration import ece
    conf = np.array([0.9, 0.8, 0.7, 0.6, 0.95, 0.55, 0.65, 0.85, 0.75, 0.5])
    correct = np.array([1, 1, 0, 1, 1, 0, 1, 1, 0, 0], dtype=float)
    assert weighted_ece(conf, correct, np.ones(10)) == pytest.approx(ece(conf.tolist(), correct.tolist()))
    counts, word_chapter = bootstrap_index(["a"] * 5 + ["b"] * 5, resamples=200)
    point, samples = ratio_ci(correct, np.ones(10, bool), counts, word_chapter)
    assert point["value"] == pytest.approx(0.6) and point["ci95"][0] <= 0.6 <= point["ci95"][1]
    assert ratio_ci(correct, np.zeros(10, bool), counts, word_chapter)[0] == {"value": None, "ci95": None}


def test_joint_calibrators_fit_known_cases():
    np = pytest.importorskip("numpy")
    sys.path.insert(0, str(ROOT / "scripts"))
    from joint_calibration import isotonic_fit, isotonic_predict, logistic_fit, logistic_predict
    rng = np.random.default_rng(0)
    x = np.hstack([rng.normal(size=(20000, 2)), np.ones((20000, 1))])
    true = np.array([1.5, -0.5, 0.3])
    y = (rng.random(20000) < 1 / (1 + np.exp(-(x @ true)))).astype(float)
    assert np.allclose(logistic_fit(x, y), true, atol=0.1)
    assert logistic_predict(x[:1], true)[0] == pytest.approx(1 / (1 + np.exp(-(x[0] @ true))))
    c = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
    model = isotonic_fit(c, np.array([0.0, 1.0, 0.0, 1.0, 1.0, 1.0]))
    fitted = isotonic_predict(c, model)
    assert np.all(np.diff(fitted) >= 0) and fitted[0] == 0.0 and fitted[1] == fitted[2] == 0.5 and fitted[-1] == 1.0


def test_platt_on_logit_contains_the_identity():
    np = pytest.importorskip("numpy")
    sys.path.insert(0, str(ROOT / "scripts"))
    from joint_calibration import features, logistic_predict
    log_p = np.log(np.array([[0.999, 0.99, 0.9, 0.95, 0.999], [0.5, 0.9, 0.99, 0.8, 0.7]]))
    c0 = np.exp(log_p.sum(1))
    assert np.allclose(logistic_predict(features(log_p, "J4"), np.array([1.0, 0.0])), c0)
    assert features(log_p, "J5").shape == (2, 6) and features(log_p, "J1").shape == (2, 2)
