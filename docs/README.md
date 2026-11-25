# Documentation: Start Here

Project Pāṇini splits Sanskrit sandhi with typed rules taken from Pāṇini's
grammar, and uses a small neural model to choose among the rules' answers.
Every answer carries a proof, and the system abstains when it is unsure.

**New here? Read three things, in order:**
1. The project [readme](../readme.md): what it is and what it does not
   claim (two minutes).
2. [VERSIONS.md](VERSIONS.md): how the system grew from 0.1 to 0.10, one
   question at a time, with every result (ten minutes).
3. [The paper](paper/panini-neuro-symbolic-ai.md): the full argument, for
   when you want details.

To run the code, use the [Quick Start](../QUICKSTART.md).

## The Building Blocks

A fused form such as *cāpi* passes through five blocks, and a sixth checks
the data:

    fused form in context ──▶ 1. rules ──▶ 2. candidates with proofs
        ──▶ 3. ranker ──▶ 4. confidence gate ──▶ answer, or "unsure"
    5. RLCD: the same idea for whole-word morphology
    6. review: people check and correct the data

| # | Block | What it does | Code | Read | Since |
| --- | --- | --- | --- | --- | --- |
| 1 | Typed rules | Each sandhi rule is a typed, testable rewrite, traced to its sūtra | `src/panini/rules.py`, `data/rules/` | [Rule authoring guide](guides/RULE_AUTHORING_GUIDE.md), [all-sandhi source corpus](ALL_SANDHI_DATASET.md) | 0.1 |
| 2 | Candidate generator | Undoes a fused form into every rule-licensed split, each with a forward proof | `src/panini/candidates.py` | [Protocol §10](EXPERIMENT_PROTOCOL.md#10-candidate-generator) | 0.1 |
| 3 | Ranker | Picks a candidate from frequency, the Vidyut kosha and pretrained word scores | `src/panini/ranking.py`, `lexicon.py`, `pretraining.py` | [Protocol §11](EXPERIMENT_PROTOCOL.md#11-neural-ranker), [pretraining plan](PRETRAINING_PLAN.md) | 0.1, 0.4, 0.5 |
| 4 | Confidence gate | Answers only when confidence is at least 0.95; otherwise abstains | `src/panini/calibration.py` | [RLCD plan §4](RLCD_TRANSITION_PLAN.md) | 0.7 |
| 5 | RLCD | Clause schema, constraint checks before Vidyut derivation, and a morphological tagger | `src/panini/clause.py`, `derive.py`, `tagger.py`, `data/rlcd/` | [RLCD plan](RLCD_TRANSITION_PLAN.md), [constraint review](RLCD_CONSTRAINTS.md) | 0.7 |
| 6 | Review | Expert review packets, and the community pilot with hidden controls | `src/review/`, `scripts/*review*.py`, `scripts/*pilot*.py` | [Review app design](REVIEW_APP_DESIGN.md), [pilot guide](../data/reviews/pilot/README.md), [expert reviewer guide](../data/reviews/README.md) | 0.1, 0.10 |

All text inside the system is in SLP1 (version 0.6, `src/panini/translit.py`);
IAST and Devanagari are for people.

## Where Things Are

| Folder | Holds | Map |
| --- | --- | --- |
| `docs/` | This page, the timeline, and the protocol record (below) | — |
| `docs/paper/` | The manuscript and its figures | — |
| `docs/guides/` | How to contribute and how to write rules | — |
| `docs/architecture/` | Draft long-term designs, not adopted, reviewed by the RLCD plan | — |
| `docs/archive/` | Retired January 2026 plans, kept for history | — |
| `reports/` | Every result, dev and test | [reports/README.md](../reports/README.md) |
| `data/` | Rules, reviews, RLCD tables, schemas; rebuilt corpora in `data/processed/` | [data/README.md](../data/README.md) |
| `datasets/` | Source corpus manifests (the DCS archive itself is downloaded) | [datasets/README.md](../datasets/README.md) |

## The Protocol Record

These documents set out each experiment **before** it ran. Frozen test
records and code name them by path, so they stay where they are.

| Document | Version | What it fixes |
| --- | --- | --- |
| [Experiment protocol](EXPERIMENT_PROTOCOL.md) | 0.1 to 0.9 | Questions, splits, metrics, release gates, and every amendment |
| [Pretraining plan](PRETRAINING_PLAN.md) | 0.5 | Corpora, hypotheses and steps for pretraining |
| [RLCD transition plan](RLCD_TRANSITION_PLAN.md) | 0.7 | Review of the RLCD architecture and its staged path |
| [RLCD constraint review](RLCD_CONSTRAINTS.md) | 0.7 | Root and stem tables awaiting the grammarian |
| [Stage 3 test amendment](STAGE3_TEST_AMENDMENT.md) | 0.8 | Frozen settings and hypotheses for the tagger test |
| [Sandhi pretraining test amendment](SANDHI_PRETRAINING_TEST_AMENDMENT.md) | 0.9 | Frozen settings and hypotheses for the pretraining test, with its erratum |
| [Review app design](REVIEW_APP_DESIGN.md) | 0.10 | The crowd review app and its pilot |

Plans not yet built:
- [Gold-set plan](GOLD_SET_PLAN.md): an independent, expert-reviewed test
  set.
- [Dataset generation pipeline](dataset-generation-pipeline.md): an
  English-to-Pāṇinian dataset design, reviewed in the RLCD plan (stage 4).

Field examples: [dataset-structure.json](dataset-structure.json).

## Ground Rules

- "Verified" means consistent with the encoded and tested rule subset, not
  complete Sanskrit correctness.
- Spent test parts are never reused for tuning; any reuse is disclosed.
- Nothing is marked reviewed without an actual review.
- See [contributing](guides/contributing.md) before opening a pull request.
