#!/usr/bin/env python3
"""Quaiint contacts engine: the deterministic half of a network review.

Reads contact exports (Google CSV, vCard) plus any pasted bounce / auto-reply text,
and writes one clean master list in Google's own CSV format, a change log, and one
batch of questions for the person. It never decides about people: anything that
needs judgment goes to questions.md, and the person's answers come back in via
--decisions.

    python3 contacts.py build  --in EXPORTS... --out OUT [--bounces FILE...]
                               [--relationships relationships.csv] [--decisions decisions.json]
                               [--me you@x.com ...] [--dead-domain oldco.com ...]
    python3 contacts.py header --in some-google-export.csv     # print the header it will copy

Standard library only (Python 3.8+). Nothing is sent anywhere.
"""
import argparse, collections, csv, datetime, json, os, re, shutil, sys

EMAIL = re.compile(r"[A-Za-z0-9._%+'-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
AUTOMATED = re.compile(
    r"(^|[._-])(no-?reply|do-?not-?reply|donotreply|notifications?|notify|mailer-daemon|postmaster|bounces?|"
    r"billing|invoices?|receipts?|alerts?|automated|calendar-notification)([._-]|@)"
    r"|@(reply|bounce|em|email|mail|e|news|info)\d*\.(?!edu)|@docs\.google\.|@facebookmail\.|@linkedin\.com$"
    r"|^[0-9a-f]{8,}[_-]", re.I)
ROLE = re.compile(r"^(support|help|info|hello|team|sales|admin|office|contact|jobs|careers|press|media|marketing|hr|accounts?)@", re.I)
LEFT = re.compile(r"no longer (with|at|employed|works?|working)|has left|have left|left the (company|firm|organi[sz]ation)|"
                  r"is no longer|account (is )?(no longer|not) (in service|active|monitored)|unmonitored", re.I)
HARD = re.compile(r"address not found|user unknown|no such user|does not exist|doesn't exist|recipient (address )?rejected|"
                  r"mailbox (unavailable|not found)|5\.1\.1|550[ -]|unknown recipient|invalid recipient|"
                  r"Delivery Status Notification \(Failure\)|undeliverable|could not be delivered", re.I)
SOFT = re.compile(r"mailbox (is )?full|over quota|quota exceeded|temporar|try again later|Delay\)|will retry", re.I)
POLICY = re.compile(r"blocked|not authori[sz]ed|policy|rejected by|access denied|spam", re.I)
FORWARD = re.compile(r"(?:contact|reach|email|write to|forward(?:ed)? to|new (?:e-?mail|address)(?: is)?)[:\s]+(?:me at\s+|him at\s+|her at\s+|them at\s+)?"
                     r"([A-Za-z0-9._%+'-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", re.I)

def norm(e):
    e = e.strip().strip('<>.,;:"\'').lower()
    u, _, d = e.partition('@')
    return u.split('+')[0] + '@' + d

def phone_key(p):
    d = re.sub(r'\D', '', p or '')
    return d[-10:] if len(d) >= 7 else ''

def letters(s):
    return re.sub(r'[^a-z]', '', (s or '').lower())

# ---------------------------------------------------------------- reading
class Card:
    __slots__ = ('first', 'middle', 'last', 'org', 'title', 'birthday', 'notes', 'emails', 'phones',
                 'addrs', 'sites', 'labels', 'src', 'extra')
    def __init__(self, src):
        self.first = self.middle = self.last = self.org = self.title = self.birthday = ''
        self.notes, self.emails, self.phones, self.addrs, self.sites = [], [], [], [], []
        self.labels, self.src, self.extra = [], {src}, {}
    def name(self):
        return ' '.join(x for x in (self.first, self.last) if x).strip()
    def who(self):
        return self.name() or (self.emails[0] if self.emails else (self.phones[0] if self.phones else '(no name)'))

def add_unique(lst, v):
    if v and v not in lst:
        lst.append(v)

HANDLED = {'First Name', 'Middle Name', 'Last Name', 'Organization Name', 'Organization Title', 'Birthday', 'Notes', 'Labels'}

def is_google_csv(fields):
    return fields and 'First Name' in fields and any(f.startswith('E-mail 1') for f in fields)

def read_google_csv(path, src):
    with open(path, encoding='utf-8-sig', newline='') as f:
        rd = csv.DictReader(f)
        fields = rd.fieldnames or []
        cards = []
        for r in rd:
            c = Card(src)
            g = lambda k: (r.get(k) or '').strip()
            c.first, c.middle, c.last = g('First Name'), g('Middle Name'), g('Last Name')
            c.org, c.title, c.birthday = g('Organization Name'), g('Organization Title'), g('Birthday')
            if g('Notes'):
                c.notes.append(g('Notes'))
            for k in fields:
                v = r.get(k) or ''
                if not v:
                    continue
                if k.startswith('E-mail ') and k.endswith('Value'):
                    for e in EMAIL.findall(v):
                        add_unique(c.emails, e.lower())
                elif k.startswith('Phone ') and k.endswith('Value'):
                    for p in v.split(':::'):
                        if p.strip() and '@' not in p:
                            add_unique(c.phones, p.strip())
                elif k.startswith('Address ') and k.endswith('Formatted'):
                    lab = (r.get(k.replace('Formatted', 'Label')) or '').strip()
                    add_unique(c.addrs, (lab, v.strip()))
                elif k.startswith('Website ') and k.endswith('Value') and 'google.com/profiles' not in v:
                    add_unique(c.sites, v.strip())
            for l in (r.get('Labels') or '').split(':::'):
                add_unique(c.labels, l.strip())
            for k in fields:   # anything we don't model (nickname, custom fields, …) passes through untouched
                if k not in HANDLED and not re.match(r'(E-mail|Phone|Address|Website) \d', k) and (r.get(k) or '').strip():
                    c.extra[k] = r[k].strip()
            cards.append(c)
        return fields, cards

def read_vcf(path, src):
    cards, cur = [], None
    raw = open(path, encoding='utf-8', errors='ignore').read().replace('\r\n ', '').replace('\n ', '')
    for line in raw.splitlines():
        key, _, val = line.partition(':')
        k = key.split(';')[0].upper()
        if k == 'BEGIN':
            cur = Card(src)
        elif k == 'END' and cur is not None:
            cards.append(cur); cur = None
        elif cur is None:
            continue
        elif k == 'N':
            parts = val.split(';') + ['', '']
            cur.last, cur.first = parts[0].strip(), parts[1].strip()
        elif k == 'FN' and not (cur.first or cur.last) and '@' not in val:
            bits = val.split(); cur.first = bits[0] if bits else ''; cur.last = ' '.join(bits[1:])
        elif k == 'EMAIL':
            for e in EMAIL.findall(val):
                add_unique(cur.emails, e.lower())
        elif k == 'TEL':
            add_unique(cur.phones, val.strip())
        elif k == 'ORG':
            cur.org = val.split(';')[0].strip()
        elif k == 'TITLE':
            cur.title = val.strip()
        elif k == 'BDAY':
            cur.birthday = val.strip()
        elif k == 'NOTE':
            add_unique(cur.notes, val.replace('\\n', '\n').strip())
        elif k == 'ADR':
            add_unique(cur.addrs, ('', ', '.join(x for x in val.split(';') if x.strip())))
        elif k == 'CATEGORIES':
            for l in val.split(','):
                add_unique(cur.labels, l.strip())
    return cards

# ---------------------------------------------------------------- bounces
def read_bounces(paths):
    """Return (dead: {email: reason}, soft: set, forwards: {old: new})."""
    dead, soft, forwards = {}, set(), {}
    for p in paths:
        text = open(p, encoding='utf-8', errors='ignore').read()
        for line in text.splitlines():
            es = [norm(e) for e in EMAIL.findall(line)]
            if not es:
                continue
            subject = es[0]
            fw = FORWARD.search(line)
            if LEFT.search(line):
                dead.setdefault(subject, 'left the organisation (auto-reply)')
                if fw and norm(fw.group(1)) != subject:
                    forwards[subject] = norm(fw.group(1))
            elif SOFT.search(line):
                soft.add(subject)
            elif HARD.search(line):
                dead.setdefault(subject, 'hard bounce')
            elif POLICY.search(line):
                dead.setdefault(subject, 'blocked by the receiving organisation')
    for e in list(soft):
        if e in dead:
            soft.discard(e)
    return dead, soft, forwards

# ---------------------------------------------------------------- merging
def same_person(a, b):
    """A shared email or phone only means one person if the names agree too:
    switchboards, assistants and team inboxes are shared by many people."""
    la, lb, fa, fb = letters(a.last), letters(b.last), letters(a.first), letters(b.first)
    if not (la or fa) or not (lb or fb):
        return True
    if la and lb:
        if la == lb or (len(la) == 1 and lb.startswith(la)) or (len(lb) == 1 and la.startswith(lb)):
            return not (fa and fb) or fa[:1] == fb[:1]
        return False
    return fa == fb

def keys_of(c):
    return [('e', norm(e)) for e in c.emails] + [('p', phone_key(p)) for p in c.phones if phone_key(p)]

def fold(cards):
    parent = list(range(len(cards)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    named = lambda c: bool(letters(c.first) or letters(c.last))
    owners = collections.defaultdict(list)
    for i, c in enumerate(cards):          # pass 1: named cards whose names agree
        if not named(c):
            continue
        for k in keys_of(c):
            for j in owners[k]:
                if same_person(c, cards[j]):
                    parent[find(i)] = find(j)
            owners[k].append(i)
    for i, c in enumerate(cards):          # pass 2: a nameless card joins one person only
        if named(c):
            continue
        hits = {find(j) for k in keys_of(c) for j in owners[k]}
        if len(hits) == 1:
            parent[find(i)] = hits.pop()
        for k in keys_of(c):
            owners[k].append(i)
    groups = collections.defaultdict(list)
    for i in range(len(cards)):
        groups[find(i)].append(cards[i])
    return list(groups.values())

def combine(cs):
    m = Card('merged'); m.src = set().union(*(c.src for c in cs))
    best = max(cs, key=lambda c: (bool(c.first and c.last), len(c.first + c.last)))
    m.first, m.middle, m.last = best.first, best.middle, best.last
    for c in cs:
        m.org = m.org or c.org; m.title = m.title or c.title; m.birthday = m.birthday or c.birthday
        for e in c.emails: add_unique(m.emails, e)
        for p in c.phones:
            if phone_key(p) not in {phone_key(x) for x in m.phones} or not phone_key(p):
                add_unique(m.phones, p)
        for a in c.addrs: add_unique(m.addrs, a)
        for s in c.sites: add_unique(m.sites, s)
        for n in c.notes: add_unique(m.notes, n)
        for l in c.labels: add_unique(m.labels, l)
        for k, v in c.extra.items(): m.extra.setdefault(k, v)
    return m

# ---------------------------------------------------------------- writing
def google_header(base, n_email, n_phone, n_addr):
    """Google's own export header, with the numbered blocks sized to fit. A shortened
    header makes Google's importer put every field into Notes."""
    out, seen = [], set()
    for c in base:
        if c.startswith('E-mail ') or c.startswith('Phone ') or re.match(r'Address \d', c):
            continue
        out.append(c)
        if c == 'Labels':
            out += [f'E-mail {i} - {x}' for i in range(1, n_email + 1) for x in ('Label', 'Value')]
            out += [f'Phone {i} - {x}' for i in range(1, n_phone + 1) for x in ('Label', 'Value')]
            addr_parts = [x.split(' - ', 1)[1] for x in base if x.startswith('Address 1 - ')] or ['Label', 'Formatted']
            out += [f'Address {i} - {x}' for i in range(1, n_addr + 1) for x in addr_parts]
    return out

DEFAULT_BASE = ['First Name', 'Middle Name', 'Last Name', 'Phonetic First Name', 'Phonetic Middle Name',
    'Phonetic Last Name', 'Name Prefix', 'Name Suffix', 'Nickname', 'File As', 'Organization Name',
    'Organization Title', 'Organization Department', 'Birthday', 'Notes', 'Photo', 'Labels',
    'E-mail 1 - Label', 'E-mail 1 - Value', 'Phone 1 - Label', 'Phone 1 - Value', 'Address 1 - Label',
    'Address 1 - Formatted', 'Address 1 - Street', 'Address 1 - City', 'Address 1 - PO Box', 'Address 1 - Region',
    'Address 1 - Postal Code', 'Address 1 - Country', 'Address 1 - Extended Address', 'Website 1 - Label',
    'Website 1 - Value']

def to_row(m, hdr):
    r = {k: '' for k in hdr}
    r.update({k: v for k, v in m.extra.items() if k in r})
    r.update({'First Name': m.first, 'Middle Name': m.middle, 'Last Name': m.last, 'Organization Name': m.org,
              'Organization Title': m.title, 'Birthday': m.birthday, 'Notes': '\n\n'.join(m.notes),
              'Labels': ' ::: '.join(m.labels)})
    for i, e in enumerate(m.emails, 1):
        r[f'E-mail {i} - Label'] = '* Other' if i > 1 else '* '
        r[f'E-mail {i} - Value'] = e
    for i, p in enumerate(m.phones, 1):
        r[f'Phone {i} - Label'] = 'Mobile' if i == 1 else 'Other'
        r[f'Phone {i} - Value'] = p
    for i, (lab, a) in enumerate(m.addrs, 1):
        if f'Address {i} - Formatted' in r:
            r[f'Address {i} - Label'] = lab; r[f'Address {i} - Formatted'] = a
    if m.sites and 'Website 1 - Value' in r:
        r['Website 1 - Value'] = m.sites[0]
        if len(m.sites) > 1:
            r['Notes'] = '\n\n'.join(filter(None, [r['Notes'], 'Other websites: ' + ', '.join(m.sites[1:])]))
    return r

def write_csv(path, hdr, rows):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=hdr, extrasaction='ignore')
        w.writeheader(); w.writerows(rows)

# ---------------------------------------------------------------- build
def build(a):
    today = datetime.date.today().isoformat()
    os.makedirs(a.out, exist_ok=True)
    files = []
    for p in a.inputs:
        if os.path.isdir(p):
            files += [os.path.join(p, f) for f in sorted(os.listdir(p)) if f.lower().endswith(('.csv', '.vcf'))]
        else:
            files.append(p)
    backup = os.path.join(a.out, f'originals-{today}')
    os.makedirs(backup, exist_ok=True)
    for p in files + list(a.bounces or []):
        dst = os.path.join(backup, os.path.basename(p))
        if not os.path.exists(dst):
            shutil.copy2(p, dst)

    base_header, cards, seen = None, [], {}
    for p in files:
        src = os.path.basename(p)
        if p.lower().endswith('.vcf'):
            cs = read_vcf(p, src)
        else:
            with open(p, encoding='utf-8-sig', newline='') as f:
                fields = next(csv.reader(f), [])
            if not is_google_csv(fields):
                print(f'skipped {src}: not a Google Contacts CSV (export with "Google CSV")', file=sys.stderr)
                continue
            fields, cs = read_google_csv(p, src)
            base_header = base_header or []
            for k in fields:            # union of every export's columns, in Google's order
                if k not in base_header: base_header.append(k)
        for c in cs:                      # identical cards across accounts (a copied address book)
            sig = (c.first, c.last, tuple(sorted(norm(e) for e in c.emails)), tuple(sorted(phone_key(x) for x in c.phones)), c.org)
            if sig in seen:               # same card copied into another account: keep one, lose nothing
                k = seen[sig]
                for key, v in c.extra.items(): k.extra.setdefault(key, v)
                for l in c.labels: add_unique(k.labels, l)
                for n in c.notes: add_unique(k.notes, n)
                for a_ in c.addrs: add_unique(k.addrs, a_)
                for s_ in c.sites: add_unique(k.sites, s_)
                k.birthday = k.birthday or c.birthday; k.title = k.title or c.title
                continue
            seen[sig] = c; cards.append(c)
    base_header = base_header or DEFAULT_BASE

    me = {norm(e) for e in (a.me or [])}
    dead, soft, forwards = read_bounces(a.bounces or [])
    dead_domains = {d.lower().lstrip('@') for d in (a.dead_domain or [])}
    rel = {}
    if a.relationships:
        for r in csv.DictReader(open(a.relationships, encoding='utf-8-sig')):
            rel[norm(r['email'])] = r
    dec = json.load(open(a.decisions)) if a.decisions else {}
    dec_remove = {norm(e) for e in dec.get('remove_addresses', [])}
    dec_letgo = {norm(e) for e in dec.get('let_go', [])}
    dec_keep_label = {norm(k): v for k, v in dec.get('labels', {}).items()}
    dec_add = {norm(k): [norm(x) for x in v] for k, v in dec.get('add_addresses', {}).items()}
    dec_untouched = {norm(e) for e in dec.get('leave_untouched', [])}
    dec_different = [{norm(e) for e in grp} for grp in dec.get('different_people', [])]
    dec_same = [{norm(e) for e in grp} for grp in dec.get('same_person', [])]

    log = []   # (person, action, detail, reason)
    def L(who, action, detail, reason): log.append((who, action, detail, reason))

    # 1. fold cards into people
    people = []
    for grp in fold(cards):
        m = combine(grp) if len(grp) > 1 else grp[0]
        if len(grp) > 1:
            names = sorted({c.name() for c in grp if c.name()})
            L(m.who(), 'merged', f'{len(grp)} cards', 'shared email or phone, and the names agree'
              + (f' ({" / ".join(names)})' if len(names) > 1 else ''))
        people.append(m)

    # 2. the person's own "same person" answers
    for grp in dec_same:
        hit = [p for p in people if {norm(e) for e in p.emails} & grp]
        if len(hit) > 1:
            keep = combine(hit)
            for p in hit: people.remove(p)
            people.append(keep); L(keep.who(), 'merged', f'{len(hit)} cards', 'your call: same person')

    # 3. same full name, no shared key
    questions = {'same_name': [], 'no_current_address': [], 'stale_details': [], 'sensitive': []}
    by_name = collections.defaultdict(list)
    for p in people:
        if letters(p.first) and letters(p.last):
            by_name[(letters(p.first), letters(p.last))].append(p)
    for key, grp in by_name.items():
        if len(grp) < 2:
            continue
        ids = [{norm(e) for e in p.emails} for p in grp]
        if any(all(i & d for i in ids if i) for d in dec_different):
            continue
        thin = [p for p in grp if len(p.emails) == 1 and not p.phones and not p.org and not p.addrs]
        rest = [p for p in grp if p not in thin]
        if len(rest) == 1 and thin:
            for t in thin:
                add_unique(rest[0].emails, t.emails[0]); people.remove(t)
                for l in t.labels: add_unique(rest[0].labels, l)
                L(rest[0].who(), 'merged', f'added {t.emails[0]}', 'same full name; that card was only a newer address')
        else:
            questions['same_name'].append([(p.who(), p.org, '; '.join(p.emails) or '; '.join(p.phones)) for p in grp])

    # 4. addresses: dead, automated, forwarded, the person's removals
    out, letgo, nothing_left = [], [], []
    for p in people:
        pe = {norm(e) for e in p.emails}
        if pe & dec_untouched:
            out.append(p); continue
        if pe & dec_letgo:
            letgo.append(p); L(p.who(), 'let go', '; '.join(p.emails), 'your call'); continue
        keep, left_company, auto = [], False, []
        for e in p.emails:
            n = norm(e); dom = n.split('@')[1]
            if n in me:
                continue
            reason = None
            if n in dec_remove: reason = 'your call: out of date'
            elif n in dead: reason = dead[n]
            elif dom in dead_domains or any(dom.endswith('.' + d) for d in dead_domains): reason = 'company domain is gone'
            if reason:
                L(p.who(), 'removed address', e, reason)
                if 'left' in reason or 'domain' in reason: left_company = True
                new = forwards.get(n)
                if new and new not in [norm(x) for x in keep] and new not in [norm(x) for x in p.emails]:
                    keep.append(new); L(p.who(), 'added address', new, f'given in the auto-reply from {e}')
                continue
            if AUTOMATED.search(n):
                auto.append(e); continue
            keep.append(e)
        for n, adds in dec_add.items():
            if n in pe:
                for x in adds:
                    if x not in keep: keep.append(x); L(p.who(), 'added address', x, 'your call')
        p.emails = keep
        if not (p.first or p.last) and p.emails and all(AUTOMATED.search(norm(e)) or ROLE.match(e) for e in p.emails) and not p.phones:
            L(p.who(), 'removed card', '; '.join(p.emails), 'not a person (role or automated address)'); continue
        if not (p.first or p.last or p.emails or p.phones or p.addrs):
            if pe:
                L('(no name)', 'removed card', '; '.join(sorted(pe)), 'not a person (automated sender)')
            continue
        for e in auto:
            L(p.who(), 'removed address', e, 'automated sender')
        if not p.emails and pe:
            questions['no_current_address'].append((p.who(), p.org, '; '.join(sorted(pe))))
            add_unique(p.notes, 'Quaiint: no current email; every address on file bounced or was retired.')
        if left_company and (p.org or p.phones):
            add_unique(p.notes, 'Quaiint: has left the company on file; employer and office phone are probably out of date.')
            questions['stale_details'].append((p.who(), p.org))
        if not (p.emails or p.phones or p.addrs):
            nothing_left.append(p)
        out.append(p)

    # 5. labels
    dropped = 0
    for p in out:
        before = len(p.labels)
        p.labels = [l for l in p.labels if l and not l.startswith('Imported')]
        dropped += before - len(p.labels)
        if '* myContacts' not in p.labels: p.labels.insert(0, '* myContacts')
        st = None
        for e in p.emails:
            r = rel.get(norm(e))
            if r and r.get('status') in ('still_in_touch', 'dormant'):
                st = 'Still in touch' if r['status'] == 'still_in_touch' else (st or 'Dormant')
        if st: add_unique(p.labels, st)
        for e in p.emails:
            for l in dec_keep_label.get(norm(e), []): add_unique(p.labels, l)
    if dropped:
        L('(all)', 'dropped labels', f'{dropped} "Imported on …" labels', 'import noise')
    labeled = sum(1 for p in out if 'Still in touch' in p.labels or 'Dormant' in p.labels)
    # people in the email history whose address isn't on any card, but whose name is: ask, never assume
    on_cards = {norm(e) for p in out for e in p.emails}
    by_full = collections.defaultdict(list)
    for p in out:
        if letters(p.first) and letters(p.last):
            by_full[letters(p.first) + ' ' + letters(p.last)].append(p)
    questions['history_match'] = []
    for e, r in rel.items():
        if r.get('status') not in ('still_in_touch', 'dormant') or e in on_cards:
            continue
        others = [norm(x) for x in (r.get('other_emails') or '').split(';') if x.strip()]
        if any(o in on_cards for o in others):
            continue
        t = (r.get('name') or '').lower().split()
        key = (letters(t[0]) + ' ' + letters(t[-1])) if len(t) >= 2 else ''
        for p in by_full.get(key, []):
            questions['history_match'].append((p.who(), p.org, '; '.join(p.emails) or '; '.join(p.phones),
                                               '; '.join([e] + others), r['status'].replace('_', ' '), r.get('last_contact', '')))

    # 6. write
    n_e = max([len(p.emails) for p in out] + [1]); n_p = max([len(p.phones) for p in out] + [1])
    n_a = max([len(p.addrs) for p in out] + [1])
    hdr = google_header(base_header, n_e, n_p, min(n_a, 3))
    out.sort(key=lambda p: (letters(p.last) or letters(p.first) or (p.emails or [''])[0]))
    rows = [to_row(p, hdr) for p in out]
    for old in [f for f in os.listdir(a.out) if f.startswith('master-contacts-google-part')]:
        os.remove(os.path.join(a.out, old))
    for i in range(0, len(rows), a.part_size):
        write_csv(os.path.join(a.out, f'master-contacts-google-part{i // a.part_size + 1}.csv'), hdr, rows[i:i + a.part_size])
    test = [r for r in rows if r.get('E-mail 1 - Value') and r.get('Phone 1 - Value')][:5] or rows[:5]
    write_csv(os.path.join(a.out, 'master-contacts-google-TEST-5.csv'), hdr, test)
    with open(os.path.join(a.out, 'change-log.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['person', 'action', 'detail', 'reason']); w.writerows(log)
    if letgo:
        with open(os.path.join(a.out, 'let-go.csv'), 'w', newline='') as f:
            w = csv.writer(f); w.writerow(['person', 'emails'])
            for p in letgo: w.writerow([p.who(), '; '.join(p.emails)])

    with open(os.path.join(a.out, 'questions.md'), 'w') as f:
        f.write('# Questions only you can answer\n\nAnswer in any words. Nothing below has been changed yet.\n\n')
        if questions['same_name']:
            f.write('## Same name, no shared email or phone. One person or different people?\n\n')
            for grp in questions['same_name']:
                f.write('- ' + '  vs.  '.join(f'**{w}**' + (f' ({o})' if o else '') + f': {d}' for w, o, d in grp) + '\n')
            f.write('\n')
        if questions['no_current_address']:
            f.write('## No current email left. Know a new one, or let them go?\n\n')
            for w, o, d in questions['no_current_address']:
                f.write(f'- **{w}**' + (f' ({o})' if o else '') + f'. Old: {d}\n')
            f.write('\n')
        if questions.get('history_match'):
            f.write('## Same name in your email and your contacts, different addresses. Same person?\n\n')
            f.write('If yes, the email address gets added to the card and the relationship label applied.\n\n')
            for w, o, d, he, st, lc in questions['history_match']:
                f.write(f'- **{w}**' + (f' ({o})' if o else '') + f': {d}  vs.  email history: {he} ({st}, last {lc})\n')
            f.write('\n')
        if questions['stale_details']:
            f.write('## Moved on. Keep the old employer and office phone, or clear them?\n\n')
            for w, o in questions['stale_details']:
                f.write(f'- **{w}**' + (f' (was {o})' if o else '') + '\n')
            f.write('\n')
        f.write('## Anyone sensitive?\n\nFamily, someone who has died, someone who asked to be left alone. '
                'Name them and say what you want: leave untouched, label Do not contact, or remove.\n')

    soft_hit = sorted({norm(e) for p in out for e in p.emails} & soft)
    summary = {
        'date': today, 'files': [os.path.basename(x) for x in files], 'cards_in': len(cards),
        'people_out': len(out), 'merges': sum(1 for x in log if x[1] == 'merged'),
        'dead_addresses_removed': sum(1 for x in log if x[1] == 'removed address' and x[3] != 'automated sender'),
        'automated_removed': sum(1 for x in log if x[3] == 'automated sender' or x[1] == 'removed card'),
        'new_addresses_found': sum(1 for x in log if x[1] == 'added address'),
        'let_go': len(letgo), 'no_current_email': len(questions['no_current_address']),
        'questions': {k: len(v) for k, v in questions.items() if k not in ('sensitive', 'history_match')},
        'soft_bounces_kept': soft_hit, 'labels': dict(collections.Counter(l for p in out for l in p.labels)),
        'import_parts': (len(rows) + a.part_size - 1) // a.part_size,
        'relationship_file_used': bool(rel),
        'relationship_labels_applied': labeled,
        'history_name_matches_to_confirm': len(questions.get('history_match', [])),
    }
    json.dump(summary, open(os.path.join(a.out, 'summary.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k not in ('labels', 'files')}, indent=1))

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build')
    b.add_argument('--in', dest='inputs', nargs='+', required=True, help='export files or folders')
    b.add_argument('--out', required=True)
    b.add_argument('--bounces', nargs='*', help='text files with pasted bounces / auto-replies')
    b.add_argument('--relationships', help='relationships.csv from signals.py')
    b.add_argument('--decisions', help="decisions.json with the person's answers")
    b.add_argument('--me', nargs='*', help="the person's own addresses (never kept as contacts)")
    b.add_argument('--dead-domain', nargs='*', help='company domains that no longer receive mail')
    b.add_argument('--part-size', type=int, default=2500, help='Google imports at most 3,000 per file')
    h = sub.add_parser('header')
    h.add_argument('--in', dest='inputs', nargs=1, required=True)
    a = ap.parse_args()
    if a.cmd == 'header':
        with open(a.inputs[0], encoding='utf-8-sig', newline='') as f:
            print(next(csv.reader(f)))
    else:
        build(a)

if __name__ == '__main__':
    main()
