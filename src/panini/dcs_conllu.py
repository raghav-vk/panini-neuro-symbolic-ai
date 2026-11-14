"""DCS CoNLL-U to SLP1 rows with schema labels (docs/RLCD_TRANSITION_PLAN.md, stage 3 step 2).

Reads the pinned checkout from scripts/fetch_dcs_conllu.py. Text and lemmas are IAST and become
SLP1 (amendment 0.6). DCS features map onto the schema v0.3 names where they are one-to-one;
where they are not (reports/dcs-conllu/PROFILE.md), the label says so instead of guessing:
Past is "Lit|Lun" and Fut is "Lrt|Lut", voice is "passive" or "unmarked", and nothing here
claims a karaka role or a prayoga.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from panini.pretraining import spans
from panini.translit import SLP1_LETTERS, iast_hiatus_ambiguous, iast_to_slp1

CASE = {"Nom": "Prathama", "Acc": "Dvitiya", "Ins": "Trtiya", "Dat": "Caturthi", "Abl": "Panchami",
        "Gen": "Sasthi", "Loc": "Saptami", "Voc": "Sambodhana", "Cpd": "compound_member"}
NUMBER = {"Sing": "Eka", "Dual": "Dvi", "Plur": "Bahu"}
GENDER = {"Masc": "Pum", "Fem": "Stri", "Neut": "Napumsaka"}
PERSON = {"3": "Prathama", "2": "Madhyama", "1": "Uttama"}
# (Tense, Mood) of a finite verb -> lakara; the two DCS classes that merge lakaras keep both names.
LAKARA = {("Pres", "Ind"): "Lat", ("Impf", "Ind"): "Lan", ("Pres", "Opt"): "VidhiLin", ("Pres", "Imp"): "Lot",
          ("Past", "Prec"): "AshirLin", ("Fut", "Cond"): "Lrn", ("Past", "Ind"): "Lit|Lun", ("Fut", "Ind"): "Lrt|Lut"}


def feats(field):
    return dict(x.split("=", 1) for x in field.split("|") if "=" in x)


def labels(upos, f):
    """Schema labels for one word; keys absent where DCS does not record them."""
    out = {}
    if "Case" in f:
        out["vibhakti"] = CASE.get(f["Case"], "other:" + f["Case"])
    if f.get("Number") in NUMBER:
        out["vacana"] = NUMBER[f["Number"]]
    if f.get("Gender") in GENDER:
        out["linga"] = GENDER[f["Gender"]]
    if upos == "VERB" and "Person" in f:
        out["purusha"] = PERSON[f["Person"]]
        out["lakara"] = LAKARA.get((f.get("Tense"), f.get("Mood")), f"other:{f.get('Tense')}|{f.get('Mood')}")
        out["voice"] = "passive" if f.get("Voice") == "Pass" else "unmarked"
    if "VerbForm" in f:
        out["verb_form"] = f["VerbForm"]
    return out


def overlap_text(slp1):
    """Letters and spaces only, so DCS and DCS_pick compare on the same footing."""
    return " ".join("".join(ch for ch in slp1 if ch in SLP1_LETTERS or ch == " ").split())


def read_chapter(path):
    """Sentences of one .conllu chapter: [{sent_id, text, text_slp1, words, hiatus_ambiguous}]."""
    sentences, current = [], None
    for line in Path(path).open(encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("# text = "):
            current = {"text": line[9:], "words": []}
            sentences.append(current)
        elif line.startswith("# sent_id = ") and current is not None:
            current["sent_id"] = line[12:]
        elif line[:1].isdigit() and current is not None:
            cols = line.split("\t")
            if len(cols) < 10 or "-" in cols[0]:
                continue
            misc = feats(cols[9])
            word = {"form": iast_to_slp1(misc.get("Unsandhied", cols[1])), "lemma": iast_to_slp1(cols[2]),
                    "upos": cols[3], **labels(cols[3], feats(cols[5]))}
            if misc.get("UnsandhiedReconstructed") == "True":
                word["form_reconstructed"] = True
            if "LemmaId" in misc:
                word["lemma_id"] = int(misc["LemmaId"])
            current["words"].append(word)
    for s in sentences:
        s["text_slp1"] = iast_to_slp1(s["text"])
        s["hiatus_ambiguous"] = any(iast_hiatus_ambiguous(w) for w in s["text"].split())
    return sentences


def chapter_info(path):
    """chapterId -> {path, text, text_id, time_slot, vedic, syntax_gold} from lookup/chapter-info.xml.

    A chapter counts as Vedic if it has a <details> block (Veda, shakha and register metadata);
    docs/GOLD_SET_PLAN.md excludes Vedic texts from the first version.
    """
    out = {}
    for ch in ET.parse(path).getroot().iter("chapter"):
        layers = {(x.get("type"), x.text) for x in ch.iter("layer")}
        out[int(ch.findtext("chapterId"))] = {
            "path": ch.findtext("path"), "text": ch.findtext("textName"), "text_id": int(ch.findtext("textId")),
            "time_slot": ch.findtext("dcsTimeSlot"), "vedic": ch.find("details") is not None,
            "syntax_gold": ("gold", "syntax") in layers}
    return out


CHAPTER_ID = re.compile(r"-(\d+)\.conllu$")


def chapter_id(path):
    return int(CHAPTER_ID.search(Path(path).name).group(1))


def span_hashes(text):
    return {hash(piece) for piece in spans(text)}
