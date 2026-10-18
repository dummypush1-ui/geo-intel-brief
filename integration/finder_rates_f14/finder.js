// F14 served-copy evidence drawer. Data only. Never reads notes/keys/storage.
(() => {
 const META=/*F14_META*/;
 const make=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n};
 function row(dl,label,value){dl.append(make('dt',label),make('dd',value===null||value===undefined?'Not listed in this snapshot':typeof value==='object'?JSON.stringify(value):String(value)))}
 function paint(){
  const anchor=document.getElementById('d-tpl');if(!anchor||!S.db||!Number.isInteger(S.sel))return;
  const existing=document.getElementById('f14-evidence');if(existing){if(existing.dataset.selection===String(S.sel))return;existing.remove()}
  const e=S.db.entries[S.sel];if(!e)return;
  const box=make('details');box.id='f14-evidence';box.dataset.selection=String(S.sel);box.className='detail-sec';box.append(make('summary','Rate source evidence - preserved snapshot'));
  box.append(make('p','Snapshot data, not advice. These source labels and values are preserved, not a current official check. They do not show that a shipment qualifies for a rate, exemption or rebate.'));
  const dl=make('dl');row(dl,'Selected identity',SYS[e[0]].tag+' '+e[1]);row(dl,'Dataset build label',DATA_BUILD);row(dl,'Source attribution in this snapshot',SYS[e[0]].src);for(const [k,v]of Object.entries(META))row(dl,k,v);
  if(e[0]!==1){row(dl,'Coverage','GST, BCD and RoDTEP drawer covers India rows only. No cross-system equivalence is inferred.');box.append(dl);anchor.after(box);return}
  row(dl,'Selected row rate label (original Finder display)',e[5]||null);
  row(dl,'BCD-prefixed rate in selected row',typeof e[5]==='string'&&e[5].startsWith('BCD ')?e[5]:null);
  row(dl,'BCD source label','CBIC Customs Tariff First Schedule as on 30.06.2025, statutory standard rate. Source attribution only; effective/concessional rates and exemptions are not verified. A missing BCD-prefixed value is not zero.');
  let key=null;for(const n of [8,6,4,2]){if(e[1].length>=n&&GST_MAP[e[1].slice(0,n)]){key=e[1].slice(0,n);break}}if(key===null&&GST_MAP['*'])key='*';
  row(dl,'GST matched source key',key);row(dl,'GST source entry (rate and wording)',key===null?null:GST_MAP[key]);row(dl,'GST match scope',key===null?'No match':key==='*'?'Residual fallback, not a product-specific qualification':key===e[1]?'Exact source key':'Parent/prefix source key, not a legal equivalence');
  row(dl,'GST source label','Notification 9/2025-Integrated Tax (Rate), 17 Sep 2025. Exempt goods use a separate list. Beverage mappings may carry a later amendment in the source; verify the notification, scope and effective date.');
  if(['22029921','22029929','22029931','22029939','22029991','22029999','22029100'].includes(e[1]))row(dl,'Beverage mapping amendment in source','Notification 01/2026-Integrated Tax (Rate), effective 1 May 2026, and corrigendum 6 May 2026. Source attribution, not current verification.');
  for(const [label,values]of[['DTA (Appendix 4R)',RODTEP_DTA],['SEZ / EOU / AA (Appendix 4RE)',RODTEP_SEZ]]){
   const hit=e[1].length===8?values[e[1]]:null;row(dl,'RoDTEP '+label+' exact 8-digit entry',hit?{rate:hit[0],cap:hit[1]||'Blank in source, not verified as uncapped',uqc:hit[2]||'Blank in source, unit not verified'}:null);
  }
  row(dl,'RoDTEP source label','DGFT Appendix 4R / 4RE, base Notification 32/2024 (wef 10.10.2024), as amended by Notification 15/2026-27 (wef 01.05.2026), as attributed by this snapshot. No current schedule or eligibility verification. No parent-code rebate is inherited.');box.append(dl);
  box.append(make('p','Open the official sources separately to check current notifications, conditions, effective dates and eligibility. A portal link is not a verification of the selected rate.'));
  for(const [label,url]of[['CBIC notification repository','https://taxinformation.cbic.gov.in/'],['CBIC GST rates','https://cbic-gst.gov.in/gst-goods-services-rates.html'],['DGFT RoDTEP','https://www.dgft.gov.in/CP/?opt=rodtep'],['ICEGATE duty calculator','https://www.icegate.gov.in/services/custom-duty-calculator']]){const p=make('p'),a=make('a',label+' (not checked live)');a.href=url;a.target='_blank';a.rel='noreferrer noopener';p.append(a);box.append(p)}
  anchor.after(box);
 }
 new MutationObserver(paint).observe(document.getElementById('root'),{subtree:true,childList:true});paint();
})();
