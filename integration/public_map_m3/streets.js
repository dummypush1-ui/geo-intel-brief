/* Manual online layer only. No geolocation, background retry, download or proxy. */
(()=>{'use strict';
const HOST='tiles.openfreemap.org',PREFIX='/workspace/map-streets/',$=id=>document.getElementById(id);
let layer=null,map=null,generation=0,timer=null;
function source(url){const u=new URL(url,location.href);if(u.origin===location.origin&&u.pathname===PREFIX+'liberty.json'&&!u.search&&!u.hash)return {url:u.href,credentials:'omit'};if(u.protocol!=='https:'||u.hostname!==HOST||u.username||u.password||u.port&&u.port!=='443'||u.search||u.hash||!/^\/(planet(?:\/|$)|fonts\/|sprites\/|natural_earth\/)/.test(u.pathname))throw Error('Street source refused');return{url:u.href,credentials:'omit'};}
function stop(message){generation++;clearTimeout(timer);timer=null;const old=layer;layer=null;if(old){try{if(map&&map.hasLayer(old))map.removeLayer(old);else old.getMaplibreMap()?.remove();}catch{try{old.getMaplibreMap()?.remove();}catch{}old.getContainer()?.remove();}}if(map){map.setMaxZoom(8);if(map.getZoom()>8)map.setZoom(8);}if($('m3-start'))$('m3-start').disabled=false;if($('m3-status'))$('m3-status').textContent=message;}
function start(){
 if(layer)return;map=window.__map;
 if(!map){$('m3-status').textContent='Load reference map first. No street request made.';return;}
 if(document.hidden){$('m3-status').textContent='Open this tab before requesting streets.';return;}
 const mine=++generation;$('m3-start').disabled=true;$('m3-status').textContent='Loading online streets. Country map remains underneath.';
 try{
  if(!window.maplibregl||!window.L?.MaplibreGL)throw Error('Street renderer unavailable');
  maplibregl.setWorkerUrl(PREFIX+'maplibre-worker.js');maplibregl.setWorkerCount(1);maplibregl.setMaxParallelImageRequests(4);
  // Provider TileJSON attribution is not rendered as HTML. Our static credit is
  // always visible directly below the map, without opening any control.
  const Safe=L.MaplibreGL.extend({getAttribution(){return '';},onRemove(m){if(this._glMap)return L.MaplibreGL.prototype.onRemove.call(this,m);this._container?.remove();}});
  layer=new Safe({style:PREFIX+'liberty.json',interactive:false,padding:0,minZoom:1,maxZoom:17,maxTileCacheSize:64,renderWorldCopies:false,refreshExpiredTiles:false,transformRequest:source,attributionControl:false});
  layer.addTo(map);const gl=layer.getMaplibreMap();
  const fail=()=>{if(mine===generation)stop('Street map unavailable. Country map and historical ports remain usable. No automatic retry; choose streets manually later.');};
  gl.on('error',fail);gl.getCanvas().addEventListener('webglcontextlost',fail,{once:true});
  timer=setTimeout(fail,15000);
  gl.once('idle',()=>{if(mine!==generation)return;clearTimeout(timer);timer=null;map.setMaxZoom(18);$('m3-status').textContent='Online streets shown. Credit stays visible in the map corner. Country-tagged news is not a precise street location; ports are historical.';});
 }catch{if(mine===generation)stop('Street renderer unavailable. Country map and historical ports remain usable. No automatic retry.');}
}
$('m3-start').addEventListener('click',e=>{if(e.isTrusted)start();});$('m3-stop').addEventListener('click',()=>stop('Country map only. Online street layer stopped; no automatic restart.'));
document.addEventListener('visibilitychange',()=>{if(document.hidden&&layer)stop('Street layer stopped while tab is hidden. Country map remains; resume manually.');});
window.addEventListener('pagehide',()=>stop('Street layer stopped.'));
window.__m3Audit=()=>({active:!!layer,generation,creditVisible:!!$('m3-credit')?.getClientRects().length});
})();
