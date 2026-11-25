# Proof-Carrying External Vowel-Sandhi Splitting with Typed Pāṇinian Rules and a Tiny Transformer

**Author:** Raghavendra V. Karnam
**Working manuscript version:** 0.6, November 2026
**Repository:** https://github.com/raghav-vk/panini-neuro-symbolic-ai
**Status:** Runnable development system. The sandhi independent-corpus
evaluation is pending. The pre-registered extension of Section 12 is complete:
one confirmatory test run.

> This version is not ready for arXiv resubmission. It contains:
> - a complete sandhi study design and measured synthetic engineering
>   results;
> - silver-data sandhi results (Section 11: test results for the baseline
>   comparison and for pretraining, plus development results for
>   calibration);
> - the completed Section 12 extension.
>
> It has no expert-reviewed rule inventory, no expert gold test set and no
> expert evaluation yet. Silver results must not be presented as the planned
> independent-corpus study.

## Abstract

Sanskrit word segmentation is difficult because sandhi can alter characters
at word boundaries and can permit multiple analyses of the same surface form.
Purely neural systems can exploit context but may produce analyses unsupported
by the intended grammatical subset; purely symbolic systems can enumerate
licensed candidates but require a method for contextual ranking. This work
studies a deliberately narrow neuro-symbolic architecture for one phenomenon:
external vowel-sandhi splitting under a reviewed inventory of 25 operational
rules. A typed symbolic layer matches boundary conditions, constructs valid
candidate analyses, and attaches a proof trace containing the operational rule
and source sūtra identifiers. A small encoder-only Transformer, targeted at
approximately one million parameters, ranks these candidates from sentence
context. The evaluation is designed to separate candidate coverage from
ranking quality and to distinguish random, unseen-pair, and strict unseen-lemma
generalization. It includes symbolic and neural baselines, data-efficiency
curves, ablations, abstention analysis, resource measurements, and blinded
expert review. A separately versioned source layer inventories 148 sandhi-related
sūtra candidates across two pedagogical classifications, including 108
operative candidates and 40 supporting records; these are an expert review
queue, not automatically executable rules. This manuscript specifies the
system and planned evaluation. An accompanying development implementation
executes 18 narrow draft encodings across five families, converts the DCS
archive without executing pickle objects, and runs a small CPU Transformer
on synthetic nonce-string probes. Those measurements establish engineering
reproducibility, not Sanskrit accuracy; independent-corpus results remain
pending and no claim of general grammatical correctness is made.

On silver boundaries extracted from the DCS, the symbolic layer finds the
correct analysis for 99.9% of unseen right-hand words. On that holdout test,
a linear ranker over training counts and a dictionary reaches 0.943 top-1,
and a tiny Transformer trained from scratch does not improve on it. In one
frozen test run, adding a word score from a Sanskrit-pretrained byte encoder
raises the linear ranker by 0.018, to 0.956–0.966. The ranker's raw
confidence keeps about 78% of test items at 0.995 accuracy. Without the
dictionary, the word score does not match it. Both gains are smaller than on
development data. A separately pre-registered extension (Section 12) tests the same small
encoder on real text, as a set of calibrated Choice decisions: per-word
case, number, gender, person and tense for 133,107 held-out words of the
Digital Corpus of Sanskrit, with the segmentation given. In one frozen test
run:
- pretraining the 4.94M-parameter byte encoder on Sanskrit improves
  whole-tag accuracy by 0.061 over the same model trained from scratch;
- a two-parameter calibration fitted on development data transfers to
  held-out texts;
- a confidence gate chosen for 90% development coverage keeps 88.5% of test
  words at 0.94 whole-tag accuracy.

The tagger does not reliably beat a dictionary-plus-statistics baseline
across texts. It trails it on several prose texts, by up to 0.17.

## 1. Introduction

The Aṣṭādhyāyī provides a compact rule system whose interpretation depends on
technical vocabulary, inherited context, ordering, exceptions, and scholarly
traditions. This structure makes Sanskrit an attractive setting for
neuro-symbolic computation, but it does not make the engineering problem
automatic. A list of sūtras is not a training dataset, and a short table of
character substitutions is not a faithful implementation of Pāṇinian grammar.

Earlier versions of this project proposed a broad Sanskrit language model,
English-to-Sanskrit translation, grammatical correction, literary generation,
and guarantees of perfect output. Those goals were too broad to evaluate in
one paper and were not supported by experiments. The present work replaces
that proposal with a falsifiable question:

> Can a very small contextual model improve the ranking of analyses that are
> explicitly licensed by a typed, expert-reviewed external vowel-sandhi
> subset, especially when test lemmas never occur in training?

External vowel sandhi is narrow enough to encode and audit, yet difficult
enough to expose the central division of labor. Boundary rules determine which
analyses are licensed by the subset. Context and lexical plausibility determine
which licensed analysis is preferred. The proposed system therefore does not
ask a Transformer to learn the rules implicitly or generate arbitrary output.
It asks the Transformer to rank a symbolic candidate set.

The intended contributions are:

1. A reproducible, pinned 148-record source inventory spanning all sandhi
   families, with explicit selection evidence and conservative candidate
   status.
2. A strongly validated JSONL representation for operational external
   vowel-sandhi rules, including source revision, conditions, exceptions,
   precedence, positive examples, counterexamples, and review metadata.
3. A symbolic candidate interface that reconstructs the observed surface and
   emits a compact proof trace for every accepted analysis.
4. A tiny contextual candidate ranker designed for training on minimal
   hardware.
5. A lexical-holdout protocol that partitions lemmas before examples and
   proves that train, development, and test vocabularies are disjoint.
6. An evaluation plan that reports candidate recall, exact analysis, subset
   compliance, abstention, compute, uncertainty, and expert judgments.

