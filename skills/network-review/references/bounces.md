# Finding bounces and "no longer with" replies through an email connector

Only with the person's yes, and only these notices. Don't open other mail.

## Searches (Gmail syntax; adapt for others)
Run each, paging through results (metadata or snippet views are enough; you rarely need full bodies):
1. Hard and soft bounces: `from:(mailer-daemon OR postmaster) newer_than:3y`
2. Left the company: `subject:("Automatic reply" OR "Auto-Reply" OR "Out of office" OR "Undeliverable") ("no longer with" OR "has left" OR "no longer at" OR "is no longer") newer_than:3y`
3. Exchange/Outlook failures: `subject:(Undeliverable OR "Delivery has failed" OR "Mail delivery failed") newer_than:3y`

With Claude's Gmail connector: `search_threads` with `pageSize: 50`; the snippet usually contains the failed
address and the reason. Open a message (`get_thread`, plain text) only when the snippet doesn't show the
address.

## Write bounces.txt
One line per notice: `sender | subject | snippet`. For example:
```
mailer-daemon@googlemail.com | Delivery Status Notification (Failure) | Address not found Your message wasn't delivered to jane@oldco.com because the address couldn't be found
pmcevoy@oldbank.com | Automatic reply: hello | I am no longer with Old Bank. Please contact me at pat@newbank.com
```
`contacts.py` skips system senders (mailer-daemon, postmaster), treats "no longer with" as dead, keeps a
new address when the reply gives one, and treats mailbox-full or "will retry" as temporary (kept, watched).
Out-of-office replies without "no longer" are ignored.

Tell the person how many you found in one sentence ("31 dead addresses, 4 people who moved on, 2 new
addresses"), then continue.
