const status=document.getElementById('status'),results=document.getElementById('results'),button=document.getElementById('read');
button.addEventListener('click',async()=>{
 const abort=new AbortController(),timer=setTimeout(()=>abort.abort(),12000);
 button.disabled=true;results.replaceChildren();status.textContent='Checking supplied BRICS boundary...';
 try{
  const r=await fetch('/api/brics/news',{credentials:'same-origin',cache:'no-store',signal:abort.signal});
  if(!r.ok||!(r.headers.get('Content-Type')||'').startsWith('application/json'))throw Error();
  const reader=r.body.getReader();let chunks=[],count=0;try{while(true){const {done,value}=await reader.read();if(done)break;count+=value.byteLength;if(count>250000)throw Error();chunks.push(value);}}finally{await reader.cancel().catch(()=>{});}
  const bytes=new Uint8Array(count);let n=0;for(const v of chunks){bytes.set(v,n);n+=v.byteLength;}const d=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
  if(d.state==='source_not_connected'){
   if(Object.keys(d).sort().join('|')!=='message|state'||d.message!=='BRICS news source not connected. No BRICS news data supplied.')throw Error();status.textContent=d.message;return;
  }
  const fields=['state','message','scope','date_policy','critical_policy','items','relevant_count','critical_24h_keys','critical_time_unknown_count'];
  if(Object.keys(d).sort().join('|')!==fields.sort().join('|')||!Number.isInteger(d.relevant_count)||d.relevant_count<0||d.relevant_count>100||!Number.isInteger(d.critical_time_unknown_count)||d.critical_time_unknown_count<0||d.critical_time_unknown_count>100||!Array.isArray(d.critical_24h_keys)||d.critical_24h_keys.length>100||d.critical_24h_keys.some(v=>typeof v!=='string'||!/^[a-f0-9]{64}$/.test(v)))throw Error();
  if(d.state!=='supplied_fixture'||d.message!=='supplied offline fixtures, not live news'||!Array.isArray(d.items)||d.items.length>100||d.scope!=='bounded_supplied_brics_fixture_not_full_store')throw Error();
  const fragment=document.createDocumentFragment();for(const row of d.items){
   const allowed=['url','title','summary','source','country','category','published_at','collected_at','corroboration_state','corroboration_count','critical_keyword_match','brics_relevant','article_key'];
   if(Object.keys(row).sort().join('|')!==allowed.sort().join('|')||typeof row.article_key!=='string'||!/^[a-f0-9]{64}$/.test(row.article_key)||!['source','country','category','url'].every(k=>typeof row[k]==='string')||!(row.corroboration_count===null||Number.isInteger(row.corroboration_count)&&row.corroboration_count>=0&&row.corroboration_count<=30))throw Error();
   if(typeof row.title!=='string'||row.title.length>2048||typeof row.summary!=='string'||row.summary.length>8000||!['unknown, not cleared','supplied source list, not independently verified'].includes(row.corroboration_state)||typeof row.brics_relevant!=='boolean'||typeof row.critical_keyword_match!=='boolean')throw Error();
   const card=document.createElement('article');card.className='story';const h=document.createElement('h2');h.textContent=row.title;const p=document.createElement('p');p.textContent=row.summary;const note=document.createElement('p');note.textContent='Offline fixture only. Corroboration: '+row.corroboration_state+'. BRICS relevance: '+row.brics_relevant+'. Keyword match: '+row.critical_keyword_match+'. Not a Geo risk rating.';card.append(h,p,note);fragment.append(card);
  }results.replaceChildren(fragment);status.textContent=d.message+'. '+d.items.length+' supplied rows, not a full-store total.';
 }catch{results.replaceChildren();status.textContent='BRICS news boundary unavailable. Not a no-news result. No automatic retry.';}finally{clearTimeout(timer);button.disabled=false;}
});
