"""Hash bucketing used by the lexical holdouts."""

import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.splits import DEFAULT_RATIOS, _assign_bucket, _lemma_ratios


def test_buckets_are_deterministic_and_follow_ratios():
    lemmas = [f"lemma{i}" for i in range(20000)]
    first = [_assign_bucket(1729, x, DEFAULT_RATIOS) for x in lemmas]
    assert first == [_assign_bucket(1729, x, DEFAULT_RATIOS) for x in lemmas]
    assert first != [_assign_bucket(7, x, DEFAULT_RATIOS) for x in lemmas]
    counts = Counter(first)
    for name, ratio in DEFAULT_RATIOS.items():
        assert abs(counts[name] / len(lemmas) - ratio) < 0.01


def test_lemma_ratios_square_back_to_example_ratios():
    ratios = _lemma_ratios(DEFAULT_RATIOS)
    assert math.isclose(sum(ratios.values()), 1.0)
    squares = {k: v * v for k, v in ratios.items()}
    total = sum(squares.values())
    for name, ratio in DEFAULT_RATIOS.items():
        assert math.isclose(squares[name] / total, ratio)
