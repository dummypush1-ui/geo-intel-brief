/* Copyright (c) 2026 Push. No key or live endpoint in this client. */
const byId = id => document.getElementById(id);
let active = 'finder', relatedId = 0, newsId = 0, lastContext = '';
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
    const summary = document.createElement('p'); summary.textContent = String(article.summary || ''); row.append(summary);
    for (const label of [article.project === 'geo' ? 'Geo' : 'BRICS', article.category, ...(item.match?.reasons || []).map(r => r.type === 'explicit_code' ? 'Explicit code mention, unverified' : r.type === 'country_context' ? 'Country context' : 'Product mention')]) {
      if (!label) continue; const badge = document.createElement('span'); badge.className = 'badge'; badge.textContent = label; row.append(badge);
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
    const params = new URLSearchParams({q:byId('news-query').value,project});
    const items = await request('/api/news?' + params);
    if (id !== newsId) return;
    render(byId('news-results'), items); byId('news-status').textContent = items.length ? `${items.length} ${items.length === 1 ? 'story' : 'stories'} shown.` : 'No stories in this view.';
  } catch (error) { if (id === newsId) byId('news-status').textContent = error.message; }
}
for (const button of document.querySelectorAll('[data-view]')) button.addEventListener('click', () => {
  active = button.dataset.view;
  for (const other of document.querySelectorAll('[data-view]')) other.setAttribute('aria-pressed',String(other === button));
  byId('finder-view').hidden = active !== 'finder'; byId('news-view').hidden = active === 'finder';
  if (active !== 'finder') {byId('news-heading').textContent = active === 'geo' ? 'Geo news' : 'BRICS news'; readNews();}
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
  } catch(error) {if (id === relatedId) byId('related-status').textContent = error.message;}
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
  } catch(error) {if (id === relatedId) byId('related-status').textContent = error.message;}
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
