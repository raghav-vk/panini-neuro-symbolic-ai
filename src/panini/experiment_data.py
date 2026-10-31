"""Development data, reviewed-data gates, and auditable split construction."""

import hashlib
import json
import random
import re
from datetime import date
import unicodedata
from collections import Counter
from itertools import combinations

from .rules import apply_rule
from .translit import iast_hiatus_ambiguous, iast_to_slp1, is_slp1_word, slp1_to_iast
from .splits import _assign_bucket, _lemma_ratios, DEFAULT_RATIOS

NAMES = ("train", "dev", "test")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def synthetic_examples(rules, per_rule=200, seed=1729):
    """Nonce-string probes. 'Lemma' IDs group synthetic stems, not Sanskrit words."""
    if per_rule < 1 or per_rule > 10_000:
        raise ValueError("per_rule must be 1..10000")
    rng = random.Random(seed)
    syllables = ["ba", "da", "ga", "ja", "ka", "la", "ma", "na", "pa", "ra", "sa", "ta"]
    stems = [syllables[i // 12] + syllables[i % 12] for i in range(144)]
    records = []
    for rule in rules:
        pairs = rng.sample([(a, b) for a in stems for b in stems], per_rule)
        for index, (a, b) in enumerate(pairs):
            left = a + rng.choice(rule.match.left_suffixes)
            right = rng.choice(rule.match.right_prefixes) + b
            tags = sorted(rule.match.required_tags)
            trace = apply_rule(rule, left, right, tags)
            records.append({"example_id": f"SYN-{rule.rule_id}-{index:05}", "source_group": f"SYN-{a}-{b}",
                            "left": left, "right": right, "left_lemma": a, "right_lemma": b,
                            "surface": trace.output, "rule_id": rule.rule_id, "family": rule.scope,
                            "tags": tags, "context": "", "context_lemmas": [],
                            "review_status": "synthetic_unreviewed", "data_kind": "nonce_string_probe"})
    return records


def reviewed_from_iast(record):
    """Reviewers work in IAST; convert a reviewed record to SLP1 (protocol amendment 0.6).

    Records that already carry an SLP1 source_sentence pass through unchanged. IAST
    ai/au is read as a diphthong; such words are flagged for a second look.
    """
    if "source_sentence" in record or not isinstance(record.get("source_sentence_iast"), str):
        return record
    iast = unicodedata.normalize("NFC", record["source_sentence_iast"])
    out = {**record, "source_sentence": record.get("source_sentence_slp1") or iast_to_slp1(iast)}
    if slp1_to_iast(out["source_sentence"], strict=False) != iast:
        raise ValueError("source_sentence_iast does not match its SLP1 sentence")
    for key in ("left", "right", "surface", "source_surface", "left_lemma", "right_lemma", "context"):
        if isinstance(out.get(key), str):
            out[key] = iast_to_slp1(out[key])
    for key in ("context_lemmas", "right_word_lemmas"):
        if isinstance(out.get(key), list):
            out[key] = [iast_to_slp1(x) if isinstance(x, str) else x for x in out[key]]
    for key in ("accepted_pairs", "accepted_pair_lemmas"):
        if isinstance(out.get(key), list):
            out[key] = [[iast_to_slp1(x) if isinstance(x, str) else x for x in pair] if isinstance(pair, list) else pair
                        for pair in out[key]]
    span = out.get("source_span")
    if isinstance(span, list) and len(span) == 2 and all(type(x) is int for x in span):
        out["source_span"] = [len(iast_to_slp1(iast[:x])) for x in span]
    out["iast_hiatus_flag"] = any(iast_hiatus_ambiguous(record.get(k) or "") for k in ("left", "right"))
    return out


def validate_reviewed(record, rules):
    """Only explicitly reviewed, surface-aligned examples enter corpus evaluation."""
    record = reviewed_from_iast(record)
    if record.get("review_status") != "expert_reviewed" or not record.get("reviewer", "").strip():
        raise ValueError("boundary requires independent review")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", record.get("reviewed_at", "")):
        raise ValueError("review date required")
    date.fromisoformat(record["reviewed_at"])
    if record.get("external_boundary_confirmed") is not True:
        raise ValueError("reviewer must confirm an external word boundary")
    return _validate_alignment(record, rules)


def validate_silver(record, rules):
    """Automatic DCS alignments: attested surfaces and annotated lemmas, never expert gold."""
    if record.get("data_kind") != "dcs_silver_alignment" or record.get("review_status") != "silver_unreviewed":
        raise ValueError("silver examples must come from the DCS alignment extractor")
    if record.get("external_boundary_confirmed") is not False:
        raise ValueError("silver examples cannot claim reviewer confirmation")
    return _validate_alignment(record, rules)


def _validate_alignment(record, rules):
    for key in ("example_id", "source_group", "left", "right", "left_lemma", "right_lemma", "surface", "rule_id"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            raise ValueError(f"missing {key}")
    span = record.get("source_span")
    sentence = record.get("source_sentence", "")
    if not isinstance(span, list) or len(span) != 2 or any(type(x) is not int for x in span):
        raise ValueError("source_span must be [start, end] SLP1 character offsets")
    if not 0 <= span[0] < span[1] <= len(sentence):
        raise ValueError("invalid source span")
    observed = sentence[span[0]:span[1]]
    if "".join(observed.split()) != record["surface"]:
        raise ValueError("surface does not match source span")
    if record.get("source_surface", observed) != observed:
        raise ValueError("source_surface differs from source span")
    record["source_surface"] = observed
    if any(any(c.isspace() for c in record[key]) for key in ("left", "right")):
        raise ValueError("each inflected word must be a single form")
    if not all(is_slp1_word(record[key]) for key in ("left", "right", "surface")):
        raise ValueError("left, right and surface must be SLP1")
    if not isinstance(record.get("tags"), list) or not isinstance(record.get("context_lemmas"), list):
        raise ValueError("tags and context_lemmas must be arrays")
    if "pada_boundary" not in record["tags"]:
        raise ValueError("external example requires pada_boundary tag")
    if any(not isinstance(x, str) or not x.strip() for x in record["tags"] + record["context_lemmas"]):
        raise ValueError("tags and context lemmas must contain nonempty strings")
    if record.get("context") and not record["context_lemmas"]:
        raise ValueError("nonempty context needs annotated lemmas for leakage auditing")
    if "accepted_pairs" in record:
        pairs = record["accepted_pairs"]
        lemmas = record.get("accepted_pair_lemmas")
        if not isinstance(pairs, list) or not pairs or not isinstance(lemmas, list) or len(pairs) != len(lemmas):
            raise ValueError("accepted pairs require parallel accepted_pair_lemmas annotations")
        if any(not isinstance(pair, list) or len(pair) != 2 or any(not isinstance(x, str) or not x for x in pair) for pair in pairs + lemmas):
            raise ValueError("accepted alternatives must be pairs of nonempty strings")
        if [record["left"], record["right"]] not in pairs:
            raise ValueError("accepted alternatives must include the primary annotated pair")
    # Missing coverage is a measured outcome, not grounds for deleting gold data.
    if record["rule_id"] not in {r.rule_id for r in rules}:
        record["family"] = "unsupported"
    else:
        record["family"] = next(r.scope for r in rules if r.rule_id == record["rule_id"])
    return record


def _normalize(record):
    def rec(value):
        if isinstance(value, str):
            return unicodedata.normalize("NFC", value)
        if isinstance(value, list):
            return [rec(x) for x in value]
        if isinstance(value, dict):
            return {k: rec(v) for k, v in value.items()}
        return value
    result = rec(record)
    for key in ("left_lemma", "right_lemma"):
        result[key] = result[key].strip()
    result["context_lemmas"] = [x.strip() for x in result.get("context_lemmas", [])]
    if "accepted_pair_lemmas" in result:
        result["accepted_pair_lemmas"] = [[x.strip() for x in pair] for pair in result["accepted_pair_lemmas"]]
    return result


def split_key(lemma):
    """Lemmas are hashed in IAST spelling, so partitions are unchanged by the switch to SLP1."""
    return slp1_to_iast(lemma, strict=False)


def lemma_set(record):
    return {record["left_lemma"], record["right_lemma"], *record.get("context_lemmas", []),
            *(lemma for pair in record.get("accepted_pair_lemmas", []) for lemma in pair)}


def right_word_lemmas(record):
    """Lemmas of the right-hand word, including compound members fused into its surface."""
    return set(record.get("right_word_lemmas") or [record["right_lemma"]])


def split_examples(records, method, seed=1729):
    """Group duplicates/sources before assignment; strict includes context lemmas.

    strict_right_lemma holds out only the right-hand word (protocol amendment 0.2): left
    words of the indeclinable scope form a closed class that training must contain. It
    deduplicates to distinct analysis types, ignoring context, so frequent forms such as
    caiva cannot dominate a partition.
    """
    if method not in {"source_random", "pair", "strict_lemma", "strict_right_lemma"}:
        raise ValueError("unknown split method")
    clean, seen, ids, duplicates = [], set(), set(), 0
    for raw in records:
        record = _normalize(raw)
        if record["example_id"] in ids:
            raise ValueError("duplicate example identity")
        ids.add(record["example_id"])
        fields = ("surface", "left", "right", "tags", "accepted_pairs")
        key = digest({k: record.get(k) for k in fields + (() if method == "strict_right_lemma" else ("context",))})
        if key in seen:
            duplicates += 1
            # Preserve source linkage through duplicate rows until grouping ends.
            record["_duplicate"] = True
        seen.add(key)
        clean.append(record)
    parent = list(range(len(clean)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    owners = {}
    for i, record in enumerate(clean):
        keys = [("source", record["source_group"]), ("surface", record["surface"])]
        if method == "pair":
            keys.append(("pair", record["left_lemma"], record["right_lemma"]))
            keys.extend(("pair", *pair) for pair in record.get("accepted_pair_lemmas", []))
        for key in keys:
            if key in owners:
                parent[find(i)] = find(owners[key])
            else:
                owners[key] = i
    groups = {}
    for i, record in enumerate(clean):
        groups.setdefault(find(i), []).append(record)
    splits = {name: [] for name in (*NAMES, "mixed")}
    lemma_ratios = _lemma_ratios(DEFAULT_RATIOS)
    for records_in_group in groups.values():
        if method == "strict_lemma":
            buckets = {_assign_bucket(seed, split_key(lemma), lemma_ratios) for r in records_in_group for lemma in lemma_set(r)}
            bucket = next(iter(buckets)) if len(buckets) == 1 else "mixed"
        elif method == "strict_right_lemma":
            # One word, not two endpoints: example ratios apply without the square-root correction.
            buckets = {_assign_bucket(seed, split_key(lemma), DEFAULT_RATIOS) for r in records_in_group for lemma in right_word_lemmas(r)}
            bucket = next(iter(buckets)) if len(buckets) == 1 else "mixed"
        else:
            key = min(r["example_id"] for r in records_in_group)
            bucket = _assign_bucket(seed, key, DEFAULT_RATIOS)
        for record in records_in_group:
            if not record.pop("_duplicate", False):
                splits[bucket].append(record)
    for rows in splits.values():
        rows.sort(key=lambda r: r["example_id"])
    overlaps = {}
    for left, right in combinations(NAMES, 2):
        a, b = splits[left], splits[right]
        overlaps[f"{left}_{right}"] = {
            "lemmas_including_context": len(set().union(*(lemma_set(r) for r in a)) & set().union(*(lemma_set(r) for r in b))),
            "right_word_lemmas": len(set().union(*(right_word_lemmas(r) for r in a)) & set().union(*(right_word_lemmas(r) for r in b))),
            "pairs": len({(r["left_lemma"], r["right_lemma"]) for r in a} & {(r["left_lemma"], r["right_lemma"]) for r in b}),
            "sources": len({r["source_group"] for r in a} & {r["source_group"] for r in b}),
            "surfaces": len({r["surface"] for r in a} & {r["surface"] for r in b})}
    for overlap in overlaps.values():
        assert overlap["sources"] == overlap["surfaces"] == 0
        if method == "pair":
            assert overlap["pairs"] == 0
        if method == "strict_lemma":
            assert overlap["lemmas_including_context"] == 0
        if method == "strict_right_lemma":
            assert overlap["right_word_lemmas"] == 0
    return splits, {"method": method, "seed": seed, "input_count": len(clean), "duplicates_removed": duplicates,
                    "counts": {k: len(v) for k, v in splits.items()}, "overlaps": overlaps,
                    "per_rule": {k: dict(Counter(r["rule_id"] for r in v)) for k, v in splits.items()},
                    "dataset_sha256": digest(clean), "context_policy": "all annotated context lemmas participate in strict assignment",
                    "grouping": "source and identical surface components; pair holdout additionally groups lemma pairs"}
