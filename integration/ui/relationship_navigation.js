/* Copyright (c) 2026 Push. Manual supplied-page relationships, no providers. */
const MAX_BYTES=250000;
const identity=/^[0-9]{4}(?:[0-9]{2}){0,4}$/;
const editions={HS:'2022',IN:'snapshot:d6d1b417562b'};
const tags=['HS','IN','US','EU','UK','KR','CA','JP','AU','BR','TW','NZ','NO','SG','IL','MX','HK','ZA','PE','SAC','CN','AE'];
const append=(box,tag,text)=>{const n=document.createElement(tag);n.textContent=text;box.append(n);return n;};
const plain=(s,n)=>typeof s==='string'&&s.length<=n&&!/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/.test(s);
const keys=(v,names)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join('|')===names.slice().sort().join('|');
function target(t){
 if(!keys(t,['system','edition','code','description','state'])||!plain(t.system,3)||!tags.includes(t.system)||!plain(t.edition,100)||!plain(t.code,12)||!identity.test(t.code)||!plain(t.description,4000)||t.state!=='resolved')throw Error('Invalid identity');
 return t;
}
function article(a){
 const fields=['article_key','project','url','title','summary','source','original_country','category','published_at','collected_at','risk_level','credibility','score','corroboration_count'];
 const required=fields.filter(k=>k!=='corroboration_count');
 if(!a||Object.keys(a).length<required.length||required.some(k=>!Object.hasOwn(a,k))||Object.keys(a).some(k=>!fields.includes(k))||!plain(a.title,2048)||!plain(a.url,2048)||!plain(a.summary,8000)||!/^[a-f0-9]{64}$/.test(a.article_key)||a.project!=='geo')throw Error('Invalid article');
 for(const k of ['source','original_country','category','risk_level','credibility']){if(a[k]!==null&&!plain(a[k],200))throw Error('Invalid article field');}
 for(const k of ['published_at','collected_at']){if(a[k]!==null&&!plain(a[k],100))throw Error('Invalid date field');}
 for(const k of ['score','corroboration_count']){if(a[k]!==undefined&&a[k]!==null&&(typeof a[k]!=='number'||!Number.isFinite(a[k])))throw Error('Invalid numeric field');}
 const u=new URL(a.url);if(!['http:','https:'].includes(u.protocol)||u.username||u.password)throw Error('Invalid URL');
 return a;
}
function relationship(r,forward){
 const fields=forward?['article_key','kind','resolution','targets','evidence','legal_classification_verified','query_code','relation_scope','article']:['article_key','kind','resolution','targets','evidence','legal_classification_verified'];
 if(!keys(r,fields)||r.kind!=='reported_code_mention'||!plain(r.resolution,80)||r.legal_classification_verified!==false||!plain(r.evidence,2000)||!Array.isArray(r.targets)||r.targets.length>100||!/^[a-f0-9]{64}$/.test(r.article_key))throw Error('Invalid relationship');
 r.targets.forEach(target);if(forward){target(r.query_code);article(r.article);if(r.relation_scope!=='same_code_mention')throw Error('Invalid relation scope');}
 return r;
}
async function get(path,params,signal){
 const r=await fetch(path+'?'+new URLSearchParams(params),{signal,cache:'no-store',credentials:'same-origin',redirect:'error'});
 if(r.status===429)throw Error('Shared relationship limit: 10 manual requests per minute per process, across all visitors. Wait up to a minute and try manually.');
 if(!r.ok)throw Error(r.status===404?'This story is unavailable in the latest-100 relationship view. No conclusion about related codes.':'Relationships unavailable. Try manually later.');
 if(!/^application\/json(?:\s*;|$)/i.test(r.headers.get('content-type')||''))throw Error('Invalid response type');
 const reader=r.body.getReader();const chunks=[];let size=0;
 try{while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>MAX_BYTES)throw Error('Response too large');chunks.push(value);}}
 finally{await reader.cancel().catch(()=>{});}
 const data=new Uint8Array(size);let at=0;for(const b of chunks){data.set(b,at);at+=b.byteLength;}
 return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(data));
}
function showTargets(box,rows){
 for(const r of rows){
  append(box,'p','Reported code mention, not verified classification: '+r.evidence);
  for(const t of r.targets){
   append(box,'p',t.system+' '+t.code+' | '+t.edition+' | '+t.description);
   // Only offer a context page, never invent a Finder hash for a conflicted
   // catalogue row. The server must prove any eventual Finder destination.
  }
 }
}
const activeStories=new Set();
const cancelStories=()=>{for(const stop of activeStories)stop();activeStories.clear();};
window.addEventListener('pagehide',cancelStories);
document.addEventListener('click',e=>{if(e.target.closest('[data-view]'))cancelStories();});
export function attachReportedCodes(row,a,frame){
 if(!/^[a-f0-9]{64}$/.test(a.article_key)||a.project!=='geo')return;
 const button=append(row,'button','Check reported codes');button.type='button';
 const status=append(row,'p','Latest-100 only. Reported mentions, not verified classification.');status.setAttribute('role','status');
 const box=append(row,'div','');let generation=0,controller=null;
 const cancel=()=>{generation++;controller?.abort();button.disabled=false;};
 button.addEventListener('click',async e=>{
  if(!e.isTrusted)return;controller?.abort();activeStories.add(cancel);controller=new AbortController();const mine=++generation,own=controller;button.disabled=true;box.replaceChildren();status.textContent='Checking latest-100 reported mentions...';
  const timer=setTimeout(()=>own.abort(),12000);
  try{
   const v=await get('/api/news-code-context',{project:'geo',article_key:a.article_key},own.signal);
   if(mine!==generation||!row.isConnected)return;
   if(!keys(v,['state','items','scope','not_exhaustive','vocabulary_state','no_matches_not_no_related_news'])||!['relationships','unassigned'].includes(v.state)||v.scope!=='supplied_article_title_summary'||v.not_exhaustive!==true||v.vocabulary_state!=='draft_not_enabled'||v.no_matches_not_no_related_news!==true||!Array.isArray(v.items)||v.items.length>100)throw Error('Invalid relationship response');
   v.items.forEach(r=>{relationship(r,false);if(r.article_key!==a.article_key)throw Error('Article identity changed');});showTargets(box,v.items);
   status.textContent=v.items.length?'Latest-100 only. Reported mentions are not verified classification.':'No supported reported mention here. This does not mean no related code exists.';
  }catch(err){if(mine===generation&&row.isConnected)status.textContent=err.name==='AbortError'?'Check stopped. Try manually.':err.message;}
  finally{clearTimeout(timer);if(mine===generation){activeStories.delete(cancel);if(row.isConnected)button.disabled=false;}}
 });

}
let contextSignature='',contextGeneration=0,contextController=null;
export function resetFinderContext(){contextSignature='';contextGeneration++;contextController?.abort();}
export function manualFinderContext(frame,box,status,label){
 const clear=()=>{if(contextSignature!=='none'){contextSignature='none';contextGeneration++;contextController?.abort();box.replaceChildren();label.textContent='';status.textContent='Select a supported HS or India code. Latest-100 only; no private lookup.';}};
 let code,system;
 try{
  if(frame.contentWindow.location.origin!==location.origin||new URL(frame.src).pathname!=='/workspace/finder/offline.html'){clear();return;}
  const doc=frame.contentDocument,hash=frame.contentWindow.location.hash.match(/^#code=(\d+):([0-9]{4}(?:[0-9]{2}){0,4})$/);
  code=doc.querySelector('.detail-code')?.textContent.trim();system=doc.querySelector('.detail-head .sys-tag')?.textContent.trim();
  if(!hash||!identity.test(code)||code!==hash[2]||tags[Number(hash[1])]!==system||!editions[system]){clear();return;}
 }catch{clear();return;}
 const sig=system+':'+code;if(sig===contextSignature)return;contextSignature=sig;contextGeneration++;contextController?.abort();box.replaceChildren();label.textContent=system+' '+code;
 status.textContent='Latest-100 only. No automatic check. Reported mentions are not classification.';
 const button=append(box,'button','Check supplied-page news');button.type='button';const results=append(box,'div','');
 button.addEventListener('click',async e=>{
  if(!e.isTrusted)return;contextController?.abort();contextController=new AbortController();const mine=++contextGeneration,own=contextController;button.disabled=true;results.replaceChildren();status.textContent='Checking latest-100 reported mentions...';const timer=setTimeout(()=>own.abort(),12000);
  try{
   const v=await get('/api/code-news-context',{query:code,system,edition:editions[system]},own.signal);
   if(mine!==contextGeneration||!button.isConnected)return;
   if(!['relationships','no_evidence_in_supplied_page'].includes(v.state))throw Error('Identity unavailable or ambiguous. No related-news conclusion.');
   if(!keys(v,['state','items','relationships','scope','not_full_store_search','vocabulary_state','no_matches_not_no_related_news'])||v.scope!=='latest100_supplied_page_only'||v.not_full_store_search!==true||v.vocabulary_state!=='draft_not_enabled'||v.no_matches_not_no_related_news!==true||!Array.isArray(v.items)||v.items.length!==1||!Array.isArray(v.relationships)||v.relationships.length>100)throw Error('Invalid relationship response');
   const t=target(v.items[0]);if(t.code!==code||t.system!==system||t.edition!==editions[system])throw Error('Identity changed');
   v.relationships.forEach(r=>{relationship(r,true);if(r.query_code.code!==code||r.query_code.system!==system||r.query_code.edition!==editions[system]||r.article.article_key!==r.article_key)throw Error('Relationship identity changed');});
   for(const r of v.relationships){const a=append(results,'a',r.article.title);a.href=r.article.url;a.target='_blank';a.rel='noopener noreferrer';append(results,'p','Reported code mention, not verified classification: '+r.evidence);}
   status.textContent=v.relationships.length?'Latest-100 reported mentions. Not full-store or meaning-based search.':'No reported-code match in latest-100. Not proof no related news exists.';
  }catch(err){if(mine===contextGeneration&&button.isConnected)status.textContent=err.name==='AbortError'?'Check stopped. Try manually.':err.message;}
  finally{clearTimeout(timer);if(mine===contextGeneration&&button.isConnected)button.disabled=false;}
 });
}
window.addEventListener('pagehide',()=>{contextGeneration++;contextController?.abort();});

document.addEventListener('click',e=>{if(e.target.closest('[data-view]')){contextSignature='';contextGeneration++;contextController?.abort();}});
