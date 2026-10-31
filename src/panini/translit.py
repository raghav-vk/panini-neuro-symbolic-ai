"""SLP1 is the internal scheme (protocol amendment 0.6); IAST is for people.

Rules, examples, splits, lexicon lookups and model input are SLP1: one ASCII
character per sound, so vowel length (a/A) is a one-byte difference and the
IAST diphthong ai/au is never confused with a + i or a + u. Reviewer files,
reports and the paper show IAST, produced only by slp1_to_iast.
"""

import unicodedata

SLP1 = dict(zip("aAiIuUfFxXeEoOMHkKgGNcCjJYwWqQRtTdDnpPbBmyrlvSzsh",
                ["a", "ā", "i", "ī", "u", "ū", "ṛ", "ṝ", "ḷ", "ḹ", "e", "ai", "o", "au", "ṃ", "ḥ",
                 "k", "kh", "g", "gh", "ṅ", "c", "ch", "j", "jh", "ñ", "ṭ", "ṭh", "ḍ", "ḍh", "ṇ",
                 "t", "th", "d", "dh", "n", "p", "ph", "b", "bh", "m", "y", "r", "l", "v", "ś", "ṣ", "s", "h"]))
SLP1_VOWELS = frozenset("aAiIuUfFxXeEoO")
# Avagraha is part of a word's spelling; everything else here is punctuation.
SLP1_LETTERS = frozenset(SLP1) | {"'"}
PUNCTUATION = frozenset(" \t\r\n0123456789.,;:!?|-()[]/")

_IAST_TO_SLP1 = sorted(((v, k) for k, v in SLP1.items()), key=lambda item: -len(item[0]))


def is_slp1_word(text):
    return bool(text) and set(text) <= SLP1_LETTERS


def slp1_to_iast(text, strict=True):
    """strict=False passes unknown characters through instead of raising."""
    unknown = set(text) - SLP1_LETTERS - PUNCTUATION
    if unknown and strict:
        raise ValueError(f"unsupported surface characters: {sorted(unknown)}")
    return unicodedata.normalize("NFC", "".join(SLP1.get(c, c) for c in text))


def iast_to_slp1(text):
    """Greedy inverse of slp1_to_iast; IAST 'ai'/'au' are read as diphthongs.

    Use iast_hiatus_ambiguous to flag IAST input where that reading is a guess.
    """
    text, out, i = unicodedata.normalize("NFC", text), [], 0
    while i < len(text):
        for iast, slp1 in _IAST_TO_SLP1:
            if text.startswith(iast, i):
                out.append(slp1)
                i += len(iast)
                break
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def iast_hiatus_ambiguous(text):
    """True if the IAST has 'ai' or 'au', which could be a vowel sequence, not a diphthong."""
    text = unicodedata.normalize("NFC", text)
    return "ai" in text or "au" in text