The contribution is an experimental system for a bounded rule inventory, not
a complete computational grammar and not a claim that neural-symbolic
composition guarantees Sanskrit correctness in general.

## 2. Related Work

### 2.1 Sanskrit Word Segmentation

Krishna, Satuluri, and Goyal formalized a Sanskrit word-segmentation benchmark
and released 115,000 sentences with ground-truth segmentation and lexical and
morphological candidate information. Their work emphasizes that task
definitions, candidate spaces, and evaluation criteria must be aligned
[Krishna et al., 2017].

Hellwig and Nehrdich modeled Sanskrit word splitting with character-level
recurrent and convolutional networks. Their formulation uses sentence context
to judge semantically plausible splits and demonstrates the value of learned
character representations [Hellwig and Nehrdich, 2018].

TransLIST combines Transformer representations with latent-word information,
soft-masked attention, and post-ranking of candidate paths. It is the closest
architectural comparison because it also combines learned representations with
linguistically informed candidates [Sandhan et al., 2022]. The present study
does not claim novelty merely from using a Transformer and a candidate lattice.
Its empirical distinction must come from hard subset validity, a typed and
reviewed rule interface, proof traces, strict lexical evaluation, and a much
smaller measured parameter and compute budget.

### 2.2 Symbolic Sanskrit Software and Data

The Sanskrit Heritage platform has motivated a line of finite-state,
lexicon-driven candidate generation used by segmentation research. Vidyut is
an open-source Sanskrit software ecosystem that implements a large
Aṣṭādhyāyī-based derivational subset and provides sandhi and segmentation
components. It is a valuable implementation reference and potential baseline,
but agreement with Vidyut alone is not treated as scholarly validation of this
project's operational rules.

The ashtadhyayi-com data repository contains digital material used by
ashtadhyayi.com, including sūtra and commentary data. From pinned commit
`51bff9fb38c6f571b4a2bc8499d97576f00ffcce`, this project deterministically
selects 148 sandhi-related source records using the union of the relevant
Siddhānta Kaumudī and Laghu Siddhānta Kaumudī chapter assignments. It records
the exact file and commit rather than treating the repository as an unversioned
grammar oracle. The repository snapshot contains no license file; its
maintainer permits use in products offered free of charge and forbids
commercial use. Only sūtra identifiers, ancient sūtra text, and factual
classifications are copied; modern commentary is not.

The Digital Corpus of Sanskrit provides morphologically analyzed Sanskrit
material. The local legacy archive examined for this project is verified as
the `DCS_pick.zip` artifact in Zenodo record 803508 by filename, byte size, and
MD5, and the record is licensed CC BY 4.0. Its hundreds of thousands of
sentence analyses still require a separate safe parsing and alignment step
before they become external vowel-sandhi examples.

### 2.3 Positioning

The proposed design follows a constrained-ranking view:

- Symbolic knowledge defines a permitted candidate set.
- A neural encoder estimates contextual preference within that set.
- A trace records why a candidate was admitted.
- Abstention handles insufficient symbolic coverage or low ranking confidence.

The study's scientific value depends on demonstrating measurable advantages
under controlled baselines and leakage-resistant evaluation. Architecture
description alone is insufficient.

## 3. Scope and Claims

### 3.1 Included

- External sandhi at a single vowel boundary.
- A target inventory of 25 expert-reviewed operational rules.
- One frozen internal transliteration.
- Candidate generation and contextual ranking.
- Random, exact-pair, strict lexical, and optional source holdouts.
- Proof traces relative to the encoded subset.

### 3.2 Excluded

- Internal sandhi and compound segmentation unless explicitly added before the
  protocol freeze.
- Executable consonant, visarga, and nasal/anusvāra rules outside the reviewed
  pilot inventory. Their sūtra candidates remain available in the broader
  source layer for staged expansion.
- Full sentence segmentation as the primary task.
- Morphological generation, kāraka analysis, translation, correction, and
  literary generation. Morphological tagging appears only in the separately
  pre-registered extension of Section 12, which is evaluated on its own
  terms and does not change the claims of the sandhi study.
- Vedic-only rules unless declared as a separate evaluation stratum.
- Claims of complete Pāṇinian or semantic correctness.

### 3.3 Guarantee Boundary

For a non-abstained output, the system can guarantee only that:

1. An encoded rule matched the supplied boundary and typed tags.
2. No encoded forbidden tag was present.
3. Executing the recorded rewrite reconstructed the observed surface.
4. The proof identifies the operational record and its declared source.

This is subset compliance. It can still be linguistically wrong if the rule
inventory, tags, lexical analysis, source interpretation, or implementation is
wrong or incomplete. Expert evaluation is therefore part of the study rather
than an optional endorsement after it.

## 4. Task Formulation

Let x be an observed surface span, c its sentence context, t a set of typed
grammatical tags, and R the frozen rule inventory. The symbolic component
enumerates:

    C_R(x, t) = {z_1, z_2, ..., z_k}

Each candidate z contains a left form, right form, operational rule, and proof
trace. Every z in the set must reconstruct x under its recorded rewrite.

The neural ranker computes:

    score_theta(c, x, z) in the real numbers

and estimates a distribution over candidates in the same set:

    p_theta(z | c, x, C_R) = softmax(score_theta(c, x, z))

At inference, the model returns the highest-scoring candidate only when its
development-calibrated confidence exceeds threshold tau. Otherwise it
abstains.

Evaluation separates:

- **Candidate recall:** whether the gold z is in C_R.
- **Conditional ranking accuracy:** whether the model ranks gold first when it
  is present.
- **End-to-end accuracy:** whether the final output is exactly correct over all
  examples.
- **Selective performance:** accuracy and error risk as coverage changes with
  tau.

## 5. Typed Rule Representation

Each operational rule has:

