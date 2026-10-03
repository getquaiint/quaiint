// POST /api/request — a "run it with us" request becomes an issue in a PRIVATE GitHub repo,
// so every lead lands in Dave's inbox and stays on the record. No database, no third party.
// Env (Vercel project settings): GITHUB_TOKEN (fine-grained, Issues: read/write on LEADS_REPO only),
//                                LEADS_REPO (e.g. "getgetquaiint/leads").
const SITUATIONS = { leaving: 'Leaving or left a company', account: 'An old account is shutting down',
                     sold: 'Sold or wound down a company', overdue: 'About to email my network' };
const EMAIL = /^[^\s@]{1,64}@[^\s@]{1,255}\.[^\s@]{2,}$/;

module.exports = async (req, res) => {
  if (req.method !== 'POST') { res.setHeader('Allow', 'POST'); return res.status(405).json({ error: 'POST only' }); }
  let b = req.body;
  if (typeof b === 'string') { try { b = JSON.parse(b); } catch { b = {}; } }
  b = b || {};
  if (b.company) return res.status(200).json({ ok: true });            // honeypot: bots fill hidden fields
  const email = String(b.email || '').trim().slice(0, 254);
  if (!EMAIL.test(email)) return res.status(400).json({ error: 'Enter a valid email address.' });
  const situation = SITUATIONS[b.situation] || 'Not given';
  const note = String(b.note || '').trim().slice(0, 600);
  const source = String(b.source || 'direct').replace(/[^\w.\-]/g, '').slice(0, 60);
  const GITHUB_TOKEN = (process.env.GITHUB_TOKEN || '').trim().replace(/^["']|["']$/g, '');
  const LEADS_REPO = (process.env.LEADS_REPO || '').trim();
  if (!GITHUB_TOKEN || !LEADS_REPO) return res.status(503).json({ error: 'Requests are not set up yet.' });
  const body = [`**Email:** ${email}`, `**What's changing:** ${situation}`, `**Came from:** ${source}`,
                note ? `\n**Note:**\n> ${note.replace(/\n/g, '\n> ')}` : ''].join('\n');
  const r = await fetch(`https://api.github.com/repos/${LEADS_REPO}/issues`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${GITHUB_TOKEN}`, Accept: 'application/vnd.github+json', 'User-Agent': 'quaiint-site',
               'X-GitHub-Api-Version': '2022-11-28' },
    body: JSON.stringify({ title: `Review request: ${situation}`, body, labels: ['request', source] }),
  });
  if (!r.ok) {
    const detail = await r.text().catch(() => '');
    console.error('github', r.status, detail.slice(0, 300));          // visible in Vercel logs, never to the visitor
    return res.status(502).json({ error: 'Could not save the request.', code: r.status });
  }
  return res.status(200).json({ ok: true });
};
