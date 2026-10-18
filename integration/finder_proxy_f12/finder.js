// F12 served-copy bridge. Never reads keys/notes or calls fetch/provider URLs.
// The unchanged F11 data-only report button remains independent.
(() => {
 const host=window.top;
 const EDITIONS=/*F12_EDITIONS*/;
 let pending=null,held=false;
 const identity=i=>{const e=S.db.entries[i],system=SYS[e[0]].tag;return {system,edition:EDITIONS[system],code:String(e[1])}};
 const warn='AI snapshot context, not verified. No live web research or legal classification. ';
 function message(text){let node=document.getElementById('f12-status');if(!node){node=document.createElement('p');node.id='f12-status';node.setAttribute('role','status');document.getElementById('view').prepend(node)}node.textContent=text;}
 function request(feature,indices,question='',report=null){
  if(pending||held){message('Earlier proxy request is pending or held. Do not retry. Data-only features still work.');if(report)report.close();return}
  if(host===window){message('Open this Finder in the workspace to use the existing proxy. Data-only features still work.');if(report)report.close();return}
  const candidates=indices.map(identity);if(candidates.some(x=>!x.edition)){message('This identity is unavailable for the selected proxy context.');if(report)report.close();return}
  const id=crypto.randomUUID();pending={id,feature,candidates,selection:S.sel,compare:[S.cmpA,S.cmpB],report};message('Requesting once through the existing proxy. No personal keys or notes are sent. Classifier requests include your typed query (up to 1,000 characters); do not enter private information.');
  host.postMessage({type:'finder-proxy-f12-request',id,feature,candidates,question},location.origin);
 }
 window.addEventListener('message',event=>{
  if(event.origin!==location.origin||event.source!==host||!pending||event.data?.type!=='finder-proxy-f12-response'||event.data.id!==pending.id)return;
  const p=pending;pending=null;const data=event.data.result;
  if(!data||data.ok!==true||typeof data.answer!=='string'||data.answer.length>4000){held=event.data.dispatched===true;message('Existing proxy unavailable or request held. No automatic retry. Data-only report is available.');if(p.report){openTemplateReport(S.db,p.selection,p.report)}return}
  const refs=Array.isArray(data.sources)?data.sources.map(s=>String(s.title||'')+' ['+String(s.date||'')+']').join('; '):'';
  const text=warn+data.answer+(refs?' Sources: '+refs:'');
  // A late answer must not repaint another code or comparison.
  if(p.report){
   const html=buildTemplateReport(S.db,p.selection,null,{f12Context:text});p.report.document.open();p.report.document.write(html);p.report.document.close();setupTemplateReportWindow(p.report);
  }else if(p.feature==='classification_context'){
   message(text); // Preserve offline candidates, never invent/replace code picks.
  }else if(p.feature==='code_comparison'){
   if(S.cmpA!==p.compare[0]||S.cmpB!==p.compare[1])return;
   V.cmpVerdict=text;V.cmpErr=null;paintCompare();message(warn);
  }else{
   if(S.sel!==p.selection)return;
   const field={plain_words:'plain',trade_brief:'brief',paperwork:'doc'}[p.feature];V[field]=text;V[field+'Err']=null;paintDetail();message(warn);
  }
 });
 document.addEventListener('click',event=>{
  const button=event.target.closest('button');if(!button)return;
  const feature={'plain-go':'plain_words','brief-go':'trade_brief','doc-go':'paperwork','cmpv-go':'code_comparison','f12-report':'report_context'}[button.id];
  if(!feature)return;event.preventDefault();event.stopImmediatePropagation();
  let report=null;if(feature==='report_context'){report=window.open('','_blank');if(!report){message('Popup blocked. Allow popups or use the data-only report.');return}}
  request(feature,feature==='code_comparison'?[S.cmpA,S.cmpB]:[S.sel],'',report);
 },true);
 // Add, never replace, the original report action. No request on load/render.
 const observe=new MutationObserver(()=>{
  const data=document.getElementById('d-tpl');if(data&&!document.getElementById('f12-report')){const button=document.createElement('button');button.id='f12-report';button.className='file-button is-compact';button.textContent='Optional AI snapshot-context PDF';button.type='button';data.after(button)}
 });observe.observe(document.getElementById('root'),{subtree:true,childList:true});
 // Original classifier keeps its local search/fallback logic. AI only explains
 // supplied candidates after an explicit manual classifier click.
 window.__f12Classify=()=>{const r=search(S.db,V.q.trim(),'','',V.sysFilter);const ids=groupFamilies(S.db,r.out).slice(0,4);if(!ids.length){message('No preserved candidates to explain. Offline search remains available.');return}request('classification_context',ids,V.q.trim().slice(0,1000))};
})();
