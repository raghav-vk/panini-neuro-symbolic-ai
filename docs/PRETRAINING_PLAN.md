# Plan: Self-Supervised Pretraining for the Neural Ranker

**Status:** Adopted as amendment 0.5 of `docs/EXPERIMENT_PROTOCOL.md`
(section 11.3) on 2026-10-24. Nothing here has been run yet.

## In Plain Terms

**The problem.** Splitting a fused form takes two steps:

1. **The rules list the possible splits.** For *tathāgata* they give both
   *tathā + agata* and *tathā + āgata*. This step is essentially solved: the
   correct split is in the list 99.9 percent of the time.
2. **Something picks the right one.** This is where the neural part should
   help, and so far it doesn't.

The hard cases look like that example. The sandhi works either way, so the
only question is whether *agata* or *āgata* is a real word. The best picker
today is a simple formula, not the neural network. Its strongest signal is a
dictionary lookup (the Vidyut kosha), and it scores 0.909 on dev.

The network loses because the test words never appear in its 9,066 labelled
training examples, so it cannot know which forms are real. The dictionary
does. The dictionary also carries non-commercial licence terms, which
conflicts with the long-term plans.

**The idea.** Before the network learns to pick splits, let it read lots of
plain Sanskrit text with no labels: all of about 440,000 corpus sentences,
not just the 9,000 labelled examples. This is pretraining, the way large
language models learn a language before being taught a task. From that
reading it can learn what real Sanskrit words look like, with no dictionary.

It learns from two exercises:

1. **Fill in the blanks.** Hide some letters in a sentence and guess them.
2. **Spot the fake.** Take a real word and change its first or last vowel
   the way sandhi confusions do (*āgata* to *agata*). The model learns to tell
   the real form from the fake. Our rules decide which changes to make, so
   the rules teach the network. This is the neuro-symbolic contribution.

**What we then test**, each against today's 0.909:

| | Question | If yes |
| --- | --- | --- |
| 1 | Can the network's "is this a real word" score **replace** the dictionary? | The neural part does the dictionary's job, with no licence problem |
| 2 | Does that score **plus** the dictionary beat the dictionary alone? | The network fills the dictionary's gaps (it misses about 10 percent of the words needed) |
| 3 | Does the pretrained network, trained further as the picker itself, beat the formula? | The neural part is the best picker |

**Keeping it honest.** The network must not read the test sentences during
pretraining. There are two versions of the text:

- **P-A (main):** the dev and test sentences are removed, with their copies
  and near-copies. Test words can still appear in other sentences, just as
  they appear in the dictionary.
- **P-B (strict):** every sentence containing any test word is also removed.
  Any gain must then come from how Sanskrit words are built, not from having
  seen the word.

**Order and stopping point.**

