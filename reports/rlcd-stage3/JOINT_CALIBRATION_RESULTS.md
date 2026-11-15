# RLCD Stage 3: Joint Calibration Results (Dev, Post Hoc)

**Dev only, post hoc.** The settings were pre-registered in
`docs/RLCD_TRANSITION_PLAN.md` ("Stage 3 Joint Calibration Pre-Registered
Settings", PR #85), but only after the per-head result that motivated them
was seen. The test part was not read.

- **Generated tables:** `JOINT_CALIBRATION.md`.
- **Full numbers:** `joint_calibration.json`.
- **Code:** `scripts/joint_calibration.py`.

**Quantity calibrated.** The confidence that a word's whole tag (all five
heads) is correct. There are 130,107 dev words and 169 chapters. Six
checkpoints were used: N1 and N3, seeds 7, 11 and 19.

## Decision Rules

| Hypothesis | Per seed, NLL difference (7 / 11 / 19) | Mean, 95% chapter bootstrap | Verdict |
| --- | --- | --- | --- |
| **H-J1** J2 beats the raw product (J0) | +0.029 / +0.032 / +0.032 | +0.031 [+0.030, +0.032] | Not supported: J2 is worse |
| **H-J2** J2 beats per-head temperatures (JT) | +0.021 / +0.023 / +0.023 | +0.022 [+0.017, +0.026] | Not supported: J2 is worse |

## Why J1 and J2 Failed: a Specification Error

J1 and J2 model the log-odds of correctness as a linear function of log c₀,
or of the five log pᵢ. For a confident word c₀ is close to 1, so log c₀ is
close to 0, and the model gives every such word nearly the same probability,
σ(b). Neither calibrator can express "99.9% sure". The symptom fits exactly:
mean confidence equals accuracy (0.890 / 0.890), but ECE is about 0.05 and
NLL is worse than no calibration at all.

The standard form of Platt scaling uses logit(c₀), which does not have this
limit. This was a mistake in writing the settings, not a property of joint
calibration. The hypotheses are reported as pre-registered: not supported. A
correctly specified parametric calibrator would need a new pre-registration.

## Findings

Cross-fit, N1 seeds 7 / 11 / 19:

| Calibrator | NLL | ECE (10 equal-mass bins) | Mean confidence vs accuracy |
| --- | --- | --- | --- |
| J0, raw product | 0.202 / 0.204 / 0.206 | 0.016 / 0.014 / 0.015 | 0.886 vs 0.890 (seed 7) |
| JT, per-head temperatures | 0.210 / 0.213 / 0.215 | 0.033 / 0.033 / 0.033 | 0.857 vs 0.890 |
| J1, Platt on log c₀ | 0.240 / 0.244 / 0.245 | 0.050 / 0.051 / 0.052 | 0.890 vs 0.890 |
| J2, logistic on log pᵢ | 0.231 / 0.236 / 0.238 | 0.045 / 0.046 / 0.048 | 0.890 vs 0.890 |
| **J3, isotonic on c₀** | **0.199 / 0.202 / 0.203** | **0.0010 / 0.0006 / 0.0009** | 0.890 vs 0.890 |

1. **Isotonic regression (J3) calibrates the whole-tag confidence almost
   exactly.** It has the lowest NLL of the five calibrators for every seed,
   though the margin over J0 is small (about 0.003 to 0.004). It cannot
   reorder words, so abstention is unchanged (AURC 0.015 to 0.016). The
   bootstrap ECE intervals for J3 lie slightly above the point value,
   because ECE is biased upward under resampling.
2. **The raw product (J0) is already good.** JT, J1 and J2 all make it
   worse. Of these, only JT changes the ordering, and only slightly.
3. **Calibration does not transfer fully across texts.** Fitted on
   Kathāsaritsāgara and scored on the other 16 texts (31,225 words):
   - accuracy there is lower (0.820 to 0.827)
   - the raw product is underconfident (0.805 against 0.827 for seed 7,
     ECE 0.027 to 0.031)
   - J3 lowers ECE to 0.016 to 0.018, with NLL about equal to J0's
4. **The prose texts are the worst calibrated.** For N1 seed 7, J0's ECE is
   0.065 on Harṣacarita and 0.054 on Aṣṭasāhasrikā, against 0.011 to 0.029
   on the other large texts. J3 reduces them to 0.039 and 0.030. These are
   the same texts where the tagger is weakest
   (`TAGGER_DEV_RESULTS.md`, finding 2).
5. **N3 (Brier loss) is no better calibrated than N1.** Every calibrator
   ranks the same way for both.

## What This Means for the RLCD Gate

- **Use isotonic regression on the joint outcome.** A gate over whole
  analyses should calibrate the joint confidence directly. Isotonic
  regression on the product of head probabilities did this almost exactly in
  dev cross-fitting.
- **Never multiply per-head calibrated probabilities.** That is the one
  thing to avoid.
- **Calibrate per text type as well.** Because calibration shifts across
  texts, a gate used on a new genre (prose, in particular) needs
  recalibration or a calibrator fitted on mixed genres.

Before any of this is used as a claim, it needs a confirmatory run on the
test part, under a frozen amendment that fixes J3 and its fitting data in
advance.

## Caveats

- **Post hoc on dev.** The analysis was motivated by a dev result already
  seen.
- **Small margin.** J3's NLL gain over J0 is small; its large gain is in
  ECE.
- **Mis-specified parametric arms.** The J1 and J2 failures say nothing
  about correctly specified parametric calibration.
