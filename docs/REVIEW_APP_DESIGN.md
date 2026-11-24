# Design Draft: A Community Review App for Sanskrit Data

**Status:** Draft for discussion, 2026-11-23. Nothing here is built, and no
data has been shown to anyone. Section 10 lists the decisions needed before
building.

## In Plain Terms

Expert review is the slowest part of the project. Issues #63 to #71 and #78
wait on two people. This app would let many more people check and correct
the project's Sanskrit data in Devanagari or IAST. Their answers are stored
in SLP1, like everything else in the project. Reviewers earn points and
places on a leaderboard, and the best are credited by name in dataset
releases and the paper.

The design rests on three rules:
1. **Points reward accuracy, not volume.** A leaderboard that rewards speed
   fills the data with fast guesses.
2. **The crowd never sees evaluation data.** Test splits, dev splits and the
   gold-set reserve stay out of the app, or they stop being independent.
3. **Crowd labels are their own tier.** They improve silver and training
   data. They do not replace the expert gold set or the grammarian's review.

## 1. What the App Is For

| Use | In scope | Why |
| --- | --- | --- |
| Checking proposed sandhi splits in training data | Yes | Same task as issue #67; the worksheet already exists |
| Checking morphological tags on training sentences | Yes | Stage 3 tagger output; the gate says which words need a person |
| Judging naturalness of synthetic Tier 1 clauses | Yes | `data/reviews/rlcd_tier1_sample.*` has no reviewer yet |
| Reviewing the draft rules and the RLCD tables | No (expert track only) | Needs a grammarian; crowd answers would not count as review |
| Building the expert gold test set | No | `docs/GOLD_SET_PLAN.md` requires expert, blind, adjudicated labels |
| Correcting dev or test labels | No | Would change the data the results were measured on |

The app can host an **expert track** later, using the same tools for the
grammarian and the text reader. That track would be separate, and its items
would be invisible to everyone else.

## 2. Where the Model Helps: Routing by Confidence

The calibrated gate (paper sections 11.4 and 12.4) gives the app its queue.
The model labels everything, and its confidence decides what goes to people:

- **Above τ:** accepted automatically. A small random sample still goes to
  people, to measure the gate's error rate.
- **Below τ:** sent to reviewers, most uncertain first.
- **Every correction feeds training.** It also gives fresh labelled data
  for recalibrating the gate.

This is the RLCD loop with people as the slow path, so each reviewed item is
one the model actually needed help with.

## 3. Roles

| Role | Can do | How earned |
| --- | --- | --- |
| Contributor | Answer tasks; answers count only in aggregate | Sign up |
| Trusted reviewer | Answers carry more weight; can resolve 2-to-1 splits | Sustained accuracy on control items (section 5) |
| Expert | Expert track; final say on disputes | Invited (the grammarian and the text reader) |
| Maintainer | Task sets, exports, bans | The project owner |

## 4. Tasks and Input

**What a reviewer sees.** Each task shows a sentence with one highlighted
form, in the reviewer's chosen script (Devanagari or IAST). The reviewer
chooses an answer, as in the current worksheets: correct, wrong (with a
correction), or unsure (with a note). "Unsure" never costs points.

**Typing Sanskrit.** Reviewers can type in Devanagari, IAST or
Harvard-Kyoto. The app converts the input with `vidyut.lipi` (already a
dependency; Devanagari `गच्छति` becomes SLP1 `gacCati`). It then shows the
reviewer the normalised form for confirmation before saving.

**Symbolic check on corrections.** A corrected split is passed to the rule
layer (`panini.candidates.forward`). The correction is accepted only if a
rule derives the attested surface from it. If none does, it goes to an
expert queue marked "outside the rule inventory". Such a correction may be
right, but no rule covers it.

## 5. Quality Control

- **Redundancy.** Each item gets three independent answers. Reviewers never
  see others' answers on an item until it is resolved.
