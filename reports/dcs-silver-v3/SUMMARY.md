# Silver DCS Results with External Lexicon (2026-10-24)

Settings were fixed in protocol amendment 0.4 (section 11.2) before these runs.

- **Data and rules:** the same 39,838 silver examples and 18 draft rules as
  `reports/dcs-silver-v2`.
- **Kosha flags:** each candidate is flagged as found or not found in the
  Vidyut 0.4.0 kosha (`scripts/annotate_lexicon.py`). The kosha contains
  CC BY-NC-SA 3.0 Monier-Williams data. It and the flags are not
  redistributed.
- **Neural runs:** `--external-lexicon --boundary-vowel-feature`, 3 epochs
  (best epoch chosen on dev), width 64, 2 layers, maximum length 300, seeds 7,
  11, 19, 23, 29.

This is the third evaluation of the right-word holdout test set; see protocol
section 9.5 and `docs/PRETRAINING_PLAN.md` section 9.

## Primary Result: Right-Word Holdout

`strict_right_lemma`, 821 test examples. Paired differences are against
`linear_features_short_vowel` with index tie-breaking (top-1 0.9428).

| Ranker | Test top-1 | Paired difference (95% CI) |
| --- | ---: | ---: |
| Frequency, short-vowel tie-break | 0.825 (0.831 tie-averaged) | |
| **Linear head features + kosha + short-vowel tie-break** | **0.943 (0.946 tie-averaged)** | baseline |
| Transformer + head with kosha and boundary-vowel features | 0.897 ± 0.017 | −0.046 [−0.059, −0.034] |
| Residual Transformer on the frozen linear model | 0.943 ± 0.002 | +0.000 [−0.005, +0.005] |

- The kosha raises the best non-neural ranker from 0.831 to 0.946, so the
  dev result holds on test.
- The Transformer with the same features is worse on every seed (exact
  McNemar p < 0.001 per seed).
- The residual Transformer equals the linear model it starts from.
- No neural variant adds accuracy on unseen right-hand words.

## Other Splits

| Split | Test n | Linear + kosha (tie-averaged) | Transformer + features | Paired difference (95% CI) |
| --- | ---: | ---: | ---: | ---: |
| source_random | 1,892 | 0.934 | 0.936 ± 0.002 | +0.007 [+0.001, +0.012] |
| pair | 1,342 | 0.935 | 0.933 ± 0.003 | +0.000 [−0.005, +0.006] |
| strict_lemma | 36 | 0.778 | 0.772 ± 0.060 | not interpretable (36 examples) |

On `source_random` the Transformer is slightly ahead of the linear model.
Against index tie-breaking the lead is 0.7 points; against the tie-averaged
score it is about 0.3. Test words there mostly occur in training. On unseen
right-hand words the Transformer gives no gain. This is consistent with the
view that it lacks lexical knowledge beyond the labelled data, which
`docs/PRETRAINING_PLAN.md` addresses.

## Files

- `results.json`: all four splits.
- `residual_results.json`: residual run on the right-word holdout.
- `paired_*.json`: `scripts/compare_paired.py --baseline linear_features_short_vowel --models tiny_full`.

Reproduce:

    .venv/bin/python scripts/fetch_vidyut_data.py
    .venv/bin/python scripts/annotate_lexicon.py --data data/processed/dcs-silver-v2-splits --output data/processed/dcs-silver-v2-kosha-splits
    .venv/bin/python scripts/run_experiment.py --data data/processed/dcs-silver-v2-kosha-splits --output runs/dcs-silver-v3-kosha --external-lexicon --boundary-vowel-feature --epochs 3 --max-length 300
    .venv/bin/python scripts/run_experiment.py --data data/processed/dcs-silver-v2-kosha-splits --output runs/dcs-silver-v3-residual --splits strict_right_lemma --external-lexicon --boundary-vowel-feature --residual --epochs 3 --max-length 300
