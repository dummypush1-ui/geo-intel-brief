/* Exact public offline snapshot allowlist; no private route interception. */
const CACHE='geo-public-finder-c100d1017b7c-v1';
const BASE=new URL('./',self.location.href);
const OFFLINE=new URL('offline.html',BASE).href;
self.addEventListener('install',event=>{event.waitUntil((async()=>{const response=await fetch(OFFLINE,{cache:'no-store',credentials:'same-origin'});if(!response.ok||response.redirected||response.headers.get('X-Finder-Public-Snapshot')!=='true'||!response.headers.get('Content-Type')?.startsWith('text/html'))throw new Error('Public snapshot unavailable');const cache=await caches.open(CACHE);await cache.put(OFFLINE,response);await self.skipWaiting();})());});
self.addEventListener('activate',event=>{event.waitUntil((async()=>{for(const key of await caches.keys())if((key.startsWith('geo-public-finder-')||key.startsWith('hsn-data-'))&&key!==CACHE)await caches.delete(key);await self.clients.claim();})());});
self.addEventListener('fetch',event=>{const url=new URL(event.request.url);url.hash='';if(event.request.method!=='GET'||url.href!==OFFLINE)return;event.respondWith((async()=>{const cache=await caches.open(CACHE);const hit=await cache.match(OFFLINE);if(hit)return hit;return fetch(event.request);})());});
