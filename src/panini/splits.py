"""Deterministic hash bucketing shared by the lexical holdouts in experiment_data."""

import hashlib
import math

SPLIT_NAMES = ("train", "dev", "test")
DEFAULT_RATIOS = {"train": 0.8, "dev": 0.1, "test": 0.1}


def _lemma_ratios(example_ratios):
    # Squaring these endpoint proportions recovers the requested distribution
    # among examples whose two lemmas land in the same partition.
    roots = {name: math.sqrt(value) for name, value in example_ratios.items()}
    total = sum(roots.values())
    return {name: roots[name] / total for name in SPLIT_NAMES}


def _hash_fraction(seed, lemma):
    digest = hashlib.sha256(f"{seed}:{lemma}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def _assign_bucket(seed, lemma, ratios):
    value = _hash_fraction(seed, lemma)
    cumulative = 0.0
    for name in SPLIT_NAMES:
        cumulative += ratios[name]
        if value < cumulative:
            return name
    return SPLIT_NAMES[-1]
