'use strict';
const el = id => document.getElementById(id);
const state = {rows: [], selected: new Set(), shown: 30, brief: null, watches: []};
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeUrl = value => { try {const u = new URL(value); return ['http:','https:'].includes(u.protocol) ? u.href : '#';} catch {return '#';} };
function notice(text) {el('notice').textContent = text; el('notice').hidden = !text;}
async function api(path, options = {}) {
  const response = await fetch(path, {credentials:'same-origin', ...options});
  const data = await response.json().catch(() => ({error:'Unexpected server response. Try again after Render wakes.'}));
  if (!response.ok) { if(response.status === 401) locked(); throw new Error(typeof data.error === 'string' ? data.error : data.error?.message || 'Request failed (' + response.status + ')'); }
  return data;
}
function locked() {el('workspace').hidden = true; el('login-panel').hidden = false; el('logout').hidden = true;}
function unlocked() {el('workspace').hidden = false; el('login-panel').hidden = true; el('logout').hidden = false;}
function filters() {return {search:el('search').value.trim(), source:el('source').value, country:el('country').value, hs:el('hs').value.replace(/\D/g,'')};}
function filtered() {const f=filters(); return state.rows.filter(a => (!f.source || a.app===f.source) && (!f.country || a.country===f.country) && (!f.hs || a.codes.some(t=>t.code.startsWith(f.hs.slice(0,4)))) && (!f.search || (a.title+' '+a.summary+' '+a.source).toLowerCase().includes(f.search.toLowerCase())));}
function render() {
  const rows = filtered(); el('visible-count').textContent = rows.length + ' stories';
  el('feed').innerHTML = rows.slice(0,state.shown).map(a => `<article class="story"><div class="story-head"><input type="checkbox" data-select="${esc(a.id)}" aria-label="Select ${esc(a.title)}" ${state.selected.has(a.id)?'checked':''}><div><div class="meta">${esc(a.app)} · ${esc(a.source)} · ${esc(a.country || 'Global')} · ${esc(a.date.slice(0,10))}</div><h3><a href="${esc(safeUrl(a.url))}" target="_blank" rel="noopener noreferrer">${esc(a.title)}</a></h3></div></div><p class="summary">${esc(a.summary.slice(0,350))}</p><div class="chips"><span class="badge">${esc(a.category)}${a.risk?' · '+esc(a.risk):''}</span>${a.codes.map(t=>`<a class="chip" href="/hsn/#code=0:${encodeURIComponent(t.code)}" target="_blank" rel="noopener" title="${esc(t.label)} — matched: ${esc(t.terms.join(', '))}">HS ${esc(t.code)} ↗</a>`).join('')}</div></article>`).join('') || '<div class="empty">No matching stories yet. Collect both feeds, wait for completion, then refresh—or change your filters.</div>';
  el('more').hidden = rows.length <= state.shown;
  el('selected-count').textContent = state.selected.size + ' stories selected';
}
async function refresh() {
  const [feed, caps] = await Promise.all([api('/api/intel/feed'),api('/api/intel/capabilities')]);
  state.rows=feed.articles; state.selected=new Set([...state.selected].filter(id=>state.rows.some(a=>a.id===id)));
  unlocked();
  const country=el('country').value;
  const countries=[...new Set(state.rows.map(a=>a.country).filter(Boolean))].sort();
  el('country').innerHTML='<option value="">All countries</option>'+countries.map(c=>`<option>${esc(c)}</option>`).join('');
  el('country').value=countries.includes(country)?country:'';
  el('story-count').textContent=state.rows.length; el('country-count').textContent=countries.length;
  el('code-count').textContent=new Set(state.rows.flatMap(a=>a.codes.map(t=>t.code))).size;
  el('provider-count').textContent=caps.providers.length;
  el('provider').innerHTML='<option value="">Automatic fallback</option>'+caps.providers.map(p=>`<option value="${esc(p)}">${esc(p.toUpperCase())}</option>`).join('');
  el('analyze').disabled=!caps.providers.length;
  el('ai-status').textContent=caps.providers.length?'Server keys are configured. Provider access is checked when you analyze.':'Add GEMINI_KEYS, GROQ_KEYS, MISTRAL_KEYS or NVIDIA_KEYS in Render, then redeploy.';
  el('stream-storage').textContent='Stream edits are saved in '+caps.stream_storage+'. Workspace sign-in also unlocks BRICS stream controls.';
  el('ships').disabled=!caps.ais.keySet;
  el('ship-status').textContent=caps.ais.keySet?'Live feed configured; load positions to check availability.':'Add AISSTREAM_KEY in Render to enable live positions.';
  el('updated').textContent='Updated '+new Date(feed.updated).toLocaleString()+' · Latest 150 records per feed';
  notice(Object.entries(feed.errors).map(([k,v])=>k.toUpperCase()+': '+v).join(' · ')); render();
}
async function busy(id, fn) {const b=el(id);b.disabled=true;try{await fn();}catch(e){notice(e.message);}finally{b.disabled=false;}}
el('login-form').addEventListener('submit', async e=>{
  e.preventDefault();el('login-error').textContent='';
  try {await api('/api/intel/session',{method:'POST',headers:{'X-Trigger-Key':el('secret').value}});el('secret').value='';await refresh();}
  catch(error){el('login-error').textContent=error.message;}
});
el('logout').onclick=async()=>{try{await api('/api/intel/session',{method:'DELETE'});location.reload();}catch(e){notice(e.message);}};
el('refresh').onclick=()=>busy('refresh',refresh);
el('collect').onclick=()=>busy('collect',async()=>{
  const result=await api('/api/trigger/collect',{method:'POST'});
  notice('Collection '+result.status.replaceAll('_',' ')+'. You can leave this page; it runs on the server.');
  pollCollection(0);
});
let pollTimer;
function pollCollection(attempt){clearTimeout(pollTimer);pollTimer=setTimeout(async()=>{try{const s=await api('/api/status');if(s.collecting&&attempt<30){notice('Collecting both feeds…');pollCollection(attempt+1);}else{await refresh();const failed=Object.entries(s.scheduler.jobs).filter(([k,v])=>(k.includes('collect')||k.includes('tier'))&&!v.ok);notice(s.collecting?'Collection still running. Refresh later.':failed.length?'Collection completed with source errors. Check Render logs.':'Collection finished. Feed refreshed.');}}catch(e){notice(e.message);}},8000);}
['search','source','country','hs'].forEach(id=>el(id).addEventListener('input',()=>{state.shown=30;render();}));
el('more').onclick=()=>{state.shown+=30;render();};
el('feed').addEventListener('change',e=>{const id=e.target.dataset.select;if(!id)return;if(e.target.checked){if(state.selected.size===6){e.target.checked=false;notice('Select up to six stories for one brief.');return;}state.selected.add(id);}else state.selected.delete(id);el('selected-count').textContent=state.selected.size+' stories selected';});
el('analyze').onclick=()=>busy('analyze',async()=>{
  if(!state.selected.size)throw new Error('Select at least one story using its checkbox.');
  el('ai-status').textContent='Reading selected stories and building the brief…';
  try{const data=await api('/api/intel/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ids:[...state.selected],provider:el('provider').value})});state.brief=data;el('analysis-result').hidden=false;el('analysis-text').textContent=data.text;el('analysis-meta').textContent=data.provider+' · '+data.model;el('analysis-sources').innerHTML=data.sources.map(s=>`<li><a href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener noreferrer">${esc(s.title)}</a></li>`).join('');el('ai-status').textContent='Brief ready. Verify the cited sources before acting.';}catch(e){el('ai-status').textContent='Analysis did not complete.';throw e;}
});
el('download-brief').onclick=()=>{const d=state.brief;if(!d)return;const text='Geo Intel Brief\nGenerated: '+d.generated+'\nAI: '+d.provider+' / '+d.model+'\n\n'+d.text+'\n\nSources\n'+d.sources.map(s=>'['+s.number+'] '+s.title+'\n'+s.url).join('\n')+'\n\nAI research only. Verify reported facts and HS classification.';const url=URL.createObjectURL(new Blob([text],{type:'text/plain'}));const a=document.createElement('a');a.href=url;a.download='geo-intel-brief.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
el('ships').onclick=()=>busy('ships',async()=>{const port=el('port').value;const d=await api('/hsn/api/ships?port='+encodeURIComponent(port));el('port').innerHTML='<option value="ALL">All tracked ports</option>'+d.ports.map(p=>`<option value="${esc(p.code)}">${esc(p.name)} (${p.count})</option>`).join('');el('port').value=port;el('ship-status').textContent=d.count+' vessels matched · '+(d.warming?'Feed warming up':'Updated '+new Date(d.updated).toLocaleTimeString());el('ship-list').innerHTML=d.vessels.slice(0,12).map(v=>`<p><b>${esc(v.name||v.mmsi)}</b> · ${esc(v.type||'Unknown type')}<br>${esc(v.port)} · ${esc(v.flag||'Unknown flag')} · seen ${v.seenAgoSec}s ago</p>`).join('')||'<p>No positions available for this port yet.</p>';});
try{state.watches=JSON.parse(localStorage.getItem('geo-intel-views')||'[]');if(!Array.isArray(state.watches))state.watches=[];state.watches=state.watches.filter(w=>w&&typeof w==='object').slice(0,8);}catch{state.watches=[];}
function watches(){el('watchlist').innerHTML=state.watches.map((w,i)=>`<span class="watch"><button data-watch="${i}">${esc(w.country||w.hs||w.search||w.source||'All stories')}</button><button class="remove-watch" data-remove="${i}" aria-label="Remove saved view">×</button></span>`).join('');}
function saveWatches(){try{localStorage.setItem('geo-intel-views',JSON.stringify(state.watches));}catch{notice('Browser storage is unavailable; saved views will last only for this visit.');}watches();}
el('save-watch').onclick=()=>{if(state.watches.length>=8){notice('You can save up to eight views. Remove one first.');return;}state.watches.push(filters());saveWatches();};
el('watchlist').onclick=e=>{if(e.target.dataset.remove!==undefined){state.watches.splice(Number(e.target.dataset.remove),1);saveWatches();}else if(e.target.dataset.watch!==undefined){const w=state.watches[Number(e.target.dataset.watch)];for(const id of ['search','source','country','hs'])el(id).value=w[id]||'';state.shown=30;render();}};
watches();refresh().catch(e=>{if(el('workspace').hidden)el('login-error').textContent=e.message==='unauthorized'?'':e.message;else notice(e.message);});
