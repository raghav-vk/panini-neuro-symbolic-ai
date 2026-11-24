# Sandhi Pretraining: Confirmatory Test Results

**The one test run under protocol amendment 0.9** (section 11.7,
`docs/SANDHI_PRETRAINING_TEST_AMENDMENT.md`, with its erratum), made
2026-11-23 with `scripts/run_sandhi_pretraining_test.py` at merge commit
`564d1f1`. Every encoder, split file, rule set and data release matched its
frozen hash. Nothing was trained, selected or tuned on test, and there was no
re-run. Before the run, the script's `--smoke` mode reproduced every recorded
dev result exactly.

- **Generated tables:** `SUMMARY.md`.
- **Full numbers:** `sandhi_pretraining_test.json`.

**Test data.** The right-word holdout (`strict_right_lemma`): 821 examples of
unseen right-hand lemmas in 817 source groups, from the silver DCS
boundaries, in SLP1 (file SHA-256 `90129cbf…`). **This is the fourth use of
these 821 items** and the first use of the SLP1 file; the three earlier uses
read the IAST file.

## Verdicts

Paired differences are against R-K, the linear ranker with the kosha.
Intervals are 95% source-group bootstrap intervals of the seed-mean
difference (1,000 resamples, seed 1729).

| ID | Hypothesis | Per seed (7 / 11 / 19) | Mean [95% CI] | Exact McNemar p | Verdict |
| --- | --- | --- | --- | --- | --- |
| **T-P1** | R-N (neural score, no kosha) is non-inferior to R-K, margin 0.010 | −0.016 / −0.006 / −0.018 | −0.013 [−0.033, +0.006] | 0.15 / 0.63 / 0.10 | **Not supported** |
| **T-P1s** | R-N beats R-K | as above | as above | as above | **Not supported** |
| **T-P2** | R-KN (kosha + neural score) beats R-K | +0.015 / +0.024 / +0.016 | +0.018 [+0.004, +0.033] | 0.088 / 0.0017 / 0.060 | **Supported** |
| **T-P3** | R-KN coverage at τ = 0.95 lies within [0.71, 0.86] | 0.781 / 0.788 / 0.762 | — | — | **Supported** |

## What the Test Establishes

**1. The neural word score adds to the kosha.** With both, the linear ranker
reaches 0.956, 0.966 and 0.957 top-1, against 0.942 for the kosha alone. The
gain holds for every seed and the interval excludes 0. These are the best
scores on this test set so far. For the single seeds, R-KN wins 27–29 items
and loses 9–15; McNemar p is below 0.05 for seed 11 only, as the rule
(every seed positive, interval of the mean above 0) anticipated.

**2. The gain is about a third of the dev gain.** On dev, R-KN beat R-K by
+0.048 to +0.054; on test, by +0.015 to +0.024. Dev was used repeatedly, and
the choice to score words alone was made on dev, so some shrinkage was
expected. The size is not.

**3. The neural score does not replace the kosha.** On dev, R-N beat R-K by
+0.022 to +0.026. On test it is behind for every seed (−0.006 to −0.018), and
two seeds fall outside the non-inferiority margin. The losses are
concentrated in SDH-001, which has 503 of the 821 examples: R-K 0.942, R-N
0.899 to 0.915. R-N is ahead on several small rules (SDH-003, SDH-013), but
they are too small to weigh.

R-N is the arm with no CC BY-NC-SA kosha data in it. On this evidence, a
ranker without the kosha costs about 0.013 top-1, with an interval from
−0.033 to +0.006.

**4. The gate transfers.** At the frozen τ = 0.95, R-KN accepts 76–79% of
test items (dev 76–81%) at 0.994–0.995 accuracy (dev 0.993–0.996). The
gate's confidence is the raw ranker probability, with no calibration.

**5. The reference score.** R-K scores 0.942 (0.945 tie-averaged) on the
SLP1 file, against 0.943 (0.946) on the IAST file in the third use. The
erratum anticipated this: candidate order, and so tie-breaking, depends on
the transliteration.

**6. Descriptive.**

- **Words in sentence.** Scoring the words in their sentence is worse than
  scoring them alone, as on dev: R-N 0.890–0.915 and R-KN 0.939–0.954.
- **Strict P-B pretraining.** It stays below the kosha: R-N 0.833 (−0.108)
  and R-KN 0.922 (−0.019, p 0.056), with gate coverage 0.658.

## What the Paper Can Say

Tested once, on the 821 right-word holdout items:

- A word score from a Sanskrit-pretrained 4.94M-parameter byte encoder
  improves a dictionary-based linear ranker, by +0.018 top-1.
- Its raw confidence supports abstention: about 78% of items accepted at
  0.995 accuracy, with the threshold chosen on dev.

It cannot say that the neural score replaces the dictionary, or that the dev
gains carry over at full size.

## Disclosures

- **Fourth use.** The items were scored three times before. The R-K score on
  the IAST file was known before this run.
- **Silver data, draft rules.** The labels are silver DCS boundaries, and the
  18 rules are unreviewed drafts. These are right-word holdout results, not
  the strict both-lemma holdout or the expert gold set.
- **P-A pretraining.** The confirmatory encoders saw the held-out right-hand
  words in other sentences; the strict P-B encoder, which did not, is below
  the kosha.
- **Narrow bootstrap.** The interval covers item and source-group variation,
  not the choice of texts or the selection of settings on dev.
- **Erratum.** The frozen split hashes were corrected from the IAST to the
  SLP1 files before the run (amendment section 7).
