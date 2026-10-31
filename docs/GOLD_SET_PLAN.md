# Plan: Expert-Verified Gold Test Set

**Status:** Draft, 2026-10-24. Nothing has been built. Tracks GitHub issue #63.
Once approved, it becomes a protocol amendment before any item is shown to a
reviewer.

## 1. Purpose

The silver right-word holdout test set has been evaluated three times
(protocol sections 9.5, 11.1 and 11.2). The paper needs one untouched,
independently verified evaluation set. It should also cover what the silver
data cannot: external vowel sandhi with **inflected left words** (for example
*tvayoditam* = *tvayā* + *uditam*), not only indeclinables.

Experts **verify generated proposals** rather than annotate from scratch.
The design limits the two risks of doing so:

- **Anchoring.** Reviewers tend to accept a single proposed answer.
- **Circularity.** If proposals came from our own system, the gold set would
  agree with it.

## 2. Source

The full Digital Corpus of Sanskrit in CoNLL-U format
(https://github.com/OliverHellwig/sanskrit, `dcs/data/conllu`).

| Property | Value (checked 2026-10-24) |
| --- | --- |
| License | CC BY 4.0. Stated in `dcs/data/readme.md` and `dcs/data/conllu/readme.md` |
| Citation | Hellwig, *The Digital Corpus of Sanskrit (DCS)*, 2010–2024 |
| Size | 744,757 lines, 5,464,818 words, 271 texts, one file per chapter |
| Annotation | "The analysis of each string has been verified by one annotator" |
| Fused strings | Multiword tokens (`3-5 asamajñānam`) with component words below them |
| Pre-sandhi forms | `Unsandhied=` in MISC. In one sampled chapter, 829 of 910 words are marked `UnsandhiedReconstructed=True` |
| Compound members | `Case=Cpd` |

The reconstruction flag means most pre-sandhi forms are derived, not
directly annotated. DCS therefore supplies **proposals** that are independent
of our system. It is not gold by itself. The gold label is the expert's
decision.

DCS_pick, our training source, is a 2017 subset of DCS. Its sentence IDs do
not match the CoNLL-U `sent_id` values, so overlap is checked on text.

## 3. Held-Out Text Selection

1. Clone the pinned DCS commit, using a sparse checkout of `dcs/data/conllu`.
   Record the commit hash and file hashes.
2. For each chapter, measure overlap with DCS_pick: exact normalised sentence
   matches, plus 30-character spans as in `docs/PRETRAINING_PLAN.md`.
3. Keep only chapters with **no** exact match and no near match. Prefer whole
   texts that are absent from DCS_pick.
4. Exclude Vedic texts in the first version. Our rules target classical
   external sandhi.
5. Record the held-out chapters in a manifest. They must also stay out of
   every future pretraining corpus. If GRETIL or other text is added later,
   it must be checked against this manifest too.

## 4. Item Extraction

An item is one external vowel-sandhi junction, taken from either:

- **Inside a multiword token**, between two consecutive components where the
  left one is not a compound member (`Case` is not `Cpd`), for example
  *pratītyeha*.
- **Across whitespace**, where the left word's final vowel has been changed
  (yaṇ, as in *namāmy asama-*) or the right word's initial vowel is fused.

The left pre-sandhi form must end in a vowel and the right one must start
with a vowel. Both come from `Unsandhied`.

The CoNLL-U files are IAST. Items are converted to SLP1 when extracted and
stored in SLP1, like everything else internally (protocol amendment 0.6).
Reviewers still see and type IAST. Their answers are converted back to SLP1
when merged. A word whose IAST contains *ai* or *au*, which could be a
diphthong or two vowels, is flagged for the grammarian to confirm.

Each item records:

- the sentence;
- the fused surface span with its offsets;
- the DCS proposal (left, right, lemmas, morphology);
- the reconstruction flag;
- the chapter and text IDs;
- whether the left word is inflected or indeclinable.

## 5. Sampling

- **About 600 items.** That allows at least 20 per evaluated rule where
  attested, with rare rules (a + ṛ, u + u) taken in full.
- **Strata:** junction type (vowel pair and result), left-word type (at
  least 40 percent inflected), and genre (epic, kāvya, śāstra, purāṇa).
- **At most 10 items per chapter,** to avoid clustering.
- **About 5 percent control items:** unambiguous cases chosen in advance,
  used to check attention. They are reported, not scored.

## 6. What Reviewers See

For each item:

- the sentence, with the fused span highlighted;
- the candidate splits, shuffled. This is the union of our rules'
  candidates and the DCS proposal, so the DCS answer is always among them.
  Nothing is pre-selected, and the source of each option is hidden.

The reviewer chooses one of:

- **one of the candidates;**
- **none of these, with the correct split typed in**, which keeps rule
  coverage measurable;
- **not an external sandhi boundary** (for example compound-internal, or a
  misalignment);
- **unsure**, with a comment.

The worksheet runs locally. It exports one JSONL file per reviewer, and a
validator checks each file before it is committed.

## 7. Roles and Workflow

| Step | Text reader | Grammarian |
| --- | --- | --- |
| Pilot: 30 items, then refine the guidelines | yes | yes |
| Main pass | all items | an independent 25 percent overlap |
| Adjudication | | every disagreement, every "none", every "unsure" |

- Reviewers work blind to each other, on separate branches and files, until
  both are done.
- The pilot items are excluded from the final set.
- Effort estimate (unverified):
  - text reader: about 5 hours at 30 seconds per item;
  - grammarian: about 2 to 3 hours, including adjudication.

## 8. Freezing and Use

1. The adjudicated set is frozen with a SHA-256 hash and committed with
   attribution.
2. The model settings to be evaluated are frozen in a protocol amendment
   **before** the gold set is scored.
3. The gold set is scored once. It is never used for tuning or for choosing
   models.

## 9. What the Paper Reports

- Inter-annotator agreement (Cohen's kappa) on the overlap.
- How often the DCS proposal was accepted. This is an estimate of DCS
  reconstruction error, which bears on the silver data.
- The rate of "none" answers, which measures rule coverage of the gold set.
- How proposals were generated and blinded, and the control-item results.
- Results separately for indeclinable and inflected left words.

## 10. Build Steps

1. Pinned sparse clone and a manifest of held-out chapters, with an overlap
   audit.
2. Item extractor, with unit tests on CoNLL-U fixtures.
3. Stratified sampler with a seed and a sampling report.
4. Worksheet in verify mode, plus a validator.
5. Reviewer guide, the pilot, then the main pass.
6. Merge script: agreement, adjudication queue, frozen output.

## 11. Open Questions

- Is 600 items enough? A larger set narrows confidence intervals but costs
  reviewer time.
- Should Vedic texts come later as a separate set?
- Would reviewers prefer the browser worksheet or files in the GitHub repo?
  Either way, answers must stay blind until both are done.
