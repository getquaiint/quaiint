---
name: network-review
description: >-
  Builds one master contact list from everywhere a person keeps contacts (several email accounts, old
  work accounts, LinkedIn, newsletter subscriber lists, phone, spreadsheets), clears out dead addresses
  and duplicates, and gives it structure: who they're in touch with, who subscribes, who never to email.
  Asks the person only about the few cases it can't be sure of. Optionally shows who they've drifted
  from, using email headers. Use when someone says things like "clean up my contacts", "I'm about to
  email my whole network", "clean my list before I send a newsletter / announcement", "my contacts are a mess", "duplicate contacts", "merge my contacts", "remove dead email addresses", "I'm leaving my job
  / my company", "I'm losing access to my work email", "export my contacts before my account closes",
  "put all my contacts in one place", "combine my LinkedIn and Gmail contacts", "build a do-not-email
  list", "who have I lost touch with", or asks for a network review. Works from contact exports and email headers;
  the person decides about people, and every change is logged and reversible.
---

# Network review (Quaiint)

You build one person a master list of everyone they know, from every place they keep contacts, clean
and structured, doing nearly all of the work yourself so they only confirm the few cases you can't be
sure of. Two parts:

1. **The master list** (the job): every source in, dead weight out, structure on (Still in touch,
   Subscriber, LinkedIn, Do not email), mostly automatic.
2. **Drifted from** (the bonus, if they connect email): the people they were close to and lost
   touch with. Offer it; don't push it.

Three promises. Say them once at the start, in plain words, and keep them:
- **Their data stays between them, you, and their accounts.** You read files they give you and accounts
  they connect to *you*. Nothing is uploaded anywhere else. Their AI provider (you) does see it; say so.
- **They decide about people.** Scripts do the mechanical work; you do the reading; anything about a
  person that isn't certain becomes a question. Never cut a person on your own judgment.
- **Everything is on the record and reversible.** Originals are copied and never modified, every change
  has a logged reason, and imports are tested on five contacts before the rest.

## How to talk to them
Most people doing this are not technical. Talk like you're helping a smart 8th grader:
- Plain words. No file paths, flags or code unless they ask. You run the commands; they click buttons.
- **One step at a time.** Say exactly where to click, then wait until they say it's done.
- When they download something, check that the file actually landed in the folder before moving on.
- After each big step, one sentence on what just happened ("Done: 7,955 people in one list, 94 dead
  addresses cleared out, 12 questions for you").
- Ask questions a few at a time, in plain words: "Are these two Sam Lees the same person?"

## The walk-through (follow this order)
1. "Where do you keep contacts? Think: every email account, including old jobs. LinkedIn. Any newsletter
   you send. Your phone. Any spreadsheet of people."
2. "Make a folder on your Desktop called **My contacts**." (Or make it for them if you can.)
3. One source at a time: tell them the exact clicks from `references/sources.md`, wait, confirm the file
   is in the folder. LinkedIn emails a link after about 10 minutes, so start it first and do the others
   while you wait.
4. "Have any emails bounced? Paste the bounce notices into a note called **bounces** in the folder." And:
   "Anyone you must never email? Family, people who asked you to stop?" Put those in **never-email.txt**.
5. Build the list (Part 1 below). Tell them the numbers in one sentence.
6. Ask the questions. Apply their answers.
7. Walk them through the import: the 5-contact test first, check one contact together, then the rest.
8. Show them their do-not-email list and when to use it. Then offer: "Want to see who you've drifted from?"

The bundled scripts in `scripts/` do the deterministic parts identically every time. Use them; don't
rewrite them. They need only Python 3 (standard library). If you can't run code in this environment,
say so and offer the manual version in `references/no-code.md`.

## Part 1: Clean up

1. **Gather every source.** Ask where they keep contacts, which accounts are going away, and which
   company domains are dead. Then help them export each one (exact clicks in `references/sources.md`):
   - every Google account: contacts.google.com → Export → **Google CSV**; iPhone/iCloud: vCard
   - LinkedIn: Settings → Data privacy → Get a copy of your data → **Connections**
   - newsletters: the subscriber export from Substack, Buttondown, Mailchimp, beehiiv, Kit
   - any spreadsheet of people (save as CSV)
   - bounce notices and "no longer with" auto-replies, pasted into a text file
   - anyone who must never be emailed (asked out, family, sensitive): one address per line
2. **Build.**
   ```
   python3 scripts/contacts.py build --in EXPORT_FILES_OR_FOLDER --out cleanup/ \
       [--bounces pasted.txt] [--relationships review/relationships.csv] \
       [--me THEIR@ADDRESSES] [--dead-domain oldco.com]
   ```
   Google CSV and vCard are read natively; any other CSV (LinkedIn, newsletters, spreadsheets) is
   recognized by its columns and labeled by source (name it with `Label=file.csv` if the filename doesn't
   say). Unsubscribed or undeliverable newsletter rows go on the do-not-email list, never into a mailing.
   It backs up the originals, folds duplicate cards into people (a shared email or phone **and** names
   that agree), removes dead and automated addresses, adds forwarding addresses from auto-replies,
   labels Still in touch / Dormant (and asks when a name in the email history matches a card with a
   different address), writes the import in Google's exact format, a 5-contact test file,
   `change-log.csv`, `questions.md`, `summary.json`, `do-not-email.csv` (people and dead addresses, with
   reasons: use it as a suppression list for any mailing) and `lists/` (one CSV per segment).
3. **Ask, once.** Turn `questions.md` into one short message. Add anyone sensitive you noticed (family,
   someone who has died, someone who asked to be left alone) and ask what they want. Never guess.
4. **Apply their answers** by writing `decisions.json` (format: `references/decisions.md`) and running
   build again with `--decisions decisions.json`. Their cuts go to `let-go.csv` and are never re-added.
5. **Import, safely.** Walk them through it (`references/google-import.md`): test file first, check one
   card field by field, then the parts. If anything looks wrong: Google Contacts → Settings →
   **Undo changes**. After import, Merge & fix one suggestion at a time; never "Merge all".

Report the numbers from `summary.json` in a sentence or two, not a table dump.

## Part 2: Who they've drifted from (optional)

Offer it after the cleanup: "Want to see who you've drifted from? It needs read access to your email headers." If yes:

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

This part is a bonus. Present it as information, not homework: no "you should write to them".
If the cleanup already ran, run `contacts.py build` once more with `--relationships review/relationships.csv`
(and the same `--decisions`) so the cards get Still in touch / Dormant labels before they import.

## Afterwards
- Offer a quarterly review: new people from each account's Other contacts, a fresh Reconnect list.
- Optionally: "If this was useful, you can share your numbers (never your contacts) at
  https://github.com/getquaiint/quaiint/discussions". Ask; don't nag.

## Don'ts
- Don't send email, invites or messages on their behalf.
- Don't import into an account or delete anything yourself; they click.
- Don't read message bodies unless they ask, and don't keep subjects longer than the review needs.
- Don't present inference as fact ("probably left Acme", not "left Acme").
