# Expert Review: Reviewer Guide

Thank you for helping. This folder holds everything the two reviewers need.
Each task has its own GitHub issue:

| Issue | Reviewer | Task | Time (rough guess) |
| --- | --- | --- | --- |
| #65 | Grammarian | The 18 draft sandhi rules | 2 to 3 hours |
| #66 | Grammarian | Three short checks | under 1 hour |
| #67 | Text reader | 200 proposed splits from the corpus | about 2 hours |
| #68 | Grammarian | 50 of the same 200, checked independently | about 30 minutes |

The gold-test-set tasks (#69 to #71) come later and will get their own
worksheets.

Transliteration throughout is IAST.

## Two ground rules

1. **Work independently.** The text reader and the grammarian check some of
   the same items so we can measure agreement. Please don't discuss those
   items, or look at each other's answers, until both of you have handed in.
2. **Judge what is in front of you.** "Unsure" with a short note is a useful
   answer. Please don't guess to avoid it.

## Handing in your work

You can hand in either way:

- **On GitHub:** commit your file to `data/reviews/` on your own branch (the
  branch names are below), and open a pull request that mentions the issue.
- **By email:** send the file to the project owner, who commits it with your
  name as the reviewer.

Before handing in, the project owner (or you, if you have the repository)
runs the validator below. It lists anything missing.

## Tasks #67 and #68: checking proposed splits

**Open the worksheet.** Download your worksheet file from GitHub: open it,
then use "Download raw file". Open the downloaded file in Chrome, Firefox or
Edge. It works offline and sends nothing anywhere.

- Text reader (#67): `silver_text_reader.html`, 200 items.
- Grammarian (#68): `silver_grammarian.html`, 50 items.

**What you see.** Each item shows a sentence from the Digital Corpus of
Sanskrit with one fused form highlighted, and a proposed split such as

    cāpi = ca + api

The two words are proposed with the sandhi at the highlighted junction
undone. Judge **only that junction**. Each word keeps whatever form it has at
its other end in the sentence. The dictionary forms (lemmas) are shown as a
hint, and they come from the corpus annotation.

**Your answer.** Choose one:

1. **Correct.** Both words are right as written.
2. **Wrong.** The fields fill with the proposal. Edit them to the correct two
   words.
3. **Not a sandhi junction between two separate words.** For example the
   fused form is inside a compound, or the highlight is in the wrong place.
4. **Unsure.** Add a note saying why.

You can add a note to any answer. Keys 1 to 4 choose an answer and the arrow
keys move between items.

**Saving.** Answers are saved in your browser as you go, so you can close it
and come back. Use the same browser on the same computer. To be safe, use
**Export answers** at the end of each session. The export is also the file
you hand in:

- `silver_answers.text_reader.jsonl` on the branch `review/text-reader-silver`;
- `silver_answers.grammarian.jsonl` on the branch `review/grammarian-silver`.

To continue on another computer, open the worksheet there and load the
exported file with "Resume from an exported answers file".

**Validation:**

    python scripts/validate_review.py answers data/reviews/silver_sample.jsonl \
        data/reviews/silver_answers.text_reader.jsonl

    python scripts/validate_review.py answers data/reviews/silver_sample.jsonl \
        data/reviews/silver_answers.grammarian.jsonl --ids data/reviews/silver_overlap_ids.json

## Task #65: the 18 draft rules

1. Read `REVIEW_PACKET.md`. It gives each rule's sūtra, the subset of it we
   encode, and the conditions. The rules themselves, with their test
   examples, are in `data/rules/development_sandhi.jsonl`.
2. Copy `rule_queue.template.jsonl` to `rule_queue.grammarian.jsonl`. It has
   one line per rule. Fill in each line:

   | Field | Value |
   | --- | --- |
   | `scope_correct` | `true` or `false`: does the rule apply in exactly the right contexts? |
   | `examples_correct` | `true` or `false`: are the positive and negative examples right? |
   | `exceptions_complete` | `true` or `false`: are the exceptions that matter covered or blocked? |
   | `precedence_correct` | `true` or `false`: is the order relative to other rules right? |
   | `decision` | `"approve"`, `"revise"` or `"reject"` |
   | `notes` | required for `revise`, `reject`, or any `false` |
   | `reviewer`, `reviewed_at` | your name, and the date as `2026-11-02` |

   Leave the other fields as they are.

3. Look most closely at **SDH-013 to SDH-018**: vṛddhi with e and o, u + u,
   a + ṛ, and the remaining yaṇ cases. They were drafted from how often each
   junction occurs in the corpus, not from the grammar first.
4. Hand in on the branch `review/grammarian-rules`.

If editing the file is awkward, write your answers in the issue instead (one
paragraph per rule), and the project owner will transcribe them for you to
check.

**Validation:**

    python scripts/validate_review.py rules data/rules/development_sandhi.jsonl \
        data/reviews/rule_queue.grammarian.jsonl

A rule is marked expert-reviewed only after this record exists.

## Task #66: three short checks

Fill in the last column of each table in `GRAMMARIAN_CHECKS.md`. You can edit
it on GitHub directly, on the branch `review/grammarian-checks`, or paste your
answers into issue #66. The 12 boundaries in section 3 are also in
`uncovered_examples.jsonl`, with full details.

## The files here

| File | What it is |
| --- | --- |
| `silver_sample.jsonl` | The 200 review items: sentence, highlight span, proposed split, lemmas |
| `silver_overlap_ids.json` | The 50 items both reviewers check, chosen with a fixed seed |
| `silver_text_reader.html`, `silver_grammarian.html` | The worksheets, with the items built in |
| `uncovered_examples.jsonl` | The 12 extracted boundaries no rule generates |
| `GRAMMARIAN_CHECKS.md` | The worksheet for issue #66 |
| `REVIEW_PACKET.md`, `rule_queue.template.jsonl` | The rule review packet and blank decision file |
| `manifest.json` | Hashes of the inputs and outputs, and the seed |

The sentences come from DCS_pick (Krishna, Satuluri and Goyal 2017; CC BY 4.0;
see `THIRD_PARTY_NOTICES.md`). The proposed splits are derived automatically
from its annotation and are not verified. That is what this review is for.

Regenerate the files with:

    python scripts/prepare_expert_review.py
    cd data/reviews
    python ../../scripts/build_review_page.py silver_sample.jsonl --mode verify \
        --title "Silver sample: 200 proposed splits" \
        --answers-name silver_answers.text_reader.jsonl --output silver_text_reader.html
    python ../../scripts/build_review_page.py silver_sample.jsonl --mode verify \
        --ids silver_overlap_ids.json --title "Silver sample: 50-item overlap" \
        --answers-name silver_answers.grammarian.jsonl --output silver_grammarian.html
