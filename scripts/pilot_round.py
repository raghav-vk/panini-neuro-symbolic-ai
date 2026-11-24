#!/usr/bin/env python3
"""Run a time-boxed community review round end to end (docs/REVIEW_APP_DESIGN.md, stage 0).

    pilot_round.py keys                       make the sealing key pair (once per round)
    pilot_round.py intake --event EVENT.json  check one hand-in issue; write the bot's reply
    pilot_round.py fetch --output ISSUES.json download the hand-in issues and the bot's receipts
    pilot_round.py close --issues ISSUES.json score every valid hand-in and write the report

Hand-ins are sealed in the worksheet: the answers are encrypted with AES-256-GCM under a fresh key,
and that key with RSA-OAEP (SHA-256) under the round's public key. Only the holder of the private
key (the PILOT_PRIVATE_KEY secret) can read them, so reviewers cannot copy each other's answers
from the public issues before the round closes.

The intake reply never reveals correctness. It records the SHA-256 of the sealed text it checked
in a hidden receipt line, and only for text that arrived before the deadline (for an edited issue,
the edit time counts). At close, an issue counts only if its current text has such a receipt, it was
opened before the deadline, and it is the author's latest such issue.
"""

import argparse
import base64
import hashlib
import json
import os
import re
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from build_pilot_set import KEY, OUTPUT, read_jsonl

ROUND = OUTPUT / "round.json"
PRIVATE_KEY = OUTPUT / "private/round_private_key.pem"
BEGIN, END = "-----BEGIN PANINI SEALED ANSWERS-----", "-----END PANINI SEALED ANSWERS-----"
RECEIPT = re.compile(r"<!-- pilot-receipt round=(\S+) sha256=([0-9a-f]{64}) -->")
MAX_SEALED = 60_000


def load_round(path=ROUND):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def when(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


# Sealing ------------------------------------------------------------------------------------------

def b64(data):
    return base64.b64encode(data).decode()


def make_keys(private_path):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    private_path.parent.mkdir(parents=True, exist_ok=True)
    private_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                               serialization.NoEncryption()))
    os.chmod(private_path, 0o600)
    return b64(key.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo))


def _oaep():
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    return padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)


