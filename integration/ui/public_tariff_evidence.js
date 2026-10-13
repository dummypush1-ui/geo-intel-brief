/* Manual supplied-document display. No timers/retry/providers/storage. */
const $=id=>document.getElementById(id),MAX=250000;
const hosts={IN:['www.cbic.gov.in','cbic.gov.in','www.indiabudget.gov.in'],US:['www.usitc.gov','hts.usitc.gov','www.federalregister.gov'],EU:['eur-lex.europa.eu','taxation-customs.ec.europa.eu','ec.europa.eu']};
const exact=(v,n)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join('|')===n.slice().sort().join('|');
const plain=(v,n)=>typeof v==='string'&&v.length<=n&&!/[\u0000-\u001f\u007f\ud800-\udfff]/.test(v);
const add=(box,tag,text)=>{const el=document.createElement(tag);el.textContent=text;box.append(el);return el;};
const date=v=>plain(v,10)&&/^\d{4}-\d{2}-\d{2}$/.test(v)&&new Date(v+'T00:00:00Z').toISOString().slice(0,10)===v;
function source(r){if(!plain(r.source_url,1000)||/[\s\\%]/.test(r.source_url))throw Error('Invalid source');const u=new URL(r.source_url);if(u.protocol!=='https:'||!hosts[r.jurisdiction]?.includes(u.hostname)||u.username||u.password||u.hash||u.port&&u.port!=='443')throw Error('Invalid source');return u.href;}
function row(r){
 if(!exact(r,['id','jurisdiction','nomenclature','edition','codes','document_id','source_url','published_date','effective_dates','excerpt','conditions','review_state','reviewed_at']))throw Error('Invalid evidence');
 for(const [k,n]of [['id',100],['nomenclature',80],['edition',100],['document_id',200],['excerpt',2000],['conditions',1000]])if(!plain(r[k],n)||!r[k].trim())throw Error('Invalid evidence');
 if(!['IN','US','EU'].includes(r.jurisdiction)||!['candidate','document_reviewed'].includes(r.review_state)||!date(r.published_date)||!Array.isArray(r.codes)||r.codes.length>100||r.codes.some(c=>!plain(c,12)||!/^\d{2,12}$/.test(c))||new Set(r.codes).size!==r.codes.length||!Array.isArray(r.effective_dates)||r.effective_dates.length>20||r.effective_dates.some(d=>!date(d)))throw Error('Invalid evidence');
 if(r.review_state==='candidate'?r.reviewed_at!==null:!plain(r.reviewed_at,64)||!Number.isFinite(Date.parse(r.reviewed_at)))throw Error('Invalid review');source(r);return r;
}
let sequence=0,controller=null;
$('tariff-form').addEventListener('submit',async e=>{
 e.preventDefault();if(!e.isTrusted)return;controller?.abort();controller=new AbortController();const own=controller,mine=++sequence,button=e.target.querySelector('button');button.disabled=true;const timer=setTimeout(()=>own.abort(),12000);$('tariff-items').replaceChildren();$('tariff-status').textContent='Checking supplied evidence...';
 try{
  const r=await fetch('/api/tariff-evidence?'+new URLSearchParams({jurisdiction:$('tariff-jurisdiction').value}),{signal:own.signal,cache:'no-store',credentials:'same-origin',redirect:'error'});
  if(r.status===429)throw Error('Shared limit: 10 manual starts per rolling minute per process, across all visitors. Try manually later.');
  if(!r.ok)throw Error('Evidence unavailable: no conclusion about tariffs.');if(!/^application\/json(?:\s*;|$)/i.test(r.headers.get('content-type')||''))throw Error('Invalid evidence response');
  const reader=r.body.getReader(),chunks=[];let bytes=0;
  try{while(true){const {done,value}=await reader.read();if(done)break;bytes+=value.byteLength;if(bytes>MAX)throw Error('Evidence response too large');chunks.push(value);}}finally{await reader.cancel().catch(()=>{});}
  const raw=new Uint8Array(bytes);let at=0;for(const c of chunks){raw.set(c,at);at+=c.byteLength;}const v=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw));if(mine!==sequence)return;
  if(v.state==='evidence_source_not_connected'){
   if(!exact(v,['state','message','current_rates_verified','legal_effect_independently_verified','network','polling'])||v.message!=='Evidence source not connected: no conclusion about tariffs.'||[v.current_rates_verified,v.legal_effect_independently_verified,v.network,v.polling].some(x=>x!==false))throw Error('Invalid evidence response');$('tariff-status').textContent=v.message;return;
  }
  if(!exact(v,['state','observed_at','age_seconds','items','total_supplied','truncated','limit','scope','current_rates_verified','legal_effect_independently_verified','network','delivery','polling'])||v.state!=='supplied_document_evidence'||v.scope!=='supplied_evidence_not_complete_tariff_history'||[v.current_rates_verified,v.legal_effect_independently_verified,v.network,v.delivery,v.polling].some(x=>x!==false)||!plain(v.observed_at,64)||!Number.isFinite(Date.parse(v.observed_at))||!Number.isInteger(v.age_seconds)||v.age_seconds<0||!Number.isInteger(v.total_supplied)||v.total_supplied<0||v.total_supplied>1000||v.limit!==100||typeof v.truncated!=='boolean'||!Array.isArray(v.items)||v.items.length>100)throw Error('Invalid evidence response');
  v.items.forEach(row);if(v.items.length!==Math.min(v.total_supplied,100)||v.truncated!==(v.total_supplied>100)||v.items.some(r=>r.reviewed_at&&Date.parse(r.reviewed_at)>Date.parse(v.observed_at)))throw Error('Invalid evidence response');$('tariff-status').textContent='Supplied document capture: '+v.observed_at+'. Not current rates, verified legal effect or complete tariff history.';
  if(!v.items.length)add($('tariff-items'),'p','No supplied document for this jurisdiction. No conclusion about tariffs.');
  for(const r of v.items){const box=add($('tariff-items'),'article','');box.className='story';add(box,'h2',r.document_id);add(box,'p',r.jurisdiction+' | '+r.nomenclature+' | '+r.edition);add(box,'p','Review: '+r.review_state+'. Current rates and legal effect are not verified.');add(box,'p','Published: '+r.published_date+'. Supplied effective dates: '+(r.effective_dates.join(', ')||'not supplied')+'.');add(box,'p','Codes as supplied: '+(r.codes.join(', ')||'not supplied')+'. No Finder jurisdiction is inferred.');add(box,'p','Excerpt: '+r.excerpt);add(box,'p','Conditions: '+r.conditions);const a=add(box,'a','Review supplied source document');a.href=source(r);a.target='_blank';a.rel='noopener noreferrer';}
 }catch(err){if(mine===sequence)$('tariff-status').textContent=err.name==='AbortError'?'Check stopped: no conclusion about tariffs.':err.message;}
 finally{clearTimeout(timer);if(mine===sequence)button.disabled=false;}
});
window.addEventListener('pagehide',()=>{sequence++;controller?.abort();});