- A stable EVS-NNN identifier and scope.
- Draft, self-checked, or expert-reviewed status.
- One or more source sūtra identifiers.
- Source text, URL, immutable commit, and license.
- An explicit operational interpretation.
- Left suffix and right prefix classes.
- Required and forbidden grammatical tags.
- A boundary operation specifying which matches are kept or dropped and what
  string is emitted.
- Precedence and optionality.
- Positive examples, counterexamples, notes, and review metadata.

Unknown fields are rejected. Positive examples execute during loading and fail
validation if their declared surface differs from the rewrite output.
Publication mode rejects draft rules, unresolved licenses, unpinned source
revisions, missing review, and insufficient examples.

The repository retains the illustrative EVS seed and now contains 12 separate
SDH development encodings spanning five families. They have 24 positive string
probes and 32 executable negative checks, but no independent approval. Neither
the drafts nor the source corpus establish the planned 25-rule coverage.

## 6. Symbolic Candidate Layer

### 6.1 Matching

The compiler normalizes input using a frozen versioned transform, checks typed
tags, and finds matching boundary suffixes and prefixes. Longest boundary
strings are matched first within a rule. Rule conflicts are resolved by
explicit precedence rather than source-file order.

### 6.2 Candidate Construction

For each applicable rule, the engine constructs the unsandhied pair, executes
the forward rewrite, and keeps the analysis only if the resulting surface
equals the observation. Optional rules may contribute more than one licensed
candidate.

### 6.3 Proof Trace

Every candidate includes:

- Rule and source sūtra identifiers.
- Input forms and observed tags.
- Matched left and right boundary strings.
- Kept, dropped, and emitted boundary content.
- Reconstructed surface.
- Rule-inventory version.

The trace is intended for reproducibility and expert inspection. It is a
certificate of program execution against a declared subset, not a formal proof
that the grammatical interpretation is universally accepted.

### 6.4 Failure and Abstention

The system abstains when no candidate exists. It may also abstain when:

- The candidate set exceeds a predeclared safety limit.
- Required lexical or grammatical tags are unavailable.
- Multiple top candidates remain below a calibrated margin.
- The best score is below a development-selected threshold.

Failure categories are logged and reported rather than converted to fallback
concatenations or unconstrained neural guesses.

## 7. Neural Candidate Ranker

The initial ranker is a four-layer encoder with hidden width 128, four
attention heads, and feed-forward width 512. The exact parameter count depends
on the frozen input vocabulary and is reported from code. The target is
approximately one million parameters.

Each candidate serialization contains:

- Left sentence context.
- Observed surface.
- Right sentence context.
- Candidate left and right forms.
- Operational rule identifier.
- Typed condition tags.
- Compact proof features.

A learned classification representation is projected to one scalar score.
Scores are normalized only among candidates for the same example. This avoids
asking the model to generate arbitrary transliteration strings and makes every
ranked output inspectable.

The model uses character or byte inputs so rare Sanskrit forms do not become
unknown tokens. The choice, normalization, maximum sequence length, and
truncation policy are frozen before experiments. No pretrained language model
is required for the primary system.

## 8. Data

### 8.1 Grammar Source and Operational Rule Data

The generated all-sandhi source corpus contains 148 unique sūtra candidates
from pinned ashtadhyayi-com commit
`51bff9fb38c6f571b4a2bc8499d97576f00ffcce`. The reproducible inclusion
criterion is the union of records assigned by the source to Siddhānta Kaumudī
chapters 3-7 or Laghu Siddhānta Kaumudī chapters 2-3. Source type codes identify
108 operative candidates and 40 definitions, governing scopes, and
interpretive or transference principles. The artifact SHA-256 is
`6160267d448a6ab589e00f9582ee87ea3bc47fd42fafb37fa9b3a9dfe0f2ebab`.

All 148 records are marked `source_candidate`, require expert review, and have
no linked computational rules. This distinction prevents three unsupported
assumptions: that pedagogical chapter membership proves exhaustiveness, that
every selected sūtra independently performs a rewrite, or that one sūtra maps
to exactly one operational rule.

The 25-rule inventory will be authored from pinned sources and independently
reviewed. Each rule requires multiple positive examples and at least one
counterexample. Controlled examples belong to the symbolic specification and
cannot be introduced after test results are inspected.

### 8.2 Corpus Data

The local DCS_pick ZIP contains 441,735 unique pickle data records and two
ancillary Python files. All 441,735 data records are extracted. A non-executing
audit of 100 sampled pickle streams found the expected legacy DCS constructor
and no additional constructor opcodes. The local ZIP also matches Zenodo record
803508 by filename (`DCS_pick.zip`), byte size (199,818,951), and MD5
(`556395ddc0f087fbf0a199a0581775d0`). Its independently computed SHA-256 is
`7b13cc2fda84318cba23d9c7667cd3ea30600091e446dac43fae86ebe90e4e85`.
Zenodo records a CC BY 4.0 license. These facts establish provenance and local
integrity, not annotation accuracy.

The records include sentence, lemma grouping, chunk, morphology-code, and
sentence-identifier fields. They are sentence analyses rather than directly
labeled instances of this paper's task. The preprocessing pipeline must:

1. Check the local archive against the frozen verified manifest.
2. Parse records without executing untrusted constructors.
3. Preserve original identifiers and source strings.
4. Normalize to the frozen internal transliteration.
5. Identify two-lexeme external vowel boundaries.
6. Align the observed surface with left and right forms.
7. Attach an operational rule and proof.
8. Route ambiguous or unsupported cases to review or rejection.

The 53-example translation toy dataset from the original project is excluded
from all experiments.

### 8.3 Derived Example Schema

Every example stores stable example and source identifiers, context, surface,
left and right forms, left and right lemmas, operational rule, typed tags,
proof, provenance, and annotation status. Original and normalized text are
both retained.

