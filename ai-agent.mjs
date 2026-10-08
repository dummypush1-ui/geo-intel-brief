// AI jobs. Rule: AI proposes, code verifies. Nothing unverified is ever written.
import fs from 'fs';
import zlib from 'zlib';
import {extractNotificationPdf} from './updater_runtime/pdf-extract.mjs';
import {groundGst} from './updater_runtime/gst-grounding.mjs';
import { geminiPost } from './gemini.mjs';
import {appendAliases,validateGstChange} from './updater_runtime/table-edit.mjs';
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
    add.push({term,sets:good}); have.add(term);
  }
  if (!add.length) return 'no valid aliases proposed';
  const result=appendAliases(t,add);
  fs.writeFileSync(f,result.source);
  return 'added '+result.added+' aliases';
}

// JOB 2 - GST: read NEW IGST rate notifications and PROPOSE changes (never edits gstmap.ts directly).
// Grounding: one explicit code/rate/description row, with context retained for review.
// The workflow turns state/gst-proposal.json into a Pull Request for you to approve.
export async function draftGst(askFn = ask, fetchFn = fetch) {
  if (!KEY && askFn === ask) return 'skipped: no GEMINI_API_KEY';
  const SEEN = 'state/gst-seen.json';
  const page = await (await fetchFn(IN_URL, { headers: { 'User-Agent': 'hsn-finder-updater' },signal:AbortSignal.timeout(20000) })).text();
  const links = [...page.matchAll(/<a[^>]+href="([^"]+\.pdf)"[^>]*>([\s\S]*?)<\/a>/gi)]
    .map((m) => ({ url: new URL(m[1], IN_URL).href, text: m[2].replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim() }))
    .filter((l) => /integrated tax\s*\(rate\)/i.test(l.text));
  if (!fs.existsSync(SEEN)) { fs.writeFileSync(SEEN, JSON.stringify({ seen: links.map((l) => l.url) }) + '\n'); return 'baseline: ' + links.length + ' notifications marked as already known'; }
  const st = JSON.parse(fs.readFileSync(SEEN, 'utf8')), fresh = links.filter((l) => !st.seen.includes(l.url)).slice(0, 3);
  if (!fresh.length) return 'no new notifications';
  const changes = [], srcs = [], held = []; let rejected = 0;
  for (const l of fresh) {
    const response=await fetchFn(l.url,{signal:AbortSignal.timeout(20000)});if(response.ok===false)throw new Error('Notification PDF HTTP failure');
    if(Number(response.headers?.get('content-length')||0)>10*1024*1024)throw new Error('PDF response too large');
    let bytes;if(response.body){const chunks=[];let size=0;for await(const chunk of response.body){size+=chunk.byteLength;if(size>10*1024*1024)throw new Error('PDF response too large');chunks.push(Buffer.from(chunk));}bytes=Buffer.concat(chunks);}else bytes=Buffer.from(await response.arrayBuffer());
    let text;try{text=extractNotificationPdf(bytes);}catch(e){throw new Error('GST notice held for PDF review: '+l.url+' ('+e.message+')');}
    const out = await askFn('From this Indian GST notification text, list every GOODS rate entry with an HS code. Only what is explicitly stated. JSON: [{"code":"digits only, 2-8 digits","rate":"like 18%","description":"exact description from the same row, excluding code/rate"}]\n\n' + text.slice(0, 90000));
    for (const c of Array.isArray(out) ? out : []) {
      let candidate,code,rate;
      try {
        code=String(c.code || '').replace(/\D/g,'');rate=String(c.rate || '').trim();
        candidate=validateGstChange({code,rate,description:String(c.description || '').slice(0,200),source:l.url},[l.url]);
      }
      catch { rejected++; continue; }
      const grounded=groundGst(candidate,text);
      if(grounded.state!=='row_matched_pending_review'){rejected++;held.push({candidate,source:l.url,...grounded});continue;}
      changes.push({...candidate,evidence:grounded.evidence,review_required:true});
    }
    srcs.push(l.url); st.seen.push(l.url);
  }
  if(srcs.length){
    const file='state/gst-proposal.json';let proposal={state:'manual_review_required',sources:[],changes:[],held:[]};
    if(fs.existsSync(file)){proposal=JSON.parse(fs.readFileSync(file,'utf8'));if(proposal.state!=='manual_review_required'||!Array.isArray(proposal.sources)||!Array.isArray(proposal.changes)||!Array.isArray(proposal.held))throw new Error('Existing GST proposal requires operator archive before replacement');}
    // Existing pending sources are immutable until operator review.
    const freshSources=srcs.filter(s=>!proposal.sources.includes(s));
    proposal.sources.push(...freshSources);proposal.changes.push(...changes.filter(c=>freshSources.includes(c.source)));proposal.held.push(...held.filter(c=>freshSources.includes(c.source)));
    const tmp=file+'.tmp';fs.writeFileSync(tmp,JSON.stringify(proposal,null,1));fs.renameSync(tmp,file);
  }
  fs.writeFileSync(SEEN, JSON.stringify(st) + '\n');
  return changes.length + ' row-matched proposals pending review from ' + srcs.length + ' notifications (' + rejected + ' AI items rejected for invalid schema or unmatched grounding)';
}
