"""Non-executing decoder for the primitive protocol-0 DCS record subset."""

import pickletools
import re

from .translit import SLP1_VOWELS, iast_to_slp1, slp1_to_iast


class DCSDecodeError(ValueError):
    """Unsupported or malformed legacy record."""


def decode_record(data, max_bytes=1_000_000):
    """Interpret a small stack language; never import or instantiate pickle names."""
    if len(data) > max_bytes:
        raise DCSDecodeError("record exceeds byte limit")
    mark, instance = object(), object()
    stack, memo = [], {}
    state, instances = None, 0

    def marked():
        values = []
        while stack and stack[-1] is not mark:
            values.append(stack.pop())
        if not stack:
            raise DCSDecodeError("missing MARK")
        stack.pop()
        return list(reversed(values))

    try:
        for count, (opcode, arg, pos) in enumerate(pickletools.genops(data)):
            if count > 100_000 or len(stack) > 10_000:
                raise DCSDecodeError("resource limit")
            name = opcode.name
            if name == "MARK":
                stack.append(mark)
            elif name == "INST":
                if arg != "__main__ DCS" or marked() or instances:
                    raise DCSDecodeError("unexpected instance")
                instances += 1
                stack.append(instance)
            elif name in {"STRING", "UNICODE", "INT", "LONG", "FLOAT", "NONE"}:
                if name == "STRING":
                    arg = arg.encode("latin1").decode("utf-8")
                stack.append(arg)
            elif name in {"LIST", "TUPLE", "DICT"}:
                values = marked()
                if name == "DICT":
                    if len(values) % 2:
                        raise DCSDecodeError("odd dictionary")
                    stack.append(dict(zip(values[::2], values[1::2])))
                else:
                    stack.append(values if name == "LIST" else tuple(values))
            elif name == "APPEND":
                value = stack.pop()
                if type(stack[-1]) is not list:
                    raise DCSDecodeError("APPEND target")
                stack[-1].append(value)
            elif name == "SETITEM":
                value, key = stack.pop(), stack.pop()
                if type(stack[-1]) is not dict or type(key) is not str:
                    raise DCSDecodeError("SETITEM target/key")
                if key in stack[-1]:
                    raise DCSDecodeError("duplicate field")
                stack[-1][key] = value
            elif name == "PUT":
                if arg in memo or arg < 0 or arg > 100_000:
                    raise DCSDecodeError("invalid memo index")
                memo[arg] = stack[-1]
            elif name == "GET":
                stack.append(memo[arg])
            elif name == "BUILD":
                if state is not None:
                    raise DCSDecodeError("duplicate BUILD")
                state = stack.pop()
                if stack[-1] is not instance or type(state) is not dict:
                    raise DCSDecodeError("invalid DCS state")
            elif name == "STOP":
                if stack != [instance] or state is None or pos != len(data) - 1:
                    raise DCSDecodeError("invalid final stack or trailing bytes")
            else:
                raise DCSDecodeError(f"unsupported opcode: {name}")
        if state is None:
            raise DCSDecodeError("missing state")
        validate_state(state)
        return state
    except (ValueError, IndexError, KeyError, TypeError, UnicodeError) as exc:
        raise DCSDecodeError(str(exc)) from exc


def validate_state(state):
    """Reject cycles, unexpected fields and unaligned analyses before JSON output."""
    visited = 0

    def walk(value, ancestors=(), depth=0):
        nonlocal visited
        visited += 1
        if visited > 100_000 or depth > 20:
            raise DCSDecodeError("expanded object limit")
        if type(value) in {str, int, float, bool, type(None)}:
            return
        if type(value) not in {list, tuple, dict} or id(value) in ancestors:
            raise DCSDecodeError("non-primitive or cyclic object")
        for item in (value.values() if type(value) is dict else value):
            walk(item, (*ancestors, id(value)), depth + 1)

    walk(state)
    if set(state) != {"lemmas", "dcs_chunks", "sent_id", "cng", "sentence"}:
        raise DCSDecodeError("unexpected DCS fields")
    if not isinstance(state["sentence"], str) or type(state["sent_id"]) is not int:
        raise DCSDecodeError("invalid sentence identity")
    if any(type(state[k]) is not list for k in ("lemmas", "dcs_chunks", "cng")):
        raise DCSDecodeError("invalid annotation lists")
    if len(state["lemmas"]) != len(state["cng"]):
        raise DCSDecodeError("unaligned chunk counts")
    if state["dcs_chunks"] != [lemma for group in state["lemmas"] for lemma in group]:
        raise DCSDecodeError("dcs_chunks is not the flattened lemma sequence")
    for lemmas, codes in zip(state["lemmas"], state["cng"]):
        if type(lemmas) is not list or type(codes) is not list or len(lemmas) != len(codes):
            raise DCSDecodeError("unaligned lemma/morphology counts")
        if any(not isinstance(x, str) for x in [*lemmas, *codes]):
            raise DCSDecodeError("invalid analysis strings")


