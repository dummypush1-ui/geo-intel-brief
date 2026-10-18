// Supplied ship response presentation only. No requests, timers or activation.
export const PORT_OPTIONS226=Object.freeze([["INNSA", "Nhava Sheva (JNPT)"], ["INBOM", "Mumbai"], ["INMUN", "Mundra"], ["INIXY", "Kandla (Deendayal)"], ["INMAA", "Chennai"], ["INENR", "Kamarajar (Ennore)"], ["INCOK", "Kochi"], ["INTUT", "Tuticorin (V.O.C.)"], ["INNML", "New Mangalore"], ["INVTZ", "Visakhapatnam"], ["INPRT", "Paradip"], ["INHAL", "Haldia / Kolkata"], ["SGSIN", "Singapore"], ["CNSHA", "Shanghai"], ["CNNGB", "Ningbo-Zhoushan"], ["CNSZX", "Shenzhen"], ["CNTSN", "Tianjin"], ["CNTAO", "Qingdao"], ["HKHKG", "Hong Kong"], ["KRPUS", "Busan"], ["JPYOK", "Tokyo / Yokohama"], ["TWKHH", "Kaohsiung"], ["MYPKG", "Port Klang"], ["MYTPP", "Tanjung Pelepas"], ["LKCMB", "Colombo"], ["AEJEA", "Jebel Ali (Dubai)"], ["NLRTM", "Rotterdam"], ["BEANR", "Antwerp"], ["DEHAM", "Hamburg"], ["DEBRV", "Bremerhaven"], ["ESVLC", "Valencia"], ["ESALG", "Algeciras"], ["GRPIR", "Piraeus"], ["GBFXT", "Felixstowe / London"], ["USLAX", "Los Angeles"], ["USLGB", "Long Beach"], ["USNYC", "New York / New Jersey"], ["USSAV", "Savannah"], ["USHOU", "Houston"], ["BRSSZ", "Santos"], ["ZADUR", "Durban"], ["EGSUZ", "Suez Canal (both ends)"]].map(v=>Object.freeze(v)));
const names=new Map(PORT_OPTIONS226);
const coverage='Every vessel broadcasts its own position by AIS radio; volunteer shore stations relay it through the free AISStream community feed. Coastal coverage only - a ship mid-ocean appears when it nears land. Destination and ETA are keyed in by the crew and can be stale. Free data, not for navigation.';
const plain=v=>v!==null&&typeof v==='object'&&Object.getPrototypeOf(v)===Object.prototype;
const closed=(v,keys)=>plain(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const text=(v,nullable=true)=>v===null&&nullable||typeof v==='string'&&v.length<=120&&!/[\u0000-\u001f\u007f-\u009f\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]/u.test(v);
const num=(v,lo,hi)=>typeof v==='number'&&Number.isFinite(v)&&v>=lo&&v<=hi;
const integer=(v,cap)=>Number.isInteger(v)&&v>=0&&v<=cap;
export function parseShips226(raw){
 if(typeof raw!=='string'||raw.length>1048576)return null;
 try{
  const d=JSON.parse(raw);
  if(!closed(d,['ok','warming','stalled','updated','count','ports','vessels'])||d.ok!==true||typeof d.warming!=='boolean'||typeof d.stalled!=='boolean'||!integer(d.count,6000)||typeof d.updated!=='string'||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(d.updated))return null;
  const time=new Date(d.updated);if(!Number.isFinite(time.getTime())||time.toISOString()!==d.updated)return null;
  if(!Array.isArray(d.ports)||d.ports.length!==42||!Array.isArray(d.vessels)||d.vessels.length>150||d.count<d.vessels.length)return null;
  const seen=new Set();
  for(const p of d.ports){if(!closed(p,['code','name','count'])||typeof p.code!=='string'||!names.has(p.code)||seen.has(p.code)||p.name!==names.get(p.code)||!integer(p.count,6000))return null;seen.add(p.code);}
  const ids=new Set();
  for(const v of d.vessels){
   if(!closed(v,['mmsi','name','type','flag','sog','dest','eta','lat','lon','port','seenAgoSec'])||typeof v.mmsi!=='string'||!/^\d{9}$/.test(v.mmsi)||ids.has(v.mmsi))return null;ids.add(v.mmsi);
   if(!['name','type','flag','dest','eta'].every(k=>text(v[k]))||!(v.sog===null||num(v.sog,0,102.3))||!num(v.lat,-90,90)||!num(v.lon,-180,180)||typeof v.port!=='string'||!names.has(v.port)||!integer(v.seenAgoSec,31536000))return null;
  }
  return d;
 }catch{return null;}
}
export function addPortOptions226(select){
 select.replaceChildren();
 for(const [code,name]of [['ALL','All supported ports'],...PORT_OPTIONS226]){const option=select.ownerDocument.createElement('option');option.value=code;option.textContent=name;select.append(option);}
}
export function renderShips226(root,raw,{complete=false}={}){
 root.replaceChildren();root.hidden=true;if(!complete||!raw)return false;
 const doc=root.ownerDocument;const node=(tag,value)=>{const n=doc.createElement(tag);if(value!==undefined)n.textContent=value;return n;};
 const d=parseShips226(raw);root.hidden=false;
 if(!d){root.append(node('p','Structured ship view unavailable. The supplied response is shown below.'));return false;}
 root.append(node('h3','Supplied ship response'),node('p',`Showing ${d.vessels.length} supplied rows; source reported ${d.count}`),node('p','Source timestamp (as supplied): '+d.updated));
 root.append(node('p',`Feed flags as reported: warming ${d.warming?'true':'false'}, stalled ${d.stalled?'true':'false'}. These flags do not prove freshness.`));
 if(!d.vessels.length)root.append(node('p','Supplied response has no vessels.'));
 else{
  const wrap=node('div');wrap.style.overflowX='auto';wrap.style.maxWidth='100%';wrap.style.maxHeight='420px';wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label','Supplied vessel table; scroll horizontally');
  const table=node('table');table.style.minWidth='900px';table.style.width='100%';table.style.borderCollapse='collapse';
  root.append(node('p','Supplied vessel rows. Destination and ETA are as reported.'));table.setAttribute('aria-label','Supplied vessel rows');
  const head=node('thead'),hr=node('tr');for(const h of ['Vessel','Type','Flag','Speed','Destination (as reported)','ETA (as reported)','Port area','Seen age (as reported)']){const th=node('th',h);th.scope='col';th.style.textAlign='left';th.style.padding='8px';hr.append(th);}head.append(hr);table.append(head);
  const body=node('tbody');for(const v of d.vessels){const tr=node('tr');for(const val of [v.name||'MMSI '+v.mmsi,v.type||'-',v.flag||'-',v.sog===null?'-':v.sog+' kn',v.dest||'-',v.eta||'-',names.get(v.port),v.seenAgoSec+' seconds']){const td=node('td',val);td.style.padding='8px';td.style.borderTop='1px solid #cedcea';td.style.maxWidth='200px';td.style.overflowWrap='anywhere';tr.append(td);}body.append(tr);}table.append(body);wrap.append(table);root.append(wrap);
 }
 root.append(node('p',coverage));return true;
}