- **Control items.** About one task in ten has a known answer. Controls come
  from expert-adjudicated review items (#67/#68 once finished) and from
  Vidyut-derived synthetic forms. They never come from the gold set or any
  test split. They look exactly like normal tasks.
- **Aggregation.** Answers are weighted by each reviewer's control accuracy
  (a Dawid–Skene-style model, so a few careless answers don't outvote
  careful ones).
- **Escalation.** Disputed items, any "outside the rule inventory"
  correction and low-agreement items go to an expert.
- **Reporting.** Agreement (Cohen's or Fleiss' kappa) between the crowd and
  the experts on overlap items, published with each data release.

## 6. Gamification

Status should come from being right.

- **Points are scored late.** They are awarded only when an item is
  resolved, by agreement with the final answer or a control. Instant points
  invite guessing.
- **Leaderboard by accuracy-weighted points.** A minimum control accuracy
  (for example 85%) is required to appear on it. Weekly and all-time boards.
- **Badges by expertise.** For example, by sandhi family, text or kind of
  task. A "found an error" badge goes to accepted corrections the model got
  wrong.
- **Real credit.** Leaders are named in each dataset release's
  `CONTRIBUTORS` file and in the paper's acknowledgements. That is the
  bragging right with lasting value.
- **No pressure loops.** Streaks are capped, there are no penalties for
  breaks, and there are daily task limits.

**Anti-gaming measures:**
- control items indistinguishable from normal tasks
- rate limits
- flags for accounts that agree with each other unusually often
- leaderboard places revoked if control accuracy falls

## 7. Protecting the Evaluation Data

The server, not the user interface, holds an **exclusion list** by hash. It
covers:
- the right-word holdout dev and test items
- the stage 3 DCS dev and test chapters
- the eight gold-set reserve texts (`reports/dcs-conllu/split_manifest.json`)
- the review-overlap items still pending

A task generator refuses any item on the list, and a test checks this on
every build. Task sets are built only from training splits and the
unassigned pool.

## 8. Licensing and Privacy

- **DCS text.** CC BY 4.0: it may be shown with attribution on every page.
- **The kosha and Monier-Williams data.** CC BY-NC-SA: the app does not show
  them or use them to build tasks. That keeps the app clear of the
  non-commercial and share-alike terms.
- **ashtadhyayi.com material.** Excluded until the licence question
  (Vidyut's MIT note against the February 2024 email) is settled.
- **Contributions.** Contributors agree that their answers are released
  under one stated licence (CC BY 4.0 or CC0; to decide), with credit by
  handle.
- **Personal data.** A display handle and a login only. No real names unless
  a contributor asks to be credited by name.

## 9. Building in Stages

| Stage | What | For whom | Rough size |
| --- | --- | --- | --- |
| 0. Pilot | Extend the existing offline worksheets (`src/review/worksheet.html`, `scripts/build_review_page.py`) with Devanagari input and control items. Answers handed in as files; no server | 5 to 10 invited people | A few days |
| 1. Hosted app | Accounts, task queue, three-way redundancy, delayed scoring, leaderboard, nightly JSONL export with hashes to `data/reviews/crowd/` | An open community | A few weeks |
| 2. Gate routing | Tasks chosen by model confidence (section 2), retraining on resolved items, expert track | Ongoing | Later |

For stage 1, a small Python backend (for example FastAPI with SQLite, later
Postgres) fits best. It can call `vidyut.lipi` and the rule layer directly,
with no second implementation. The frontend can be a plain web app that
works on phones.

Every export is versioned and hashed, like the other data. A merge script
turns resolved answers into a `crowd_reviewed` data tier with full
provenance: who answered, the control accuracy at the time, and how the
item was resolved.

## 10. Decisions Needed

1. **Audience.** Students, teachers, traditional scholars, or all of these?
   The answer sets the interface language (English, Hindi, Sanskrit) and how
   hard the tasks can be.
2. **Contribution licence.** CC BY 4.0 or CC0.
3. **Hosting and cost.** Where it runs, and who owns the domain and the
   data.
4. **Pilot first?** Stage 0 tests whether people come back before anything
   is built.
5. **Name and identity.** Whether the app carries the project's name.
