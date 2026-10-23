# Experiment Utilities

## Complete Development Workflow

See [Quick Start](../QUICKSTART.md) for commands in execution order.

| Utility | Purpose |
| --- | --- |
| `build_development_rules.py` | Generate 12 narrow draft rules, negative checks and the expert review packet |
| `convert_dcs.py` | Verify archive identity, decode primitive data without pickle execution, quarantine failures |
| `extract_dcs_boundaries.py` | Align DCS lemmas to attested surfaces as silver external vowel-sandhi examples, without consulting rules |
| `build_review_page.py` | Create a local browser worksheet for boundary annotation and JSONL export |
| `prepare_experiment.py` | Admit synthetic, silver DCS or reviewed examples, build three holdouts and forward-certified candidates |
| `run_experiment.py` | CPU baselines, five-seed ranker training, ablations, checkpoint and metric artifacts |
| `predict_sandhi.py` | Inspect candidates/proofs and optional checkpoint-based selection or abstention |
| `verify_run.py` | Recompute metrics from saved scores, check frozen hashes and independently replay test proofs |
| `summarize_development.py` | Retain compact measured evidence and source hashes without raw corpus files |
| `check_review.cjs` | Optional Playwright desktop/mobile worksheet navigation and export QA |

Data/run tools require new output directories and do not overwrite prior
reviews or experiments. Rule rebuilding only replaces generated templates.

## build_sandhi_sutra_corpus.py

Builds the deterministic all-sandhi source-candidate corpus from a pinned
checkout of `ashtadhyayi-com/data`:

    PYTHONDONTWRITEBYTECODE=1 python3 \
      scripts/build_sandhi_sutra_corpus.py \
      --source-dir vendor/ashtadhyayi-data

The default expected commit is
`51bff9fb38c6f571b4a2bc8499d97576f00ffcce`. The builder selects the union of
the configured Siddhānta Kaumudī and Laghu Siddhānta Kaumudī sandhi chapters,
validates IDs and source types, emits canonical JSONL, and records its SHA-256
and counts in a manifest.

The output is a scholarly review queue, not 148 automatically executable
rules. See `docs/ALL_SANDHI_DATASET.md`.

## validate_rules.py

Validates the typed JSONL rule inventory.

Draft structure:

    python3 scripts/validate_rules.py

Publication gate:

    python3 scripts/validate_rules.py \
      --expected-count 25 \
      --publication-ready

## audit_dcs_archive.py

Verifies the ZIP against the frozen source manifest, compares ZIP and extracted
pickle records, and samples pickle opcodes without instantiating serialized
objects.

    python3 scripts/audit_dcs_archive.py --sample 100

This command checks local integrity only. Provenance and licensing for the
exact archive are recorded separately in `datasets/dcs_source_manifest.json`;
neither artifact verifies annotation correctness.

Use `--skip-manifest-check` only for an explicitly documented diagnostic of a
different archive; it is not valid for a frozen experiment.

## build_lexical_holdout.py

Partitions normalized lemmas before examples and writes train, dev, test,
mixed, and manifest files.

    python3 scripts/build_lexical_holdout.py \
      input-examples.jsonl \
      output-directory

Input records require example_id, left_lemma, right_lemma, and rule_id.

## Legacy Toy Script

`generate_toy_dataset.py` belongs to the original broad language-model
proposal. Its output is retained only as project history and is excluded from
the sandhi experiment. Do not use it for training, evaluation, or publication
claims.
