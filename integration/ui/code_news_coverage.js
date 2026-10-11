'use strict';
// Dormant D3a fixture transport. POST endpoint not registered by this unit.
(()=>{
 const $=id=>document.getElementById(id),root=document.querySelector('main');
 const available=root.dataset.coverageAvailable==='true',CAP=524288,TOKEN=/^[A-Za-z0-9_-]{43}$/;
 let generation=0,controller=null,target=null,nextRequest=null,retryRequest=null;
 const plain=(s,cap)=>typeof s==='string'&&s.length<=cap&&!/[\x00-\x08\x0b-\x1f]/.test(s);
 const identity=p=>p&&['system','edition','code'].every(k=>typeof p[k]==='string')&&/^[A-Z]{2,3}$/.test(p.system)&&/^[A-Za-z0-9:_.-]{1,100}$/.test(p.edition)&&/^[0-9]{2,12}$/.test(p.code);
 const equal=(a,b)=>['system','edition','code'].every(k=>a[k]===b[k]);
 function node(tag,text){const n=document.createElement(tag);n.textContent=text;return n;}
 function buttons(){ $('start').disabled=!available;$('next').disabled=!available||!nextRequest||!!controller;$('retry').disabled=!available||!retryRequest||!!controller; }
 function reset(message='No scan requested. Start manually when needed.'){
  generation++;controller?.abort();controller=null;target=null;nextRequest=null;retryRequest=null;
  $('coverage-items').replaceChildren();$('coverage-summary').replaceChildren();$('coverage-summary').hidden=true;root.dataset.state='idle';$('state-heading').textContent='No scan requested';$('status').textContent=available?message:'Coverage unavailable. Your selected identity is unchanged.';buttons();
 }
 function readIdentity(){return {system:$('system').value,edition:$('edition').value,code:$('code').value};}
 function prefill(){
  const p=new URLSearchParams(location.search),keys=[...p.keys()];
  if(!keys.length)return;
  if(keys.length!==3||new Set(keys).size!==3||keys.some(k=>!['system','edition','code'].includes(k)))return;
  const value=Object.fromEntries(p);if(!identity(value))return;
  for(const k of ['system','edition','code'])$(k).value=value[k];$('prefill').textContent='Prefilled identity is unverified until resolved. Start manually.';
 }
 async function stream(response){
  if(!response.headers.get('content-type')?.startsWith('application/json')||!response.body)throw Error('invalid');
  const reader=response.body.getReader(),chunks=[];let length=0;
  try{while(true){const r=await reader.read();if(r.done)break;length+=r.value.byteLength;if(length>CAP){await reader.cancel();throw Error('large');}chunks.push(r.value);}}
  finally{reader.releaseLock();}
  const data=new Uint8Array(length);let at=0;for(const part of chunks){data.set(part,at);at+=part.byteLength;}
  try{return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(data));}catch(_){throw Error('invalid');}
 }
 function validate(r,started){
  if(!r||!['continue_scan','complete_mutable_read','budget_stopped_incomplete'].includes(r.state)||r.evidence_complete!==false||r.consistency!=='mutable_read_not_snapshot'||r.evidence_scope!=='bounded_explicit_mentions_only_not_all_commodity_news'||r.total_count!==null||typeof r.coverage_gap!=='boolean')throw Error('invalid');
  const complete=r.state==='complete_mutable_read';if(r.scan_complete!==complete)throw Error('invalid');
  if(!/^[a-f0-9]{64}$/.test(r.manifest)||!/^[A-Za-z0-9_.-]{1,40}$/.test(r.matcher_version)||r.scope!==r.next_cursor||(r.state==='continue_scan'?!TOKEN.test(r.next_cursor):r.next_cursor!==null))throw Error('invalid');
  for(const k of ['articles_checked','articles_refused_mentions_limit','articles_unreadable','articles_checked_this_page','articles_refused_this_page','articles_unreadable_this_page','rows_consumed_this_page','parent_pages','public_rows_received'])if(!Number.isSafeInteger(r[k])||r[k]<0)throw Error('invalid');
  if(r.articles_checked+r.articles_refused_mentions_limit+r.articles_unreadable>r.public_rows_received||r.rows_consumed_this_page>100||r.parent_pages<1||r.parent_pages>20||r.public_rows_received>2000||r.articles_checked_this_page+r.articles_refused_this_page+r.articles_unreadable_this_page!==r.rows_consumed_this_page||r.articles_checked<r.articles_checked_this_page||r.articles_refused_mentions_limit<r.articles_refused_this_page||r.articles_unreadable<r.articles_unreadable_this_page||r.coverage_gap!==(r.articles_refused_mentions_limit+r.articles_unreadable>0)||!plain(r.coverage_message,300))throw Error('invalid');
  if(!Array.isArray(r.items)||r.items.length>25)throw Error('invalid');
  for(const item of r.items){if(!plain(item.article_key,100)||!item.article_key||!Array.isArray(item.relationships)||!item.relationships.length||item.relationships.length>32)throw Error('invalid');
   for(const link of item.relationships)if(link.article_key!==item.article_key||link.kind!=='reported_code_mention'||link.legal_classification_verified!==false||!identity(link.target)||!equal(link.target,started)||!plain(link.target.description,4000)||!link.target.description||!plain(link.evidence,18001))throw Error('invalid');
  }
  return r;
 }
 function render(r){
  $('availability').textContent='Manual coverage fixture available';
  const summary=document.createDocumentFragment(),batch=document.createDocumentFragment();
  summary.append(node('p','Evidence complete: false. This is not a full search of commodity news.'),node('p','Checked: '+r.articles_checked+' | Mention-limit refusals: '+r.articles_refused_mentions_limit+' | Unreadable: '+r.articles_unreadable),node('p','Consumed this batch: '+r.rows_consumed_this_page+' | Parent pages: '+r.parent_pages),node('p',(r.coverage_gap?'Coverage gap: ':'Coverage report: ')+r.coverage_message));
  for(const item of r.items){const article=node('article','');article.className='article';article.append(node('h3','Article key: '+item.article_key));for(const link of item.relationships){article.append(node('p',link.target.system+' '+link.target.code+' | '+link.target.edition+' | '+link.target.description));const evidence=node('p',link.evidence);evidence.className='evidence';article.append(evidence);}batch.append(article);}
  if(!r.items.length)batch.append(node('p','No supported mentions in this batch. This does not establish that no related news exists.'));
  $('coverage-summary').replaceChildren(summary);$('coverage-summary').className='summary';$('coverage-summary').hidden=false;$('coverage-items').replaceChildren(batch);root.dataset.state=r.state;
  $('state-heading').textContent=r.state==='complete_mutable_read'?'End of the scanned page stream (mutable read, not a snapshot)':r.state==='budget_stopped_incomplete'?'Page budget reached - scan is incomplete':'More of the scanned page stream remains';
  $('status').textContent='Only this batch is shown. Not verified classification or duty advice.';
  nextRequest=r.next_cursor?JSON.stringify({scope:r.next_cursor,manifest:r.manifest,matcher_version:r.matcher_version}):null;retryRequest=null;
 }
 async function send(body,started){
  generation++;const id=generation;controller?.abort();const current=new AbortController();controller=current;target=started;retryRequest=null;buttons();$('status').textContent='Checking reported code mentions...';
  const timer=setTimeout(()=>current.abort(),7000);
  try{
   const response=await fetch('/api/code-news-coverage',{method:'POST',body,headers:{'Content-Type':'application/json'},credentials:'omit',redirect:'error',cache:'no-store',signal:current.signal});
   if(id!==generation)return;
   if(response.status===429)throw Error('busy');if(response.status===410)throw Error('expired');if(response.status===403)throw Error('refused');if(!response.ok)throw Error('unavailable');
   const r=await stream(response);if(id!==generation)return;
   if(r.state==='target_unavailable'){
    if(!globalThis.CODE_NEWS_RESOLUTIONS.includes(r.resolution))throw Error('invalid');
    $('coverage-items').replaceChildren();$('coverage-summary').hidden=true;nextRequest=null;retryRequest=null;root.dataset.state='idle';$('state-heading').textContent='Identity unresolved';$('status').textContent='No identity selected: '+r.resolution+'. Review the system and snapshot edition manually.';return;
   }
   const sent=JSON.parse(body);if(sent.scope&&(r.manifest!==sent.manifest||r.matcher_version!==sent.matcher_version))throw Error('invalid');
   validate(r,started);render(r);
  }catch(error){
   if(id!==generation)return;
   $('availability').textContent=error.message==='refused'?'Coverage request refused':error.message==='busy'?'Code scans busy':'Coverage unavailable';
   root.dataset.state='error';$('state-heading').textContent='Scan request not completed';
   const continuation=Object.hasOwn(JSON.parse(body),'scope');
   if(error.message==='expired'){nextRequest=null;retryRequest=null;$('coverage-items').replaceChildren();$('coverage-summary').hidden=true;$('status').textContent='Scan expired. Start again manually; your selected identity is unchanged.';}
   else if(error.message==='busy'){retryRequest=body;$('status').textContent='Code scans are busy. Wait, then retry the same request manually.';}
   else if(error.message==='large'||error.message==='invalid'||error instanceof SyntaxError){nextRequest=null;retryRequest=null;$('coverage-items').replaceChildren();$('coverage-summary').hidden=true;$('status').textContent=error.message==='large'?'Response too large. No batch was rendered.':'Invalid response. No batch was rendered.';}
   else{retryRequest=continuation?body:null;$('status').textContent=error.message==='refused'?'Coverage request refused. Your selected identity is unchanged.':continuation?'Coverage unavailable. Retry the same request manually; no automatic retry.':'First response unavailable. Restart manually; an earlier reservation may remain for 120 seconds idle, up to 30 minutes total.';}
  }finally{clearTimeout(timer);if(id===generation){controller=null;buttons();}}
 }
 $('coverage-start').addEventListener('submit',e=>{e.preventDefault();if(!e.isTrusted||!available)return;const started=readIdentity();reset();if(!identity(started)){$('status').textContent='Enter an exact system tag, snapshot edition and numeric code.';return;}send(JSON.stringify(started),started);});
 $('next').addEventListener('click',e=>{if(e.isTrusted&&available&&nextRequest&&!controller)send(nextRequest,target);});
 $('retry').addEventListener('click',e=>{if(e.isTrusted&&available&&retryRequest&&!controller)send(retryRequest,target);});
 for(const k of ['system','edition','code'])$(k).addEventListener('input',()=>reset('Identity changed. Start a new manual scan.'));
 document.addEventListener('visibilitychange',()=>{if(document.hidden)reset();});
 window.addEventListener('pagehide',()=>reset());window.addEventListener('pageshow',()=>reset());
 prefill();reset();if(available)$('availability').textContent='Manual coverage fixture available';
})();
