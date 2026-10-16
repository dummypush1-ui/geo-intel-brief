/*F10_CONFIG*/
'use strict';
const status=document.getElementById('status'),save=document.getElementById('save'),clear=document.getElementById('clear');
const scope=new URL(CFG.base,location.origin).href,scriptURL=new URL(CFG.base+'worker.js',location.origin).href;
let busy=false;
async function action(run){if(busy)return;busy=true;save.disabled=clear.disabled=true;try{await run();}catch(error){status.textContent='Snapshot storage unavailable: '+error.message;}finally{busy=false;save.disabled=clear.disabled=false;}}
save.onclick=()=>action(async()=>{
 if(!('serviceWorker'in navigator)||!isSecureContext)throw new Error('A secure supported browser is required');
 const registration=await navigator.serviceWorker.register(scriptURL,{scope,updateViaCache:'none'});
 if(registration.scope!==scope)throw new Error('Worker scope mismatch');
 const worker=registration.installing||registration.waiting||registration.active;
 if(!worker||worker.scriptURL!==scriptURL)throw new Error('Worker identity mismatch');
 if(worker.state!=='activated')await new Promise((resolve,reject)=>{const changed=()=>{if(worker.state==='activated'){worker.removeEventListener('statechange',changed);resolve();}else if(worker.state==='redundant'){worker.removeEventListener('statechange',changed);reject(new Error('Snapshot verification or install failed'));}};worker.addEventListener('statechange',changed);changed();});
 const cache=await caches.open(CFG.cache);const stored=await cache.match(new URL(CFG.base+'snapshot.html',location.origin).href);
 if(!stored||stored.headers.get('X-Finder-Device-Snapshot')!==CFG.digest)throw new Error('Stored snapshot not confirmed');
 const raw=await stored.arrayBuffer();
 if(raw.byteLength!==CFG.size)throw new Error('Stored snapshot length mismatch');
 const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw))).map(x=>x.toString(16).padStart(2,'0')).join('');
 if(digest!==CFG.digest)throw new Error('Stored snapshot digest mismatch');
 status.textContent='This public snapshot is saved. Browser storage may still be evicted.';
});
clear.onclick=()=>action(async()=>{
 for(const registration of await navigator.serviceWorker.getRegistrations()){
  if(registration.scope!==scope)continue;
  const workers=[registration.active,registration.waiting,registration.installing].filter(Boolean);
  if(workers.some(worker=>worker.scriptURL!==scriptURL))throw new Error('Different worker at this scope; nothing cleared');
  if(!await registration.unregister())throw new Error('Worker removal not confirmed');
 }
 await caches.delete(CFG.cache);
 if((await navigator.serviceWorker.getRegistrations()).some(reg=>reg.scope===scope)||(await caches.keys()).includes(CFG.cache))throw new Error('Removal not confirmed');
 status.textContent='This snapshot was cleared. Other editions, keys and notes were not changed. Close existing snapshot tabs to release their worker.';
});
