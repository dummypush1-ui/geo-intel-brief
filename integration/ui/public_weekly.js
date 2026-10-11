// Manual public PDF. No polling, persistence or automatic retry.
const form=document.getElementById('weekly-form'),status=document.getElementById('weekly-status');
let busy=false;
form.addEventListener('submit',async event=>{
 event.preventDefault();if(busy)return;busy=true;
 const button=form.querySelector('button');button.disabled=true;
 status.textContent='Generating from the latest-100 supplied sample. Stopping the browser wait does not stop server generation.';
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),30000);
 let url=null;
 try{
  const start=document.getElementById('weekly-start').value,end=document.getElementById('weekly-end').value;
  const r=await fetch('/api/weekly-report.pdf?'+new URLSearchParams({start,end}),{signal:controller.signal,credentials:'same-origin',cache:'no-store'});
  if(r.status===429){status.textContent='Busy or global start limit reached. All visitors share 10 starts per 60 seconds per process. Wait up to 60 seconds and retry manually.';return;}
  if(r.status===400){status.textContent='Check the dates: India time, exclusive end, 1 to 31 days, 1970 to 2100.';return;}
  if(r.status===503){status.textContent='Supplied-news PDF unavailable. Try manually later. No report saved or sent.';return;}
  if(!r.ok||!r.headers.get('content-type')?.startsWith('application/pdf'))throw new Error();
  const blob=await r.blob();if(blob.size>2097152||!new TextDecoder().decode(await blob.slice(0,8).arrayBuffer()).startsWith('%PDF-1.4'))throw new Error();
  url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='weekly-supplied-news.pdf';document.body.append(a);a.click();a.remove();
  const release=url;setTimeout(()=>URL.revokeObjectURL(release),1000);url=null;
  status.textContent='PDF download prepared from supplied sample rows only, not complete weekly history. Empty means no supplied items, not no events.';
 }catch(error){status.textContent=error.name==='AbortError'?'Browser wait stopped. Server generation may continue. Retry manually later.':'PDF unavailable. Try manually later. No report saved or sent.';}
 finally{clearTimeout(timer);if(url)URL.revokeObjectURL(url);busy=false;button.disabled=false;}
});