### 8.4 Deduplication

Before splitting, the pipeline removes exact duplicate source spans, identical
surface-analysis triples, repeated ordered lemma-rule triples, and exact
context hashes. Near-duplicate editions are grouped by work or source so they
cannot cross partitions.

## 9. Lexical Holdout

A random split can overestimate performance when frequent forms or exact pairs
occur in both training and test data. The study therefore reports three
primary split families.

### 9.1 Source-Grouped Random

Source sentences, not isolated boundaries, are assigned 80/10/10 to
train/development/test. This is the easiest setting.

### 9.2 Exact-Pair Holdout

The ordered normalized pair of left lemma and right lemma is assigned as one
unit. Test pairs are unseen during training, but each individual lemma may
have appeared with another partner.

### 9.3 Strict Unseen-Lemma Holdout

Distinct normalized lemmas are assigned to partitions before examples.
An example enters train, development, or test only when both lemmas belong to
that partition. Cross-partition examples are retained in a mixed audit file
but are not used in the strict benchmark. The implementation asserts:

    V_train intersect V_dev = empty
    V_train intersect V_test = empty
    V_dev intersect V_test = empty

The split is deterministic from a fixed seed and logs its input hash, lemma
bucket ratios, retained counts, mixed count, rule counts, and overlap checks.
This prevents both exact-pair memorization and reuse of either constituent
lemma from inflating the strict result.

Strict splitting can remove many edges in a densely connected lexical graph.
That is an honest cost of the stronger question. The paper reports the mixed
rate and does not silently search seeds for a favorable test distribution.

## 10. Experimental Design

### 10.1 Baselines

- Majority operational rule.
- Symbolic candidate ranking by precedence and training frequency.
- Character n-gram and lexical-frequency ranker.
- Parameter-matched unconstrained tiny Transformer.
- Constrained candidate ranker without rule or trace features.
- Full typed constrained ranker.

Vidyut and TransLIST are optional external comparisons if their licenses,
input formats, data, and metrics can be aligned. Published results on a
different benchmark are cited as context, not copied into the main comparison
table.

### 10.2 Data Efficiency

Train learned systems on 250, 1,000, 5,000, and all available examples. Sample
training subsets once per seed while preserving the frozen development and
test sets. Run five final seeds.

### 10.3 Ablations

- No sentence context.
- No operational rule identifiers or typed tags.
- No proof features.
- No hard candidate constraint.
- Randomized rule identifiers.
- Random-split training evaluated on strict lexical test.

### 10.4 Metrics

Symbolic metrics are gold candidate recall, candidate-set size, forward
reconstruction rate, rule coverage, and missing-gold error category.

End-to-end metrics are exact pair match, exact pair-and-rule match, top-3
recall, macro and micro exact match, subset compliance, coverage, and
risk-coverage curves.

Efficiency metrics are parameter count, checkpoint size, wall-clock training
time, peak RAM, peak VRAM, median latency, and p95 latency.

### 10.5 Statistical Reporting

Report mean and standard deviation across seeds. Use paired bootstrap
confidence intervals over test examples for model differences. Select
hyperparameters and abstention thresholds on development data only.

## 11. Results

### Development Evidence (Not the Main Study)

The September development run uses 2,400 constructed nonce-string boundaries
across 12 draft encodings, not reviewed Sanskrit word pairs. Source-random and
pair holdouts coincide because the synthetic source groups already identify
pairs: 1,923 training, 229 development and 248 test items. The strict holdout
retains 796/112/131 items and withholds 1,361 cross-partition items. Retained
strict partitions have zero annotated lemma, source and surface overlap.

Three non-neural baselines and the tiny ranker, with no-rule and no-context
ablations, run on CPU over five seeds. The exact scores, parameter counts,
resource measurements and frozen data hashes are retained in
[the development report](../../reports/development-v1/SUMMARY.md). Candidate recall
is complete on these probes by construction and is not an independent measure
of linguistic coverage. Synthetic contexts are empty, so context ablation is
a software control, not a test of semantic disambiguation. No reliable benefit
from rule-ID features or claim of research-model superiority follows from
this experiment.

The non-executing DCS conversion examined 441,735 archive records, converted
441,722 and quarantined 13 malformed records with explicit reasons. It created
200 boundary proposals for expert annotation; none is represented as gold.
These proposals expose lemma slots and source sentences, leaving inflected
forms and surface alignment to review rather than inventing them from lemmas.

The results below come from the first corpus-derived data: **silver**
boundaries automatically extracted from the DCS (`DCS_pick`, Krishna et al.
2017). The study ran under protocol amendments 0.2 to 0.6. Three
differences from the planned study must be kept in view:

- **Draft rules.** The rule inventory is 18 *draft* encodings, not the 25
  expert-reviewed rules of Section 3.
- **Silver labels.** Labels are automatic alignments, not expert gold.
- **A different lexical test.** The left words are chunk-initial
  indeclinables (211 lemmas). So the strict test of Section 9.3 is replaced
  by a **right-word holdout**: unseen right-hand lemmas, with indeclinables
  allowed in every partition. These are right-word holdout results, not
  Section 9.3 results. The both-lemma holdout needs inflected left words
  (Phase 2) and is still pending.

### 11.1 Silver Data and Candidate Coverage

| Split | Train | Dev | Test | Mixed | Lemma overlap, train–test | Test gold candidate recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Source-grouped random | 32,749 | 1,828 | 1,892 | — | 743 lemmas | 1.000 |
| Exact-pair holdout | 33,637 | 1,490 | 1,342 | — | 549 lemmas (allowed) | 1.000 |
| Strict lexical (Section 9.3) | 1,334 | 34 | 36 | 35,065 | 0 | 1.000 |
| **Right-word holdout** | 9,066 | 988 | 821 | 2,679 | 0 right-word lemmas | 0.999 |

