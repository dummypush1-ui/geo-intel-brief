const status=document.getElementById('status'),results=document.getElementById('results'),button=document.getElementById('read');
const exact=(o,keys)=>o&&typeof o==='object'&&!Array.isArray(o)&&Object.keys(o).sort().join('|')===[...keys].sort().join('|');
const str=(v,n)=>typeof v==='string'&&v.length<=n;
const key=v=>str(v,64)&&/^[a-f0-9]{64}$/.test(v);
button.addEventListener('click',async()=>{
 const abort=new AbortController(),timer=setTimeout(()=>abort.abort(),12000);button.disabled=true;status.textContent='Reading separate BRICS source...';
 try{
  const response=await fetch('/api/brics/news',{credentials:'same-origin',cache:'no-store',signal:abort.signal});
  if(!response.ok||!(response.headers.get('Content-Type')||'').startsWith('application/json'))throw Error();
  const reader=response.body.getReader();let chunks=[],count=0;try{while(true){const {done,value}=await reader.read();if(done)break;count+=value.byteLength;if(count>250000)throw Error();chunks.push(value);}}finally{await reader.cancel().catch(()=>{});}
  const bytes=new Uint8Array(count);let at=0;for(const v of chunks){bytes.set(v,at);at+=v.byteLength;}
  const data=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
  if(!exact(data,['state','message','scope','skipped_rows','items','critical_24h_keys','critical_time_unknown_count','source_freshness','date_policy'])||data.state!=='reviewed_brics_read'||data.scope!=='latest100_then_brics_filter_not_full_store'||data.message!=='Separate read-only BRICS source; latest up to100 stored rows, not whole-store totals.'||!Array.isArray(data.items)||data.items.length>100||!Number.isInteger(data.skipped_rows)||data.skipped_rows<0||data.skipped_rows>100||data.items.length+data.skipped_rows>100||!Array.isArray(data.critical_24h_keys)||data.critical_24h_keys.length>100||data.critical_24h_keys.some(v=>!key(v))||!Number.isInteger(data.critical_time_unknown_count)||data.critical_time_unknown_count<0||data.critical_time_unknown_count>100||!str(data.date_policy,300)||!str(data.source_freshness,200))throw Error();
  const fragment=document.createDocumentFragment(),seen=new Set();
  for(const row of data.items){
   if(!exact(row,['url','title','summary','source','country','category','published_at','collected_at','corroboration_state','corroboration_count','critical_keyword_match','brics_relevant','article_key'])||!key(row.article_key)||seen.has(row.article_key)||!str(row.title,2048)||!str(row.summary,8000)||!['source','country','category'].every(k=>str(row[k],200))||!str(row.url,2048)||!['published_at','collected_at'].every(k=>row[k]===null||str(row[k],100)&&Number.isFinite(Date.parse(row[k])))||typeof row.critical_keyword_match!=='boolean'||row.brics_relevant!==true||!['unknown, not cleared','supplied source list, not independently verified'].includes(row.corroboration_state)||!(row.corroboration_count===null||Number.isInteger(row.corroboration_count)&&row.corroboration_count>=0&&row.corroboration_count<=30))throw Error();
   const url=new URL(row.url);if(url.protocol!=='https:'||url.username||url.password||url.port&&url.port!=='443'||/[\s\\]/u.test(row.url))throw Error();seen.add(row.article_key);
   const card=document.createElement('article');card.className='story';const h=document.createElement('h2');const titleLink=document.createElement('a');titleLink.href=url.href;titleLink.textContent=row.title;titleLink.target='_blank';titleLink.rel='noopener noreferrer';h.append(titleLink);const p=document.createElement('p');p.textContent=row.summary;const note=document.createElement('p');note.textContent=[row.source,row.country,row.category,'Collected: '+(row.collected_at||'unknown'),'Corroboration: '+row.corroboration_state,data.critical_24h_keys.includes(row.article_key)?'Critical keyword match within collected24h, not a risk rating':'Not a current24h critical keyword match'].join(' | ');
   const link=document.createElement('a');link.href=url.href;link.textContent='Read source';link.target='_blank';link.rel='noopener noreferrer';card.append(h,p,note,link);fragment.append(card);
  }
  if(data.critical_24h_keys.some(k=>!seen.has(k)))throw Error();
  results.replaceChildren(fragment);status.textContent=data.skipped_rows+' unsafe rows skipped. '+data.items.length+' BRICS-relevant rows in the latest stored sample. '+data.critical_24h_keys.length+' critical keyword matches within collected24h. Not whole-store totals or proof of live collection.';
 }catch{results.replaceChildren();status.textContent='Separate BRICS source unavailable. Not a no-news result. No Geo fallback or automatic retry.';}finally{clearTimeout(timer);button.disabled=false;}
});
