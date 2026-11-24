"""Helpers of the frozen sandhi pretraining test script (amendment 0.9)."""

import json
import sys
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import run_sandhi_pretraining_test as frozen_run


def test_annotate_copies_rows_and_keeps_candidate_order():
    rows = [{"id": 1, "candidates": [{"left": "a"}, {"left": "b"}]}, {"id": 2, "candidates": [{"left": "c"}]}]
    out = frozen_run.annotate(rows, [(-1.0, -2.0), (-3.0, -4.0), (-5.0, -6.0)])
    assert [c["neural_left"] for r in out for c in r["candidates"]] == [-1.0, -3.0, -5.0]
    assert out[1]["candidates"][0]["neural_right"] == -6.0
    assert "neural_left" not in rows[0]["candidates"][0]


def test_paired_reports_seed_differences_and_mcnemar():
    reference = np.array([1, 1, 0, 0, 1, 0], float)
    arms = [np.array([1, 1, 1, 0, 1, 0], float), np.array([1, 1, 1, 1, 1, 0], float)]
    d = frozen_run.paired(arms, reference, ["g1", "g1", "g2", "g3", "g4", "g5"], resamples=200)
    assert d["per_seed"] == pytest.approx([1 / 6, 2 / 6])
    assert d["mean"] == pytest.approx(0.25)
    assert d["ci95"][0] <= d["mean"] <= d["ci95"][1]
    assert d["mcnemar_p"] == [1.0, 0.5]


def test_gate_coverage_and_accepted_accuracy():
    g = frozen_run.gate(np.array([0.99, 0.96, 0.5, 0.94]), np.array([1, 0, 1, 1], float), 0.95)
    assert g["coverage"] == 0.5 and g["accepted_accuracy"] == 0.5


def test_frozen_settings_name_the_slp1_splits():
    settings = json.loads(frozen_run.FROZEN.read_text())
    assert settings["split_dir"].endswith("dcs-silver-slp1-kosha-splits/strict_right_lemma")
    assert set(settings["split_sha256"]) == {"train", "dev", "test"}
    assert settings["erratum"]["superseded_split_sha256"] != settings["split_sha256"]