def boundary_proposals(record):
    """Adjacent lemma slots are REVIEW proposals, never inferred inflected forms."""
    slots = [(i, j, lemma, record["cng"][i][j])
             for i, group in enumerate(record["lemmas"]) for j, lemma in enumerate(group)]
    for index, (left, right) in enumerate(zip(slots, slots[1:])):
        yield {"example_id": f"DCS-{record['sent_id']}-{index}", "source_group": f"DCS-{record['sent_id']}",
               "source_sentence_slp1": record["sentence"], "source_sentence_iast": slp1_to_iast(record["sentence"]),
               "left_lemma": left[2], "right_lemma": right[2], "left_morphology": left[3], "right_morphology": right[3],
               "left_slot": list(left[:2]), "right_slot": list(right[:2]),
               "boundary_kind": "within_chunk" if left[0] == right[0] else "between_chunks",
               "left": None, "right": None, "surface": None, "source_span": None,
               "tags": [], "context": "", "context_lemmas": [], "rule_id": None,
               "review_status": "pending", "reviewer": "", "reviewed_at": "", "external_boundary_confirmed": False,
               "notes": "Supply inflected forms, source span, boundary type, contextual lemmas and applicable tags; lemmas are not pre-sandhi forms."}


# Observed junction material for vowel sandhi: vowels, glides, r (ṛ-guṇa) and avagraha.
JUNCTION_CHARACTERS = SLP1_VOWELS | set("yvr'")
INDECLINABLE, COMPOUND_MEMBER = "2", "3"
# Indeclinables that DCS codes as "2" but that mainly form compounds (mahā-ṛṣi, sa-indra):
# their boundary is compound-internal, not external. Expert review should confirm this list.
# SLP1 spellings: mahA, nAnA = mahā, nānā.
COMPOUND_PREFIXES = frozenset({"mahA", "sa", "su", "ati", "prati", "nAnA", "go", "dus", "ku"})


def external_vowel_boundaries(record, context_window=1):
    """Align DCS lemma annotations to attested surfaces without consulting sandhi rules.

    Yields (example, None) or (None, rejection_reason) for every adjacent lemma pair
    whose left lemma ends and right lemma begins in a vowel. Only boundaries whose
    inflected forms are fully determined are kept: an indeclinable (code 2, form equals
    lemma) opening its whitespace chunk, followed by a non-verbal word that runs to the
    chunk end. Compound-forming prefixes are excluded.
    The fused junction is read from the surface, so rule coverage stays a measurement.
    """
    sentence = record["sentence"]
    chunks = [(m.start(), m.group()) for m in re.finditer(r"\S+", sentence)]
    if len(chunks) != len(record["lemmas"]):
        yield None, "chunk_group_mismatch"
        return
    try:
        slp1_to_iast(sentence)  # rejects characters outside SLP1 and punctuation
    except ValueError:
        yield None, "surface_unsupported"
        return
    # DCS_pick lemmas are IAST; every field below is SLP1 (protocol amendment 0.6).
    all_lemmas = [[iast_to_slp1(lemma) for lemma in group] for group in record["lemmas"]]
    for c, ((offset, chunk), lemmas, codes) in enumerate(zip(chunks, all_lemmas, record["cng"])):
        for j in range(len(lemmas) - 1):
            left, right = lemmas[j], lemmas[j + 1]
            if not (left and right and left[-1] in SLP1_VOWELS and right[0] in SLP1_VOWELS):
                continue
            reason = _boundary_rejection(chunk, left, right, codes, j, left)
            if isinstance(reason, str):
                yield None, reason
                continue
            junction_end = reason
            window = range(max(0, c - context_window), min(len(chunks), c + context_window + 1))
            neighbours = [k for k in window if k != c]
            context = " ".join(chunks[k][1] if k != c else "_" for k in window)
            yield {
                "example_id": f"DCS-{record['sent_id']}-{c}-{j}", "source_group": f"DCS-{record['sent_id']}",
                "left": left, "right": right[0] + chunk[junction_end:],
                "left_lemma": left, "right_lemma": right, "right_word_lemmas": lemmas[j + 1:],
                "surface": chunk, "source_surface": chunk,
                "source_sentence": sentence, "source_span": [offset, offset + len(chunk)],
                "observed_junction": chunk[len(left) - 1:junction_end],
                "vowel_pair": [left[-1], right[0]],
                "left_morphology": codes[j], "right_morphology": codes[j + 1:],
                "tags": ["pada_boundary"], "boundary_type": "indeclinable_left_external",
                "context": context if neighbours else "",
                "context_lemmas": [*lemmas[j + 2:], *(l for k in neighbours for l in all_lemmas[k])],
                "review_status": "silver_unreviewed", "data_kind": "dcs_silver_alignment",
                "external_boundary_confirmed": False,
            }, None


def _boundary_rejection(chunk, left, right, codes, j, lemma):
    """Return a rejection reason, or the surface offset where the right word's body begins."""
    if codes[j] == COMPOUND_MEMBER:
        return "compound_internal_left"
    if codes[j] != INDECLINABLE:
        return "inflected_left_form_unknown"
    if j != 0:
        return "left_not_chunk_initial"
    if lemma in COMPOUND_PREFIXES:
        return "left_compound_prefix"
    # Verbal forms may add an augment or reduplication, so their initial vowel is not the root's.
    if codes[j + 1].startswith("-"):
        return "right_verb_initial_uncertain"
    # The right word must extend to the chunk end: only compound members may intervene.
    if any(code != COMPOUND_MEMBER for code in codes[j + 1:-1]):
        return "right_end_fused"
    if not chunk.startswith(left[:-1]):
        return "left_misaligned"
    body = right[1:1 + min(3, max(1, len(right) - 2))]
    if not body:
        return "right_too_short"
    start = len(left) - 1
    ends = [k for k in range(start + 1, min(start + 4, len(chunk)) + 1)
            if chunk.startswith(body, k) and set(chunk[start:k]) <= JUNCTION_CHARACTERS]
    if len(ends) != 1:
        return "junction_ambiguous" if ends else "junction_unresolved"
    return ends[0]
