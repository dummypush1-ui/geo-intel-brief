// Copyright (c)2026 Push. Manual supplied-view identity comparison only.
// No Notification API, service worker, timers, sends or network of its own.
const LIMIT=500;
function label(v){return typeof v==='string'&&v.length>0&&v.length<=100&&v.trim()===v&&!/[\p{C}]/u.test(v);}
function identity(v){return typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);}
export function baselineKey(country,project){if(!label(country)||!['','geo','brics'].includes(project))throw new Error('Exact country/project required');return JSON.stringify([country,project]);}
export function validateBaselines(value){
 if(!Array.isArray(value)||value.length>60)throw new Error('Invalid bounded saved baselines');const keys=new Set();
 return value.map(r=>{if(!r||Object.getPrototypeOf(r)!==Object.prototype||!Object.hasOwn(r,'key')||!Object.hasOwn(r,'seen')||Object.keys(r).sort().join(',')!=='key,seen')throw new Error('Invalid baseline');let parsed;try{parsed=JSON.parse(r.key)}catch{throw new Error('Invalid key')};if(!Array.isArray(parsed)||parsed.length!==2||baselineKey(...parsed)!==r.key||keys.has(r.key))throw new Error('Invalid/duplicate key');keys.add(r.key);if(!Array.isArray(r.seen)||r.seen.length>LIMIT||r.seen.some(x=>!identity(x))||new Set(r.seen).size!==r.seen.length)throw new Error('Invalid saved identities');return {key:r.key,seen:[...r.seen]};});
}
export function compareUpdate(saved,key,items){
 if(!Array.isArray(items)||items.length>100||items.some(r=>!r||!identity(r.article_key)))throw new Error('Bounded supplied identities required');
 const entries=validateBaselines(saved),old=entries.find(e=>e.key===key);const current=[...new Set(items.map(r=>r.article_key))];
 const unseen=old?items.filter((r,i)=>!old.seen.includes(r.article_key)&&items.findIndex(x=>x.article_key===r.article_key)===i):[];
 const merged=[...new Set([...current,...(old?.seen||[])])];const next=entries.filter(r=>r.key!==key);next.push({key,seen:merged.slice(0,LIMIT)});
 return {state:old?'compared':'baseline',items:unseen,next:next.slice(-60),memory_trimmed:merged.length>LIMIT||next.length>60,scope:'newly_seen_in_current_supplied_view_not_newly_published'};
}
