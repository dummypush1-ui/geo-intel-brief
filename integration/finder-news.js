/* Copyright (c) 2026 Push. Additive client bridge, not injected into finder. */
export async function relatedNews(endpoint, context, fetcher = fetch) {
  const base = new URL(endpoint, location.origin);
  if (base.origin !== location.origin) throw new Error('Private same-origin routing required');
  const response = await fetcher(base.href, {method: 'POST', credentials: 'same-origin', headers: {'Content-Type':'application/json'}, body: JSON.stringify(context)});
  if (!response.ok) return {state: response.status === 403 ? 'private' : 'unavailable', items: []};
  const data = await response.json();
  return {state:'ready', items: Array.isArray(data.items) ? data.items : []};
}
export function renderNews(container, result) {
  container.replaceChildren();
  for (const item of result.items || []) {
    const article = item.article || item;
    let url;
    try {url = new URL(article.url);} catch {continue;}
    if (!['https:','http:'].includes(url.protocol) || url.username || url.password) continue;
    const link = document.createElement('a');
    link.href = url.href; link.textContent = String(article.title || 'News');
    link.rel = 'noopener noreferrer'; link.target = '_blank';
    const row = document.createElement('p'); row.append(link); container.append(row);
  }
}
