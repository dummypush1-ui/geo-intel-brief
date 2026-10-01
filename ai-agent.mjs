// AI jobs. Rule: AI proposes, code verifies. Nothing unverified is ever written.
import fs from 'fs';
import zlib from 'zlib';
import { execSync } from 'child_process';
import { geminiPost } from './gemini.mjs';
const KEY = process.env.GEMINI_API_KEY || '';
const IN_URL = 'https://cbic-gst.gov.in/gst-goods-services-rates.html';
export const ask = async (prompt) => {
  const { data } = await geminiPost(KEY, { contents: [{ parts: [{ text: prompt }] }], generationConfig: { temperature: 0, responseMimeType: 'application/json' } });
  const t = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
  return JSON.parse(t.replace(/^```[a-z]*\n?/i, '').replace(/```\s*$/, '').trim());
};
function descriptions() {
  let b = ''; for (let n = 0; fs.existsSync(`src/datachunk${n}.ts`); n++) b += fs.readFileSync(`src/datachunk${n}.ts`, 'utf8').match(/"([A-Za-z0-9+/=]+)"/)[1];
  return JSON.parse(zlib.gunzipSync(Buffer.from(b, 'base64')).toString()).map((r) => String(r[2] || '').toLowerCase());
}

// JOB 1 - grow the search-alias list (what traders type -> official wording).
// Verified: every word-set must match 1..3000 real tariff descriptions.
export async function expandAliases(askFn = ask, D = null) {
  if (!KEY && askFn === ask) return 'skipped: no GEMINI_API_KEY';
  const f = 'src/aliases.ts'; let t = fs.readFileSync(f, 'utf8');
  const have = new Set([...t.matchAll(/^\s*'([^']+)':/gm)].map((m) => m[1]));
  const arr = await askFn('You help traders find customs tariff codes. Suggest 40 common product terms (English and Indian trade usage, Hinglish spellings welcome) NOT already in this list: ' + [...have].slice(0, 400).join(', ') +
    '. For each, give word-sets: arrays of 1-3 lowercase words that appear together in OFFICIAL tariff descriptions (example: "mobile phone" -> [["smartphones"],["cellular","telephone"]]). Return JSON: [{"term":"...","sets":[["w1","w2"]]}]');
  D = D || descriptions(); const add = [];
  for (const e of Array.isArray(arr) ? arr : []) {
    const term = String(e.term || '').toLowerCase().trim().replace(/\s+/g, ' ');
    if (!/^[a-z][a-z0-9 -]{1,38}$/.test(term) || have.has(term)) continue;
    const sets = (Array.isArray(e.sets) ? e.sets : []).filter((s) => Array.isArray(s) && s.length >= 1 && s.length <= 3 && s.every((w) => /^[a-z]{3,20}$/.test(w))).slice(0, 4);
    const good = sets.filter((s) => { const n = D.reduce((c, d) => c + (s.every((w) => d.includes(w)) ? 1 : 0), 0); return n >= 1 && n <= 3000; });
    if (!good.length || good.length < sets.length) continue;
    add.push(`  '${term}': ${JSON.stringify(good).replace(/"/g, "'")},`); have.add(term);
  }
  if (!add.length) return 'no valid aliases proposed';
  fs.writeFileSync(f, t.replace(/\n\};\s*$/, '\n' + add.join('\n') + '\n};\n'));
  return 'added ' + add.length + ' aliases';
}

// JOB 2 - GST: read NEW IGST rate notifications and PROPOSE changes (never edits gstmap.ts directly).
// Grounding: each proposed code and rate must literally appear in the notification text.
// The workflow turns state/gst-proposal.json into a Pull Request for you to approve.
export async function draftGst(askFn = ask, fetchFn = fetch) {
  if (!KEY && askFn === ask) return 'skipped: no GEMINI_API_KEY';
  const SEEN = 'state/gst-seen.json';
  const page = await (await fetchFn(IN_URL, { headers: { 'User-Agent': 'hsn-finder-updater' } })).text();
  const links = [...page.matchAll(/<a[^>]+href="([^"]+\.pdf)"[^>]*>([\s\S]*?)<\/a>/gi)]
    .map((m) => ({ url: new URL(m[1], IN_URL).href, text: m[2].replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim() }))
    .filter((l) => /integrated tax\s*\(rate\)/i.test(l.text));
  if (!fs.existsSync(SEEN)) { fs.writeFileSync(SEEN, JSON.stringify({ seen: links.map((l) => l.url) }) + '\n'); return 'baseline: ' + links.length + ' notifications marked as already known'; }
  const st = JSON.parse(fs.readFileSync(SEEN, 'utf8')), fresh = links.filter((l) => !st.seen.includes(l.url)).slice(0, 3);
  if (!fresh.length) return 'no new notifications';
  const changes = [], srcs = []; let rejected = 0;
  for (const l of fresh) {
    fs.writeFileSync('/tmp/n.pdf', Buffer.from(await (await fetchFn(l.url)).arrayBuffer()));
    const text = execSync('pdftotext -layout /tmp/n.pdf -', { maxBuffer: 5e7 }).toString(), rows = text.split('\n').map((x) => x.replace(/[\s.]/g, ''));
    const out = await askFn('From this Indian GST notification text, list every GOODS rate entry with an HS code. Only what is explicitly stated. JSON: [{"code":"digits only, 2-8 digits","rate":"like 18%","description":"short"}]\n\n' + text.slice(0, 90000));
    for (const c of Array.isArray(out) ? out : []) {
      const code = String(c.code || '').replace(/\D/g, ''), rate = String(c.rate || '').trim();
      if (!/^\d{2,8}$/.test(code) || !/^\d+(\.\d+)?%$/.test(rate)) continue;
      // grounding: the code and its rate (with a % sign) must appear on the same table row or within the next 2 lines
      const rx = new RegExp('(^|\\D)' + rate.replace('%', '').replace('.', '\\.') + '%');
      const raw = text.split('\n'), hit = rows.some((r, i) => r.includes(code) && rx.test(raw.slice(i, i + 3).join(' ').replace(/\s+%/g, '%')));
      if (!hit) { rejected++; continue; }
      changes.push({ code, rate, description: String(c.description || '').slice(0, 200), source: l.url });
    }
    srcs.push(l.url); st.seen.push(l.url);
  }
  fs.writeFileSync(SEEN, JSON.stringify(st) + '\n');
  if (changes.length) fs.writeFileSync('state/gst-proposal.json', JSON.stringify({ sources: srcs, changes }, null, 1));
  return changes.length + ' verified proposals from ' + srcs.length + ' notifications (' + rejected + ' AI items rejected as not found in the text)';
}
