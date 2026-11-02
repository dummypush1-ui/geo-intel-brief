// Auto-refresh OFAC (SDN XML) and EU (CSV) sanctions rows in src/sanctions.ts.
// UFLPA rows (HTML page, no feed) are kept as-is and watched by monitor.mjs.
// Safety: a list is replaced only if the new row count is within +/-15% of the old one.
import fs from 'fs';
const FILE = 'src/sanctions.ts';
const dec = (s) => s.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&#(\d+);/g, (_, n) => String.fromCharCode(+n));
const tag = (x, t) => { const m = x.match(new RegExp('<' + t + '>([^<]*)</' + t + '>')); return m ? dec(m[1]).trim() : ''; };
async function get(url) {
  const r = await fetch(url, { headers: { 'User-Agent': 'hsn-finder-updater' }, signal: AbortSignal.timeout(120000) });
  if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + url);
  return r.text();
}
function parseOfac(xml) {
  const rows = [];
  for (const m of xml.matchAll(/<sdnEntry>([\s\S]*?)<\/sdnEntry>/g)) {
    const e = m[1];
    const prog = [...e.matchAll(/<program>([^<]*)<\/program>/g)].map((x) => dec(x[1])).join(';') || 'SDN';
    const nm = (b) => { const l = tag(b, 'lastName'), f = tag(b, 'firstName'); return f ? l + ', ' + f : l; };
    const main = nm(e.split('<akaList>')[0]);
    if (main) rows.push([main, 'OFAC', prog]);
    for (const a of e.matchAll(/<aka>([\s\S]*?)<\/aka>/g)) { const n = nm(a[1]); if (n) rows.push([n, 'OFAC', prog]); }
  }
  return rows;
}
function parseCsv(text, delim) {
  const out = []; let row = [], f = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += c; }
    else if (c === '"') q = true;
    else if (c === delim) { row.push(f); f = ''; }
    else if (c === '\n') { row.push(f.replace(/\r$/, '')); out.push(row); row = []; f = ''; }
    else f += c;
  }
  if (f || row.length) { row.push(f); out.push(row); }
  return out;
}
function parseEu(csv) {
  const t = parseCsv(csv.replace(/^\uFEFF/, ''), ';'), h = t[0];
  const iN = h.indexOf('NameAlias_WholeName'), iP = h.indexOf('Entity_Regulation_Programme');
  if (iN < 0) throw new Error('EU CSV format changed (no NameAlias_WholeName column)');
  const seen = new Set(), rows = [];
  for (const r of t.slice(1)) {
    const n = (r[iN] || '').trim(); if (!n) continue;
    const p = (iP >= 0 && r[iP] || '').trim() || 'EU';
    const k = n + '|' + p; if (seen.has(k)) continue; seen.add(k); rows.push([n, 'EU', p]);
  }
  return rows;
}
export async function refreshSanctions() {
  const t = fs.readFileSync(FILE, 'utf8');
  const meta = JSON.parse(t.match(/SANCTIONS_META = (\{.*\});/)[1]);
  const old = JSON.parse(t.slice(t.indexOf('= [[') + 2, t.lastIndexOf(']') + 1));
  const by = (l) => old.filter((r) => r[1] === l);
  const res = {}; let rows = []; const today = new Date().toISOString().slice(0, 10);
  for (const [list, parse] of [['OFAC', parseOfac], ['EU', parseEu]]) {
    const prev = by(list);
    try {
      const nu = parse(await get(meta.sources[list]));
      if (nu.length < prev.length * 0.85 || nu.length > prev.length * 1.15) throw new Error('row count ' + nu.length + ' vs ' + prev.length + ' outside +/-15% - kept old list');
      rows.push(...nu); res[list] = 'updated ' + nu.length; meta[list.toLowerCase()] = list + ' auto-refreshed ' + today;
    } catch (e) { rows.push(...prev); res[list] = 'kept old: ' + e.message; }
  }
  rows.push(...by('UFLPA'));
  rows.sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
  meta.checked = today;
  const out = t.split('\n')[0] + '\nexport const SANCTIONS_META = ' + JSON.stringify(meta) + ';\nexport const SANCTIONS: [string, string, string][] = ' + JSON.stringify(rows) + ';\n';
  if (Object.values(res).some((v) => v.startsWith('updated'))) fs.writeFileSync(FILE, out);
  return res;
}
