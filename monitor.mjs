// Watches every official source. A change must be seen on 2 consecutive runs
// (filters page noise) before a GitHub Issue "Source changed: X" is opened.
import fs from 'fs';
import crypto from 'crypto';
import {ensureIssue}from './updater_runtime/github-issue.mjs';
const STATE = 'state/sources.json';
const app = fs.readFileSync('src/app.js', 'utf8');
const sources = [...app.matchAll(/tag: '(\w+)', name: '([^']+)'.*?url: '([^']+)'/g)].map((m) => ({ id: m[1], name: m[2], url: m[3] }));
const san = fs.readFileSync('src/sanctions.ts', 'utf8').match(/"UFLPA":"([^"]+)"/);
if (san) sources.push({ id: 'UFLPA', name: 'DHS UFLPA Entity List', url: san[1] });
const norm = (h) => h.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>|<[^>]+>/g, ' ').replace(/\b[0-9a-f]{16,}\b/gi, '').replace(/\s+/g, ' ').trim();
// For these three tariffs, compare only the actual code/description/core duty fields.
// HTTP ETags, page layout and dataset version labels can change without changing the app data.
const get = async (url) => {
  const r = await fetch(url, { headers: { 'User-Agent': 'hsn-finder-updater' }, signal: AbortSignal.timeout(60000) });
  if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + url);
  return r;
};
const digest = (rows) => 'd:' + crypto.createHash('sha256').update(JSON.stringify(rows.sort((a, b) => JSON.stringify(a).localeCompare(JSON.stringify(b))))).digest('hex');
const stripHtml = (s) => String(s || '').replace(/<sub>(.*?)<\/sub>/gi, '$1').replace(/<[^>]+>/g, '').replace(/&nbsp;|\u00a0/g, ' ').replace(/^[-\s]+|[\s.;:,]+$/g, '').replace(/\s+/g, ' ').trim().toLowerCase();
async function tariffSig(id) {
  if (id === 'US') {
    // Live official USITC HTS export, through Chapter 97 only; 98/99 are outside app scope.
    const release = await (await get('https://hts.usitc.gov/reststop/currentRelease')).json();
    if (!/^\d{4}HTSRev\d+$/.test(release.name || '')) throw new Error('USITC current release missing');
    const data = await (await get('https://hts.usitc.gov/reststop/exportList?from=0101&to=9707&format=JSON&styles=false')).json();
    if (!Array.isArray(data) || data.length < 25000 || !data.some((r) => r.htsno === '9706.90.00.60')) throw new Error('USITC release incomplete');
    return digest(data.filter((r) => r.htsno && !/^(98|99)/.test(r.htsno)).map((r) => [r.htsno.replace(/\./g, ''), String(r.description || '').replace(/\s+/g, ' ').trim(), r.general || '']));
  }
  if (id === 'UK') {
    const api = 'https://data.api.trade.gov.uk/v1/datasets/uk-tariff-2021-01-01/versions';
    const versions = await (await get(api + '?format=json')).json();
    const v = versions.versions?.[0]?.id;
    if (!/^v\d+\.\d+\.\d+$/.test(v || '')) throw new Error('UK version missing');
    const root = api + '/' + v + '/tables/';
    // Fingerprint only fields the app uses; numeric row IDs and SIDs are not tariff data.
    const cq = 'SELECT commodity__code,commodity__suffix,commodity__description,commodity__validity_start,commodity__validity_end FROM S3Object';
    const codes = await (await get(root + 'commodities-report/data?format=csv&query-s3-select=' + encodeURIComponent(cq))).text();
    // Type 103 + ERGA OMNES area 1011 is the general third-country duty subset baked here.
    const query = "SELECT commodity__code,measure__duty_expression,measure__effective_start_date,measure__effective_end_date,measure__geographical_area__id,measure__additional_code__code FROM S3Object WHERE measure__type__id = '103' AND measure__geographical_area__id = '1011'";
    const duty = await (await get(root + 'measures-on-declarable-commodities/data?format=csv&query-s3-select=' + encodeURIComponent(query))).text();
    if (codes.length < 1e6 || duty.length < 5e5 || !duty.includes('0101210000')) throw new Error('UK tariff data incomplete');
    return 'd:' + crypto.createHash('sha256').update(codes.split('\n').filter(Boolean).sort().join('\n') + '\n' + duty.split('\n').filter(Boolean).sort().join('\n')).digest('hex');
  }
  if (id === 'BR') {
    const data = await (await get('https://portalunico.siscomex.gov.br/classif/api/publico/nomenclatura/download/json')).json();
    if (!Array.isArray(data.Nomenclaturas) || data.Nomenclaturas.length < 14000) throw new Error('Brazil Classif data incomplete');
    return digest(data.Nomenclaturas.map((r) => [r.Codigo.replace(/\./g, ''), stripHtml(r.Descricao)]));
  }
  throw new Error('unknown tariff system ' + id);
}
async function sig(url, id) {
  if (['US', 'UK', 'BR'].includes(id)) return tariffSig(id);
  const r = await get(url);
  const v = r.headers.get('etag') || r.headers.get('last-modified');
  if (v) return 'h:' + v;
  return 's:' + crypto.createHash('sha256').update(norm((await r.text()).slice(0, 2e6))).digest('hex');
}
export async function issue(title,body,options){return ensureIssue(title,body,options);}
export async function monitor({stateFile=STATE,sourceList=sources,signature=sig,issueFn=issue,clock=()=>new Date()}={}) {
  const st = fs.existsSync(stateFile) ? JSON.parse(fs.readFileSync(stateFile, 'utf8')) : {};
  const report = { changed: [], unreachable: [], baseline: 0,issue_health:[] };
  const notify=async(e,id,title,body)=>{
    e.pending_issues ||= [];if(!e.pending_issues.some(p=>p.title===title))e.pending_issues.push({title,body});
    let result;try{result=await issueFn(title,body);}catch{result={state:'failed',reason:'invalid_issue_request',retry_safe:true};}
    report.issue_health.push({id,title,...result});e.issue_state=result.state;
    if(['created','existing'].includes(result.state))e.pending_issues=e.pending_issues.filter(p=>p.title!==title);
  };
  for (const s of sourceList) {
    const e = (st[s.id] = st[s.id] || {});
    try {
      if(e.pending_issue){e.pending_issues ||= [];if(!e.pending_issues.some(p=>p.title===e.pending_issue.title))e.pending_issues.push(e.pending_issue);delete e.pending_issue;}
      for(const pending of [...(e.pending_issues||[])])await notify(e,s.id,pending.title,pending.body);
      const g = await signature(s.url, s.id); e.fails = 0;
      if (['US', 'UK', 'BR'].includes(s.id) && !e.sig?.startsWith('d:')) { e.sig = g; e.cand = null; e.n = 0; report.baseline++; continue; }
      if (!e.sig) { e.sig = g; report.baseline++; }
      else if (g === e.sig) { e.cand = null; e.n = 0; }
      else if (g === e.cand) { e.n++; if (e.n >= 2) { e.sig = g; e.cand = null; e.n = 0; e.changedAt = clock().toISOString().slice(0, 10); report.changed.push(s.id);
        const note = ['US', 'UK', 'BR'].includes(s.id)
          ? 'The official code/description or core-duty data changed'
          : 'The official source page signature changed; this does not prove the bundled tariff rates are stale';
        await notify(e,s.id,'Source changed: ' + s.name, `${note} (${e.changedAt}).\n${s.url}\n\nReview exact source changes before updating the app.`); } }
      else { e.cand = g; e.n = 1; }
    } catch (err) {
      e.fails = Math.min((e.fails || 0) + 1, 8); report.unreachable.push(s.id);
      if (e.fails === 7) await notify(e,s.id,'Source unreachable for 7 attempts: ' + s.name, s.url + '\n' + err.message);
    }
  }
  const dir=(await import('node:path')).dirname(stateFile);fs.mkdirSync(dir,{recursive:true});
  const tmp=stateFile+'.tmp';fs.writeFileSync(tmp,JSON.stringify(st,null,1)+'\n');fs.renameSync(tmp,stateFile);
  return report;
}
