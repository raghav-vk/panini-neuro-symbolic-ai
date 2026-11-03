# Pretraining: Dev Results (H-P1, H-P2)

**Dev only.** The right-word holdout test set was not read. One pretraining seed.

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
