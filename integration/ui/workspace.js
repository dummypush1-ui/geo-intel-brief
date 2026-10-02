/* Copyright (c) 2026 Push. No key or live endpoint in this client. */
const byId = id => document.getElementById(id);
let active = 'finder', relatedId = 0, newsId = 0, statsId = 0, signalsId = 0, snapshotsId = 0, lastContext = '';
const frame = byId('finder');
const SYS_COUNTRY = {IN:'India',US:'United States',EU:'European Union',UK:'United Kingdom',KR:'South Korea',CA:'Canada',JP:'Japan',AU:'Australia',BR:'Brazil',TW:'Taiwan',NZ:'New Zealand',NO:'Norway',SG:'Singapore',IL:'Israel',MX:'Mexico',HK:'Hong Kong',ZA:'South Africa',PE:'Peru',CN:'China',AE:'United Arab Emirates',SAC:'India'};
function safeLink(value) {
  try { const u = new URL(value); return ['https:','http:'].includes(u.protocol) && !u.username && !u.password ? u.href : null; } catch { return null; }
}
function render(container, items) {
  container.replaceChildren();
  for (const item of items) {
    const article = item.article || item, url = safeLink(article.url);
    if (!url) continue;
    const row = document.createElement('article'); row.className = 'story';
    const link = document.createElement('a'); link.href = url; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.textContent = String(article.title || 'News'); row.append(link);
    const meta = document.createElement('p'); meta.className = 'story-meta'; meta.textContent = [article.source, article.original_country, article.published_at ? 'Published '+String(article.published_at).slice(0,10) : '', article.collected_at ? 'Collected '+String(article.collected_at).slice(0,10) : ''].filter(Boolean).join(' · '); row.append(meta);
    const summary = document.createElement('p'); summary.textContent = String(article.summary || ''); row.append(summary);
    for (const label of [article.project === 'geo' ? 'Geo' : 'BRICS', article.category, ...(item.match?.reasons || []).map(r => r.type === 'explicit_code' ? 'Explicit code mention, unverified' : r.type === 'country_context' ? 'Country context' : 'Product mention')]) {
      if (!label) continue; const badge = document.createElement('span'); badge.className = 'badge'; badge.textContent = label; row.append(badge);
    }
    const signal=document.createElement('p');signal.className='story-meta';
    signal.textContent=article.project==='geo' ? [article.risk_level ? 'Risk: '+article.risk_level : 'Risk: not recorded',article.credibility ? 'Credibility: '+article.credibility : 'Credibility: not recorded',article.score!=null ? 'Score: '+article.score : ''].filter(Boolean).join(' · ') : (article.corroboration_count!=null ? 'Supplied corroboration entries: '+article.corroboration_count : 'Corroboration: not recorded');row.append(signal);
    if(article.article_key && ['geo','brics'].includes(article.project)) {
      const button=document.createElement('button');button.type='button';button.textContent='Find exact mentioned codes';
      const status=document.createElement('p');status.setAttribute('role','status');const choices=document.createElement('div');
      let attempt=0;
      button.addEventListener('click',async()=>{
        const current=++attempt;status.textContent='Checking exact code mentions...';choices.replaceChildren();
        try {
          const items=await request('/api/finder-context',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project:article.project,article_key:article.article_key})});
          if(current!==attempt || !row.isConnected)return;
          status.textContent=items.length ? 'Exact mentions only. These do not verify a tariff change.' : 'No verified exact code destinations.';
          for(const item of items) {
            let u;try{u=new URL(item.finder_url,location.origin);}catch{continue;}
            if(u.username || u.password || u.origin!==location.origin || u.pathname!=='/workspace/finder/index.html' || u.search || !/^#code=\d+:\d{2,12}$/.test(u.hash))continue;
            const pick=document.createElement('button');pick.type='button';pick.textContent=String(item.context?.system || 'Code')+' '+String(item.context?.code || '');
            pick.addEventListener('click',()=>{frame.src=u.href;document.querySelector('[data-view=finder]').click();frame.focus();});choices.append(pick);
          }
        } catch(error){if(current===attempt && row.isConnected)status.textContent=error.message;}
      });row.append(button,status,choices);
    }
    container.append(row);
  }
}
async function request(url, options) {
  const response = await fetch(url, {credentials:'same-origin',cache:'no-store',...options});
  if (response.status === 403) throw new Error('Private news is locked. Approved access control is not configured.');
  if (!response.ok) throw new Error('News is unavailable. Finder remains separate.');
  const data = await response.json(); return Array.isArray(data.items) ? data.items : [];
}
async function readNews() {
  const id = ++newsId, project = active;
  byId('news-status').textContent = 'Loading news...'; byId('news-results').replaceChildren();
  try {
    const params = new URLSearchParams({q:byId('news-query').value,project,category:byId('news-category').value,country:byId('news-country').value});
    const items = await request('/api/news?' + params);
    if (id !== newsId) return;
    render(byId('news-results'), items); byId('news-status').textContent = items.length ? `Showing ${items.length} ${items.length === 1 ? 'story' : 'stories'} (up to first 100, newest collection first).` : 'No stories in this view.';
  } catch (error) { if (id === newsId) byId('news-status').textContent = error.message; }
}
for (const button of document.querySelectorAll('[data-view]')) button.addEventListener('click', () => {
  active = button.dataset.view;
  for (const other of document.querySelectorAll('[data-view]')) other.setAttribute('aria-pressed',String(other === button));
  byId('finder-view').hidden = active !== 'finder'; byId('news-view').hidden = active === 'finder';
  if (active !== 'finder') {byId('news-heading').textContent = active === 'geo' ? 'Geo news' : 'BRICS news'; byId('news-category').value='';byId('news-country').value='';readStats(active);readSignals(active);readSnapshots(active);readNews();}
});
byId('news-search').addEventListener('submit', event => {event.preventDefault();readNews();});
async function syncContext() {
  let context;
  try {
    const doc = frame.contentDocument;
    const m = frame.contentWindow.location.hash.match(/^#code=(\d+):(\d+)$/);
    const code = doc.querySelector('.detail-code')?.textContent.replace(/\D/g,'');
    const description = doc.querySelector('.detail-desc')?.textContent || '';
    const system = doc.querySelector('.detail-head .sys-tag')?.textContent || '';
    if (!m || !code) {
      const query = doc.querySelector('#q-main')?.value.trim() || '';
      if (query) {await searchContext(query); return;}
      lastContext = ''; ++relatedId; byId('context').textContent = ''; byId('related').replaceChildren(); byId('related-status').textContent = 'No code selected.'; return;
    }
    context = {code,system,country:SYS_COUNTRY[system] || '',product_terms:[description].filter(t => t.length >= 3)};
  } catch {return;}
  const signature = JSON.stringify(context); if (signature === lastContext) return; lastContext = signature;
  const id = ++relatedId;
  byId('context').textContent = `${context.system || 'Code'} ${context.code}${context.country ? ' · ' + context.country : ''}`;
  byId('related').replaceChildren(); byId('related-status').textContent = 'Loading related news...';
  try {
    const items = await request('/api/related-news',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(context)});
    if (id !== relatedId) return;
    render(byId('related'),items); byId('related-status').textContent = items.length ? `${items.length} stories with matching evidence.` : 'No matching stories. This does not mean there is no trade risk.';
  } catch(error) {if (id === relatedId) {lastContext='';byId('related-status').textContent = error.message;}}
}
async function searchContext(query) {
  const signature = 'search:' + query;
  if (signature === lastContext) return; lastContext = signature;
  const id = ++relatedId;
  byId('context').textContent = 'News search: ' + query;
  byId('related').replaceChildren(); byId('related-status').textContent = 'Loading news search...';
  try {
    const items = await request('/api/news?' + new URLSearchParams({q:query}));
    if (id !== relatedId) return;
    render(byId('related'),items); byId('related-status').textContent = items.length ? `${items.length} news results. Code results stay in Finder.` : 'No news matches. Code results stay in Finder.';
  } catch(error) {if (id === relatedId) {lastContext='';byId('related-status').textContent = error.message;}}
}
frame.addEventListener('load', () => {
  frame.contentWindow.addEventListener('hashchange', () => requestAnimationFrame(syncContext));
  let searchTimer;
  frame.contentDocument.addEventListener('input', event => {
    if (event.target.id !== 'q-main') return;
    clearTimeout(searchTimer); searchTimer = setTimeout(syncContext,350);
  });
  new MutationObserver(() => requestAnimationFrame(syncContext)).observe(frame.contentDocument.body,{childList:true,subtree:true});
  syncContext();
});

