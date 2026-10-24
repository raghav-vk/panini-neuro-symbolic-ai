"""External word-list lookup (Vidyut kosha) for candidate word forms.

Candidate words keep the word-final sandhi of their sentence (asurāḥ, udakaṃ,
ādityo, etaj); the kosha stores pausal forms (asurās, udakam). A form counts as
known if any pausal variant is in the kosha. Variants are generous on purpose:
the feature is "could be a real word", not a morphological analysis.
"""

from .dcs import iast_to_slp1

# SLP1 word-final letter -> possible pausal letters.
FINAL_VARIANTS = {
    "H": ["s", "r"], "M": ["m"], "S": ["s"], "z": ["s"], "r": ["s", "r"], "j": ["t", "d"], "g": ["k"],
    "q": ["w"], "b": ["p"], "d": ["t", "d"], "N": ["N", "n"], "Y": ["n", "m"], "R": ["n", "m"],
    "n": ["n", "m"], "l": ["t"], "c": ["t"],
}


def pausal_variants(slp1):
    variants = {slp1}
    if slp1[-1:] in FINAL_VARIANTS:
        variants |= {slp1[:-1] + x for x in FINAL_VARIANTS[slp1[-1]]}
    if slp1.endswith("o"):
        variants.add(slp1[:-1] + "as")  # -aḥ before a voiced sound
    if slp1[-1:] in ("a", "A"):
        variants.add(slp1 + "s")  # -aḥ/-āḥ before a vowel loses its visarga
    return variants


class KoshaLexicon:
    def __init__(self, path):
        from vidyut.kosha import Kosha
        self.kosha, self.cache = Kosha(str(path)), {}

    def known(self, iast):
        if iast not in self.cache:
            self.cache[iast] = any(self.kosha.get(v) for v in pausal_variants(iast_to_slp1(iast)))
        return self.cache[iast]


def annotate(rows, lexicon):
    """Add kosha_left / kosha_right flags to every candidate; reads candidate strings only."""
    for row in rows:
        for candidate in row["candidates"]:
            candidate["kosha_left"] = lexicon.known(candidate["left"])
            candidate["kosha_right"] = lexicon.known(candidate["right"])
    return rows
