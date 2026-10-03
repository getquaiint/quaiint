# Evals

## Script checks (every change)
`python3 evals/run_evals.py` rebuilds the fixtures (fake exports, pasted bounces, email headers, each
seeded with a known trap) and checks both scripts against `fixtures/truth.json`. All 38 must pass.

## End-to-end with a fresh agent (before each release)
Give a fresh agent session nothing but the skill folder and `evals/fixtures/`, and say:

> Run a network review. My contact exports are in evals/fixtures/exports, pasted bounces in
> evals/fixtures/bounces.txt, and email headers in evals/fixtures/headers.jsonl; my address is
> me@example.com. I'm not available for questions: write them to questions.md and continue.

Pass if it: uses the bundled scripts rather than rewriting them; does not merge the six switchboard
colleagues; asks about the three same-name pairs; leaves Lena Ortiz (a closing lawyer) off the Reconnect
list while keeping Theo Hale on it; never modifies the fixtures; and produces review.md, the import parts,
the test file, change-log.csv and questions.md. Run it on at least two different models.
