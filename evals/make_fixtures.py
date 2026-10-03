#!/usr/bin/env python3
"""Build the eval fixtures: fake contact exports, pasted bounces and email headers,
each seeded with a known trap, plus truth.json with the right answers.
Everything here is invented. Deterministic (fixed seed)."""
import csv, json, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'network-review', 'scripts'))
from contacts import DEFAULT_BASE  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FX = os.path.join(HERE, 'fixtures')
random.seed(7)
os.makedirs(os.path.join(FX, 'exports'), exist_ok=True)

hdr = DEFAULT_BASE[:]
i = hdr.index('E-mail 1 - Value') + 1
hdr[i:i] = ['E-mail 2 - Label', 'E-mail 2 - Value']
first = "Ava Ben Cara Dev Eli Fay Gus Hana Ivan Jade Kofi Lena Milo Nia Owen Pia Quinn Rafa Sana Theo Uma Vik Wren Xavi Yara Zeke Aria Bo Cole Dina".split()
last = "Abbott Baker Chen Diaz Evans Fox Garcia Hale Ito Jones Khan Lopez Moss Nolan Ortiz Patel Quist Reyes Singh Tran Usher Vance Wong Xu Young Zane Ames Brook Cruz Dunn".split()
cos = ['acme.com', 'globex.com', 'initech.com', 'umbrella.co', 'hooli.com', 'vandelay.com', 'oldagency.net', 'piedpiper.io']

def row(fn, ln, emails=(), phones=(), org='', labels='* myContacts'):
    r = {k: '' for k in hdr}
    r.update({'First Name': fn, 'Last Name': ln, 'Organization Name': org, 'Labels': labels})
    for n, e in enumerate(emails, 1):
        r[f'E-mail {n} - Label'] = '* Work' if n == 1 else 'Home'; r[f'E-mail {n} - Value'] = e
    for n, p in enumerate(phones, 1):
        r['Phone 1 - Label'] = 'Work'; r['Phone 1 - Value'] = p
    return r

people, used = [], set()
while len(people) < 220:
    fn, ln = random.choice(first), random.choice(last)
    if (fn, ln) not in used:
        used.add((fn, ln)); people.append((fn, ln, random.choice(cos)))
email = lambda fn, ln, co: f'{fn.lower()}.{ln.lower()}@{co}'
A = [row(fn, ln, [email(fn, ln, co)], [f'(617) {random.randint(200, 999)}-{random.randint(1000, 9999)}'],
         co.split('.')[0].title(), '* myContacts ::: Imported 1/5/15 ::: Clients') for fn, ln, co in people]
truth = {}
# trap 1: six colleagues share an office switchboard; must NOT be merged
for r in A[:6]:
    r['Phone 1 - Value'] = '(212) 555-0100'
truth['switchboard'] = [f'{fn} {ln}' for fn, ln, _ in people[:6]]
# trap 2: the same 40 people in a second account, with a personal address; must be merged
B = []
for fn, ln, co in people[10:50]:
    B.append(row(fn, ln, [email(fn, ln, co), f'{fn.lower()}{ln.lower()}{random.randint(1, 99)}@gmail.com'], [], '',
                 '* myContacts ::: Imported on 6/22'))
truth['cross_account'] = [f'{fn} {ln}' for fn, ln, _ in people[10:50]]
# trap 3: same full name, different person at a hospital; must go to questions, not be merged
for fn, ln, co in people[60:63]:
    B.append(row(fn, ln, [f'{fn[0].lower()}{ln.lower()}@cityhospital.org'], ['(503) 444-1212'], 'City Hospital'))
truth['same_name_strangers'] = [f'{fn} {ln}' for fn, ln, _ in people[60:63]]
# trap 4: automated senders; must be removed
junk = ['noreply@calendar.hooli.com', 'notifications@billing.acme.com', 'support@initech.com']
for j in junk:
    A.append(row('', '', [j]))
truth['automated'] = junk
# trap 5: 12 hard bounces and 3 "no longer with" auto-replies that give a new address
dead = [email(fn, ln, co) for fn, ln, co in people[100:115]]
truth['dead'] = dead
truth['forwards'] = {d: d.split('@')[0] + '@newco.com' for d in dead[12:]}
# trap 6: a vCard export with one new person and one existing person
vcf = ('BEGIN:VCARD\nVERSION:3.0\nN:Quist;Rafa;;;\nFN:Rafa Quist\nEMAIL;TYPE=HOME:rafa.quist@fastmail.com\nTEL:+1 415 555 0199\nEND:VCARD\n'
       f'BEGIN:VCARD\nVERSION:3.0\nN:{people[70][1]};{people[70][0]};;;\nFN:{people[70][0]} {people[70][1]}\n'
       f'EMAIL:{email(*people[70])}\nTEL:+1 646 555 0123\nEND:VCARD\n')
truth['vcf_new_person'] = 'Rafa Quist'
truth['vcf_existing_person'] = f'{people[70][0]} {people[70][1]}'

for name, rows in (('old-company-account.csv', A), ('personal-account.csv', B)):
    with open(os.path.join(FX, 'exports', name), 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=hdr); w.writeheader(); w.writerows(rows)
open(os.path.join(FX, 'exports', 'phone.vcf'), 'w').write(vcf)
with open(os.path.join(FX, 'bounces.txt'), 'w') as f:
    f.write('# pasted from my inbox\n')
    for d in dead[:12]:
        f.write(f'Delivery Status Notification (Failure): Address not found: {d}\n')
    for d in dead[12:]:
        u = d.split('@')[0]
        f.write(f'Automatic reply from {d}: "{u.replace(".", " ").title()} is no longer with the company. Please contact {u}@newco.com"\n')

