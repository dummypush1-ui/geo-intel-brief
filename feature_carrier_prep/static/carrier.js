'use strict';
function add(parent, tag, value, cls) {const el=document.createElement(tag);el.textContent=value;if(cls)el.className=cls;parent.appendChild(el);return el;}
async function load(kind, target, draw) {
 const box=document.getElementById(target);const response=await fetch('/carrier-preview/api/'+kind,{credentials:'same-origin',cache:'no-store'});
 if(!response.ok)throw new Error('Supplied fixture unavailable');const data=await response.json();
 if(data.items.length===0){add(box,'p','No supplied evidence.');return;}
 for(const row of data.items){const item=add(box,'div','','item');draw(item,row);}
}
(async()=>{try{
 await load('carriers','carrier-items',(el,r)=>{add(el,'strong',r.name);add(el,'p',r.carrier_id);add(el,'span',r.state,'badge');});
 await load('routes','route-items',(el,r)=>{add(el,'strong',r.service);for(const leg of r.legs){add(el,'p',leg.origin+' to '+leg.destination);add(el,'p',leg.departure_at+' / '+leg.arrival_at);add(el,'span',leg.classifier,'badge');}add(el,'p','Evidence state: '+r.state);});
 await load('events','event-items',(el,r)=>{add(el,'strong',r.category+' / '+r.code);add(el,'p',r.event_at);add(el,'span',r.classifier,'badge');add(el,'p','Source recorded '+r.source_recorded_at+'; revision '+r.revision+(r.cancelled?'; cancelled':''));});
 await load('context','context-items',(el,r)=>{add(el,'strong',r.title);add(el,'p',r.matched_aliases.join(', '));add(el,'p','Exact phrase context only; not shipment verification.');});
 await load('sources','source-items',(el,r)=>{add(el,'strong',r.publisher);add(el,'p',r.release+' / '+r.scope);add(el,'p','Observed '+r.observed_at);add(el,'span',r.state,'badge');});
 document.getElementById('status').textContent='Supplied fixture view loaded. Not live.';
 }catch(error){document.getElementById('status').textContent='Unavailable. Private access or supplied reader required.';}})();
