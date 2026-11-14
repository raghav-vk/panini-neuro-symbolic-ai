# Plan: Review of the RLCD Architecture and a Staged Transition

**Status:** Adopted as amendment 0.7 of `docs/EXPERIMENT_PROTOCOL.md`
(section 11.5) on 2026-11-14. No test set has been used. Stage 1 was
pre-registered and run on dev the same day, before formal adoption; protocol
section 11.5 discloses this.

**Documents reviewed:**

- `docs/architecture/unified_neuro_symbolic_architecture_specification.md`
  (commit 4746652)
- `docs/architecture/rlcd_decision_schema_specification.md` (commit b39e387)
- `docs/dataset-generation-pipeline.md` (commit 8e15cec)
- `docs/dataset-structure.json` (commit 3a78548)
- `scripts/eval_calibration.py` (now `scripts/simulate_calibration.py`), its JSON and
  plots (commits 7c3602b and 3a78548), renamed `*_simulated.*` in stage 0

## In Plain Terms

The new design has three parts. A small neural encoder reads a sentence. A
set of decision heads picks grammatical parameters (voice, tense, root, roles,
number) with probabilities that should match how often they are right. The
Vidyut engine then derives the Sanskrit forms by rule. When the heads are
unsure, several analyses are derived and checked.

**The goal.** Build a high-fidelity model that reaches high accuracy with far
fewer parameters and far less GPU than a large language model, by letting
rules do what rules can do and a small calibrated network decide the rest.
RLCD, adopted from Jev (Guo et al., arXiv:2609.29429), is the decision part. Sandhi splitting is
the first tangible demonstration for the paper, not the limit of the project.

The direction fits that goal and the long-term Sanskrit core with language
interfaces. But the documents state several things as results or
guarantees that the repository does not support:

1. **The calibration figures come from made-up data.** The evaluation script
   does not run the model.
2. **Vidyut does not reject invalid input.** It derives forms from invented
   roots and impossible parameter combinations, so "it compiled" does not
   mean "it is valid".
3. **The encoder has never seen English.** It was pretrained on SLP1
   Sanskrit only, so the English-to-Sanskrit path gets nothing from it.

This plan records those findings and proposes a staged path. The paper's
evidence comes from sandhi splitting. RLCD enters first as honest calibration
and abstention on that task, then as Sanskrit-side analysis, and English comes
last. Every stage reports parameters and compute next to accuracy, since
efficiency is the claim the project is ultimately after.

## 1. Critical Findings

### 1.1 The calibration results are simulated

`scripts/eval_calibration.py` imports torch but never loads a checkpoint. In
`reconstruct_dev_distribution_from_seed11` it takes the seed 11 dev counts
from `reports/pretraining-v1/pretrain_S_PA_seed11.json`:

- 1,576 of 1,583 attested words correct
- 247 of 271 altered words correct

It then **invents a score for every word** from hand-chosen normal and uniform
distributions that reproduce those counts. In `main`, it stretches them with
`logits * 1.45 + 0.35` to create overconfidence, and then "calibrates" the
result. Every number in `calibration_eval_seed11.json` follows from those
choices, not from the model:

- the "uncalibrated" ECE 0.013 and Brier 0.017
- the "calibrated" ECE 0.009 and Brier 0.016
- the temperature 0.675 and bias -0.15
- all reliability bins

The file is labelled `"mode": "seed11_history_verified"`, which reads as a
measured result.

Two further defects would remain even with real scores:

- **The fallback is an oracle.** `evaluate_hybrid_routing` replaces every
  routed prediction with the true label
  (`np.where(symbolic_mask, labels, preds)`). The reported hybrid balanced
  accuracies (0.965 at τ = 0.85 and 0.978 at τ = 0.95) assume Vidyut is always
  right. Vidyut has no word-validity judgement to fall back on in this task.
- **Calibration is fitted and scored on the same 1,854 words.**

Affected artifacts (original names; all renamed `*_simulated.*` in stage 0):

- `reports/pretraining-v1/calibration_eval_seed11.json`
- `reports/pretraining-v1/calibration_plots.pdf` and `.png`
- `docs/paper/artifacts/calibration_plots.pdf` (a different rendering, 25 KB
  against 28.7 KB)

Panel (b) of the figure plots the real training history and is fine on its
own. Panels (a) and (c) must not appear in the paper. The protocol (section
8.4) says never to describe generated material as attested.

### 1.2 Vidyut derives forms without checking them

Checked on 2026-11-14 with `vidyut==0.4.0` in the project `.venv`:

| Input | Vidyut output | Problem |
| --- | --- | --- |
| Invented root `Darba~`, bhvādi, laṭ, prathama, dvi | `DarbataH` | No such root |
| Invented root `kuwapa~` | `kuwapataH` | No such root |
| `ga\mx~` declared as curādi | `gAmayete`, `gAmayataH` | Wrong gaṇa accepted |
| `qula\Ba~\z` (ātmanepada) in parasmaipada | nothing | Rejected by Vidyut (checked in stage 2) |
| `ga\mx~`, bhāve, dvivacana | `gamyete` | Bhāve takes only the singular |
| `gamx~` (anudātta marker missing) | `gamataH` | Silent wrong form; only `ga\mx~` gives `gacCataH` |
| Invented stem `xyzab`, puṃliṅga, tṛtīyā | a declined form | No such stem |

