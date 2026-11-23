# Sandhi Pretraining: Frozen Test Run (generated; right-word holdout test file)

Amendment 0.9 (protocol section 11.7, docs/SANDHI_PRETRAINING_TEST_AMENDMENT.md, with its erratum). Code at commit `564d1f1bbc8d76f543716ee0dbcc780c6247470f`. 821 examples in 817 source groups; intervals are 95% source-group bootstrap intervals of the seed-mean difference against R-K. No multiplicity correction.

## Confirmatory hypotheses

- **T-P1** R-N is non-inferior to R-K (margin 0.01): per seed -0.0158, -0.0061, -0.0183; mean -0.0134 [-0.0325, +0.0061]; McNemar p 0.15, 0.63, 0.1; **not supported**
- **T-P1s** R-N beats R-K: per seed -0.0158, -0.0061, -0.0183; mean -0.0134 [-0.0325, +0.0061]; McNemar p 0.15, 0.63, 0.1; **not supported**
- **T-P2** R-KN beats R-K: per seed +0.0146, +0.0244, +0.0158; mean +0.0183 [+0.0041, +0.0333]; McNemar p 0.088, 0.0017, 0.06; **supported**
- **T-P3** R-KN coverage at tau = 0.95 lies within [0.71, 0.86] for every seed: coverage 0.781, 0.788, 0.762; **supported**

## Arms

| Arm | Role | Words scored | Top-1 | Tie-averaged | vs R-K | McNemar p | Gate coverage | Accepted accuracy |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| R-K | reference | — | 0.942 | 0.945 | — | — | — | — |
| R-N-seed7 | confirmatory | alone | 0.926 | 0.926 | -0.016 | 0.15 | — | — |
| R-KN-seed7 | confirmatory | alone | 0.956 | 0.956 | +0.015 | 0.088 | 0.781 | 0.994 |
| R-N-seed11 | confirmatory | alone | 0.935 | 0.935 | -0.006 | 0.63 | — | — |
| R-KN-seed11 | confirmatory | alone | 0.966 | 0.966 | +0.024 | 0.0017 | 0.788 | 0.995 |
| R-N-seed19 | confirmatory | alone | 0.923 | 0.923 | -0.018 | 0.1 | — | — |
| R-KN-seed19 | confirmatory | alone | 0.957 | 0.957 | +0.016 | 0.06 | 0.762 | 0.995 |
| R-N-seed7-in-sentence | descriptive | in sentence | 0.915 | 0.915 | -0.027 | 0.021 | — | — |
| R-KN-seed7-in-sentence | descriptive | in sentence | 0.954 | 0.954 | +0.012 | 0.2 | 0.776 | 0.997 |
| R-N-seed11-in-sentence | descriptive | in sentence | 0.903 | 0.903 | -0.039 | 0.0011 | — | — |
| R-KN-seed11-in-sentence | descriptive | in sentence | 0.948 | 0.948 | +0.006 | 0.58 | 0.778 | 0.995 |
| R-N-seed19-in-sentence | descriptive | in sentence | 0.890 | 0.890 | -0.051 | 4.7e-05 | — | — |
| R-KN-seed19-in-sentence | descriptive | in sentence | 0.939 | 0.939 | -0.002 | 0.9 | 0.772 | 0.987 |
| R-N-PB | descriptive | alone | 0.833 | 0.833 | -0.108 | 8.9e-15 | — | — |
| R-KN-PB | descriptive | alone | 0.922 | 0.922 | -0.019 | 0.056 | 0.658 | 0.993 |

## Per rule (top-1)

| Rule | Examples | R-K | R-N-seed7 | R-N-seed11 | R-N-seed19 | R-KN-seed7 | R-KN-seed11 | R-KN-seed19 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SDH-001 | 503 | 0.942 | 0.899 | 0.915 | 0.901 | 0.938 | 0.956 | 0.946 |
| SDH-002 | 7 | 0.857 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| SDH-003 | 53 | 0.906 | 0.962 | 0.962 | 0.925 | 1.000 | 1.000 | 0.962 |
| SDH-004 | 49 | 1.000 | 1.000 | 1.000 | 0.959 | 1.000 | 1.000 | 1.000 |
| SDH-005 | 101 | 0.980 | 0.990 | 0.990 | 0.990 | 0.990 | 0.980 | 0.980 |
| SDH-006 | 44 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| SDH-013 | 14 | 0.500 | 0.786 | 0.714 | 0.786 | 0.786 | 0.786 | 0.786 |
| SDH-014 | 8 | 0.750 | 0.625 | 0.875 | 0.750 | 1.000 | 1.000 | 1.000 |
| SDH-015 | 4 | 0.750 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| SDH-016 | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| SDH-017 | 24 | 1.000 | 1.000 | 0.958 | 1.000 | 1.000 | 1.000 | 1.000 |
| SDH-018 | 12 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| UNSUPPORTED | 1 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
