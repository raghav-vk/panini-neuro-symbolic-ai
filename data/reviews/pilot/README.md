# Community Review Pilot: Reviewer Guide

Thank you for trying the pilot. It tests whether a wider group of readers
can help check the project's Sanskrit data. It is the first stage of
`docs/REVIEW_APP_DESIGN.md`.

## What You Do

**Open the worksheet** at
<https://raghav-vk.github.io/panini-neuro-symbolic-ai/review/pilot.html> in
Chrome, Firefox, Edge or Safari. It works on a phone, but a laptop is easier
for handing in. Nothing is sent anywhere while you work: your answers are
saved in that browser on that device, so finish where you started. You can
also download `pilot_worksheet.html` and open it offline.

**Choose a script.** The worksheet shows Sanskrit in Devanagari by default.
You can switch to IAST at the top, and switch back at any time.

**Judge each item.** Each of the 60 items shows a sentence with one fused
form highlighted, and a proposed split such as

    चापि = च + अपि

Judge **only the highlighted junction**: is the fused form really these two
words, with the sandhi undone? Choose one answer:

1. **Correct.** Both words are right as written.
2. **Wrong.** Type the correct two words. You can type in Devanagari or
   IAST.
3. **Not a sandhi junction.** For example, the junction is inside a
   compound, or the highlight is misplaced.
4. **Unsure.** Add a short note saying why.

"Unsure" with a note is a good answer. It never costs points, so please
don't guess to avoid it.

**Work alone.** Several people answer the same items, so that we can see
where readers agree. Please don't discuss the items with other reviewers
until everyone has handed in.

**Hand in before the deadline.** The round runs for one week and closes on
**Tuesday 1 December 2026 at 23:59 UTC**. The worksheet and the welcome
page count down to it. Answers handed in later are not scored.

1. Click **Hand in**. The worksheet seals your answers: they are encrypted
   so that only the project can open them, and only after the round closes.
2. Click **Copy sealed answers**, then **Open the hand-in form**, paste into
   the box and submit. The form needs a free GitHub account.
3. A bot replies within a few minutes to confirm how many items you
   answered. It never says which answers were right.

You can hand in again until the deadline, and your latest hand-in counts.
**Save a backup** downloads your answers so you can resume on another
device.

The whole worksheet takes about 30 to 45 minutes.

## How Points Work

Points are counted only after everyone has handed in:

- **Agreeing with the group's answer:** 1 point per item. Answers are
  weighted by each reviewer's accuracy on items whose answer is already
  known.
- **A correction the group adopts:** 3 points, if the sandhi rules can turn
  your two words back into the fused form.
- **Items with a known answer:** some items have one, and they look the same
  as the others. They count extra.

The leaderboard lists reviewers with high accuracy on the known items.
Tick **Credit me by this name** to appear by name on the leaderboard, in
the dataset release and in the paper's acknowledgements. Otherwise you
appear as "Reviewer A", "Reviewer B" and so on.

When the round closes, scoring runs automatically. The results, the
leaderboard and a short report are published, and your hand-in issue gets
a link to them.

## What Happens to Your Answers

The answers become a "community-reviewed" layer of the training data, kept
separate from the expert review. Items the group cannot settle go to the
project's grammarian. The sentences come from the Digital Corpus of
Sanskrit (Krishna et al. 2017, CC BY 4.0).

## For the Project Owner

- **Invite reviewers:** `invite/` has a message, an email and a reminder
  (`INVITE.md`), a flyer (`flyer.png`, source `flyer.html`) and the site's QR
  code.
- **Build the set:** `scripts/build_pilot_set.py`. It draws only from the
  training split and refuses evaluation data. The answer key goes to
  `data/reviews/pilot/private/`, which git ignores. Never commit it or share
  it with reviewers.
- **Build the worksheet:** `scripts/build_review_page.py
  data/reviews/pilot/pilot_items.jsonl --mode verify --devanagari --round
  data/reviews/pilot/round.json --title "Community review pilot: check
  proposed splits" --answers-name pilot_answers.jsonl --output
  data/reviews/pilot/pilot_worksheet.html`
- **The round** (`round.json`): its deadline, the public sealing key and
  the success criteria, fixed before any answers. The private key is in
  `private/round_private_key.pem` and in the `PILOT_PRIVATE_KEY` secret;
  the answer key is also in the `PILOT_ANSWER_KEY` secret (base64).
- **Automation:** `.github/workflows/pilot-intake.yml` confirms each
  hand-in issue. After the deadline, `.github/workflows/pilot-close.yml`
  scores every valid hand-in with `scripts/pilot_round.py`, writes
  `reports/review-pilot/<round>/` (report, leaderboard, expert queue) and
  opens a pull request. Run it by hand from the Actions tab if needed.
- **Check a file:** `scripts/validate_review.py answers
  data/reviews/pilot/pilot_items.jsonl FILE`
- **Score:** `scripts/score_pilot.py FILE [FILE ...]`. It writes the
  leaderboard and expert queue to `runs/pilot-scores/`.
- **Publish:** `.github/workflows/pages.yml` deploys the worksheet to GitHub
  Pages when it changes on `main` (or run the workflow by hand). It publishes
  only `site/index.html` and the worksheet.
- **Before sending:** check the 12 control answers in the private key.
  Done on 2026-11-24: `manifest.json` records `controls_vetted: true`.