`Vyakarana.derive` applies rules to whatever it is given. The pipeline's
claim that a failed compilation catches a hallucinated root or an illegal pada,
"guaranteeing zero morphological hallucinations", is false as written.

Validity needs a separate constraint layer:

- the root and gaṇa must exist in the Dhātupāṭha (`dhatupatha.tsv` in the
  Vidyut data)
- pada (parasmaipada or ātmanepada) must be allowed for the root
- transitivity must fit the voice: karmaṇi needs a transitive root, bhāve an
  intransitive one, and bhāve takes only the singular
- the stem must be in the kosha with the stated gender
- every generated form must round-trip: analysing it with the kosha must
  return the input parameters

### 1.3 Compiling proves form, not meaning

Even with the constraint layer, a compiled AST only shows that the parameters
produce a well-formed word. It does not show that they match the English
sentence. In Tier 3 (LLM labelling) the main error is semantic: a wrong role,
root or tense. Vidyut cannot detect it. Silver data will carry label noise of
unknown size until a human-checked sample measures it.

## 2. Architecture Gaps

**English input.** The S-PA encoder was pretrained on 439,274 SLP1 Sanskrit
sentences. Path A (English to Sanskrit) feeds it English bytes it has never
seen, so the pretrained trunk adds nothing there. Reading English needs either
bilingual pretraining or a separate English encoder. That is a design
decision for stage 4, not a detail.

