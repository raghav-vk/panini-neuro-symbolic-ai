# Documentation

This directory contains only the active research specification and
collaboration guides for the current neuro-symbolic sandhi experiment.

## Start Here

| Document | Purpose |
| --- | --- |
| [Silver DCS results](../reports/dcs-silver-v3/SUMMARY.md) | Current results: right-word holdout with the external lexicon |
| [Earlier silver results](../reports/dcs-silver-v2/SUMMARY.md) | Results without the external lexicon |
| [Development results](../reports/development-v1/SUMMARY.md) | September synthetic CPU smoke experiment |
| [Review packet](../data/reviews/REVIEW_PACKET.md) | 18 draft rule encodings awaiting expert judgement |
| [Working paper](panini-neuro-symbolic-ai.md) | Manuscript being developed for archival submission |
| [Experiment protocol](EXPERIMENT_PROTOCOL.md) | Research questions, frozen-study design, amendments, metrics, and release gates |
| [Pretraining plan](PRETRAINING_PLAN.md) | Adopted plan for self-supervised pretraining of the neural ranker |
| [All-sandhi dataset](ALL_SANDHI_DATASET.md) | Reproducible 148-record source corpus and expert-screening workflow |
| [Rule authoring guide](RULE_AUTHORING_GUIDE.md) | Convert reviewed interpretations into typed executable rules |
| [Contributing](contributing.md) | Contribution boundaries and review requirements |

For setup and verification, use the repository-level
[Quick Start](../QUICKSTART.md). Release gates are in protocol section 18.
Corpus-specific requirements are in [datasets/README.md](../datasets/README.md).

## Scope

The broad language-model, translation, literary-generation, and universal
grammar-engine plans from early project drafts are retired. They are available
from Git history if needed but are intentionally absent from the current
documentation tree.

The current source corpus spans sandhi families. The executable development
experiment uses 18 draft encodings across five families; the independent
scholarly benchmark still awaits reviewed rules and corpus examples.
No document in this directory should
describe source candidates as automatically executable rules or subset
compliance as complete Sanskrit correctness.
