"""DCS CoNLL-U conversion to SLP1 rows with schema labels (RLCD stage 3 step 2)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from panini.dcs_conllu import chapter_id, chapter_info, labels, overlap_text, read_chapter

CHAPTER = """## text: Rāmāyaṇa
# text = nāradaṃ paripapraccha vālmīkir munipuṃgavam
# sent_id = 112118
1\tnāradaṃ\tnārada\tNOUN\t_\tCase=Acc|Gender=Masc|Number=Sing\t_\t_\t_\tLemmaId=33717|Unsandhied=nāradam|UnsandhiedReconstructed=True
2\tparipapraccha\tparipracch\tVERB\t_\tTense=Past|Mood=Ind|Person=3|Number=Sing\t_\t_\t_\tLemmaId=162075|Unsandhied=paripapraccha
3-4\tvālmīkir munipuṃgavam\t_\t_\t_\t_\t_\t_\t_\t_
3\tvālmīki\tvālmīki\tNOUN\t_\tCase=Nom|Gender=Masc|Number=Sing\t_\t_\t_\tUnsandhied=vālmīkiḥ
4\tmuni\tmuni\tNOUN\t_\tCase=Cpd\t_\t_\t_\t_

# text = rāmeṇa gamyate vanam
# sent_id = 7
1\trāmeṇa\trāma\tNOUN\t_\tCase=Ins|Gender=Masc|Number=Sing\t_\t_\t_\t_
2\tgamyate\tgam\tVERB\t_\tTense=Pres|Mood=Ind|Person=3|Number=Sing|Voice=Pass\t_\t_\t_\t_
3\tvanam\tvana\tNOUN\t_\tCase=Nom|Gender=Neut|Number=Sing\t_\t_\t_\t_
"""

INFO = """<info>
 <chapter><path>A/A-0000-A, 1-11.conllu</path><textName>A</textName><textId>1</textId><chapterName>A, 1</chapterName>
  <chapterId>11</chapterId><chapterPosition>1</chapterPosition><dcsTimeSlot>4</dcsTimeSlot>
  <annotation><layer type="gold">morpho-syntax</layer><layer type="gold">syntax</layer></annotation></chapter>
 <chapter><path>V/V-0000-V, 1-12.conllu</path><textName>V</textName><textId>2</textId><chapterName>V, 1</chapterName>
  <chapterId>12</chapterId><chapterPosition>1</chapterPosition><dcsTimeSlot>1</dcsTimeSlot>
  <details><veda>RV</veda></details><annotation><layer type="gold">morpho-syntax</layer></annotation></chapter>
</info>
"""


def test_read_chapter_converts_to_slp1_and_maps_features(tmp_path):
    path = tmp_path / "Rāmāyaṇa-0000-Rām, Bā, 1-1067.conllu"
    path.write_text(CHAPTER, encoding="utf-8")
    first, second = read_chapter(path)
    assert first["sent_id"] == "112118" and first["text_slp1"] == "nAradaM paripapracCa vAlmIkir munipuMgavam"
    assert [w["form"] for w in first["words"]] == ["nAradam", "paripapracCa", "vAlmIkiH", "muni"]
    assert first["words"][0] == {"form": "nAradam", "lemma": "nArada", "upos": "NOUN", "vibhakti": "Dvitiya",
                                 "vacana": "Eka", "linga": "Pum", "form_reconstructed": True, "lemma_id": 33717}
    verb = first["words"][1]
    assert (verb["lakara"], verb["purusha"], verb["vacana"], verb["voice"]) == ("Lit|Lun", "Prathama", "Eka", "unmarked")
    assert first["words"][3]["vibhakti"] == "compound_member"
    assert second["words"][1]["voice"] == "passive" and second["words"][1]["lakara"] == "Lat"
    assert chapter_id(path) == 1067


def test_labels_never_guess_merged_classes():
    assert labels("VERB", {"Tense": "Fut", "Mood": "Ind", "Person": "1", "Number": "Plur"})["lakara"] == "Lrt|Lut"
    assert labels("VERB", {"Tense": "Past", "Mood": "Jus", "Person": "3"})["lakara"] == "other:Past|Jus"
    assert "purusha" not in labels("VERB", {"Case": "Nom", "VerbForm": "Part"})


def test_overlap_text_keeps_letters_and_spaces():
    assert overlap_text("nAradaM  paripapracCa | 12 vAlmIkir.") == "nAradaM paripapracCa vAlmIkir"
    assert overlap_text("taTAnye 'pi") == "taTAnye 'pi"


def test_chapter_info_flags_vedic_and_gold_syntax(tmp_path):
    path = tmp_path / "chapter-info.xml"
    path.write_text(INFO, encoding="utf-8")
    info = chapter_info(path)
    assert info[11]["vedic"] is False and info[11]["syntax_gold"] is True and info[11]["time_slot"] == "4"
    assert info[12]["vedic"] is True and info[12]["syntax_gold"] is False
