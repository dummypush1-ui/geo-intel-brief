import {DEFAULT_CHANNELS,channelList,videoId,embedUrl,watchUrl} from './live_channels.js';
const el=id=>document.getElementById(id);
let channels=channelList(DEFAULT_CHANNELS),selected=channels[0]?.video,playersStarted=false,liveVisible=false;
// Only this preview browser stores settings. No server/config/database writes.
// Render's disk is deliberately not used. Storage failure stays explicit.
const key='geo-intel-preview-channels-v1';
try{const saved=localStorage.getItem(key);if(saved && saved.length<=10000)channels=channelList(JSON.parse(saved));else if(saved)el('channel-status').textContent='Saved list is too large and was ignored; defaults loaded.';}catch{el('channel-status').textContent='Saved local channels unavailable; defaults loaded.';}
selected=channels[0]?.video;
function frame(channel,title){const iframe=document.createElement('iframe');iframe.src=embedUrl(channel.video);iframe.title=title+' '+channel.name;iframe.setAttribute('sandbox','allow-scripts allow-same-origin allow-presentation');iframe.allow='autoplay; encrypted-media; picture-in-picture';iframe.referrerPolicy='strict-origin-when-cross-origin';iframe.allowFullscreen=true;return iframe;}
function external(channel){const a=document.createElement('a');a.href=watchUrl(channel.video);a.target='_blank';a.rel='noopener noreferrer';a.textContent='Open on YouTube';return a;}
function renderSelected(){const target=el('live-selected');target.replaceChildren();const channel=channels.find(c=>c.video===selected);if(!channel){target.textContent='No channel selected.';return;}const h=document.createElement('h3');h.textContent=channel.name;target.append(h);if(playersStarted)target.append(frame(channel,'Selected player'));target.append(external(channel));}
function renderChannels(){
 const wall=el('live-wall'),list=el('my-channel-list');list.replaceChildren();
 const existing=new Map([...wall.querySelectorAll('[data-video]')].map(tile=>[tile.dataset.video,tile]));
 for(const tile of existing.values())if(!channels.some(c=>c.video===tile.dataset.video))tile.remove();
 for(const c of channels){let tile=existing.get(c.video);if(!tile && liveVisible){tile=document.createElement('article');tile.dataset.video=c.video;tile.className='live-tile';const choose=document.createElement('button');choose.textContent=c.name;choose.addEventListener('click',()=>{selected=c.video;el('live-selected').dataset.video=selected;renderSelected();});tile.append(choose);if(playersStarted)tile.append(frame(c,'Mini player'));tile.append(external(c));wall.append(tile);}
  const row=document.createElement('div');row.className='channel-row';const name=document.createElement('span');name.textContent=c.name;const remove=document.createElement('button');remove.textContent='Remove '+c.name;remove.addEventListener('click',()=>{const next=channels.filter(x=>x.video!==c.video);save(next);});row.append(name,external(c),remove);list.append(row);
 }
 if(!channels.length)wall.textContent='Your channel list is empty. Add a video in My channels.';
 if(liveVisible && el('live-selected').dataset.video!==selected){el('live-selected').dataset.video=selected||'';renderSelected();}
}
function save(next){channels=channelList(next);if(!channels.some(c=>c.video===selected))selected=channels[0]?.video;
 try{localStorage.setItem(key,JSON.stringify(channels));el('channel-status').textContent='Saved in this browser only. Other devices and cleared storage do not share this list.';}catch{el('channel-status').textContent='Storage unavailable. Changes last only for this page session.';}renderChannels();}
el('channel-add').addEventListener('submit',event=>{event.preventDefault();try{const video=videoId(el('channel-link').value);if(!video)throw new Error('Paste an exact YouTube watch link or video ID.');save([...channels,{name:el('channel-name').value,video}]);el('channel-add').reset();}catch(error){el('channel-status').textContent=error.message;}});
// Players are created once; news refresh never calls either render function.
// No message listener, wildcard trust, API discovery or polling is installed.
renderChannels();

document.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>{
 liveVisible=button.dataset.view==='live';
 if(liveVisible){playersStarted=true;renderChannels();}
}));