# trap 7: LinkedIn export (notes above the header; most rows have no email)
li = ['Notes:', '"When exporting your connection data, you may notice that some of the email addresses are missing."', '',
      'First Name,Last Name,URL,Email Address,Company,Position,Connected On']
fn, ln, co = people[80]
li.append(f'{fn},{ln},https://www.linkedin.com/in/{fn.lower()}{ln.lower()},{email(fn, ln, co)},{co.split(".")[0].title()},VP Sales,04 Mar 2015')
fn, ln, co = people[81]          # no email, same name and company as an existing card: should attach
li.append(f'{fn},{ln},https://www.linkedin.com/in/{fn.lower()}-{ln.lower()},,{co.split(".")[0].title()},Director,12 Jan 2019')
li.append('Juno,Okafor,https://www.linkedin.com/in/junookafor,,Stripe,Engineer,02 Feb 2024')   # new, no email
li.append('Remy,Laurent,https://www.linkedin.com/in/remylaurent,remy@laurent.studio,Laurent Studio,Founder,09 Sep 2022')
open(os.path.join(FX, 'exports', 'Connections.csv'), 'w').write('\n'.join(li) + '\n')
truth['linkedin'] = {'attached_by_email': f'{people[80][0]} {people[80][1]}', 'attached_by_name_company': f'{people[81][0]} {people[81][1]}',
                     'new_people': ['Juno Okafor', 'Remy Laurent']}
# trap 8: newsletter exports with subscription status
fn, ln, co = people[90]; fn2, ln2, co2 = people[91]
open(os.path.join(FX, 'exports', 'substack-subscribers.csv'), 'w').write(
    'email,name,active_subscription,email_disabled,subscription_created_at\n'
    f'{email(fn, ln, co)},{fn} {ln},true,false,2026-01-02\n'
    f'{email(fn2, ln2, co2)},{fn2} {ln2},false,true,2025-06-01\n'
    'newreader@fastmail.com,New Reader,true,false,2026-09-30\n')
fn3, ln3, co3 = people[92]
open(os.path.join(FX, 'exports', 'buttondown-export.csv'), 'w').write(
    'email,subscriber_type,creation_date\n'
    f'{email(fn3, ln3, co3)},unsubscribed,2024-02-02\n'
    'reader2@proton.me,regular,2025-03-03\n')
open(os.path.join(FX, 'do-not-email.txt'), 'w').write('# people who asked\nasked.out@example.org  # asked to be removed\n' + f'{email(*people[93])}  # family\n')
truth['newsletters'] = {'active': f'{fn} {ln}', 'unsubscribed': [email(fn2, ln2, co2), email(fn3, ln3, co3)],
                        'new_subscribers': ['newreader@fastmail.com', 'reader2@proton.me'], 'dne_file': email(*people[93])}

# email headers for signals.py
me = 'me@example.com'
H = []
def msg(date, frm, to, cc=None, subject='hi'):
    H.append({'date': date, 'from': frm, 'to': to, 'cc': cc or [], 'subject': subject})
for y in (2024, 2025, 2026):                              # still in touch
    msg(f'{y}-03-01T10:00:00Z', me, ['Nia Lopez <nia@lopez.family>'])
    msg(f'{y}-03-02T10:00:00Z', 'Nia Lopez <nia@lopez.family>', [me])
for y in range(2014, 2019):                                # dormant: close, then quiet since 2018
    for k in range(6):
        msg(f'{y}-0{k + 1}-05T10:00:00Z', me, ['Theo Hale <theo@oldstartup.com>'])
        msg(f'{y}-0{k + 1}-06T10:00:00Z', 'Theo Hale <theo@oldstartup.com>', [me])
msg('2019-02-01T10:00:00Z', me, ['Theo Hale <theo.hale@gmail.com>'])   # same person, second address
msg('2019-02-02T10:00:00Z', 'Theo Hale <theo.hale@gmail.com>', [me])
for k in range(5):                                         # you wrote, never answered
    msg(f'2025-0{k + 1}-01T10:00:00Z', me, ['Gus Ames <gus@vcfirm.com>'])
for k in range(8):                                         # automated sender
    msg(f'2026-0{k + 1}-01T10:00:00Z', 'Hooli News <newsletter@news.hooli.com>', [me])
msg('2026-05-01T10:00:00Z', me, [f'p{k}@blast.example' for k in range(10)])   # group blast, ignored
for k in range(4):                                         # transactional, dormant (for the AI to judge)
    msg(f'2019-0{k + 1}-01T10:00:00Z', me, ['Lena Ortiz <lena@lawfirm.com>'], subject='Re: Series A closing docs')
    msg(f'2019-0{k + 1}-02T10:00:00Z', 'Lena Ortiz <lena@lawfirm.com>', [me], subject='Re: Series A closing docs')
with open(os.path.join(FX, 'headers.jsonl'), 'w') as f:
    for m in H:
        f.write(json.dumps(m) + '\n')
truth['signals'] = {'me': me, 'still_in_touch': ['Nia Lopez'], 'dormant': ['Theo Hale', 'Lena Ortiz'],
                    'you_wrote_only': ['Gus Ames'], 'excluded': ['newsletter@news.hooli.com', 'p0@blast.example'],
                    'grouped': {'Theo Hale': ['theo@oldstartup.com', 'theo.hale@gmail.com']}}
json.dump(truth, open(os.path.join(FX, 'truth.json'), 'w'), indent=1)
print('fixtures written to', FX)
