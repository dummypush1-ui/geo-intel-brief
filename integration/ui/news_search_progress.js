/* Sequential manual/scroll history continuation. No retries or new route. */
export function newsScrollController({fetchPage,onPage,onState}){
 let generation=0,busy=false,next=null,filters=null,ended=false,abort=null,blocked=false,pages=0,scanned=0,matches=0;
 const state=text=>onState(text,{busy,ended,canLoad:!!next&&!busy&&!blocked});
 async function load(first=false){
  if(busy||blocked||!first&&!next)return false;
  const mine=generation,token=first?'':next;busy=true;abort=new AbortController();state('Searching source rows. Mutable read, not a snapshot.');
  try{
   const d=await fetchPage(filters,token,abort.signal);if(mine!==generation)return false;
   const fields=['items','scope','consistency','sort_semantics','limit','offset','next_cursor','exhausted','scanned_this_page','total_count'];
   if(!d||Object.keys(d).sort().join('|')!==fields.sort().join('|')||d.scope!=='whole_geo_store_cursor'||d.consistency!=='mutable_read_not_snapshot'||d.sort_semantics!=='raw_mongo_source_fields_with_id_tiebreak'||d.limit!==25||d.offset!==scanned||d.total_count!==null||typeof d.exhausted!=='boolean'||!Array.isArray(d.items)||d.items.length>25||!Number.isInteger(d.scanned_this_page)||d.scanned_this_page<0||d.scanned_this_page>1000||d.scanned_this_page<d.items.length||d.next_cursor!==null&&(typeof d.next_cursor!=='string'||!/^[A-Za-z0-9_-]{43}$/.test(d.next_cursor))||d.exhausted!==(d.next_cursor===null)||d.next_cursor===token)throw Error('Invalid search page. Refresh to restart.');
   next=d.next_cursor;ended=d.exhausted;pages++;scanned+=d.scanned_this_page;matches+=d.items.length;onPage(d.items,{first,ended});
   state('Mutable read, not a snapshot. Scanned '+pages+' pages / '+scanned+' source rows; '+matches+' matching stories so far. '+(ended?'Cursor exhausted without error for this read. Refresh for changes.':d.items.length?'More may exist. Load more to keep searching.':'Empty scan, more may exist. Load more to keep searching.'));return true;
  }catch(e){if(mine!==generation)return false;blocked=true;state(e.message||'Search unavailable. Not complete. Refresh to restart.');return false;}
  finally{if(mine===generation){busy=false;abort=null;onState(null,{busy,ended,canLoad:!!next&&!blocked});}}
 }
 return{reset(f){generation++;abort?.abort();busy=false;next=null;ended=false;blocked=false;pages=scanned=matches=0;filters={...f};return load(true);},more(){return load();},cancel(){generation++;abort?.abort();busy=false;next=null;blocked=true;state('Browser search paused. Server cursor closes after idle expiry, not immediately. Open Geo news to restart.');}};
}
