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
