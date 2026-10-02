# Getting email headers

Only senders, recipients and dates (and subjects, if the person agrees). Never message bodies unless
they ask.

## With an email connector (fastest)
Most assistants with a Gmail connector can search threads and return metadata. With Claude's Gmail
connector, for example: `search_threads` with `view: THREAD_VIEW_METADATA_ONLY`, `pageSize: 50`, paging
with `pageToken`.

Pull, in this order, stopping when you have enough:
1. `in:sent newer_than:2y`: who they're still in touch with.
2. `in:sent older_than:2y newer_than:8y`: who they've drifted from. Around 1,000 threads (20 pages) is
   enough for a first Reconnect list; say if you sampled.
3. Optional: `-in:sent newer_than:8y -category:promotions -category:social -category:updates` for
   replies they received.

Write one JSON object per message (not per thread) to `headers.jsonl`:
```
{"date": "2021-03-04T15:02:00Z", "from": "Ana Ruiz <ana@x.com>", "to": ["me@y.com"], "cc": [], "subject": "..."}
```
Leave `subject` out unless they said yes to subjects.

## Without a connector
Google Takeout (takeout.google.com) → deselect all → Mail → choose "Sent" (and optionally "Inbox")
→ export as .mbox. Large mailboxes are fine: `signals.py --mbox` streams headers and skips bodies
(about 80,000 messages in 15 seconds). Apple Mail and Outlook can also export .mbox.

## Their own addresses
Ask for every address they've sent from (personal and old work). Pass them all with `--me`, or the
script guesses the most common sender.
