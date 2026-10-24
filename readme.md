# Project Pāṇini: A Focused Neuro-Symbolic Sandhi Experiment

This repository is developing a small, reproducible neuro-symbolic research
system for Sanskrit sandhi. The source layer now covers candidate sūtras across
vowel, consonant, visarga, nasal/anusvāra, non-application, and supporting
material. A runnable development pipeline now exercises 18 narrow draft
encodings across five families. The planned scholarly benchmark remains
external vowel-sandhi splitting under independently reviewed rules and data.

The project no longer claims to build a complete Sanskrit language model,
English-to-Sanskrit translator, or universally correct grammar engine in its
first paper.

## Status

**Working experiment, not publication-ready.**

Implemented:

- Strictly validated JSONL contract for typed sandhi rules.
- Twelve cross-family draft rules, 24 positive probes, 32 negative checks,
  and a source-linked expert review packet; the old EVS seed is retained.
- Inverse candidates with priority-aware forward proof traces and abstention.
- Source-grouped, pair, and strict lemma holdouts with context/source audits.
- Non-executing DCS decoder: 441,722 converted records, 13 quarantined records.
- A 200-item DCS boundary review queue and local browser annotation worksheet.
- Symbolic-order, frequency, character-bigram, and tiny Transformer rankers.
- Five-seed CPU smoke experiments, no-rule/no-context ablations, saved
  checkpoints, predictions, metrics and resource measurements.
- Verified DCS archive provenance, CC BY 4.0 license, and checksums.
- Reproducible 148-record all-sandhi sūtra candidate corpus, including 108
  operative candidates and 40 supporting records.
- Research protocol, authoring guide, and expanded working manuscript.
- Automated test suite for rules, splits, archive safety, and source-corpus
  reproducibility.

Still required:

- Author and independently review the complete 25-rule inventory.
- Obtain authoritative confirmation of the ashtadhyayi-com data license.
- Expert-screen and operationalize the broader all-sandhi source candidates.
- Have qualified reviewers complete the boundary and rule worksheets.
- Extend single-step encodings to the reviewed inventory and derivation chains.
- Run the independent-corpus study, unconstrained generative comparison,
  data-efficiency curves, and blinded expert evaluation.
- Replace every TBD in the manuscript from saved experiment artifacts.

## Research Question

Can a roughly one-million-parameter contextual encoder rank external
vowel-sandhi analyses better than symbolic and frequency baselines when test
lemmas never occur in training?

The intended division of labor is:

    observed surface and context
                |
                v
    typed symbolic candidate generator
                |
                v
    valid candidates plus proof traces
                |
                v
    tiny contextual Transformer ranker
                |
                v
    verified candidate or explicit abstention

The word verified means compliant with the encoded and tested subset. It does
not mean complete Sanskrit grammatical or semantic correctness.

## Quick Start

For the complete runnable workflow, use [QUICKSTART.md](QUICKSTART.md).
The [development results](reports/development-v1/SUMMARY.md) are engineering
checks on nonce strings, not measured Sanskrit accuracy. The
[review packet](data/reviews/REVIEW_PACKET.md) is ready for collaborators.

The current rule and data utilities use the Python standard library. Install
pytest for tests:

    python3 -m pip install "pytest>=7.4"

Run the test suite:

    python3 -m pytest tests -q

Validate draft rule structure:

    python3 scripts/validate_rules.py

The publication gate is expected to fail until all 25 rules are reviewed:

    python3 scripts/validate_rules.py \
      --expected-count 25 \
      --publication-ready

Audit the local DCS archive without unpickling records:

    python3 scripts/audit_dcs_archive.py --sample 100

## Rule Authoring

Rules are stored one JSON object per line in:

    data/rules/external_vowel_sandhi.jsonl

The seed EVS-001 record is a format example, not an approved scholarly claim.
Each final rule needs pinned sources, explicit conditions, precedence,
positive examples, a counterexample, and independent review.

See docs/RULE_AUTHORING_GUIDE.md for the collaborative workflow and
data/schemas/sandhi-rule.schema.json for the formal contract.

## Strict Lexical Holdout

An exact-pair holdout is not enough: the model may have seen both words with
other partners. The strict split assigns each normalized lemma to exactly one
partition before assigning examples. An example is retained only when both
lemmas belong to the same partition; cross-partition examples go to a mixed
audit file.

Given a derived examples file:

    python3 scripts/build_lexical_holdout.py \
      data/processed/examples.jsonl \
      data/processed/strict-lexical

The output manifest records the input hash, seed, split counts, mixed count,
per-rule coverage, and zero-overlap assertions.

## Dataset Status

The pinned all-sandhi source corpus contains 148 sūtra candidates selected by
an explicit chapter-union criterion. Of these, 108 are source-labeled
operative candidates and 40 supply definitions, scope, or interpretive
support. They are not yet 148 executable rules. See
docs/ALL_SANDHI_DATASET.md and the machine-readable manifest in data/sources/.

The local DCS_pick archive contains 441,735 unique pickle data records plus
two ancillary Python files. All data records are extracted. A 100-record
opcode sample passed non-executing inspection.

These are sentence analyses, not 441,735 ready-to-train external-sandhi
examples. The local ZIP matches Zenodo's DCS_pick artifact by filename, size,
and MD5; Zenodo licenses the record under CC BY 4.0. The verified record is in
datasets/dcs_source_manifest.json. Raw corpora and generated splits are
intentionally ignored by Git.

The original 53-example translation toy dataset is retained only as project
history and is excluded from the proposed paper.

## Documentation

- docs/README.md: canonical documentation map and scope boundary.
- docs/panini-neuro-symbolic-ai.md: working research paper.
- docs/ALL_SANDHI_DATASET.md: broad source selection, reproduction, expert
  operationalization, and tests.
- docs/EXPERIMENT_PROTOCOL.md: frozen-study plan and release gates.
- docs/RULE_AUTHORING_GUIDE.md: how to author and review the 25 rules.
- docs/approach-to-solution.md: focused system design and implementation order.
- datasets/README.md: corpus, derived-example, and split requirements.
- COMPILE_AND_TEST.md: test layers and expected outcomes.

Retired broad architecture and issue-roadmap documents remain available in Git
history rather than beside the active research specification.

## Collaboration

The most valuable collaborators now are:

- Pāṇinian grammar reviewers for rule interpretation, exceptions, and
  precedence.
- Sanskrit corpus annotators for boundary alignment and adjudication.
- NLP researchers for baselines, statistical evaluation, and error analysis.
- Engineers for the candidate lattice, tiny ranker, and reproducible runs.

Engineering contributors must not mark a rule expert_reviewed without the
named reviewer's approval.

## Research Integrity

- Do not report unmeasured values.
- Do not tune on the test set.
- Do not compare scores across incompatible datasets as direct baselines.
- Do not directly unpickle unverified corpus files.
- Do not call automatically generated examples attested.
- Do not describe subset compliance as perfect Sanskrit.
- Do not resubmit the paper while result placeholders or unresolved licenses
  remain.

## License

Project code and original documentation are licensed under the Apache
License 2.0; see LICENSE and NOTICE. Third-party data and source material
retain their own terms; see THIRD_PARTY_NOTICES.md. In particular,
ashtadhyayi-com material may only be used in products offered free of charge
and may not be used commercially.
