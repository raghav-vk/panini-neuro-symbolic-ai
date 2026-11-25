# Data by Version

What each data folder holds, which version created it
([docs/VERSIONS.md](../docs/VERSIONS.md)), and whether it is in git.
Folder names keep their original suffixes because scripts and frozen test
records name these paths; the suffixes count generations, not versions.

## In Git

| Folder | Holds | Version |
| --- | --- | --- |
| [rules/](rules/) | Draft typed sandhi rules and negative checks (SLP1) | 0.1; 18 rules in 0.3; SLP1 in 0.6 |
| [sources/](sources/README.md) | The 148-record all-sandhi sūtra source corpus | 0.1 |
| [schemas/](schemas/) | JSON schemas: sandhi rules and sūtra sources (0.1), RLCD clauses (0.7) | 0.1, 0.7 |
| [rlcd/](rlcd/) | Root, stem and frame tables, clause fixtures, provisional acceptance | 0.7 |
| [reviews/](reviews/README.md) | Expert review packets, silver sample and worksheets | Prepared 26 October 2026, after 0.5; SLP1 in 0.6 |
| [reviews/pilot/](reviews/pilot/README.md) | Community review pilot: items, worksheet, round settings | 0.10 |

`reviews/pilot/private/` (answer key and round key) is never committed.

## Rebuilt Locally (git-ignored)

These folders are too large for git or carry licence limits. Scripts rebuild
them; most write a manifest with hashes.

| Folder | Holds | Version | Rebuild with |
| --- | --- | --- | --- |
| `external/vidyut-0.4.0/` | Vidyut data: kosha, dhātupāṭha (non-commercial terms) | 0.4 | `scripts/fetch_vidyut_data.py` |
| `external/dcs-conllu/` | DCS CoNLL-U treebank, pinned commit | 0.7 | `scripts/fetch_dcs_conllu.py` |
| `processed/dcs/` | DCS archive decoded without executing pickle | 0.1 | `scripts/convert_dcs.py` |
| `processed/dcs-smoke/` | A 100-record conversion test | 0.1 | `scripts/convert_dcs.py` |
| `processed/development/`, `development-v1/` | Synthetic development splits | 0.1 | `scripts/prepare_experiment.py` |
| `processed/dcs-silver-v2/` | Silver boundaries, IAST | 0.2 to 0.4 | `scripts/extract_dcs_boundaries.py` |
| `processed/dcs-silver-v2-kosha-splits/` | IAST splits with kosha flags (superseded; see the 0.9 erratum) | 0.4 | `scripts/annotate_lexicon.py` |
| `processed/dcs-silver-slp1/`, `-slp1-splits/`, `-slp1-kosha-splits/` | The SLP1 silver data used from 0.6 on, including the 0.9 test | 0.6 | Not recorded; probably the three scripts above in order |
| `processed/pretrain-v1/` | Pretraining corpora P-A and P-B, dev sentences, audit | 0.5 | `scripts/build_pretraining_corpus.py` |
| `processed/neural-*` | Splits with pretrained word scores (`ctx`: in sentence; `nc`: word alone) | 0.5 | `scripts/annotate_neural_lexicon.py` |
| `processed/rlcd-tier1-v0/` | Generated Tier 1 clauses (not used by the tagger) | 0.7 | `scripts/generate_tier1.py` |
| `processed/dcs-conllu-v1/` | DCS CoNLL-U in SLP1, split by chapter | 0.7, 0.8 | `scripts/convert_dcs_conllu.py`, then `split_dcs_conllu.py` |

Model checkpoints and run outputs are in `runs/` (also git-ignored).
`data/raw/` and `data/synthetic/` are empty leftovers.
