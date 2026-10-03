# Quaiint

**Every contact you have, in one list you can trust.**

Quaiint is a free [Agent Skill](https://agentskills.io) for the AI assistant you already use: Claude,
Codex, Cursor, Gemini CLI, or any tool that reads `SKILL.md`.

- **Free.** No plan, no trial, no account.
- **Not an app.** A set of instructions your assistant follows, plus two small open scripts.
- **Never asks for a password.** You export your own contacts; it works on those files on your computer.

1. **One master list.** Contacts from every email account (old jobs included), LinkedIn, your newsletter
   subscribers, your phone and your spreadsheets become one list: dead addresses gone, duplicates folded,
   people who moved on flagged, and structure on top (still in touch, subscriber, LinkedIn, **do not
   email**). Your AI handles what it's sure about and asks you only about the rest: a handful of
   questions, not thousands of rows.
2. **Who you've drifted from** (optional). If you connect your email, it also shows the people you were
   close to and lost touch with.

You decide about people. Every change is logged with a reason, your originals are never modified, and
the import is tested on five contacts first.

## How to do it (about an hour, mostly waiting for downloads)

1. **Open your AI assistant.** Claude Code, Codex, Cursor, or any assistant that uses skills.
2. **Add the skill:** `npx skills add getquaiint/quaiint` (or ask your assistant to install it).
3. **Make a folder on your Desktop called "My contacts."**
4. **Download your contacts from each place into it:** each Google account (contacts.google.com → Export →
   Google CSV), LinkedIn (Settings → Data privacy → Get a copy of your data → Connections), your newsletter
   (Subscribers → Export), iPhone (icloud.com/contacts → Export vCard). Not sure how? Ask your assistant.
5. **Bounced emails:** if your assistant is connected to your email, it finds bounces and "no longer with"
   replies for you, reading only those notices. Otherwise, paste any bounce notices into a note called "bounces".
6. **Tell your assistant:** "Build my master contact list from the My contacts folder on my Desktop."
7. **Answer its questions.** Usually a handful. It handles the rest.
8. **Import the list:** test file first at contacts.google.com → Import, check one contact, then the rest.
   Changed your mind? Settings → Undo changes.

Manual install: copy `skills/network-review/` into your assistant's skills folder (Claude Code: `~/.claude/skills/`).

## What it needs
- **Exports** from wherever you keep contacts: Google (each account), iCloud, LinkedIn, Substack,
  Buttondown, Mailchimp, any CRM or spreadsheet. Clicks for each: `references/sources.md`.
- **Email headers**, only for the optional drifted-from list: an email connector in your assistant (e.g.
  Gmail), or a mailbox export (Google Takeout → Mail → .mbox). Senders, recipients and dates only, never
  message bodies unless you ask.
- An assistant that can run Python 3 (standard library only). Without one, the skill offers a rougher
  manual version.

## Privacy
Quaiint has no server. Your contacts and mail stay between you, your AI assistant and your accounts.
Your AI provider does see what you give your assistant, so use one you trust with your email.

## What's inside
| | |
|---|---|
| `skills/network-review/SKILL.md` | The instructions your assistant follows |
| `scripts/signals.py` | Who you're still in touch with, who's dormant, reconnect candidates (headers only) |
| `scripts/contacts.py` | The cleanup: merging, dead addresses, labels, Google-format import, change log |
| `references/` | Header recipes, import steps, the decisions format, the review template |
| `evals/` | Fake data seeded with known traps and the checks every release must pass |

## The traps it's built to avoid
These are real ones, from the first run:
- **Office switchboards fuse colleagues.** A shared phone number alone never merges two people; names
  have to agree too.
- **Same name ≠ same person.** Two Sam Lees at different companies go to you as a question.
- **Google's importer dumps fields into Notes** if the header isn't exactly its own. The output copies
  your export's header, and you test five contacts first.
- **Work volume isn't closeness.** A colleague with 4,000 emails shouldn't outrank a friend you wrote 40
  times. Strength is measured on a log scale, with reciprocity and how long you've known someone.

## Run the evals
```
python3 evals/run_evals.py
```
38 checks across both scripts. See `evals/README.md` for the end-to-end test with a fresh agent.

## Share how it went
Numbers only, never contacts: [Discussions](https://github.com/getquaiint/quaiint/discussions).
Going through a career change and want help with your first review? Open a discussion or write to the
address on [the site](https://quaiint.com).

MIT licensed.
