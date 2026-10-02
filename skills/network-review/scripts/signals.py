#!/usr/bin/env python3
"""Quaiint signals: who you're still in touch with, from email headers only.

Reads message headers (never bodies) from a mailbox export (.mbox, e.g. Google Takeout)
and/or a JSONL file of headers your assistant pulled through an email connector, and
writes:

  relationships.csv          one row per person: counts, dates, status
  reconnect-candidates.csv   people you were close to and haven't written to in a while,
                             strongest first, for the review (the person decides)

    python3 signals.py --mbox Sent.mbox Inbox.mbox --me you@x.com --out OUT
    python3 signals.py --headers headers.jsonl --me you@x.com --out OUT [--subjects]

headers.jsonl: one JSON object per message: {"date": "...", "from": "...", "to": "...",
"cc": "...", "subject": "..."} (to/cc may be strings or lists). Standard library only.
Only messages with 6 or fewer recipients count: group blasts don't make relationships.
"""
import argparse, collections, csv, datetime, email.utils, json, math, os, re, sys
from email.parser import BytesHeaderParser

AUTOMATED = re.compile(
    r"(^|[._-])(no-?reply|do-?not-?reply|donotreply|notifications?|notify|mailer-daemon|postmaster|bounces?|"
    r"billing|invoices?|receipts?|alerts?|automated|calendar-notification|updates?|news(letter)?|marketing|hello|info|support|team)([._-]|@)"
    r"|@(reply|bounce|em|email|mail|e|news|info|mg|mailer|sendgrid|mailchimp)\d*\.|@docs\.google\.|@facebookmail\.|"
    r"@linkedin\.com$|@.*(substack|medium|calendly|zoom|slack|notion|github|atlassian|hubspot|salesforce)\.com$", re.I)

def norm(e):
    e = (e or '').strip().strip('<>.,;:"\'').lower()
    u, _, d = e.partition('@')
    return (u.split('+')[0] + '@' + d) if d else ''

def addrs(v):
    if isinstance(v, list):
        v = ', '.join(v)
    return [(n.strip().strip('"'), norm(a)) for n, a in email.utils.getaddresses([v or '']) if '@' in (a or '')]

def when(v):
    if not v:
        return None
    try:
        d = email.utils.parsedate_to_datetime(v)
    except Exception:
        try:
            d = datetime.datetime.fromisoformat(str(v).replace('Z', '+00:00'))
        except Exception:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=datetime.timezone.utc)
    return d

def mbox_headers(path):
    """Stream an mbox and yield header dicts without reading bodies into memory."""
    hp = BytesHeaderParser()
    with open(path, 'rb') as f:
        buf, in_head, prev_blank = [], False, True
        for line in f:
            if line.startswith(b'From ') and prev_blank:
                buf, in_head = [], True
                prev_blank = False
                continue
            if in_head:
                if line in (b'\n', b'\r\n'):
                    in_head = False
                    h = hp.parsebytes(b''.join(buf))
                    yield {'date': h.get('Date'), 'from': h.get('From'), 'to': h.get('To'),
                           'cc': h.get('Cc'), 'subject': h.get('Subject')}
                else:
                    buf.append(line)
            prev_blank = line in (b'\n', b'\r\n')

