"""Calibration, abstention and routing metrics (RLCD stage 1)."""

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.calibration import (accuracy_at_coverage, argmax, aurc, best_tau, binary_nll, bins, bootstrap, brier,
                                correctness_nll, ece, fit_beta, fold, ranker_nll, risk_coverage, route, sigmoid,
                                softmax, threshold)


def test_fold_is_stable_and_balanced():
    assert fold("DCS-101320") == fold("DCS-101320")
    share = sum(fold(f"g{i}") for i in range(2000)) / 2000
    assert 0.45 < share < 0.55


def test_softmax_and_argmax_ties():
    assert softmax([0.0, 0.0]) == [0.5, 0.5]
    p = softmax([2.0, 0.0], beta=0.5)
    assert p[0] == pytest.approx(sigmoid(1.0))
    assert argmax([1.0, 3.0, 3.0]) == 1


def test_fit_beta_recovers_the_generating_temperature():
    # Labels drawn exactly in proportion to sigmoid(2 * logit): the NLL minimum is at beta = 2.
    items = []
    for logit in (-2.0, -1.0, -0.5, 0.5, 1.0, 2.0):
        p = sigmoid(2 * logit)
        ones = round(1000 * p)
        items += [(logit, 1)] * ones + [(logit, 0)] * (1000 - ones)
    assert fit_beta(lambda b: binary_nll(items, b)) == pytest.approx(2.0, abs=0.02)


def test_ranker_nll_matches_softmax_and_skips_missing_gold():
    items = [([1.0, 0.0], 0), ([0.0, 0.0, 0.0], None)]
    assert ranker_nll(items, 1.0) == pytest.approx(-math.log(softmax([1.0, 0.0])[0]))


def test_perfectly_calibrated_bins_have_zero_ece():
    confidence = [0.5] * 4 + [1.0] * 4
    correct = [1, 0, 1, 0, 1, 1, 1, 1]
    assert ece(confidence, correct, count=2) == pytest.approx(0.0)
    assert ece(confidence, correct, count=2, equal_mass=False) == pytest.approx(0.0)


def test_equal_width_bins_put_edges_on_the_left_bin():
    b = bins([0.1, 0.2, 0.95], [1, 1, 0], count=10, equal_mass=False)
    assert [x["count"] for x in b] == [1, 1, 1]
    assert b[0]["confidence"] == 0.1


def test_overconfidence_is_measured():
    assert ece([0.9] * 10, [1] * 5 + [0] * 5, count=1) == pytest.approx(0.4)
    assert brier([0.9, 0.9], [1, 0]) == pytest.approx((0.01 + 0.81) / 2)
    assert correctness_nll([0.5, 0.5], [1, 0]) == pytest.approx(math.log(2))


def test_risk_coverage_and_aurc():
    confidence, correct = [0.9, 0.8, 0.7, 0.6], [1, 1, 0, 1]
    assert risk_coverage(confidence, correct) == [1.0, 1.0, 2 / 3, 0.75]
    assert aurc(confidence, correct) == pytest.approx((0 + 0 + 1 / 3 + 0.25) / 4)
    assert accuracy_at_coverage(confidence, correct, 0.5) == 1.0
    assert threshold(confidence, correct, 0.75) == {"tau": 0.75, "coverage": 0.5, "accepted_accuracy": 1.0}


def test_routing_uses_the_slow_path_outcome_not_the_label():
    confidence, fast, slow = [0.9, 0.5, 0.4], [1, 0, 0], [0, 1, 0]
    assert route(confidence, fast, slow, 0.6) == {"tau": 0.6, "accuracy": 2 / 3, "routed": 2 / 3}


def test_best_tau_trades_accuracy_against_cost():
    confidence, fast, slow = [0.9, 0.5, 0.4], [1, 0, 0], [1, 1, 0]
    assert best_tau(confidence, fast, slow, cost=0.1) == 0.9   # route the two below 0.9; one is fixed
    assert best_tau(confidence, fast, slow, cost=0.6) == 0.0   # routing costs more than it gains


def test_bootstrap_resamples_whole_clusters():
    clusters = ["a", "a", "b", "b"]
    values = [1, 1, 0, 0]
    low, high = bootstrap(clusters, lambda idx: sum(values[i] for i in idx) / len(idx), resamples=200)
    assert low == 0.0 and high == 1.0
    assert bootstrap(clusters, lambda idx: len(idx) % 2, resamples=50) == [0, 0]