def seal(payload, public_spki):
    """The worksheet's sealing, in Python (for tests and for answers handed in by other routes)."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.serialization import load_der_public_key
    secret, iv = os.urandom(32), os.urandom(12)
    body = AESGCM(secret).encrypt(iv, json.dumps(payload, ensure_ascii=False).encode(), None)
    wrapped = load_der_public_key(base64.b64decode(public_spki)).encrypt(secret, _oaep())
    text = "1." + ".".join(b64(x) for x in (wrapped, iv, body))
    return "\n".join([BEGIN, *(text[i:i + 76] for i in range(0, len(text), 76)), END])


def sealed_text(text):
    """The sealed block in an issue body, whitespace removed, or None."""
    start, end = text.find(BEGIN), text.find(END)
    if start < 0 or end < start:
        return None
    return re.sub(r"\s+", "", text[start + len(BEGIN):end])


def unseal(sealed, private_pem):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    version, wrapped, iv, body = sealed.split(".")
    if version != "1":
        raise ValueError(f"unknown sealing version {version!r}")
    secret = load_pem_private_key(private_pem, password=None).decrypt(base64.b64decode(wrapped), _oaep())
    return json.loads(AESGCM(secret).decrypt(base64.b64decode(iv), base64.b64decode(body), None))


def digest(sealed):
    return hashlib.sha256(sealed.encode()).hexdigest()


# Intake -------------------------------------------------------------------------------------------

def check_submission(body, arrived_at, round_config, items, private_pem):
    """(status, details): status is received, late or invalid. Details never reveal correctness."""
    from validate_review import check_answers
    sealed = sealed_text(body or "")
    if sealed is None:
        return "invalid", {"reason": "no sealed answers found: paste the whole block, including the BEGIN and END lines"}
    if len(sealed) > MAX_SEALED:
        return "invalid", {"reason": "the sealed block is too long"}
    try:
        payload = unseal(sealed, private_pem)
    except Exception:
        return "invalid", {"reason": "the sealed block could not be opened: it may be cut short or changed"}
    if payload.get("round") != round_config["round"]:
        return "invalid", {"reason": f"these answers are for round {payload.get('round')!r}, not {round_config['round']!r}"}
    if when(arrived_at) > when(round_config["closes"]):
        return "late", {}
    rows = payload.get("answers")
    if not isinstance(rows, list):
        return "invalid", {"reason": "the sealed block has no answers"}
    problems = check_answers(items, rows)
    answered = sum(1 for r in rows if isinstance(r, dict) and r.get("decision"))
    return "received", {"sha256": digest(sealed), "answered": answered, "items": len(items),
                        "problems": len(problems), "credit": bool(payload.get("credit"))}


def reply(status, details, round_config):
    closes = when(round_config["closes"]).strftime("%A %-d %B %Y, %H:%M UTC")
    if status == "invalid":
        return (f"**Not received yet.** {details['reason']}.\n\nPlease open a new hand-in from the worksheet "
                f"(Hand in → Copy sealed answers) before {closes}.")
    if status == "late":
        return f"**This round closed on {closes}**, so these answers will not be scored. Thank you for reviewing!"
    receipt = f"<!-- pilot-receipt round={round_config['round']} sha256={details['sha256']} -->"
    lines = [f"**Received.** {details['answered']} of {details['items']} items answered.", ""]
    if details["problems"]:
        lines += [f"The worksheet flagged {details['problems']} incomplete answers (for example a missing note on "
                  "\"unsure\"). They still count where they can. To fix them, hand in again from the worksheet: "
                  "your latest hand-in before the deadline is the one scored.", ""]
    lines += [f"Your answers stay sealed until the round closes on **{closes}**. Scoring and the leaderboard then "
              "run automatically, and this issue gets a link to the results.",
              "",
              "You will be credited by name if you ticked the box." if details["credit"] else
              "You chose not to be credited by name, so the leaderboard will show you anonymously.",
              "", f"Sealed hash: `{details['sha256'][:16]}`", receipt]
    return "\n".join(lines)


def intake(args):
    event = json.loads(Path(args.event).read_text(encoding="utf-8"))
    issue = event["issue"]
    round_config = load_round(args.round)
    arrived = issue["updated_at"] if event.get("action") == "edited" else issue["created_at"]
    status, details = check_submission(issue.get("body"), arrived, round_config,
                                       read_jsonl(args.items), private_key(args))
    Path(args.reply).write_text(reply(status, details, round_config) + "\n", encoding="utf-8")
    print(status)


def github(path, token):
    """Every page of a GitHub REST list endpoint."""
    import urllib.request
    url, out = f"https://api.github.com/{path}{'&' if '?' in path else '?'}per_page=100", []
    while url:
        request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}",
                                                       "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(request) as response:
            out += json.loads(response.read())
            links = dict((m.group(2), m.group(1)) for m in re.finditer(r'<([^>]+)>; rel="(\w+)"', response.headers.get("Link", "")))
            url = links.get("next")
    return out


def fetch(args):
    repo, token = os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"]
    issues = []
    for issue in github(f"repos/{repo}/issues?labels={args.label}&state=all", token):
        if "pull_request" in issue:
            continue
        comments = github(f"repos/{repo}/issues/{issue['number']}/comments", token) if issue["comments"] else []
        issues.append({"number": issue["number"], "author": issue["user"]["login"], "created_at": issue["created_at"],
                       "body": issue.get("body") or "",
                       "comments": [{"author": c["user"]["login"], "body": c.get("body") or ""} for c in comments]})
    Path(args.output).write_text(json.dumps(issues, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(issues)} hand-in issues")


def private_key(args):
    if os.environ.get("PILOT_PRIVATE_KEY"):
        return os.environ["PILOT_PRIVATE_KEY"].encode()
    return Path(args.private_key).read_bytes()


# Close: collect, score, report --------------------------------------------------------------------

def collect(issues, round_config, private_pem, bot="github-actions[bot]"):
    """{login: payload} for the latest valid, on-time, unedited hand-in per author.

    issues: [{"number", "author", "created_at", "body", "comments": [{"author", "body"}]}].
    """
    closes, chosen = when(round_config["closes"]), {}
    for issue in sorted(issues, key=lambda i: i["created_at"]):
        sealed = sealed_text(issue.get("body") or "")
        if sealed is None or when(issue["created_at"]) > closes:
            continue
        receipts = {m.group(2) for c in issue.get("comments", []) if c.get("author") == bot
                    for m in RECEIPT.finditer(c.get("body", "")) if m.group(1) == round_config["round"]}
        if digest(sealed) not in receipts:
            continue
        try:
            payload = unseal(sealed, private_pem)
        except Exception:
            continue
        if payload.get("round") == round_config["round"]:
            chosen[issue["author"]] = {**payload, "issue": issue["number"]}
    return chosen


def minutes(payload):
    try:
        return (when(payload["sealed_at"]) - when(payload["started_at"])).total_seconds() / 60
    except (KeyError, TypeError, ValueError):
        return None


def display_names(submissions):
    """Credited reviewers by their chosen name (or handle); the rest as Reviewer A, B, ..."""
    names, anonymous = {}, 0
    for login in sorted(submissions, key=lambda x: submissions[x]["issue"]):
        p = submissions[login]
        if p.get("credit"):
            names[login] = (str(p.get("reviewer") or "").strip() or f"@{login}")[:60]
        else:
            names[login] = f"Reviewer {chr(65 + anonymous)}" if anonymous < 26 else f"Reviewer {anonymous + 1}"
            anonymous += 1
    return names


def kappa_words(kappa):
    if kappa is None:
        return "not computable"
    for bound, word in ((0.2, "slight"), (0.4, "fair"), (0.6, "moderate"), (0.8, "substantial")):
        if kappa < bound:
            return "poor" if kappa < 0 else word
    return "almost perfect"


def criteria_table(result, submissions, items, criteria):
    stats = list(result["reviewers"].values())
    accuracies = [s["control_accuracy"] for s in stats if s["control_accuracy"] is not None]
    complete = sum(s["answered"] >= len(items) for s in stats)
    ac1 = result["agreement"]["gwet_ac1_real_items"]
    rows = [
        ("Valid hand-ins", f"≥ {criteria['min_submissions']}", str(len(submissions)),
         len(submissions) >= criteria["min_submissions"]),
        ("Reviewers who answered every item", f"≥ {criteria['min_completion_share']:.0%}",
         f"{complete / len(stats):.0%}" if stats else "—",
         bool(stats) and complete / len(stats) >= criteria["min_completion_share"]),
        ("Median control accuracy", f"≥ {criteria['min_median_control_accuracy']:.0%}",
         f"{statistics.median(accuracies):.0%}" if accuracies else "—",
         bool(accuracies) and statistics.median(accuracies) >= criteria["min_median_control_accuracy"]),
        ("Agreement on real items (Gwet's AC1)", f"≥ {criteria['min_gwet_ac1']:.2f}",
         "—" if ac1 is None else f"{ac1:.2f}", ac1 is not None and ac1 >= criteria["min_gwet_ac1"]),
    ]
    return rows, all(r[3] for r in rows)


def report(result, submissions, items, key, round_config):
    real = [k for k in key if k["kind"] == "real"]
    resolved = result["resolved"]
    status = Counter(r["status"] for r in resolved.values())
    settled = [r for r in resolved.values() if r["status"] == "resolved"]
    verdicts = Counter(r["decision"] for r in settled)
    wrong = [r for r in resolved.values() if r.get("decision") == "wrong"]
    stats = result["reviewers"]
    accuracies = sorted(s["control_accuracy"] for s in stats.values() if s["control_accuracy"] is not None)
    times = sorted(t for t in (minutes(p) for p in submissions.values()) if t is not None and t > 0)
    unsure = sum(s["unsure"] for s in stats.values())
    answered = sum(s["answered"] for s in stats.values())
    agreement = result["agreement"]
    kappa, ac1, raw = (agreement[k] for k in ("fleiss_kappa_real_items", "gwet_ac1_real_items", "observed_agreement_real_items"))
    rows, passed = criteria_table(result, submissions, items, round_config["criteria"])
    opens, closes = (when(round_config[k]).strftime("%-d %B %Y") for k in ("opens", "closes"))

    lines = [f"# Community Review Pilot ({round_config['round']}): Results", "",
             f"*Generated automatically when the round closed. Round open {opens} to {closes} (UTC).*", "",
             "## In Plain Terms", ""]
    if not submissions:
        lines += ["No valid hand-ins arrived before the deadline, so there is nothing to score.", ""]
    else:
        lines += [f"{len(submissions)} reviewers handed in on time. They checked {len(real)} proposed splits from the "
                  f"training data, plus {len(key) - len(real)} hidden items with known answers.",
                  f"Their agreement with each other on the real items was {kappa_words(ac1)}: "
                  f"{'—' if raw is None else f'{raw:.0%}'} of reviewer pairs gave the same answer "
                  f"(Gwet's AC1 {'—' if ac1 is None else f'{ac1:.2f}'}).",
                  f"The group settled {status['resolved']} of {len(real)} real items: {verdicts['correct']} confirmed as "
                  f"correct, {verdicts['wrong']} judged wrong, {verdicts['not_boundary']} judged not a sandhi junction. "
                  f"{len(result['expert_queue'])} items go to the grammarian.", ""]
    lines += ["**Verdict on the stated criteria: " + ("met; go to stage 1 (hosted app).**" if passed else
              "not met; adjust the pilot before building stage 1.**"), "",
              "## Criteria Stated Before the Round", "",
              "These were fixed in `data/reviews/pilot/round.json` before any answers came in.", "",
              "| Criterion | Needed | Result | Met |", "| --- | ---: | ---: | :---: |"]
    lines += [f"| {name} | {need} | {got} | {'yes' if ok else 'no'} |" for name, need, got, ok in rows]
    lines += ["", "## Reviewers", "",
              f"- Control accuracy per reviewer: {', '.join(f'{a:.0%}' for a in accuracies) or '—'}.",
              f"- \"Unsure\" answers: {unsure} of {answered} ({unsure / answered:.0%})." if answered else "- \"Unsure\" answers: —.",
              (f"- Time from first answer to hand-in (median, includes breaks): {statistics.median(times):.0f} minutes "
               f"(range {times[0]:.0f} to {times[-1]:.0f})." if times else "- Time to hand in: not recorded."),
              f"- On the leaderboard (control accuracy ≥ 85% and at least 80% of items answered): "
              f"{sum(s['on_leaderboard'] for s in stats.values())} of {len(stats)}.",
              "", "## What the Group Found in the Data", "",
              "| Outcome on real items | Count |", "| --- | ---: |"]
    lines += [f"| {label} | {status.get(s, 0)} |" for s, label in
              (("resolved", "Settled by a weighted majority"), ("disputed", "Disputed (no clear majority)"),
               ("outside_rule_inventory", "Crowd correction the rules cannot derive"), ("no_votes", "No usable votes"))]
    if wrong:
        derivable = sum(1 for r in wrong if r.get("derivable"))
        lines += ["", f"The group judged {len(wrong)} silver splits wrong; for {derivable} of them it agreed on a "
                  "correction that the sandhi rules can turn back into the fused form. These are candidate fixes "
                  "for the silver data and go to the grammarian before any change."]
    lines += ["", "Every item the group did not confirm as correct is listed in `EXPERT_QUEUE.md`. The leaderboard is in "
              "`LEADERBOARD.md`; reviewers who did not ask for credit appear anonymously.", "",
              "## Caveats", "",
              "- The real items come from the training split only; this round says nothing about evaluation data, "
              "which reviewers never saw.",
              "- Votes are weighted by control accuracy on only 12 control items, so one mistake moves a reviewer's "
              "weight by about 8 points.",
              "- The pilot sample is small and the reviewers were invited, not recruited at random.",
              f"- Fleiss' kappa was {'—' if kappa is None else f'{kappa:.2f}'}. Kappa is not the criterion because it "
              "falls towards zero when nearly every item has the same answer, as here (most silver splits are correct), "
              "even when reviewers agree; Gwet's AC1 was chosen for this reason before the round opened."]
    return "\n".join(lines) + "\n"


def public_result(result, names):
    """results.json without logins: reviewers under their display names."""
    return {**result, "reviewers": {names[login]: s for login, s in result["reviewers"].items()}}


def close(args):
    from panini.rules import load_rules
    from score_pilot import RULES, expert_queue, leaderboard, score
    round_config = load_round(args.round)
    now = datetime.now(timezone.utc)
    if now < when(round_config["closes"]) and not args.force:
        print(f"round {round_config['round']} is still open until {round_config['closes']}")
        return
    issues = json.loads(Path(args.issues).read_text(encoding="utf-8"))
    items, key = read_jsonl(args.items), read_jsonl(args.key)
    submissions = collect(issues, round_config, private_key(args))
    result = score(items, key, {login: p["answers"] for login, p in submissions.items()}, load_rules(RULES))
    names = display_names(submissions)
    renamed = public_result(result, names)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "REPORT.md").write_text(report(result, submissions, items, key, round_config), encoding="utf-8")
    (out / "LEADERBOARD.md").write_text(leaderboard(renamed), encoding="utf-8")
    (out / "EXPERT_QUEUE.md").write_text(expert_queue(result, items), encoding="utf-8")
    (out / "results.json").write_text(json.dumps(renamed, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "issues.json").write_text(json.dumps({"scored": sorted(p["issue"] for p in submissions.values()),
                                                 "all": sorted(i["number"] for i in issues)}) + "\n", encoding="utf-8")
    print(f"scored {len(submissions)} hand-ins; wrote {out}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--round", type=Path, default=ROUND)
    p.add_argument("--items", type=Path, default=OUTPUT / "pilot_items.jsonl")
    p.add_argument("--private-key", type=Path, default=PRIVATE_KEY)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("keys", help="make the key pair; prints the public key for round.json")
    i = sub.add_parser("intake")
    i.add_argument("--event", type=Path, required=True)
    i.add_argument("--reply", type=Path, required=True)
    f = sub.add_parser("fetch", help="needs GITHUB_REPOSITORY and GITHUB_TOKEN")
    f.add_argument("--output", type=Path, required=True)
    f.add_argument("--label", default="pilot-hand-in")
    c = sub.add_parser("close")
    c.add_argument("--issues", type=Path, required=True)
    c.add_argument("--key", type=Path, default=KEY)
    c.add_argument("--output", type=Path)
    c.add_argument("--force", action="store_true", help="score before the deadline (local testing only)")
    args = p.parse_args()
    if args.command == "keys":
        if args.private_key.exists():
            raise SystemExit(f"{args.private_key} exists; refusing to replace the round's key")
        print(make_keys(args.private_key))
    elif args.command == "intake":
        intake(args)
    elif args.command == "fetch":
        fetch(args)
    else:
        args.output = args.output or ROOT / "reports/review-pilot" / load_round(args.round)["round"]
        close(args)


if __name__ == "__main__":
    main()
