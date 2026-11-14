# DCS CoNLL-U: What It Records (Profile)

Checkout: commit `8aeed5a` of OliverHellwig/sanskrit, `dcs/data/conllu`
(`datasets/dcs_conllu_manifest.json`, CC BY 4.0). Counts from
`scripts/profile_dcs_conllu.py`; full numbers in `profile.json`. Fetched
2026-11-14 for RLCD stage 3, step 2.

| Item | Count |
| --- | ---: |
| Texts | 271 |
| Chapter files (`.conllu`) | 16,051 |
| Sentences | 770,945 |
| Syntactic words | 5,801,761 |
| Treebank files (`.conllu_parsed`) | 7,227 |

The readme quotes 744,757 lines and 5,464,818 words; the dump has grown since.
Its annotation note: "The analysis of each string has been verified by one
annotator."

## What This Means for Stage 3

**Text is IAST.** It is converted to SLP1 on ingest (amendment 0.6). Most
pre-sandhi forms (`Unsandhied=`) are reconstructed, not annotated
(`UnsandhiedReconstructed=True`), as `docs/GOLD_SET_PLAN.md` noted.

**Nominal features map directly.** Case (8 cases, plus `Cpd` for compound
members), Number and Gender map one-to-one onto vibhakti, vacana and liṅga.

**Verb tense does not map one-to-one onto lakāra:**

| DCS | Lakāra |
| --- | --- |
| `Pres` + `Ind` | laṭ |
| `Impf` + `Ind` | laṅ |
| `Pres` + `Opt` | vidhiliṅ |
| `Pres` + `Imp` | loṭ |
| `Past` + `Prec` | āśīrliṅ |
| `Fut` + `Cond` | lṛṅ |
| `Past` + `Ind` | liṭ **or** luṅ: not distinguished |
| `Fut` + `Ind` | lṛṭ **or** luṭ: not distinguished |
| `Jus`, `Sub` | injunctive and subjunctive (mostly Vedic), outside schema v0.3 |

The two ambiguous rows need a second source, such as Vidyut's analysis of the
form, or must be kept as coarse classes.

**Voice is marked only when passive.** That is 37,335 words. Karmaṇi and
bhāve are not told apart, and pada (parasmaipada or ātmanepada) is not
recorded.

**Treebank relations are mostly unattributed.** Of 2,053,930 words in the
treebank files, 180,837 carry an `Annotator=` mark. The other 1,873,093 have
no mark and may be parser output. Their relations (`nsubj`, `obj`, `obl`,
`iobj`, …) are therefore not gold role labels. Only the annotator-marked
subset might serve as a kāraka source, after review.

**Overlap.** DCS_pick, our pretraining source, is a 2017 subset of DCS. Before
any DCS sentence is used for training or evaluation, the overlap and held-out
chapter rules of `docs/GOLD_SET_PLAN.md` section 3 apply.

## Overlap with DCS_pick (`scripts/convert_dcs_conllu.py`)

Rule as in the pretraining corpora: an exact match after normalisation, or
at least two distinct 30-character substrings shared with any DCS_pick
sentence. Summary in `overlap_summary.json`; per chapter in
`overlap_by_chapter.jsonl`.

| Item | Count |
| --- | ---: |
| DCS sentences | 770,945 |
| Exact copies of a DCS_pick sentence | 429,766 (56%) |
| Near copies | 10,755 |
| Matching a right-word holdout **dev** source sentence | 1,406 sentences in 1,166 chapters |
| Matching a right-word holdout **test** source sentence | 1,292 sentences in 1,039 chapters |
| Chapters with no overlap at all | 6,792 |
| … of which not marked Vedic | 531 chapters, 40,475 sentences |
| … and also not in DCS time slot 1 | 37,837 sentences |

**The held-out sentences are spread across the corpus.** The 984 dev and 817
test source sentences recur (repeated verses, shared formulas) in more than a
thousand chapters each. Every matching DCS sentence must stay out of stage 3
training.

**The Vedic flag is incomplete.** A `<details>` block marks 9,970 chapters as
Vedic, but some Vedic texts have none: Hiraṇyakeśi- and Mānavaśrautasūtra and
the Ṣaḍviṃśabrāhmaṇa. All of them are in DCS time slot 1. The proposed rule
for "classical" is no `<details>` block and a time slot other than 1. A
reviewed text list would be better.

**The clean classical pool is concentrated:**

- **Whole clean texts.** 12 non-Vedic texts are clean in every chapter,
  totalling 6,241 sentences. The kāvya among them are Saundarānanda (2,128),
  Āryāsaptaśatī (1,464), Narmamālā (816), Kokilasaṃdeśa (324), Bhallaṭaśataka
  (206), Haṃsasaṃdeśa (120), Caurapañcaśikā (100) and Mukundamālā (68).
- **Partly clean texts.** These add 34,234 clean sentences, 24,734 of them
  from Kathāsaritsāgara.

The gold set (`docs/GOLD_SET_PLAN.md`) and the stage 3 evaluation must divide
this pool, without sharing a chapter. That is a decision to record before any
of it is read for results.

**Other notes.**
- One chapter (Śikṣāsamuccaya, 10815) has no metadata entry. It is kept but
  never counted as classical.
- One metadata entry (Skandapurāṇa, Revākhaṇḍa chapter 230) has a `:` in its
  file name, and the file did not check out as `.conllu` on macOS.
- 200,917 sentences contain IAST *ai* or *au*, which the converter reads as
  diphthongs. Hiatus spellings would be misread there; they are flagged, not
  corrected.
