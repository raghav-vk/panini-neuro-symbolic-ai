# Plan: Self-Supervised Pretraining for the Neural Ranker

**Status:** Adopted as amendment 0.5 of `docs/EXPERIMENT_PROTOCOL.md`
(section 11.3) on 2026-10-24. Nothing here has been run yet.

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
