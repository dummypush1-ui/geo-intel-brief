// Exact owned-frame provider events only. No availability lookup or auto retry.
export const PROVIDER_ORIGIN='https://www.youtube-nocookie.com';
export function failureState(data){
 if(typeof data!=='string'||data.length>4096)return null;
 let body;try{body=JSON.parse(data);}catch{return null;}
 if(!body||typeof body!=='object'||Array.isArray(body))return null;
 if(body.event==='infoDelivery'&&body.info&&typeof body.info==='object'&&!Array.isArray(body.info)&&body.info.playerState===0)return 'ended';
 if(body.event==='onStateChange'&&body.info===0)return 'ended';
 if(body.event==='onError'&&[2,5,100,101,150].includes(body.info))return 'error';
 return null;
}
export function installRecovery(doc,win){
 const selected=doc.getElementById('selected'),wall=doc.getElementById('wall');
 if(!selected||!wall)throw new Error('Player recovery mount unavailable.');
 const seen=new WeakSet(),held=new Map();let closed=false,sequence=0;
 const frames=()=>[...selected.querySelectorAll('iframe'),...wall.querySelectorAll('iframe')];
 function owned(frame){return frame.isConnected&&(frame.parentElement===selected||frame.parentElement?.matches('#wall > article'));}
 function url(frame){try{const value=new URL(frame.src);return value.origin===PROVIDER_ORIGIN&&/^\/embed\/[A-Za-z0-9_-]{11}$/.test(value.pathname)?value:null;}catch{return null;}}
 function attach(frame){
  if(seen.has(frame)||!owned(frame)||!url(frame))return;
  seen.add(frame);if(!frame.id)frame.id='brics-recovery-'+(++sequence);frame.addEventListener('load',()=>{if(closed||!owned(frame))return;try{frame.contentWindow.postMessage(JSON.stringify({event:'listening',id:frame.id}),PROVIDER_ORIGIN);}catch{}});
 }
 function sweep(){
  if(closed)return;
  for(const [host,state]of held)if(!host.isConnected||!host.contains(state.panel)){held.delete(host);host.removeAttribute('data-recovery-held');}
  for(const frame of frames())attach(frame);
 }
 function clear(){for(const [host,state]of held){state.panel.remove();host.removeAttribute('data-recovery-held');}held.clear();}
 function message(event){
  if(closed||event.origin!==PROVIDER_ORIGIN)return;
  const state=failureState(event.data);if(!state)return;
  const frame=frames().find(f=>owned(f)&&f.contentWindow===event.source&&url(f));if(!frame)return;
  const host=frame.parentElement;if(held.has(host))return;
  const target=url(frame),panel=doc.createElement('div');panel.className='player-recovery';panel.setAttribute('role','status');
  const text=doc.createElement('p');text.textContent=state==='ended'?'This player reported that the video ended. Live availability is unverified.':'This player reported a playback error. Availability or provider restrictions are unverified.';
  const retry=doc.createElement('button');retry.type='button';retry.textContent=host===selected?'Retry selected player':'Retry mini player';
  const add=doc.createElement('button');add.type='button';add.textContent='Add a new feed';add.onclick=()=>{if(closed||!panel.isConnected)return;const input=doc.getElementById('name');input?.scrollIntoView({block:'center'});input?.focus();};
  const watch=doc.createElement('a');watch.href='https://www.youtube.com/watch?v='+target.pathname.split('/').pop();watch.target='_blank';watch.rel='noopener noreferrer';watch.textContent='Open on YouTube';
  retry.onclick=()=>{
   if(closed||!host.isConnected||!host.contains(panel)||held.get(host)?.panel!==panel)return;
   held.delete(host);host.removeAttribute('data-recovery-held');panel.remove();
   const next=frame.cloneNode(false);host.append(next);attach(next);
  };
  host.dataset.recoveryHeld='true';frame.remove();panel.append(text,retry,doc.createTextNode(' '),add,doc.createTextNode(' '),watch);host.append(panel);held.set(host,{panel});
 }
 function reset(){if(!closed)clear();}
 const observer=new MutationObserver(sweep);observer.observe(selected,{childList:true,subtree:true});observer.observe(wall,{childList:true,subtree:true});
 win.addEventListener('message',message);doc.getElementById('stop')?.addEventListener('click',reset,true);doc.getElementById('start')?.addEventListener('click',reset,true);
 function close(){if(closed)return;closed=true;observer.disconnect();win.removeEventListener('message',message);doc.getElementById('stop')?.removeEventListener('click',reset,true);doc.getElementById('start')?.removeEventListener('click',reset,true);clear();}
 win.addEventListener('pagehide',()=>{close();win.addEventListener('pageshow',function resume(event){if(event.persisted){win.removeEventListener('pageshow',resume);installRecovery(doc,win);}});},{once:true});sweep();return close;
}
