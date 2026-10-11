// Public browser-only extras. No server mutation, cookie or remote API.
export const STORAGE_KEY='geo-intel-public-brics-extras-v1';
export const FIXED=Object.freeze({name:'Republic',video:'jndNegut8RY'});
export const DEFAULT_EXTRAS=Object.freeze([
 {name:'Al Jazeera English',video:'gCNeDWCI0vo'},
 {name:'France24 English',video:'HvZt-nh9sGg'},
 {name:'DW News',video:'LuKwFajn37U'},
 {name:'ANI News',video:'nOuWVqeUGt4'},
].map(Object.freeze));
const DEFAULT_IDS=new Set([FIXED.video,...DEFAULT_EXTRAS.map(c=>c.video)]);
export function videoId(value){
 if(typeof value!=='string'||value.length>200||/[\s\\%#\p{C}]/u.test(value))return null;
 if(/^[A-Za-z0-9_-]{11}$/.test(value))return value;
 let m=value.match(/^https:\/\/youtu\.be\/([A-Za-z0-9_-]{11})$/);
 if(!m)m=value.match(/^https:\/\/(?:www\.)?youtube\.com\/watch\?v=([A-Za-z0-9_-]{11})$/);
 if(!m)m=value.match(/^https:\/\/(?:www\.)?youtube\.com\/(?:live|embed)\/([A-Za-z0-9_-]{11})$/);
 return m?.[1]||null;
}
// NFKC + casefold for reserved ASCII 'Republic'. Compatibility characters become
// ASCII before lowercasing; no non-ASCII casefold can produce this ASCII word.
export function nameKey(s){return s.normalize('NFKC').toLowerCase();}
export function extrasChecked(value){
 if(!Array.isArray(value)||value.length>8)throw new Error('Use up to 8 extra channels.');
 const videos=new Set([FIXED.video]),names=new Set([nameKey(FIXED.name)]);
 return value.map(row=>{
  if(!row||typeof row!=='object'||Array.isArray(row)||Object.getPrototypeOf(row)!==Object.prototype||Object.keys(row).sort().join(',')!=='name,video')throw new Error('Invalid channel fields.');
  if(typeof row.name!=='string'||!row.name.trim()||[...row.name].length>80||/[\p{C}]/u.test(row.name)||!/[\p{L}\p{N}\p{P}\p{S}]/u.test(row.name.replace(/[\u115f\u1160\u2800\u3164\uffa0]/g,'')))throw new Error('Use a visible short channel name.');
  const name=row.name.trim(),video=videoId(row.video),key=nameKey(name);
  if(!video)throw new Error('Use a valid YouTube video ID or exact link.');
  if(videos.has(video)||names.has(key))throw new Error('Duplicate or reserved Republic channel.');
  videos.add(video);names.add(key);return {name,video};
 });
}
export function loadExtras(storage){
 try{const saved=storage.getItem(STORAGE_KEY);if(saved===null)return {extras:extrasChecked([...DEFAULT_EXTRAS]),message:''};
  if(typeof saved!=='string'||saved.length>10000)throw new Error();
  return {extras:extrasChecked(JSON.parse(saved)),message:'Saved in this browser only.'};
 }catch{return {extras:extrasChecked([...DEFAULT_EXTRAS]),message:'Saved local channels invalid or unavailable; four defaults restored.'};}
}
export function embedUrl(id){if(videoId(id)!==id)throw new Error('Invalid ID.');return 'https://www.youtube-nocookie.com/embed/'+id+'?autoplay=1&mute=1&playsinline=1&rel=0';}
export function watchUrl(id){if(videoId(id)!==id)throw new Error('Invalid ID.');return 'https://www.youtube.com/watch?v='+id;}

if(typeof document!=='undefined'){
 const el=id=>document.getElementById(id);
 let storage;try{storage=localStorage;}catch{storage={getItem(){throw new Error();},setItem(){throw new Error();}};}
 const loaded=loadExtras(storage);let extras=loaded.extras,selected=FIXED.video,started=true,ready=false;
 const active=new Set(),tiles=new Map();
 const channels=()=>[FIXED,...extras];
 const status=message=>{el('status').textContent=message;};
 function frame(c,title){const f=document.createElement('iframe');f.src=embedUrl(c.video);f.title=title+' '+c.name;f.setAttribute('sandbox','allow-scripts allow-same-origin allow-presentation');f.allow='autoplay; encrypted-media; picture-in-picture';f.referrerPolicy='strict-origin-when-cross-origin';f.allowFullscreen=true;return f;}
 function external(c){const a=document.createElement('a');a.href=watchUrl(c.video);a.target='_blank';a.rel='noopener noreferrer';a.textContent='Open on YouTube';return a;}
 function selectedPlayer(){const target=el('selected'),c=channels().find(c=>c.video===selected)||FIXED;target.replaceChildren();const h=document.createElement('h2');h.textContent=c.name;target.append(h);if(started)target.append(frame(c,'Selected player'));target.append(external(c));}
 function mini(tile,c){const existing=tile.querySelector('iframe');if(active.has(c.video)&&started&&!existing)tile.append(frame(c,'Mini player'));if((!active.has(c.video)||!started)&&existing)existing.remove();}
 function render(){
  const current=channels();for(const [id,tile]of tiles)if(!current.some(c=>c.video===id)){tile.remove();tiles.delete(id);active.delete(id);}
  for(const c of current){let tile=tiles.get(c.video);if(!tile){tile=document.createElement('article');tile.dataset.video=c.video;const h=document.createElement('h2');h.textContent=c.name;const controls=document.createElement('div');controls.className='tile-head';const choose=document.createElement('button');choose.textContent='Select '+c.name;choose.onclick=()=>{if(!ready)return;selected=c.video;started=true;selectedPlayer();};controls.append(choose);
    const play=document.createElement('button');play.textContent='Load mini '+c.name;play.onclick=()=>{if(!ready)return;started=true;active.add(c.video);mini(tile,c);};controls.append(play);tile.append(h,controls,external(c));tiles.set(c.video,tile);el('wall').append(tile);}
   mini(tile,c);
  }
  el('list').replaceChildren();for(const c of current){const row=document.createElement('div');row.className='channel-row';const name=document.createElement('span');name.textContent=c.name;row.append(name,external(c));if(c.video===FIXED.video){const badge=document.createElement('span');badge.className='badge';badge.textContent='Compulsory - cannot be removed';row.append(badge);}else{const remove=document.createElement('button');remove.textContent='Remove '+c.name;remove.onclick=()=>save(extras.filter(e=>e.video!==c.video));row.append(remove);}el('list').append(row);}
 }
 function save(next){if(!ready)throw new Error('Supplied configuration unavailable.');extras=extrasChecked(next);if(!channels().some(c=>c.video===selected)){selected=FIXED.video;selectedPlayer();}
  try{storage.setItem(STORAGE_KEY,JSON.stringify(extras));status('Saved in this browser only. Other devices and cleared storage do not share this list.');}catch{status('Storage unavailable. Changes last only for this page session.');}
  render();
 }
 el('stop').onclick=()=>{started=false;active.clear();selectedPlayer();render();status('Players stopped. No new video loads until you start or select.');};
 el('start').onclick=()=>{if(!ready)return;started=true;for(const c of channels())if(DEFAULT_IDS.has(c.video))active.add(c.video);selectedPlayer();render();status('Default IDs still in your list started. Extras load only on click.');};
 el('add').onsubmit=event=>{event.preventDefault();try{save([...extras,{name:el('name').value,video:el('link').value}]);el('add').reset();}catch(e){status(e.message);}};
 el('reset').onclick=()=>{if(confirm('Reset your extra channels to the four defaults in this browser?'))save([...DEFAULT_EXTRAS]);};
 // Validate the fixed readonly server payload before any iframe creation.
 async function init(){try{const r=await fetch('/api/brics/streams',{cache:'no-store',credentials:'same-origin'});if(!r.ok)throw new Error();const body=await r.text();if(body.length>32768)throw new Error();const data=JSON.parse(body);
   if(!Array.isArray(data.streams)||data.streams.length!==5)throw new Error();
   const seeds=[FIXED,...DEFAULT_EXTRAS];for(let i=0;i<5;i++){const row=data.streams[i],seed=seeds[i];if(!row||row.name!==seed.name||row.video!==seed.video||row.watch_url!==watchUrl(seed.video)||row.compulsory!==(i===0)||'embed_url'in row)throw new Error();}
   ready=true;if(started)for(const c of channels())if(DEFAULT_IDS.has(c.video))active.add(c.video);
   selectedPlayer();render();status(loaded.message||'Supplied video IDs loaded. Playback and live availability unverified.');
  }catch{started=false;el('start').disabled=true;el('add').querySelector('button').disabled=true;status('Supplied stream configuration unavailable. No players started.');}}
 init();
}
