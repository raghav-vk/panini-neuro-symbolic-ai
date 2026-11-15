# Amendment 0.9: Frozen Settings for the Sandhi Pretraining Test Run

**Status:** Adopted 2026-11-14 as section 11.7 of
`docs/EXPERIMENT_PROTOCOL.md`. At adoption no pretraining condition had been
scored on the test set. The test run follows exactly once, after the
hash-checked frozen script (section 4) is merged. It is the "further amendment" that section
11.3 and `docs/PRETRAINING_PLAN.md` section 8, step 7, require before the
test run.

**Test set.** The right-word holdout (`strict_right_lemma`): 821 examples of
unseen right-hand lemmas, from the silver DCS boundaries.

## 1. Why This Run, and What Is Already Known

The pretraining results in paper section 11.3 are dev results. The plan
calls for freezing the settings and making one test run with paired
comparisons.

**This is the fourth use of this test set**, after:
1. a timing run with the original 12 rules;
2. the amendment 0.3 model;
3. the amendment 0.4 comparison.

It is disclosed as reuse.

**The reference score is already known.** Linear + kosha scored 0.943
(0.946 tie-averaged) in the third use. Only the pretraining arms below are
unseen on test. The final untouched evaluation remains the expert gold set
(`docs/GOLD_SET_PLAN.md`), for which texts are reserved.

## 2. What Is Frozen

The values are in `reports/pretraining-v1/frozen_test_settings.json`.

**Encoders**, by SHA-256:
- the size-S encoders pretrained on P-A, seeds 7, 11 and 19
- the P-B seed 7 encoder (descriptive)

These are the final checkpoints used on dev.

**Neural word score.** The discriminator's log P(attested) for each
candidate's left and right word, scored **alone**, not in their sentence
(`scripts/annotate_neural_lexicon.py --no-context`). This was chosen on dev:
it was better and steadier (paper section 11.3).

**Ranker.** `linear_features_short_vowel`, seed 7, trained on the training
split only, exactly as in the dev runs:

| Arm | Lexical features | Encoders |
| --- | --- | --- |
| R-K | kosha (reference) | — |
| R-N | neural score, no kosha | P-A seeds 7, 11, 19 |
| R-KN | kosha + neural score | P-A seeds 7, 11, 19 |
| R-N-PB, R-KN-PB | as above | P-B seed 7 (descriptive) |

**Gate.** The R-KN ranker's raw top-candidate probability, accepted at
τ = 0.95, with no calibration. RLCD stage 1 found temperature scaling
changed nothing on dev. Dev coverage was 0.765, 0.806 and 0.761, with
accepted accuracy 0.993 to 0.996.

**Data.**
- the training, dev and test split files (SHA-256 in the settings file)
- the 18 draft rules (`rules_sha256`)
- the Vidyut 0.4.0 data release

**Not tested.**
- **H-P3** (fine-tuned pretrained ranker) failed the plan's dev stopping
  rule: it was no better than 0.909.
- **The reference-only rows** of plan section 7 (ByT5-Sanskrit, rcNN) were
  not run.

## 3. Confirmatory Hypotheses (test)

Paired differences are against R-K, on the 821 test examples. Intervals are
95%, from 1,000 bootstrap resamples of source groups, seed 1729. Exact
McNemar p-values are reported per seed.

| ID | Hypothesis | Rule | Dev result |
| --- | --- | --- | --- |
| **T-P1** | H-P1: the neural score can replace the kosha without losing accuracy (R-N against R-K) | Non-inferiority: every seed's difference > −0.010, and the lower bound of the mean difference over seeds > −0.010 | +0.022 to +0.026 |
| **T-P1s** | R-N beats R-K | Every seed > 0, and the interval excludes 0 | as above |
| **T-P2** | H-P2: adding the neural score to the kosha improves on the kosha alone (R-KN against R-K) | Every seed > 0, and the interval excludes 0 | +0.048 to +0.054 |
| **T-P3** | The gate transfers: R-KN coverage at τ = 0.95 lies within [0.71, 0.86] for every seed (dev range ± 0.05) | as stated | 0.761–0.806 |

**Also reported, with no hypothesis:**
- the P-B arms (dev: below the kosha)
- in-sentence scoring
- accepted accuracy at τ
- tie-averaged accuracy
- per-rule results

All four verdicts are reported whatever the outcome. No multiplicity
correction is applied.

## 4. Procedure

1. **Code before the run.** A hash-checked frozen script is reviewed and
   merged first, as for amendment 0.8. It:
   - checks every hash
   - refuses uncommitted code and a second run
   - annotates the test file with each frozen encoder's word scores
   - trains the three arms on the training split
   - scores the test file and writes only to `reports/pretraining-v1/test/`
2. **One run.** A re-run is allowed only after a crash that produced no
   results.
3. **Nothing is retrained, reselected or retuned** after the test numbers
   are seen.

## 5. Disclosures

- **Repeated dev use.** Dev was used repeatedly, including with the first
  checkpoint. Scoring words alone was chosen on dev.
- **Fourth test use.** This is the fourth use of the test set, and the R-K
  score is already known.
- **Silver data.** The data are silver and the rules are drafts. These are
  right-word holdout results, not section 9.3 results.
- **Licensing.** The kosha includes CC BY-NC-SA material. The pretrained
  encoders do not; no kosha data was used in pretraining.

## 6. Decisions at Adoption (2026-11-14)

1. **Margin.** The non-inferiority margin for T-P1 is 0.010.
2. **Timing.** The fourth use goes ahead now. The expert gold set remains
   the final untouched evaluation.
3. **P-B arms.** They stay descriptive.
