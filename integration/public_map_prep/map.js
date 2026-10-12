/* Local-fixture candidate. No OSM/provider connector exists here. */
(function(root){'use strict';
class TileGate{
 constructor(clock=()=>Date.now()){this.clock=clock;this.active=0;this.errors=0;this.paused=false;this.pauseAt=0;this.generation=0;this.queue=[];this.jobs=new Map();this.failed=new Set();this.maxActive=0;this.hidden=false;this.cancelling=false;}
 resume(){if(this.paused&&this.clock()-this.pauseAt<60000)return false;this.cancelAll();this.generation++;this.errors=0;this.paused=false;this.failed.clear();return true;}
 pause(){this.paused=true;this.pauseAt=this.clock();this.generation++;this.cancelAll();}
 add(key,start){if(this.paused||this.hidden||this.failed.has(key)||this.jobs.has(key))return null;
 const item={key,start,g:this.generation,state:'queued',abort:null};this.jobs.set(key,item);this.queue.push(item);this.pump();return ()=>this.cancel(item);}
 finish(item,ok){if(item.state==='ended')return;const active=item.state==='active';item.state='ended';this.jobs.delete(item.key);if(active)this.active--;
 if(item.g===this.generation&&!ok){this.failed.add(item.key);this.errors++;if(this.errors>=3)this.pause();}this.pump();}
 cancel(item){if(item.state==='ended')return;const active=item.state==='active';item.state='ended';this.jobs.delete(item.key);this.queue=this.queue.filter(x=>x!==item);if(active)this.active--;if(item.abort)item.abort();this.pump();}
 cancelAll(){this.cancelling=true;for(const item of [...this.jobs.values()])this.cancel(item);this.queue=[];this.cancelling=false;}
 pump(){if(this.cancelling)return;while(this.active<4&&this.queue.length&&!this.paused&&!this.hidden){const item=this.queue.shift();if(item.state!=='queued')continue;if(item.g!==this.generation){this.cancel(item);continue;}item.state='active';this.active++;this.maxActive=Math.max(this.maxActive,this.active);const abort=item.start(ok=>this.finish(item,ok));if(typeof abort==='function'){if(item.state==='ended')abort();else item.abort=abort;}}}
 visible(v){this.hidden=!v;if(!v)this.cancelAll();else this.pump();}
}
if(typeof module!=='undefined'){module.exports={TileGate};return;}
root.MapTileGate=TileGate;
const $=id=>document.getElementById(id);let map=null,shapes=null,layer=null,inflight=false;const gate=new TileGate();let loaded=false;
function safeURL(v){try{if(typeof v!=='string'||v.length>2048||/[\s\\]/.test(v))return false;const u=new URL(v);return u.protocol==='https:'&&!u.username&&!u.password&&(!u.port||u.port==='443');}catch{return false;}}
async function bounded(url){const c=new AbortController(),timer=setTimeout(()=>c.abort(),10000);try{const r=await fetch(url,{signal:c.signal,cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer'});if(!r.ok)throw Error('Map data unavailable');const reader=r.body.getReader();let size=0,chunks=[];while(true){const x=await reader.read();if(x.done)break;size+=x.value.length;if(size>262144){await reader.cancel();throw Error('Oversized map response');}chunks.push(x.value);}const bytes=new Uint8Array(size);let n=0;for(const x of chunks){bytes.set(x,n);n+=x.length;}return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));}finally{clearTimeout(timer);}}
function clearNews(){$('articles').replaceChildren();if(shapes&&map){map.removeLayer(shapes);shapes=null;}}
function article(row){const card=document.createElement('article'),a=document.createElement('a');a.textContent=row.title;a.href=row.url;a.rel='noreferrer noopener';a.target='_blank';const p=document.createElement('p');p.textContent=(row.country||'Unmapped country')+' | '+row.source+(row.feature_id?' | country-level tag':' | unmapped');card.append(a,p);$('articles').append(card);}
function valid(x){if(!x||x.fixture_only!==true||!Array.isArray(x.rows)||x.rows.length>100||!x.countries||x.countries.type!=='FeatureCollection'||x.countries.features.length>256)return false;return x.rows.every(r=>typeof r.title==='string'&&r.title.length<=2048&&typeof r.country==='string'&&r.country.length<=100&&typeof r.source==='string'&&r.source.length<=100&&safeURL(r.url));}
async function refresh(){if(inflight)return;inflight=true;$('load').disabled=true;$('refresh').disabled=true;clearNews();try{const x=await bounded('/api/map-data');if(!valid(x))throw Error('Invalid fixture map response');if(!map){map=L.map('map',{minZoom:2,maxZoom:8,scrollWheelZoom:false,preferCanvas:true,attributionControl:true,maxBounds:[[-85.0511,-180],[85.0511,180]]}).setView([20,80],2);map.attributionControl.addAttribution('SIMULATED local reference data');}
 shapes=L.geoJSON(x.countries,{style:{color:'#f4bd68',weight:2,fillOpacity:.25},onEachFeature:(f,l)=>l.on('click',()=>{ $('articles').replaceChildren();x.rows.filter(r=>r.feature_id===f.properties.id).forEach(article);})}).addTo(map);x.rows.forEach(article);$('status').textContent='SIMULATED fixture: '+x.rows.length+' country-tagged articles in latest-100 view. '+x.rows_unmapped+' unmapped.';loaded=true;$('tiles').disabled=false;
}catch(e){clearNews();$('status').textContent=e.message+'; news cleared. No automatic retry.';}finally{inflight=false;$('load').disabled=false;$('refresh').disabled=!loaded;}}
function tiles(){if(!map||!gate.resume()){$('tile-status').textContent='Paused. Wait 60 seconds before a deliberate resume.';return;}if(layer)map.removeLayer(layer);
 const Fake=L.TileLayer.extend({_removeTile(key){const t=this._tiles[key];if(t&&t.el._gateCancel)t.el._gateCancel();return L.GridLayer.prototype._removeTile.call(this,key);},_abortLoading(){for(const key of Object.keys(this._tiles)){if(this._tiles[key].coords.z!==this._tileZoom)this._removeTile(key);}},createTile(coords,done){const img=document.createElement('img');img.alt='';img.referrerPolicy='strict-origin-when-cross-origin';const key=coords.z+'/'+coords.x+'/'+coords.y;const g=gate.generation;
 const cancel=gate.add(key,finish=>{let timer;const stop=()=>{clearTimeout(timer);img.onload=null;img.onerror=null;img.removeAttribute('src');};
 const end=ok=>{clearTimeout(timer);img.onload=null;img.onerror=null;finish(ok);if(!ok&&gate.paused)$('tile-status').textContent='Simulated tiles paused after 3 errors. Local map and news remain usable.';if(g===gate.generation)done(ok?null:Error('Tile unavailable'),img);};
 img.onload=()=>end(true);img.onerror=()=>end(false);timer=setTimeout(()=>{stop();end(false);},10000);img.src='/workspace/map-fixture/tiles/'+key+'.png';return stop;});
 img._gateCancel=cancel;if(!cancel)setTimeout(()=>done(Error('Tile suppressed'),img),0);return img;}});
 layer=new Fake('/workspace/map-fixture/tiles/{z}/{x}/{y}.png',{minZoom:2,maxZoom:8,noWrap:true,keepBuffer:0,updateWhenIdle:true,updateWhenZooming:false,detectRetina:false,attribution:'SIMULATED local tiles'}).on('tileunload',e=>{if(e.tile._gateCancel)e.tile._gateCancel();}).addTo(map);root.__map=map;root.__mapLayer=layer;$('tile-status').textContent='SIMULATED local tiles loading, maximum 4 starts. No real OSM requests.';
}
$('load').onclick=refresh;$('refresh').onclick=refresh;$('tiles').onclick=tiles;function visibility(v){gate.visible(v);if(layer&&map){if(!v)map.removeLayer(layer);else if(!map.hasLayer(layer)&&!gate.paused)map.addLayer(layer);}}
document.addEventListener('visibilitychange',()=>visibility(!document.hidden));root.__mapVisibility=visibility;root.__mapGate=gate;
})(typeof window!=='undefined'?window:globalThis);
