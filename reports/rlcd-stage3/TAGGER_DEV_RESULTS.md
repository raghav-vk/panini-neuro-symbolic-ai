# RLCD Stage 3: Tagger Dev Results

**Dev only.** The settings were pre-registered in `docs/RLCD_TRANSITION_PLAN.md`
("Stage 3 Training Pre-Registered Settings", PR #82), with one addendum made
before any run: how forms without SLP1 letters are handled (PR #83). The test
part of the DCS division was not read. Runs were made 2026-11-14 on the
project Mac (MPS).

- **Generated tables:** `SUMMARY_TAGGER.md`.
- **Full numbers:** `tagger_dev.json`.
- **Code:** `scripts/train_tagger.py`, `scripts/eval_tagger.py`,
  `src/panini/tagger.py`.

**The task.** Tag each word of a real DCS sentence, with the segmentation
given, for vibhakti, vacana, liṅga, puruṣa and lakāra. Each head also has a
`NONE` option.

**The dev set.** 130,107 words in the 169 non-empty dev chapters. (28 of the
197 assigned chapters contain no sentences.) 55 words without a form were
dropped and no word was truncated. 8,412 words (6.5%) have forms never seen
in training.

## Decision Rules

| Hypothesis | Per seed (7 / 11 / 19) | Mean, 95% chapter bootstrap | Verdict |
| --- | --- | --- | --- |
| **H-S3-1** N1 beats B2 (kosha + prior) on full-tag accuracy | +0.027 / +0.024 / +0.023 | +0.025 [+0.004, +0.040] | Supported |
| **H-S3-2** N1 beats N2 (pretraining helps) | +0.065 / +0.064 / +0.062 | +0.064 [+0.061, +0.066] | Supported |

Both rules are met as pre-registered: every seed is above the reference, and
the interval excludes 0. H-S3-1 must be read with finding 2 below.

## Findings

**1. Pretraining is the clearest effect.** On full-tag accuracy, the
pretrained encoder (N1, 0.885 to 0.890) beats the same model trained from
scratch (N2, 0.822 to 0.825) by +0.064. The gain is the same across seeds and
the interval is narrow. It holds for every head, and is largest for puruṣa
(+0.076) and lakāra (+0.089). The pretraining text (P-A) contains no dev
chapter, because dev chapters were chosen to have no overlap with DCS_pick.

**2. N1's pooled lead over the kosha baseline comes from one text.**
Kathāsaritsāgara supplies 98,882 of the 130,107 dev words (76%). There N1
reaches 0.910 against 0.861 for B2. Across all 17 dev texts, N1 beats B2 in
only 8:

| Text | Words | N1 seed 7 | B2 |
| --- | ---: | ---: | ---: |
| Kathāsaritsāgara | 98,882 | 0.910 | 0.861 |
| Kirātārjunīya | 7,165 | 0.857 | 0.830 |
| Harṣacarita | 6,330 | **0.725** | **0.868** |
| Tantrāloka | 4,890 | 0.928 | 0.883 |
| Mīmāṃsāsūtrabhāṣya | 3,410 | 0.855 | 0.887 |
| Aṣṭasāhasrikā | 2,506 | **0.729** | **0.874** |
| Mūlamadhyamakārikāḥ | 1,254 | 0.930 | 0.892 |
| Śyainikaśāstra | 1,086 | 0.917 | 0.869 |

The losses include two prose texts, Harṣacarita and Aṣṭasāhasrikā, by about
0.14. Why is not established. A likely candidate is that the training pool is
mostly verse, while these texts have long prose compounds. That is a
hypothesis to test, not a finding. The honest statement is:

> N1 beats the kosha baseline on pooled dev, but the gain is carried by
> Kathāsaritsāgara and does not hold across texts.

**3. The neural tagger generalises to unseen forms; the lookup baselines do
not.** On the 8,412 words with forms never seen in training, N1 scores 0.777
to 0.788 full-tag accuracy. B2 scores 0.484; it takes 7,055 of these from the
kosha. B1 scores 0, by construction.

**4. Per head, N1 is ahead on nominals and behind on verbs:**

| Head (gold not NONE) | B2 | N1 seed 7 | N1 macro over values | B2 macro |
| --- | ---: | ---: | ---: | ---: |
| vibhakti | 0.860 | 0.916 | 0.877 | 0.843 |
| vacana | 0.946 | 0.961 | 0.938 | 0.928 |
| liṅga | 0.854 | 0.890 | 0.906 | 0.872 |
| puruṣa | 0.952 | 0.939 | 0.945 | 0.953 |
| lakāra | 0.950 | 0.920 | **0.719** | 0.911 |

The lakāra macro score (0.719) shows that rare lakāras are poorly learned.
The training pool has only 76 āśīrliṅ and 70 lṛṅ verbs.

**5. Brier loss (N3) gives no advantage over cross-entropy (N1).** Full-tag
accuracy is 0.883 to 0.887, against 0.885 to 0.890. Calibrated ECE is
slightly worse (0.038 to 0.040 against 0.033), and lakāra accuracy is lower
(0.891 to 0.894 against 0.916 to 0.920). This is descriptive, as
pre-registered (H-S3-3).

**6. Calibrating each head separately makes the whole-tag confidence worse.**
Word confidence is the product of the five heads' top probabilities.

- **Raw.** The product is already close to calibrated: ECE 0.014 to 0.016
  for N1, mean confidence 0.886 against accuracy 0.890.
- **Per-head scaling.** Every head is individually overconfident and gets a
  temperature above 1 (1.04 to 1.27). The heads' errors are correlated,
  though: when case is wrong, number and gender often are too. So the product
  of separately calibrated probabilities understates how often the whole tag
  is right. Calibrated ECE rises to 0.033, and mean confidence falls to
  0.857.
- **Implication.** The confidence used to gate a whole analysis must be
  calibrated on the joint outcome, not head by head. This is the review's
  open "joint AST confidence" gap (plan section 2), now observed. A joint
  calibration was not pre-registered and is not reported here.

**7. Abstention pays off.** For N1 the risk–coverage area is 0.016. Keeping
the most confident 90% of words gives 0.937 to 0.941 full-tag accuracy, and
95% gives 0.917 to 0.921, against 0.885 to 0.890 overall. For N2 the area is
0.037. This is reported on per-head calibrated confidence, as pre-registered.
Temperature scaling can change the ordering slightly, because the five
temperatures differ.

**8. Compute.**

- **Model size.** 4,945,444 parameters: the encoder plus 8,224 in the heads.
- **Training time.** About 10 minutes per run on MPS, from the seven clean
  runs (9.8 to 10.3). Two recorded times are inflated by the machine, not the
  model: N1 seed 11 (73.3 minutes, memory swapping) and N2 seed 7 (115.1
  minutes, the Mac slept).
- **Tagging time.** The whole dev set took 14.9 s on MPS and 15.4 s on CPU.
  The two are almost equal, which shows the evaluation harness is dominated
  by Python bookkeeping, not by the model. So this is not a valid measure of
  model speed. A proper latency measurement needs a separate harness.

## What This Supports

Supported on dev:

- **Pretraining helps.** The 4.94M-parameter encoder, pretrained on Sanskrit
  text it never saw at evaluation, tags real classical Sanskrit far better
  than the same model trained from scratch (H-S3-2, robust).
- **It generalises beyond lookup.** It tags unseen forms far better than
  dictionary or lookup baselines.

Not supported: that it beats a kosha-plus-statistics baseline across
classical texts. It does on pooled dev (H-S3-1), but only because one text
dominates. It loses clearly on two prose texts and on verbs.

## Caveats

- **Dev only.** A test run needs a frozen amendment, and per-text results
  should be part of what is frozen and reported.
- **Gold-segmented input.** Real input would need segmentation first.
- **Silver labels.** DCS analyses are verified by one annotator; most
  pre-sandhi forms are reconstructed.
- **Merged classes.** Lakāra is scored on DCS's merged classes (`Lit|Lun`,
  `Lrt|Lut`).
- **Narrow bootstrap.** The bootstrap resamples dev chapters, which reflects
  chapter variation but not which texts were chosen. Per-text results show
  that choice matters.

## Suggested Next Steps (not yet registered)

1. A joint calibration of the whole-tag confidence (finding 6). This is the
   input the RLCD gate needs.
2. A diagnosis of the prose texts (finding 2): sentence length, compound
   density, and per-head errors on Harṣacarita and Aṣṭasāhasrikā.
3. A hybrid: B2's analysis for seen verb forms, N1 elsewhere. Findings 3 and
   4 suggest the two are complementary. Sanskrit-side RL fine-tuning (plan
   stage 3 step 6) is the larger version of the same idea.
