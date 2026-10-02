#!/usr/bin/env python3
"""Run the bundled scripts on the fixtures and check every trap against truth.json.
Exit code 0 only if everything passes.   python3 evals/run_evals.py"""
import csv, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, '..', 'skills', 'network-review', 'scripts')
FX = os.path.join(HERE, 'fixtures')
subprocess.run([sys.executable, os.path.join(HERE, 'make_fixtures.py')], check=True, capture_output=True)
T = json.load(open(os.path.join(FX, 'truth.json')))
out = tempfile.mkdtemp(prefix='quaiint-eval-')
results = []
def check(name, ok, detail=''):
    results.append((name, ok, detail))

# ---- signals
sig = subprocess.run([sys.executable, os.path.join(SCRIPTS, 'signals.py'), '--headers', os.path.join(FX, 'headers.jsonl'),
                      '--me', T['signals']['me'], '--out', out], capture_output=True, text=True)
check('signals runs', sig.returncode == 0, sig.stderr[-300:])
rel = list(csv.DictReader(open(os.path.join(out, 'relationships.csv')))) if sig.returncode == 0 else []
by = {r['name']: r for r in rel}
for status in ('still_in_touch', 'dormant', 'you_wrote_only'):
    for n in T['signals'][status]:
        check(f'signals: {n} is {status}', by.get(n, {}).get('status') == status, by.get(n, {}).get('status', 'missing'))
for e in T['signals']['excluded']:
    check(f'signals: ignores {e}', all(e not in (r['email'] + r['other_emails']) for r in rel))
for n, es in T['signals']['grouped'].items():
    r = by.get(n, {})
    check(f'signals: {n} grouped across addresses', set(es) <= {r.get('email')} | set(filter(None, r.get('other_emails', '').split('; '))))
cands = [r['name'] for r in csv.DictReader(open(os.path.join(out, 'reconnect-candidates.csv')))] if rel else []
check('signals: dormant friend tops reconnect candidates', cands[:1] == ['Theo Hale'], ', '.join(cands[:3]))

# ---- contacts
cmd = [sys.executable, os.path.join(SCRIPTS, 'contacts.py'), 'build', '--in', os.path.join(FX, 'exports'),
       '--bounces', os.path.join(FX, 'bounces.txt'), '--relationships', os.path.join(out, 'relationships.csv'), '--out', out]
b = subprocess.run(cmd, capture_output=True, text=True)
check('contacts runs', b.returncode == 0, b.stderr[-300:])
summary = json.load(open(os.path.join(out, 'summary.json'))) if b.returncode == 0 else {}
rows = []
for f in sorted(os.listdir(out)):
    if f.startswith('master-contacts-google-part'):
        rows += list(csv.DictReader(open(os.path.join(out, f), encoding='utf-8-sig')))
emails_of = lambda r: [v for k, v in r.items() if k and k.startswith('E-mail') and k.endswith('Value') and v]
named = {}
for r in rows:
    named.setdefault(f"{r['First Name']} {r['Last Name']}".strip(), []).append(r)
all_emails = {e for r in rows for e in emails_of(r)}
log = list(csv.DictReader(open(os.path.join(out, 'change-log.csv'))))
q = open(os.path.join(out, 'questions.md')).read()

check('switchboard colleagues stay separate', all(len(named.get(n, [])) == 1 for n in T['switchboard']) and
      not any(r['action'] == 'merged' and any(n in r['reason'] for n in T['switchboard'][1:]) for r in log))
check('cross-account duplicates merged', all(len(named.get(n, [])) == 1 and len(emails_of(named[n][0])) >= 2 for n in T['cross_account']))
check('same-name strangers asked, not merged', all(len(named.get(n, [])) == 2 and n in q for n in T['same_name_strangers']))
check('automated senders removed', not (set(T['automated']) & all_emails))
check('dead addresses removed', not (set(T['dead']) & all_emails), str(sorted(set(T['dead']) & all_emails)))
check('forwarding addresses added', set(T['forwards'].values()) <= all_emails)
check('vCard: new person added', T['vcf_new_person'] in named)
check('vCard: existing person merged, not duplicated', len(named.get(T['vcf_existing_person'], [])) == 1)
check('no-current-email people kept and asked about', summary.get('no_current_email') == 12 and 'No current email' in q)
check('import labels dropped, * myContacts kept', all('Imported' not in r['Labels'] and '* myContacts' in r['Labels'] for r in rows))
hdr = next(csv.reader(open(os.path.join(out, 'master-contacts-google-part1.csv'), encoding='utf-8-sig')))
check("output uses Google's header", hdr[:3] == ['First Name', 'Middle Name', 'Last Name'] and 'Labels' in hdr and 'E-mail 1 - Value' in hdr and 'Phonetic First Name' in hdr)
check('5-contact test file written', len(list(csv.DictReader(open(os.path.join(out, 'master-contacts-google-TEST-5.csv'), encoding='utf-8-sig')))) == 5)
check('original exports backed up', any(d.startswith('originals-') for d in os.listdir(out)))
check('every change logged with a reason', all(r['reason'] for r in log))
check('summary reports relationship labels actually applied', 'relationship_labels_applied' in summary)
check('email-history name matching a card at another address becomes a question',
      ('Theo Hale' not in named) or ('Same name in your email' in q and 'theo@oldstartup.com' in q))

# decisions round-trip: the person's answers are applied exactly
dec = {'different_people': [[f"{T['same_name_strangers'][0].split()[0].lower()}.{T['same_name_strangers'][0].split()[1].lower()}@oldagency.net"]],
       'let_go': [T['dead'][0]], 'labels': {}}
first_stranger = T['same_name_strangers'][0]
src_rows = list(csv.DictReader(open(os.path.join(FX, 'exports', 'old-company-account.csv'), encoding='utf-8-sig')))
mine = [r['E-mail 1 - Value'] for r in src_rows if f"{r['First Name']} {r['Last Name']}" == first_stranger]
theirs = [r['E-mail 1 - Value'] for r in csv.DictReader(open(os.path.join(FX, 'exports', 'personal-account.csv'), encoding='utf-8-sig'))
          if f"{r['First Name']} {r['Last Name']}" == first_stranger]
dec['different_people'] = [mine + theirs]
json.dump(dec, open(os.path.join(out, 'decisions.json'), 'w'))
out2 = out + '-2'
b2 = subprocess.run(cmd[:-1] + [out2, '--decisions', os.path.join(out, 'decisions.json')], capture_output=True, text=True)
q2 = open(os.path.join(out2, 'questions.md')).read() if b2.returncode == 0 else ''
check('decisions: answered same-name pair is not asked again', first_stranger not in q2.split('## No current')[0])
lg = os.path.join(out2, 'let-go.csv')
check('decisions: let-go person is removed and listed', os.path.exists(lg) and len(list(csv.reader(open(lg)))) == 2)

w = max(len(n) for n, _, _ in results)
for n, ok, d in results:
    print(f"{'PASS' if ok else 'FAIL'}  {n.ljust(w)}  {d if not ok else ''}")
fails = sum(1 for _, ok, _ in results if not ok)
print(f'\n{len(results) - fails}/{len(results)} passed')
sys.exit(1 if fails else 0)
