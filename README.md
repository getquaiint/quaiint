# Quaiint

**Every contact you have, in one list you can trust.**

Quaiint is a free [Agent Skill](https://agentskills.io) for the AI assistant you already use: Claude,
Codex, Cursor, Gemini CLI, or any tool that reads `SKILL.md`.

1. **One master list.** Contacts from every email account (old jobs included), LinkedIn, your newsletter
   subscribers, your phone and your spreadsheets become one list: dead addresses gone, duplicates folded,
   people who moved on flagged, and structure on top (still in touch, subscriber, LinkedIn, **do not
   email**). Your AI handles what it's sure about and asks you only about the rest: a handful of
   questions, not thousands of rows.
2. **Who you've drifted from** (optional). If you connect your email, it also shows the people you were
   close to and lost touch with.

You decide about people. Every change is logged with a reason, your originals are never modified, and
the import is tested on five contacts first.

## Install

```
npx skills add getquaiint/quaiint
```

Or copy `skills/network-review/` into your assistant's skills folder (Claude Code: `~/.claude/skills/`).

Then say: **"Clean up my contacts."**

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
