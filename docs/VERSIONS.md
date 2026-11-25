# How the System Evolved: Versions 0.1 to 0.10

Each version is one step in the project, numbered after the experiment
protocol ([EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md)). Version 0.1 is
the base protocol; 0.2 to 0.9 are its amendments, each decided before the
results it governs. Version 0.10, the community review pilot, is a project
step rather than a protocol amendment.

Read this page top to bottom to see why each piece exists: every version
answers a question the previous one raised. What comes next is in
[ROADMAP.md](ROADMAP.md).

**Three numberings to keep apart:**
- **Versions**, as here: 0.1 to 0.10.
- **Folder suffixes** such as `dcs-silver-v2` and `dcs-silver-v3`. These count
  data and report generations, not versions: `reports/dcs-silver-v2` belongs
  to version 0.3. The maps in [reports/README.md](../reports/README.md) and
  [data/README.md](../data/README.md) give the version of every folder.
- **The manuscript version**: [the paper](paper/panini-neuro-symbolic-ai.md)
  is at 0.6, numbered on its own.

**Dev results and test results.** Most results are on dev data and can be
rerun. A **test** result comes from a single frozen run whose settings were
fixed in advance; that test part is then spent and may not be used to tune
anything. The table marks which is which.

## At a Glance

| Version | Date (2026) | Question | Outcome | Kind |
| --- | --- | --- | --- | --- |
| [0.1](#01-base-protocol-and-development-run) | Aug to Oct | Can typed rules propose the right split, and a small model pick it, with a proof? | The pipeline runs end to end on synthetic data | Smoke run |
| [0.2](#02-right-word-holdout) | 23 Oct | How do we test generalisation when left words are a closed class? | Hold out unseen right-hand words: 9,066 train, 988 dev, 821 test | Design |
| [0.3](#03-silver-dcs-18-rules-and-a-lexical-head) | 23 to 24 Oct | Does the Transformer beat word frequency on unseen words? | No: 0.822 against 0.825 | Test |
| [0.4](#04-external-lexicon) | 24 Oct | Does a dictionary (the Vidyut kosha) close the gap? | Linear model + kosha 0.943; the Transformer falls behind at 0.897 | Test |
| [0.5](#05-self-supervised-pretraining) | 24 Oct to 3 Nov | Can pretraining on Sanskrit text give the model its own lexical knowledge? | On dev, pretrained word scores + kosha reach about 0.95 against 0.903 | Dev |
| [0.6](#06-slp1-inside-the-system) | 30 Oct | Can everything switch to SLP1 internally without changing results? | Yes: same splits, same 0.903 reference | Dev |
| [0.7](#07-rlcd-calibration-constraints-and-a-tagger) | 14 Nov | Does the model know when it is unsure, and can the approach grow to morphology? | Well calibrated; abstaining at 0.95 gives over 99% accuracy on about 80% of items | Dev |
| [0.8](#08-frozen-test-of-the-morphological-tagger) | 14 Nov | Do the stage 3 tagger findings hold on unseen texts? | Pretraining helps (+0.061); beating the kosha does not hold | Test |
| [0.9](#09-frozen-test-of-sandhi-pretraining) | 14 to 23 Nov | Do the pretraining findings hold on the sandhi test set? | Neural + kosha helps (+0.018); neural alone does not replace the kosha | Test |
| [0.10](#010-community-review-pilot) | 23 Nov to 1 Dec | Can a wider group of readers check data reliably? | Round open until 1 December 2026, 23:59 UTC | Pilot |

## 0.1 Base Protocol and Development Run

- **Question.** Can a typed rule engine always include the right external
  vowel-sandhi split among its candidates, and can a tiny Transformer rank
  them better than symbolic and frequency baselines, with a proof trace?
  ([protocol](EXPERIMENT_PROTOCOL.md), research questions RQ1 to RQ5.)
- **Built.** The building blocks everything else stands on:
  - typed sandhi rules (`src/panini/rules.py`) and the single-step candidate
    generator with forward proofs (`candidates.py`);
  - a safe DCS archive decoder (`dcs.py`);
  - data admission and holdout splits (`experiment_data.py`, `splits.py`);
  - baselines and the byte Transformer ranker (`ranking.py`);
  - the review worksheet (`src/review/worksheet.html`).
- **Data.** Draft rules in `data/rules/`, the all-sandhi sūtra source corpus
  in `data/sources/`, and the DCS archive conversion (441,722 of 441,735
  records converted, 13 quarantined).
- **Results.** [reports/development-v1](../reports/development-v1/SUMMARY.md).
  On synthetic data only, the tiny ranker (128,769 parameters, CPU) scored
  0.669 against 0.611 for frequency, with full candidate recall. This shows
  that the pipeline works, not that it reads Sanskrit.
- **Dates.** The protocol was written on 13 August; the run was in
  September; code and report were committed on 23 October.
- **Next.** Real data: silver split examples extracted from DCS without
  consulting the rules.

## 0.2 Right-Word Holdout

- **Question.** In the silver data, left words are a small closed class
  (mostly indeclinables such as *ca*), so a holdout over both words left
  almost nothing to test. How can generalisation be tested fairly?
- **Decision.** Hold out unseen **right-hand** words only
  ([protocol §9.5](EXPERIMENT_PROTOCOL.md#95-right-word-holdout-amendment-02)).
  Under the old holdout, 96% of examples became mixed and test kept 36
  examples; the new one gives 9,066 train, 988 dev and 821 test examples.
- **Note.** A single timing run touched these 821 test items; its scores
  were declared not results, but it counts as the first of four uses.
- **Next.** Inflected left words (phase 2) are still to come; the
  [gold-set plan](GOLD_SET_PLAN.md) aims at them.

## 0.3 Silver DCS: 18 Rules and a Lexical Head

- **Question.** With six more vowel rules (18 in all) and a lexical feature
  head, does the Transformer beat word frequency on unseen right words?
- **Built.** Rules SDH-013 to SDH-018, the `--lexical` head, and paired
  significance tests (`scripts/compare_paired.py`). Rule coverage rose from
  68.1% to 99.97% of tokens.
- **Results (test, five seeds).**
  [reports/dcs-silver-v2](../reports/dcs-silver-v2/SUMMARY.md): Transformer
  + lexical head 0.822 ± 0.010 against frequency with a short-vowel
  tie-break 0.825; paired difference −0.002 [−0.013, +0.009]. No neural
  variant differed measurably from the baseline.
- **Next.** Give the ranker a dictionary.

## 0.4 External Lexicon

- **Question.** With the Vidyut kosha as a feature, does the Transformer (or
  a residual Transformer) beat a linear model with the same kosha feature?
- **Built.** Kosha lookup (`src/panini/lexicon.py`,
  `scripts/fetch_vidyut_data.py`, `scripts/annotate_lexicon.py`), a
  boundary-vowel feature and the residual variant.
- **Results (test, five seeds).**
  [reports/dcs-silver-v3](../reports/dcs-silver-v3/SUMMARY.md): linear +
  kosha **0.943**; Transformer 0.897 ± 0.017 (−0.046); residual 0.943,
  no difference. The simple model with a dictionary wins.
- **Licence.** The kosha includes CC BY-NC-SA material; it is a local
  research dependency, never committed (see `THIRD_PARTY_NOTICES.md`).
- **Next.** The Transformer lacks lexical knowledge, so teach it Sanskrit
  first.

## 0.5 Self-Supervised Pretraining

- **Question.** Can a byte encoder pretrained on decontaminated Sanskrit text
  stand in for the kosha (H-P1), add to it (H-P2), or as a fine-tuned ranker
  beat linear + kosha (H-P3)?
  ([plan](PRETRAINING_PLAN.md), [protocol §11.3](EXPERIMENT_PROTOCOL.md#113-self-supervised-pretraining-amendment-05).)
- **Built.** Pretraining corpora P-A and P-B with a contamination audit,
  span-masking and near-miss pretraining (`src/panini/pretraining.py`,
  `scripts/pretrain.py`), and pretrained word scores for the ranker
  (`scripts/annotate_neural_lexicon.py`). The encoder has 4.94M parameters.
- **Texts.** The encoder read DCS_pick: about 439,000 sentences from 236
  texts, led by the Mahābhārata (29%) and Rāmāyaṇa (9%), then purāṇas,
  āyurveda and rasaśāstra works. See
  [CORPUS_TEXTS.md](../reports/pretraining-v1/CORPUS_TEXTS.md) for the list.
- **Results (dev).**
  [reports/pretraining-v1/DEV_RESULTS.md](../reports/pretraining-v1/DEV_RESULTS.md):
  against the kosha reference of 0.903, pretrained scores alone reach 0.925
  to 0.929 and with the kosha 0.950 to 0.956 (three seeds). Fine-tuning the
  pretrained ranker did not help (0.901). An encoder pretrained on the
  stricter corpus, P-B, stayed below the kosha.
- **Order.** The plan was adopted on 24 October, but its runs (2 to 3
  November) came after 0.6, so they are all in SLP1.
- **Next.** A frozen test of these findings (0.9), and calibration (0.7).

## 0.6 SLP1 Inside the System

- **Question.** Can every internal representation switch from IAST to SLP1,
  an ASCII transliteration with one character per sound, without changing
  any split or result?
- **Built.** `src/panini/translit.py`; SLP1 throughout the code, rules and
  review files. IAST (and later Devanagari) is for people only.
- **Results (dev).** In the protocol only
  ([§11.4](EXPERIMENT_PROTOCOL.md#114-slp1-as-the-internal-transliteration-amendment-06)):
  split membership unchanged; linear + kosha 0.903 in both schemes.
- **Side effect.** The 0.9 settings were first frozen with the hashes of the
  old IAST files, fixed by an erratum on 23 November.

## 0.7 RLCD: Calibration, Constraints and a Tagger

RLCD extends the project from choosing a sandhi split to calibrated,
rule-checked decisions about whole words.
([plan](RLCD_TRANSITION_PLAN.md), [protocol §11.5](EXPERIMENT_PROTOCOL.md#115-rlcd-transition-plan-amendment-07).)
All of it is dev work; the plan was adopted on 14 November. Stage 1 ran
before formal adoption, and the protocol says so.

- **Stage 1, calibration.** Is the ranker's confidence trustworthy?
  [reports/rlcd-stage1](../reports/rlcd-stage1/DEV_RESULTS.md): yes, the
  calibration error (ECE) is 0.013 to 0.029. Accepting only answers with
  confidence of at least 0.95 covers 77% to 81% of items at 99.1% to 99.6%
  accuracy. Combining models for routing gained at most 0.007.
  (`src/panini/calibration.py`.)
- **Stage 2, constraints.** A clause schema and a constraint layer that
  checks roots and stems before Vidyut derives forms
  (`src/panini/clause.py`, `derive.py`, `data/rlcd/`,
  `data/schemas/rlcd-clause.schema.json`;
  [constraint review](RLCD_CONSTRAINTS.md)). Main finding: Vidyut enforces
  pada but accepts some invalid analyses, so the constraint layer is needed.
- **Stage 3, a morphological tagger.** Real DCS CoNLL-U data
  ([reports/dcs-conllu](../reports/dcs-conllu/PROFILE.md)) and a five-head
  tagger over the pretrained encoder (`src/panini/tagger.py`). On dev,
  pretraining helped by +0.064, and the tagger beat the kosha baseline
  overall (+0.025), but mostly on one text, the Kathāsaritsāgara. Joint
  calibration with Platt scaling (J4) worked best
  ([reports/rlcd-stage3](../reports/rlcd-stage3/SUMMARY_TAGGER.md)).
- **Next.** Freeze the stage 3 findings and test them once (0.8).

## 0.8 Frozen Test of the Morphological Tagger

- **Question.** On unseen classical DCS chapters (192 chapters, 16,271
  sentences, 25 texts), do the stage 3 findings hold?
  ([amendment](STAGE3_TEST_AMENDMENT.md).)
- **Built.** A hash-checked frozen run, `scripts/run_stage3_test.py`.
- **Results (test, one run; this test part is spent).**
  [reports/rlcd-stage3/test](../reports/rlcd-stage3/test/TEST_RESULTS.md):
  - pretraining helps: **+0.061** [+0.058, +0.064] (supported);
  - the tagger beats the kosha baseline: +0.018 [−0.005, +0.040] (**not**
    supported);
  - J4 calibration and the abstention gate transfer: supported (gate
    coverage 0.884 to 0.886).
- **Next.** The paper (manuscript 0.5), and the matching frozen test for
  sandhi pretraining.

## 0.9 Frozen Test of Sandhi Pretraining

- **Question.** On the 821 right-word test items, does the neural word score
  replace the kosha (T-P1), add to it (T-P2), and does the 0.95 gate hold
  (T-P3)? ([amendment](SANDHI_PRETRAINING_TEST_AMENDMENT.md), with its
  erratum.)
- **Built.** A hash-checked frozen run,
  `scripts/run_sandhi_pretraining_test.py`.
- **Results (test, one run; the fourth and last use of these items).**
  [reports/pretraining-v1/test](../reports/pretraining-v1/test/TEST_RESULTS.md):
  - neural score alone replacing the kosha: −0.013 [−0.033, +0.006] (**not**
    supported);
  - neural score + kosha: **+0.018** [+0.004, +0.033] (supported; 0.956 to
    0.966 against 0.942);
  - the gate: supported (coverage 0.762 to 0.788).
- **Next.** The paper (manuscript 0.6). The bottleneck is now reviewed data,
  which leads to 0.10.

## 0.10 Community Review Pilot

- **Question.** Can a wider group of readers check silver splits reliably
  enough to justify building a hosted review app?
  ([design](REVIEW_APP_DESIGN.md), [pilot guide](../data/reviews/pilot/README.md).)
- **Built.**
  - **Worksheet.** A Devanagari worksheet with input in Devanagari or IAST,
    stored as SLP1 (`src/review/verify.html`).
  - **Items.** 60 training items, 12 of them hidden controls with known
    answers (`scripts/build_pilot_set.py`).
  - **Scoring.** Weighted votes and a leaderboard
    (`scripts/score_pilot.py`).
  - **The round.** A one-week round with sealed hand-ins and automatic
    scoring (`scripts/pilot_round.py`, `.github/workflows/pilot-*.yml`),
    hosted at https://raghav-vk.github.io/panini-neuro-symbolic-ai/
- **Criteria, fixed before any answers.** At least 5 hand-ins; at least 80%
  of reviewers answer every item; median control accuracy of at least 85%;
  agreement (Gwet's AC1) of at least 0.60. If all four hold, build the
  hosted app.
- **Results.** Due after the round closes on 1 December 2026, 23:59 UTC, in
  `reports/review-pilot/pilot-1/` (written automatically).
