# RLCD Stage 3: Confirmatory Test Results

**The one test run under protocol amendment 0.8** (section 11.6,
`docs/STAGE3_TEST_AMENDMENT.md`), made 2026-11-14 with
`scripts/run_stage3_test.py` at commit `6367e00`. Every checkpoint, data file
and setting matched its frozen hash, and nothing was fitted on test. This was
the first and only reading of the stage 3 test part. The right-word holdout
sandhi test set was not touched.

- **Generated tables:** `SUMMARY.md`.
- **Full numbers:** `stage3_test.json`.

**Test data.** 133,107 words in the 167 non-empty test chapters. (25 of the
192 contain no sentences.) 71 words without a form were dropped. 47,089 words
lie outside Kathāsaritsāgara, and 9,446 have forms unseen in training.

## Verdicts

| ID | Hypothesis | Per seed (7 / 11 / 19) | Mean, 95% chapter bootstrap | Verdict |
| --- | --- | --- | --- | --- |
| **T-1** | N1 beats N2: pretraining helps | +0.063 / +0.061 / +0.060 | +0.061 [+0.058, +0.064] | **Supported** |
| **T-2** | N1 beats B2 (kosha + prior), pooled | +0.021 / +0.017 / +0.017 | +0.018 [−0.005, +0.040] | **Not supported** |
| **T-2b** | B2 beats N1 outside Kathāsaritsāgara | +0.036 / +0.039 / +0.037 | +0.037 [−0.018, +0.081] | **Not supported** |
| **T-3** | The frozen J4 has lower NLL than the raw product | −0.0042 / −0.0034 / −0.0037 | −0.0038 [−0.0058, −0.0020] | **Supported** |
| **T-4** | Gate coverage at the frozen τ lies within [0.85, 0.95] | 0.886 / 0.884 / 0.885 | — | **Supported** |

## What the Test Establishes

**1. Pretraining helps, and it replicates.** The pretrained 4.94M-parameter
encoder tags unseen classical Sanskrit 0.061 better on full-tag accuracy than
the same model trained from scratch. Dev showed +0.064. The gain holds for
every seed and every head. This is the robust result of stage 3.

**2. The whole-analysis calibration and the gate carry over.**

- **J4 transfers.** The two-parameter J4 was fitted only on dev, yet it
  lowers NLL on test for every seed and cuts ECE from 0.019–0.020 to
  0.006–0.008.
- **The gate holds.** The threshold τ was set for 90% coverage on dev. On
  test it accepts 88.4–88.6% of words, inside the frozen tolerance.
- **The accepted words are as accurate as on dev.** Their full-tag accuracy
  is 0.939–0.942 (dev 0.939–0.942), against 0.878–0.882 for all words. So the
  system can say which words to trust, and that statement holds on new text.

**3. The neural tagger does not reliably beat the kosha baseline.** N1 is
ahead pooled for every seed (+0.017 to +0.021), but the interval includes 0,
so T-2 fails. Of the 25 test texts, N1 is better in 14, ties in one and is
worse in 10. The losses include large prose texts:

| Text | Words | N1 seed 7 | B2 |
| --- | ---: | ---: | ---: |
| Kathāsaritsāgara | 86,018 | 0.914 | 0.862 |
| Harṣacarita | 12,305 | **0.694** | **0.860** |
| Kirātārjunīya | 9,336 | 0.867 | 0.841 |
| Mīmāṃsāsūtrabhāṣya | 3,669 | 0.867 | 0.892 |
| Śatakatraya | 2,511 | 0.800 | 0.855 |
| Lalitavistara | 1,447 | **0.738** | **0.873** |
| Avadānaśataka | 643 | 0.781 | 0.877 |

Harṣacarita, the largest test text after Kathāsaritsāgara, is the clearest
case: N1 trails by 0.17, against 0.14 on dev.

**4. The negative finding is consistent, but not confirmed.** Outside
Kathāsaritsāgara the kosha baseline is ahead for every seed, by +0.036 to
+0.039 (dev +0.041 to +0.048). Those 47,089 words come from 24 texts of very
different difficulty, so the chapter bootstrap is wide and the interval
includes 0. The dev smoke run had already shown the same rule failing on dev
(interval [−0.006, +0.084]). T-2b was underpowered as frozen; it is not
evidence that the gap is absent.

**5. Descriptive.**

- **Unseen forms.** N1 reaches 0.760 to 0.768 full-tag accuracy on them,
  against 0.485 for B2.
- **Brier loss.** N3 again matches N1 on accuracy (0.875 to 0.878) and is
  slightly worse on verbs.

## What the Paper Can Say

Tested once, on held-out classical texts never seen in pretraining or
training:

- **Pretraining helps.** A 4.94M-parameter byte encoder pretrained on
  Sanskrit tags real Sanskrit 0.06 better than the same model trained from
  scratch.
- **The confidence is usable.** Its two-parameter calibrated confidence is
  accurate across texts, and a threshold chosen on dev keeps about 88% of
  words at about 94% full-tag accuracy on test.
- **It generalises.** It handles unseen word forms far better than lookup.

What it cannot say:

- **Not a reliable win over the kosha baseline.** The neural tagger does
  not reliably beat a dictionary-plus-statistics baseline across texts. It
  trails it on several prose texts, by as much as 0.17.

## Caveats

- **Silver labels.** Test labels are DCS analyses verified by one annotator,
  not the expert gold set.
- **Gold-segmented input.** The segmentation is given.
- **Narrow uncertainty.** The bootstrap reflects chapter variation within
  these texts, not the choice of texts.
- **Lenient text rule.** "Classical" (no Vedic metadata block, time slot
  other than 1) let in two Kauśikasūtra commentaries, which are Vedic-ritual
  texts, with 488 test words between them.
- **Spent test part.** The test part is now used. Any further claim on it
  must be disclosed as a second use.
