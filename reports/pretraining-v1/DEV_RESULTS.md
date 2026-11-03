# Pretraining: Dev Results (H-P1, H-P2)

**Dev only.** The right-word holdout test set was not read. Sections 1 and 2 are the first run (P-A, seed 7);
section 3 adds seeds 11 and 19, the strict P-B corpus and fine-tuning (H-P3), from the 2026-11-02 overnight queue.

Encoder: size S (4.94M parameters), P-A, both objectives, 10 passes (34,720 steps,
1 h 57 min on an Apple M5 Pro through MPS), seed 7. The final checkpoint is used;
no checkpoint was chosen on dev. Record: `pretrain_S_PA_seed7.json`.

Label-free checks on 984 dev sentences at the end: masked-byte accuracy 0.515,
near-miss discrimination balanced accuracy 0.955.

## Linear ranker on dev (988 examples)

`linear_features_short_vowel` with training counts, rule frequency and the short-vowel
tie-break, plus the features shown. Paired against the kosha row (top-1 0.903).

| Features added | Words scored | Top-1 | Tie-averaged | Net vs kosha | 95% paired bootstrap | Exact McNemar p |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| Kosha (reference) | | 0.903 | 0.909 | | | |
| Neural score (H-P1) | in sentence | 0.927 | 0.927 | +0.024 | [+0.002, +0.047] | 0.042 |
| Neural score (H-P1) | alone | 0.925 | 0.925 | +0.022 | [+0.001, +0.044] | 0.055 |
| Kosha + neural (H-P2) | in sentence | 0.950 | 0.950 | +0.048 | [+0.027, +0.069] | 5e-06 |
| Kosha + neural (H-P2) | alone | 0.950 | 0.950 | +0.048 | [+0.028, +0.068] | 2e-06 |

The bootstrap resamples dev items, not source clusters, and covers neither pretraining
seed variance nor the choice among the four rows above.

## Caveats

- **One pretraining seed.** The plan's stopping rule asks for a gain beyond the seed
  spread; that needs further pretraining seeds.
- **P-A, not P-B.** P-A keeps sentences that contain held-out right words elsewhere
  (plan section 3). The strict P-B condition is still to run.
- **Dev has been looked at repeatedly**, including with the first-pass checkpoint
  (H-P1 0.807 in sentence, 0.828 alone; H-P2 0.879 and 0.897). Those numbers were
  not used to choose anything.
- The kosha-free H-P1 row is the licence-relevant one: no Monier-Williams data in the
  encoder or in that ranker.

## 3. Seeds, P-B and fine-tuning (2026-11-02 queue)

Same settings as above; records `pretrain_S_PA_seed11.json`, `pretrain_S_PA_seed19.json`,
`pretrain_S_PB_seed7.json`. P-B: 26,570 steps (10 passes of its 15.1M characters); end of
training masked-byte accuracy 0.484, balanced discrimination 0.929 (P-A seed 7: 0.515, 0.955).

### Linear ranker, net versus kosha (0.903), all pretraining runs

| Encoder | H-P1 in sentence | H-P1 alone | H-P2 in sentence | H-P2 alone |
| --- | ---: | ---: | ---: | ---: |
| P-A seed 7 | 0.927 (+0.024) | 0.925 (+0.022) | 0.950 (+0.048) | 0.950 (+0.048) |
| P-A seed 11 | 0.912 (+0.009, p 0.49) | 0.926 (+0.023, p 0.047) | 0.945 (+0.043) | 0.952 (+0.050) |
| P-A seed 19 | 0.909 (+0.006, p 0.68) | 0.929 (+0.026, p 0.022) | 0.942 (+0.039) | 0.956 (+0.054) |
| **P-B seed 7** | **0.834 (−0.069)** | **0.845 (−0.058)** | **0.884 (−0.019, p 0.084)** | **0.890 (−0.013, p 0.24)** |

P-A seed spread: H-P1 in sentence 0.909–0.927, alone 0.925–0.929; H-P2 in sentence
0.942–0.950, alone 0.950–0.956. Words scored alone are both better and steadier.
Every P-A H-P2 row beats kosha with McNemar p < 0.001.

Against the kosha-free linear ranker (0.778, the fair reference for H-P1), P-B adds
+0.056 in sentence and +0.067 alone (p 5e-4 and 2e-5); P-A seeds add +0.13 to +0.15.

**Reading.** Most of the P-A gain comes from the encoder having seen the held-out right
words in other sentences. With those sentences removed (P-B), the neural score still
helps a ranker with no lexicon, but it no longer beats the kosha, and adding it to the
kosha is slightly harmful. One likely cause is a train/dev shift: every training right
word is in P-B, no dev right word is, so the ranker learns to trust the score more than
it should on dev (mean gold right-word score: train −0.12, dev −0.42 in sentence).

### Fine-tuned ranker (H-P3), three seeds, kosha data

Width 256, 6 layers, 8 heads, 3 epochs, boundary-vowel feature; epoch chosen on dev, so
these are optimistic.

| Ranker | Seeds 7 / 11 / 19 | Mean |
| --- | --- | ---: |
| Linear + kosha (reference) | 0.903 | 0.903 |
| Pretrained (P-A seed 7) + kosha | 0.897 / 0.904 / 0.901 | 0.901 |
| From scratch + kosha | 0.902 / 0.890 / 0.896 | 0.896 |
| Pretrained, no kosha (lexical features) | 0.823 / 0.841 / 0.827 | 0.830 |

With the kosha, both fine-tuned rankers stay at the linear reference: 13 to 15 losses
and 1 to 14 wins each, so the Transformer adds almost nothing on top of the features.
Pretraining is within seed noise of scratch. Without the kosha, the pretrained ranker
(0.830) beats the linear lexical-only ranker (0.778) but is far below linear + neural
score (0.925). No from-scratch, no-kosha control was run.