There are 39,838 silver examples in all. The strict lexical split keeps only
36 test examples, far below the planned minimum, which is why the
right-word holdout was adopted (protocol section 9.5).

The six rules added in amendment 0.3 were chosen from junction counts over
all partitions. Only observed surfaces were used, never ranker scores. With
them, dev candidate recall rose from 0.847 to 0.999.

### 11.2 Main Comparison: Right-Word Holdout (Test)

Settings were fixed on dev (amendment 0.4). The neural rankers have width
64, 2 layers, mean pooling and a maximum length of 300, over seeds 7, 11, 19,
23 and 29. The best epoch of 3 was chosen on dev. Paired differences are
against the linear model, with 95% bootstrap intervals over test examples.

| Ranker | Test top-1 (821) | Paired difference |
| --- | ---: | ---: |
| Symbolic rule order | 0.607 | |
| Character bigram | 0.582 | |
| Frequency, short-vowel tie-break | 0.825 (0.831 tie-averaged) | |
| **Linear features + Vidyut kosha + short-vowel tie-break** | **0.943** (0.946 tie-averaged) | reference |
| Tiny Transformer + the same features | 0.897 ± 0.017 (seeds 0.875–0.914) | −0.046 [−0.059, −0.034] |
| Residual Tiny Transformer on the frozen linear model | 0.943 ± 0.002 | +0.000 [−0.005, +0.005] |

**The symbolic layer does the heavy lifting.** It finds the correct analysis
in 99.9% of cases. Ranking candidates by training counts and dictionary
(kosha) membership already reaches 0.943 on unseen right-hand words.

**The tiny Transformer adds no accuracy here.** Trained from scratch on the
labelled data, it is worse than the linear model on every seed (exact
McNemar p < 0.001 per seed). As a residual correction to the linear model it
ties.

**On the other splits:**

| Split | Test n | Linear + kosha (tie-averaged) | Transformer + features | Paired difference |
| --- | ---: | ---: | ---: | ---: |
| Source-grouped random | 1,892 | 0.934 | 0.936 ± 0.002 | +0.007 [+0.001, +0.012] |
| Exact-pair holdout | 1,342 | 0.935 | 0.933 ± 0.003 | +0.000 [−0.005, +0.006] |
| Strict lexical | 36 | 0.778 | 0.772 ± 0.060 | not interpretable |

The Transformer gains slightly only where test words occur in training.

**Test-set use disclosure.** This right-word holdout test set has now been
evaluated three times:
1. a single-seed timing run with the original 12 rules, superseded;
2. the amendment 0.3 model, which scored 0.822 against 0.831 for frequency;
3. the run above;
4. the frozen pretraining run of Section 11.3 (amendment 0.9), on the same
   821 items in SLP1.

Any further use must be disclosed as such.

### 11.3 Self-Supervised Pretraining

The negative result in 11.2 motivated a pretraining plan (amendment 0.5).
- **Encoder.** A 4,937,220-parameter byte encoder (width 256, 6 layers).
- **Pretraining data.** Decontaminated DCS_pick text:
  - P-A: the held-out sentences and their near-duplicates removed;
    439,274 sentences.
  - P-B: additionally, every sentence containing a held-out right-hand
    lemma removed.
- **Objectives.** Span-masked byte modelling and rule-guided
  real-or-near-miss discrimination.
- **Use.** The discriminator's word score is added to the linear ranker as a
  feature.

Settings were chosen on the 988 dev examples, then frozen by hash
(amendment 0.9, protocol section 11.7) for one test run on the 821
right-word holdout examples. That run was the fourth use of the test set
(Section 11.2). Before it, the frozen script reproduced every dev result
below exactly.

| Ranker (top-1) | Dev, P-A seeds 7 / 11 / 19 | Test, P-A seeds 7 / 11 / 19 | Dev / test, P-B seed 7 |
| --- | --- | --- | --- |
| Linear, no lexicon | 0.778 | — | 0.778 / — |
| Linear + kosha (R-K, reference) | 0.903 (0.909 tie-averaged) | 0.942 (0.945 tie-averaged) | 0.903 / 0.942 |
| Linear + neural score, no kosha (R-N, H-P1) | 0.925 / 0.926 / 0.929 | 0.926 / 0.935 / 0.923 | 0.845 / 0.833 |
| Linear + kosha + neural score (R-KN, H-P2) | 0.950 / 0.952 / 0.956 | 0.956 / 0.966 / 0.957 | 0.890 / 0.922 |
| Fine-tuned pretrained ranker + kosha (H-P3) | about 0.90 | not tested | — |

Words are scored alone, not in their sentence. The R-K test score differs
from the 0.943 of Section 11.2 because candidate order, and so
tie-breaking, depends on the transliteration (SLP1 here, IAST there).

**Confirmatory test results** (paired against R-K; 95% source-group
bootstrap intervals of the seed mean):

| Hypothesis | Test, per seed | Mean [95% CI] | Dev | Verdict |
| --- | --- | --- | --- | --- |
| T-P1: R-N is non-inferior to R-K (margin 0.010) | −0.016 / −0.006 / −0.018 | −0.013 [−0.033, +0.006] | +0.022 to +0.026 | Not supported |
| T-P1s: R-N beats R-K | as above | as above | as above | Not supported |
| T-P2: R-KN beats R-K | +0.015 / +0.024 / +0.016 | +0.018 [+0.004, +0.033] | +0.048 to +0.054 | Supported |
| T-P3: R-KN coverage at τ = 0.95 within [0.71, 0.86] | 0.781 / 0.788 / 0.762 | — | 0.761–0.806 | Supported |

**What this shows:**
- **The neural score adds to the kosha.** The gain holds for every seed,
  but it is about a third of the dev gain. Dev was used repeatedly, and
  scoring words alone was chosen on it.
