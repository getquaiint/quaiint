# Quaiint: two-week launch sprint

**Question to answer:** do people who aren't Dave install it, finish a review, and want help?

## Before day 1 (Dave, about 45 minutes)
| | Step | Why |
|---|---|---|
| 1 | Buy **quaiint.com** (available as of 10/2) on Vercel | The site, the form, and the address on every link |
| 2 | Create the GitHub org **quaiint**, then a **public** repo `quaiint/quaiint` (Claude pushes the code once it exists) | `npx skills add quaiint/quaiint` and skills.sh need a public repo |
| 3 | Create a **private** repo `quaiint/leads` and a fine-grained token with Issues read/write on it only | Every "run it with us" request becomes an issue: emailed to you, private, permanent |
| 4 | New Vercel project from `site/`, add env vars `GITHUB_TOKEN` and `LEADS_REPO=quaiint/leads`, attach quaiint.com | Claude can do this with the Vercel CLI once you OK it |
| 5 | Run your own reconnect review (`"Who should I reconnect with?"`) and write to 3 people from it | You need a true story before telling one |

## Days 1–14
| Day | Channel | What |
|---|---|---|
| 1 (Wed 10/7) | Launch check | Claude runs the evals, a fresh-agent end-to-end test, and a test install from the public repo; flips the davebalter.com footer line on |
| 1 | LinkedIn feed (7,880 followers) | Launch post in your voice: the afternoon you found 1,015 people your address book never saved and 129 dead addresses. Link in the first comment |
| 2 (Thu 10/8) | LinkedIn newsletter (327) | One-line P.S. under the issue |
| 3–5 | Direct | Personal notes to ~20 people you know are mid-transition (left a company, sold one). Offer to run it with them |
| 4 | skills.sh + GitHub lists | Confirm the skills.sh listing; open PRs to the awesome-claude-skills lists |
| 6 (Tue 10/13) | Substack (238) + davebalter.com | A Mostly True Story about one reconnection, if it happened and you want to tell it. Footer line on every story page |
| 8 | Hacker News | "Show HN: an Agent Skill that finds who you've drifted from (no server, full change log)", only if days 1–7 show any pull |
| 2, 5, 9, 12 | Measurement | Claude logs installs, stars, site visits, requests and shared results in `LOG.md` |

## What counts
| Signal | Where it's read |
|---|---|
| Installs | skills.sh install count; GitHub clones and traffic (the repo's Insights) |
| Interest | GitHub stars, site visits (Vercel Analytics), visits from the davebalter.com footer (`utm_source=davebalter`) |
| Completed reviews | Results shared in GitHub Discussions; replies to your notes |
| Want help | Issues in `quaiint/leads` |

## Go / no-go on day 14
- **Go** (build the done-with-you offer and a price per completed review): **100+ installs, 15+ completed
  reviews, 5+ requests for help.**
- **Iterate** (fix what the feedback says, run two more weeks): installs but few completed reviews. That
  means setup friction.
- **No-go** (keep it as your own quarterly tool): under 30 installs and no requests.

## Already done (10/2)
- Skill reworked so the reconnect list comes first, with descriptions written in people's words
- Bundled, tested scripts, so the AI follows procedure instead of improvising: `signals.py` reads 80k
  messages in 15 seconds; `contacts.py` writes Google's exact import format and loses no fields
- 28 eval checks pass. A fresh agent ran the current skill end to end (Sonnet) and the first version (Opus); the gaps they found are fixed
- Site with the install command, plain privacy wording, a working request form (once deployed), and an example reconnect list
- davebalter.com footer line on branch `quaiint-footer`, switched off until launch
