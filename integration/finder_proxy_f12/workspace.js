import {mountBrokerPanel} from './panel.mjs';
const frame=document.getElementById('finder');
if(frame){
 const root=document.createElement('section');root.id='finder-proxy-f12-account';frame.after(root);
 const client=mountBrokerPanel(root,{enabled:true,features:true,fetcher:window.fetch.bind(window),nonceFactory:()=>crypto.randomUUID().replace(/-/g,'')});
 const note=document.createElement('p');note.textContent='Optional Finder context uses the existing proxy only after sign-in and review gates. No personal AI key is needed. Selected public snapshot evidence is sent to the existing proxy. When you click the classifier, your typed query (up to 1,000 characters) is also sent to the proxy; do not enter private information. No notes, private news or saved keys. AI text is not current research or a legal verdict. Unknown requests are never retried automatically.';root.prepend(note);
 function sourceWindow(){
  if(frame.getAttribute('src')?.startsWith('/workspace/finder/live.html')){
   try{return frame.contentWindow.document.getElementById('finder-frame')?.contentWindow}catch{return null}
  }return frame.contentWindow;
 }
 let busy=false;
 window.addEventListener('message',async event=>{
  if(event.origin!==location.origin||event.source!==sourceWindow())return;
  const v=event.data;if(!v||v.type!=='finder-proxy-f12-request'||typeof v.id!=='string'||!/^[a-f0-9-]{36}$/.test(v.id))return;
  if(Object.keys(v).sort().join(',')!=='candidates,feature,id,question,type')return;
  const reply=(result,dispatched)=>event.source.postMessage({type:'finder-proxy-f12-response',id:v.id,result,dispatched},location.origin);
  if(busy){reply({ok:false},false);return}
  const before=client.view();if(before.session!=='signed_in'||before.blocked){reply({ok:false},before.blocked);root.scrollIntoView({block:'nearest'});return}
  busy=true;try{
   const state=await client.request('features',{feature:v.feature,question:v.question,candidates:v.candidates});let result;
   try{result=JSON.parse(state.answer)}catch{result={ok:false}}
   reply(result,true);
  }catch{reply({ok:false},false)}finally{busy=false}
 });
}