- **It does not replace the kosha.** On dev the neural score alone beat the
  kosha; on test it is behind for every seed. Most of the loss is in
  SDH-001, which holds 503 of the 821 examples. This arm uses no CC BY-NC-SA
  kosha data, so a ranker without the kosha costs about 0.013 on this
  evidence.
- **Strict P-B pretraining stays below the kosha.** P-B removes every
  sentence with a held-out right-hand word, so most of the P-A gain comes
  from seeing those words in other contexts.
- **Fine-tuning adds nothing.** Fine-tuning the pretrained encoder as the
  ranker (H-P3) failed its dev stopping rule and was not tested.
- **Scoring in sentence is worse.** It was worse on dev, and it is worse on
  test (descriptive).

Full results: `reports/pretraining-v1/test/TEST_RESULTS.md`.

### 11.4 Calibration and Abstention

The H-P2 ranker's confidences were evaluated with temperature scaling
cross-fitted on dev (RLCD stage 1, pre-registered).

- **Already calibrated.** Raw ECE is 0.013 to 0.029, and temperature scaling
  does not change it beyond its interval. The discriminator's word
  probability is also calibrated (ECE 0.001 to 0.003).
- **Abstention works.** Accepting only answers with confidence ≥ 0.95 keeps
  77 to 81% of dev examples, at 0.991 to 0.996 accuracy, against 0.950 to
  0.956 overall.
- **Routing to an ensemble does not help.** Sending uncertain items to a
  three-seed ensemble gains at most 0.007, inside the intervals.

The calibration figures are dev only. The gate itself was tested once
(T-P3 in Section 11.3). With the raw confidence and τ = 0.95 frozen, it
accepts 76 to 79% of test items at 0.994 to 0.995 accuracy, against 0.956 to
0.966 overall.

### 11.5 Not Yet Run

The planned study of Sections 3 and 10 remains to be done:
- the expert-reviewed rule inventory and the expert-verified gold test set
  (`docs/GOLD_SET_PLAN.md`; the texts are reserved, see Section 12.2)
- the both-lemma strict holdout (Phase 2)
- the data-efficiency curves and the ablations of Section 10.3
- the blinded expert evaluation of Section 13

Their results will be reported in this section when they exist.

## 12. Extension: Calibrated Morphological Decisions on Real Text

This section reports a separately pre-registered extension. It asks whether
the small byte encoder of the sandhi study, pretrained on Sanskrit text, can
make **calibrated typed decisions** about real Sanskrit. It was carried out
under protocol amendments 0.7 and 0.8. The plan, pre-registrations and all
reports are in the repository (`docs/RLCD_TRANSITION_PLAN.md`,
`docs/STAGE3_TEST_AMENDMENT.md`, `reports/rlcd-stage3/`).

### 12.1 Approach

The decision layer follows the reinforcement-learning-for-calibrated-decisions
(RLCD) interface of Jev (Guo et al. 2026). The model answers typed questions
about its input in one pass. Each answer is a *Choice*: a probability
distribution over a listed set of options. The training reported here is
supervised. Jev's training is not published, and the reinforcement-learning
stages planned for this project are not part of these results.

### 12.2 Task and Data

**Task.** For every word of a sentence, given in its pre-sandhi
(pada-pāṭha) segmentation, predict five Choices: vibhakti, vacana, liṅga,
puruṣa and lakāra. Each also has a NONE option for "not applicable". DCS
merges two pairs of lakāras (perfect and aorist, and the two futures), so
those are scored as merged classes. Kāraka and prayoga are not predicted.

**Source.** The Digital Corpus of Sanskrit in CoNLL-U (Hellwig 2010–2024),
pinned at one commit: 271 texts, 770,945 sentences. It was converted from
IAST to SLP1.

**Overlap audit.** Each sentence was checked against DCS_pick, the
pretraining source, with the pretraining overlap rule. 56% of DCS sentences
are exact copies of DCS_pick text.

**Division.** Recorded before any sentence was read for results:
- **Evaluation.** Development and test come only from chapters with no exact
  or near copy of DCS_pick text, in classical texts. They are split into dev
  and test by hashed chapter. Test has 133,107 words in 167 chapters and 25
  texts, never seen in pretraining or training.
- **Gold-set reserve.** Eight whole clean kāvya texts, for the expert gold
  set.
- **Training.** 336,132 classical sentences.

Labels are DCS analyses, each verified by one annotator. They are silver
labels, not expert gold.

### 12.3 Systems

| System | Description |
| --- | --- |
| B2 | Dictionary plus statistics: the most frequent tag of the form in training; for unseen forms, the Vidyut kosha analysis most frequent in training |
| N1 | The 4,937,220-parameter encoder pretrained on decontaminated DCS_pick text (P-A), fine-tuned with five linear Choice heads; cross-entropy loss; 3 seeds |
| N2 | The same architecture trained from scratch; 3 seeds |
| N3 | As N1 with a multi-class Brier loss; 3 seeds; descriptive only |

Training settings were fixed in advance: two passes, learning rate 2 × 10⁻⁴,
and the final checkpoint, with no selection on development data. Each run
takes about 10 minutes on an Apple M-series laptop GPU.

### 12.4 Whole-Analysis Confidence and Gate

A gate that accepts or defers a whole analysis needs the probability that
*all five* decisions are correct. Three findings on development data led to
the frozen choices.

- **Per-head calibration hurts the joint confidence.** Temperature-scaling
  each head separately (Guo et al. 2017) made the whole-tag confidence
  *worse*: ECE rose from 0.015 to 0.033. The heads' errors are correlated,
  so the product of separately calibrated probabilities understates the
  joint accuracy.
