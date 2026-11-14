# RLCD Stage 1: Dev Results

**Dev only.** The right-word holdout test set was not read. Settings were
pre-registered in `docs/RLCD_TRANSITION_PLAN.md` (stage 1, commit 7d82b6b)
before the analysis ran, and adopted in protocol amendment 0.7 (section
11.5). Generated tables: `SUMMARY.md`. Full numbers: `calibration.json`.
Figure: `calibration_figure.pdf` (`scripts/plot_calibration.py`; the same
figure is in `docs/paper/artifacts/rlcd_stage1_calibration.pdf`). Code: `scripts/eval_calibration.py` and
`src/panini/calibration.py`. Run on 2026-11-14 on the project Mac.

These are observed results from the real model outputs. They replace nothing
in the paper: the earlier simulated figures (`*_simulated.*`) were never
results.

## Reproduction check

For each of seeds 7, 11 and 19, the per-word discriminator evaluator gives
exactly the counts (1,583 attested and 271 altered words) and both
accuracies recorded at the end of pretraining. A unit test also checks the
evaluator against `pretraining.evaluate`.

## Findings

**1. The ranker's confidence is already calibrated; temperature scaling adds
nothing.** The H-P2 linear ranker's raw top-candidate probability has an
equal-mass ECE of 0.013 to 0.029 across the three seeds. It is slightly
underconfident: mean confidence 0.935 to 0.943 against accuracy 0.950 to
0.956. The cross-fitted temperatures are close to 1 (0.90 to 1.06), and ECE,
Brier and NLL do not change beyond their intervals. The figure shows where
the remaining error sits: the least confident tenth of items (confidence about
0.58) is right 0.67 to 0.77 of the time. Below 0.9, the ranker is
underconfident.

**2. The discriminator, asked as a Noul, is calibrated too.** Its
P(attested) has an equal-mass ECE of 0.001 to 0.003 raw (equal-width 0.004 to
0.007), with temperatures again near 1. Accuracy here is top-label over all
1,854 words (0.983). Most of these words are attested, so this is not the
balanced accuracy of 0.955 reported in pretraining.

**3. Abstention is where the confidence pays off.** Errors gather at low
confidence:

| Operating point | Coverage | Accuracy of accepted items |
| --- | --- | --- |
| Accept everything | 1.00 | 0.950 to 0.956 |
| Best 90% of items | 0.90 | 0.976 to 0.983 |
| τ = 0.85 | 0.85 to 0.87 | 0.980 to 0.986 |
| τ = 0.95 | 0.77 to 0.81 | 0.991 to 0.996 |

So the system can state which fifth of its answers to send for expert review,
and be right more than 99% of the time on the rest.

**4. Routing to a three-seed ensemble barely helps here.** The ensemble
reaches 0.957, against 0.950 to 0.956 for a single seed, a gain inside the
intervals. The gate does recover all of it while running the ensemble on only
13 to 23% of items (τ = 0.85 or 0.95). The learned cost-aware threshold does
the same at 3 to 4.5% routed. At costs of 0.02 and 0.05 it earns more than
the fixed thresholds; at 0.01 the two are tied. The reward differences are in
the fourth decimal, because there is little gain to route for. This is an
offline contextual bandit with full-information feedback. It shows the
mechanism works, not that RL improves accuracy here.

**5. Compute.** One 4,937,220-parameter encoder scores all 988 dev examples
(8,484 candidates) in about 1.2 s on MPS (about 1.2 ms per example) and about
5.9 s on CPU (about 6 ms per example). Each measurement is 3 runs; a second
measurement gave 1.22 to 1.23 s and 5.89 to 5.90 s.

## Reading for the paper

The tangible stage 1 claim is calibrated confidence with selective
prediction. A 4.94M-parameter encoder plus a symbolic candidate generator
gives confidence that matches its accuracy without post-hoc fitting. A single
threshold trades coverage for accuracy predictably, so uncertain items can be
routed to a reviewer. The ensemble-routing result is reported as a negative
finding.

## Caveats

- **Dev only, and dev has been used before** (pretraining plan, step 4).
  Using τ or c on test needs a frozen amendment and a disclosed fourth use of
  the right-word holdout test set.
- **Small error counts.** Each seed has 43 to 49 errors in 988 examples, so
  ECE intervals are wide relative to their values.
- **Clusters are almost single items.** The 988 examples come from 984 source
  groups, so the cluster bootstrap is close to an item bootstrap.
- **The discriminator's task is narrow:** single-word vowel-length swaps at a
  15% corruption rate. Its calibration says nothing about other kinds of error.
- **The fast path is not purely neural.** The ranker combines the neural
  score with the kosha and rule features (H-P2). The kosha-free H-P1 variant
  was not part of this pre-registration.
