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

**Working experiment, not publication-ready.** Rules and data are drafts or
silver; nothing has been expert reviewed yet.

Current results, on silver DCS data with a holdout of unseen right-hand words
([report](reports/dcs-silver-v3/SUMMARY.md)):

| | Test (tie-averaged top-1) |
| --- | ---: |
| Gold split among the rule-generated candidates | 99.9% |
| Best system: linear model over word counts, rule frequency, the Vidyut kosha and a short-vowel preference | 0.946 |
| Previous best baseline (frequency, short-vowel tie-break) | 0.831 |
| Byte-level Transformer with the same features | 0.897 |

The neural ranker does not yet beat the symbolic features on unseen words.
The next step is self-supervised pretraining on decontaminated Sanskrit text
([plan](docs/PRETRAINING_PLAN.md), protocol amendment 0.5).

Implemented:

- 18 draft rules across five families, with negative checks and a review
  packet.
- Inverse candidate generation with forward proof traces and abstention.
- Non-executing DCS conversion: 441,722 sentences.
- Rule-independent extraction of 39,838 silver vowel-sandhi boundaries.
- Four holdouts: source-random, exact pair, both-lemma strict, and right-word
  strict.
- Baselines, a byte Transformer ranker, a lexical feature head, an optional
  external lexicon, a residual variant, ablations and paired significance
  tests.
- A reproducible 148-record all-sandhi sūtra source corpus.

Still required:

- Expert review of the rules, a silver sample and an independent gold test
  set.
- The pretraining study.
- Phase 2 data with inflected left words.
- The 25-rule reviewed inventory for the publication gate.
- Comparison with prior Sanskrit segmentation work.
- Results in place of every TBD in the manuscript.

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

See `THIRD_PARTY_NOTICES.md`. Raw corpora, generated splits and runs are
ignored by Git. Reported results are kept in `reports/`.

## Documentation

- [docs/README.md](docs/README.md): documentation map.
- [docs/panini-neuro-symbolic-ai.md](docs/panini-neuro-symbolic-ai.md): working
  paper.
- [docs/EXPERIMENT_PROTOCOL.md](docs/EXPERIMENT_PROTOCOL.md): study design,
  amendments and release gates.
- [docs/PRETRAINING_PLAN.md](docs/PRETRAINING_PLAN.md): adopted pretraining
  plan.
- [docs/RULE_AUTHORING_GUIDE.md](docs/RULE_AUTHORING_GUIDE.md): authoring and
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
