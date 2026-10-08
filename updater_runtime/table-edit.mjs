// Pure, exact closed-source table edits. No filesystem, effects or AI authority.
export function insertRows(source, declaration, rows) {
  if(typeof source!=='string'||!Array.isArray(rows)||rows.some(r=>typeof r!=='string'||r.includes('\n')))throw Error('Invalid table input');
  if(source.split(declaration).length!==2)throw Error('Exactly one table declaration required');
  const ends=[...source.matchAll(/^\};\s*$/gm)];
  if(ends.length!==1||!/^\s*$/.test(source.slice(ends[0].index+ends[0][0].length)))throw Error('Exactly one final table terminator required');
  if(!rows.length)return source;
  const index=ends[0].index;
  const before=source.slice(0,index).replace(/\s*$/,'');
  // Last existing row may omit its comma. Add the separator literally.
  const separator=before.endsWith('{')||before.endsWith(',')?'':',';
  return before+separator+'\n'+rows.join('\n')+'\n};\n';
}
export function validateGstChange(c, sources) {
    if(!c||typeof c!=='object'||Array.isArray(c)||Object.keys(c).some(k=>!['code','rate','description','source'].includes(k))||typeof c.code!=='string'||! /^(?:\d{2}|\d{4}|\d{6}|\d{8})$/.test(c.code)||typeof c.rate!=='string'||! /^\d+(?:\.\d+)?%$/.test(c.rate)||Number(c.rate.slice(0,-1))>100||typeof c.description!=='string'||!c.description.trim()||c.description.length>2000||/[\x00-\x1f\x7f]/.test(c.description)||c.source!==undefined&&(typeof c.source!=='string'||!sources.includes(c.source)))throw Error('Invalid GST change');
  return c;
}
export function applyGst(source, proposal) {
  if(!proposal||typeof proposal!=='object'||Array.isArray(proposal)||!Array.isArray(proposal.changes)||!proposal.changes.length||proposal.changes.length>500||!Array.isArray(proposal.sources)||!proposal.sources.length||proposal.sources.some(s=>typeof s!=='string'||!/^https:\/\//.test(s)||s.length>2048))throw Error('Invalid GST proposal');
  const declaration='export const GST_MAP: Record<string, [string, string]> = {';
  insertRows(source,declaration,[]);
  const seen=new Set(),lines=[];let next=source,applied=0;
  for(const c of proposal.changes){
    validateGstChange(c,proposal.sources);
    if(seen.has(c.code))throw Error('Duplicate proposal code');
    seen.add(c.code);
    const re=new RegExp('^  "'+c.code+'": (\\[[^\\n]*\\]),?$', 'gm');
    const matches=[...next.matchAll(re)];
    const loose=[...next.matchAll(new RegExp('^[ \t]*[\"\']'+c.code+'[\"\'][ \t]*:', 'gm'))];
    if(loose.length>1)throw Error('Duplicate GST row');
    if(loose.length!==matches.length)throw Error('GST row format requires review');
    const row='  '+JSON.stringify(c.code)+': '+JSON.stringify([c.rate,c.description])+',';
    let previous=null;
    if(matches.length){
      try{previous=JSON.parse(matches[0][1]);}catch{throw Error('Invalid existing GST row');}
      if(!Array.isArray(previous)||previous.length!==2||previous.some(v=>typeof v!=='string'))throw Error('Invalid existing GST schema');
      next=next.replace(re,()=>row);
    } else next=insertRows(next,declaration,[row]);
    const verify=new RegExp('^  "'+c.code+'": (\\[[^\\n]*\\]),?$', 'gm');
    const stored=[...next.matchAll(verify)];
    if(stored.length!==1||JSON.stringify(JSON.parse(stored[0][1]))!==JSON.stringify([c.rate,c.description]))throw Error('GST edit verification failed');
    applied++;
    lines.push({code:c.code,previous:previous?.[0]??null,rate:c.rate,description:c.description});
  }
  return {source:next,applied,lines};
}
export function appendAliases(source, entries) {
  const declaration='export const ALIASES: Record<string, string[][]> = {';
  insertRows(source,declaration,[]);
  if(!Array.isArray(entries))throw Error('Invalid aliases');
  const seen=new Set([...source.matchAll(/^\s*'([^']+)':/gm)].map(m=>m[1])),rows=[];
  for(const e of entries){
    if(!e||typeof e!=='object'||Object.keys(e).length!==2||typeof e.term!=='string'||! /^[a-z][a-z0-9 -]{1,38}$/.test(e.term)||seen.has(e.term)||!Array.isArray(e.sets)||!e.sets.length||e.sets.length>4||e.sets.some(s=>!Array.isArray(s)||s.length<1||s.length>3||s.some(w=>typeof w!=='string'||! /^[a-z]{3,20}$/.test(w))))throw Error('Invalid alias entry');
    rows.push(`  '${e.term}': ${JSON.stringify(e.sets).replace(/"/g,"'")},`);seen.add(e.term);
  }
  const next=insertRows(source,declaration,rows);
  for(const e of entries)if([...next.matchAll(new RegExp("^  '"+e.term+"':",'gm'))].length!==1)throw Error('Alias edit verification failed');
  return {source:next,added:entries.length};
}
