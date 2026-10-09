/* Sequential scroll pages. No timers/polling; explicit scroll or button only. */
export function newsScrollController({fetchPage,onPage,onState}) {
 let generation=0,busy=false,next=null,filters=null,ended=false,abort=null,blocked=false;
 const state=(text)=>onState(text,{busy,ended,canLoad:!!next&&!busy&&!blocked});
 async function load(first=false) {
  if(busy || blocked || (!first&&!next))return false;
  const g=generation,token=first?'':next;busy=true;abort=new AbortController();state('Loading stories...');
  try {
   const d=await fetchPage(filters,token,abort.signal);
   if(g!==generation)return false;
   if(d.scope!=='whole_geo_store_cursor' || d.consistency!=='mutable_read_not_snapshot' || !Array.isArray(d.items) || d.items.length>25 || (d.next_cursor!==null && (typeof d.next_cursor!=='string'|| !/^[A-Za-z0-9_-]{43}$/.test(d.next_cursor))))throw new Error('Invalid news page. Refresh to restart.');
   if(d.next_cursor && d.next_cursor===token)throw new Error('News cursor did not advance. Refresh to restart.');
   next=d.next_cursor;ended=!next;onPage(d.items,{first,ended});
   state(ended?'End of this read. Refresh for new stories.':d.items.length?'Scroll down for more stories.':'No matching stories in this scan. Load more to continue.');
   return true;
  } catch(e) {
   if(g!==generation)return false;
   blocked=true;state(e.message||'News unavailable. Refresh to restart.');return false;
  } finally {
   if(g===generation){busy=false;abort=null;onState(null,{busy,ended,canLoad:!!next&&!blocked});}
  }
 }
 return {
  reset(f){generation++;abort?.abort();busy=false;next=null;ended=false;blocked=false;filters={...f};return load(true);},
  more(){return load();},
  cancel(){generation++;abort?.abort();busy=false;next=null;blocked=true;state('News paused. Open Geo news to refresh.');}
 };
}
