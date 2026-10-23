"""Single-step inversion with forward certificates, not a full derivation engine."""

from dataclasses import asdict
from .rules import apply_rule, GRAMMATICAL_TAGS, RuleValidationError


def forward(rules, left, right, tags=()):
    """Highest numeric priority wins for the SAME underlying pair.

    Optional higher-priority rewrites do not suppress lower-priority outcomes.
    Priorities are operational annotations, not a model of Paninian precedence.
    """
    matches = [(rule, apply_rule(rule, left, right, tags)) for rule in rules]
    matches = [(rule, trace) for rule, trace in matches if trace is not None]
    floor = max((r.precedence for r, _ in matches if not r.optional), default=-1)
    return [trace for rule, trace in matches if rule.precedence >= floor]


def enumerate_candidates(surface, rules, tags=(), lexicon=None):
    """Invert without gold words. Unknown prerequisites are not inferred."""
    if not surface or len(surface) > 512:
        raise ValueError("surface must have between 1 and 512 characters")
    pairs = set()
    if isinstance(tags, str):
        raise TypeError("tags must be a collection, not a string")
    tags = frozenset(tags)
    if tags - GRAMMATICAL_TAGS:
        raise RuleValidationError("unregistered grammatical tags")
    for rule in rules:
        if not rule.match.required_tags <= tags or rule.match.forbidden_tags & tags:
            continue
        for left in rule.match.left_suffixes:
            for right in rule.match.right_prefixes:
                middle = ((left if rule.operation.left == "keep_match" else "")
                          + rule.operation.emit
                          + (right if rule.operation.right == "keep_match" else ""))
                for pos in range(len(surface) - len(middle) + 1):
                    if surface[pos:pos + len(middle)] != middle:
                        continue
                    pair = (surface[:pos] + left, right + surface[pos + len(middle):])
                    if lexicon is None or all(word in lexicon for word in pair):
                        pairs.add(pair)
    candidates = []
    for left, right in sorted(pairs):
        traces = [asdict(t) for t in forward(rules, left, right, tags) if t.output == surface]
        if traces:
            candidates.append({"left": left, "right": right, "proofs": traces})
    return candidates


def gold_indices(record, candidates):
    accepted = record.get("accepted_pairs", [[record["left"], record["right"]]])
    return [i for i, c in enumerate(candidates) if [c["left"], c["right"]] in accepted]