- **Calibrate the joint confidence directly.** Isotonic regression (Zadrozny
  and Elkan 2002) and Platt scaling (Platt 2000) of the logit of the raw
  product c₀ both calibrated it well. Platt scaling, with two parameters,
  transferred best across texts.
- **Frozen gate.** The Platt parameters were fitted once on all development
  words. The gate threshold τ was set to accept 90% of development words.

These calibration choices were made post hoc on development data. The test
run below is their first independent check.

### 12.5 Confirmatory Test

All systems, the calibrator, τ and five hypotheses were frozen by hash before
the test part was read (amendment 0.8). The test part was then read exactly
once. Each hypothesis holds only if every seed agrees and the 95%
chapter-bootstrap interval of the mean paired difference excludes 0.

| Hypothesis | Mean over seeds [95% CI] | Verdict |
| --- | --- | --- |
| T-1: N1 beats N2 on whole-tag accuracy | +0.061 [+0.058, +0.064] | Supported |
| T-2: N1 beats B2 on whole-tag accuracy, pooled | +0.018 [−0.005, +0.040] | Not supported |
| T-2b: B2 beats N1 outside Kathāsaritsāgara | +0.037 [−0.018, +0.081] | Not supported |
| T-3: the frozen calibration lowers NLL against the raw product | −0.0038 [−0.0058, −0.0020] | Supported |
| T-4: test coverage at the frozen τ lies within [0.85, 0.95] | 0.884–0.886 | Supported |

**Accuracy on test** (ranges over seeds; head columns are accuracy on words
whose gold value is not NONE):

| System | Whole tag | Unseen forms | vibhakti | vacana | liṅga | puruṣa | lakāra |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B2 | 0.862 | 0.485 | 0.864 | 0.946 | 0.852 | 0.950 | 0.948 |
| N1 | 0.878–0.882 | 0.760–0.768 | 0.910–0.912 | 0.953–0.955 | 0.871–0.876 | 0.937–0.942 | 0.917–0.925 |
| N2 | 0.817–0.819 | 0.695–0.701 | 0.872–0.874 | 0.928–0.930 | 0.813–0.815 | 0.862–0.866 | 0.835–0.836 |
| N3 | 0.875–0.878 | 0.757–0.767 | 0.907–0.909 | 0.951–0.953 | 0.870–0.874 | 0.916–0.923 | 0.895–0.899 |

**Calibration and gate on test (N1):**
- **ECE.** The frozen Platt calibration lowers it from 0.019–0.020 for the
  raw product to 0.006–0.008.
- **Gate.** It accepts 88.4–88.6% of words. The accepted words have 0.939–0.942
  whole-tag accuracy, the same as on development data, against 0.878–0.882
  for all words.

**By text.** N1 beats B2 in 14 of 25 test texts and is worse in 10.
Kathāsaritsāgara supplies 65% of test words, and there N1 is ahead: 0.914
against 0.862 for seed 7. N1 trails on several prose texts: Harṣacarita,
0.694 against 0.860; Lalitavistara, 0.738 against 0.873.

### 12.6 Interpretation

**What the test supports:**
1. **Pretraining helps.** Self-supervised pretraining of a 4.94M-parameter
   byte encoder on Sanskrit text measurably improves its decisions about
   unseen classical texts. The gain is +0.061, about the same as on
   development data (+0.064), and holds for every head.
2. **The confidence is usable.** A two-parameter calibration of the
   whole-analysis confidence, fitted on development data, transfers to
   held-out texts. A threshold chosen on development data keeps its
   accepted-word accuracy. The system can say which of its analyses to trust,
   which is the property a neuro-symbolic gate needs.
3. **It generalises beyond lookup.** The encoder handles unseen word forms
   far better than lookup: 0.76 against 0.49 whole-tag accuracy.

**What it does not support:** a reliable advantage over a
dictionary-plus-statistics baseline across texts. The dev-observed loss
outside Kathāsaritsāgara recurred in direction on test, but the frozen test
for it lacked the power to confirm it. The prose texts, where the encoder
trails most, are the obvious target for further work.

## 13. Expert Evaluation

At least 200 outputs will be sampled across rules, split families, correctness
categories, and abstentions. When feasible, two reviewers with Pāṇinian
grammar expertise will independently judge:

- Whether the split is acceptable in context.
- Whether the operational rule applies.
- Whether the cited source is appropriate.
- Whether the proof trace is sufficient and understandable.

The paper reports acceptance rates, raw agreement, Cohen's kappa when two
reviewers participate, and a qualitative error taxonomy. Reviewer
disagreements remain visible and may motivate a narrower rule inventory.

## 14. Reproducibility

Every reported run must preserve:

- Code commit.
- Rule-inventory commit and SHA-256 digest.
- Source and derived-data manifests.
- Normalization and deduplication versions.
- Split method, seed, and manifest.
- Model configuration and exact parameter count.
- Optimizer, schedule, batch size, epochs, and early-stopping rule.
- Hardware, software versions, wall time, and memory.
- Predictions, proof traces, metric output, and bootstrap samples.

The test command is:

    python3 -m pytest tests -q

The current suite covers the typed loader, proof application, publication
gates, deterministic lexical splitting, zero lemma overlap, pickle-opcode
audit, all-sandhi source-corpus reproducibility, and legacy compatibility
tests.

## 15. Limitations and Risks

First, a 25-rule inventory represents only a small operational subset and may
not capture commentary-dependent interpretation, optionality, lexical
exceptions, or interactions required by expert analysis. The broader
148-record corpus is only a source review queue and does not remove this
limitation.

Second, corpus analyses can contain annotation errors and may not identify the
precise external boundary needed by this task. Automatic conversion can create
selection bias toward easy, unambiguous cases.

Third, strict lexical holdout changes the lexical and rule distribution and
withholds cross-partition examples. Both retained coverage and excluded mixed
examples must be reported.

