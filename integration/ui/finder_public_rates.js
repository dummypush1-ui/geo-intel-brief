'use strict';
// No startup requests, storage, credentials, provider keys or polling.
const form=document.getElementById('public-rates');
form.addEventListener('submit',async event=>{
 event.preventDefault();if(!event.isTrusted)return;
 const button=form.querySelector('button'),out=document.getElementById('rate-status');
 const base=document.getElementById('rate-base').value,quote=document.getElementById('rate-quote').value;
 if(base===quote){out.textContent='Choose two different currencies.';return;}
 button.disabled=true;out.textContent='Fetching a reference rate...';
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),5000);
 try{
  const response=await fetch('/api/finder-public-rates?'+new URLSearchParams({base,quote}),{method:'GET',credentials:'omit',redirect:'error',cache:'no-store',signal:controller.signal});
  if(!response.ok)throw new Error(response.status===429?'Rates busy. Wait before another manual request.':'Reference rates unavailable. Try later manually.');
  const text=await response.text();if(text.length>4096)throw new Error('Response refused.');
  const row=JSON.parse(text);
  if(row.base!==base||row.quote!==quote||typeof row.rate!=='number'||!Number.isFinite(row.rate)||row.rate<=0||typeof row.date!=='string')throw new Error('Response refused.');
  out.textContent='1 '+base+' = '+row.rate+' '+quote+' | reference date '+row.date+(row.cached?' | cached':'')+'. Not a live trade price.';
 }catch(error){out.textContent=error.name==='AbortError'?'Request timed out. No automatic retry.':error.message;}
 finally{clearTimeout(timer);button.disabled=false;}
});
// The unchanged offline snapshot has old key-provider advice. Hide only that
// misleading tip inside this public wrapper. No source or storage is changed.
const localFrame=document.querySelector('iframe');
localFrame.addEventListener('load',()=>{
 try{
  const removeTip=()=>{for(const p of localFrame.contentDocument.querySelectorAll('p'))if(p.textContent.startsWith('Tip: add a free Gemini or Groq key'))p.remove();};
  removeTip();
  const observer=new MutationObserver(removeTip);
  observer.observe(localFrame.contentDocument.body,{subtree:true,childList:true});
 }catch(_){/* The offline boundary remains intact if its document is unavailable. */}
});
