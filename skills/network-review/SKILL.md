---
name: network-review
description: >-
  Reviews a person's network and contacts: who they've drifted from and should reconnect with, plus a
  cleanup of their address book across every account (dead addresses, duplicates, people who moved on).
  Use when someone says things like "who should I reconnect with", "who have I lost touch with",
  "my contacts are a mess", "duplicate contacts", "merge my contacts", "clean up my address book",
  "I'm leaving my job / my company", "I'm losing access to my work email", "export my contacts before
  my account closes", or asks for a network review. Works from contact exports and email headers;
  the person decides about people, and every change is logged and reversible.
---

# Network review (Quaiint)

You help one person see their network clearly. Two acts, in this order:

1. **Reconnect** (the payoff, minutes): who they were close to and have drifted from.
2. **Clean up** (the utility, optional): one accurate contact list across every account.

Three promises. Say them once at the start, in plain words, and keep them:
- **Their data stays between them, you, and their accounts.** You read files they give you and accounts
  they connect to *you*. Nothing is uploaded anywhere else. Their AI provider (you) does see it; say so.
- **They decide about people.** Scripts do the mechanical work; you do the reading; anything about a
  person that isn't certain becomes a question. Never cut a person on your own judgment.
- **Everything is on the record and reversible.** Originals are copied and never modified, every change
  has a logged reason, and imports are tested on five contacts before the rest.

The bundled scripts in `scripts/` do the deterministic parts identically every time. Use them; don't
rewrite them. They need only Python 3 (standard library). If you can't run code in this environment,
say so and offer the manual version in `references/no-code.md`.

## Act 1: Reconnect

**Get email headers** (who, when; never message bodies unless they ask). Fastest first:
- **An email connector is available** (e.g. Gmail): pull metadata for their sent mail from 2 to 8 years
  ago, plus the last 2 years (to know who they're still in touch with). Write one JSON line per message to
  `headers.jsonl`. Recipe and limits: `references/headers.md`.
- **No connector**: ask for a mailbox export (Google Takeout → Mail → .mbox; Outlook/Apple → .mbox).
  Sent mail alone is enough to start.

Run:
```
python3 scripts/signals.py --headers headers.jsonl [--mbox Sent.mbox] --me THEIR@ADDRESSES --out review/ [--subjects]
```
Ask before using `--subjects`: subject lines help you tell friends from deal counterparties, but they're
more personal than names and dates.

**Then use judgment** on `reconnect-candidates.csv` (strongest dormant relationships first):
- Drop obvious transactions (lawyers on a closing, vendors, recruiters) and anyone in the sensitive list.
- Pick 10 to 15. If there are fewer good ones, list only those, say why (usually too little history),
  and offer to pull more: older sent mail, another account. Never pad the list. For each, one line: who they are to the person, when it went quiet, and why now might be
  a good moment if you can tell (a new job, a shared interest). Don't invent facts.
- Write `review/review.md` (template: `references/review-template.md`) and show it.

Research on dormant ties (Levin, Walter & Murnighan, 2011) found reconnecting is often as useful as
talking to current contacts, takes less time, and brings fresher information. Mention it once, briefly.

Ask: **"Want me to clean up your contact list too?"** Act 2 is optional.

## Act 2: Clean up

1. **Gather.** Ask which accounts they use, which are going away, and which company domains are dead.
   For each account: contacts.google.com → Export → **Google CSV** (iCloud: vCard). Ask them to paste or
   export bounce notices and "no longer with" auto-replies if they have them.
2. **Build.**
   ```
   python3 scripts/contacts.py build --in EXPORT_FILES_OR_FOLDER --out cleanup/ \
       [--bounces pasted.txt] [--relationships review/relationships.csv] \
       [--me THEIR@ADDRESSES] [--dead-domain oldco.com]
   ```
   It backs up the originals, folds duplicate cards into people (a shared email or phone **and** names
   that agree), removes dead and automated addresses, adds forwarding addresses from auto-replies,
   labels Still in touch / Dormant (and asks when a name in the email history matches a card with a
   different address), writes the import in Google's exact format, a 5-contact test file,
   `change-log.csv`, `questions.md` and `summary.json`.
3. **Ask, once.** Turn `questions.md` into one short message. Add anyone sensitive you noticed (family,
   someone who has died, someone who asked to be left alone) and ask what they want. Never guess.
4. **Apply their answers** by writing `decisions.json` (format: `references/decisions.md`) and running
   build again with `--decisions decisions.json`. Their cuts go to `let-go.csv` and are never re-added.
5. **Import, safely.** Walk them through it (`references/google-import.md`): test file first, check one
   card field by field, then the parts. If anything looks wrong: Google Contacts → Settings →
   **Undo changes**. After import, Merge & fix one suggestion at a time; never "Merge all".

Report the numbers from `summary.json` in a sentence or two, not a table dump.

## Afterwards
- Offer a quarterly review: new people from each account's Other contacts, a fresh Reconnect list.
- Optionally: "If this was useful, you can share your numbers (never your contacts) at
  https://github.com/getquaiint/quaiint/discussions". Ask; don't nag.

## Don'ts
- Don't send email, invites or messages on their behalf.
- Don't import into an account or delete anything yourself; they click.
- Don't read message bodies unless they ask, and don't keep subjects longer than the review needs.
- Don't present inference as fact ("probably left Acme", not "left Acme").