Fourth, proof traces explain execution of encoded rules but do not establish
the truth or completeness of those rules. Trace faithfulness and grammatical
acceptability are separate evaluation questions.

Fifth, results on external vowel sandhi do not justify claims about full word
segmentation, morphology, syntax, translation, literary quality, or language
modeling.

Sixth, the pretraining gains of Section 11.3 are smaller on test than on
the repeatedly used dev set. They rest on the fourth use of one silver test
set, with encoders that saw the held-out right-hand words in other
sentences (P-A).

Seventh, the Section 12 extension has its own limits:
- **Silver labels.** Its labels are silver, single-annotator DCS analyses.
- **Gold-segmented input.** Its input is gold-segmented.
- **Merged tenses.** It scores two pairs of tenses as merged classes.
- **Narrow bootstrap.** Its bootstrap reflects chapter variation within the
  chosen texts, not the choice of texts.
- **Post hoc calibration.** Its calibration choices were made post hoc on
  development data and confirmed only by a single test run.
- **Imperfect text rule.** The rule defining classical texts admitted two
  Vedic-ritual commentaries, with 488 test words between them.
- **Spent test part.** The test part is now used; any further use must be
  disclosed.

Finally, the DCS archive is released under CC BY 4.0. The ashtadhyayi-com
material is available only for products offered free of charge and may not be
used commercially, which is stricter than this project's Apache-2.0 code
license. The release therefore keeps that material under its upstream terms
and includes only ancient source text, factual classifications, code,
manifests, hashes, and reconstruction instructions, not modern commentary or
translations.

## 16. Conclusion

This study replaces a broad proposal for a Sanskrit language model with a
bounded experiment whose claims can be falsified. A reproducible all-sandhi
source inventory creates a transparent path for expert-led expansion, while a
typed symbolic layer defines and traces the reviewed external-vowel pilot. A
tiny Transformer ranks only licensed candidates, and strict lexical evaluation
tests whether results survive removal of training vocabulary. The architecture
is lightweight by design, but archival value will come from completed
experiments, leakage controls, baselines, ablations, resource measurements,
and expert analysis. Until those results replace all placeholders, this
document remains a working protocol rather than a completed research article.
The completed extension in Section 12 shows, on real held-out text, the two
properties the larger design depends on:
- the small encoder benefits from Sanskrit pretraining;
- its confidence in a whole analysis can be calibrated and used to decide
  when to trust it.

It also shows where a lookup baseline remains stronger.

The frozen sandhi pretraining test of Section 11.3 points the same way. The
pretrained word score improves a dictionary-based ranker, and the ranker's
confidence supports abstention on held-out items, but the score does not
replace the dictionary.

## References

Hellwig, Oliver, and Sebastian Nehrdich. 2018. Sanskrit Word Segmentation Using
Character-level Recurrent and Convolutional Neural Networks. Proceedings of
EMNLP 2018. https://aclanthology.org/D18-1295/

Krishna, Amrith, Pavan Kumar Satuluri, and Pawan Goyal. 2017. A Dataset for
Sanskrit Word Segmentation. Proceedings of the LaTeCH-CLfL Workshop.
https://aclanthology.org/W17-2214/

Krishna, Amrith, Pavankumar Satuluri, and Pawan Goyal. 2017. A Dataset for
Sanskrit Word Segmentation [dataset]. Zenodo. DOI: 10.5281/zenodo.803508.
https://zenodo.org/records/803508

Sandhan, Jivnesh, Rathin Singha, Narein Rao, Suvendu Samanta, Laxmidhar
Behera, and Pawan Goyal. 2022. TransLIST: A Transformer-Based Linguistically
Informed Sanskrit Tokenizer. Findings of EMNLP 2022.
https://aclanthology.org/2022.findings-emnlp.513/

Vaswani, Ashish, et al. 2017. Attention Is All You Need. Advances in Neural
Information Processing Systems 30.
https://papers.nips.cc/paper/7181-attention-is-all-you-need

ashtadhyayi-com contributors. Data powering ashtadhyayi.com.
https://github.com/ashtadhyayi-com/data

Ambuda contributors. Vidyut: Reliable infrastructure for Sanskrit software.
https://github.com/ambuda-org/vidyut

Ambuda contributors. Sanitized data from the Digital Corpus of Sanskrit.
https://github.com/ambuda-org/dcs

Guo, Chuan, Geoff Pleiss, Yu Sun, and Kilian Q. Weinberger. 2017. On
Calibration of Modern Neural Networks. Proceedings of the 34th International
Conference on Machine Learning (ICML 2017), PMLR 70, pages 1321–1330.
https://proceedings.mlr.press/v70/guo17a.html

Guo, Ruoqi, Yi Liu, Gelei Deng, Yuekang Li, Lida Zhao, Yutao Wu, Simin Chen,
Ying Zhang, and Leo Yu Zhang. 2026. Just Ask Jev: Reinforcement Learning for
Calibrated Decisions as a Zero-Shot Detector of AI Alignment Failures.
arXiv:2609.29429.

Hellwig, Oliver. 2010–2024. The Digital Corpus of Sanskrit (DCS).
https://github.com/OliverHellwig/sanskrit

Platt, John C. 2000. Probabilistic Outputs for Support Vector Machines and
Comparisons to Regularized Likelihood Methods. In Alexander J. Smola, Peter
Bartlett, Bernhard Schölkopf, and Dale Schuurmans, editors, Advances in Large
Margin Classifiers, pages 61–74. MIT Press.

Zadrozny, Bianca, and Charles Elkan. 2002. Transforming Classifier Scores into
Accurate Multiclass Probability Estimates. Proceedings of the Eighth ACM
SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD
2002), pages 694–699. https://doi.org/10.1145/775047.775151