async function readStats(project) {
  const id=++statsId;
  byId('news-stats').textContent='Loading read-view counts...';
  try {
    const r=await fetch('/api/news-stats?'+new URLSearchParams({project}),{credentials:'same-origin',cache:'no-store'});
    if(!r.ok)throw new Error('Read-view counts unavailable.');
    const d=await r.json();if(active!==project || id!==statsId)return;
    byId('news-stats').textContent=`${Number.isFinite(d.count) ? d.count : 'Unknown number of'} loaded stories, not total database count. Latest collection: ${d.latest_collected ? String(d.latest_collected).replace('T',' ').slice(0,16)+' UTC' : 'not recorded'}.`;
    for(const [id,key,label] of [['news-category','categories','All categories'],['news-country','countries','All countries']]) {
      const select=byId(id), selected=select.value;select.replaceChildren();const first=document.createElement('option');first.value='';first.textContent=label;select.append(first);
      for(const row of d[key] || []) {const option=document.createElement('option');option.value=String(row.label);option.textContent=String(row.label)+(Number.isFinite(row.count) ? ` (${row.count})` : '');select.append(option);}
      if([...select.options].some(option=>option.value===selected))select.value=selected;
    }
  } catch(error){if(active===project && id===statsId)byId('news-stats').textContent=error.message;}
}
for(const id of ['news-category','news-country'])byId(id).addEventListener('change',readNews);

