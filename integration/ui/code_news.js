'use strict';
// Manual only. No storage, startup request, polling, provider or generic q path.
const $=id=>document.getElementById(id);
const states={resolved:'Code resolved.',ambiguous:'Choose an exact system and snapshot edition below.',unknown_code:'Code not found in this preserved snapshot.',not_in_link_model:'Code exists outside supported relationship lengths, or is a chapter. Not in link model.',conflicting_source_rows:'Conflicting source descriptions. No code was selected.',unusable_description:'Description unavailable for this code. No guess was made.',mixed_or_malformed_code:'Enter a code alone or keywords alone. This page does not run keyword news search.',keywords_not_code:'Use a code on this page. Keyword search remains in News.',no_evidence_in_supplied_page:'No relationship in this supplied page. This is not evidence that no related news exists.',article_unavailable_in_supplied_page:'Article is not in this supplied page.',unassigned:'No supported reported code in this supplied article.',rate_limited:'Busy. Wait before another manual request.'};
async function get(path,params){
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),12000);
 try{const r=await fetch(path+'?'+params,{credentials:'omit',cache:'no-store',redirect:'error',signal:controller.signal});const t=await r.text();if(t.length>250000)throw Error('Response too large.');return JSON.parse(t);}finally{clearTimeout(timer);}
}
function badge(box,item){
 const p=document.createElement('p');p.textContent=(item.kind==='reported_code_mention'?'Reported code mention, not verified classification':'Suggested commodity context, not verified classification')+': '+(item.evidence?.commodity_phrases?.join(', ')||item.evidence||'')+' | '+(item.resolution||'');box.append(p);
 for(const target of item.targets||[]){const label=document.createElement('p');label.textContent=target.system+' '+target.code+' | '+target.edition+' | '+(target.description||target.state||'');box.append(label);}
 if(item.article){let url;try{url=new URL(item.article.url);}catch{return;}if(!['http:','https:'].includes(url.protocol)||url.username||url.password)return;const a=document.createElement('a');a.href=url.href;a.textContent=item.article.title;a.rel='noopener noreferrer';a.target='_blank';box.append(a);const key=document.createElement('p');key.textContent='Article key: '+item.article.article_key;box.append(key);}
}
$('code-query').addEventListener('submit',async e=>{
 e.preventDefault();if(!e.isTrusted)return;const button=e.currentTarget.querySelector('button');button.disabled=true;$('code-results').replaceChildren();$('code-choices').replaceChildren();
 try{const params=new URLSearchParams({query:$('code-query-value').value});if($('code-system').value)params.set('system',$('code-system').value);if($('code-edition').value)params.set('edition',$('code-edition').value);const result=await get('/api/code-news-context',params);$('code-state').textContent=states[result.state]||result.state;
  for(const item of result.items||[]){const p=document.createElement('p');p.textContent=item.system+' '+item.code+' | '+item.edition+' | '+(item.description||item.state||'');$('code-choices').append(p);}
  for(const item of result.relationships||[])badge($('code-results'),item);
 }catch(_){$('code-state').textContent='Relationships unavailable. No automatic retry.';}finally{button.disabled=false;}
});
$('news-code-query').addEventListener('submit',async e=>{
 e.preventDefault();if(!e.isTrusted)return;const button=e.currentTarget.querySelector('button');button.disabled=true;$('article-results').replaceChildren();
 try{const result=await get('/api/news-code-context',new URLSearchParams({project:$('article-project').value,article_key:$('article-key').value}));$('article-state').textContent=states[result.state]||result.state;for(const item of result.items||[])badge($('article-results'),item);}catch(_){$('article-state').textContent='Relationships unavailable. No automatic retry.';}finally{button.disabled=false;}
});
