# Roadmap: Done, Next and Waiting

One place for what is done, what is next, and what each open step waits on,
across every plan in the project. The plans themselves keep the detail; this
page links to them. For how the project got here, see
[VERSIONS.md](VERSIONS.md).

**Status as of 25 November 2026** (size M started). Update this page in the same pull request
that changes a step's status.

| Mark | Meaning |
| --- | --- |
| ✅ | Done, with a result or artifact |
| 🔄 | In progress |
| ⏭️ | Next: can start now |
| ⏸️ | Waiting on a person or a decision (named) |
| 🕓 | Later: depends on earlier steps |

## Now: the Five Things That Matter Most

1. 🔄 **Community review pilot (0.10).** The round closes on
   1 December 2026, 23:59 UTC. Scoring, the report and the results PR are
   automatic. Then decide on stage 1 of the review app against the four
   criteria fixed in advance.
2. ⏸️ **Expert review: grammarian.** The 18 draft rules (#65), compound
   prefixes and uncovered examples (#66), the silver overlap (#68), and the
   RLCD root and stem tables (#78). This blocks the publication rule gate
   and the gold set.
3. ⏸️ **Expert review: text reader.** The 200-example silver sample (#67)
   and the Tier 1 naturalness sample.
4. ⏭️ **Gold test set.** The silver test set is spent (four uses). The paper
   needs an untouched, expert-verified test set
   ([plan](GOLD_SET_PLAN.md), #63). It starts with the 30-item pilot (#69),
   which needs both reviewers.
5. ⏸️ **ashtadhyayi.com licence.** The February 2024 email says free products
   only, which conflicts with Vidyut's MIT note. Settle it before any
   release that includes material derived from ashtadhyayi.com. Waiting on
   the project owner and upstream.

## Track 1: The Sandhi Paper

The first paper's claim rests on sandhi splitting
([protocol §19](EXPERIMENT_PROTOCOL.md#19-minimum-publishable-result)).

| Step | Status | Waits on | Where |
| --- | --- | --- | --- |
| Typed rules, candidates with proofs, baselines, ranker | ✅ 0.1 to 0.4 | — | [VERSIONS](VERSIONS.md) |
| Silver DCS data and the right-word holdout | ✅ 0.2, 0.3 | — | [protocol §9.5](EXPERIMENT_PROTOCOL.md#95-right-word-holdout-amendment-02) |
| Main comparison on test | ✅ 0.4: linear + kosha 0.943 | — | [report](../reports/dcs-silver-v3/SUMMARY.md) |
| Pretraining and the frozen test | ✅ 0.5, 0.9: +0.018 with the kosha | — | [report](../reports/pretraining-v1/test/TEST_RESULTS.md) |
| Calibration and abstention | ✅ 0.7, confirmed in 0.9 | — | [report](../reports/rlcd-stage1/DEV_RESULTS.md) |
| Expert review of the 18 rules | ⏸️ | Grammarian (#65, #66) | [review packet](../data/reviews/REVIEW_PACKET.md) |
| 25-rule reviewed inventory (gate B) | 🕓 | Rule review; 18 drafts exist, 25 needed | [rule guide](guides/RULE_AUTHORING_GUIDE.md) |
| Silver sample review | ⏸️ | Text reader (#67), grammarian (#68) | [reviewer guide](../data/reviews/README.md) |
| Gold test set: pilot, main pass, adjudication | ⏭️ then ⏸️ | Both reviewers (#69, #70, #71) | [gold-set plan](GOLD_SET_PLAN.md) |
| Phase 2: inflected left words | 🕓 | A morphological generator; the gold set covers it | #64, [protocol §9.5](EXPERIMENT_PROTOCOL.md#95-right-word-holdout-amendment-02) |
| Data-efficiency curves and ablations of paper §10.3 | ⏭️ | — | [paper §11.5](paper/panini-neuro-symbolic-ai.md) |
| Blinded expert evaluation of 200 outputs | 🕓 | Gold set and reviewers | [protocol §17](EXPERIMENT_PROTOCOL.md#17-expert-evaluation) |
| Comparison with prior Sanskrit segmentation work | ⏭️ | — | [paper §2](paper/panini-neuro-symbolic-ai.md) |
| Record the 0.9 result in protocol §11.7 | ⏭️ | — | [protocol §11.7](EXPERIMENT_PROTOCOL.md#117-frozen-settings-for-the-sandhi-pretraining-test-run-amendment-09) |

**Release gates** ([protocol §18](EXPERIMENT_PROTOCOL.md#18-test-ladder)):

| Gate | Status |
| --- | --- |
| A. Code: all tests pass from a clean checkout | ✅ in CI on every push |
| B. Rules: 25 reviewed rules | ⏸️ 18 drafts, none reviewed |
| C. Corpus: archive audit, source corpus hashes, rights confirmed | ⏸️ audit tools exist; rights for ashtadhyayi.com material unresolved |
| D. Splits: zero leakage | ✅ for the silver holdouts (split audits, asserted by tests); recheck for the gold set |
| E. Symbolic coverage: recall at least 95% | ✅ on silver (99.9%) |
| F. Experiment: baselines, five seeds, regenerated results, manifests | ✅ for the silver studies |
| G. Scholarship: expert review, limitations, related work, no placeholders | ⏸️ expert review outstanding |

## Track 2: Pretraining

[Pretraining plan §8](PRETRAINING_PLAN.md#8-order-of-work-and-stopping-rules).

| Step | Status | Notes |
| --- | --- | --- |
| 1. Build P-A and P-B with the audit | ✅ | [corpus audit](../reports/pretraining-v1/corpus_audit.json), [texts](../reports/pretraining-v1/CORPUS_TEXTS.md); issue #61 can close |
| 2. Timing pilot | ✅ | [pilot](../reports/pretraining-v1/pilot_S_1000_steps.json) |
| 3. Pretrain size S on P-A | ✅ | Three seeds |
| 4. H-P1 and H-P2 on dev | ✅ | [dev results](../reports/pretraining-v1/DEV_RESULTS.md) |
| 5. H-P3, fine-tuning, on dev | ✅ | No gain (0.901 against 0.903) |
| 6. Pretrain the larger size M; run P-B | 🔄 | P-B was run with S (below the kosha). Size M was decided on 2026-11-25, with settings fixed in advance in [plan §8.1](PRETRAINING_PLAN.md#81-step-6-settings-size-m-pre-registered-2026-11-25): three seeds, dev only. The timing pilot is done: learning rate 2.5e-4, about 7 hours per seed |
| 7. Freeze and run one test | ✅ 0.9 | [test results](../reports/pretraining-v1/test/TEST_RESULTS.md) |
| Prose and genre balance | ⏭️ | The corpus is 29% Mahābhārata and mostly verse, and the tagger is weakest on prose. A hypothesis to test, for example by adding prose text whose licence allows it |

## Track 3: RLCD (Calibrated Decisions on Whole Words)

[RLCD plan §4](RLCD_TRANSITION_PLAN.md#4-staged-transition).

| Stage and step | Status | Notes |
| --- | --- | --- |
| 0. Clean up simulated figures and specification errors | ✅ | |
| 1. Calibration and abstention on sandhi | ✅ 0.7 | [results](../reports/rlcd-stage1/DEV_RESULTS.md) |
| 2. Schema, constraint layer, Vidyut compiler (items 0 to 3) | ✅ | `clause.py`, `derive.py` |
| 2. Grammarian checks the constraint tables (item 4) | ⏸️ | Grammarian (#78); accepted provisionally on 14 November |
| 3.1 Tier 1 generator | ✅ | Not for training until its tables are reviewed |
| 3.2 to 3.5 DCS morphology, splits, tagger heads, baselines | ✅ 0.7 | [tagger dev results](../reports/rlcd-stage3/TAGGER_DEV_RESULTS.md) |
| Joint and Platt calibration | ✅ 0.7, confirmed in 0.8 | [Platt results](../reports/rlcd-stage3/PLATT_CALIBRATION_RESULTS.md) |
| Frozen stage 3 test | ✅ 0.8 | [test results](../reports/rlcd-stage3/test/TEST_RESULTS.md) |
| 3.6 RL fine-tuning with the Vidyut reward | ⏭️ | Needs its own pre-registration before any run |
| Diagnose the prose texts (Harṣacarita, Aṣṭasāhasrikā) | ⏭️ | Suggested in the tagger dev results |
| Hybrid: kosha analysis for known verb forms, tagger elsewhere | ⏭️ | Suggested in the tagger dev results; needs pre-registration |
| 4. English interface | 🕓 | A separate, later paper; decide the English encoder first ([plan §6](RLCD_TRANSITION_PLAN.md#6-english-encoder-choices-for-stage-4)) |

## Track 4: Reviewing the Data

| Step | Status | Notes |
| --- | --- | --- |
| Expert review packets and worksheets | ✅ | Waiting for the reviewers (see "Now") |
| Review app design | ✅ | [design](REVIEW_APP_DESIGN.md) |
| Stage 0 pilot, round pilot-1 | 🔄 0.10 | Closes 1 December; results PR opens automatically |
| Decisions for stage 1: audience, contribution licence, hosting, name | ⏸️ | Project owner ([design §10](REVIEW_APP_DESIGN.md#10-decisions-needed)) |
| Stage 1: hosted app | 🕓 | Only if the pilot meets its criteria |
| Stage 2: route items by model confidence | 🕓 | After stage 1 |

## Housekeeping

| Item | Status | Notes |
| --- | --- | --- |
| Record the rebuild command for the SLP1 silver data (0.6) | ⏭️ | Never written down ([data map](../data/README.md)) |
| Update stale status lines in the pretraining plan and the RLCD specifications | ⏭️ | They predate the 0.9 run and the adoption of 0.7 |
| Review open issues from January | ✅ | Closed on 2026-11-25: #33, #52 and #58 as done by current code; #30 to #32 as superseded. #61 (pretraining step 1) is done and can be closed too |
| Report Vidyut's declension of feminine stems upstream | ⏸️ | Project owner's approval before contacting upstream |

The protocol's original work queue (§20, August 2026) is kept as a record;
this page replaces it for planning.
