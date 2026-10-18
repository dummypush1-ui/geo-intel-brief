// F16 preserved trade-year comparison. No requests, prediction or saved state.
(() => {
 const META=/*F16_META*/;
 const el=(t,text)=>{const n=document.createElement(t);if(text!==undefined)n.textContent=String(text);return n};
 const field=(dl,k,v)=>dl.append(el('dt',k),el('dd',v===null||v===undefined?'Not supplied':typeof v==='object'?JSON.stringify(v):v));
 const valid=(v)=>typeof v==='number'&&Number.isFinite(v)&&v>=0;
 const number=v=>typeof v==='number'&&Number.isFinite(v)?String(v):'Unavailable';
 function change(a,b,weight=false){if(!valid(a)||!valid(b)||(weight&&(a===0||b===0)))return 'Unavailable - missing or unreported observation';return number(b-a)+(a===0?' (percentage unavailable: baseline zero)':' ('+number(Math.round((b-a)/a*10000)/100)+'%)')}
 function draw(){
  const anchor=document.getElementById('d-tpl');if(!anchor||!S.db||!Number.isInteger(S.sel))return;const existing=document.getElementById('f16-trend');if(existing){if(existing.dataset.selection===String(S.sel))return;existing.remove()}
  const e=S.db.entries[S.sel];if(!e)return;const box=el('details');box.id='f16-trend';box.dataset.selection=String(S.sel);box.className='detail-sec';box.append(el('summary','Trade-year comparison - preserved India data'),el('p','Data, not advice. Compare two calendar years in the preserved series. No current-market, demand, forecast, price or shipment decision is made. No live refresh.'));
  const dl=el('dl');field(dl,'Selected identity',SYS[e[0]].tag+' '+e[1]);field(dl,'Dataset build label',DATA_BUILD);for(const [k,v]of Object.entries(META))field(dl,k,v);box.append(dl);
  if(e[0]!==1||e[1].length<6){box.append(el('p','Open an India code with at least six digits. Foreign or chapter/heading codes do not establish an India trade-series mapping.'));anchor.after(box);return}
  const code=e[1].slice(0,6);box.append(el('p','Series scope: India merchandise trade, HS6 '+code+', partner World, calendar years. National product detail is not separately measured. Dataset source attribution: UN Comtrade, reporter699; imports value CIF, exports value USD; net weight kg. Zero weight means not reported, not zero physical flow. Values are retained as source observations, not independently reconciled.'));
  const rows=TRADE_TREND[code];if(!Array.isArray(rows)||rows.length===0){box.append(el('p','No series in this snapshot. This is not zero trade or proof of no demand.'));anchor.after(box);return}
  const map=new Map(),duplicates=new Set();for(const r of rows){if(!Array.isArray(r)||r.length!==5||!Number.isInteger(r[0]))continue;if(map.has(r[0]))duplicates.add(r[0]);map.set(r[0],r)}
  const years=[...map.keys()].sort((a,b)=>a-b);if(!years.length){box.append(el('p','No valid year rows in this snapshot.'));anchor.after(box);return}
  box.append(el('p','Year rows present: '+years.join(', ')+'. Dataset expected years: '+TRADE_TREND_YEARS.join(', ')+'. Missing years are not interpolated. Duplicate years: '+(duplicates.size?[...duplicates].join(', ')+'; last source row displayed':'none')+'.'));
  const controls=el('div');const selectors=[];for(const [id,label]of[['f16-from','From calendar year'],['f16-to','To calendar year']]){const l=el('label',label+' '),s=el('select');s.id=id;for(const y of years){const o=el('option',y);o.value=String(y);s.append(o)}l.append(s);controls.append(l);selectors.push(s)}selectors[0].value=String(years[0]);selectors[1].value=String(years[years.length-1]);box.append(controls);const result=el('div');box.append(result);
  function compare(){result.replaceChildren();const ya=Number(selectors[0].value),yb=Number(selectors[1].value),a=map.get(ya),b=map.get(yb);if(!a||!b){result.append(el('p','Choose two year rows present in this snapshot.'));return}if(duplicates.has(ya)||duplicates.has(yb)){result.append(el('p','Chosen year has duplicate source rows. No arithmetic comparison is made.'));return}
   result.append(el('p',ya===yb?'Same-year identity check, not growth.':yb<ya?'Reverse chronological comparison. Changes use the chosen From year as baseline.':'Changes use the chosen From year as baseline.'));
   const values=el('dl');for(const [i,label,unit,weight]of[[1,'Imports','USD',false],[2,'Exports','USD',false],[3,'Imports net weight','kg',true],[4,'Exports net weight','kg',true]]){const show=v=>valid(v)?weight&&v===0?'Not reported (source 0)':number(v)+' '+unit:'Unavailable';field(values,label+' '+ya,show(a[i]));field(values,label+' '+yb,show(b[i]));field(values,label+' change ('+unit+')',change(a[i],b[i],weight))}result.append(values,el('p','Differences and percentages are arithmetic on snapshot values, not a forecast. A zero value is retained as a source value, not evidence that all trade was measured. Values and weights have different reporting coverage; no unit price is inferred.'));
  }
  for(const s of selectors)s.addEventListener('change',compare);compare();anchor.after(box);
 }
 new MutationObserver(draw).observe(document.getElementById('root'),{subtree:true,childList:true});draw();
})();
