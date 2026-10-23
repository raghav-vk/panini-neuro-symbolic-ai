"""Non-executing decoder for the primitive protocol-0 DCS record subset."""

import pickletools
import unicodedata


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


SLP1 = dict(zip("aAiIuUfFxXeEoOMHkKgGNcCjJYwWqQRtTdDnpPbBmyrlvSzsh",
                ["a", "ā", "i", "ī", "u", "ū", "ṛ", "ṝ", "ḷ", "ḹ", "e", "ai", "o", "au", "ṃ", "ḥ",
                 "k", "kh", "g", "gh", "ṅ", "c", "ch", "j", "jh", "ñ", "ṭ", "ṭh", "ḍ", "ḍh", "ṇ",
                 "t", "th", "d", "dh", "n", "p", "ph", "b", "bh", "m", "y", "r", "l", "v", "ś", "ṣ", "s", "h"]))


def slp1_to_iast(text):
    unknown = sorted(set(text) - set(SLP1) - set(" \t\r\n0123456789.,;:!?|'-()[]/"))
    if unknown:
        raise ValueError(f"unsupported surface characters: {unknown}")
    return unicodedata.normalize("NFC", "".join(SLP1.get(c, c) for c in text))


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
