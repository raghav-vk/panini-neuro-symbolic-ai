# Quick Start

The **development pipeline runs on CPU**. Rules remain drafts, and silver or
synthetic results are not a scholarly validation of Sanskrit grammar. Current
results are in [the silver DCS report](reports/dcs-silver-v3/SUMMARY.md).

## 1. Install and Test

Use Python 3.12 for the tested training environment. Standard-library data
tools also work on Python 3.10+. No GPU or pretrained model download is needed.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -r requirements-train.txt
.venv/bin/python -m pytest tests -q
```

The full environment includes the CPU training/checkpoint round-trip test.
Without PyTorch, that test is explicitly skipped; other tests still run.

## 2. Review the Draft Rules

```sh
.venv/bin/python scripts/build_development_rules.py
.venv/bin/python scripts/validate_rules.py data/rules/development_sandhi.jsonl
```

Start with [REVIEW_PACKET.md](data/reviews/REVIEW_PACKET.md). It covers twelve vowel,
two consonant, two nasal, one visarga and one non-application encoding. These
are 18 operational cases, not 18 complete sutras or coverage of all sandhi.
Copy the JSONL review template to a separate working file before recording
decisions; rebuilding replaces generated templates, never scholarly reviews.

## 3. Convert and Annotate DCS

With the verified archive at `datasets/DCS_pick.zip`:

```sh
.venv/bin/python scripts/convert_dcs.py --output data/processed/my-dcs
.venv/bin/python scripts/build_review_page.py data/processed/my-dcs/boundary_review.jsonl
```

Open `data/processed/my-dcs/review.html` in a browser. The worksheet runs locally
and offers export/resume without uploading data. Export your work before closing.
The existing full conversion and worksheet are in `data/processed/dcs/` on
the development machine. They are intentionally not committed.

The decoder does not execute pickle objects. It preserves original sentences,
lemmas and morphology codes. `dcs_chunks` is the flattened lemma sequence,
not a second list of inflected surface words. Reviewers must supply the actual
left/right inflected forms, exact observed span, tags, and external-boundary
confirmation. The initial 200-item queue is a convenience sample, not a gold test set.
Source offsets in this worksheet refer to the IAST sentence. On ingest the
record is converted to SLP1, the internal scheme (protocol amendment 0.6), and
the offsets with it. The exact span is kept as `source_surface`, and only
whitespace is removed for the model's `surface`; punctuation is not silently
discarded.

### Silver DCS Examples

To derive real examples automatically from the converted sentences:

```sh
.venv/bin/python scripts/extract_dcs_boundaries.py \
  --sentences data/processed/my-dcs/sentences.jsonl --output data/processed/my-silver
```

The extractor keeps only boundaries whose inflected forms are fully determined:
an indeclinable opening a whitespace chunk, joined to a non-verbal word that
runs to the chunk end. It reads the fused junction from the attested surface and
the gold words from DCS lemmas, never from the sandhi rules, so candidate recall
remains a measurement. `report.json` counts every rejection reason and junction
type; `review_sample.jsonl` is a stratified sample for expert audit. These are
silver data, not expert-reviewed gold.

## 4. Prepare All Holdouts

For the synthetic engineering test:

```sh
.venv/bin/python scripts/prepare_experiment.py --output data/processed/my-experiment
```

For independent-corpus work, use `--examples /path/to/reviewed_boundaries.jsonl`
instead, or `--silver-examples data/processed/my-silver/examples.jsonl` for
silver DCS data. Pending or unaligned annotations are rejected. Missing candidate
coverage is retained as a failure, not silently removed. Freeze the reviewed
rule snapshot with `--rules` for both preparation and inference.

Preparation saves candidates, proof traces, file hashes, counts and overlap
audits for source-random, pair, strict-lemma and right-word splits. The strict split also
checks annotated context lemmas; cross-partition source groups go to `mixed`.
Synthetic lemma identifiers denote nonce stems, not real Sanskrit lemmas.

Optional external lexicon (research use only; Monier-Williams data in the
kosha is CC BY-NC-SA 3.0, see `THIRD_PARTY_NOTICES.md`):

```sh
.venv/bin/pip install -r requirements-lexicon.txt
.venv/bin/python scripts/fetch_vidyut_data.py
.venv/bin/python scripts/annotate_lexicon.py \
  --data data/processed/my-experiment --output data/processed/my-experiment-kosha
```

Then pass `--external-lexicon` to `run_experiment.py` with the annotated
directory.

All output directories must be new. Use a new name for each rerun so existing
reviews, frozen datasets and checkpoints are never overwritten accidentally.

## 5. Train and Measure

```sh
.venv/bin/python scripts/run_experiment.py \
  --data data/processed/my-experiment --output runs/my-experiment --ablations
```

Defaults: five seeds, three epochs, two layers, width 64, four attention heads,
UTF-8 byte inputs, and CPU. `--baselines-only` needs no PyTorch.
`--width 128 --layers 4` selects the larger research architecture.
`--train-limit 250` supports training-only learning-curve subsampling; report
the actual retained count if fewer examples are available.

Read `SUMMARY.md` and `results.json` in the output folder. Scores include
candidate recall, top-1/top-3, MRR, per-rule/family counts, macro rule accuracy,
dev-selected abstention, parameter count, runtime and cumulative process RAM.
Checkpoints and per-item predictions are saved. Empty synthetic contexts
cannot demonstrate contextual disambiguation or meaningful context ablations.

Independently replay the candidates and regenerate every reported metric:

```sh
.venv/bin/python scripts/verify_run.py --data data/processed/my-experiment --run runs/my-experiment
```

## 6. Try an Analysis

```sh
.venv/bin/python scripts/predict_sandhi.py 'devālaya'
.venv/bin/python scripts/predict_sandhi.py 'devālaya' \
  --checkpoint runs/my-experiment/strict_lemma-tiny_full-7.pt
```

Inspect the candidate words and their reconstructed surface, not just the
score. Open inversion can produce nonwords: there is no test-derived
dictionary filter or morphological analyzer. Checkpoints trained with
`--external-lexicon` look candidates up in the kosha given by `--kosha`. `--tags` supplies grammatical prerequisites explicitly. An unsupported
surface yields no candidates; a checkpoint may also abstain at its saved
development-selected threshold. No missing forms are silently concatenated.

## 7. Verify

Before a release, check every gate in protocol section 18 from a clean
checkout. The DCS archive audit needs the extracted archive:

```sh
unzip -q datasets/DCS_pick.zip -d datasets/
.venv/bin/python scripts/audit_dcs_archive.py --sample 1000
.venv/bin/python scripts/validate_rules.py --expected-count 25 --publication-ready
```

The publication gate fails until 25 reviewed rules exist.

## What Counts as Success?

Passing code tests and complete synthetic candidate recall show that the
pipeline is mechanically consistent. They do not show that its rules are
correct, exhaustive, or that the Transformer understands Sanskrit. Next,
independent reviewers must approve the rules and actual corpus boundaries.
Only a frozen, sufficiently sized reviewed benchmark can support the paper's
research claims. See [EXPERIMENT_PROTOCOL.md](docs/EXPERIMENT_PROTOCOL.md).
