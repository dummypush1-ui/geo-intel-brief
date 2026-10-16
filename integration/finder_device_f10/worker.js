/*F10_CONFIG*/
'use strict';
const SNAPSHOT=new URL(CFG.base+'snapshot.html',self.location.origin).href;
async function verified(response){
 if(!response.ok||response.status!==200||response.redirected||response.type==='opaque'||response.headers.get('X-Finder-Device-Snapshot')!==CFG.digest||!response.headers.get('Content-Type')?.startsWith('text/html'))throw new Error('Snapshot response refused');
 const reader=response.body.getReader(),chunks=[];let size=0;
 try{for(;;){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>CFG.size)throw new Error('Snapshot size refused');chunks.push(value);}}
 catch(error){await reader.cancel();throw error;}
 finally{reader.releaseLock();}
 if(size!==CFG.size)throw new Error('Snapshot length refused');
 const raw=new Uint8Array(size);let at=0;for(const chunk of chunks){raw.set(chunk,at);at+=chunk.byteLength;}
 const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw))).map(x=>x.toString(16).padStart(2,'0')).join('');
 if(digest!==CFG.digest)throw new Error('Snapshot digest refused');
 return new Response(raw,{status:200,headers:response.headers});
}
self.addEventListener('install',event=>event.waitUntil((async()=>{
 // No cache is opened or replaced until the whole selected response verifies.
 const response=await verified(await fetch(SNAPSHOT,{cache:'no-store',credentials:'omit',redirect:'error'}));
 const cache=await caches.open(CFG.cache);await cache.put(SNAPSHOT,response);await self.skipWaiting();
})()));
self.addEventListener('activate',event=>event.waitUntil(self.clients.claim()));
self.addEventListener('fetch',event=>{
 const url=new URL(event.request.url);url.hash='';
 if(event.request.method!=='GET'||url.href!==SNAPSHOT)return;
 event.respondWith((async()=>{const cache=await caches.open(CFG.cache);const hit=await cache.match(SNAPSHOT);if(hit)return verified(hit);return verified(await fetch(event.request));})());
});
