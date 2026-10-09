// Default-OFF same-origin controller. No backend key, provider URL or storage.
export function createBrokerClient({enabled=false,fetcher,nonceFactory,onChange=()=>{}}={}) {
 if(typeof enabled!=='boolean'||typeof onChange!=='function')throw Error('Invalid client selection');
 if(enabled&&(typeof fetcher!=='function'||typeof nonceFactory!=='function'))throw Error('Explicit client adapters required');
 let state={session:'signed_out',request:enabled?'idle':'disabled',username:'',answer:'',message:enabled?'Sign in with your owner-provisioned account.':'Built-in AI and ships are off. Own-provider keys are unchanged.'};
 let csrf='',busy=false,blocked=false,lastNonce='';
 const view=()=>Object.freeze({...state,busy,blocked});
 function emit(patch){state={...state,...patch};onChange(view());return view();}
 async function call(path,body,token=''){
  const allowed=['/account/preauth','/account/login','/account/logout','/account/whoami','/api/finder-broker/ships','/api/finder-broker/ai'];
  if(!allowed.includes(path))throw Error('Closed route');
  const options={method:body===undefined?'GET':'POST',credentials:'same-origin',cache:'no-store',redirect:'error',headers:{Accept:'application/json'}};
  if(body!==undefined){options.headers['Content-Type']='application/json';options.body=JSON.stringify(body);}
  if(token)options.headers['X-CSRF-Token']=token;
  // Browser supplies Origin on same-origin POST. Do not set or trust caller host.
  const controller=new AbortController();options.signal=controller.signal;
  const timer=setTimeout(()=>controller.abort(),25000);
  let res,raw='';try{
   res=await fetcher(path,options);
   if(res.body?.getReader){const reader=res.body.getReader(),decoder=new TextDecoder();let total=0;
    try{while(true){const {value,done}=await reader.read();if(done)break;total+=value.byteLength;if(total>1048576){await reader.cancel();throw Error('Response too large');}raw+=decoder.decode(value,{stream:true});}raw+=decoder.decode();}finally{reader.releaseLock();}
   }else{raw=await res.text();if(raw.length>1048576)throw Error('Response too large');}
  }finally{clearTimeout(timer);}
  if(typeof res.status!=='number'||typeof res.text!=='function')throw Error('Invalid response');
  return {status:res.status,data:JSON.parse(raw)};
 }
 async function login(username,password){
  if(!enabled||busy)return view();csrf='';busy=true;emit({message:'Signing in...'});
  try{
   const pre=await call('/account/preauth');
   if(pre.status!==200||typeof pre.data.csrf!=='string')throw Error('Preauth unavailable');
   const r=await call('/account/login',{username,password,csrf:pre.data.csrf});password='';
   if(r.status!==200||r.data.ok!==true||typeof r.data.csrf!=='string')return emit({session:'signed_out',username:'',message:r.status===429?'Sign-in attempts are limited. Wait before trying again.':'Sign-in failed. Check your account credentials.'});
   csrf=r.data.csrf;
   return emit({session:'signed_in',username:String(r.data.username||username),message:blocked?'Signed in. The earlier request is still held. Do not resubmit.':'Signed in. Built-in AI stays off until a model is verified.'});
  }catch{return emit({session:'signed_out',username:'',message:'Sign-in unavailable. No automatic retry.'});}
  finally{password='';busy=false;onChange(view());}
 }
 async function checkSession(){
  if(!enabled||busy)return view();busy=true;
  try{
   const r=await call('/account/whoami');
   if(r.status!==200||r.data.ok!==true||typeof r.data.csrf!=='string'){csrf='';return emit({session:'expired',username:'',message:'Session expired or signed out. Sign in again.'});}
   csrf=r.data.csrf;return emit({session:'signed_in',username:String(r.data.username||''),message:blocked?'Request held. Sign-in does not clear it.':'Signed in.'});
  }catch{csrf='';return emit({session:'expired',username:'',message:'Session unavailable. Sign in again.'});}
  finally{busy=false;onChange(view());}
 }
 async function logout(){
  if(!enabled||busy)return view();busy=true;
  let confirmed=false;try{const r=await call('/account/logout',{csrf});confirmed=r.status===200&&r.data.ok===true;}catch{}
  finally{csrf='';busy=false;emit({session:'signed_out',username:'',answer:'',message:confirmed?(blocked?'Signed out. The request is still held; do not resubmit.':'Signed out.'):'Local session cleared. Server sign-out was not confirmed; check the session before continuing.'});}
  return view();
 }
 async function request(operation,payload){
  if(!enabled||busy||blocked||state.session!=='signed_in')return view();
  if(!['ships','ai'].includes(operation)||!payload||typeof payload!=='object')throw Error('Closed operation');
  if(operation==='ai'){return emit({request:'disabled',message:'Built-in AI is off until a model is verified.'});}
  if(Object.keys(payload).join(',')!=='port'||typeof payload.port!=='string')throw Error('Closed ships payload');
  const nonce=nonceFactory();if(typeof nonce!=='string'||!/^[A-Za-z0-9_-]{20,80}$/.test(nonce)||nonce===lastNonce)throw Error('Fresh request nonce required');
  lastNonce=nonce;busy=true;emit({request:'sending',answer:'',message:'Request sent once. Do not refresh or resubmit.'});
  try{
   const r=await call('/api/finder-broker/'+operation,{nonce,...payload},csrf);
   if(r.status===401||r.status===403){csrf='';blocked=true;return emit({session:'expired',username:'',request:'held',message:'Session expired or the request was refused. Its outcome is held. Sign-in does not clear it; do not resubmit.'});}
   if(r.data?.state==='replay_status_only'){blocked=true;return emit({request:'replay',message:'This request was already recorded. No cached answer is available. Do not resubmit.'});}
   if(r.status===409||r.status>=500){blocked=true;return emit({request:'held',message:'Request held. Its outcome may be unknown. The owner must check it before another request.'});}
   if(r.status<200||r.status>=300){blocked=true;return emit({request:'unknown',message:'Request outcome is unknown. Do not retry or submit a new request.'});}
   return emit({request:'complete',answer:JSON.stringify(r.data,null,2),message:'Ship response received. No automatic refresh.'});
  }catch{blocked=true;return emit({request:'unknown',message:'Request outcome is unknown. Do not retry, reload or submit a new request.'});}
  finally{busy=false;onChange(view());}
 }
 return Object.freeze({view,login,logout,checkSession,request});
}
