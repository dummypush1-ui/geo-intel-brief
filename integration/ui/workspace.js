import {newsScrollController} from './news_scroll.js';
/* Copyright (c) 2026 Push. No key or live endpoint in this client. */
const byId = id => document.getElementById(id);
let active = 'finder', relatedId = 0, newsId = 0, statsId = 0, signalsId = 0, snapshotsId = 0, volumeId = 0, lastContext = '';
const frame = byId('finder');
const SYS_COUNTRY = {IN:'India',US:'United States',EU:'European Union',UK:'United Kingdom',KR:'South Korea',CA:'Canada',JP:'Japan',AU:'Australia',BR:'Brazil',TW:'Taiwan',NZ:'New Zealand',NO:'Norway',SG:'Singapore',IL:'Israel',MX:'Mexico',HK:'Hong Kong',ZA:'South Africa',PE:'Peru',CN:'China',AE:'United Arab Emirates',SAC:'India'};
function safeLink(value) {
  try { const u = new URL(value); return ['https:','http:'].includes(u.protocol) && !u.username && !u.password ? u.href : null; } catch { return null; }
}
function render(container, items, append = false) {
  if(!append)container.replaceChildren();
  for (const item of items) {
    const article = item.article || item, url = safeLink(article.url);
    if (!url) continue;
    const row = document.createElement('article'); row.className = 'story';
    const link = document.createElement('a'); link.href = url; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.textContent = String(article.title || 'News'); row.append(link);
    const meta = document.createElement('p'); meta.className = 'story-meta'; meta.textContent = [article.source, article.original_country, article.published_at ? 'Published '+String(article.published_at).slice(0,10) : '', article.collected_at ? 'Collected '+String(article.collected_at).slice(0,10) : ''].filter(Boolean).join(' · '); row.append(meta);
    const summary = document.createElement('p'); summary.textContent = String(article.summary || ''); row.append(summary);
    for (const label of [article.project === 'geo' ? 'Geo' : 'Other source', article.category, ...(item.match?.reasons || []).map(r => r.type === 'explicit_code' ? 'Explicit code mention, unverified' : r.type === 'country_context' ? 'Country context' : 'Product mention')]) {
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
const fullPages = byId('news-view').dataset.fullNewsPages === 'true';
let shownNews=0,removedNews=0;
const scrollNews=newsScrollController({
 async fetchPage(filters,cursor,signal){
  const p=new URLSearchParams({...filters,limit:'25'});if(cursor)p.set('cursor',cursor);
  const r=await fetch('/api/news-page?'+p,{credentials:'same-origin',cache:'no-store',signal});
  if(r.status===409)throw new Error('News read expired or changed. Refresh to restart.');
  if(r.status===429)throw new Error('News is busy. Refresh to retry after a short pause.');
  if(!r.ok)throw new Error('Whole-store news unavailable. Refresh to restart.');
  return r.json();
 },
 onPage(items,{first}){
  const box=byId('news-results');if(first){box.replaceChildren();shownNews=removedNews=0;}
  render(box,items,true);shownNews+=items.length;
  // Bound live DOM without imposing a bound on store traversal. Preserve visual
  // position by compensating for removed cards above the viewport.
  let removedHeight=0;
  while(box.children.length>200){const card=box.firstElementChild;removedHeight+=card.getBoundingClientRect().height+parseFloat(getComputedStyle(card).marginBottom||0)+parseFloat(getComputedStyle(card).marginTop||0);card.remove();removedNews++;}
  if(removedHeight)window.scrollBy(0,-removedHeight);
  const notice=byId('news-trim-notice');notice.hidden=!removedNews;notice.textContent=removedNews?`${removedNews} earlier cards left the display window. Refresh to start over.`:'';
  byId('news-status').textContent=`Read ${shownNews} matching stories so far. Total unknown; source can change.`;
 },
 onState(text,{busy,canLoad}){if(text)byId('news-scroll-status').textContent=text;byId('news-load-more').disabled=!canLoad;byId('news-results').setAttribute('aria-busy',String(busy));}
});
byId('news-load-more').addEventListener('click',()=>scrollNews.more());
if('IntersectionObserver'in window){
 const observer=new IntersectionObserver(entries=>{if(fullPages && active==='geo' && entries.some(e=>e.isIntersecting))scrollNews.more();},{rootMargin:'0px 0px 300px 0px'});
 observer.observe(byId('news-scroll-sentinel'));
}
async function readNews() {
 if(fullPages && active==='geo'){
  ++newsId;byId('news-scroll-sentinel').hidden=false;byId('news-status').textContent='Loading whole-store read...';byId('news-results').replaceChildren();byId('news-trim-notice').hidden=true;readVolume(active);
  return scrollNews.reset({q:byId('news-query').value,project:active,category:byId('news-category').value,country:byId('news-country').value,sort:byId('news-sort').value});
 }

  const id = ++newsId, project = active;
  byId('news-status').textContent = 'Loading news...'; byId('news-results').replaceChildren();readVolume(project);
  try {
    const params = new URLSearchParams({q:byId('news-query').value,project,category:byId('news-category').value,country:byId('news-country').value,sort:byId('news-sort').value});
    const items = await request('/api/news?' + params);
    if (id !== newsId) return;
    render(byId('news-results'), items); byId('news-status').textContent = items.length ? `Showing ${items.length} ${items.length === 1 ? 'story' : 'stories'} (up to first 100 in selected sort; loaded view, not full database).` : 'No stories in this view.';
  } catch (error) { if (id === newsId) byId('news-status').textContent = error.message; }
}
for (const button of document.querySelectorAll('[data-view]')) button.addEventListener('click', () => {
  scrollNews.cancel();byId('news-scroll-sentinel').hidden=true;
  active = button.dataset.view;
  for (const other of document.querySelectorAll('[data-view]')) other.setAttribute('aria-pressed',String(other === button));
  byId('finder-view').hidden = active !== 'finder'; byId('news-view').hidden = active !== 'geo';byId('live-view').hidden=active!=='live';byId('channels-view').hidden=active!=='channels';
  if (active === 'geo') {byId('news-heading').textContent = active === 'geo' ? 'Geo news' : 'BRICS news'; byId('news-category').value='';byId('news-country').value='';const sort=byId('news-sort');sort.replaceChildren();for(const [value,label] of [['newest','Newest collection'],['title','Title A-Z'],['country','Country A-Z'],active==='geo' ? ['score','Highest Geo score'] : ['corroboration','Most supplied corroboration entries']]){const option=document.createElement('option');option.value=value;option.textContent=label;sort.append(option);}byId('export-status').textContent='';readStats(active);readSignals(active);readSnapshots(active);readNews();readCritical();readSourceHealth();}
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
for(const id of ['news-category','news-country','news-sort'])byId(id).addEventListener('change',readNews);

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

function snapshotLink(value,key) {
 if(typeof value!=='string' || /[\\%]/.test(value) || /[\p{C}\u2800\u3164\u115f\u1160\uffa0]/u.test(value))return null;
 if(key==='brics_streams' && /^https:\/\/www\.youtube\.com\/watch\?v=[A-Za-z0-9_-]{11}$/.test(value) && !/[\r\n]/.test(value))return value;
 const link=safeLink(value);if(!link)return null;
 const u=new URL(link);
 if(key==='brics_streams' && u.hostname==='www.youtube.com')return /^https:\/\/www\.youtube\.com\/channel\/UC[A-Za-z0-9_-]{22}\/live$/.test(value) && !/[\r\n]/.test(value) ? value : null;
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
    const url=snapshotLink(item.source_url || item.url || item.watch_url,key);if(!url || typeof item.name!=='string' || !/[\p{L}\p{N}\p{S}]/u.test(item.name.replace(/[\u2800\u3164\u115f\u1160\uffa0\ufffc]/g,'')) || /[\p{C}\u2800\u3164\u115f\u1160\uffa0]/u.test(item.name))continue;
    const row=document.createElement('article');row.className='snapshot-row';const link=document.createElement('a');link.href=url;link.target='_blank';link.rel='noopener noreferrer';link.textContent=item.name;row.append(link);
    const meta=document.createElement('p');
    if(key==='geo_events')meta.textContent=['Event date: '+String(item.event_date || 'not recorded'),item.category ? 'Category: '+String(item.category) : '',item.confidence ? 'Confidence: '+String(item.confidence) : ''].filter(Boolean).join(' · ');
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

byId('news-export').addEventListener('click',async()=>{
 const project=active,status=byId('export-status');if(!['geo','brics'].includes(project))return;
 status.textContent='Preparing loaded sample export...';
 try {
  const params=new URLSearchParams({project,q:byId('news-query').value,category:byId('news-category').value,country:byId('news-country').value,sort:byId('news-sort').value});
  const r=await fetch('/api/news-export.csv?'+params,{credentials:'same-origin',cache:'no-store'});
  if(!r.ok || r.headers.get('X-Export-Scope')!=='loaded_read_view_not_full_database')throw new Error('Loaded sample export unavailable.');
  const blob=await r.blob();if(active!==project)return;
  const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='loaded-news-sample.csv';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  status.textContent='Loaded sample exported (up to 100 matched stories, not a full database backup).'+(r.headers.get('X-Export-Truncated')==='true' ? ' More matched loaded stories were omitted.' : '');
 }catch(error){if(active===project)status.textContent=error.message;}
});

async function readVolume(project) {
 const id=++volumeId,summary=byId('volume-summary'),details=byId('volume-details'),days=byId('volume-days');
 summary.textContent='Loading sample volume...';details.hidden=true;details.open=false;days.replaceChildren();
 try {
  const params=new URLSearchParams({project,q:byId('news-query').value,category:byId('news-category').value,country:byId('news-country').value,sort:byId('news-sort').value});
  const r=await fetch('/api/sample-volume?'+params,{credentials:'same-origin',cache:'no-store'});if(!r.ok)throw new Error('Sample volume unavailable.');const d=await r.json();
  if(active!==project || id!==volumeId)return;
  if(d.scope!=='loaded_read_view' || d.not_total_database!==true || !Array.isArray(d.daily_volume) || d.daily_volume.length!==(project==='geo'?7:14) || d.daily_volume.some(x=>!/^\d{4}-\d{2}-\d{2}$/.test(x.date) || !Number.isInteger(x.count) || x.count<0 || x.count>100))throw new Error('Sample volume unavailable.');
  const total=d.daily_volume.reduce((n,x)=>n+x.count,0),peak=d.daily_volume.reduce((a,b)=>b.count>a.count?b:a);
  summary.textContent=(total ? 'Peak day: '+peak.date+', '+peak.count+' stories (loaded sample). ' : 'No dated stories in these UTC calendar days (loaded sample). ')+d.sample_count+' distinct story URLs in the current filtered, sorted sample (up to 100'+(d.truncated?', truncated':'')+'). Missing collection time: '+d.missing_time_count+'. Future collection time excluded: '+d.future_time_count+'. Outside window: '+d.outside_window_count+'. Duplicate URLs omitted: '+d.duplicates_omitted+'. As of '+d.as_of+'. Not full database totals.';
  for(const row of d.daily_volume){const line=document.createElement('div');line.className='volume-day';const label=document.createElement('span');label.textContent=row.date+' UTC'+(row.date===d.as_of.slice(0,10)?' (partial day)':'')+': '+row.count;const meter=document.createElement('meter');meter.min=0;meter.max=Math.max(1,peak.count);meter.value=row.count;meter.setAttribute('aria-label',row.date+' UTC, '+row.count+' loaded stories');line.append(label,meter);days.append(line);}details.hidden=false;
 }catch(error){if(active===project && id===volumeId){summary.textContent=error.message;days.replaceChildren();details.hidden=true;}}
}

// News-only controls never replace, reload or change a player iframe.
// No interval/timer is enabled by this offline increment.
let criticalId = 0;
async function readCritical() {
 const id=++criticalId,status=byId('critical-status'),container=byId('critical-results');
 if(active!=='geo'){status.textContent='Critical-story policy unavailable for this view.';container.replaceChildren();return;}
 status.textContent='Loading critical stories...';container.replaceChildren();
 try {
  const r=await fetch('/api/critical-stories',{credentials:'same-origin',cache:'no-store'});
  if(!r.ok)throw new Error('Critical stories unavailable.');const d=await r.json();
  if(id!==criticalId || active!=='geo')return;
  if(d.scope!=='loaded_read_view' || d.not_total_database!==true || d.policy!=='supplied_geo_critical_risk_only' || !Array.isArray(d.items))throw new Error('Critical-story contract unavailable.');
  render(container,d.items);
  status.textContent=d.count+' critical '+(d.count===1?'story':'stories')+' in the loaded view, not database totals. As of '+String(d.as_of || '').slice(0,16).replace('T',' ')+' UTC'+'. Missing collection time: '+d.missing_time_count+'. Future times excluded: '+d.future_time_count+'.'+(d.truncated?' Showing first 100.':'')+(d.other_project_policy_unavailable_count?' Other-source critical policy unavailable.':'');
 }catch(error){if(id===criticalId && active==='geo')status.textContent=error.message;}
}
byId('news-theme').addEventListener('click',()=>{
 const dark=byId('news-view').dataset.theme!=='dark';
 byId('news-view').dataset.theme=dark?'dark':'light';
 byId('news-theme').setAttribute('aria-pressed',String(dark));
 byId('news-theme').textContent=dark?'Light news view':'Dark news view';
});
byId('news-refresh').addEventListener('click',()=>{
 if(!['geo','brics'].includes(active))return;
 readStats(active);readSignals(active);readSnapshots(active);readNews();readCritical();readSourceHealth();
});

let sourceHealthId=0;
async function readSourceHealth(){
 const id=++sourceHealthId,status=byId('source-health-status'),rows=byId('source-health-rows');
 status.textContent='Loading source observations...';rows.replaceChildren();
 try{
  const r=await fetch('/api/source-health',{credentials:'same-origin',cache:'no-store'});
  if(!r.ok)throw new Error('Source observations unavailable.');const d=await r.json();
  if(id!==sourceHealthId || active==='finder')return;
  if(d.not_live_status!==true || !Array.isArray(d.items))throw new Error('Source contract unavailable.');
  if(d.state==='source_health_unwired'){status.textContent='Source-check reader is not connected. Current health is unknown.';return;}
  if(d.state!=='supplied_snapshot' || d.scope!=='supplied_source_checks')throw new Error('Source contract unavailable.');
  status.textContent='Captured observations at '+String(d.observed_at).slice(0,16).replace('T',' ')+' UTC, '+d.age_seconds+' seconds old. Not current health.'+(d.truncated?' First 100 of '+d.total_supplied+' checks shown.':'');
  for(const item of d.items){const row=document.createElement('p');row.className='source-health-row';row.textContent=String(item.name)+' · recorded '+String(item.status)+' · fetched '+(item.count??'not recorded')+' · checked '+(item.checked_at?String(item.checked_at).slice(0,16).replace('T',' ')+' UTC':'not recorded')+(item.error_code?' · error '+String(item.error_code):'');rows.append(row);}
  if(!d.items.length){const row=document.createElement('p');row.textContent='No source checks in this supplied snapshot.';rows.append(row);}
 }catch(error){if(id===sourceHealthId && active!=='finder'){status.textContent=error.message;rows.replaceChildren();}}
}

// Geo news is the selected home; Finder remains a separate intact section.
document.querySelector('[data-view="geo"]').click();

{
/* Original Geo dashboard structure adapted to existing bounded read view.
   No polling, totals inference, new provider, writes, or original app import. */
const q=id=>document.getElementById(id);
const labels={GEOPOLITICS:'Geopolitics',CONFERENCE:'Conferences & Meetings',TRADE:'Trade Activity',SANCTIONS:'Sanctions & Circulars',RISK:'Risk Signals',RESEARCH:'Research Papers & Documents',GENERAL:'Other'};
const risks={CRITICAL:'#c53030',HIGH:'#dd6b20',MODERATE:'#d69e2e',LOW:'#718096'};
const cred={HIGH:'#2f855a',MEDIUM:'#b7791f',LOW:'#a0aec0'};
function stat(value,label){const d=document.createElement('div');d.className='stat';const n=document.createElement('div');n.className='num';n.textContent=value;const l=document.createElement('div');l.className='lbl';l.textContent=label;d.append(n,l);return d;}
function bars(title,rows){const d=document.createElement('section');d.className='card';const h=document.createElement('h3');h.textContent=title;d.append(h);const max=Math.max(1,...rows.map(x=>x[1]));for(const [name,count,color]of rows){const line=document.createElement('div');line.className='barrow';const n=document.createElement('span');n.className='name';n.textContent=name;const meter=document.createElement('meter');meter.min=0;meter.max=max;meter.value=count;meter.setAttribute('aria-label',name+': '+count+' in loaded sample');meter.style.accentColor=color;const c=document.createElement('span');c.className='cnt';c.textContent=count;line.append(n,meter,c);d.append(line);}if(!rows.length){const p=document.createElement('p');p.textContent='No recorded values in this loaded sample.';d.append(p);}return d;}
function decorate(){const root=q('news-results');for(const h of root.querySelectorAll('.geo-group'))h.remove();let previous='';for(const row of root.querySelectorAll(':scope > .story')){const badges=Array.from(row.querySelectorAll('.badge'));const cat=badges.find(x=>labels[x.textContent])?.textContent||'GENERAL';if(cat!==previous){const h=document.createElement('h3');h.className='geo-group';h.textContent=labels[cat]||cat;root.insertBefore(h,row);previous=cat;}const text=Array.from(row.querySelectorAll('.story-meta')).find(p=>p.textContent.startsWith('Risk:'))?.textContent||'';const risk=/Risk: (CRITICAL|HIGH|MODERATE|LOW)(?: |$|·)/.exec(text)?.[1];row.dataset.geoRisk=risk||'UNKNOWN';}}
let queued=false;const observer=new MutationObserver(()=>{if(queued)return;queued=true;queueMicrotask(()=>{observer.disconnect();decorate();observer.observe(q('news-results'),{childList:true,subtree:true});queued=false;});});observer.observe(q('news-results'),{childList:true,subtree:true});
let serial=0;
async function refresh(){const id=++serial;q('geo-stat-row').replaceChildren(stat('Loading','Articles in loaded view'),stat('Loading','Critical 24h, loaded'),stat('Unavailable','Upcoming events'),stat('Loading','Active loaded categories'));q('geo-bar-panels').replaceChildren();try{const rs=await Promise.all(['/api/news-stats?project=geo','/api/dashboard-signals?project=geo'].map(u=>fetch(u,{credentials:'same-origin',cache:'no-store'})));if(rs.some(r=>!r.ok))throw Error();const [stats,signals]=await Promise.all(rs.map(r=>r.json()));if(id!==serial)return;if(stats.scope!=='loaded_read_view'||stats.not_total_database!==true||signals.scope!=='loaded_read_view'||signals.not_total_database!==true)throw Error();const cats=Array.isArray(stats.categories)?stats.categories:[];q('geo-stat-row').replaceChildren(stat(Number.isInteger(stats.count)?String(stats.count):'Unknown','Articles in loaded view'),stat(Number.isInteger(signals.critical_24h_loaded)?String(signals.critical_24h_loaded):'Unknown','Critical 24h, loaded'),stat('Unavailable','Upcoming events'),stat(String(cats.length),'Active loaded categories'));
const categoryRows=cats.filter(x=>typeof x.label==='string'&&Number.isInteger(x.count)&&x.count>=0).map(x=>[labels[x.label]||x.label,x.count,'#2b6cb0']);q('geo-bar-panels').append(bars('Volume by category - loaded sample',categoryRows),bars('Risk level breakdown - recorded sample',Object.entries(risks).filter(([k])=>Number.isInteger(signals.risk_levels?.[k])&&signals.risk_levels[k]>0).map(([k,v])=>[k,signals.risk_levels[k],v])),bars('Source credibility - recorded sample',Object.entries(cred).filter(([k])=>Number.isInteger(signals.credibility_levels?.[k])&&signals.credibility_levels[k]>0).map(([k,v])=>[k,signals.credibility_levels[k],v])));
}catch{if(id===serial){q('geo-stat-row').replaceChildren(stat('Unavailable','Articles in loaded view'),stat('Unavailable','Critical 24h, loaded'),stat('Unavailable','Upcoming events'),stat('Unavailable','Active categories'));const p=document.createElement('p');p.textContent='Dashboard sample unavailable. No totals inferred.';q('geo-bar-panels').replaceChildren(p);}}}
for(const [key,label]of [['','All'],...Object.entries(labels)]){const b=document.createElement('button');b.type='button';b.className='tab';b.dataset.category=key;b.setAttribute('role','tab');b.textContent=label;b.addEventListener('click',()=>{const select=q('news-category');if(!Array.from(select.options).some(o=>o.value===key)){const o=document.createElement('option');o.value=key;o.textContent=label;select.append(o);}select.value=key;select.dispatchEvent(new Event('change',{bubbles:true}));syncTabs();});b.setAttribute('aria-selected',String(!key));if(!key)b.classList.add('active');q('geo-category-tabs').append(b);}
q('news-refresh').addEventListener('click',refresh);document.querySelector('[data-view=geo]').addEventListener('click',refresh);refresh();

function syncTabs(){for(const b of q('geo-category-tabs').children){const selected=b.dataset.category===q('news-category').value;b.classList.toggle('active',selected);b.setAttribute('aria-selected',String(selected));}}
q('geo-category-tabs').setAttribute('role','tablist');q('news-category').addEventListener('change',syncTabs);document.querySelector('[data-view=geo]').addEventListener('click',syncTabs);syncTabs();

}