**The audit head was trained for another task.** The discriminator learned
one thing: whether a single word has had a vowel length swapped (a/A, i/I,
u/U, e/E, o/O) in its sentence. The Path B example's error in `rAmeRa vanaM
gacCati` is agreement between words. `rAmeRa` is a valid word. The example's
p_valid of 0.14 is not something the current head could produce; it is
illustrative only. Agreement checking needs its own objective and data.

**The name and the method must match.** RLCD (reinforcement learning for
calibrated decisions) is kept as the project's name for the approach, adopted
from Jev (section 2.1). But the specifications describe only supervised training: fixed
labels and a Brier loss, with no sampled actions, no reward and no
environment. A reviewer will read "reinforcement learning", look for it, and
not find it. Section 4.1 makes the RL part real. Also:

- The ECE term assigns bins with a hard threshold, so no gradient flows
  through bin membership.
- Adding ECE to the Brier loss makes the loss no longer strictly proper.
- Temperature scaling on held-out dev data is the standard and simpler way to
  calibrate after training.

**The confidence gate is undefined for an AST.** τ = 0.85 is applied to one
head's probability, but the gate routes whole analyses. Multiplying head
probabilities assumes independence, and prayoga, vibhakti and vacana are
tightly coupled. Enumerating top-K ASTs over up to 255 roots, 255 stems per
slot and nine roles grows combinatorially. The gate needs a defined joint
score and a search bound.

**No span extraction.** The heads take noun-phrase spans ("The two boys") as
given. Nothing in the design finds them. The reference code also mean-pools
the whole sentence into one vector, which cannot carry several entities.

**Schema coverage is narrow:**

- one finite verb per sentence
- no avyayas, samāsa, kṛdantas (participles, absolutives, infinitives),
  taddhitas, negation or questions
- `upapada_nimitta` and `sambanDa_zazWI` are listed as kāraka options but are
  not kārakas
- the walkthrough uses `kriyAviSezaRa` for "happily", which is not among the
  options

**Unmeasured numbers are stated as facts:**

- latencies of 1.8, 2.1, 3.4, 0.8 and 0.5 ms and ~36 MB RAM (section 7 of the
  unified specification)
- `"calibration_ece_estimate": 0.014` and all probabilities in the traces
- "confirms the 4.94M backbone encodes deep Paninian structural awareness"
  (the discriminator covers vowel-length swaps only)

**Internal inconsistencies:**

- `docs/dataset-structure.json` uses `lat` and `dvi`; the schema uses `laW`
  and `dvivacana`. It omits `linga` for `jala`.
- The specifications refer to `docs/UNIFIED_NEURO_SYMBOLIC_DESIGN.md` and
  `docs/RLCD_DECISION_SCHEMA.md`, which do not exist.
- The schema writes roots as `gam\l~`; Vidyut 0.4.0 rejects that string and
  expects `ga\mx~`.

### 2.1 What Jev Actually Specifies

Checked on 2026-11-14 against Guo et al., *Just Ask Jev: Reinforcement
Learning for Calibrated Decisions as a Zero-Shot Detector of AI Alignment
Failures*, arXiv:2609.29429 (24 Sep 2026), and the vendor documentation it
cites (TypeSafe AI, https://docs.typesafe.ai).

- **Jev is TypeSafe AI's model, and its training is not published.** The
  paper and the documentation describe how Jev is queried and evaluated. They
  give no model size, RL algorithm, reward or training data. Whether the
  weights are open, and under what licence, is not stated. So the project can
  adopt Jev's **interface and evaluation**, but the training method is ours to
  design, state and defend.
- **The primitives in this repository's schema differ from Jev's:**

  | Primitive | Jev | `rlcd_decision_schema_specification.md` |
  | --- | --- | --- |
  | Noul | A yes/no question; returns P(yes) | "Null / Abstain" weight for an absent slot |
  | Choice | A distribution over listed options, the argmax and a confidence | Same idea, plus "Plackett–Luce" and "max 255", which Jev does not state |
  | Score | A distribution over ordered levels 0 to K−1 and the expected level | A continuous score in [0, 1] |

  Noul is the serious mismatch: it is a truth question, not an abstention.
  Abstention for an absent slot is better written as a Choice option
  (`NONE`), and a Noul can ask questions such as "Is this split licensed by
  6.1.101?".
- **Jev's calibration measure is ECE with reliability curves.** The paper
  reports a pooled ECE of 0.047. Brier appears only in its related work, so
  the Brier + ECE training loss in the specifications is this project's
  choice, not Jev's.
- **One call answers many questions in parallel.** "All questions see the
  same state, are answered independently, and share one call"; the paper
  reports 11.4 questions per call on average. This matches the
  specification's single-pass design. Answered independently, the questions
  also leave the joint-AST gap above open.
- **The acronym is already taken.** The paper itself notes that RLCD also
  stands for reinforcement learning from contrastive distillation (Yang et
  al., 2024). The paper here should define the term on first use and cite
  both.
- **Jev is a hosted, general-purpose judge.** Its reported advantage is cost:
  63 times cheaper than LLM-judge scorers. This project's claim is different:
  a small model with a rule engine for one language. The paper should present
  Jev as the inspiration for the interface, not as evidence for that claim.

## 3. Dataset Pipeline Gaps

**Tier 1 (reverse synthetic generation):**

- Uniform sampling gives grammatical nonsense ("the stone drinks the moon").
  Roles need selectional constraints, such as an animate agent for *pā*.
- The five English paraphrases of one AST must stay in one split.
- Lexical holdouts (unseen roots and stems) are needed, in the spirit of
  protocol section 9.3.
- Generated data is synthetic. It is not gold even when a human translates
  the English, because the Sanskrit side was never attested.

**Tier 2 (mining aligned corpora):**

- DCS tags lemma, case, number, gender, tense, mood and person. It does not
  tag kāraka or prayoga. Case does not map one-to-one onto role: tṛtīyā can be
  the agent of a passive, an instrument, or the companion after *saha*.
- Vidyut returns no confidence score, so "filter where Vidyut returns a
  confidence score below its deterministic threshold" cannot be implemented.
- Classical English translations are free and not sentence-aligned, so one
  AST per English sentence is often wrong.
- DCS-derived text overlaps P-A, P-B, the right-word holdout and the
  held-out chapters planned in `docs/GOLD_SET_PLAN.md`. The same leakage audit
  applies.

**Tier 3 (LLM schema distillation):** see section 1.3. OpenOrca and UltraChat
contain model outputs, and GPT-4o and other commercial models have terms on
using outputs to train models. Check these before releasing an Apache 2.0
dataset.

**Licences to verify:**

- Mitrasaṃgraha and Itihasa: not yet checked.
- Vidyut's `prakriya/README.md` says the ashtadhyayi.com files were shared
  "under an MIT license". That differs from the 2024-02-18 written reply to
  the project ("Commercial use of the dataset is not allowed"). Ask the
  ashtadhyayi.com maintainer to clarify which terms apply to the copies in
  the Vidyut data. This plan offers no legal opinion.

**Volumes.** The pipeline targets 50,000 to 100,000 gold pairs and a
5,000-pair gold test set. Two expert reviewers are available. The gold-set
plan works with a few hundred items. Gold targets must be sized to reviewer
time.

## 4. Staged Transition

The paper's validated result is sandhi-split ranking: P-A neural plus the
kosha reaches a dev top-1 of about 0.95 against 0.909 for the kosha alone
(`reports/pretraining-v1/DEV_RESULTS.md`). Each stage below is decided on dev
and recorded before it runs. Only stage 1 is in scope for the current paper;
stages 2 to 4 work towards the larger goal.

### 4.1 Where Reinforcement Learning Enters

RL earns its place where there is a decision with a cost, or where a reward
can be computed but no label exists. Both occur in this design:

- **The gate is a decision with a cost.** For each item the model either
  commits to its answer or routes it to the slower symbolic search or
  fallback. The reward is +1 for a correct final answer, minus a cost for
  every routed item. This is a contextual bandit, and it can be run on the
  sandhi task now (stage 1). It ties calibration directly to the efficiency
  goal: a well-calibrated score routes only the items that need it.
- **Vidyut can score answers that have no label.** For unlabelled Sanskrit
  (stage 3) or English (stage 4), sample an analysis from the heads, derive it
  with Vidyut, and reward it when it passes the constraint layer and its
  derived surface matches the input. Policy-gradient fine-tuning (REINFORCE
  with a baseline) on this reward needs no annotation.
- **Calibration enters the reward.** The stated confidence is rewarded with a
  proper scoring rule (negative Brier), so the policy is paid for being right
  about how often it is right, not only for being right.

Supervised Brier training and temperature scaling remain the first step: they
give the policy a calibrated start. The paper must describe which parts of
RLCD it actually ran. If stage 1 runs only the supervised part and the
bandit gate, it says exactly that.

Cite Jev as Guo et al. (2026), arXiv:2609.29429, and TypeSafe AI's
documentation. Because Jev's training is not published (section 2.1), the
paper describes this project's RLCD training in full. Related work should also cover calibration-reward
RL for language models, such as RLCR (Reinforcement Learning with Calibration
Rewards, 2025), to show how this work differs.

### Stage 0: Clean up (before anything else)

1. **Done 2026-11-14.** Simulated artifacts renamed, not deleted:
   - `scripts/eval_calibration.py` → `scripts/simulate_calibration.py`, with a
     docstring saying what it simulates; its outputs now carry `_simulated`
     and the `mode` field reads `simulated_from_seed11_counts`
   - `reports/pretraining-v1/calibration_eval_seed11_simulated.json` and
     `calibration_plots_simulated.{pdf,png}`
   - `docs/paper/artifacts/calibration_plots_simulated.{pdf,png}` (the PNG was
     `Code_Generated_Image.png`, the same simulated figure)

   The name `scripts/eval_calibration.py` is reserved for the stage 1
   evaluator that runs the model. Note that `matplotlib` is not in the
   requirements files.
2. **Done 2026-11-14.** Latency, memory and probability figures in both
   architecture specifications are marked illustrative or targets.
3. **Done 2026-11-14.** File paths, root spellings (checked against
   `dhatupatha.tsv`: `ga\mx~`, `i\R`, `yA\`, `paWa~`, `pA\`) and field
   names agree across the specifications, the pipeline and
   `dataset-structure.json`. The example record derives in Vidyut 0.4.0 as
   `aSvO`, `jalam` (`jalaM` by sandhi) and `pibataH`.
4. **Done 2026-11-14.** Both architecture specifications and the pipeline
   carry a status note: draft design, not adopted, no results, with pointers
   to this plan. They also now cite Jev (arXiv:2609.29429), use Jev's
   primitive definitions (Noul as a yes/no question; `NONE` for an absent
   slot), and drop the claims that a Vidyut compile guarantees validity.

The design gaps (constraint layer, joint AST confidence, span extraction,
schema coverage, English encoder) are left to stages 2 to 4.

### Stage 1: Calibration and abstention on the sandhi task (current paper)

This tests the "Score" primitive and the confidence gate on data the project
already has.

1. Write a real evaluator that loads `runs/pretrain-S-PA-seed{7,11,19}` and
   dumps per-word discriminator logits on dev. Do the same for the H-P2 ranker
   scores per candidate.
2. Split dev into a calibration half and an evaluation half by source
   sentence. Fit temperature (and optionally a bias) on the first half only.
3. Report ECE, Brier and reliability diagrams on the second half, with bin
   counts and bootstrap intervals.
4. Report a coverage–accuracy curve. Abstained items go to a **real**
   fallback: the kosha-only ranker or the linear ranker. Never the true label.
5. Pre-register the thresholds compared (for example τ = 0.85 and 0.95) before
   running.
6. Learn the gate as a cost-aware bandit (section 4.1) and compare it with
   the fixed thresholds at equal routing rates.
7. Report parameters, wall-clock time and the routed fraction with every
   accuracy figure, measured on the project Mac.

Protocol section 14.2 already requires coverage and abstention to be reported
with accuracy, so this extends the existing design rather than adding a new
claim.

**Result (dev, 2026-11-14):** `reports/rlcd-stage1/DEV_RESULTS.md`.
- The ranker and the discriminator are already calibrated (ECE about 0.01 to
  0.03 and 0.001 to 0.003), and temperature scaling adds nothing.
- Abstaining on the least confident fifth of items gives more than 99%
  accuracy on the rest.
- Routing to the three-seed ensemble gains at most 0.007, inside the
  intervals.

#### Stage 1 Pre-Registered Settings

Recorded 2026-11-14 and committed before any stage 1 analysis was run. Dev
only; no test set is read. The settings below replace steps 1 to 7 where they
are more specific.

**Disclosure.** Before writing these settings, the saved dev predictions were
checked for alignment. That check showed per-seed accuracy (already
reported), error counts (49, 47, 43) and the mean raw confidence (0.935,
0.943, 0.935). No calibration, binning or gate was computed.

**Systems.**

- **R, the sandhi ranker.** H-P2 linear ranker
  (`linear_features_short_vowel`, kosha plus neural score, words scored
  alone), one per P-A encoder seed. The inputs are the saved dev predictions:
  - seed 7: `runs/final-nc-hp2/`
  - seeds 11 and 19: `runs/eval-pretrain-S-PA-seed{11,19}-nc-hp2/`

  All three runs score the same 988 examples, in the same order and with the
  same candidates. The one example whose gold split is not among the
  candidates counts as an error throughout.
- **E, the slow path.** An ensemble of the three R rankers: the mean of their
  temperature-scaled candidate probabilities. It costs three encoder passes
  instead of one.
- **N, the discriminator as a Noul** ("Is this word attested?"). P(attested)
  is the sigmoid of minus the word logit. It is computed per word on the 984
  dev sentences, with the fixed corruption that `pretraining.evaluate` uses
  (seed 0, same random stream), for the final checkpoints
  `runs/pretrain-S-PA-seed{7,11,19}/encoder.pt`.
  - **Reproduction check:** per seed, the word counts (1,583 attested, 271
    altered) and both accuracies must equal the final dev record in
    `reports/pretraining-v1/pretrain_S_PA_seed*.json`. If they do not, the
    evaluator is wrong and N is not reported.

**Confidence.** For R and E, the probability of the top-ranked candidate under
a softmax over the candidate scores. For N, the probability of the predicted
label, max(p, 1 − p).

**Calibration.** Temperature scaling only: one parameter per system and seed,
fitted by minimising negative log-likelihood. The fitting uses **2-fold
cross-fitting**:

- Folds are assigned by SHA-256 of `rlcd-stage1:` plus the source group (R
  and E) or the sentence index (N).
- The temperature is fitted on one fold and applied to the other, in both
  directions.
- All results pool the out-of-fold predictions.

**Calibration metrics.**

- Top-label ECE, with 10 equal-mass bins as primary and 10 equal-width bins
  as secondary.
- Top-label Brier: the mean of (confidence − correct)².
- NLL of correctness.
- Reliability bins, with counts.
- 95% intervals from 1,000 bootstrap resamples of source groups (R, E) or
  sentences (N), seed 1729.

Every metric is reported before and after temperature scaling.

**Gates (R as the fast path).** Each gate is reported per seed and as the
mean over seeds:

1. **Abstention.**
   - A risk–coverage curve and its area (AURC).
   - Accuracy of the accepted items at 90% and 95% coverage.
   - Coverage and accepted accuracy at τ = 0.85 and τ = 0.95, on calibrated
     confidence.
2. **Routing to E.** Final accuracy and the routed fraction at τ = 0.85 and
   0.95. Two references: R on every item, and E on every item.
3. **Cost-aware gate.** The reward per item is 1 if the final answer is
   correct, minus c if the item was routed to E, for c ∈ {0.01, 0.02,
   0.05}.
   - The policy is a single threshold τ, chosen on one fold to maximise mean
     reward and scored on the other, in both directions.
   - It is compared with the fixed thresholds at the same routed fraction.
   - Both outcomes are known for every logged item, so this is an offline
     contextual bandit with full-information feedback. That is the honest
     description, and it is what the paper will say.

**Compute.** Parameters (4,937,220 per encoder) and passes per item (1 for R,
3 for E). Wall-clock time to score all 988 dev rows with one encoder,
measured on the project Mac with MPS and CPU, 3 repetitions.

**Claims.** Stage 1 results are dev results. Using any of them on the test
set needs a later amendment that freezes τ and c and discloses the next test
use.

**Outputs.** `scripts/eval_calibration.py` writes
`reports/rlcd-stage1/calibration.json` and `SUMMARY.md`. Figures wait until
matplotlib is added to the requirements.

### Stage 2: Vidyut wrapper and schema v0.3

0. Write the AST and decision schema as a JSON Schema with shared fixtures
   (section 7), so that a later Rust port is tested against the same contract.
1. Add an AST module for one clause with one finite verb, kartṛ, karman and
   optionally karaṇa or adhikaraṇa. Use Vidyut's own enum names, and write
   roots as their Dhātupāṭha entries (`ga\mx~`).
2. Add the constraint layer of section 1.2.
3. Add tests:
   - round-trip from AST to surface form to kosha analysis
   - the invalid cases in the section 1.2 table must be rejected
4. Ask the grammarian reviewer to check the constraint table (pada,
   transitivity, voice and number limits).

**Progress (2026-11-14).** Items 0 to 3 are done. Item 4 is requested in
`docs/RLCD_CONSTRAINTS.md`.

- **Contract.** `data/schemas/rlcd-clause.schema.json` (v0.3), with 29
  hand-written fixtures in `data/rlcd/clause_fixtures.jsonl` (12 licit, 17
  illicit).
- **Constraint layer.** `src/panini/clause.py`, which is pure. It reads two
  draft tables: `data/rlcd/dhatu_constraints.tsv` (31 roots) and
  `data/rlcd/stem_lexicon.tsv` (39 stems).
- **Compiler.** `src/panini/derive.py` derives each word with Vidyut and keeps
  its sūtra steps, and `tests/test_clause.py` tests it.

Three findings changed the design:

- **Vidyut does enforce pada.** It derives nothing for a pada the root does
  not take, so that check is Vidyut's (`NO_DERIVATION`). Section 1.2's list
  holds otherwise.
- **The kosha cannot decide gender.** It inflects stems in every gender, and
  its stem-level gender list is incomplete. Gender therefore comes from the
  reviewed stem table. As a result, the constraint layer no longer depends on
  the CC BY-NC-SA kosha, which serves only the informational round trip (35 of
  36 fixture forms confirmed).
- **Feminine-suffix stems must be declared.** `Pratipadika.basic("sItA")`
  declines wrongly (`sItAH`); `Pratipadika.nyap` is right. The stem table
  records the kind.

### Stage 3: Sanskrit-side analysis dataset and heads

The encoder knows Sanskrit, so analysis of Sanskrit is where it can help
first.

1. **Tier 1 generator, small and reviewed.** About 30 common roots and 300
   stems with selectional constraints, about 10,000 sentences, labelled
   synthetic. The text reader reviews a sample for naturalness.
2. **DCS morphology.** Map the CoNLL-U fields DCS actually tags: verb lakāra,
   person and number, and noun vibhakti, vacana and liṅga. Use vibhakti, not
   kāraka, as the first target.
3. **Splits.** Keep the P-A and P-B exclusions and the gold-set chapter
   manifest. Hold out roots and stems lexically.
4. **Heads.** Per-word heads for vibhakti, vacana and liṅga, and per-clause
   heads for lakāra, puruṣa, vacana and prayoga, on the S-PA encoder.
5. **Baselines.** Kosha lookup plus majority class. Calibrate as in stage 1.
6. **RL fine-tuning.** Policy-gradient fine-tuning on unlabelled DCS
   sentences with the Vidyut reward of section 4.1. Compare with supervised
   training alone on the same dev set.

**Progress (2026-11-14), step 1.** `scripts/generate_tier1.py` produces
`rlcd-tier1-v0`: 10,000 distinct clauses (28,732 words) from seed 1729. The
output regenerates byte for byte and is not committed. Its manifest is
`reports/rlcd-stage3/tier1_manifest.json`.

- **How it samples.** Participants are drawn to fit each root's role frame
  (`data/rlcd/frames.tsv`, with `data/rlcd/stem_classes.tsv`). Person and
  number follow the agreeing participant. Every clause then goes through the
  stage 2 compiler.
- **Mix.** Kartari 7,558, karmaṇi 1,722, bhāve 720. About 1,000 per lakāra,
  except 912 for luṅ. 255 to 386 per root.
- **Review sample.** 100 sentences, at least one per root, in
  `data/reviews/rlcd_tier1_sample.{md,jsonl}`, for the text reader's
  naturalness check. The frames and classes are draft tables for the text
  reader. The root and stem tables are under review in issue #78.
- **Not for training yet.** The manifest records `for_training: false` while
  any table row is unreviewed (140 rows now).

Two findings came from the kosha round trip during generation:

- **A Vidyut defect.** Vidyut 0.4.0 omits ciṇ (3.1.66) in bhāve luṅ. It gives
  `aBAvizwa` for *aBāvi*, though karmaṇi luṅ is right (`agAmi`). The
  combination is blocked as `ENGINE_DEFECT` (fixture X18), so 67 proposals
  were rejected. This is worth reporting upstream.
- **A kosha gap.** The kosha files the luṅ forms of *kṛ* (`akArzIt`, `akfta`)
  under another `kf\Y` entry, not Tanādi `qukf\Y`. The round trip therefore
  rejects them (48 proposals). The rejection is conservative and false, and is
  kept until the stem and root analysis does not depend on the kosha.

**Next for stage 3.**
- **Step 2: the DCS CoNLL-U is fetched (2026-11-14).** It is at commit
  `8aeed5a`, from `scripts/fetch_dcs_conllu.py`, and is verified against
  `datasets/dcs_conllu_manifest.json`. It holds 271 texts, 770,945 sentences
  and 5.8M words. `reports/dcs-conllu/PROFILE.md` records what it gives.
  - Nominal case, number and gender map directly.
  - `Past` (liṭ or luṅ) and `Fut` (lṛṭ or luṭ) do not map one-to-one onto a
    lakāra.
  - Voice is marked only when passive.
  - Most treebank relations carry no annotator mark, so they are not gold
    roles.

  **Mapping and audit done (2026-11-14).** `scripts/convert_dcs_conllu.py`
  writes SLP1 rows with schema labels (`src/panini/dcs_conllu.py`). Merged
  classes are labelled as such (`Lit|Lun`, `Lrt|Lut`), and no kāraka or
  prayoga is claimed. It also audits every sentence against DCS_pick.
  - 56% of DCS sentences are exact copies of DCS_pick text.
  - Sentences matching held-out sandhi dev or test sentences occur in more
    than 1,000 chapters each.
  - Only 37,837 classical sentences (no Vedic block, time slot other than 1)
    lie in chapters with no overlap at all.

  The gold set and the stage 3 evaluation must divide that pool, as recorded
  in `reports/dcs-conllu/PROFILE.md`. The division is to be decided before
  any of it is read for results.

  **DCS division, approved 2026-11-14 (pre-registered).** No sentence was
  read for results before this was recorded. The division is applied by
  `scripts/split_dcs_conllu.py` and recorded in
  `reports/dcs-conllu/split_manifest.json`.

  - **Definitions.** A chapter is *classical* if it has no `<details>` block
    and its DCS time slot is not 1. It is *clean* if no sentence in it is an
    exact or near copy of DCS_pick text.
  - **Gold-set reserve.** Every chapter of eight whole clean kāvya texts:
    Saundarānanda, Āryāsaptaśatī, Narmamālā, Kokilasaṃdeśa, Bhallaṭaśataka,
    Haṃsasaṃdeśa, Caurapañcaśikā and Mukundamālā. Only the gold set
    (`docs/GOLD_SET_PLAN.md`) may use them. No stage 3 code reads them, and
    they stay out of every future pretraining corpus.
  - **Stage 3 evaluation.** Every other classical clean chapter. Each goes to
    dev or test by SHA-256 of `rlcd-stage3:` plus the chapter ID. Results are
    reported per text as well as pooled, because Kathāsaritsāgara supplies
    most of them. The test part is not read until a frozen amendment.
  - **Stage 3 training.** Every remaining sentence, except any that matches a
    right-word holdout dev or test source sentence. Vedic and non-classical
    sentences stay in the pool with their flags; the training
    pre-registration decides whether to use them.
- **Steps 4 to 6** (heads, baselines, RL fine-tuning) are pre-registered
  before they run, as stage 1 was.

#### Stage 3 Training Pre-Registered Settings (steps 4 and 5)

Recorded 2026-11-14 and committed before any model is trained. Dev only. The
test part of the DCS division stays sealed.

**Disclosure.** Before these settings were written, only the classical
training pool was profiled: sentence and word counts, length percentiles, and
the label distributions per field. No dev or test sentence was read.

**Task.** Morphological tagging of real Sanskrit with the segmentation given.

- **Input.** One DCS sentence as its pada-pāṭha: the word forms DCS gives
  (`form`, mostly reconstructed), in SLP1, joined by single spaces.
- **Output.** Five Choice heads per word. Each has a `NONE` option for
  "not applicable":

  | Head | Options |
  | --- | --- |
  | vibhakti | the 8 cases, `compound_member`, `NONE` |
  | vacana | Eka, Dvi, Bahu, `NONE` |
  | liṅga | Pum, Stri, Napumsaka, `NONE` |
  | puruṣa | Prathama, Madhyama, Uttama, `NONE` |
  | lakāra | Lat, Lan, VidhiLin, Lot, AshirLin, Lrn, `Lit|Lun`, `Lrt|Lut`, `other`, `NONE` |

  Labels come from `src/panini/dcs_conllu.py`; every `other:…` lakāra
  becomes `other`. Segmentation, kāraka and prayoga are not part of this
  task.
- **Length.** A sentence longer than 256 bytes is cut into consecutive
  chunks of whole words of at most 256 bytes, in training and evaluation
  alike. A single word longer than 256 bytes is truncated, and the number of
  such words is reported.

**Data.**

- **Training.** The classical part of the stage 3 training pool: chapters
  with no `<details>` block and time slot other than 1. That is 336,132
  sentences and 2,642,506 words.
- **Evaluation.** Stage 3 dev: 16,340 sentences in 197 chapters.
- **Excluded.** Vedic and time-slot-1 sentences, the Tier 1 synthetic data
  (its tables are unreviewed, issue #78) and the gold reserve. A later
  pre-registration may add the first two as separate arms.

**Systems.**

| ID | System | Runs |
| --- | --- | --- |
| B0 | Majority value per head, from training | 1 |
| B1 | Form lookup: the most frequent full tag of the exact form in training; otherwise B0 | 1 |
| B2 | Kosha + prior: B1 if the form was seen in training; otherwise the kosha analyses of the form (pausal variants), choosing the tag most frequent in training; otherwise B0 | 1 |
| N1 | S-PA encoder pretrained on P-A, fine-tuned with the five heads, cross-entropy | P-A encoder seeds 7, 11, 19 (each fine-tuned with the same seed) |
| N2 | The same architecture from random initialisation, cross-entropy | seeds 7, 11, 19 |
| N3 | As N1, with the sum of the five multi-class Brier scores as the loss | seeds 7, 11, 19 |

**Neural settings, fixed for N1 to N3.**

- **Model.** Encoder size S (width 256, 6 layers, 8 heads, 256 positions).
  A word's vector is the mean of its bytes' final hidden states. Each head is
  one linear layer over that vector, and the whole encoder is fine-tuned.
- **Optimiser.** AdamW, learning rate 2e-4, weight decay 0.01, dropout 0.1.
  Batches of 64 chunks in 64-byte length buckets. 500 warm-up steps, then
  cosine decay.
- **Length of training.** Two passes over the classical training pool. The
  final checkpoint is used; no checkpoint or setting is chosen on dev.
- **Device.** MPS on the project Mac.

**Metrics (dev).**

- **Primary.** Full-tag accuracy: the share of words with all five heads
  correct, `NONE` included.
- **Per head.**
  - Accuracy on words whose gold value is not `NONE`.
  - Accuracy of `NONE` predictions.
  - Macro accuracy over values.
- **Subsets.** Words whose form never occurs in training (unseen forms), and
  each dev text separately.
- **Calibration.**
  - Each head gets a temperature, fitted on one half of the dev chapters and
    applied to the other, both ways (2-fold, folds by SHA-256 of
    `rlcd-stage3-cal:` plus the chapter ID).
  - Word confidence is the product of the five calibrated top probabilities.
  - Reported: ECE with 10 equal-mass bins, top-label Brier and NLL, raw and
    calibrated, for N1 to N3.
- **Abstention.** Risk–coverage area (AURC) and full-tag accuracy at 90% and
  95% coverage, on calibrated word confidence.
- **Compute.** Parameters; training time per run; wall-clock time to tag the
  whole dev set on MPS and on CPU (3 runs each).
- **Intervals.** 95% intervals from 1,000 bootstrap resamples of dev
  chapters, seed 1729.

**Hypotheses and decision rules (dev).**

- **H-S3-1. N1 beats B2 on full-tag accuracy.** Supported if every N1 seed
  is above B2, and the 95% chapter-bootstrap interval of the mean paired
  difference over seeds excludes 0.
- **H-S3-2. N1 beats N2** (pretraining helps), by the same rule.
- **H-S3-3. N3 against N1 is descriptive.** Calibration and accuracy are
  compared and no direction is claimed.
- **All results are dev results.** A test run needs a later amendment that
  freezes the system and its settings.

**Outputs.**

- **Code.** `scripts/train_tagger.py` and `scripts/eval_tagger.py`; runs in
  `runs/tagger-<system>-seed<N>/`.
- **Report.** `reports/rlcd-stage3/TAGGER_DEV_RESULTS.md`, with the
  generated tables beside it.

### Stage 4: English interface (later work, separate paper)

1. Decide how the model reads English (section 6).
2. Produce English for Tier 1 ASTs with an LLM whose terms allow it.
3. Add kāraka labels only with a reviewed case-to-role mapping.
4. Add Tier 3 only after a human-checked sample measures its label noise.

## 5. Decisions

Recorded 2026-11-14:

1. **Scope.** The paper rests on sandhi splitting as the tangible
   demonstration. The project goal is larger: high accuracy with fewer
   parameters and less GPU. Stages 2 to 4 continue towards it.
2. **Name.** RLCD (reinforcement learning for calibrated decisions) is kept,
   as adopted from Jev (arXiv:2609.29429). Section 4.1 makes the RL part real, and the paper
   claims only the parts that were run.
3. **Simulated artifacts.** Renamed `*_simulated.*` (stage 0, item 1). The
   paper uses observed artifacts from stage 1.
4. **English encoder.** Deferred until stage 3 is done. The choices are in
   section 6.

Primitive definitions were aligned with Jev's in stage 0. Still open: the
non-kāraka options (`upapada_nimitta`, `sambanDa_zazWI`) in the kāraka Choice,
to be settled in schema v0.3 (stage 2).

## 6. English Encoder Choices (for Stage 4)

The decision heads and Vidyut do not depend on the input language: every
encoder below feeds the same heads and the same AST. That keeps the Sanskrit
core stable, as the project direction requires.

| Option | What it is | For | Against |
| --- | --- | --- | --- |
| A. Bilingual byte encoder | Continue pretraining S-PA on English and SLP1 bytes, plus aligned pairs | One tiny model; no tokenizer; strongest fit with the low-parameter goal | 4.94M parameters may be too few for English meaning; English bytes are long against the 256-byte limit; needs aligned data |
| B. Small pretrained English encoder | A published compact encoder (about 4M to 30M parameters, such as BERT-tiny, ELECTRA-small or MiniLM), frozen or lightly tuned, feeding the same heads | English understanding for free; cheap to try | More parameters; a tokenizer; licence check per model; two encoders to run |
| C. Distil from a large model | A large model labels English with ASTs; a small student encoder learns English to AST directly | Small model at inference; large model used only offline | Teacher label noise; terms of use on model outputs; Vidyut checks form, not meaning |
| D. Indic first | Read Hindi, Marathi and other Devanagari languages with the byte encoder before English | Matches the project's stated order (Indic, then English); shared vocabulary and script with Sanskrit | Needs Indic–Sanskrit aligned data; English waits longer |

Options can be combined. A suggested comparison at the end of stage 3 is B as
the baseline and A as the efficiency experiment, judged by accuracy against
parameters and compute. Option C can supply training data for either. Option
D is a question of order; the project direction puts Indic languages before
English, while the specifications start with English. That conflict should be
settled before stage 4.

## 7. Implementation Languages

Recorded 2026-11-14.

| Part | Language | Why |
| --- | --- | --- |
| Training: heads, Brier loss, RL fine-tuning | Python and PyTorch, permanently | The heads are small layers on the encoder and train with it; autograd, MPS and the pretraining code are Python |
| Calibration fitting and evaluation (`scripts/eval_calibration.py`) | Python, permanently | Research tools over a few thousand items; reviewers must be able to rerun them |
| Constraint layer, gate and branch search | Python in stage 2, then Rust | Deterministic code next to Vidyut, which is Rust; native crates avoid the Python bindings, and branch search is where the cost will be. Port once the rules are settled and reviewed |
| Inference runtime (encoder, heads, gate, Vidyut) | Rust, when a product needs it | Where the low-parameter, low-compute claim becomes a deployment measurement; a 4.94M-parameter encoder can run through ONNX Runtime or candle |

**Not yet.** Interfaces will change through stages 1 to 3, a second toolchain
makes the paper harder to reproduce, and Python overhead is not yet a
measured bottleneck. Profiling decides what is ported first.

**Prepare now, so the port is cheap:**

1. **A shared contract.** The AST and decision schema as a JSON Schema, with
   fixtures that pair each AST with its expected derivation or rejection.
   Both implementations must pass them. Stage 2 delivers it.
2. **A pure constraint layer.** Plain functions with no PyTorch, so that it
   translates almost line for line.
3. **Calibration ships with the model.** The fitted temperature and gate
   threshold are exported with the weights, so a Rust runtime reproduces the
   same probabilities.
4. **Parity tests when porting.** Rust and Python outputs on dev must agree
   within a stated tolerance before the Rust path is used.
