# Silver DCS Results, Rules v2 (2026-10-24)

Data: 39,838 silver external vowel-sandhi boundaries aligned from DCS lemma
annotations (`scripts/extract_dcs_boundaries.py`). The 18 draft rules and the
alignments are not expert reviewed. Settings were fixed on dev before this test
run (protocol amendment 0.3, section 11.1): lexical feature head, 3 epochs,
width 64, 2 layers, mean pooling, maximum length 300, seeds 7, 11, 19, 23, 29.

## Primary Result: Right-Word Holdout

`strict_right_lemma` (section 9.5): 9,066 train, 988 dev, 821 test. Test
right-word lemmas never occur in training.

| Ranker | Test top-1 | Paired difference to baseline (95% CI) |
| --- | ---: | ---: |
| Symbolic order (tie-averaged) | 0.141 | |
| Character bigram | 0.582 | |
| Frequency (tie-averaged) | 0.611 | |
| Frequency, short-vowel tie-break | 0.825 (0.831 tie-averaged) | baseline |
| Transformer + lexical head | 0.822 ± 0.010 | −0.002 [−0.013, +0.009] |
| ... without rule IDs | 0.830 ± 0.006 | +0.005 [−0.004, +0.015] |
| ... without context | 0.828 ± 0.004 | +0.003 [−0.008, +0.014] |

Candidate recall is 0.999, with 9.2 candidates per example.

No neural variant differs measurably from the frequency baseline. Exact McNemar
tests per seed are in `paired.json`. Removing rule IDs or context from the
model input does not hurt. On dev the full model led the baseline by 2.4
points (0.824 against 0.800). That lead did not hold on test, most likely
because the variant was chosen on dev.

**Interpretation.** The demonstrated contribution of the rules is candidate
generation: near-complete recall with a small candidate set. The neural ranker
does not yet add accuracy beyond word frequency. The remaining errors mostly
turn on the vowel length of a right word never seen in training, which neither
the training lexicon nor one neighbouring chunk of context can settle.

## Other Splits

| Split | Test n | Best baseline (tie-averaged) | Transformer + lexical head |
| --- | ---: | ---: | ---: |
| source_random | 1,892 | 0.905 | 0.912 ± 0.002 |
| pair | 1,342 | 0.899 | 0.902 ± 0.003 |
| strict_lemma | 36 | 0.722 | 0.767 ± 0.095 |

`strict_lemma` (section 9.3) keeps only 36 test examples, far below the
500-example minimum, and is not interpretable. Phase 2 of section 9.5
addresses this.

## Files

- `results.json`: all four splits, baselines and full model.
- `ablations_results.json`: right-word holdout with no-rules and no-context
  ablations. Its full-model seeds reproduce `results.json` exactly.
- `paired.json`: `scripts/compare_paired.py --run runs/dcs-silver-v2-lexical-ablations`.
- `extraction_report.json`: silver extraction counts and rule coverage.

Reproduce:

    .venv/bin/python scripts/extract_dcs_boundaries.py --output data/processed/dcs-silver-v2
    .venv/bin/python scripts/prepare_experiment.py --silver-examples data/processed/dcs-silver-v2/examples.jsonl --output data/processed/dcs-silver-v2-splits
    .venv/bin/python scripts/run_experiment.py --data data/processed/dcs-silver-v2-splits --output runs/dcs-silver-v2-lexical --lexical --epochs 3 --max-length 300
    .venv/bin/python scripts/run_experiment.py --data data/processed/dcs-silver-v2-splits --output runs/dcs-silver-v2-lexical-ablations --splits strict_right_lemma --ablations --lexical --epochs 3 --max-length 300
