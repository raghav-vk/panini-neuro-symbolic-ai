# Results by Version

Every result in the project, mapped to the version that produced it
([docs/VERSIONS.md](../docs/VERSIONS.md)). Folder names keep their original
suffixes (`-v1`, `-v2`, `-v3`) because frozen test records name these
paths. The suffixes count data generations, not versions.

**Dev** results can be rerun. **Test** results come from one frozen run;
that test part is spent.

| Version | Folder | Start with | Kind |
| --- | --- | --- | --- |
| 0.1 | [development-v1/](development-v1/) | [SUMMARY.md](development-v1/SUMMARY.md) | Synthetic smoke run |
| 0.3 | [dcs-silver-v2/](dcs-silver-v2/) | [SUMMARY.md](dcs-silver-v2/SUMMARY.md) | Test (five seeds) |
| 0.4 | [dcs-silver-v3/](dcs-silver-v3/) | [SUMMARY.md](dcs-silver-v3/SUMMARY.md) | Test (five seeds) |
| 0.5 | [pretraining-v1/](pretraining-v1/) | [DEV_RESULTS.md](pretraining-v1/DEV_RESULTS.md) | Dev |
| 0.7 | [rlcd-stage1/](rlcd-stage1/) | [DEV_RESULTS.md](rlcd-stage1/DEV_RESULTS.md) | Dev: calibration and abstention |
| 0.7 | [dcs-conllu/](dcs-conllu/) | [PROFILE.md](dcs-conllu/PROFILE.md) | Data profile and the stage 3 split |
| 0.7 | [rlcd-stage3/](rlcd-stage3/) | [SUMMARY_TAGGER.md](rlcd-stage3/SUMMARY_TAGGER.md) | Dev: tagger, joint and Platt calibration |
| 0.8 | [rlcd-stage3/test/](rlcd-stage3/test/) | [TEST_RESULTS.md](rlcd-stage3/test/TEST_RESULTS.md) | Test (one frozen run) |
| 0.9 | [pretraining-v1/test/](pretraining-v1/test/) | [TEST_RESULTS.md](pretraining-v1/test/TEST_RESULTS.md) | Test (one frozen run) |
| 0.10 | `review-pilot/pilot-1/` (after 1 December 2026) | — | Pilot, written automatically |

Versions 0.2 (a split design) and 0.6 (the switch to SLP1) have no folder of
their own; their evidence is in the protocol, sections 9.5 and 11.4.

## Inside the Mixed Folders

Two folders hold work from more than one version:

- **pretraining-v1/**
  - 0.5 dev: `DEV_RESULTS.md`, `corpus_audit.json`,
    `pilot_S_1000_steps.json`, `pretrain_S_*.json`.
  - 0.9 test: `frozen_test_settings.json` and `test/`.
  - `calibration_*_simulated.*` are simulated figures from the RLCD review,
    not results (protocol §11.5).
- **rlcd-stage3/**
  - 0.7 dev: `tier1_manifest.json`, `TAGGER_DEV_RESULTS.md`,
    `SUMMARY_TAGGER.md`, `tagger_dev.json`, `JOINT_CALIBRATION*`, `joint_calibration.json`,
    `PLATT_CALIBRATION*`, `platt_calibration.json`.
  - 0.8 test: `frozen_test_settings.json` and `test/`.

The paper's copies of figures are in `docs/paper/artifacts/`.
