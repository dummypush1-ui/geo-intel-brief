// Conservative table-row evidence. AI output never establishes tax scope.
export function groundGst(candidate,text){
 const lines=text.split(/\r?\n/);const hits=[];
 for(let i=0;i<lines.length;i++){
  const row=lines[i];const code=row.match(/^\s*(?:\d+\.\s+)?(\d{4}|\d{6}|\d{8})(?!\d)\s+(.+)$/);
  if(!code||code[1]!==candidate.code)continue;
  const rates=[...row.matchAll(/(?<![\d.])(\d+(?:\.\d+)?)\s*%/g)].map(m=>m[1]+'%');
  if(rates.length!==1||rates[0]!==candidate.rate)continue;
  // Scope modifiers, exemptions and nearby footnotes require human analysis.
  const context=lines.slice(Math.max(0,i-2),Math.min(lines.length,i+3)).join('\n');
  if(/\b(except|excluding|exempt|subject to|provided that|condition|other than|chapter|nil)\b|[*†‡]/i.test(context))continue;
  const description=row.replace(/^\s*(?:\d+\.\s+)?\d{4,8}\s+/,'').replace(/\d+(?:\.\d+)?\s*%/g,'').trim();
  if(!description||description.toLowerCase()!==candidate.description.toLowerCase())continue;
  hits.push({line:i+1,row,code:candidate.code,rate:candidate.rate,description,context,scope:'explicit_single_rate_goods_row',review_required:true});
 }
 return hits.length===1?{state:'row_matched_pending_review',evidence:hits[0]}:{state:'held_ambiguous',reason:hits.length?'multiple_rows':'no_unique_unconditional_row'};
}
