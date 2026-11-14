"""Calibration, abstention and routing metrics for RLCD stage 1 (docs/RLCD_TRANSITION_PLAN.md, section 4).

Plain Python on lists, so that results do not depend on a numerical library and the functions
port directly to the Rust runtime (plan section 7). Confidence is always top-label: the
probability of the answer the system gives, scored against whether that answer is correct.
"""

import hashlib
import math
import random

SALT = "rlcd-stage1"


def fold(key, salt=SALT):
    """0 or 1 from SHA-256 of salt:key, so fold membership never depends on order or outcomes."""
    return hashlib.sha256(f"{salt}:{key}".encode()).digest()[0] & 1


def softmax(scores, beta=1.0):
    """Candidate probabilities at inverse temperature beta (beta = 1 / T)."""
    top = max(scores)
    weights = [math.exp(beta * (s - top)) for s in scores]
    total = sum(weights)
    return [w / total for w in weights]


def argmax(values):
    """Index of the largest value; ties go to the lowest index, as in ranking.metrics."""
    return min(range(len(values)), key=lambda i: (-values[i], i))


def sigmoid(x):
    return 1 / (1 + math.exp(-x)) if x >= 0 else math.exp(x) / (1 + math.exp(x))


def ranker_nll(items, beta):
    """Mean negative log probability of the gold candidate; items are (scores, gold index or None)."""
    losses = []
    for scores, gold in items:
        if gold is None:
            continue
        top = max(scores)
        log_total = beta * top + math.log(sum(math.exp(beta * (s - top)) for s in scores))
        losses.append(log_total - beta * scores[gold])
    return sum(losses) / len(losses)


def binary_nll(items, beta):
    """Mean negative log-likelihood of binary labels; items are (logit for label 1, label in {0, 1})."""
    total = 0.0
    for logit, label in items:
        z = beta * logit if label else -beta * logit
        total += math.log1p(math.exp(-z)) if z >= 0 else -z + math.log1p(math.exp(z))
    return total / len(items)


def fit_beta(nll, low=0.01, high=20.0, steps=100):
    """Inverse temperature minimising nll(beta), by golden-section search.

    Both NLLs above are convex in beta, so the search finds the global minimum on [low, high].
    """
    ratio = (math.sqrt(5) - 1) / 2
    a, b = low, high
    c, d = b - ratio * (b - a), a + ratio * (b - a)
    fc, fd = nll(c), nll(d)
    for _ in range(steps):
        if fc <= fd:
            b, d, fd = d, c, fc
            c = b - ratio * (b - a)
            fc = nll(c)
        else:
            a, c, fc = c, d, fd
            d = a + ratio * (b - a)
            fd = nll(d)
    return (a + b) / 2


def bins(confidence, correct, count=10, equal_mass=True):
    """Reliability bins: [{count, confidence, accuracy}], empty bins dropped.

    Equal-mass bins split the items sorted by confidence into count near-equal groups;
    equal-width bins split [0, 1] into count intervals, closed on the right.
    """
    n = len(confidence)
    if equal_mass:
        order = sorted(range(n), key=lambda i: confidence[i])
        groups = [order[k * n // count:(k + 1) * n // count] for k in range(count)]
    else:
        groups = [[] for _ in range(count)]
        for i, c in enumerate(confidence):
            groups[min(count - 1, max(0, math.ceil(c * count) - 1))].append(i)
    return [{"count": len(g), "confidence": sum(confidence[i] for i in g) / len(g),
             "accuracy": sum(correct[i] for i in g) / len(g)} for g in groups if g]


def ece(confidence, correct, count=10, equal_mass=True):
    n = len(confidence)
    return sum(b["count"] / n * abs(b["accuracy"] - b["confidence"])
               for b in bins(confidence, correct, count, equal_mass))


def brier(confidence, correct):
    return sum((c - y) ** 2 for c, y in zip(confidence, correct, strict=True)) / len(confidence)


def correctness_nll(confidence, correct, eps=1e-12):
    return -sum(math.log(max(eps, c if y else 1 - c)) for c, y in zip(confidence, correct, strict=True)) / len(confidence)


def risk_coverage(confidence, correct):
    """Accuracy of the k most confident items for k = 1..n; ties keep item order."""
    order = sorted(range(len(confidence)), key=lambda i: -confidence[i])
    hits, curve = 0, []
    for k, i in enumerate(order, 1):
        hits += correct[i]
        curve.append(hits / k)
    return curve


def aurc(confidence, correct):
    """Area under the risk-coverage curve: mean error rate over all coverage levels."""
    curve = risk_coverage(confidence, correct)
    return sum(1 - a for a in curve) / len(curve)


def accuracy_at_coverage(confidence, correct, coverage):
    curve = risk_coverage(confidence, correct)
    return curve[max(1, math.ceil(coverage * len(curve))) - 1]


def threshold(confidence, correct, tau):
    """Coverage and accuracy of the items with confidence at least tau."""
    kept = [y for c, y in zip(confidence, correct, strict=True) if c >= tau]
    return {"tau": tau, "coverage": len(kept) / len(confidence),
            "accepted_accuracy": sum(kept) / len(kept) if kept else None}


def route(confidence, fast, slow, tau):
    """Final accuracy and routed fraction when items below tau go to the slow path."""
    routed = [c < tau for c in confidence]
    final = [s if r else f for r, f, s in zip(routed, fast, slow, strict=True)]
    return {"tau": tau, "accuracy": sum(final) / len(final), "routed": sum(routed) / len(routed)}


def reward(confidence, fast, slow, tau, cost):
    result = route(confidence, fast, slow, tau)
    return result["accuracy"] - cost * result["routed"]


def best_tau(confidence, fast, slow, cost):
    """Threshold with the highest mean reward; on ties, the one that routes least.

    Candidates are 0 (route nothing), every observed confidence (route what lies below it)
    and just above 1 (route everything).
    """
    candidates = [0.0] + sorted(set(confidence)) + [1.0 + 1e-9]
    return max(candidates, key=lambda t: (reward(confidence, fast, slow, t, cost), -t))


def bootstrap(clusters, statistic, resamples=1000, seed=1729):
    """95% percentile interval of statistic(indices) over resampled clusters.

    clusters[i] is the cluster of item i. Each resample draws clusters with replacement and
    passes the indices of all their items, repeated as drawn.
    """
    members = {}
    for i, c in enumerate(clusters):
        members.setdefault(c, []).append(i)
    keys = sorted(members)
    rng = random.Random(seed)
    values = []
    for _ in range(resamples):
        indices = [i for k in rng.choices(keys, k=len(keys)) for i in members[k]]
        values.append(statistic(indices))
    values.sort()
    return [values[int(0.025 * resamples)], values[int(0.975 * resamples) - 1]]