1. Build P-A and P-B (issue #61, the next step).
2. Time a short trial run on the laptop.
3. Pretrain the small model (about 5M parameters).
4. Test questions 1 to 3 on dev.
5. Only if it clearly beats 0.909: train the larger model, run the strict P-B
   version, then make a single test-set run.

If nothing beats 0.909, the paper says so: at this scale, pretraining does
not replace a dictionary. That is still publishable, because no one has
measured it.

ByT5-Sanskrit, a much larger published model, is scored only for comparison.
It has very likely seen our test sentences already, so it is labelled as a
contaminated reference and is never part of our system.

The sections below give the details.

## 1. Why

On the silver DCS right-word holdout (protocol sections 11.1 and 11.2), the
rules generate the gold split for 99.9 percent of examples. Choosing among
the candidates is now done best by a linear model over symbolic features:
training-word frequency, rule frequency, Vidyut kosha membership and a
short-vowel preference. It scores 0.909 on dev. No Transformer variant has
beaten it, including a residual correction that starts at the linear model.

The hard cases turn on whether a word exists, as in *āgata* against *agata*,
when the word never occurs in the 9,066 labelled training examples. A ranker
trained only on those examples cannot learn that. The kosha supplies it
symbolically. ByT5-Sanskrit (Nehrdich et al. 2024, arXiv:2409.13920) shows
that byte-level pretraining on unlabelled Sanskrit can acquire lexical
knowledge without a lexicon. This plan tests whether a small model of our own
can do the same, and whether that makes the neural part necessary.

A literature survey found no published evidence that state space models or
hybrid architectures help at our scale and sequence length (under 300 bytes).
They are left out of the core plan. At most they are one later ablation.

## 2. Hypotheses

- **H-P1 (neural lexicon).** A pretrained model's score for "this candidate
  word is real" can replace the kosha flag in the linear model without losing
  accuracy. If true, the neural part does the job the dictionary does, with no
  hand-built lexicon and no non-commercial data.
- **H-P2 (complement).** Adding the neural score to the kosha flag improves
  over the kosha flag alone, because the kosha misses about 10 percent of gold
  right words.
- **H-P3 (pretrained ranker).** Fine-tuning the pretrained encoder as the
  ranker beats `linear_features_short_vowel` with the kosha.

## 3. Corpus and Decontamination

The source is DCS_pick (CC BY 4.0): 441,722 sentences, 21.5M characters,
converted to IAST to match the ranker's input. No other corpus is used in the
first round, so licensing stays simple. GRETIL and Sangraha are possible
later; their licences vary and need checking first.

Two pretraining corpora, both built from the right-word holdout split:

| Corpus | Removes | Sentences kept | Characters kept |
| --- | --- | ---: | ---: |
| P-A | the 1,801 dev and test source sentences, plus their exact and near duplicates | 439,921 before duplicate removal | 21.4M |
| P-B | P-A, plus every sentence containing any of the 652 held-out right-word lemmas | 349,450 before duplicate removal | 16.4M |

Duplicates: 44 sentences elsewhere in the corpus are exact copies of a dev or
test sentence. Another 425 share at least two 30-character spans with one
(measured 2026-10-24). All are removed.

The author confirmed P-A as the main condition and P-B as the strict
condition on 2026-10-24.

- **P-A** is the main condition. The model may see a held-out word in other
  sentences, just as the kosha contains it. That is external knowledge about
  the language, not about the test items.
- **P-B** is the strict condition. The model never sees held-out right words.
  Any gain must come from morphology and phonotactics, not memorised words.

The build script must write an audit report with removed counts, hashes and
the duplicate checks. The paper reports both conditions.

### Other data considered

**Hellwig and Nehrdich 2018 (EMNLP) sandhi data**
(`OliverHellwig/sanskrit`, `papers/2018emnlp/data`), checked 2026-10-28.

| Property | Finding |
| --- | --- |
| Content | DCS text lines with each character's pre-sandhi form: about 26,700 lines each in the validation and test files. The training file is on Google Drive |
| License | **GNU AGPLv3**, for code and data alike |
| Source | DCS, the same corpus as DCS_pick. About 31 percent of its validation and test lines exactly match a DCS_pick sentence; the rest are DCS text that DCS_pick lacks |
| Overlap with our holdout | At least 60 of our 1,801 dev and test sentences appear exactly in its validation and test files. The training file was not checked and very likely holds more |

**Decision: not used for pretraining or training.**

- **Licence.** AGPLv3 copyleft conflicts with releasing our code and
  weights under Apache 2.0, and with commercial use. How it applies to model
  weights is unsettled, which is reason enough to stay clear.
- **No new text.** It is DCS text. The full DCS in CoNLL-U format is the same
  text under CC BY 4.0, so if more pretraining text is wanted, that is the
  source to use.
- **Contamination.** It would need the same decontamination as P-A. It also
  overlaps the held-out DCS chapters planned for the gold set
  (`docs/GOLD_SET_PLAN.md`), which must stay out of every pretraining corpus.

Its pretrained rcNN model may still be run locally as a **prior-work
reference** on our items, cited as Hellwig and Nehrdich 2018. Like
ByT5-Sanskrit, it was trained on DCS and may have seen our test sentences, so
its score is labelled as contaminated.

## 4. Model

A bidirectional byte-level Transformer encoder, the same family as the
current ranker, so pretrained weights load directly. Two sizes:

| Size | Width | Layers | Heads | Approximate parameters |
| --- | ---: | ---: | ---: | ---: |
| S | 256 | 6 | 8 | 5M |
| M | 512 | 6 | 8 | 20M |

Training runs on the laptop's Apple M5 Pro GPU through PyTorch MPS. MPS is
not bit-for-bit deterministic, so every result is reported over several seeds.

## 5. Pretraining Objectives

1. **Span-masked byte language modelling.** Mask about 15 percent of bytes in
   spans of mean length 3 and predict them.
2. **Rule-guided real-or-near-miss discrimination**, the neuro-symbolic part
   (ELECTRA-style, arXiv:2003.10555). Take word-initial and word-final vowels
   in running text and alter them the way sandhi confusions do: flip vowel
   length (a/ā, i/ī, u/ū) and apply the inverse rewrites our rules license.
   The model learns to tell the attested form from the altered one.
   - Altered forms that occur anywhere in the corpus as a word are dropped as
     negatives, because they may be real words.
   - The kosha is not used in pretraining, so the pretrained weights carry no
     Monier-Williams terms.

Objective 2 fits our error type exactly: it teaches the model which boundary
vowel a real word has. The paper can then say the rules teach the network,
not only filter for it.

## 6. How the Pretrained Model Is Used

1. **Neural lexicon score.** The discriminator's probability that the
   candidate's left and right words are real becomes a feature of the linear
   model. This tests H-P1 and H-P2.
2. **Fine-tuned ranker.** The pretrained encoder initialises the candidate
   scorer, with the lexical head and optionally the residual start. This tests
   H-P3.

## 7. Comparisons

All on the right-word holdout, dev only until the final run:

| Condition | Lexical knowledge from |
| --- | --- |
| Linear + training counts + short vowel | training data only |
| Linear + kosha (current best, 0.909 dev) | dictionary |
| Linear + neural score (P-A) | unlabelled text |
| Linear + neural score (P-B) | unlabelled text, held-out words removed |
| Linear + kosha + neural score (P-A) | both |
| Fine-tuned pretrained ranker, S and M (P-A) | unlabelled text plus labels |
| Fine-tuned ranker without pretraining (existing) | labels only |
| Objective ablation: masked LM only, or discrimination only | |
| Reference only: ByT5-Sanskrit candidate scores (`buddhist-nlp/byt5-sanskrit`) | 5.4B characters of pretraining |
| Reference only: rcNN (Hellwig and Nehrdich 2018), run locally | DCS-trained segmenter |

**ByT5-Sanskrit** (582M parameters) is a cited reference point, never a
component of our system. Its pretraining text very likely contains DCS texts,
and its multitask model was fine-tuned on DCS. Its score on our test items is
therefore contaminated and is reported only as an upper reference, labelled as
such. Only the base model is scored, never the multitask model. Our own models
must stand on their own comparisons.

## 8. Order of Work and Stopping Rules

1. Build P-A and P-B with the audit report. Unit tests for every filter.
2. Time a pilot: size S, 1,000 steps on MPS. Check the cost estimate before
   committing to full runs.
3. Pretrain S on P-A, both objectives. Check held-out masked-byte accuracy
   and discrimination accuracy on dev-sentence words, without labels.
4. Test H-P1 and H-P2 on dev with 3 seeds. Use the linear model with the neural
   score; this needs no fine-tuning.
5. Fine-tune for H-P3 on dev with 3 seeds.
6. Only if step 4 or 5 beats 0.909 by more than the seed spread: pretrain M,
   and run P-B for the strict condition.
7. Freeze the settings in amendment 0.6. Then make one test run with paired
   comparisons.

If no condition beats 0.909 on dev, the paper reports that pretraining at
this scale does not displace the symbolic lexicon. That is still a
publishable result, given the survey found no prior study of it.

## 9. Test-Set Reuse

The right-word holdout test set has already been evaluated three times:

- the timing run with 12 rules;
- the section 11.1 run;
- the section 11.2 runs.

A fourth evaluation must be disclosed as reuse. The stronger option is a new
final test set. Before the paper is final, the planned independently reviewed
gold set (protocol sections 6 and 17) should serve as the untouched
evaluation. The silver results stay as development evidence.

## 10. Licensing

- The pretraining text is CC BY 4.0 (DCS_pick), with attribution.
- The kosha is not used in pretraining. The pretrained weights are therefore
  free of the Monier-Williams non-commercial terms and can be released under
  Apache 2.0, with DCS attribution.
- If H-P1 holds, the neural lexicon would be a fully open replacement for the
  non-commercial dictionary. That matters for the long-term plans.

## 11. Must-Cite Related Work

- ByT5-Sanskrit: Nehrdich, Hellwig and Keutzer 2024 (arXiv:2409.13920).
- Hellwig and Nehrdich 2018, rcNN-SS (EMNLP, D18-1295).
- TransLIST: Sandhan et al. 2022 (arXiv:2210.11753).
- SanskritShala: Sandhan et al. 2023 (arXiv:2302.09527).
- Krishna et al. 2018 (arXiv:1809.01446).
- CharSS (arXiv:2407.06331).
- Dave et al. 2021 (arXiv:2010.12940).
- ByT5 (arXiv:2105.13626).
- ELECTRA (arXiv:2003.10555).
- Data contamination: Magar and Schwartz 2022 (arXiv:2203.08242).
- State space model caveats: arXiv:2312.04927 and arXiv:2402.01032.

Entries come from a literature survey on 2026-10-24. Check each against the
original paper before it is cited.
