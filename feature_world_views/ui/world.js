// Copyright (c) 2026 Push. All rights reserved.
const status = document.getElementById('status');
const results = document.getElementById('results');
const refresh = document.getElementById('refresh');
function node(tag, text, cls) {
  const el = document.createElement(tag); el.textContent = text;
  if (cls) el.className = cls; return el;
}
const form = document.getElementById('filters');
function params() { return new URLSearchParams(new FormData(form)); }
function render(data) {
  document.getElementById('export').hidden = false;
  document.getElementById('export').href = '/workspace/world/export.csv?' + new URLSearchParams(data.filters);
  for (const [name, key] of [['country', 'original_country'], ['category', 'category'], ['project', 'project']]) {
    const select = form.elements.namedItem(name); const selected = select.value;
    while (select.options.length > 1) select.remove(1);
    for (const value of data.options[key]) select.append(new Option(value, value));
    if (selected && !data.options[key].includes(selected)) select.append(new Option(selected, selected));
    select.value = selected;
  }
  results.replaceChildren();
  for (const row of data.items) {
    const card = node('article', '', 'story');
    const grid = node('div', '', 'story-grid');
    const news = node('div', '');
    news.append(node('p', `${row.project === 'geo' ? 'Geo news' : 'BRICS news'} · ${row.original_country || 'Country not supplied'} · ${row.category}`, 'meta'));
    const title = node('h3', ''); const link = node('a', row.title);
    let url = null; try { url = new URL(row.url); } catch (_) { /* Bad row link stays text. */ }
    if (url && ['http:', 'https:'].includes(url.protocol) && !url.username && !url.password) {
      link.href = url.href; link.target = '_blank'; link.rel = 'noopener noreferrer';
    }
    title.append(link); news.append(title, node('p', row.summary));
    news.append(node('p', `${row.source || 'Source not supplied'} · Collected: ${row.collected_at || 'Not supplied'}`, 'meta'));
    const trade = node('section', '', 'trade'); trade.append(node('h4', 'Trade context'));
    for (const match of row.trade_context) trade.append(node('span', `${match.system} ${match.code}`, 'code'), node('p', match.system_name, 'context-note'));
    trade.append(node('p', row.trade_context.length ? 'Explicit code mention. Bundled snapshot only; tariff rate not verified.' : 'No verified exact-code match supplied. No product-to-code guess.', 'context-note'));
    const drill = node('button', 'Story detail'); drill.type = 'button';
    drill.addEventListener('click', () => openDetail(row.article_key, drill));
    news.append(drill); grid.append(news, trade); card.append(grid); results.append(card);
  }
  status.textContent = `${data.count} matching stories of ${data.supplied_count} supplied. ${data.trade_state === 'not_supplied' ? 'Trade index not supplied.' : 'Exact-code trade context available.'} ${data.truncated ? 'Input truncated to 100 per project. ' : ''}Not database totals.`;
}
let detailOpener = null;
const detailPanel = document.getElementById('detail');
const detailBody = document.getElementById('detail-body');
let detailRequest = 0;
async function openDetail(key, opener) {
  const ticket = ++detailRequest; detailOpener = opener;
  detailPanel.hidden = false; detailBody.replaceChildren(node('p', 'Loading story detail...'));
  document.getElementById('close-detail').focus();
  try {
    const response = await fetch('/workspace/world/article/' + encodeURIComponent(key), {cache: 'no-store', credentials: 'same-origin'});
    if (!response.ok) throw new Error('Unavailable');
    const data = await response.json(); if (ticket !== detailRequest) return;
    detailBody.replaceChildren(node('h3', data.item.title), node('p', data.item.summary), node('p', 'Trade evidence: explicit code mentions only. Tariff rate not verified.'));
    detailBody.append(node('p', 'Collected: ' + (data.evidence.collected_at || 'Not supplied')));
    detailBody.append(node('h3', 'Other supplied stories'));
    if (!data.related.length) detailBody.append(node('p', 'No matching stories in this supplied snapshot.'));
    for (const item of data.related) {
      const button = node('button', item.title + ' (' + item.basis.replaceAll('_', ' ') + ')');
      button.type = 'button'; button.addEventListener('click', () => openDetail(item.article_key, opener));
      detailBody.append(button);
    }
    detailPanel.scrollIntoView({block: 'start'});
  } catch (_) { if (ticket === detailRequest) detailBody.replaceChildren(node('p', 'Story detail unavailable or no longer in supplied snapshot.')); }
}
document.getElementById('close-detail').addEventListener('click', () => {
  detailRequest++; detailPanel.hidden = true; if (detailOpener?.isConnected) detailOpener.focus();
});
let loadRequest = 0;
async function load() {
  const ticket = ++loadRequest; document.getElementById('export').hidden = true;
  detailRequest++; detailPanel.hidden = true;
  refresh.disabled = true; status.textContent = 'Loading supplied view...'; results.replaceChildren();
  try {
    const response = await fetch('/workspace/world/data?' + params(), {cache: 'no-store', credentials: 'same-origin'});
    if (!response.ok) throw new Error('Unavailable');
    const data = await response.json(); if (ticket !== loadRequest) return; render(data);
  } catch (_) { if (ticket !== loadRequest) return; results.replaceChildren(); status.textContent = 'World view unavailable. No current data shown. Try refresh.'; }
  finally { if (ticket === loadRequest) refresh.disabled = false; }
}
form.addEventListener('submit', event => { event.preventDefault(); load(); });
document.getElementById('reset').addEventListener('click', () => {for (const name of ['country','category','project','q','code']) form.elements.namedItem(name).value = ''; load();});
refresh.addEventListener('click', load);
load();
