# RLCD Stage 3: Logit Platt Calibration Results (Dev, Post Hoc)

**Dev only, post hoc.** The settings were pre-registered in
`docs/RLCD_TRANSITION_PLAN.md` ("Stage 3 Logit Platt Calibration
Pre-Registered Settings", PR #87), after the J0 to J3 results were seen. The
test part was not read.

- **Generated tables:** `PLATT_CALIBRATION.md`.
- **Full numbers:** `platt_calibration.json`.
- **Command:** `scripts/joint_calibration.py --calibrators J0 J3 J4 J5 --name platt_calibration`.

**Quantity calibrated.** The confidence that a word's whole tag is correct,
on 130,107 dev words in 169 chapters, for N1 and N3, seeds 7, 11 and 19. J0
and J3 reproduce the first round's numbers exactly
(`JOINT_CALIBRATION_RESULTS.md`).

## Decision Rules

| Hypothesis | Per seed, NLL difference (7 / 11 / 19) | Mean, 95% chapter bootstrap | Verdict |
| --- | --- | --- | --- |
| **H-J3** J4 (Platt on logit c₀) beats J0 | −0.0033 / −0.0024 / −0.0026 | −0.0028 [−0.0037, −0.0020] | **Supported** |
| **H-J4** J5 (logistic on the five head logits) beats J0 | +0.0100 / +0.0125 / +0.0126 | +0.0117 [+0.0106, +0.0127] | Not supported: J5 is worse |

## Findings

**1. With the logit, two parameters are enough.** J4 lowers NLL below the
raw product for every seed. Cross-fitted, it nearly matches isotonic
regression:

| N1, cross-fit | J0 | J3, isotonic | J4, Platt on logit | J5 |
| --- | --- | --- | --- | --- |
| NLL (seeds 7 / 11 / 19) | 0.202 / 0.204 / 0.206 | 0.199 / 0.202 / 0.203 | 0.199 / 0.202 / 0.203 | 0.212 / 0.217 / 0.219 |
| ECE | 0.016 / 0.014 / 0.015 | 0.0010 / 0.0006 / 0.0009 | 0.005 / 0.005 / 0.006 | 0.010 / 0.011 / 0.010 |

Isotonic regression still has the lowest ECE in-domain. J4 has the same NLL
to within 0.0003 or less.

**2. J4 transfers across texts better than isotonic regression.** Fitted on
Kathāsaritsāgara and scored on the other 16 texts (31,225 words):

| N1, transfer | J0 | J3, isotonic | J4 | J5 |
| --- | --- | --- | --- | --- |
| NLL (seeds 7 / 11 / 19) | 0.259 / 0.264 / 0.262 | 0.259 / 0.262 / **0.268** | **0.253 / 0.260 / 0.258** | 0.272 / 0.279 / 0.280 |
| ECE | 0.031 / 0.028 / 0.027 | 0.018 / 0.018 / 0.016 | **0.016 / 0.017 / 0.013** | 0.024 / 0.025 / 0.026 |

- **J4 is best for N1** on both NLL and ECE, for every seed.
- **J4 beats the raw product for N3 too:** on transfer NLL for all six
  runs.
- **Isotonic regression is less robust.** Its step function, fitted to one
  text, is worse than doing nothing on transfer NLL for N1 seed 19 and for
  N3 seeds 11 and 19.

**3. J5 is worse than J0, as its structure suggests.** A sum of head logits
cannot reproduce a product of probabilities. Its six weights also reorder
words, which worsens abstention: AURC is 0.017 to 0.018 against 0.015 to
0.016. Learning how the heads' errors are correlated, which J5 was meant to
do, needs a different form from a linear model on head logits.

**4. N3 is again worse calibrated than N1.** J4 brings N3's ECE only to 0.009
to 0.011, against 0.005 to 0.006 for N1.

**5. The prose texts improve but stay the worst** (cross-fit, N1 seed 7).
Harṣacarita's ECE goes from 0.065 (J0) to 0.047 (J4) or 0.039 (J3), and
Aṣṭasāhasrikā's from 0.054 to 0.044 or 0.030.

## Recommendation for the RLCD Gate

Use **J4, Platt scaling of logit(c₀)**, as the gate's calibrator for whole
analyses.

- **Measured:** it is as good as isotonic regression in-domain, better
  across texts, and never worse than doing nothing.
- **Small:** it is two numbers, so it ships with the model and ports to the
  Rust runtime trivially (plan section 7).
- **Avoid** multiplying per-head calibrated probabilities (JT), and linear
  models on per-head features (J1, J2, J5).

Before this becomes a claim, it needs a confirmatory run on the test part,
under a frozen amendment that fixes J4, its fitting data and the gate
thresholds in advance.

## Caveats

- **Post hoc on dev,** and chosen after two earlier calibrators failed.
- **Small NLL gains.** J4's NLL gain over J0 is small (0.003); its larger
  gains are in ECE and in transfer.
- **Single-direction transfer.** It was tested one way only: from one large
  verse text to the rest.
