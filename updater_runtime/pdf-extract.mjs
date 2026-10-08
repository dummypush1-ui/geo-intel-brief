import fs from 'node:fs';import os from 'node:os';import path from 'node:path';import {spawnSync}from 'node:child_process';
export const PDFTOTEXT_VERSION='22.02.0';
export function extractNotificationPdf(bytes,{tool='pdftotext',timeout=20000}={}){
 if(!Buffer.isBuffer(bytes)||bytes.length<5||bytes.length>10*1024*1024||bytes.subarray(0,5).toString()!=='%PDF-')throw new Error('PDF format or size refused');
 const v=spawnSync(tool,['-v'],{encoding:'utf8',timeout:2000,maxBuffer:4096});
 if(v.error?.code==='ENOENT')throw new Error('Required pdftotext build input missing');
 if(v.error||v.status!==0||!((v.stdout||'')+(v.stderr||'')).includes('pdftotext version '+PDFTOTEXT_VERSION+'\n'))throw new Error('Required pdftotext version '+PDFTOTEXT_VERSION+' unavailable');
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'gst-pdf-'));try{
  const file=path.join(dir,'notice.pdf');fs.writeFileSync(file,bytes,{mode:0o600});
  const r=spawnSync(tool,['-layout',file,'-'],{encoding:'utf8',timeout,maxBuffer:2*1024*1024});
  if(r.error||r.status!==0)throw new Error('PDF extraction failed or exceeded time/output limit');
  if(!r.stdout?.trim())throw new Error('Empty PDF extraction');return r.stdout;
 }finally{fs.rmSync(dir,{recursive:true,force:true});}
}
