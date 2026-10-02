# decisions.json

Write the person's answers here, then run `contacts.py build ... --decisions decisions.json`.
Identify people by any email address on their card. Every field is optional.

```json
{
  "same_person":       [["sam@oldco.com", "sam.lee@gmail.com"]],
  "different_people":  [["jo@venturefirm.com", "jsmith@university.edu"]],
  "remove_addresses":  ["old.address@formerjob.com"],
  "add_addresses":     {"pat@hotmail.com": ["pat.new@gmail.com"]},
  "let_go":            ["someone@x.com"],
  "leave_untouched":   ["family.member@x.com"],
  "labels":            {"brother@x.com": ["Do not contact"]}
}
```

- `different_people`: the pair stops being asked about.
- `let_go`: removed from the master list and written to `let-go.csv`. Never re-added on later runs
  (keep the file).
- `leave_untouched`: copied through exactly as exported (for family, someone who has died, anyone they
  want left alone).
