# Exporting contacts from each source

Put every export in one folder and pass the folder to `contacts.py build --in`.

| Source | Where | File |
|---|---|---|
| Google (each account) | contacts.google.com → Export → Contacts (and Other contacts, if they want people they've emailed) → **Google CSV** | contacts.csv |
| iPhone / iCloud | icloud.com/contacts → select all → ⚙ → Export vCard | .vcf |
| Outlook | Outlook.com → People → Manage → Export contacts | CSV |
| LinkedIn | Settings → Data privacy → Get a copy of your data → **Connections** (arrives by email in ~10 minutes) | Connections.csv |
| Substack | Dashboard → Subscribers → Export | CSV |
| Buttondown | Subscribers → Export | CSV |
| Mailchimp | Audience → All contacts → Export Audience | CSV (subscribed/unsubscribed/cleaned files) |
| beehiiv / Kit | Subscribers → Export | CSV |
| HubSpot or another CRM | Contacts → Export | CSV |
| A spreadsheet | File → Download → CSV | CSV |

Notes
- LinkedIn only includes email addresses for connections who allow it (often a few percent). Connections
  without an email still come in: they attach to an existing person when the name and company agree, and
  otherwise become new cards labeled LinkedIn with their profile link.
- Newsletter exports carry subscription status. Unsubscribed, undeliverable, cleaned or bounced rows go
  on the do-not-email list, never into a mailing.
- If a filename doesn't say what it is, name it on the command line: `"Board list=board.csv"`.