async function readSignals(project) {
 const id=++signalsId, status=byId('signal-status'), values=byId('signal-values');
 status.textContent='Loading dashboard signals...';values.replaceChildren();
 try {
  const r=await fetch('/api/dashboard-signals?'+new URLSearchParams({project}),{credentials:'same-origin',cache:'no-store'});
  if(!r.ok)throw new Error('Dashboard signals unavailable.');const d=await r.json();
  if(active!==project || id!==signalsId)return;
  status.textContent='Signals from '+(Number.isFinite(d.loaded_count) ? d.loaded_count : 'unknown number of')+' loaded stories only, not database totals.';
  const add=text=>{const p=document.createElement('p');p.textContent=text;values.append(p);};
  if(project==='geo') {
   add('Critical in 24h (loaded sample): '+(Number.isFinite(d.critical_24h_loaded) ? d.critical_24h_loaded : 'not recorded')+'. Critical stories missing time: '+(Number.isFinite(d.critical_missing_time_count) ? d.critical_missing_time_count : 'not recorded')+'.');
   for(const [key,label,missing] of [['risk_levels','Risk levels','missing_risk_count'],['credibility_levels','Credibility','missing_credibility_count']])add(label+': '+Object.entries(d[key] || {}).map(([k,v])=>k+' '+v).join(', ')+'; not recorded '+(Number.isFinite(d[missing]) ? d[missing] : 'not recorded')+'.');
  } else add('Critical count unavailable without the original BRICS policy. Corroboration missing in '+(Number.isFinite(d.missing_corroboration_count) ? d.missing_corroboration_count : 'unknown number of')+' loaded stories.');
 }catch(error){if(active===project && id===signalsId)status.textContent=error.message;}
}

