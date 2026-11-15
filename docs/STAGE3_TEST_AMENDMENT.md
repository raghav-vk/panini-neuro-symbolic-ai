# Amendment 0.8: Frozen Settings for the RLCD Stage 3 Test Run

**Status:** Adopted 2026-11-14 as section 11.6 of
`docs/EXPERIMENT_PROTOCOL.md`. At adoption the stage 3 test part had never
been read. The test run follows exactly once, after the hash-checked
`--frozen` mode (section 4) is merged.

**Scope.** The DCS stage 3 test part, which is used here for the first time.
It is a different set from the right-word holdout sandhi test set (protocol
sections 9.5 and 11.1 to 11.3), and that set is not touched here.

## 1. Why This Run

Every stage 3 result so far is a dev result: the tagger (`TAGGER_DEV_RESULTS.md`)
and the calibration rounds (`JOINT_CALIBRATION_RESULTS.md`,
`PLATT_CALIBRATION_RESULTS.md`). Dev was used to choose things, and the J4
calibrator was chosen post hoc, after two earlier calibrators failed. This
run tests the choices on data none of them saw.

## 2. What Is Frozen

Nothing below may change after adoption. The values are recorded in
`reports/rlcd-stage3/frozen_test_settings.json`.

**Systems.**

| System | Definition | Frozen by |
| --- | --- | --- |
| N1 | Tagger fine-tuned from the P-A encoder, seeds 7, 11, 19 | Checkpoint SHA-256s (e.g. seed 7 `5019b8d3…`) |
| N2 | Same architecture from scratch, seeds 7, 11, 19 | Checkpoint SHA-256s |
| N3 | As N1 with Brier loss, seeds 7, 11, 19; **descriptive only** | Checkpoint SHA-256s |
| B2 | Kosha + training prior, as in `scripts/eval_tagger.py` | The code at the run commit, the training file (`split_manifest.json` hash) and the Vidyut 0.4.0 data (`scripts/fetch_vidyut_data.py` hash) |
| J0 | Raw product of the five head probabilities | — |
| J4 | Platt scaling of logit(c₀), fitted once on **all** dev words per N1 seed | (a, b) = (0.8036, 0.2338), (0.8271, 0.1840), (0.8192, 0.1830) for seeds 7, 11, 19 |
| Gate | Accept a word if its J4 confidence ≥ τ, where τ gives 90% coverage on dev | τ = 0.6007, 0.5896, 0.5855 for seeds 7, 11, 19 |

**Data and processing.**
- **The test part.** 192 chapters, 16,271 sentences and 133,178 words, in 25
  texts. Kathāsaritsāgara supplies 11,513 of the sentences. These figures are
  structure from `split_manifest.json`; no outcomes are known.
- **Processing, exactly as on dev.**
  - Forms keep their SLP1 letters only; words left with no form are dropped
    and counted.
  - Sentences are chunked at word boundaries to at most 256 bytes.
  - Labels come from `src/panini/tagger.py`.

**Metrics and intervals.** As pre-registered for dev:
- full-tag accuracy, per-head accuracy, unseen forms and per text
- NLL, ECE (10 equal-mass bins) and Brier of the whole-tag confidence
- 95% intervals from 1,000 bootstrap resamples of test chapters, seed 1729

## 3. Confirmatory Hypotheses (test)

Each uses the same rule as on dev: it holds for every seed, and the 95%
chapter-bootstrap interval of the mean paired difference excludes 0.

| ID | Hypothesis | Dev result it tests |
| --- | --- | --- |
| **T-1** | N1 beats N2 on full-tag accuracy | H-S3-2, +0.064 |
| **T-2** | N1 beats B2 on full-tag accuracy, pooled | H-S3-1, +0.025 |
| **T-2b** | **B2 beats N1** on full-tag accuracy over the words outside Kathāsaritsāgara | Dev: N1 − B2 = −0.041 to −0.048 on 31,225 words; a negative finding tested for replication |
| **T-3** | J4, with the frozen (a, b), has lower NLL than J0 | H-J3, −0.0028 |
| **T-4** | The gate transfers: for every seed, test coverage at the frozen τ lies within [0.85, 0.95] | Dev coverage 0.90 by construction |

**Also reported, with no hypothesis:**
- results per text
- accepted full-tag accuracy at τ
- ECE for J0 and J4
- N1 against B2 on unseen forms and per head
- N3 (descriptive arm): full-tag accuracy, per-head accuracy and the J0 calibration metrics. No J4 is fitted for N3, and no hypothesis concerns it.

**Multiplicity.** These are five pre-specified tests, and all five are
reported whatever the outcome. No correction is applied. Each verdict stands
alone and is labelled confirmatory.

## 4. Procedure

1. **Code before the run** (reviewed and merged first; it is not run on test
   until this amendment is adopted):
   - `scripts/eval_tagger.py` and `scripts/joint_calibration.py` gain a
     `--split test --frozen reports/rlcd-stage3/frozen_test_settings.json`
     mode.
   - That mode refuses to run if any checkpoint, data or settings hash
     differs.
   - It applies J4 and τ as recorded; it fits nothing on test.
   - It writes only to `reports/rlcd-stage3/test/`.
2. **One run.** The test part is read once. A re-run is allowed only after a
   crash that produced no results, and any deviation is recorded in the
   report.
3. **Nothing is retrained or reselected** after the test numbers are seen.
4. **The report states every verdict,** including those against the
   project's hopes. A failure of T-2, or a confirmation of T-2b, is reported
   as plainly as the rest.

## 5. Disclosures

- **Dev was used repeatedly.** It was used for the tagger, for three
  calibration rounds and for choosing J4 and τ.
- **Provisional tables.** The tagger was not trained on Tier 1, so the
  provisional table acceptance (`data/rlcd/provisional_acceptance.json`)
  does not affect this run.
- **Silver test labels.** Labels are DCS analyses verified by one annotator,
  not the expert gold set. The gold set (`docs/GOLD_SET_PLAN.md`) is reserved
  separately and is not used here.

## 6. Decisions at Adoption (2026-11-14)

1. **T-2b stays** as a confirmatory test of the negative dev finding.
2. **T-4 tolerance.** ±0.05 around 90% coverage.
3. **N3 is added as a descriptive arm.** It is frozen by checkpoint hash and
   carries no hypothesis.