def jsonl_headers(path):
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if line:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--mbox', nargs='*', default=[])
    ap.add_argument('--headers', nargs='*', default=[])
    ap.add_argument('--me', nargs='*', default=[], help="your own addresses (inferred if omitted)")
    ap.add_argument('--out', required=True)
    ap.add_argument('--as-of', help='date to measure "how long ago" from (default: latest message)')
    ap.add_argument('--dormant-months', type=int, default=24)
    ap.add_argument('--max-recipients', type=int, default=6)
    ap.add_argument('--subjects', action='store_true', help='keep up to 3 recent subjects per candidate (helps tell friends from deals)')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    msgs = []
    for p in a.mbox:
        msgs += list(mbox_headers(p))
    for p in a.headers:
        msgs += list(jsonl_headers(p))
    if not msgs:
        sys.exit('no messages found')

    me = {norm(x) for x in a.me}
    if not me:
        c = collections.Counter(addr for m in msgs for _, addr in addrs(m.get('from'))[:1])
        me = {c.most_common(1)[0][0]}
        print(f'assuming your address is {next(iter(me))} (pass --me to set it)', file=sys.stderr)

    P = collections.defaultdict(lambda: {'name': '', 'sent': 0, 'recv': 0, 'first': None, 'last_sent': None,
                                         'last_recv': None, 'subjects': []})
    latest, skipped_big = None, 0
    for m in msgs:
        d = when(m.get('date'))
        if not d:
            continue
        frm = addrs(m.get('from'))
        rcpt = addrs(m.get('to')) + addrs(m.get('cc'))
        if len(rcpt) > a.max_recipients:
            skipped_big += 1
            continue
        latest = d if latest is None or d > latest else latest
        sender = frm[0][1] if frm else ''
        if sender in me:
            for n, e in rcpt:
                if e in me or AUTOMATED.search(e):
                    continue
                r = P[e]; r['sent'] += 1; r['name'] = r['name'] or n
                r['last_sent'] = max(filter(None, [r['last_sent'], d]))
                r['first'] = min(filter(None, [r['first'], d]))
                if a.subjects and m.get('subject'): r['subjects'].append((d, str(m['subject'])[:90]))
        elif any(e in me for _, e in rcpt) and sender and not AUTOMATED.search(sender):
            r = P[sender]; r['recv'] += 1; r['name'] = r['name'] or (frm[0][0] if frm else '')
            r['last_recv'] = max(filter(None, [r['last_recv'], d]))
            r['first'] = min(filter(None, [r['first'], d]))
            if a.subjects and m.get('subject'): r['subjects'].append((d, str(m['subject'])[:90]))

    as_of = when(a.as_of) if a.as_of else latest
    cutoff = as_of - datetime.timedelta(days=round(a.dormant_months * 30.44))

    # one person, several addresses: group by full name when there is one
    def name_key(n, e):
        t = re.sub(r'[^a-z ]', '', (n or '').lower()).split()
        return ' '.join([t[0], t[-1]]) if len(t) >= 2 else 'email:' + e
    G = collections.defaultdict(list)
    for e, r in P.items():
        G[name_key(r['name'], e)].append((e, r))
    rows = []
    for key, items in G.items():
        sent = sum(r['sent'] for _, r in items); recv = sum(r['recv'] for _, r in items)
        firsts = [r['first'] for _, r in items if r['first']]
        lasts = [x for _, r in items for x in (r['last_sent'], r['last_recv']) if x]
        if not lasts:
            continue
        first, last = min(firsts), max(lasts)
        name = max((r['name'] for _, r in items), key=len)
        emails = [e for e, r in sorted(items, key=lambda x: -(x[1]['sent'] + x[1]['recv']))]
        two_way = sent > 0 and recv > 0
        if two_way and last >= cutoff:
            status = 'still_in_touch'
        elif two_way and min(sent, recv) >= 2 and last < cutoff:
            status = 'dormant'
        elif sent and not recv:
            status = 'you_wrote_only'
        elif recv and not sent:
            status = 'they_wrote_only'
        else:
            status = 'light'
        span = (last - first).days / 365.25
        # log scale: a colleague with 4,000 work emails should not drown out a friend you wrote 40 times
        score = 2 * math.log2(1 + min(sent, recv)) + math.log2(1 + sent + recv) / 2 + min(span, 10) / 2
        subj = sorted((x for _, r in items for x in r['subjects']), reverse=True)[:3]
        rows.append({'email': emails[0], 'other_emails': '; '.join(emails[1:]), 'name': name, 'status': status,
                     'sent': sent, 'received': recv, 'first': first.date().isoformat(), 'last_contact': last.date().isoformat(),
                     'years_quiet': round((as_of - last).days / 365.25, 1), 'strength': round(score, 2),
                     'recent_subjects': ' | '.join(sj for _, sj in subj) if a.subjects else ''})
    rows.sort(key=lambda x: (-x['strength'], x['email']))
    fields = ['email', 'other_emails', 'name', 'status', 'sent', 'received', 'first', 'last_contact', 'years_quiet', 'strength'] + (['recent_subjects'] if a.subjects else [])
    with open(os.path.join(a.out, 'relationships.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    cand = [r for r in rows if r['status'] == 'dormant'][:50]
    with open(os.path.join(a.out, 'reconnect-candidates.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore'); w.writeheader(); w.writerows(cand)
    counts = collections.Counter(r['status'] for r in rows)
    print(json.dumps({'messages_read': len(msgs), 'group_messages_skipped': skipped_big, 'as_of': as_of.date().isoformat(),
                      'people': len(rows), 'by_status': dict(counts), 'reconnect_candidates': len(cand)}, indent=1))

if __name__ == '__main__':
    main()
