# Project Pāṇini: A Neuro-Symbolic Sanskrit Sandhi Experiment

This repository builds a small, reproducible neuro-symbolic system for
Sanskrit sandhi splitting. Typed rules derived from Pāṇini's grammar generate
candidate analyses with proof traces, and a neural model ranks them. The
first paper targets external vowel-sandhi splitting.

The long-term aim is a Sanskrit-centred engine with interfaces to Indian
languages, then English and other languages. The first paper claims none of
that. It is not a complete Sanskrit language model, a translator or a
universally correct grammar engine.

## Status

**Working research system, not publication-ready.** Rules and data are drafts
or silver; no expert review is complete yet.

Main results so far, all on held-out test data
([how the system got here](docs/VERSIONS.md)):

| Version | Finding |
| --- | --- |
| 0.4 | A linear model over word counts, rule frequency and the Vidyut kosha picks the right split for 0.943 of unseen right-hand words; a byte Transformer reaches 0.897 ([report](reports/dcs-silver-v3/SUMMARY.md)) |
| 0.9 | Adding word scores from a Sanskrit-pretrained encoder to the kosha gains +0.018 [+0.004, +0.033]; the scores alone do not replace the kosha ([report](reports/pretraining-v1/test/TEST_RESULTS.md)) |
| 0.9 | Answering only at confidence of at least 0.95 covers 76% to 79% of items, with 99.4% to 99.5% of those answers right |
| 0.8 | For whole-word morphology, pretraining helps the tagger (+0.061), but beating the kosha baseline did not hold ([report](reports/rlcd-stage3/test/TEST_RESULTS.md)) |

**Now (0.10):** a community review pilot is open until 1 December 2026.
[Take part](https://raghav-vk.github.io/panini-neuro-symbolic-ai/).

Implemented:

- 18 draft rules across five families, with negative checks and a review
  packet.
- Inverse candidate generation with forward proof traces and abstention.
- Non-executing DCS conversion: 441,722 sentences, and 39,838 silver
  vowel-sandhi boundaries extracted without consulting the rules.
- Four holdouts, baselines, a byte Transformer ranker, an optional external
  lexicon, ablations and paired significance tests.
- Self-supervised pretraining on decontaminated Sanskrit text.
- A calibrated confidence gate for abstention.
- RLCD: a clause schema, a constraint layer before Vidyut derivation, and a
  morphological tagger on DCS CoNLL-U.
- A reproducible 148-record all-sandhi sūtra source corpus.
- A community review worksheet with hidden controls, sealed hand-ins and
  automatic scoring.

Still required:

- Expert review of the rules, a silver sample and an independent gold test
  set.
- Phase 2 data with inflected left words.
- The 25-rule reviewed inventory for the publication gate.
- Comparison with prior Sanskrit segmentation work.
- The studies still listed as not run in the manuscript (§11.5).

The full list, with what each step waits on, is in the
[roadmap](docs/ROADMAP.md).

## How It Works

    fused surface form, with context
                |
                v
    typed symbolic candidate generator
                |
                v
    rule-licensed candidates with proof traces
                |
                v
    ranker: symbolic features and a neural scorer
                |
                v
    chosen analysis, or an explicit abstention

"Verified" means consistent with the encoded and tested rule subset. It does
not mean complete Sanskrit grammatical or semantic correctness.

## Getting Started

See [QUICKSTART.md](QUICKSTART.md) for the full workflow, from installation
and tests through DCS conversion, silver extraction, splits and training to
prediction. In short:

    python3.12 -m venv .venv
    .venv/bin/python -m pip install -r requirements.txt -r requirements-train.txt
    .venv/bin/python -m pytest tests -q

## Data

- **DCS_pick** (Krishna et al. 2017, Zenodo, CC BY 4.0) supplies the
  sentences. Its provenance and checksums are in
  `datasets/dcs_source_manifest.json`.
- **ashtadhyayi-com/data** supplies the sūtra source corpus, under free,
  non-commercial terms.
- **Vidyut kosha** is an optional external lexicon. It contains
  CC BY-NC-SA 3.0 Monier-Williams data and is never committed.

All Sanskrit is stored and processed in SLP1. IAST is used only for display,
review worksheets and the paper (protocol amendment 0.6).

See `THIRD_PARTY_NOTICES.md`. Raw corpora, generated splits and runs are
ignored by Git. Reported results are kept in `reports/`.

## Documentation

- [docs/README.md](docs/README.md): **start here**, with the building blocks.
- [docs/VERSIONS.md](docs/VERSIONS.md): how the system evolved, 0.1 to 0.10.
- [docs/ROADMAP.md](docs/ROADMAP.md): what is done, next, and waiting.
- [docs/paper/panini-neuro-symbolic-ai.md](docs/paper/panini-neuro-symbolic-ai.md): working
  paper.
- [docs/EXPERIMENT_PROTOCOL.md](docs/EXPERIMENT_PROTOCOL.md): study design,
  amendments and release gates.
- [docs/PRETRAINING_PLAN.md](docs/PRETRAINING_PLAN.md): adopted pretraining
  plan.
- [docs/guides/RULE_AUTHORING_GUIDE.md](docs/guides/RULE_AUTHORING_GUIDE.md): authoring and
  reviewing rules.
- [docs/ALL_SANDHI_DATASET.md](docs/ALL_SANDHI_DATASET.md): the all-sandhi
  source corpus.
- [datasets/README.md](datasets/README.md): corpus and split requirements.
- [scripts/README.md](scripts/README.md): every script.

## Collaboration

The most valuable collaborators now are:

- Pāṇinian grammar reviewers, for rule interpretation, exceptions and
  precedence.
- Sanskrit annotators, for the silver sample and the gold test set.
- NLP researchers, for pretraining, baselines and evaluation.

Engineering contributors must not mark a rule `expert_reviewed` without the
named reviewer's approval.

## Research Integrity

- Do not report unmeasured values.
- Do not tune on the test set. Record decisions in the protocol before test
  runs.
- Do not compare scores across incompatible datasets as direct baselines.
- Do not unpickle unverified corpus files.
- Do not call automatically extracted or generated examples attested or gold.
- Do not describe subset compliance as perfect Sanskrit.

## License

Project code and original documentation are licensed under the Apache License
2.0; see LICENSE and NOTICE. Third-party data and source material keep their
own terms; see THIRD_PARTY_NOTICES.md. In particular, ashtadhyayi-com material
may be used only in products offered free of charge, and not commercially.