function snapshotLink(value) {
 if(typeof value!=='string' || /[\\%]/.test(value) || /[\p{C}\u2800\u3164\u115f\u1160\uffa0]/u.test(value))return null;
 const link=safeLink(value);if(!link)return null;
 const u=new URL(link);
 if(u.search || u.hash || !/^[a-z0-9]+(?:[.-][a-z0-9]+)*$/.test(u.hostname) || !u.hostname.includes('.') || /(?:^|\.)(?:localhost|local|internal|test|invalid|example)$/.test(u.hostname) || /^(?:[0-9]+|0x[0-9a-f]+)$/.test(u.hostname.split('.').at(-1)) || (u.port && !['80','443'].includes(u.port)))return null;
 return u.href;
}
async function readSnapshots(project) {
 const id=++snapshotsId,status=byId('snapshot-status'),panels=byId('snapshot-panels');
 status.textContent='Loading captured dashboard snapshots...';panels.replaceChildren();
 const labels=project==='geo' ? {geo_events:'Geo events'} : {brics_sources:'BRICS source observations',brics_streams:'BRICS stream links'};
 const unavailable=(key,unwired=false)=>{const p=document.createElement('p');p.textContent=labels[key]+(unwired ? ': snapshot reader is not connected.' : ': verified snapshot unavailable.');panels.append(p);};
 try {
  const r=await fetch('/api/dashboard-snapshots?'+new URLSearchParams({project}),{credentials:'same-origin',cache:'no-store'});
  if(!r.ok)throw new Error('Captured dashboard snapshots unavailable.');const d=await r.json();
  if(active!==project || id!==snapshotsId)return;
  if(d.project!==project || d.not_live_status!==true)throw new Error('Captured dashboard snapshot contract unavailable.');
  status.textContent='Supplied snapshots only, not current source health or live video.';
  for(const key of Object.keys(labels)) {
   const panel=d.panels?.[key];
   if(panel?.state!=='supplied_snapshot' || !Array.isArray(panel.items) || !panel.observed_at){unavailable(key,d.state==='snapshot_readers_unwired');continue;}
   const section=document.createElement('section');section.className='snapshot-panel';const heading=document.createElement('h4');heading.textContent=labels[key];section.append(heading);
   const observation=document.createElement('p');observation.className='muted';observation.textContent='Snapshot observed at '+String(panel.observed_at)+'.';section.append(observation);
   if(!panel.items.length){const p=document.createElement('p');p.textContent='No entries in this supplied snapshot.';section.append(p);}
   let shown=0;
   for(const item of panel.items.slice(0,100)) {
    if(!item || typeof item!=='object')continue;
    const url=snapshotLink(item.source_url || item.url || item.watch_url);if(!url || typeof item.name!=='string' || !/[\p{L}\p{N}\p{S}]/u.test(item.name.replace(/[\u2800\u3164\u115f\u1160\uffa0\ufffc]/g,'')) || /[\p{C}\u2800\u3164\u115f\u1160\uffa0]/u.test(item.name))continue;
    const row=document.createElement('article');row.className='snapshot-row';const link=document.createElement('a');link.href=url;link.target='_blank';link.rel='noopener noreferrer';link.textContent=item.name;row.append(link);
    const meta=document.createElement('p');
    if(key==='geo_events')meta.textContent='Event date: '+String(item.event_date || 'not recorded');
    else if(key==='brics_sources')meta.textContent=[item.country,'Captured status: '+(['ok','warning','error','disabled'].includes(item.last_status) ? item.last_status : 'not recorded'),'Captured count: '+(Number.isInteger(item.last_count) && item.last_count>=0 ? item.last_count : 'not recorded'),'Last checked in snapshot: '+String(item.last_checked || 'not recorded')].filter(Boolean).join(' · ');
    else meta.textContent=[item.country,'Outbound link only. Availability not checked.'].filter(Boolean).join(' · ');
    row.append(meta);
    if(key==='geo_events' && typeof item.description==='string'){const p=document.createElement('p');p.textContent=/[\p{C}]/u.test(item.description.replace(/[\n\t]/g,'')) ? '' : item.description;row.append(p);}
    section.append(row);shown++;
   }
   if(panel.items.length && !shown){const p=document.createElement('p');p.textContent='No displayable links in this supplied snapshot.';section.append(p);}
   if(panel.truncated===true){const p=document.createElement('p');p.className='muted';p.textContent='Showing the first 100 entries in deterministic snapshot order.';section.append(p);}
   if(Number.isInteger(panel.rejected_count) && panel.rejected_count>0){const p=document.createElement('p');p.className='muted';p.textContent=panel.rejected_count+' entries withheld by snapshot validation.';section.append(p);}
   panels.append(section);
  }
 } catch(error){if(active===project && id===snapshotsId){status.textContent=error.message;panels.replaceChildren();for(const key of Object.keys(labels))unavailable(key);}}
}
