# Experiment Utilities

## Complete Development Workflow

See [Quick Start](../QUICKSTART.md) for commands in execution order.

| Utility | Purpose |
| --- | --- |
| `build_development_rules.py` | Generate 18 narrow draft rules, negative checks and the expert review packet |
| `convert_dcs.py` | Verify archive identity, decode primitive data without pickle execution, quarantine failures |
| `extract_dcs_boundaries.py` | Align DCS lemmas to attested surfaces as silver external vowel-sandhi examples, without consulting rules |
| `prepare_expert_review.py` | Write the committed silver-sample review items, overlap IDs, uncovered examples and grammarian checks to `data/reviews/` |
| `build_review_page.py` | Create a local browser worksheet: boundary annotation, or `--mode verify` for checking proposed splits |
| `validate_review.py` | Check a reviewer's answers file or rule decision file before it is committed |
| `prepare_experiment.py` | Admit synthetic, silver DCS or reviewed examples, build four holdouts and forward-certified candidates |
| `run_experiment.py` | CPU baselines, five-seed ranker training, ablations, checkpoint and metric artifacts |
| `compare_paired.py` | Paired bootstrap and per-seed McNemar comparison of saved test predictions against a baseline |
| `fetch_vidyut_data.py` | Download and verify the pinned Vidyut data release (optional external lexicon; non-commercial terms) |
| `annotate_lexicon.py` | Copy prepared splits and flag candidate words found in the Vidyut kosha, for `--external-lexicon` |
| `predict_sandhi.py` | Inspect candidates/proofs and optional checkpoint-based selection or abstention; input and output in IAST by default, `--scheme slp1` otherwise |
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

    unzip -q datasets/DCS_pick.zip -d datasets/
    python3 scripts/audit_dcs_archive.py --sample 100

The extracted copy is needed only for this audit; conversion reads the ZIP.

This command checks local integrity only. Provenance and licensing for the
exact archive are recorded separately in `datasets/dcs_source_manifest.json`;
neither artifact verifies annotation correctness.

Use `--skip-manifest-check` only for an explicitly documented diagnostic of a
different archive; it is not valid for a frozen experiment.


