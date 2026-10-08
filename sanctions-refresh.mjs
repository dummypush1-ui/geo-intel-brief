// Auto-refresh OFAC (SDN XML) and EU (CSV) sanctions rows in src/sanctions.ts.
// UFLPA rows (HTML page, no feed) are kept as-is and watched by monitor.mjs.
// Outliers and empty-base bootstrap require review of an exact candidate hash.
import fs from 'fs';
import {decodeXmlEntities} from './updater_runtime/xml-entities.mjs';
import {sanctionsDecision} from './updater_runtime/sanctions-policy.mjs';
const FILE = 'src/sanctions.ts';
const dec = decodeXmlEntities;
const tag = (x, t) => { const m = x.match(new RegExp('<' + t + '>([^<]*)</' + t + '>')); return m ? dec(m[1]).trim() : ''; };
async function get(url) {
  const r = await fetch(url, { headers: { 'User-Agent': 'hsn-finder-updater' }, signal: AbortSignal.timeout(120000) });
  if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + url);
  const chunks=[];let bytes=0;
  for await(const chunk of r.body){bytes+=chunk.byteLength;if(bytes>32*1024*1024){throw new Error('Sanctions response too large');}chunks.push(Buffer.from(chunk));}
  return Buffer.concat(chunks).toString('utf8');
}
function parseOfac(xml) {
  if(!/<(?:\w+:)?sdnList(?:\s[^>]*)?>[\s\S]*<\/(?:\w+:)?sdnList>\s*$/.test(xml)||/<!(?:DOCTYPE|ENTITY)/i.test(xml))throw new Error('Invalid OFAC envelope');
  const rows = [];
  if((xml.match(/<sdnEntry>/g)||[]).length!==(xml.match(/<\/sdnEntry>/g)||[]).length)throw new Error('Incomplete OFAC entry');
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
  if(q)throw new Error('Unclosed CSV quote');
  return out;
}
function parseEu(csv) {
  const t = parseCsv(csv.replace(/^\uFEFF/, ''), ';'), h = t[0];
  const iN = h.indexOf('NameAlias_WholeName'), iP = h.indexOf('Entity_Regulation_Programme');
  if (iN < 0) throw new Error('EU CSV format changed (no NameAlias_WholeName column)');
  const seen = new Set(), rows = [];
  for (const r of t.slice(1)) {
    if(r.every(v=>!v.trim()))continue;
    if(r.length!==h.length)throw new Error('Malformed CSV row width');
    const n = (r[iN] || '').trim(); if (!n) continue;
    const p = (iP >= 0 && r[iP] || '').trim() || 'EU';
    const k = n + '|' + p; if (seen.has(k)) continue; seen.add(k); rows.push([n, 'EU', p]);
  }
  return rows;
}
export async function refreshSanctions({file=FILE,reviewFile='state/sanctions-review.json',fetchText=get,clock=new Date(),reviewedHashes={}}={}) {
  const t = fs.readFileSync(file, 'utf8');
  const meta = JSON.parse(t.match(/SANCTIONS_META = (\{.*\});/)[1]);
  const oldMatch=t.match(/^export const SANCTIONS: \[string, string, string\]\[\] = (\[[^\n]*\]);$/m);
  if(!oldMatch)throw new Error('Sanctions declaration missing');
  const old=JSON.parse(oldMatch[1]);
  if(!Array.isArray(old)||old.some(r=>!Array.isArray(r)||r.length!==3||r.some(v=>typeof v!=='string')||!['OFAC','EU','UFLPA'].includes(r[1])))throw new Error('Invalid saved sanctions rows');
  const by = (l) => old.filter((r) => r[1] === l);
  const res = {};let pending={}, history={};
  if(fs.existsSync(reviewFile)){const prior=JSON.parse(fs.readFileSync(reviewFile,'utf8'));if(prior.state!=='manual_review_only'||!prior.candidates||typeof prior.candidates!=='object'||Array.isArray(prior.candidates))throw new Error('Invalid saved review candidates');pending=prior.candidates;history=prior.candidate_history||{};if(typeof history!=='object'||Array.isArray(history))throw new Error('Invalid saved candidate history');}
  let rows = [];
  const today = clock.toISOString().slice(0,10);
  if(Object.keys(reviewedHashes).some(k=>!['OFAC','EU'].includes(k)))throw new Error('Unknown reviewed list');
  meta.health ||= {};
  if(typeof meta.health!=='object'||Array.isArray(meta.health))throw new Error('Invalid saved sanctions health');
  for (const [list, parse] of [['OFAC', parseOfac], ['EU', parseEu]]) {
    const prev = by(list), before=meta.health[list]||{};
    try {
      const decision=sanctionsDecision(prev,parse(await fetchText(meta.sources[list])),list,reviewedHashes[list]);
      const {rows:candidate,...health}=decision;
      if(decision.state==='updated') {
        if(pending[list]?.candidate_sha256===decision.candidate_sha256)delete pending[list];
        if(history[list])delete history[list][decision.candidate_sha256];
        rows.push(...candidate);res[list]={...health,last_success:today,stale:false,manual_review:false};
        meta[list.toLowerCase()] = list + ' auto-refreshed ' + today;
      } else {
        rows.push(...prev);res[list]={...health,last_success:before.last_success||null,stale:true,manual_review:true};
        const held={...health,observed_at:today,rows:candidate};
        if(pending[list]){history[list]||={};history[list][pending[list].candidate_sha256]=pending[list];}
        pending[list]=held;history[list]||={};history[list][health.candidate_sha256]=held;
        // Do not replace the old success label with a new success date.
      }
    } catch(e) {
      rows.push(...prev);res[list]={state:'kept_old',reason:'source_or_parse_failed',previous_count:prev.length,last_success:before.last_success||null,stale:true,manual_review:true};
    }
    meta.health[list]={...res[list],last_attempt:today};
  }
  rows.push(...by('UFLPA'));
  rows.sort((a,b)=>a[0]<b[0]?-1:a[0]>b[0]?1:0);
  // checked means both automatic lists were refreshed, never merely attempted.
  if(Object.values(res).every(v=>v.state==='updated'))meta.checked=today;
  const out=t.split('\n')[0]+'\nexport const SANCTIONS_META = '+JSON.stringify(meta)+';\nexport const SANCTIONS: [string, string, string][] = '+JSON.stringify(rows)+';\n';
  const dir=(await import('node:path')).dirname(reviewFile);fs.mkdirSync(dir,{recursive:true});
  const reviewTmp=reviewFile+'.tmp';fs.writeFileSync(reviewTmp,JSON.stringify({state:'manual_review_only',checked_at:today,candidates:pending,candidate_history:history})+'\n');fs.renameSync(reviewTmp,reviewFile);
  const tmp=file+'.tmp';fs.writeFileSync(tmp,out);fs.renameSync(tmp,file);
  return res;
}
