# Importing into Google Contacts

Do this with the person; they click.

1. Pick the master account (usually a personal one, since work accounts disappear). Confirm it's the
   one shown in the top right of contacts.google.com.
2. **Import → `master-contacts-google-TEST-5.csv`.** Open one of the five and check that the email,
   phone and labels are in their own fields, not dumped into Notes. If they're in Notes, stop: the
   header is wrong. Settings → Undo changes, then fix before going on.
3. Delete the five test contacts (or let Merge & fix catch them later).
4. Import each `master-contacts-google-partN.csv` in order. Google takes up to 3,000 per file; the
   parts are already split.
5. Check the total and the labels in the sidebar against `summary.json`.
6. Merge & fix: go one suggestion at a time; skip pairs they said are different people; never "Merge all".
   Skip "Add contact details". Those are usually old email signatures.
7. Anything wrong: Settings → **Undo changes** → a time before the import.

Second accounts (e.g. a work account): Google doesn't sync contacts between accounts. To give one a copy,
clear its contacts (they go to Trash for 30 days) and import the same files.
